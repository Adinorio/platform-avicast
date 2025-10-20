"""
GTD-based Image Processing Views
Following Getting Things Done methodology for workflow management

CAPTURE → CLARIFY → ORGANIZE → REFLECT → ENGAGE
"""

import logging
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db import models, transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
import time
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from apps.users.models import UserActivity
from django.views.generic import ListView

from .forms import ImageUploadForm, ProcessingResultReviewForm, ProcessingResultOverrideForm, CensusAllocationForm
from .models import ImageUpload, ProcessingResult, ProcessingBatch, ReviewDecision
from apps.common.permissions import permission_required

# Import census models for allocation functionality
from apps.locations.models import Census, CensusYear, CensusMonth, Site

logger = logging.getLogger(__name__)


@login_required
@permission_required('can_process_images')
def dashboard(request):
    """
    CAPTURE Stage: Main dashboard showing workflow overview
    """
    # Get counts for each GTD stage
    # For admin users, show all; for field workers, show only their own
    if request.user.role in ['SUPERADMIN', 'ADMIN']:
        capture_count = ImageUpload.objects.filter(
            upload_status='CAPTURED'
        ).count()

        clarify_count = ImageUpload.objects.filter(
            upload_status='CLARIFIED'
        ).count()

        organize_count = ImageUpload.objects.filter(
            upload_status='ORGANIZED'
        ).count()

        reflect_count = ProcessingResult.objects.filter(
            review_decision=ReviewDecision.PENDING
        ).count()

        engage_count = ProcessingResult.objects.filter(
            review_decision__in=[ReviewDecision.APPROVED, ReviewDecision.OVERRIDDEN]
        ).count()
    else:
        capture_count = ImageUpload.objects.filter(
            uploaded_by=request.user,
            upload_status='CAPTURED'
        ).count()

        clarify_count = ImageUpload.objects.filter(
            uploaded_by=request.user,
            upload_status='CLARIFIED'
        ).count()

        organize_count = ImageUpload.objects.filter(
            uploaded_by=request.user,
            upload_status='ORGANIZED'
        ).count()

        reflect_count = ProcessingResult.objects.filter(
            image_upload__uploaded_by=request.user,
            review_decision=ReviewDecision.PENDING
        ).count()

        engage_count = ProcessingResult.objects.filter(
            image_upload__uploaded_by=request.user,
            review_decision__in=[ReviewDecision.APPROVED, ReviewDecision.OVERRIDDEN]
        ).count()

    # Recent activity
    if request.user.role in ['SUPERADMIN', 'ADMIN']:
        recent_uploads = ImageUpload.objects.all().order_by("-uploaded_at")[:5]
        recent_results = ProcessingResult.objects.all().order_by("-created_at")[:5]
    else:
        recent_uploads = ImageUpload.objects.filter(
            uploaded_by=request.user
        ).order_by("-uploaded_at")[:5]

        recent_results = ProcessingResult.objects.filter(
            image_upload__uploaded_by=request.user
        ).order_by("-created_at")[:5]

    context = {
        "title": "Image Processing Dashboard",
        "capture_count": capture_count,
        "clarify_count": clarify_count,
        "organize_count": organize_count,
        "reflect_count": reflect_count,
        "engage_count": engage_count,
        "recent_uploads": recent_uploads,
        "recent_results": recent_results,
    }

    return render(request, "image_processing/dashboard.html", context)


@login_required
@permission_required('can_process_images')
def upload_images(request):
    """
    CAPTURE Stage: Upload bird images for processing
    """
    if request.method == "POST":
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # Save the upload
            upload = form.save(commit=False)
            upload.uploaded_by = request.user
            upload.file_size = request.FILES["image_file"].size
            upload.original_filename = request.FILES["image_file"].name
            upload.save()

            messages.success(
                request,
                f"✅ Image '{upload.title}' captured successfully! "
                "It will be processed in the Clarify stage."
            )

            return redirect("image_processing:dashboard")
    else:
        form = ImageUploadForm()

    context = {
        "title": "Capture Images",
        "form": form,
        "stage": "capture",
    }

    return render(request, "image_processing/upload.html", context)


@login_required
def process_images(request):
    """
    CLARIFY Stage: Process uploaded images with AI
    Enhanced with better data fetching and cache management
    """
    # Get images ready for processing (Captured status)
    if request.user.role in ['SUPERADMIN', 'ADMIN']:
        pending_images = ImageUpload.objects.filter(
            upload_status='CAPTURED'
        ).select_related('uploaded_by').order_by("uploaded_at")
    else:
        pending_images = ImageUpload.objects.filter(
            uploaded_by=request.user,
            upload_status='CAPTURED'
        ).select_related('uploaded_by').order_by("uploaded_at")

    # Force fresh data by evaluating queryset
    pending_images = list(pending_images)

    if not pending_images:
        messages.info(request, "No images waiting for processing. Upload some images first!")
        return redirect("image_processing:dashboard")

    context = {
        "title": "Clarify Images",
        "pending_images": pending_images,
        "stage": "clarify",
    }

    response = render(request, "image_processing/process.html", context)

    # Add cache-busting headers to process page as well
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'

    return response


@login_required
@require_http_methods(["POST"])
def start_processing(request, image_id):
    """
    CLARIFY Stage: Start AI processing for a specific image
    Enhanced with better error handling and cache management
    """
    image = get_object_or_404(ImageUpload, id=image_id, uploaded_by=request.user)

    if image.upload_status != 'CAPTURED':
        messages.warning(request, f"⚠️ '{image.title}' is not ready for processing (status: {image.upload_status})")
        return redirect("image_processing:process")

    try:
        # Start processing
        image.start_processing()

        # Process with AI
        result = process_image_with_ai(image)

        # Ensure the result is properly saved and committed
        if not result:
            raise RuntimeError("Processing completed but no result was created")

        # Update image status to ORGANIZED
        image.complete_processing()

        messages.success(
            request,
            f"✅ '{image.title}' processed successfully! "
            f"Detected: {result.detected_species} ({result.total_detections} birds). "
            "Ready for review."
        )

        # Return JSON response for AJAX calls, or redirect for direct form submission
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                "success": True,
                "result_id": str(result.id),
                "message": f"Processing completed for '{image.title}'",
                "redirect_url": reverse("image_processing:review")
            })
        else:
            # Force redirect to review page with cache-busting parameter
            review_url = reverse("image_processing:review")
            return redirect(f"{review_url}?t={int(timezone.now().timestamp())}")

    except Exception as e:
        logger.error(f"Processing failed for image {image_id}: {e}")

        # Handle AJAX vs direct requests differently
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                "success": False,
                "error": f"Processing failed for '{image.title}': {str(e)}"
            })
        else:
            messages.error(request, f"❌ Processing failed for '{image.title}'. Please try again.")
            # On error, stay on process page
            return redirect("image_processing:process")


def process_image_with_ai(image_upload):
    """
    Process image with actual YOLO model integration
    """
    try:
        # Import here to avoid circular imports
        from .bird_detection_service import get_bird_detection_service

        # Get the bird detection service
        service = get_bird_detection_service()

        if not service.is_available():
            raise RuntimeError("Bird detection service is not available")

        # Read the image file
        with open(image_upload.image_file.path, 'rb') as f:
            image_data = f.read()

        # Run detection
        detection_result = service.detect_birds(image_data, image_upload.original_filename)

        if not detection_result["success"]:
            raise RuntimeError(f"Detection failed: {detection_result.get('error', 'Unknown error')}")

        # Store all bounding boxes (list format for multiple detections)
        all_bboxes = [d["bounding_box"] for d in detection_result["detections"]]
        
        logger.info(f"Processing {len(detection_result['detections'])} detections")
        logger.info(f"All bounding boxes: {all_bboxes}")
        
        # Create comprehensive detection data for multi-species support
        all_detections_data = []
        for detection in detection_result["detections"]:
            all_detections_data.append({
                "species": detection["species"],
                "confidence": detection["confidence"],
                "bounding_box": detection["bounding_box"],
                "id": detection["id"]
            })
            
        logger.info(f"All detections data: {len(all_detections_data)} items")
        
        # Create multi-species summary for detected_species field
        species_counts = {}
        for detection in all_detections_data:
            species = detection["species"]
            species_counts[species] = species_counts.get(species, 0) + 1
        
        # Create a summary string showing all detected species
        if species_counts:
            species_summary = ", ".join([f"{count} {species}" for species, count in species_counts.items()])
            detected_species_summary = species_summary
        else:
            detected_species_summary = "UNKNOWN"
        
        # Create processing result from detection data
        result = ProcessingResult.objects.create(
            image_upload=image_upload,
            detected_species=detected_species_summary,
            confidence_score=detection_result["primary_confidence"],
            bounding_box=all_bboxes if all_bboxes else [{"x": 0, "y": 0, "width": 0, "height": 0}],
            total_detections=detection_result["total_detections"],
            all_detections=all_detections_data,
            ai_model_used=detection_result["model_used"],
            processing_device=detection_result["device_used"],
            review_decision=ReviewDecision.PENDING,
        )

        # Update image status
        image_upload.complete_processing()

        return result

    except Exception as e:
        logger.error(f"AI processing failed for image {image_upload.id}: {e}")
        # Create a failed result for debugging
        ProcessingResult.objects.create(
            image_upload=image_upload,
            detected_species="PROCESSING_ERROR",
            confidence_score=0.0,
            bounding_box=[{"x": 0, "y": 0, "width": 0, "height": 0}],
            total_detections=0,
            ai_model_used="ERROR",
            review_decision=ReviewDecision.PENDING,
        )
        image_upload.complete_processing()
        raise


@login_required
def image_with_bbox(request, result_id):
    """
    Return image with bounding box drawn on it for visualization
    """
    result = get_object_or_404(ProcessingResult, id=result_id)

    if not result.image_upload.image_file:
        from django.http import Http404
        raise Http404("No image file available")

    # Open the image
    from PIL import Image, ImageDraw
    import io

    image_path = result.image_upload.image_file.path
    image = Image.open(image_path)

    # Draw bounding box(es) if available and valid
    if result.bounding_box and result.total_detections > 0:
        draw = ImageDraw.Draw(image)

        # Check if bounding_box is a list (multiple detections) or single dict
        if isinstance(result.bounding_box, list):
            # Multiple bounding boxes - draw all of them
            bboxes = result.bounding_box
            for idx, bbox in enumerate(bboxes):
                x, y, width, height = bbox.get('x', 0), bbox.get('y', 0), bbox.get('width', 0), bbox.get('height', 0)
                
                # Validate coordinates
                if width > 0 and height > 0:
                    # Draw rectangle (red border, 3px thick)
                    for i in range(3):  # Draw thicker line
                        draw.rectangle(
                            [x - i, y - i, x + width + i, y + height + i],
                            outline=(255, 0, 0),  # Red color
                            width=1
                        )

                    # Add label for each detection using all_detections data
                    if result.all_detections and idx < len(result.all_detections):
                        detection = result.all_detections[idx]
                        species = detection.get("species", "Unknown")
                        confidence = detection.get("confidence", 0)
                        label_text = f"{species} ({confidence:.1%})"
                    else:
                        # Fallback to old method
                        label_text = f"{result.detected_species} #{idx + 1}"

                    # Draw background for text with better contrast
                    try:
                        from PIL import ImageFont
                        # Try to load a larger font for better readability
                        try:
                            font = ImageFont.truetype("arial.ttf", 16)
                        except:
                            try:
                                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 16)
                            except:
                                font = ImageFont.load_default()
                    except:
                        font = None

                    # Get text size for background rectangle
                    if font:
                        text_bbox = draw.textbbox((x, y - 35), label_text, font=font)
                    else:
                        text_bbox = [x, y - 35, x + len(label_text) * 10, y - 15]  # Approximate

                    # Draw background rectangle with better contrast
                    draw.rectangle(text_bbox, fill=(0, 0, 0, 180))  # Semi-transparent black

                    # Draw text in white with outline for better readability
                    draw.text((x, y - 35), label_text, fill=(255, 255, 255), font=font)
        else:
            # Single bounding box (legacy format)
            bbox = result.bounding_box
            x, y, width, height = bbox.get('x', 0), bbox.get('y', 0), bbox.get('width', 0), bbox.get('height', 0)

            # Validate coordinates
            if width > 0 and height > 0:
                # Draw rectangle (red border, 3px thick)
                for i in range(3):  # Draw thicker line
                    draw.rectangle(
                        [x - i, y - i, x + width + i, y + height + i],
                        outline=(255, 0, 0),  # Red color
                        width=1
                    )

                # Add label with detection count
                label_text = f"{result.get_detected_species_display()} ({result.confidence_score:.1%})"
                if result.total_detections > 1:
                    label_text += f" + {result.total_detections - 1} more"

                # Draw semi-transparent background for text
                try:
                    from PIL import ImageFont
                    font = ImageFont.load_default()
                except:
                    font = None

                # Get text size for background rectangle
                if font:
                    text_bbox = draw.textbbox((x, y - 30), label_text, font=font)
                else:
                    text_bbox = [x, y - 30, x + len(label_text) * 12, y - 10]  # Approximate

                # Draw background rectangle
                draw.rectangle(text_bbox, fill=(255, 0, 0))

                # Draw text in white
                draw.text((x, y - 30), label_text, fill=(255, 255, 255), font=font)
    elif result.total_detections == 0:
        # No detections, add a note
        draw = ImageDraw.Draw(image)
        draw.text((10, 10), "No birds detected", fill=(255, 165, 0))  # Orange color

    # Convert to RGB if necessary (JPEG doesn't support alpha)
    if image.mode == 'RGBA':
        # Create a white background
        background = Image.new('RGB', image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[-1])  # Use alpha channel as mask
        image = background
    elif image.mode != 'RGB':
        image = image.convert('RGB')

    # Convert back to bytes
    output = io.BytesIO()
    image.save(output, format='JPEG')
    output.seek(0)

    # Return the image
    from django.http import HttpResponse
    response = HttpResponse(output.getvalue(), content_type='image/jpeg')

    # Add extremely aggressive cache-busting headers for dynamic images
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0, private'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    response['Last-Modified'] = '0'

    # Additional headers for stubborn browsers and proxies
    response['Vary'] = 'Accept-Encoding, User-Agent'
    response['X-Accel-Expires'] = '0'

    return response


@login_required
def review_results(request):
    """
    REFLECT Stage: Review AI processing results and make decisions
    Enhanced with better data fetching and cache management
    """
    # Get results that need review
    # For admin users, show all pending results; for regular users, show only their own
    if request.user.role in ['SUPERADMIN', 'ADMIN']:
        pending_results = ProcessingResult.objects.filter(
            review_decision=ReviewDecision.PENDING
        ).select_related('image_upload', 'reviewed_by').order_by("-created_at")  # Most recent first
    else:
        pending_results = ProcessingResult.objects.filter(
            image_upload__uploaded_by=request.user,
            review_decision=ReviewDecision.PENDING
        ).select_related('image_upload', 'reviewed_by').order_by("-created_at")  # Most recent first

    # Ensure we have fresh data by forcing a database query
    pending_results = list(pending_results)  # Force evaluation of queryset

    if request.method == "POST":
        result_id = request.POST.get("result_id")
        action = request.POST.get("action")

        if result_id and action:
            result = get_object_or_404(ProcessingResult, id=result_id)

            if action == "approve":
                result.approve_result(request.user, request.POST.get("notes", ""))
                messages.success(request, f"✅ Approved '{result.image_upload.title}'")

            elif action == "reject":
                result.reject_result(request.user, request.POST.get("notes", ""))
                messages.warning(request, f"❌ Rejected '{result.image_upload.title}'")

            elif action == "override":
                # Handle override form submission
                override_form = ProcessingResultOverrideForm(request.POST)
                if override_form.is_valid():
                    result.override_result(
                        reviewer=request.user,
                        new_species=override_form.cleaned_data["new_species"],
                        new_count=override_form.cleaned_data["new_count"],
                        reason=override_form.cleaned_data["override_reason"]
                    )
                    messages.success(request, f"🔄 Overrode '{result.image_upload.title}'")

            return redirect("image_processing:review")

    context = {
        "title": "Reflect on Results",
        "pending_results": pending_results,
        "stage": "reflect",
    }

    response = render(request, "image_processing/review.html", context)

    # Add extremely aggressive cache-busting headers
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0, private'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    response['Last-Modified'] = '0'

    # Additional cache-busting headers for stubborn browsers
    response['Vary'] = 'Accept-Encoding, User-Agent'
    response['X-Accel-Expires'] = '0'  # For nginx reverse proxy

    return response


@login_required
def cache_reset(request):
    """
    Provide cache reset instructions and force browser refresh
    """
    context = {
        "title": "Cache Reset - AVICAST",
        "message": "Cache reset instructions and tools",
    }

    response = render(request, "image_processing/cache_reset.html", context)

    # Force immediate cache invalidation
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'

    return response


@login_required
def review_history(request):
    """
    View detailed review history for all processed images
    """
    # Get all processed results with review information
    if request.user.role in ['SUPERADMIN', 'ADMIN']:
        reviewed_results = ProcessingResult.objects.filter(
            review_decision__in=['APPROVED', 'REJECTED', 'OVERRIDDEN']
        ).select_related('image_upload', 'reviewed_by').order_by("-reviewed_at")
    else:
        reviewed_results = ProcessingResult.objects.filter(
            image_upload__uploaded_by=request.user,
            review_decision__in=['APPROVED', 'REJECTED', 'OVERRIDDEN']
        ).select_related('image_upload', 'reviewed_by').order_by("-reviewed_at")

    context = {
        "title": "Review History",
        "reviewed_results": reviewed_results,
        "stage": "reflect",
    }
    
    return render(request, "image_processing/review_history.html", context)


@login_required
def delete_result(request, result_id):
    """
    Delete a processing result entirely (remove from system)
    """
    if request.method != "POST":
        return JsonResponse({'error': 'Only POST requests allowed'}, status=405)
    
    result = get_object_or_404(ProcessingResult, id=result_id)
    
    # Check permissions
    if request.user.role not in ['SUPERADMIN', 'ADMIN'] and result.image_upload.uploaded_by != request.user:
        messages.error(request, "❌ You don't have permission to delete this result.")
        return redirect("image_processing:allocate")
    
    try:
        # If result is allocated, delete associated census data first
        if result.image_upload.upload_status == 'ENGAGED':
            # Delete associated census observations
            from apps.locations.models import CensusObservation
            deleted_observations = CensusObservation.objects.filter(
                census__result=result
            ).delete()
            
            # Delete associated census records
            from apps.locations.models import Census
            deleted_census = Census.objects.filter(result=result).delete()
        
        # Delete the image upload (this will cascade to delete the processing result)
        image_title = result.image_upload.title
        result.image_upload.delete()
        
        messages.success(
            request,
            f"✅ Successfully deleted '{image_title}' and all associated data."
        )
        
    except Exception as e:
        logger.error(f"Failed to delete result {result_id}: {e}")
        messages.error(
            request,
            f"❌ Failed to delete result: {str(e)}"
        )
    
    return redirect("image_processing:allocate")


@login_required
def delete_allocation(request, result_id):
    """
    Delete an allocated result (remove from census data)
    """
    if request.method != "POST":
        return JsonResponse({'error': 'Only POST requests allowed'}, status=405)
    
    result = get_object_or_404(ProcessingResult, id=result_id)
    
    # Check permissions
    if request.user.role not in ['SUPERADMIN', 'ADMIN'] and result.image_upload.uploaded_by != request.user:
        messages.error(request, "❌ You don't have permission to delete this allocation.")
        return redirect("image_processing:allocate")
    
    try:
        # Check if result is actually allocated
        if result.image_upload.upload_status != 'ENGAGED':
            messages.warning(request, f"⚠️ '{result.image_upload.title}' is not allocated.")
            return redirect("image_processing:allocate")
        
        # Delete associated census observations
        from apps.locations.models import CensusObservation
        deleted_observations = CensusObservation.objects.filter(
            census__result=result
        ).delete()
        
        # Delete associated census records
        from apps.locations.models import Census
        deleted_census = Census.objects.filter(result=result).delete()
        
        # Reset the result status
        result.image_upload.upload_status = 'REFLECTED'
        result.image_upload.save()
        
        # Clear allocation fields
        result.allocated_to_site = None
        result.allocated_to_census = None
        result.allocated_at = None
        result.save()
        
        messages.success(
            request,
            f"✅ Successfully deleted allocation for '{result.image_upload.title}'. "
            f"Removed {deleted_observations[0]} observations and {deleted_census[0]} census records."
        )
        
    except Exception as e:
        logger.error(f"Failed to delete allocation for {result.image_upload.title}: {e}")
        messages.error(
            request,
            f"❌ Failed to delete allocation for '{result.image_upload.title}': {str(e)}"
        )
    
    return redirect("image_processing:allocate")


@login_required
def allocate_results(request):
    """
    ENGAGE Stage: Allocate approved results to census data
    """
    # Get results ready for allocation (only unallocated results)
    if request.user.role in ['SUPERADMIN', 'ADMIN']:
        ready_results = ProcessingResult.objects.filter(
            review_decision__in=[ReviewDecision.APPROVED, ReviewDecision.OVERRIDDEN],
            image_upload__upload_status__in=['REFLECTED', 'ORGANIZED']  # Only show unallocated results
        ).order_by("-created_at")  # Most recent first
    else:
        ready_results = ProcessingResult.objects.filter(
            image_upload__uploaded_by=request.user,
            review_decision__in=[ReviewDecision.APPROVED, ReviewDecision.OVERRIDDEN],
            image_upload__upload_status__in=['REFLECTED', 'ORGANIZED']  # Only show unallocated results
        ).order_by("-created_at")  # Most recent first

    if request.method == "POST":
        print("DEBUG: Allocation POST request received")
        result_id = request.POST.get("result_id")
        site_id = request.POST.get("site_id")
        year = request.POST.get("year")
        month = request.POST.get("month")
        observation_date = request.POST.get("observation_date")

        print(f"DEBUG: Allocation params - result_id: {result_id}, site_id: {site_id}, year: {year}, month: {month}, date: {observation_date}")

        if result_id and site_id and year and month and observation_date:
            result = get_object_or_404(ProcessingResult, id=result_id)
            site = get_object_or_404(Site, id=site_id)

            # Check if this result has already been allocated
            if result.image_upload.upload_status == 'ENGAGED':
                messages.warning(
                    request,
                    f"⚠️ '{result.image_upload.title}' has already been allocated. Please refresh the page."
                )
                return redirect("image_processing:allocate")

            # Validate that the selected month exists for the site/year
            try:
                census_year = CensusYear.objects.get(site=site, year=int(year))
                census_month = CensusMonth.objects.get(year=census_year, month=int(month))
            except (CensusYear.DoesNotExist, CensusMonth.DoesNotExist):
                messages.error(
                    request,
                    f"❌ The selected month ({month}/{year}) does not exist for site '{site.name}'. Please create the month first."
                )
                return redirect("image_processing:allocate")

            print(f"DEBUG: Found existing CensusMonth - Site: {site.name}, Year: {year}, Month: {month}")

            # Get or create census record
            census, created = Census.objects.get_or_create(
                month=census_month,
                census_date=observation_date,
                defaults={
                    'lead_observer': request.user,
                }
            )

            # Log allocation details for debugging
            print(f"DEBUG: Allocation - Site: {site.name}, Date: {observation_date}, Count: {result.final_count}")
            print(f"DEBUG: Census record {'CREATED' if created else 'UPDATED'} - ID: {census.id}")

            print(f"DEBUG: Processing multi-species allocation for Census ID: {census.id}")

            # Handle multi-species allocation from all_detections data
            from apps.locations.models import CensusObservation
            from apps.fauna.models import Species

            species_counts = {}  # Track counts per species

            # Check if all_detections exists and has data (new multi-species format)
            if result.all_detections and len(result.all_detections) > 0:
                print(f"DEBUG: Processing {len(result.all_detections)} detections from all_detections")

                # Process each detection in all_detections
                for detection in result.all_detections:
                    species_name = detection["species"]
                    count = 1  # Each detection represents one bird

                    # Validate that the species exists in the fauna management system
                    try:
                        # Try to find the species by name or scientific name with flexible matching
                        species = Species.objects.get(
                            models.Q(name__icontains=species_name) |
                            models.Q(scientific_name__icontains=species_name) |
                            models.Q(name__iexact=species_name) |
                            models.Q(scientific_name__iexact=species_name)
                        )
                        validated_species_name = species.name
                        print(f"DEBUG: Found species in database - {validated_species_name}")
                    except Species.DoesNotExist:
                        # Try more flexible matching for common names
                        try:
                            # Handle common name variations
                            if "chinese egret" in species_name.lower():
                                species = Species.objects.filter(name__icontains="CHINESE").filter(name__icontains="EGRET").first()
                                if not species:
                                    species = Species.objects.filter(name__icontains="CHINESE").first()
                            elif "little egret" in species_name.lower():
                                species = Species.objects.filter(name__icontains="LITTLE EGRET").first()
                            elif "great egret" in species_name.lower():
                                species = Species.objects.filter(name__icontains="GREAT EGRET").first()
                            elif "intermediate egret" in species_name.lower():
                                species = Species.objects.filter(name__icontains="INTERMEDIATE EGRET").first()
                            elif "cattle egret" in species_name.lower():
                                species = Species.objects.filter(name__icontains="CATTLE EGRET").first()
                            else:
                                raise Species.DoesNotExist
                            
                            if species:
                                validated_species_name = species.name
                                print(f"DEBUG: Found species via flexible matching - {validated_species_name}")
                            else:
                                raise Species.DoesNotExist
                        except Species.DoesNotExist:
                            # If species doesn't exist in database, show error
                            messages.error(
                                request,
                                f"❌ Species '{species_name}' is not registered in the fauna management system. Please add it first."
                            )
                            return redirect("image_processing:allocate")
                    except Species.MultipleObjectsReturned:
                        # If multiple species match, use the first one
                        species = Species.objects.filter(
                            models.Q(name__icontains=species_name) |
                            models.Q(scientific_name__icontains=species_name) |
                            models.Q(name__iexact=species_name) |
                            models.Q(scientific_name__iexact=species_name)
                        ).first()
                        validated_species_name = species.name if species.name else species_name
                        print(f"DEBUG: Multiple species found, using: {validated_species_name}")

                    # Accumulate counts per species
                    if validated_species_name not in species_counts:
                        species_counts[validated_species_name] = 0
                    species_counts[validated_species_name] += count

            else:
                # Fallback to single-species logic for backward compatibility
                print(f"DEBUG: Using legacy single-species logic for backward compatibility")

                # Validate the primary detected species
                primary_species = result.detected_species if result.detected_species != "UNKNOWN" else None

                if primary_species:
                    try:
                        # Try to find the species by name or scientific name with flexible matching
                        species = Species.objects.get(
                            models.Q(name__icontains=primary_species) |
                            models.Q(scientific_name__icontains=primary_species) |
                            models.Q(name__iexact=primary_species) |
                            models.Q(scientific_name__iexact=primary_species)
                        )
                        validated_species_name = species.name
                        print(f"DEBUG: Found species in database - {validated_species_name}")
                    except Species.DoesNotExist:
                        # Try more flexible matching for common names
                        try:
                            if "chinese egret" in primary_species.lower():
                                species = Species.objects.filter(name__icontains="CHINESE").filter(name__icontains="EGRET").first()
                                if not species:
                                    species = Species.objects.filter(name__icontains="CHINESE").first()
                            elif "little egret" in primary_species.lower():
                                species = Species.objects.filter(name__icontains="LITTLE EGRET").first()
                            elif "great egret" in primary_species.lower():
                                species = Species.objects.filter(name__icontains="GREAT EGRET").first()
                            elif "intermediate egret" in primary_species.lower():
                                species = Species.objects.filter(name__icontains="INTERMEDIATE EGRET").first()
                            elif "cattle egret" in primary_species.lower():
                                species = Species.objects.filter(name__icontains="CATTLE EGRET").first()
                            else:
                                raise Species.DoesNotExist
                            
                            if species:
                                validated_species_name = species.name
                                print(f"DEBUG: Found species via flexible matching - {validated_species_name}")
                            else:
                                raise Species.DoesNotExist
                        except Species.DoesNotExist:
                            messages.error(
                                request,
                                f"❌ Species '{primary_species}' is not registered in the fauna management system. Please add it first."
                            )
                            return redirect("image_processing:allocate")
                    except Species.MultipleObjectsReturned:
                        species = Species.objects.filter(
                            models.Q(name__icontains=primary_species) |
                            models.Q(scientific_name__icontains=primary_species) |
                            models.Q(name__iexact=primary_species) |
                            models.Q(scientific_name__iexact=primary_species)
                        ).first()
                        validated_species_name = species.name if species.name else primary_species
                        print(f"DEBUG: Multiple species found, using: {validated_species_name}")

                    # Single species case
                    species_counts[validated_species_name] = result.total_detections

            # Create CensusObservation records for each species
            created_observations = []
            for species_name, total_count in species_counts.items():
                try:
                    # Check if we already have an observation for this species on this date
                    observation, obs_created = CensusObservation.objects.get_or_create(
                        census=census,
                        species_name=species_name,
                        defaults={
                            'count': total_count,
                            'family': 'Ardeidae',  # Heron/egret family
                        }
                    )

                    if not obs_created:
                        # Update existing observation count
                        old_count = observation.count
                        observation.count += total_count
                        observation.save()
                        print(f"DEBUG: Updated CensusObservation - Species: {species_name}, Old count: {old_count}, New count: {observation.count}")
                    else:
                        print(f"DEBUG: Created CensusObservation - Species: {species_name}, Count: {observation.count}")

                    created_observations.append((species_name, total_count, obs_created))

                except Exception as e:
                    print(f"ERROR: Failed to create CensusObservation for {species_name} - {e}")

            print(f"DEBUG: Created {len(created_observations)} CensusObservation records")
            for species_name, count, was_created in created_observations:
                print(f"  - {species_name}: {count} birds ({'CREATED' if was_created else 'UPDATED'})")

            # The census totals will be automatically updated via the CensusObservation save() method
            print(f"DEBUG: Census ID {census.id} - Before save: Birds: {census.total_birds}, Species: {census.total_species}")

            # Refresh census from database to see updated totals
            census.refresh_from_db()
            print(f"DEBUG: Census ID {census.id} - After refresh: Birds: {census.total_birds}, Species: {census.total_species}")

            # Create allocation history record for tracking (temporarily disabled until migration is applied)
            # from apps.locations.models import AllocationHistory
            # AllocationHistory.objects.create(
            #     processing_result=result,
            #     census=census_observation,
            #     allocated_by=request.user,
            #     bird_count=result.final_count,
            #     site=site,
            #     observation_date=observation_date,
            #     notes=f"Allocated via image processing - {result.image_upload.title}"
            # )

            # Update processing result status to show it's been allocated
            result.allocate_to_census(site=site, census=census, allocated_by=request.user)

            # Log the allocation activity
            UserActivity.log_activity(
                user=request.user,
                activity_type=UserActivity.ActivityType.CENSUS_ADDED,
                description=f"Allocated image processing result to census: {result.image_upload.title} -> {site.name} ({census_year.year} {census_month.get_month_display()})",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                metadata={
                    'processing_result_id': str(result.id),
                    'image_title': result.image_upload.title,
                    'site_id': str(site.id),
                    'site_name': site.name,
                    'census_id': str(census.id),
                    'census_date': str(census.census_date),
                    'species_allocated': list(species_counts.keys()),
                    'total_birds': sum(species_counts.values()),
                    'allocation_details': {
                        'year': census_year.year,
                        'month': census_month.month,
                        'month_display': census_month.get_month_display(),
                    }
                }
            )

            # Create success message with species details
            species_details = []
            for species_name, count in species_counts.items():
                species_details.append(f"{count} {species_name}")
            
            species_summary = ", ".join(species_details)
            
            messages.success(
                request,
                f"✅ Successfully allocated '{result.image_upload.title}' ({species_summary}) to census record at {site.name} - {census_year.year} {census_month.get_month_display()}"
            )

            return redirect("image_processing:allocate")

    # Get available sites for allocation
    available_sites = Site.objects.filter(status="active")

    # Get all available years across all sites (for initial load)
    years_query = CensusYear.objects.values_list('year', flat=True).order_by('-year')
    all_years_list = list(dict.fromkeys(years_query))  # Remove duplicates while preserving order

    # Get all available months across all sites (for initial load)
    months_query = CensusMonth.objects.values_list('month', flat=True).order_by('month')
    all_months_list = list(dict.fromkeys(months_query))  # Remove duplicates while preserving order

    # Get current year for default selection
    current_year = timezone.now().year

    context = {
        "title": "Engage with Census",
        "ready_results": ready_results,
        "available_sites": available_sites,
        "all_years": all_years_list,
        "all_months": all_months_list,
        "current_year": current_year,
        "stage": "engage",
    }

    return render(request, "image_processing/allocate.html", context)


@login_required
def get_years_for_site(request, site_id):
    """AJAX endpoint to get years for a specific site"""
    if request.method == 'GET':
        site = get_object_or_404(Site, id=site_id, status="active")
        years = CensusYear.objects.filter(site=site).values_list('year', flat=True).order_by('-year')
        years_list = list(years)
        return JsonResponse({'years': years_list})
    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def get_months_for_site_year(request, site_id, year):
    """AJAX endpoint to get months for a specific site and year"""
    if request.method == 'GET':
        site = get_object_or_404(Site, id=site_id, status="active")
        months = CensusMonth.objects.filter(
            year__site=site,
            year__year=int(year)
        ).values_list('month', flat=True).order_by('month')
        months_list = list(months)
        return JsonResponse({'months': months_list})
    return JsonResponse({'error': 'Invalid request'}, status=400)


class ImageListView(LoginRequiredMixin, ListView):
    """
    ORGANIZE Stage: List view for organizing images by workflow stage
    """
    model = ImageUpload
    template_name = "image_processing/list.html"
    context_object_name = "images"
    paginate_by = 20

    def get_queryset(self):
        """Filter images based on workflow stage"""
        stage = self.request.GET.get("stage", "all")
        if self.request.user.role in ['SUPERADMIN', 'ADMIN']:
            queryset = ImageUpload.objects.all()
        else:
            queryset = ImageUpload.objects.filter(uploaded_by=self.request.user)

        if stage == "captured":
            queryset = queryset.filter(upload_status='CAPTURED')
        elif stage == "clarified":
            queryset = queryset.filter(upload_status='CLARIFIED')
        elif stage == "organized":
            queryset = queryset.filter(upload_status='ORGANIZED')
        elif stage == "reflected":
            # Images that have been reviewed
            queryset = queryset.filter(processing_result__review_decision__in=[
                'REFLECTED', 'ENGAGED'
            ])
        elif stage == "engaged":
            queryset = queryset.filter(upload_status='ENGAGED')

        return queryset.order_by("-uploaded_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["current_stage"] = self.request.GET.get("stage", "all")
        if self.request.user.role in ['SUPERADMIN', 'ADMIN']:
            context["stage_counts"] = {
                "all": ImageUpload.objects.all().count(),
                "captured": ImageUpload.objects.filter(
                    upload_status='CAPTURED'
                ).count(),
                "clarified": ImageUpload.objects.filter(
                    upload_status='CLARIFIED'
                ).count(),
                "organized": ImageUpload.objects.filter(
                    upload_status='ORGANIZED'
                ).count(),
                "reflected": ProcessingResult.objects.filter(
                    review_decision__in=[ReviewDecision.APPROVED, ReviewDecision.REJECTED, ReviewDecision.OVERRIDDEN]
                ).count(),
                "engaged": ProcessingResult.objects.filter(
                    review_decision__in=[ReviewDecision.APPROVED, ReviewDecision.OVERRIDDEN]
                ).count(),
            }
        else:
            context["stage_counts"] = {
                "all": ImageUpload.objects.filter(uploaded_by=self.request.user).count(),
                "captured": ImageUpload.objects.filter(
                    uploaded_by=self.request.user, upload_status='CAPTURED'
                ).count(),
                "clarified": ImageUpload.objects.filter(
                    uploaded_by=self.request.user, upload_status='CLARIFIED'
                ).count(),
                "organized": ImageUpload.objects.filter(
                    uploaded_by=self.request.user, upload_status='ORGANIZED'
                ).count(),
                "reflected": ProcessingResult.objects.filter(
                    image_upload__uploaded_by=self.request.user,
                    review_decision__in=[ReviewDecision.APPROVED, ReviewDecision.REJECTED, ReviewDecision.OVERRIDDEN]
                ).count(),
                "engaged": ProcessingResult.objects.filter(
                    image_upload__uploaded_by=self.request.user,
                    review_decision__in=[ReviewDecision.APPROVED, ReviewDecision.OVERRIDDEN]
                ).count(),
            }
        return context


@login_required
def model_selection(request):
    """
    Model Management: Select and configure AI models for bird detection
    """
    # Get available models from the models directory
    import os
    from django.conf import settings
    
    models_dir = os.path.join(settings.BASE_DIR, "models")
    available_models = []
    
    if os.path.exists(models_dir):
        for model_name in os.listdir(models_dir):
            model_path = os.path.join(models_dir, model_name)
            if os.path.isdir(model_path):
                # Check for model files
                model_files = [f for f in os.listdir(model_path) if f.endswith(('.pt', '.pth', '.onnx'))]
                if model_files:
                    available_models.append({
                        'name': model_name,
                        'files': model_files,
                        'path': model_path
                    })
    
    # Get current active model (you might store this in settings or database)
    current_model = getattr(settings, 'ACTIVE_BIRD_MODEL', 'egret_500_model')
    
    context = {
        "title": "Model Management",
        "available_models": available_models,
        "current_model": current_model,
    }
    
    return render(request, "image_processing/model_selection.html", context)


@login_required
def benchmark_models(request):
    """
    Model Benchmarking: Test and compare AI model performance
    """
    # Get model performance data (this would come from your benchmarking system)
    model_performance = [
        {
            'name': 'egret_500_model',
            'accuracy': 0.6828,
            'precision': 0.6791,
            'recall': 0.6099,
            'f1_score': 0.6428,
            'inference_time': 0.0134,
            'status': 'active'
        },
        {
            'name': 'yolov8n_birds',
            'accuracy': 0.87,
            'precision': 0.84,
            'recall': 0.82,
            'f1_score': 0.83,
            'inference_time': 0.08,
            'status': 'available'
        }
    ]
    
    context = {
        "title": "Model Benchmarking",
        "model_performance": model_performance,
    }
    
    return render(request, "image_processing/benchmark.html", context)
