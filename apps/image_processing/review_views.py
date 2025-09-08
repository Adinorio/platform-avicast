"""
Views for image processing review functionality
"""

import json
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import ImageProcessingResult, ImageUpload
from .permissions import admin_required, can_review_results

logger = logging.getLogger(__name__)


@login_required
def review_view(request):
    """Display images ready for review"""
    if not can_review_results(request.user):
        messages.error(request, "Access denied. Staff only.")
        return redirect("image_processing:list")

    # Get processing results ready for review (not just uploads)
    results_to_review = (
        ImageProcessingResult.objects.filter(
            review_status=ImageProcessingResult.ReviewStatus.PENDING,
            processing_status=ImageProcessingResult.ProcessingStatus.COMPLETED,
        )
        .select_related("image_upload", "image_upload__uploaded_by")
        .order_by("-created_at")
    )

    # Get approved results
    approved_results = (
        ImageProcessingResult.objects.filter(
            review_status=ImageProcessingResult.ReviewStatus.APPROVED,
            processing_status=ImageProcessingResult.ProcessingStatus.COMPLETED,
        )
        .select_related("image_upload", "image_upload__uploaded_by")
        .order_by("-reviewed_at")
    )

    # Get rejected results
    rejected_results = (
        ImageProcessingResult.objects.filter(
            review_status=ImageProcessingResult.ReviewStatus.REJECTED,
            processing_status=ImageProcessingResult.ProcessingStatus.COMPLETED,
        )
        .select_related("image_upload", "image_upload__uploaded_by")
        .order_by("-reviewed_at")
    )

    # Get overridden results
    overridden_results = (
        ImageProcessingResult.objects.filter(
            review_status=ImageProcessingResult.ReviewStatus.OVERRIDDEN,
            processing_status=ImageProcessingResult.ProcessingStatus.COMPLETED,
        )
        .select_related("image_upload", "image_upload__uploaded_by")
        .order_by("-overridden_at")
    )

    # Get counts for different statuses
    pending_count = results_to_review.count()
    approved_count = approved_results.count()
    rejected_count = rejected_results.count()
    overridden_count = overridden_results.count()

    context = {
        "results_to_review": results_to_review,
        "approved_results": approved_results,
        "rejected_results": rejected_results,
        "overridden_results": overridden_results,
        "pending_count": pending_count,
        "approved_count": approved_count,
        "rejected_count": rejected_count,
        "overridden_count": overridden_count,
    }
    return render(request, "image_processing/review.html", context)


@login_required
def annotation_view(request, pk):
    """Ground truth annotation interface"""
    image = get_object_or_404(ImageUpload, pk=pk)

    # Get processing result if available
    try:
        processing_result = ImageProcessingResult.objects.get(image_upload=image)
    except ImageProcessingResult.DoesNotExist:
        processing_result = None

    context = {
        "image_upload": image,
        "processing_result": processing_result,
    }

    return render(request, "image_processing/annotate.html", context)


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def save_annotations(request, pk):
    """Save ground truth annotations for an image"""
    try:
        image = get_object_or_404(ImageUpload, pk=pk)
        _data = json.loads(request.body)
        annotations = _data.get("annotations", [])
        custom_species = _data.get("custom_species", [])

        if not annotations:
            return JsonResponse({"success": False, "error": "No annotations provided"})

        # Create ground truth file content (YOLO format)
        yolo_content = []
        for ann in annotations:
            line = f"{ann['class_id']} {ann['center_x']:.6f} {ann['center_y']:.6f} {ann['width']:.6f} {ann['height']:.6f}"
            yolo_content.append(line)

        # Save annotations to a file or database
        # For now, we'll store in the image's metadata
        import os
        from django.conf import settings
        from django.utils import timezone

        # Create annotations directory if it doesn't exist
        annotations_dir = os.path.join(settings.MEDIA_ROOT, "annotations")
        os.makedirs(annotations_dir, exist_ok=True)

        # Save YOLO format file
        base_name = os.path.splitext(image.original_filename)[0]
        annotation_file = os.path.join(annotations_dir, f"{base_name}.txt")

        with open(annotation_file, "w") as f:
            f.write("\n".join(yolo_content))

        # Also store in ImageUpload metadata for easy access
        # Initialize metadata if it doesn't exist
        if image.metadata is None:
            image.metadata = {}

        image.metadata["ground_truth_annotations"] = annotations
        image.metadata["custom_species"] = custom_species
        image.metadata["ground_truth_file"] = f"annotations/{base_name}.txt"
        image.metadata["annotation_created_by"] = request.user.username
        image.metadata["annotation_created_at"] = timezone.now().isoformat()
        image.save()

        logger.info(
            f"Ground truth annotations saved for image {image.pk}: {len(annotations)} annotations"
        )

        return JsonResponse(
            {
                "success": True,
                "message": f"Saved {len(annotations)} annotations",
                "annotation_file": f"annotations/{base_name}.txt",
            }
        )

    except Exception as e:
        logger.error(f"Error saving annotations for image {pk}: {e}")
        return JsonResponse({"success": False, "error": str(e)})


@login_required
def species_management_view(request):
    """Species management interface"""
    context = {}
    return render(request, "image_processing/species_management.html", context)


@csrf_exempt
@require_http_methods(["GET", "POST", "PUT", "DELETE"])
@login_required
def api_species_management(request):
    """API for managing custom species"""
    if request.method == "GET":
        # Get all custom species from all users' images
        all_species = set()

        # Collect species from all image metadata
        images_with_species = ImageUpload.objects.filter(
            metadata__custom_species__isnull=False
        ).exclude(metadata__custom_species=[])

        for image in images_with_species:
            if "custom_species" in image.metadata:
                for species in image.metadata["custom_species"]:
                    species_key = (species["name"], species.get("scientific_name", ""))
                    all_species.add(species_key)

        # Convert to list format
        species_list = [
            {
                "name": name,
                "scientific_name": scientific_name if scientific_name else None,
                "usage_count": 1,  # Could calculate actual usage
            }
            for name, scientific_name in all_species
        ]

        return JsonResponse({"species": species_list})

    elif request.method == "POST":
        # Add new global species
        _data = json.loads(request.body)
        # Implementation for adding global species
        return JsonResponse({"success": True})

    else:
        return JsonResponse({"error": "Method not allowed"}, status=405)


@login_required
@require_http_methods(["POST"])
def approve_result(request, result_id):
    """Approve a processing result"""
    if not can_review_results(request.user):
        return JsonResponse({"status": "error", "message": "Access denied"}, status=403)

    try:
        result = get_object_or_404(ImageProcessingResult, pk=result_id)
        notes = request.POST.get("notes", "")

        result.approve_result(request.user, notes)

        return JsonResponse(
            {
                "status": "success",
                "message": f'Result for "{result.image_upload.title}" approved successfully!',
            }
        )
    except Exception as e:
        return JsonResponse(
            {"status": "error", "message": f"Error approving result: {str(e)}"}, status=500
        )


@login_required
@require_http_methods(["POST"])
def reject_result(request, result_id):
    """Reject a processing result"""
    if not can_review_results(request.user):
        return JsonResponse({"status": "error", "message": "Access denied"}, status=403)

    try:
        result = get_object_or_404(ImageProcessingResult, pk=result_id)
        notes = request.POST.get("notes", "")

        result.reject_result(request.user, notes)

        return JsonResponse(
            {"status": "success", "message": f'Result for "{result.image_upload.title}" rejected.'}
        )
    except Exception as e:
        return JsonResponse(
            {"status": "error", "message": f"Error rejecting result: {str(e)}"}, status=500
        )


@login_required
@require_http_methods(["POST"])
def override_result(request, result_id):
    """Override a processing result with manual classification and/or count"""
    if not can_review_results(request.user):
        return JsonResponse({"status": "error", "message": "Access denied"}, status=403)

    try:
        result = get_object_or_404(ImageProcessingResult, pk=result_id)
        new_species = request.POST.get("species")
        new_count_str = request.POST.get("count")
        reason = request.POST.get("reason", "")

        # Validate that at least one field is being overridden
        if not new_species and not new_count_str:
            return JsonResponse(
                {
                    "status": "error",
                    "message": "At least species or count must be provided for override",
                },
                status=400,
            )

        # Parse count if provided
        new_count = None
        if new_count_str:
            try:
                new_count = int(new_count_str)
                if new_count < 0:
                    return JsonResponse(
                        {"status": "error", "message": "Count must be a non-negative number"},
                        status=400,
                    )
            except ValueError:
                return JsonResponse(
                    {"status": "error", "message": "Count must be a valid number"}, status=400
                )

        # Use original species if not provided
        if not new_species:
            new_species = result.final_species

        result.override_result(request.user, new_species, reason, new_count)

        # Build success message
        changes = []
        if new_count is not None:
            changes.append(f"count: {new_count}")
        if new_species:
            changes.append(f"species: {new_species}")

        return JsonResponse(
            {
                "status": "success",
                "message": f'Result for "{result.image_upload.title}" overridden with {" and ".join(changes)}',
            }
        )
    except Exception as e:
        return JsonResponse(
            {"status": "error", "message": f"Error overriding result: {str(e)}"}, status=500
        )


@login_required
def allocate_view(request):
    """Allocate approved results to census data"""
    if not can_review_results(request.user):
        messages.error(request, "Access denied. Staff only.")
        return redirect("image_processing:list")

    # Get approved results that can be allocated
    approved_results = (
        ImageProcessingResult.objects.filter(
            review_status__in=[
                ImageProcessingResult.ReviewStatus.APPROVED,
                ImageProcessingResult.ReviewStatus.OVERRIDDEN,
            ]
        )
        .select_related("image_upload", "image_upload__uploaded_by")
        .order_by("-created_at")
    )

    # Get sites for allocation (you'll need to implement this based on your sites system)
    # For now, we'll use mock data
    sites = [
        {"id": 1, "name": "Site A - Coastal Wetland", "location": "Eastern Coast"},
        {"id": 2, "name": "Site B - Inland Lake", "location": "Central Region"},
        {"id": 3, "name": "Site C - River Delta", "location": "Western Delta"},
    ]

    # Mock years and months for census data
    years = [2024, 2025, 2026]
    months = [
        {"id": 1, "name": "January", "abbr": "Jan"},
        {"id": 2, "name": "February", "abbr": "Feb"},
        {"id": 3, "name": "March", "abbr": "Mar"},
        {"id": 4, "name": "April", "abbr": "Apr"},
        {"id": 5, "name": "May", "abbr": "May"},
        {"id": 6, "name": "June", "abbr": "Jun"},
        {"id": 7, "name": "July", "abbr": "Jul"},
        {"id": 8, "name": "August", "abbr": "Aug"},
        {"id": 9, "name": "September", "abbr": "Sep"},
        {"id": 10, "name": "October", "abbr": "Oct"},
        {"id": 11, "name": "November", "abbr": "Nov"},
        {"id": 12, "name": "December", "abbr": "Dec"},
    ]

    context = {
        "approved_results": approved_results,
        "sites": sites,
        "years": years,
        "months": months,
    }
    return render(request, "image_processing/allocate.html", context)
