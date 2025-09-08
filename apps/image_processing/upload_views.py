"""
Views for image upload functionality
"""

import io
import logging
import os

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .forms import ImageUploadForm
from .models import ImageProcessingResult, ImageUpload
from .permissions import admin_required, can_access_image
from .utils import calculate_file_hash, create_auto_title, generate_unique_filename

logger = logging.getLogger(__name__)


@login_required
def image_upload_view(request):
    """Handle image upload - separate from processing"""
    if request.method == "POST":
        if settings.DEBUG:
            logger.info(f"POST request received with FILES: {request.FILES}")
            logger.info(f"POST data: {request.POST}")
            logger.info(f"User: {request.user}, Authenticated: {request.user.is_authenticated}")

        form = ImageUploadForm(request.POST, request.FILES)
        if settings.DEBUG:
            logger.info(f"Form created, is_valid: {form.is_valid()}")
        if not form.is_valid():
            if settings.DEBUG:
                logger.warning(f"FORM VALIDATION FAILED - Form errors: {form.errors}")
                logger.warning(f"POST data: {request.POST}")
                logger.warning(f"FILES data: {list(request.FILES.keys())}")

        if form.is_valid():
            try:
                # Get uploaded files (now supports multiple)
                image_files = request.FILES.getlist("image_file")
                logger.info(f"Uploading {len(image_files)} image(s)")

                if not image_files:
                    messages.error(request, "No images selected for upload.")
                    return redirect("image_processing:upload")

                # Handle single file case (backward compatibility)
                if len(image_files) == 1:
                    image_files = [image_files[0]]

                uploaded_images = []

                for i, image_file in enumerate(image_files, 1):
                    if settings.DEBUG:
                        logger.info(
                            f"Processing upload {i}/{len(image_files)}: {image_file.name}, size: {image_file.size}, type: {image_file.content_type}"
                        )

                    # Calculate file hash for deduplication
                    file_content = image_file.read()
                    file_hash = calculate_file_hash(file_content)
                    if settings.DEBUG:
                        logger.info(f"File hash calculated: {file_hash[:10]}...")

                    # Check for duplicates - allow re-uploads with different metadata
                    if settings.DEBUG:
                        logger.info(f"Checking for duplicates for file: {image_file.name}")
                    try:
                        existing_images = ImageUpload.objects.filter(file_hash=file_hash)
                        if settings.DEBUG:
                            logger.info(
                                f"Query result: {existing_images.count()} existing images with same hash"
                            )
                        if existing_images.exists():
                            if settings.DEBUG:
                                logger.info(
                                    f"Found {existing_images.count()} existing image(s) with same hash"
                                )

                            # Check if this is a true duplicate (same user, same title, recent upload)
                            recent_duplicate = existing_images.filter(
                                uploaded_by=request.user,
                                title__icontains=form.cleaned_data.get("title", ""),
                                uploaded_at__gte=timezone.now()
                                - timezone.timedelta(hours=settings.IMAGE_CONFIG["DUPLICATE_CHECK_HOURS"]),
                            ).first()

                            if recent_duplicate:
                                logger.info(f"Recent duplicate detected: {recent_duplicate.pk}")
                                logger.info(
                                    f"Duplicate details - Title: '{recent_duplicate.title}', User: {recent_duplicate.uploaded_by}, Time: {recent_duplicate.uploaded_at}"
                                )

                                # Add detailed warning message
                                messages.warning(
                                    request,
                                    f"""
                                <strong>Duplicate Image Detected!</strong><br>
                                You uploaded this exact image '{image_file.name}' recently with the title '{recent_duplicate.title}'.
                                <br><br>
                                <strong>Options:</strong>
                                <ul>
                                    <li>View the existing image: <a href="{reverse('image_processing:detail', args=[recent_duplicate.pk])}" class="alert-link">Click here</a></li>
                                    <li>Upload with a different title to create a new entry</li>
                                    <li>Skip this file and continue with others</li>
                                </ul>
                                """.strip(),
                                )

                                # Instead of redirecting, continue to show the upload form with the warning
                                # Remove this file from processing and continue with others
                                continue
                            else:
                                logger.info(
                                    "Allowing re-upload of same image with different metadata"
                                )
                                # Generate unique filename to avoid conflicts
                                unique_filename = generate_unique_filename(image_file.name)
                                logger.info(f"Generated unique filename: {unique_filename}")

                                messages.info(
                                    request,
                                    f"Image '{image_file.name}' was previously uploaded, but you can upload it again with different title/description.",
                                )

                                # Update the filename to avoid conflicts
                                image_file.name = unique_filename

                        logger.info("Proceeding with upload...")
                    except Exception as e:
                        logger.error(f"Error checking duplicates: {str(e)}")
                        # Continue with upload if duplicate check fails
                        logger.warning("Continuing with upload despite duplicate check error...")

                    # Reset file pointer for saving
                    logger.info("Resetting file pointer...")
                    image_file.seek(0)

                    # Create image upload record - ONLY UPLOAD, NO PROCESSING
                    logger.info(f"Creating ImageUpload object for {image_file.name}...")
                    image_upload = ImageUpload()
                    image_upload.uploaded_by = request.user
                    image_upload.file_size = image_file.size
                    image_upload.file_type = image_file.content_type
                    image_upload.file_hash = file_hash
                    image_upload.original_filename = image_file.name
                    image_upload.upload_status = (
                        ImageUpload.UploadStatus.UPLOADED
                    )  # Just uploaded, not processed

                    # Use form data for title/description if provided
                    if form.cleaned_data.get("title"):
                        image_upload.title = form.cleaned_data.get("title")
                    else:
                        # Auto-generate title from filename
                        image_upload.title = create_auto_title(image_file.name)

                    if form.cleaned_data.get("description"):
                        image_upload.description = form.cleaned_data.get("description")

                    # Save original file
                    logger.info("Saving original file...")
                    image_upload.image_file.save(image_file.name, image_file, save=False)
                    image_upload.save()
                    logger.info(
                        f"Original file saved: {image_upload.image_file.path if hasattr(image_upload.image_file, 'path') else 'No path'}"
                    )

                    # Add to uploaded images list
                    uploaded_images.append(image_upload)

                # Handle post-upload routing and feedback
                if uploaded_images:
                    # Store upload results in session for modal display
                    request.session["upload_results"] = {
                        "total": len(uploaded_images),
                        "uploaded_ids": [str(img.pk) for img in uploaded_images],
                    }

                    # Success message and redirect
                    if len(uploaded_images) == 1:
                        messages.success(
                            request,
                            f"Image '{uploaded_images[0].title}' uploaded successfully! Ready for processing.",
                        )
                    else:
                        messages.success(
                            request,
                            f"{len(uploaded_images)} images uploaded successfully! Ready for processing.",
                        )

                    # Redirect to list with status filter to show uploaded images
                    logger.info(
                        f"EXECUTING FINAL REDIRECT: Redirecting to list page with {len(uploaded_images)} uploaded images"
                    )
                    logger.info(
                        f"Session data being set: {request.session.get('upload_results', 'NOT SET')}"
                    )
                    return redirect("image_processing:list")  # Go to list to see uploaded images
                else:
                    messages.error(request, "No images were uploaded successfully.")
                    return redirect("image_processing:upload")

            except Exception as e:
                import traceback

                error_details = traceback.format_exc()
                logger.error(f"UNCAUGHT UPLOAD ERROR: {str(e)}")
                logger.error(f"Error type: {type(e).__name__}")
                logger.error(f"Traceback: {error_details}")
                messages.error(request, f"Upload failed: {str(e)}")
                logger.warning("REDIRECTING TO UPLOAD PAGE DUE TO ERROR")
                return redirect("image_processing:upload")
    else:
        form = ImageUploadForm()

    return render(request, "image_processing/upload.html", {"form": form})


@login_required
def image_list_view(request):
    """Display list of uploaded images with storage information"""
    # Get user's images or all images if admin
    if request.user.is_staff:
        images = ImageUpload.objects.all()
    else:
        images = ImageUpload.objects.filter(uploaded_by=request.user)

    # Search functionality
    search_query = request.GET.get("search", "")
    if search_query:
        images = images.filter(
            Q(title__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(original_filename__icontains=search_query)
        )

    # Filter by upload status
    status = request.GET.get("status", "")
    if status:
        images = images.filter(upload_status=status)

    # Filter by storage tier
    storage_tier = request.GET.get("storage_tier", "")
    if storage_tier:
        images = images.filter(storage_tier=storage_tier)

    # Filter by compression status
    compression_status = request.GET.get("compression_status", "")
    if compression_status == "compressed":
        images = images.filter(is_compressed=True)
    elif compression_status == "uncompressed":
        images = images.filter(is_compressed=False)

    # Pagination
    paginator = Paginator(images, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Get storage statistics
    from .local_storage import LocalStorageManager
    storage_manager = LocalStorageManager()
    storage_stats = storage_manager.get_storage_usage()

    context = {
        "page_obj": page_obj,
        "search_query": search_query,
        "status": status,
        "storage_tier": storage_tier,
        "compression_status": compression_status,
        "storage_stats": storage_stats,
        "total_images": images.count(),
        "compressed_images": images.filter(is_compressed=True).count(),
        "uncompressed_images": images.filter(is_compressed=False).count(),
        # Utility functions for templates
        "get_best_image_url": get_best_image_url,
        "get_thumbnail_url": get_thumbnail_url,
    }

    return render(request, "image_processing/list.html", context)


def get_best_image_url(image_upload):
    """
    Get the best available image URL for display.
    Returns optimized version if available, otherwise original.
    """
    if image_upload.optimized_image:
        return image_upload.optimized_image.url
    elif image_upload.image_file:
        return image_upload.image_file.url
    return None


def get_thumbnail_url(image_upload):
    """
    Get thumbnail URL, with fallbacks.
    """
    if image_upload.thumbnail:
        return image_upload.thumbnail.url
    elif image_upload.optimized_image:
        return image_upload.optimized_image.url
    elif image_upload.image_file:
        return image_upload.image_file.url
    return None


@login_required
def image_detail_view(request, pk):
    """Display detailed view of an image with storage information"""
    image = get_object_or_404(ImageUpload, pk=pk)

    # Check if user can view this image
    if not can_access_image(request.user, image):
        messages.error(request, "You don't have permission to view this image.")
        return redirect("image_processing:list")

    # Get processing result if exists
    try:
        processing_result = image.processing_result
    except ImageProcessingResult.DoesNotExist:
        processing_result = None

    # Generate image with bounding boxes if processing result exists
    processed_image_url = None
    if processing_result and processing_result.bounding_box and image.image_file:
        try:
            from .visualization_utils import draw_detections_on_image

            # Read the original image
            with image.image_file.open("rb") as f:
                image_content = f.read()

            # Get the actual dimensions that the AI model processed
            # Since we're using file_content (original image), the AI processed the original dimensions
            from PIL import Image

            original_image = Image.open(io.BytesIO(image_content))
            ai_dimensions = original_image.size  # Use actual original image dimensions
            logger.info(f"AI processed original image dimensions: {ai_dimensions}")

            # CRITICAL FIX: Always use the actual image dimensions for visualization
            # The AI model always processes the original image, regardless of what's stored
            # This fixes the issue where old processed images had wrong ai_dimensions (640x640)
            # stored but the AI actually processed the original image dimensions
            if processing_result.bounding_box.get("ai_dimensions"):
                stored_ai_dims = processing_result.bounding_box["ai_dimensions"]
                logger.info(
                    f"Stored AI dimensions: {stored_ai_dims}, Actual image dimensions: {ai_dimensions}"
                )

                # Convert both to tuples for consistent comparison
                stored_dims_tuple = (
                    tuple(stored_ai_dims) if isinstance(stored_ai_dims, list) else stored_ai_dims
                )
                actual_dims_tuple = (
                    tuple(ai_dimensions) if isinstance(ai_dimensions, list) else ai_dimensions
                )

                if stored_dims_tuple != actual_dims_tuple:
                    logger.warning(
                        f"AI dimensions mismatch detected! Stored: {stored_ai_dims}, Actual: {ai_dimensions}"
                    )
                    logger.info(
                        "Using ACTUAL image dimensions for visualization (AI always processes original image)"
                    )
                    # Keep ai_dimensions as the actual image dimensions (correct)
                else:
                    logger.info(
                        f"AI dimensions match - using actual image dimensions: {ai_dimensions}"
                    )
            else:
                logger.info(
                    f"No stored AI dimensions found - using actual image dimensions: {ai_dimensions}"
                )

            # Prepare detections for visualization
            detections = []
            if processing_result.bounding_box.get("all_detections"):
                logger.info(
                    f"Processing {len(processing_result.bounding_box['all_detections'])} detections for visualization"
                )
                for i, detection in enumerate(processing_result.bounding_box["all_detections"], 1):
                    bbox = detection.get("bounding_box", {})
                    logger.info(f"Detection {i}: species={detection.get('species')}, bbox={bbox}")
                    detections.append(
                        {
                            "species": detection.get("species", "Bird"),
                            "confidence": detection.get("confidence", 0.0),
                            "bounding_box": bbox,
                        }
                    )

            # Get the actual image dimensions for debugging
            display_width, display_height = original_image.size
            logger.info(f"Display image size: {display_width}x{display_height}")

            # Draw detections on image using actual AI dimensions
            # ai_dimensions now contains the ACTUAL image dimensions (not stored wrong dimensions)
            processed_image_bytes = draw_detections_on_image(
                image_content,
                detections,
                output_format="bytes",
                ai_processing_size=ai_dimensions,  # Use actual AI processing dimensions for accurate scaling
            )

            # Save processed image temporarily
            import os
            import uuid

            from django.core.files.base import ContentFile
            from django.core.files.storage import default_storage

            # Ensure temp directory exists
            temp_dir = os.path.join(settings.MEDIA_ROOT, "temp")
            os.makedirs(temp_dir, exist_ok=True)

            # Create a temporary filename with PNG extension to handle RGBA images
            temp_filename = f"processed_{uuid.uuid4().hex[:8]}.png"
            temp_path = f"temp/{temp_filename}"

            # Save to temporary storage
            processed_image_url = default_storage.save(
                temp_path, ContentFile(processed_image_bytes)
            )

            # Store the temp file path in session for cleanup
            if not hasattr(request, "session"):
                request.session = {}
            temp_files = request.session.get("temp_processed_images", [])
            temp_files.append(processed_image_url)
            # Keep only last 10 temp files
            if len(temp_files) > 10:
                temp_files = temp_files[-10:]
            request.session["temp_processed_images"] = temp_files

        except Exception as e:
            logger.error(f"Error generating processed image: {e}")
            processed_image_url = None

    # Get storage information
    storage_info = image.get_storage_info()

    # Get optimization statistics
    optimization_stats = None
    if hasattr(image, 'original_size') and hasattr(image, 'optimized_size'):
        if image.original_size and image.optimized_size:
            from apps.common.services.image_optimizer import UniversalImageOptimizer
            optimizer = UniversalImageOptimizer()
            optimization_stats = optimizer.get_optimization_stats(
                image.original_size, image.optimized_size
            )

    context = {
        "image_upload": image,
        "processing_result": processing_result,
        "storage_info": storage_info,
        "processed_image_url": processed_image_url,
        # Optimized image URLs
        "optimized_image_url": get_best_image_url(image),
        "thumbnail_url": get_thumbnail_url(image),
        "original_image_url": image.image_file.url if image.image_file else None,
        # Optimization information
        "optimization_stats": optimization_stats,
        "is_optimized": image.optimization_status == 'completed' and bool(image.optimized_image),
        "has_thumbnail": bool(image.thumbnail),
        "has_ai_processed": bool(image.ai_processed_image),
    }

    return render(request, "image_processing/detail.html", context)


@admin_required
def image_delete_view(request, pk):
    """Delete an image (admin only)"""
    image = get_object_or_404(ImageUpload, pk=pk)

    if request.method == "POST":
        try:
            # Delete the image file
            if image.image_file:
                if os.path.exists(image.image_file.path):
                    os.remove(image.image_file.path)

            # Delete the database record
            image.delete()

            messages.success(request, "Image deleted successfully!")
            return redirect("image_processing:list")

        except Exception as e:
            messages.error(request, f"Delete failed: {str(e)}")

    return render(request, "image_processing/delete_confirm.html", {"image": image})


@admin_required
def restore_archived_image(request, pk):
    """Restore an archived image to active storage"""
    image = get_object_or_404(ImageUpload, pk=pk)

    if image.storage_tier == "ARCHIVE":
        try:
            from .local_storage import LocalStorageManager
            storage_manager = LocalStorageManager()
            success = storage_manager.restore_from_archive(str(image.pk))
            if success:
                messages.success(request, "Image restored successfully!")
            else:
                messages.error(request, "Failed to restore image.")
        except Exception as e:
            messages.error(request, f"Restore failed: {str(e)}")
    else:
        messages.warning(request, "This image is not archived.")

    return redirect("image_processing:detail", pk=pk)


# API endpoints for upload operations
@csrf_exempt
@require_http_methods(["POST"])
@login_required
def api_upload_progress(request):
    """API endpoint for upload progress tracking"""
    # This would be implemented for real-time upload progress
    return JsonResponse({"status": "success"})


@login_required
def api_storage_stats(request):
    """API endpoint for storage statistics"""
    from .local_storage import LocalStorageManager
    storage_manager = LocalStorageManager()
    stats = storage_manager.get_storage_usage()
    return JsonResponse(stats)


@login_required
def api_image_search(request):
    """API endpoint for image search"""
    query = request.GET.get("q", "")
    if query:
        images = ImageUpload.objects.filter(
            Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(original_filename__icontains=query)
        )[:10]

        results = []
        for image in images:
            results.append(
                {
                    "id": str(image.pk),
                    "title": image.title,
                    "filename": image.original_filename,
                    "uploaded_at": image.uploaded_at.strftime("%Y-%m-%d %H:%M"),
                    "storage_tier": image.storage_tier,
                    "is_compressed": image.is_compressed,
                }
            )

        return JsonResponse({"results": results})

    return JsonResponse({"results": []})


@login_required
def api_get_progress(request):
    """API endpoint to get processing progress for images"""
    image_ids = request.GET.getlist("image_ids[]", [])

    if not image_ids:
        return JsonResponse({"error": "No image IDs provided"})

    try:
        images = ImageUpload.objects.filter(pk__in=image_ids)

        progress_data = []
        for image in images:
            progress_data.append(
                {
                    "id": str(image.pk),
                    "status": image.upload_status,
                    "step": image.processing_step,
                    "step_display": image.get_processing_step_display()
                    if image.processing_step
                    else "",
                    "progress": image.processing_progress,
                    "started_at": image.processing_started_at.isoformat()
                    if image.processing_started_at
                    else None,
                    "completed_at": image.processing_completed_at.isoformat()
                    if image.processing_completed_at
                    else None,
                    "duration": str(image.processing_duration)
                    if image.processing_duration
                    else None,
                }
            )

        return JsonResponse({"success": True, "images": progress_data})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@login_required
def api_progress(request, image_id):
    """API endpoint to get progress for a single image"""
    try:
        image = get_object_or_404(ImageUpload, pk=image_id)

        # Check if user can view this image
        if not can_access_image(request.user, image):
            return JsonResponse({"error": "Permission denied"}, status=403)

        return JsonResponse(
            {
                "id": str(image.pk),
                "status": image.upload_status,
                "step": image.processing_step,
                "step_display": image.get_processing_step_display()
                if image.processing_step
                else "",
                "progress": image.processing_progress,
                "started_at": image.processing_started_at.isoformat()
                if image.processing_started_at
                else None,
                "completed_at": image.processing_completed_at.isoformat()
                if image.processing_completed_at
                else None,
                "duration": str(image.processing_duration) if image.processing_duration else None,
            }
        )

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
