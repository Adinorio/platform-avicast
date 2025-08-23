import os
import hashlib
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.utils import timezone
from django.conf import settings

logger = logging.getLogger(__name__)

from .models import ImageUpload, ImageProcessingResult, ProcessingBatch
from .forms import ImageUploadForm, ImageProcessingForm
from .local_storage import LocalStorageManager
from .image_optimizer import ImageOptimizer

# Lazy storage manager initialization
def get_storage_manager():
    """Get storage manager instance when needed"""
    return LocalStorageManager()

@login_required
def image_upload_view(request):
    """Handle image upload with automatic processing"""
    if request.method == 'POST':
        logger.info(f"POST request received with FILES: {request.FILES}")
        logger.info(f"POST data: {request.POST}")
        
        form = ImageUploadForm(request.POST, request.FILES)
        logger.info(f"Form created, is_valid: {form.is_valid()}")
        if not form.is_valid():
            logger.warning(f"Form errors: {form.errors}")
        
        if form.is_valid():
            try:
                # Get uploaded files (now supports multiple)
                image_files = request.FILES.getlist('image_file')
                logger.info(f"Processing {len(image_files)} image(s)")
                
                if not image_files:
                    messages.error(request, "No images selected for upload.")
                    return redirect('image_processing:upload')
                
                # Handle single file case (backward compatibility)
                if len(image_files) == 1:
                    image_files = [image_files[0]]
                
                uploaded_images = []
                
                for i, image_file in enumerate(image_files, 1):
                    logger.info(f"Processing upload {i}/{len(image_files)}: {image_file.name}, size: {image_file.size}, type: {image_file.content_type}")
                    
                    # Calculate file hash for deduplication
                    file_content = image_file.read()
                    file_hash = hashlib.sha256(file_content).hexdigest()
                    logger.info(f"File hash calculated: {file_hash[:10]}...")
                    
                    # Check for duplicates - allow re-uploads with different metadata
                    logger.info(f"Checking for duplicates...")
                    try:
                        existing_images = ImageUpload.objects.filter(file_hash=file_hash)
                        if existing_images.exists():
                            logger.info(f"Found {existing_images.count()} existing image(s) with same hash")
                            
                            # Check if this is a true duplicate (same user, same title, recent upload)
                            recent_duplicate = existing_images.filter(
                                uploaded_by=request.user,
                                title__icontains=form.cleaned_data.get('title', ''),
                                uploaded_at__gte=timezone.now() - timezone.timedelta(hours=24)
                            ).first()
                            
                            if recent_duplicate:
                                logger.info(f"Recent duplicate detected: {recent_duplicate.pk}")
                                messages.warning(request, f"You recently uploaded this exact image '{image_file.name}' with title '{recent_duplicate.title}'. Consider using the existing upload or provide different metadata.")
                                # Redirect to dashboard instead of detail page
                                return redirect('image_processing:dashboard')
                            else:
                                logger.info(f"Allowing re-upload of same image with different metadata")
                                # Generate unique filename to avoid conflicts
                                base_name, ext = os.path.splitext(image_file.name)
                                timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
                                unique_filename = f"{base_name}_{timestamp}{ext}"
                                logger.info(f"Generated unique filename: {unique_filename}")
                                
                                messages.info(request, f"Image '{image_file.name}' was previously uploaded, but you can upload it again with different title/description.")
                                
                                # Update the filename to avoid conflicts
                                image_file.name = unique_filename
                        
                        logger.info(f"Proceeding with upload...")
                    except Exception as e:
                        logger.error(f"Error checking duplicates: {str(e)}")
                        # Continue with upload if duplicate check fails
                        logger.warning(f"Continuing with upload despite duplicate check error...")
                    
                    # Reset file pointer for saving
                    logger.info(f"Resetting file pointer...")
                    image_file.seek(0)
                    
                    # Create image upload record
                    logger.info(f"Creating ImageUpload object for {image_file.name}...")
                    image_upload = ImageUpload()
                    image_upload.uploaded_by = request.user
                    image_upload.file_size = image_file.size
                    image_upload.file_type = image_file.content_type
                    image_upload.file_hash = file_hash
                    image_upload.original_filename = image_file.name
                    image_upload.upload_status = ImageUpload.UploadStatus.UPLOADED
                    
                    # Use form data for title/description if provided
                    if form.cleaned_data.get('title'):
                        image_upload.title = form.cleaned_data.get('title')
                    else:
                        # Auto-generate title from filename
                        base_name = os.path.splitext(image_file.name)[0]
                        image_upload.title = base_name.replace('_', ' ').title()
                    
                    if form.cleaned_data.get('description'):
                        image_upload.description = form.cleaned_data.get('description')
                    
                    # Save original file
                    logger.info(f"Saving original file...")
                    image_upload.image_file.save(image_file.name, image_file, save=False)
                    image_upload.save()
                    logger.info(f"Original file saved: {image_upload.image_file.path if hasattr(image_upload.image_file, 'path') else 'No path'}")
                    
                    # Process image with local storage
                    logger.info(f"Starting image processing for {image_file.name}...")
                    try:
                        process_image_with_storage(image_upload, file_content)
                        logger.info(f"Image processing completed successfully for {image_file.name}")
                        uploaded_images.append(image_upload)
                    except Exception as e:
                        logger.error(f"Image processing failed for {image_file.name}: {str(e)}")
                        # Still add to uploaded_images but mark as failed
                        uploaded_images.append(image_upload)
                
                # Handle post-upload routing and feedback
                if uploaded_images:
                    successful_uploads = [img for img in uploaded_images if img.upload_status == ImageUpload.UploadStatus.PROCESSED]
                    failed_uploads = [img for img in uploaded_images if img.upload_status == ImageUpload.UploadStatus.FAILED]
                    
                    # Store upload results in session for modal display
                    request.session['upload_results'] = {
                        'total': len(uploaded_images),
                        'successful': len(successful_uploads),
                        'failed': len(failed_uploads),
                        'uploaded_ids': [str(img.pk) for img in uploaded_images]
                    }
                    
                    # Redirect to dashboard with success message
                    if len(uploaded_images) == 1:
                        if successful_uploads:
                            messages.success(request, f"Image '{uploaded_images[0].title}' uploaded and processed successfully!")
                            return redirect('image_processing:detail', pk=uploaded_images[0].pk)
                        else:
                            messages.warning(request, f"Image '{uploaded_images[0].title}' uploaded but processing failed. Check details page.")
                            return redirect('image_processing:detail', pk=uploaded_images[0].pk)
                    else:
                        if successful_uploads and failed_uploads:
                            messages.warning(request, f"{len(successful_uploads)} images processed successfully, {len(failed_uploads)} failed. Check list for details.")
                        elif successful_uploads:
                            messages.success(request, f"{len(successful_uploads)} images uploaded and processed successfully!")
                        else:
                            messages.error(request, f"All {len(uploaded_images)} images uploaded but processing failed.")
                        
                        return redirect('image_processing:dashboard')
                else:
                    # This should not happen now since we redirect on duplicate, but just in case
                    messages.error(request, "No images were uploaded successfully.")
                    return redirect('image_processing:upload')
                    
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                logger.error(f"Upload error: {str(e)}")
                logger.error(f"Traceback: {error_details}")
                messages.error(request, f"Upload failed: {str(e)}")
                return redirect('image_processing:upload')
    else:
        form = ImageUploadForm()
    
    return render(request, 'image_processing/upload.html', {'form': form})

def process_image_with_storage(image_upload, file_content):
    """Process image with local storage optimization and real bird detection"""
    try:
        logger.info(f"Starting processing for image {image_upload.pk}")
        
        # Start processing
        logger.info("Calling start_processing...")
        image_upload.start_processing()
        logger.info("start_processing completed")
        
        # Optimize image
        logger.info("Creating ImageOptimizer...")
        optimizer = ImageOptimizer()
        logger.info("Optimizing image...")
        optimized_content, new_size, format_used = optimizer.optimize_image(file_content)
        logger.info(f"Image optimized: {format_used}, new size: {new_size}")
        
        # Update image record with optimization info
        logger.info("Updating image record...")
        image_upload.compressed_size = new_size
        image_upload.is_compressed = True
        image_upload.upload_status = ImageUpload.UploadStatus.PROCESSED
        image_upload.save()
        logger.info("Image record updated")
        
        # Save optimized image
        logger.info("Saving optimized image...")
        from django.core.files.base import ContentFile
        optimized_file = ContentFile(optimized_content, f"optimized_{image_upload.original_filename}")
        image_upload.image_file.save(f"optimized_{image_upload.original_filename}", optimized_file, save=False)
        image_upload.save()
        logger.info("Optimized image saved")
        
        # Run real bird detection
        logger.info("Running bird detection...")
        try:
            from .bird_detection_service import get_bird_detection_service
            
            detection_service = get_bird_detection_service()
            if detection_service.is_available():
                logger.info("Bird detection service available, running detection...")
                detection_result = detection_service.detect_birds(file_content, image_upload.original_filename)
                
                if detection_result['success']:
                    logger.info(f"Detection successful: {detection_result['total_detections']} birds found")
                    
                    # Create processing result with real detection data
                    if not hasattr(image_upload, 'processing_result'):
                        from .models import ImageProcessingResult
                        import uuid
                        
                        # Use the best detection result
                        best_detection = detection_result['best_detection']
                        
                        if best_detection:
                            detected_species = best_detection['species']
                            confidence_score = best_detection['confidence']
                            bounding_box = best_detection['bounding_box']
                        else:
                            # No birds detected
                            detected_species = None
                            confidence_score = 0.0
                            bounding_box = {}
                        
                        # Store all detections in the bounding_box field for visualization
                        all_detections = detection_result.get('detections', [])
                        detection_data = {
                            'best_detection': bounding_box,
                            'all_detections': [
                                {
                                    'species': det['species'],
                                    'confidence': det['confidence'],
                                    'bounding_box': det['bounding_box']
                                } for det in all_detections
                            ],
                            'total_count': len(all_detections)
                        }
                        
                        processing_result = ImageProcessingResult.objects.create(
                            id=uuid.uuid4(),
                            image_upload=image_upload,
                            detected_species=detected_species,
                            confidence_score=confidence_score,
                            bounding_box=detection_data,  # Store comprehensive detection data
                            total_detections=detection_result['total_detections'],
                            processing_status=ImageProcessingResult.ProcessingStatus.COMPLETED,
                            ai_model='YOLO_V8',
                            model_version=detection_result['model_used'],
                            processing_device=detection_result['device_used'],
                            inference_time=2.5,  # TODO: Measure actual inference time
                            model_confidence_threshold=detection_result['confidence_threshold'],
                            review_status=ImageProcessingResult.ReviewStatus.PENDING,  # Ready for review
                            review_notes='',
                            is_overridden=False
                        )
                        logger.info(f"Processing result created with real detection: {processing_result.pk}")
                        logger.info(f"Species: {detected_species}, Confidence: {confidence_score}")
                        logger.info(f"Total detections: {detection_result['total_detections']}")
                    else:
                        logger.info("Processing result already exists")
                else:
                    logger.error(f"Detection failed: {detection_result.get('error', 'Unknown error')}")
                    # Create a failed processing result
                    _create_failed_processing_result(image_upload, detection_result.get('error', 'Detection failed'))
            else:
                logger.warning("Bird detection service not available, using fallback")
                _create_fallback_processing_result(image_upload)
                
        except Exception as e:
            logger.error(f"Error during bird detection: {str(e)}")
            # Create a failed processing result
            _create_failed_processing_result(image_upload, str(e))
        
        # Complete processing
        logger.info("Completing processing...")
        image_upload.complete_processing()
        logger.info("Processing completed successfully")
        
        # Check storage usage (archive functionality can be added later)
        # storage_manager = get_storage_manager()
        # storage_manager.check_and_archive_if_needed()
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Image processing error: {str(e)}")
        logger.error(f"Traceback: {error_details}")
        image_upload.mark_failed()
        # Don't re-raise the error - let the upload continue
        logger.error(f"Image processing failed for {image_upload.pk}, but upload will continue")

@login_required
def image_list_view(request):
    """Display list of uploaded images with storage information"""
    # Get user's images or all images if admin
    if request.user.is_staff:
        images = ImageUpload.objects.all()
    else:
        images = ImageUpload.objects.filter(uploaded_by=request.user)
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        images = images.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(original_filename__icontains=search_query)
        )
    
    # Filter by storage tier
    storage_tier = request.GET.get('storage_tier', '')
    if storage_tier:
        images = images.filter(storage_tier=storage_tier)
    
    # Filter by compression status
    compression_status = request.GET.get('compression_status', '')
    if compression_status == 'compressed':
        images = images.filter(is_compressed=True)
    elif compression_status == 'uncompressed':
        images = images.filter(is_compressed=False)
    
    # Pagination
    paginator = Paginator(images, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get storage statistics
    storage_manager = get_storage_manager()
    storage_stats = storage_manager.get_storage_usage()
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'storage_tier': storage_tier,
        'compression_status': compression_status,
        'storage_stats': storage_stats,
        'total_images': images.count(),
        'compressed_images': images.filter(is_compressed=True).count(),
        'uncompressed_images': images.filter(is_compressed=False).count(),
    }
    
    return render(request, 'image_processing/list.html', context)

@login_required
def image_detail_view(request, pk):
    """Display detailed view of an image with storage information"""
    image = get_object_or_404(ImageUpload, pk=pk)
    
    # Check if user can view this image
    if not request.user.is_staff and image.uploaded_by != request.user:
        messages.error(request, "You don't have permission to view this image.")
        return redirect('image_processing:list')
    
    # Get processing result if exists
    try:
        processing_result = image.processing_result
    except ImageProcessingResult.DoesNotExist:
        processing_result = None
    
    # Get storage information
    storage_info = image.get_storage_info()
    
    context = {
        'image_upload': image,
        'processing_result': processing_result,
        'storage_info': storage_info,
    }
    
    return render(request, 'image_processing/detail.html', context)

@login_required
def storage_status_view(request):
    """Display storage status and management options"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to view storage status.")
        return redirect('image_processing:list')
    
    # Get storage usage
    storage_manager = get_storage_manager()
    storage_usage = storage_manager.get_storage_usage()
    
    # Get storage recommendations
    recommendations = storage_manager._get_storage_recommendations()
    
    # Get recent uploads
    recent_uploads = ImageUpload.objects.order_by('-uploaded_at')[:10]
    
    context = {
        'storage_usage': storage_usage,
        'recommendations': recommendations,
        'recent_uploads': recent_uploads,
    }
    
    return render(request, 'image_processing/storage_status.html', context)

@login_required
def storage_cleanup_view(request):
    """Handle storage cleanup operations"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to perform storage cleanup.")
        return redirect('image_processing:list')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        days = int(request.POST.get('days', 30))
        
        try:
            if action == 'cleanup':
                # Perform actual cleanup
                storage_manager = get_storage_manager()
                result = storage_manager.cleanup_old_files(days)
                messages.success(request, f"Storage cleanup completed! Archived {result['archived_count']} files, freed {result['freed_space_mb']} MB")
            elif action == 'optimize':
                # Optimize uncompressed images
                optimize_uncompressed_images()
                messages.success(request, "Image optimization completed!")
            elif action == 'archive':
                # Archive old files
                storage_manager = get_storage_manager()
                result = storage_manager.archive_old_files(days)
                messages.success(request, f"Archived {result['archived_count']} files")
            
            return redirect('image_processing:storage_status')
            
        except Exception as e:
            messages.error(request, f"Operation failed: {str(e)}")
            return redirect('image_processing:storage_status')
    
    return render(request, 'image_processing/storage_cleanup.html')

def optimize_uncompressed_images():
    """Optimize all uncompressed images"""
    uncompressed_images = ImageUpload.objects.filter(is_compressed=False)
    
    for image in uncompressed_images:
        try:
            if image.image_file:
                # Read original file
                with image.image_file.open('rb') as f:
                    file_content = f.read()
                
                # Optimize
                optimizer = ImageOptimizer()
                optimized_content, new_size, format_used = optimizer.optimize_image(file_content)
                
                # Save optimized version
                from django.core.files.base import ContentFile
                optimized_file = ContentFile(optimized_content, f"optimized_{image.original_filename}")
                
                # Update database record
                image.image_file.save(f"optimized_{image.original_filename}", optimized_file, save=False)
                image.compressed_size = new_size
                image.is_compressed = True
                image.save()
                
        except Exception as e:
            logger.error(f"Failed to optimize image {image.id}: {e}")

@login_required
def image_delete_view(request, pk):
    """Delete an image (admin only)"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to delete images.")
        return redirect('image_processing:list')
    
    image = get_object_or_404(ImageUpload, pk=pk)
    
    if request.method == 'POST':
        try:
            # Delete the image file
            if image.image_file:
                if os.path.exists(image.image_file.path):
                    os.remove(image.image_file.path)
            
            # Delete the database record
            image.delete()
            
            messages.success(request, "Image deleted successfully!")
            return redirect('image_processing:list')
            
        except Exception as e:
            messages.error(request, f"Delete failed: {str(e)}")
    
    return render(request, 'image_processing/delete_confirm.html', {'image': image})

@login_required
def restore_archived_image(request, pk):
    """Restore an archived image to active storage"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to restore images.")
        return redirect('image_processing:list')
    
    image = get_object_or_404(ImageUpload, pk=pk)
    
    if image.storage_tier == 'ARCHIVE':
        try:
            storage_manager = get_storage_manager()
            success = storage_manager.restore_from_archive(str(image.pk))
            if success:
                messages.success(request, "Image restored successfully!")
            else:
                messages.error(request, "Failed to restore image.")
        except Exception as e:
            messages.error(request, f"Restore failed: {str(e)}")
    else:
        messages.warning(request, "This image is not archived.")
    
    return redirect('image_processing:detail', pk=pk)

# API endpoints for AJAX operations
@csrf_exempt
@require_http_methods(["POST"])
def api_upload_progress(request):
    """API endpoint for upload progress tracking"""
    # This would be implemented for real-time upload progress
    return JsonResponse({'status': 'success'})

@login_required
def api_storage_stats(request):
    """API endpoint for storage statistics"""
    storage_manager = get_storage_manager()
    stats = storage_manager.get_storage_usage()
    return JsonResponse(stats)

@login_required
def api_image_search(request):
    """API endpoint for image search"""
    query = request.GET.get('q', '')
    if query:
        images = ImageUpload.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(original_filename__icontains=query)
        )[:10]
        
        results = []
        for image in images:
            results.append({
                'id': str(image.pk),
                'title': image.title,
                'filename': image.original_filename,
                'uploaded_at': image.uploaded_at.strftime('%Y-%m-%d %H:%M'),
                'storage_tier': image.storage_tier,
                'is_compressed': image.is_compressed,
            })
        
        return JsonResponse({'results': results})
    
    return JsonResponse({'results': []})

@login_required
def review_view(request):
    """Display images ready for review"""
    if not request.user.is_staff:
        messages.error(request, "Access denied. Staff only.")
        return redirect('image_processing:list')
    
    # Get processing results ready for review (not just uploads)
    results_to_review = ImageProcessingResult.objects.filter(
        review_status=ImageProcessingResult.ReviewStatus.PENDING,
        processing_status=ImageProcessingResult.ProcessingStatus.COMPLETED
    ).select_related('image_upload', 'image_upload__uploaded_by').order_by('-created_at')
    
    # Get counts for different statuses
    pending_count = results_to_review.count()
    approved_count = ImageProcessingResult.objects.filter(
        review_status=ImageProcessingResult.ReviewStatus.APPROVED
    ).count()
    rejected_count = ImageProcessingResult.objects.filter(
        review_status=ImageProcessingResult.ReviewStatus.REJECTED
    ).count()
    overridden_count = ImageProcessingResult.objects.filter(
        review_status=ImageProcessingResult.ReviewStatus.OVERRIDDEN
    ).count()
    
    context = {
        'results_to_review': results_to_review,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'overridden_count': overridden_count,
    }
    return render(request, 'image_processing/review.html', context)

@login_required
def process_batch_view(request, pk):
    """Process a batch of images"""
    if not request.user.is_staff:
        messages.error(request, "Access denied. Staff only.")
        return redirect('image_processing:list')
    
    try:
        # Get the image to process
        image = get_object_or_404(ImageUpload, pk=pk)
        
        # Process the image
        if image.upload_status == ImageUpload.UploadStatus.UPLOADED:
            # Re-process the image
            try:
                with open(image.image_file.path, 'rb') as f:
                    file_content = f.read()
                process_image_with_storage(image, file_content)
                messages.success(request, f"Image '{image.title}' processed successfully!")
            except Exception as e:
                messages.error(request, f"Processing failed: {str(e)}")
        else:
            messages.info(request, f"Image '{image.title}' is already processed.")
        
        return redirect('image_processing:detail', pk=pk)
        
    except Exception as e:
        messages.error(request, f"Error processing image: {str(e)}")
        return redirect('image_processing:detail', pk=pk)

@login_required
def allocate_view(request):
    """Allocate approved results to census data"""
    if not request.user.is_staff:
        messages.error(request, "Access denied. Staff only.")
        return redirect('image_processing:list')
    
    # Get approved results that can be allocated
    approved_results = ImageProcessingResult.objects.filter(
        review_status__in=[
            ImageProcessingResult.ReviewStatus.APPROVED,
            ImageProcessingResult.ReviewStatus.OVERRIDDEN
        ]
    ).select_related('image_upload', 'image_upload__uploaded_by').order_by('-created_at')
    
    # Get sites for allocation (you'll need to implement this based on your sites system)
    # For now, we'll use mock data
    sites = [
        {'id': 1, 'name': 'Site A - Coastal Wetland', 'location': 'Eastern Coast'},
        {'id': 2, 'name': 'Site B - Inland Lake', 'location': 'Central Region'},
        {'id': 3, 'name': 'Site C - River Delta', 'location': 'Western Delta'},
    ]
    
    # Mock years and months for census data
    years = [2024, 2025, 2026]
    months = [
        {'id': 1, 'name': 'January', 'abbr': 'Jan'},
        {'id': 2, 'name': 'February', 'abbr': 'Feb'},
        {'id': 3, 'name': 'March', 'abbr': 'Mar'},
        {'id': 4, 'name': 'April', 'abbr': 'Apr'},
        {'id': 5, 'name': 'May', 'abbr': 'May'},
        {'id': 6, 'name': 'June', 'abbr': 'Jun'},
        {'id': 7, 'name': 'July', 'abbr': 'Jul'},
        {'id': 8, 'name': 'August', 'abbr': 'Aug'},
        {'id': 9, 'name': 'September', 'abbr': 'Sep'},
        {'id': 10, 'name': 'October', 'abbr': 'Oct'},
        {'id': 11, 'name': 'November', 'abbr': 'Nov'},
        {'id': 12, 'name': 'December', 'abbr': 'Dec'},
    ]
    
    context = {
        'approved_results': approved_results,
        'sites': sites,
        'years': years,
        'months': months,
    }
    return render(request, 'image_processing/allocate.html', context)

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def clear_upload_results(request):
    """Clear upload results from session after modal is shown"""
    if 'upload_results' in request.session:
        del request.session['upload_results']
    return JsonResponse({'status': 'success'})

@login_required
@require_http_methods(["POST"])
def approve_result(request, result_id):
    """Approve a processing result"""
    if not request.user.is_staff:
        return JsonResponse({'status': 'error', 'message': 'Access denied'}, status=403)
    
    try:
        result = get_object_or_404(ImageProcessingResult, pk=result_id)
        notes = request.POST.get('notes', '')
        
        result.approve_result(request.user, notes)
        
        return JsonResponse({
            'status': 'success',
            'message': f'Result for "{result.image_upload.title}" approved successfully!'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Error approving result: {str(e)}'
        }, status=500)

@login_required
@require_http_methods(["POST"])
def reject_result(request, result_id):
    """Reject a processing result"""
    if not request.user.is_staff:
        return JsonResponse({'status': 'error', 'message': 'Access denied'}, status=403)
    
    try:
        result = get_object_or_404(ImageProcessingResult, pk=result_id)
        notes = request.POST.get('notes', '')
        
        result.reject_result(request.user, notes)
        
        return JsonResponse({
            'status': 'success',
            'message': f'Result for "{result.image_upload.title}" rejected.'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Error rejecting result: {str(e)}'
        }, status=500)

@login_required
@require_http_methods(["POST"])
def override_result(request, result_id):
    """Override a processing result with manual classification"""
    if not request.user.is_staff:
        return JsonResponse({'status': 'error', 'message': 'Access denied'}, status=403)
    
    try:
        result = get_object_or_404(ImageProcessingResult, pk=result_id)
        new_species = request.POST.get('species')
        reason = request.POST.get('reason', '')
        
        if not new_species:
            return JsonResponse({
                'status': 'error',
                'message': 'Species is required for override'
            }, status=400)
        
        result.override_result(request.user, new_species, reason)
        
        return JsonResponse({
            'status': 'success',
            'message': f'Result for "{result.image_upload.title}" overridden with species: {new_species}'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Error overriding result: {str(e)}'
        }, status=500)

@login_required
def dashboard_view(request):
    """Display image processing dashboard with statistics and overview"""
    # Get user's images or all images if admin
    if request.user.is_staff:
        images = ImageUpload.objects.all()
    else:
        images = ImageUpload.objects.filter(uploaded_by=request.user)
    
    # Get statistics
    total_uploads = images.count()
    processed_uploads = images.filter(upload_status=ImageUpload.UploadStatus.PROCESSED).count()
    pending_review = images.filter(upload_status=ImageUpload.UploadStatus.PROCESSED).count()  # Images ready for review
    approved_results = ImageProcessingResult.objects.filter(review_status=ImageProcessingResult.ReviewStatus.APPROVED).count()
    
    # Get AI models available
    ai_models = [
        ('yolo_bird_detection', 'Bird Detection (YOLO)'),
        ('species_classification', 'Species Classification'),
        ('census_counting', 'Census Counting'),
    ]
    
    # Get recent uploads (only successful ones)
    recent_uploads = images.filter(
        upload_status__in=[
            ImageUpload.UploadStatus.PROCESSED,
            ImageUpload.UploadStatus.UPLOADED
        ]
    ).exclude(
        upload_status=ImageUpload.UploadStatus.UPLOADING  # Exclude stuck uploads
    ).order_by('-uploaded_at')[:5]
    
    # Get storage statistics
    storage_manager = get_storage_manager()
    storage_stats = storage_manager.get_storage_usage()
    
    context = {
        'total_uploads': total_uploads,
        'processed_uploads': processed_uploads,
        'pending_review': pending_review,
        'approved_results': approved_results,
        'ai_models': ai_models,
        'recent_uploads': recent_uploads,
        'storage_stats': storage_stats,
    }
    
    return render(request, 'image_processing/dashboard.html', context)

def _create_failed_processing_result(image_upload, error_message):
    """Create a failed processing result"""
    try:
        from .models import ImageProcessingResult
        import uuid
        
        if not hasattr(image_upload, 'processing_result'):
            processing_result = ImageProcessingResult.objects.create(
                id=uuid.uuid4(),
                image_upload=image_upload,
                detected_species=None,
                confidence_score=0.0,
                bounding_box={},
                total_detections=0,
                processing_status=ImageProcessingResult.ProcessingStatus.FAILED,
                ai_model='YOLO_V8',
                model_version='unknown',
                processing_device='cpu',
                inference_time=0.0,
                model_confidence_threshold=0.25,
                review_status=ImageProcessingResult.ReviewStatus.PENDING,
                review_notes=f'Processing failed: {error_message}',
                is_overridden=False
            )
            logger.info(f"Failed processing result created: {processing_result.pk}")
    except Exception as e:
        logger.error(f"Error creating failed processing result: {str(e)}")

def _create_fallback_processing_result(image_upload):
    """Create a fallback processing result when detection service is unavailable"""
    try:
        from .models import ImageProcessingResult
        import uuid
        
        if not hasattr(image_upload, 'processing_result'):
            processing_result = ImageProcessingResult.objects.create(
                id=uuid.uuid4(),
                image_upload=image_upload,
                detected_species=None,
                confidence_score=0.0,
                bounding_box={},
                total_detections=0,
                processing_status=ImageProcessingResult.ProcessingStatus.COMPLETED,
                ai_model='YOLO_V8',
                model_version='fallback',
                processing_device='cpu',
                inference_time=0.0,
                model_confidence_threshold=0.25,
                review_status=ImageProcessingResult.ReviewStatus.PENDING,
                review_notes='Detection service unavailable - manual review required',
                is_overridden=False
            )
            logger.info(f"Fallback processing result created: {processing_result.pk}")
    except Exception as e:
        logger.error(f"Error creating fallback processing result: {str(e)}")
