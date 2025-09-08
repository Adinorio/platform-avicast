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
    from .config import IMAGE_CONFIG

    def update_progress(step, progress, description=""):
        """Update progress with real-time feedback"""
        try:
            image_upload.processing_step = step
            image_upload.processing_progress = progress
            image_upload.save(update_fields=["processing_step", "processing_progress"])
            logger.info(f"Progress Update: {step} - {progress}% - {description}")
        except Exception as e:
            logger.error(f"Error updating progress: {str(e)}")

    def gradual_progress(
        start_progress, end_progress, step_name, duration=2.0, description_prefix=""
    ):
        """Simulate gradual progress over time"""
        steps = end_progress - start_progress
        if steps <= 0:
            return

        # Update progress immediately for real-time feedback
        for i in range(steps + 1):
            current_progress = start_progress + i
            current_description = f"{description_prefix}... {current_progress}%"
            update_progress(step_name, current_progress, current_description)
            # Small delay to allow frontend to catch up
            time.sleep(IMAGE_CONFIG["PROGRESS_UPDATE_DELAY"])

    try:
        start_time = time.time()
        logger.info(f"Starting processing for image {image_upload.pk}")

        # Step 1: Start processing (0-20%)
        logger.info("Step 1: Starting processing...")
        update_progress(ImageUpload.ProcessingStep.READING_FILE, 0, "Initializing...")

        image_upload.start_processing()
        logger.info("start_processing completed")

        # Gradual progress for initialization and file reading
        gradual_progress(0, 20, ImageUpload.ProcessingStep.READING_FILE, 1.5, "Reading image file")

        # Step 2: Save ORIGINAL image to maintain coordinate system consistency (20-50%)
        logger.info("Step 2: Saving ORIGINAL image to maintain coordinate system...")
        update_progress(
            ImageUpload.ProcessingStep.SAVING, 20, "Preparing to save original image..."
        )

        from django.core.files.base import ContentFile

        # CRITICAL: Save the ORIGINAL image to ensure the stored image dimensions
        # match the AI processing dimensions for accurate bounding box visualization.
        original_file = ContentFile(file_content, image_upload.original_filename)
        image_upload.image_file.save(image_upload.original_filename, original_file, save=False)
        image_upload.compressed_size = len(file_content)  # Use original size
        image_upload.is_compressed = False  # Mark as not compressed since we're keeping original
        image_upload.save()
        logger.info("ORIGINAL image saved to maintain coordinate system consistency")

        # Gradual progress for saving
        gradual_progress(20, 50, ImageUpload.ProcessingStep.SAVING, 1.0, "Saving results")

        # Step 3: Run bird detection (50-75%)
        logger.info("Step 3: Running bird detection...")
        update_progress(ImageUpload.ProcessingStep.DETECTING, 50, "Initializing AI model...")

        try:
            from .bird_detection_service import get_bird_detection_service

            detection_service = get_bird_detection_service()
            if detection_service.is_available():
                logger.info("Bird detection service available, running detection...")

                # Gradual progress for AI model loading
                gradual_progress(
                    50, 70, ImageUpload.ProcessingStep.DETECTING, 1.5, "Loading YOLO model"
                )

                # Gradual progress for image analysis
                gradual_progress(
                    70,
                    85,
                    ImageUpload.ProcessingStep.DETECTING,
                    2.0,
                    "Analyzing with AI (original image)",
                )

                # Gradual progress for bird detection
                gradual_progress(
                    85, 95, ImageUpload.ProcessingStep.DETECTING, 2.5, "Detecting birds"
                )

                # CRITICAL: Use file_content (original image) for detection.
                # This ensures coordinates are in the correct coordinate system.
                detection_result = detection_service.detect_birds(
                    file_content, image_upload.original_filename
                )

                # Get user-friendly summary for better feedback
                user_summary = detection_service.get_user_friendly_error_summary(detection_result)

                if detection_result["success"]:
                    logger.info(
                        f"Detection successful: {detection_result['total_detections']} birds found"
                    )

                    # Create processing result with real detection data
                    if not hasattr(image_upload, "processing_result"):
                        import uuid

                        from .models import ImageProcessingResult

                        # Use the best detection result
                        best_detection = detection_result["best_detection"]

                        if best_detection:
                            detected_species = best_detection["species"]
                            confidence_score = best_detection["confidence"]
                            bounding_box = best_detection["bounding_box"]
                        else:
                            # No birds detected
                            detected_species = None
                            confidence_score = 0.0
                            bounding_box = {}

                        # Store all detections in the bounding_box field for visualization
                        all_detections = detection_result.get("detections", [])

                        # CRITICAL FIX: Use the actual dimensions that the AI model processed
                        # Since we're using file_content (original image), the AI processed the original dimensions
                        from PIL import Image

                        original_image = Image.open(io.BytesIO(file_content))
                        actual_ai_dimensions = original_image.size

                        detection_data = {
                            "best_detection": bounding_box,
                            "all_detections": [
                                {
                                    "species": det["species"],
                                    "confidence": det["confidence"],
                                    "bounding_box": det["bounding_box"],
                                }
                                for det in all_detections
                            ],
                            "total_count": len(all_detections),
                            "ai_dimensions": actual_ai_dimensions,  # Store ACTUAL AI processing dimensions
                            "user_feedback": user_summary,  # Store user-friendly feedback
                            "no_detection_analysis": detection_result.get(
                                "no_detection_analysis", {}
                            ),  # Make sure this is passed through
                        }
                        logger.info(
                            f"CRITICAL FIX: Stored ACTUAL AI dimensions: {actual_ai_dimensions} (not the 640x640 optimization)"
                        )

                        processing_result = ImageProcessingResult.objects.create(
                            id=uuid.uuid4(),
                            image_upload=image_upload,
                            detected_species=detected_species,
                            confidence_score=confidence_score,
                            bounding_box=detection_data,  # Store comprehensive detection data including ai_dimensions
                            total_detections=detection_result["total_detections"],
                            processing_status=ImageProcessingResult.ProcessingStatus.COMPLETED,
                            ai_model=detection_result.get("model_version", "UNKNOWN").split("_")[0]
                            if detection_result.get("model_version")
                            else "UNKNOWN",
                            model_version=detection_result["model_used"],
                            processing_device=detection_result["device_used"],
                            inference_time=detection_result.get("inference_time", 0.0),
                            model_confidence_threshold=detection_result["confidence_threshold"],
                            review_status=ImageProcessingResult.ReviewStatus.PENDING,  # Ready for review
                            review_notes="",
                            is_overridden=False,
                        )
                        logger.info(
                            f"Processing result created with real detection: {processing_result.pk}"
                        )
                        logger.info(f"Species: {detected_species}, Confidence: {confidence_score}")
                        logger.info(f"Total detections: {detection_result['total_detections']}")
                    else:
                        logger.info("Processing result already exists")
                else:
                    logger.error(f"Detection failed: {user_summary['message']}")
                    # Create a failed processing result with user-friendly error message
                    from PIL import Image

                    original_image = Image.open(io.BytesIO(file_content))
                    actual_ai_dimensions = original_image.size
                    error_message = f"{user_summary['title']}: {user_summary['message']}"
                    if user_summary["user_guidance"]:
                        error_message += " | " + " | ".join(
                            user_summary["user_guidance"][:2]
                        )  # Include first 2 suggestions
                    _create_failed_processing_result(
                        image_upload, error_message, actual_ai_dimensions
                    )
            else:
                logger.warning("Bird detection service not available, using fallback")
                _create_fallback_processing_result(image_upload)

        except Exception as e:
            logger.error(f"Error during bird detection: {str(e)}")
            # Create a failed processing result with correct dimensions
            from PIL import Image

            original_image = Image.open(io.BytesIO(file_content))
            actual_ai_dimensions = original_image.size
            _create_failed_processing_result(image_upload, str(e), actual_ai_dimensions)

        # Step 4: Optimize images for web delivery (80-95%)
        logger.info("Step 4: Optimizing images for web delivery...")
        update_progress(ImageUpload.ProcessingStep.OPTIMIZING, 80, "Creating optimized versions...")

        try:
            from apps.common.services.image_optimizer import UniversalImageOptimizer

            optimizer = UniversalImageOptimizer()

            # Create optimized versions
            gradual_progress(80, 90, ImageUpload.ProcessingStep.OPTIMIZING, 1.0, "Optimizing for web")

            optimized_result = optimizer.optimize_for_app(file_content, 'image_processing')

            # Save optimized versions if successful
            if optimized_result.get('optimized'):
                from django.core.files.base import ContentFile

                # Save optimized web version
                optimized_filename = f"optimized_{image_upload.pk}.webp"
                image_upload.optimized_image.save(
                    optimized_filename,
                    ContentFile(optimized_result['optimized']),
                    save=False
                )
                image_upload.optimized_size = len(optimized_result['optimized'])
                image_upload.is_compressed = True

                logger.info(f"Optimized image saved: {optimized_filename}")

            # Save thumbnail version
            if optimized_result.get('thumbnail'):
                thumbnail_filename = f"thumb_{image_upload.pk}.jpg"
                image_upload.thumbnail.save(
                    thumbnail_filename,
                    ContentFile(optimized_result['thumbnail']),
                    save=False
                )
                image_upload.thumbnail_size = len(optimized_result['thumbnail'])

                logger.info(f"Thumbnail saved: {thumbnail_filename}")

            # Save AI-optimized version for future use
            if optimized_result.get('ai_ready'):
                ai_filename = f"ai_ready_{image_upload.pk}.jpg"
                image_upload.ai_processed_image.save(
                    ai_filename,
                    ContentFile(optimized_result['ai_ready']),
                    save=False
                )

                logger.info(f"AI-ready image saved: {ai_filename}")

            # Update optimization metadata
            image_upload.optimization_status = 'completed'
            image_upload.is_compressed = True

            # Save all changes at once
            image_upload.save(update_fields=[
                'optimized_image', 'thumbnail', 'ai_processed_image',
                'optimized_size', 'thumbnail_size', 'optimization_status', 'is_compressed'
            ])

            logger.info("Optimization completed successfully")

        except Exception as e:
            logger.warning(f"Image optimization failed: {str(e)}")
            # Mark optimization as failed but don't break processing
            image_upload.optimization_status = 'failed'
            image_upload.save(update_fields=['optimization_status'])
            # Continue processing even if optimization fails

        # Complete processing
        logger.info("Completing processing...")
        update_progress(ImageUpload.ProcessingStep.COMPLETE, 95, "Finalizing results...")

        # Final progress update
        gradual_progress(95, 100, ImageUpload.ProcessingStep.COMPLETE, 0.5, "Completing")

        image_upload.complete_processing()

        # Calculate and log actual processing time
        total_time = time.time() - start_time
        logger.info(f"Processing completed successfully in {total_time:.2f} seconds")

        # Store actual processing time in the model if available
        try:
            if hasattr(image_upload, "processing_duration"):
                from datetime import timedelta

                image_upload.processing_duration = timedelta(seconds=total_time)
                image_upload.save(update_fields=["processing_duration"])
        except Exception as duration_error:
            logger.warning(f"Could not save processing duration: {str(duration_error)}")
            # Don't fail the entire processing for this minor issue

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
    try:
        import json

        _data = json.loads(request.body)
        image_ids = _data.get("image_ids", [])

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
                process_image_with_storage(image, file_content)
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
                    "ai_dimensions": (640, 640),  # Default fallback dimensions
                },
                total_detections=0,
                processing_status=ImageProcessingResult.ProcessingStatus.COMPLETED,
                ai_model="UNKNOWN",
                model_version="fallback",
                processing_device="cpu",
                inference_time=0.0,
                model_confidence_threshold=0.25,
                review_status=ImageProcessingResult.ReviewStatus.PENDING,
                review_notes="Detection service unavailable - manual review required",
                is_overridden=False,
            )
            logger.info(f"Fallback processing result created: {processing_result.pk}")
    except Exception as e:
        logger.error(f"Error creating fallback processing result: {str(e)}")
