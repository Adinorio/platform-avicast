"""
Views for image processing functionality
"""

import io
import logging
import time

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import ImageProcessingResult, ImageUpload
from .permissions import admin_required, can_access_image, can_modify_image

logger = logging.getLogger(__name__)


def process_image_with_storage(image_upload, file_content):
    """Process image with local storage optimization and real bird detection"""
    from .image_processor import ImageProcessor
    
    try:
        logger.info(f"=== PROCESS_IMAGE_WITH_STORAGE FUNCTION STARTED ===")
        logger.info(f"Starting processing for image {image_upload.pk}")
        logger.info(f"Image size: {len(file_content)} bytes")
        
        # Use the new ImageProcessor class to handle the complete pipeline
        processor = ImageProcessor(image_upload)
        success = processor.process_image(file_content)
        
        if success:
            logger.info(f"Processing completed successfully for image {image_upload.pk}")
        else:
            logger.error(f"Processing failed for image {image_upload.pk}")
            
    except Exception as e:
        logger.error(f"Processing failed: {str(e)}")
        image_upload.mark_failed()
        # Don't re-raise the error - let the upload continue
        logger.error(f"Image processing failed for {image_upload.pk}, but upload will continue")


@login_required
def process_batch_view(request, pk):
    """Process a batch of images"""
    if not request.user.is_staff:
        messages.error(request, "Access denied. Staff only.")
        return redirect("image_processing:list")

    try:
        # Get the image to process
        image = get_object_or_404(ImageUpload, pk=pk)

        # Process the image
        if image.upload_status == ImageUpload.UploadStatus.UPLOADED:
            # Re-process the image
            try:
                import os
                with open(image.image_file.path, "rb") as f:
                    file_content = f.read()
                process_image_with_storage(image, file_content)
                messages.success(request, f"Image '{image.title}' processed successfully!")
            except Exception as e:
                messages.error(request, f"Processing failed: {str(e)}")
        else:
            messages.info(request, f"Image '{image.title}' is already processed.")

        return redirect("image_processing:detail", pk=pk)

    except Exception as e:
        messages.error(request, f"Error processing image: {str(e)}")
        return redirect("image_processing:detail", pk=pk)


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def api_batch_process(request):
    """API endpoint for batch processing of images"""
    logger.error("=== API_BATCH_PROCESS FUNCTION STARTED ===")
    try:
        import json

        _data = json.loads(request.body)
        image_ids = _data.get("image_ids", [])
        logger.error(f"=== API_BATCH_PROCESS: Processing {len(image_ids)} images ===")

        if not image_ids:
            return JsonResponse({"success": False, "error": "No image IDs provided"})

        # Get images that are in uploaded status OR failed status (for retry)
        images_to_process = ImageUpload.objects.filter(
            pk__in=image_ids,
            upload_status__in=[ImageUpload.UploadStatus.UPLOADED, ImageUpload.UploadStatus.FAILED],
        )

        if not images_to_process.exists():
            return JsonResponse(
                {
                    "success": False,
                    "error": "No valid images found to process. Images must be in UPLOADED or FAILED status to be processed.",
                }
            )

        processed_count = 0
        failed_count = 0

        for image in images_to_process:
            try:
                # Log if this is a retry of a failed image
                if image.upload_status == ImageUpload.UploadStatus.FAILED:
                    logger.info(f"Retrying failed image {image.pk}")
                else:
                    logger.info(f"Processing new image {image.pk}")

                # Read file content for processing
                with image.image_file.open("rb") as f:
                    file_content = f.read()

                # Process the image
                logger.error(f"=== ABOUT TO CALL PROCESS_IMAGE_WITH_STORAGE for image {image.pk} ===")
                process_image_with_storage(image, file_content)
                logger.error(f"=== PROCESS_IMAGE_WITH_STORAGE COMPLETED for image {image.pk} ===")
                processed_count += 1
                logger.info(f"Successfully processed image {image.pk}")

            except Exception as e:
                logger.error(f"Failed to process image {image.pk}: {str(e)}")
                image.mark_failed()
                failed_count += 1

        return JsonResponse(
            {
                "success": True,
                "processed": processed_count,
                "failed": failed_count,
                "message": f"Processed {processed_count} images successfully, {failed_count} failed",
            }
        )

    except Exception as e:
        logger.error(f"Batch processing error: {str(e)}")
        return JsonResponse(
            {"success": False, "error": f"Batch processing failed: {str(e)}"}, status=500
        )


def _create_failed_processing_result(image_upload, error_message, ai_dimensions=(640, 640)):
    """Create a failed processing result"""
    try:
        import uuid

        from .models import ImageProcessingResult

        if not hasattr(image_upload, "processing_result"):
            processing_result = ImageProcessingResult.objects.create(
                id=uuid.uuid4(),
                image_upload=image_upload,
                detected_species=None,
                confidence_score=0.0,
                bounding_box={
                    "best_detection": {},
                    "all_detections": [],
                    "total_count": 0,
                    "ai_dimensions": ai_dimensions,  # Use actual AI dimensions for failed results
                },
                total_detections=0,
                processing_status=ImageProcessingResult.ProcessingStatus.FAILED,
                ai_model="UNKNOWN",
                model_version="unknown",
                processing_device="cpu",
                inference_time=0.0,
                model_confidence_threshold=0.25,
                review_status=ImageProcessingResult.ReviewStatus.PENDING,
                review_notes=f"Processing failed: {error_message}",
                is_overridden=False,
            )
            logger.info(f"Failed processing result created: {processing_result.pk}")
    except Exception as e:
        logger.error(f"Error creating failed processing result: {str(e)}")


def _create_fallback_processing_result(image_upload):
    """Create a fallback processing result when detection service is unavailable"""
    try:
        import uuid

        from .models import ImageProcessingResult

        if not hasattr(image_upload, "processing_result"):
            processing_result = ImageProcessingResult.objects.create(
                id=uuid.uuid4(),
                image_upload=image_upload,
                detected_species=None,
                confidence_score=0.0,
                bounding_box={
                    "best_detection": {},
                    "all_detections": [],
                    "total_count": 0,
                    "ai_dimensions": (640, 640),
                },
                total_detections=0,
                processing_status=ImageProcessingResult.ProcessingStatus.COMPLETED,
                ai_model="FALLBACK",
                model_version="fallback",
                processing_device="cpu",
                inference_time=0.0,
                model_confidence_threshold=0.25,
                review_status=ImageProcessingResult.ReviewStatus.PENDING,
                review_notes="AI detection service unavailable - manual review required",
                is_overridden=False,
            )
            logger.info(f"Fallback processing result created: {processing_result.pk}")
    except Exception as e:
        logger.error(f"Error creating fallback processing result: {str(e)}")