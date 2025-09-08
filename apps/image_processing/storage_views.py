"""
Views for storage management functionality
"""

import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render

from .permissions import admin_required

logger = logging.getLogger(__name__)


@login_required
def storage_status_view(request):
    """Display storage status and management options"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to view storage status.")
        return redirect("image_processing:list")

    # Get storage usage
    from .local_storage import LocalStorageManager
    storage_manager = LocalStorageManager()
    storage_usage = storage_manager.get_storage_usage()

    # Get storage recommendations
    recommendations = storage_manager._get_storage_recommendations()

    # Get recent uploads
    from .models import ImageUpload
    recent_uploads = ImageUpload.objects.order_by("-uploaded_at")[:10]

    context = {
        "storage_usage": storage_usage,
        "recommendations": recommendations,
        "recent_uploads": recent_uploads,
    }

    return render(request, "image_processing/storage_status.html", context)


@login_required
def storage_cleanup_view(request):
    """Handle storage cleanup operations"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to perform storage cleanup.")
        return redirect("image_processing:list")

    if request.method == "POST":
        action = request.POST.get("action")
        days = int(request.POST.get("days", 30))

        try:
            if action == "cleanup":
                # Perform actual cleanup
                from .local_storage import LocalStorageManager
                storage_manager = LocalStorageManager()
                result = storage_manager.cleanup_old_files(days)
                messages.success(
                    request,
                    f"Storage cleanup completed! Archived {result['archived_count']} files, freed {result['freed_space_mb']} MB",
                )
            elif action == "optimize":
                # Optimize uncompressed images
                optimize_uncompressed_images()
                messages.success(request, "Image optimization completed!")
            elif action == "archive":
                # Archive old files
                from .local_storage import LocalStorageManager
                storage_manager = LocalStorageManager()
                result = storage_manager.archive_old_files(days)
                messages.success(request, f"Archived {result['archived_count']} files")

            return redirect("image_processing:storage_status")

        except Exception as e:
            messages.error(request, f"Operation failed: {str(e)}")
            return redirect("image_processing:storage_status")

    return render(request, "image_processing/storage_cleanup.html")


def optimize_uncompressed_images():
    """Optimize all uncompressed images"""
    from .models import ImageUpload
    from .image_optimizer import ImageOptimizer
    from django.core.files.base import ContentFile

    uncompressed_images = ImageUpload.objects.filter(is_compressed=False)

    for image in uncompressed_images:
        try:
            if image.image_file:
                # Read original file
                with image.image_file.open("rb") as f:
                    file_content = f.read()

                # Optimize
                optimizer = ImageOptimizer()
                optimized_content, new_size, format_used = optimizer.optimize_image(file_content)

                # Save optimized version
                optimized_file = ContentFile(
                    optimized_content, f"optimized_{image.original_filename}"
                )

                # Update database record
                image.image_file.save(
                    f"optimized_{image.original_filename}", optimized_file, save=False
                )
                image.compressed_size = new_size
                image.is_compressed = True
                image.save()

        except Exception as e:
            logger.error(f"Failed to optimize image {image.id}: {e}")


@login_required
def dashboard_view(request):
    """Display image processing dashboard with statistics and overview"""
    # Get user's images or all images if admin
    from .models import ImageProcessingResult
    from .local_storage import LocalStorageManager

    if request.user.is_staff:
        from .models import ImageUpload
        images = ImageUpload.objects.all()
    else:
        from .models import ImageUpload
        images = ImageUpload.objects.filter(uploaded_by=request.user)

    # Get statistics
    total_uploads = images.count()
    processed_uploads = images.filter(upload_status="PROCESSED").count()
    uploaded_images = images.filter(upload_status="UPLOADED").count()
    pending_review = ImageProcessingResult.objects.filter(
        review_status=ImageProcessingResult.ReviewStatus.PENDING
    ).count()
    approved_results = ImageProcessingResult.objects.filter(
        review_status=ImageProcessingResult.ReviewStatus.APPROVED
    ).count()

    # Get AI models available
    ai_models = [
        ("yolo_bird_detection", "Bird Detection (YOLO)"),
        ("species_classification", "Species Classification"),
        ("census_counting", "Census Counting"),
    ]

    # Get AI model information from models directory
    import os
    models_dir = "models"
    yolov5_models = []
    yolov8_models = []
    yolov9_models = []

    if os.path.exists(models_dir):
        for filename in os.listdir(models_dir):
            if filename.endswith(".pt"):
                file_path = os.path.join(models_dir, filename)
                file_size = os.path.getsize(file_path)
                size_mb = f"{file_size / (1024 * 1024):.1f}MB"

                model_info = {
                    "name": filename.replace(".pt", ""),
                    "size": size_mb,
                    "filename": filename,
                    "status": "Ready",
                }

                if filename.startswith("yolov5"):
                    yolov5_models.append(model_info)
                elif filename.startswith("yolov8"):
                    yolov8_models.append(model_info)
                elif filename.startswith("yolov9"):
                    yolov9_models.append(model_info)

    # Sort models by name
    yolov5_models.sort(key=lambda x: x["name"])
    yolov8_models.sort(key=lambda x: x["name"])
    yolov9_models.sort(key=lambda x: x["name"])

    # Get recent uploads (all recent uploads)
    recent_uploads = (
        images.filter(
            upload_status__in=[
                "PROCESSED",
                "UPLOADED",
                "PROCESSING",
            ]
        )
        .exclude(
            upload_status="UPLOADING"  # Exclude stuck uploads
        )
        .order_by("-uploaded_at")[:5]
    )

    # Get storage statistics
    storage_manager = LocalStorageManager()
    storage_stats = storage_manager.get_storage_usage()

    context = {
        "total_uploads": total_uploads,
        "processed_uploads": processed_uploads,
        "uploaded_images": uploaded_images,
        "pending_review": pending_review,
        "approved_results": approved_results,
        "ai_models": ai_models,
        "yolov5_models": yolov5_models,
        "yolov8_models": yolov8_models,
        "yolov9_models": yolov9_models,
        "recent_uploads": recent_uploads,
        "storage_stats": storage_stats,
    }

    return render(request, "image_processing/dashboard.html", context)
