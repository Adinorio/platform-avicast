"""
Image Processing Pipeline
Coordinates the complete image processing workflow
"""

import logging
import uuid
from typing import Dict, Any, Optional

from django.core.files.base import ContentFile

from .models import ImageProcessingResult, ImageUpload
from .progress_manager import ProgressManager
from .image_utils import ImageUtils
from .config import IMAGE_CONFIG

logger = logging.getLogger(__name__)


class ImageProcessor:
    """Coordinates the complete image processing pipeline"""
    
    def __init__(self, image_upload: ImageUpload):
        self.image_upload = image_upload
        self.progress_manager = ProgressManager(image_upload)
        self.image_utils = ImageUtils()
    
    def process_image(self, file_content: bytes) -> bool:
        """Main processing pipeline"""
        try:
            logger.info(f"Starting processing for image {self.image_upload.pk}")
            logger.info(f"Image size: {len(file_content)} bytes")
            
            # Step 1: Initialize processing
            self._initialize_processing()
            
            # Step 2: Save original image
            self._save_original_image(file_content)
            
            # Step 3: Run AI detection
            detection_result = self._run_ai_detection(file_content)
            
            # Step 4: Create processing result
            self._create_processing_result(detection_result, file_content)
            
            # Step 5: Optimize images
            self._optimize_images()
            
            # Step 6: Complete processing
            self.progress_manager.complete_processing()
            
            logger.info(f"Processing completed successfully for image {self.image_upload.pk}")
            return True
            
        except Exception as e:
            logger.error(f"Processing failed for image {self.image_upload.pk}: {str(e)}")
            self.image_upload.mark_failed()
            return False
    
    def _initialize_processing(self) -> None:
        """Step 1: Initialize processing (0-20%)"""
        logger.info("Step 1: Starting processing...")
        self.progress_manager.update_progress(
            ImageUpload.ProcessingStep.READING_FILE, 
            0, 
            "Initializing..."
        )
        
        self.image_upload.start_processing()
        logger.info("start_processing completed")
        
        # Gradual progress for initialization and file reading
        self.progress_manager.gradual_progress(
            0, 20, 
            ImageUpload.ProcessingStep.READING_FILE, 
            1.5, 
            "Reading image file"
        )
    
    def _save_original_image(self, file_content: bytes) -> None:
        """Step 2: Save original image (20-50%)"""
        logger.info("Step 2: Saving ORIGINAL image to maintain coordinate system...")
        self.progress_manager.update_progress(
            ImageUpload.ProcessingStep.SAVING, 
            20, 
            "Preparing to save original image..."
        )
        
        # CRITICAL: Save the ORIGINAL image to ensure the stored image dimensions
        # match the AI processing dimensions for accurate bounding box visualization.
        original_file = ContentFile(file_content, self.image_upload.original_filename)
        self.image_upload.image_file.save(
            self.image_upload.original_filename, 
            original_file, 
            save=False
        )
        self.image_upload.compressed_size = len(file_content)  # Use original size
        self.image_upload.is_compressed = False  # Mark as not compressed since we're keeping original
        self.image_upload.save()
        logger.info("ORIGINAL image saved to maintain coordinate system consistency")
        
        # Gradual progress for saving
        self.progress_manager.gradual_progress(
            20, 50, 
            ImageUpload.ProcessingStep.SAVING, 
            1.0, 
            "Saving results"
        )
    
    def _run_ai_detection(self, file_content: bytes) -> Dict[str, Any]:
        """Step 3: Run AI detection (50-80%)"""
        logger.info("Step 3: Running bird detection...")
        self.progress_manager.update_progress(
            ImageUpload.ProcessingStep.DETECTING, 
            50, 
            "Initializing AI model..."
        )
        
        try:
            from .bird_detection_service import get_bird_detection_service
            
            detection_service = get_bird_detection_service()
            if detection_service.is_available():
                logger.info("Bird detection service available, running detection...")
                
                # Gradual progress for AI model loading
                self.progress_manager.gradual_progress(
                    50, 70, 
                    ImageUpload.ProcessingStep.DETECTING, 
                    1.5, 
                    "Loading YOLO model"
                )
                
                # Gradual progress for image analysis
                self.progress_manager.gradual_progress(
                    70, 85,
                    ImageUpload.ProcessingStep.DETECTING,
                    2.0,
                    "Analyzing with AI (original image)",
                )
                
                # Gradual progress for bird detection
                self.progress_manager.gradual_progress(
                    85, 95, 
                    ImageUpload.ProcessingStep.DETECTING, 
                    2.5, 
                    "Detecting birds"
                )
                
                # CRITICAL: Use file_content (original image) for detection.
                # This ensures coordinates are in the correct coordinate system.
                detection_result = detection_service.detect_birds(
                    file_content, self.image_upload.original_filename
                )
                
                logger.info(f"Detection completed: {detection_result.get('total_detections', 0)} birds found")
                return detection_result
            else:
                logger.warning("Bird detection service not available, using fallback")
                return self._create_fallback_detection_result()
                
        except Exception as e:
            logger.error(f"Error during bird detection: {str(e)}")
            return self._create_error_detection_result(str(e))
    
    def _create_processing_result(self, detection_result: Dict[str, Any], file_content: bytes) -> None:
        """Create processing result from detection data"""
        if not hasattr(self.image_upload, "processing_result"):
            # Use the best detection result
            best_detection = detection_result.get("best_detection")
            
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
            
            # Get actual AI dimensions
            actual_ai_dimensions = self.image_utils.get_image_dimensions(file_content)
            
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
                "user_feedback": detection_result.get("user_feedback", {}),
                "no_detection_analysis": detection_result.get("no_detection_analysis", {}),
            }
            
            logger.info(f"Stored ACTUAL AI dimensions: {actual_ai_dimensions}")
            
            processing_result = ImageProcessingResult.objects.create(
                id=uuid.uuid4(),
                image_upload=self.image_upload,
                detected_species=detected_species,
                confidence_score=confidence_score,
                bounding_box=detection_data,
                total_detections=detection_result.get("total_detections", 0),
                processing_status=ImageProcessingResult.ProcessingStatus.COMPLETED,
                ai_model=detection_result.get("model_version", "UNKNOWN").split("_")[0]
                if detection_result.get("model_version")
                else "UNKNOWN",
                model_version=detection_result.get("model_used", "unknown"),
                processing_device=detection_result.get("device_used", "cpu"),
                inference_time=detection_result.get("inference_time", 0.0),
                model_confidence_threshold=detection_result.get("confidence_threshold", 0.25),
                review_status=ImageProcessingResult.ReviewStatus.PENDING,
                review_notes="",
                is_overridden=False,
            )
            
            logger.info(f"Processing result created: {processing_result.pk}")
            logger.info(f"Species: {detected_species}, Confidence: {confidence_score}")
        else:
            logger.info("Processing result already exists")
    
    def _optimize_images(self) -> None:
        """Step 5: Optimize images for web delivery (80-95%)"""
        logger.info("Step 5: Optimizing images for web delivery...")
        self.progress_manager.update_progress(
            ImageUpload.ProcessingStep.OPTIMIZING, 
            80, 
            "Creating optimized versions..."
        )
        
        try:
            from apps.common.services.image_optimizer import UniversalImageOptimizer
            
            optimizer = UniversalImageOptimizer()
            # Use the correct method name
            result = optimizer.optimize_for_app(
                file_content,  # Pass the image content
                'image_processing',
                preserve_original=True
            )

            # Save optimized versions if they exist
            if result.get('optimized'):
                optimized_file = ContentFile(result['optimized'])
                self.image_upload.optimized_image.save(
                    f"optimized_{self.image_upload.original_filename}",
                    optimized_file,
                    save=False
                )

            if result.get('thumbnail'):
                thumbnail_file = ContentFile(result['thumbnail'])
                self.image_upload.thumbnail.save(
                    f"thumb_{self.image_upload.original_filename}",
                    thumbnail_file,
                    save=False
                )

            if result.get('ai_ready'):
                ai_file = ContentFile(result['ai_ready'])
                self.image_upload.ai_processed_image.save(
                    f"ai_{self.image_upload.original_filename}",
                    ai_file,
                    save=False
                )

            self.image_upload.save()
            
            # Gradual progress for optimization
            self.progress_manager.gradual_progress(
                80, 95, 
                ImageUpload.ProcessingStep.OPTIMIZING, 
                1.0, 
                "Optimizing images"
            )
            
            logger.info("Image optimization completed")
            
        except Exception as e:
            logger.error(f"Error during image optimization: {str(e)}")
            # Don't fail the entire process for optimization errors
    
    def _create_fallback_detection_result(self) -> Dict[str, Any]:
        """Create fallback detection result when service is unavailable"""
        return {
            "success": True,
            "detections": [],
            "best_detection": None,
            "total_detections": 0,
            "model_used": "fallback",
            "model_version": "fallback",
            "device_used": "cpu",
            "confidence_threshold": 0.25,
            "user_feedback": {
                "title": "AI Service Unavailable",
                "message": "Bird detection service is currently unavailable",
                "user_guidance": ["Please try again later", "Contact administrator if issue persists"]
            }
        }
    
    def _create_error_detection_result(self, error_message: str) -> Dict[str, Any]:
        """Create error detection result"""
        return {
            "success": False,
            "detections": [],
            "best_detection": None,
            "total_detections": 0,
            "model_used": "error",
            "model_version": "error",
            "device_used": "cpu",
            "confidence_threshold": 0.25,
            "error": error_message,
            "user_feedback": {
                "title": "Processing Error",
                "message": f"Error during AI processing: {error_message}",
                "user_guidance": ["Try uploading a different image", "Check image format and size"]
            }
        }



