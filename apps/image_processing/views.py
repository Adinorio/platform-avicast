import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q
from .models import (
    ImageUpload, ImageProcessingResult, ProcessingBatch,
    BirdSpecies, AIModel
)
from .ai_service import get_bird_detection_service
from apps.users.models import UserActivity
from apps.locations.models import Site, CensusObservation, SpeciesObservation

logger = logging.getLogger(__name__)

@login_required
def dashboard(request):
    """Image processing dashboard with statistics and recent uploads"""
    # Get statistics
    total_uploads = ImageUpload.objects.count()
    processed_uploads = ImageUpload.objects.filter(upload_status='PROCESSED').count()
    pending_review = ImageProcessingResult.objects.filter(review_status='PENDING').count()
    approved_results = ImageProcessingResult.objects.filter(review_status='APPROVED').count()

    # Recent uploads
    recent_uploads = ImageUpload.objects.select_related('uploaded_by').order_by('-uploaded_at')[:5]

    # Recent results
    recent_results = ImageProcessingResult.objects.select_related(
        'image_upload__uploaded_by'
    ).order_by('-created_at')[:5]

    context = {
        'total_uploads': total_uploads,
        'processed_uploads': processed_uploads,
        'pending_review': pending_review,
        'approved_results': approved_results,
        'recent_uploads': recent_uploads,
        'recent_results': recent_results,
        'ai_models': AIModel.choices,
    }

    return render(request, 'image_processing/dashboard.html', context)

@login_required
def upload_view(request):
    """Handle image upload"""
    if request.method == 'POST' and request.FILES.getlist('images'):
        files = request.FILES.getlist('images')
        uploaded_files = []

        for file in files:
            try:
                # Create ImageUpload instance
                image_upload = ImageUpload.objects.create(
                    title=f"Upload by {request.user.employee_id}",
                    description=f"Uploaded via web interface",
                    image_file=file,
                    uploaded_by=request.user,
                    file_size=file.size,
                    file_type=file.content_type or 'image/jpeg',
                    original_filename=file.name
                )
                uploaded_files.append(image_upload)

            except Exception as e:
                logger.error(f"Failed to upload file {file.name}: {str(e)}")
                messages.error(request, f"Failed to upload {file.name}: {str(e)}")

        if uploaded_files:
            messages.success(request, f"Successfully uploaded {len(uploaded_files)} image(s)")
            return redirect('image_processing:process_batch', batch_id=uploaded_files[0].id)

    return render(request, 'image_processing/upload.html')

@login_required
def process_view(request, batch_id=None):
    """Process uploaded images with AI"""
    # Get images to process
    if batch_id:
        images = ImageUpload.objects.filter(
            Q(id=batch_id) | Q(upload_status='UPLOADED')
        ).filter(uploaded_by=request.user)[:10]
    else:
        images = ImageUpload.objects.filter(
            upload_status='UPLOADED',
            uploaded_by=request.user
        )[:10]

    if not images:
        messages.info(request, "No images available for processing")
        return redirect('image_processing:dashboard')

    # Get AI model preference from request
    ai_model = request.GET.get('model', 'YOLO_V8')

    context = {
        'images': images,
        'ai_model': ai_model,
        'ai_models': AIModel.choices,
    }

    return render(request, 'image_processing/process.html', context)

@login_required
def start_processing(request):
    """AJAX endpoint to start AI processing"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            image_ids = data.get('image_ids', [])
            ai_model = data.get('ai_model', 'YOLO_V8')
            confidence_threshold = float(data.get('confidence_threshold', 0.25))

            if not image_ids:
                return JsonResponse({'error': 'No images selected'}, status=400)

            # Get images
            images = ImageUpload.objects.filter(
                id__in=image_ids,
                uploaded_by=request.user
            )

            if not images:
                return JsonResponse({'error': 'Images not found'}, status=404)

            # Initialize AI service
            ai_service = get_bird_detection_service(ai_model)

            results = []
            for image in images:
                try:
                    # Mark as processing
                    image.start_processing()

                    # Run AI detection
                    detection_result = ai_service.detect_birds(
                        image.image_file.path,
                        confidence_threshold
                    )

                    # Create or update processing result
                    result, created = ImageProcessingResult.objects.get_or_create(
                        image_upload=image,
                        defaults={
                            'ai_model': ai_model,
                            'model_confidence_threshold': confidence_threshold,
                        }
                    )

                    # Update result with detection data
                    result.processing_status = 'COMPLETED' if detection_result['success'] else 'FAILED'
                    result.detected_species = detection_result.get('detected_species')
                    result.confidence_score = detection_result.get('confidence_score')
                    result.bounding_box = detection_result.get('bounding_box', {})
                    result.inference_time = detection_result.get('inference_time')
                    result.save()

                    # Mark image as processed
                    if detection_result['success']:
                        image.complete_processing()
                    else:
                        image.mark_failed()

                    results.append({
                        'image_id': image.id,
                        'success': detection_result['success'],
                        'species': detection_result.get('detected_species'),
                        'confidence': detection_result.get('confidence_score'),
                        'error': detection_result.get('error')
                    })

                except Exception as e:
                    logger.error(f"Processing failed for image {image.id}: {str(e)}")
                    image.mark_failed()
                    results.append({
                        'image_id': image.id,
                        'success': False,
                        'error': str(e)
                    })

            return JsonResponse({
                'success': True,
                'message': f'Processed {len(results)} images',
                'results': results
            })

        except Exception as e:
            logger.error(f"Processing request failed: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
def review_view(request):
    """Review and approve/reject AI processing results"""
    # Only admins can review
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied. Admin only.')
        return redirect('image_processing:dashboard')

    # Get filter parameters
    status_filter = request.GET.get('status', 'PENDING')
    model_filter = request.GET.get('model', '')
    search_query = request.GET.get('search', '')

    # Build queryset
    results = ImageProcessingResult.objects.select_related(
        'image_upload__uploaded_by'
    ).order_by('-created_at')

    if status_filter != 'ALL':
        results = results.filter(review_status=status_filter)

    if model_filter:
        results = results.filter(ai_model=model_filter)

    if search_query:
        results = results.filter(
            Q(image_upload__title__icontains=search_query) |
            Q(detected_species__icontains=search_query)
        )

    # Pagination
    paginator = Paginator(results, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'model_filter': model_filter,
        'search_query': search_query,
    }

    return render(request, 'image_processing/review.html', context)

@login_required
def approve_result(request, result_id):
    """Approve a processing result"""
    if request.user.role != 'ADMIN':
        return JsonResponse({'error': 'Access denied'}, status=403)

    try:
        result = get_object_or_404(ImageProcessingResult, id=result_id)
        result.approve_result(request.user, request.POST.get('notes', ''))

        return JsonResponse({
            'success': True,
            'message': 'Result approved successfully'
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def reject_result(request, result_id):
    """Reject a processing result"""
    if request.user.role != 'ADMIN':
        return JsonResponse({'error': 'Access denied'}, status=403)

    try:
        result = get_object_or_404(ImageProcessingResult, id=result_id)
        result.reject_result(request.user, request.POST.get('notes', ''))

        return JsonResponse({
            'success': True,
            'message': 'Result rejected successfully'
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def allocate_view(request):
    """Allocate approved results to census data"""
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied. Admin only.')
        return redirect('image_processing:dashboard')

    # Get approved results that can be allocated
    allocatable_results = ImageProcessingResult.objects.filter(
        review_status='APPROVED',
        detected_species__isnull=False
    ).select_related('image_upload__uploaded_by').order_by('-created_at')

    # Get sites for allocation
    sites = Site.objects.filter(status='active')

    context = {
        'allocatable_results': allocatable_results[:20],  # Show recent 20
        'sites': sites,
        'bird_species': BirdSpecies.choices,
    }

    return render(request, 'image_processing/allocate.html', context)

@login_required
def allocate_to_census(request):
    """Allocate processing results to census data"""
    if request.user.role != 'ADMIN':
        return JsonResponse({'error': 'Access denied'}, status=403)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            result_ids = data.get('result_ids', [])
            site_id = data.get('site_id')
            year = int(data.get('year'))
            month = int(data.get('month'))

            if not result_ids or not site_id:
                return JsonResponse({'error': 'Missing required data'}, status=400)

            # Get site
            site = get_object_or_404(Site, id=site_id)

            # Get or create census observation
            census, created = CensusObservation.objects.get_or_create(
                site=site,
                observation_date__year=year,
                observation_date__month=month,
                defaults={
                    'observation_date': timezone.now().replace(year=year, month=month, day=1),
                    'observer': request.user,
                    'weather_conditions': 'AI-assisted observation'
                }
            )

            # Process each result
            allocated_count = 0
            for result_id in result_ids:
                try:
                    result = ImageProcessingResult.objects.get(id=result_id)

                    if result.review_status == 'APPROVED' and result.detected_species:
                        # Create species observation
                        species_obs, created = SpeciesObservation.objects.get_or_create(
                            census=census,
                            species_name=result.detected_species,
                            defaults={'count': 1}
                        )

                        if not created:
                            species_obs.count += 1
                            species_obs.save()

                        allocated_count += 1

                except ImageProcessingResult.DoesNotExist:
                    continue

            return JsonResponse({
                'success': True,
                'message': f'Successfully allocated {allocated_count} results to census',
                'allocated_count': allocated_count
            })

        except Exception as e:
            logger.error(f"Allocation failed: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)
