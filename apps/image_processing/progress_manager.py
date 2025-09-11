"""
Progress Management for Image Processing
Centralizes progress tracking and updates
"""

import logging
import time
from typing import Optional

from .config import IMAGE_CONFIG
from .models import ImageUpload

logger = logging.getLogger(__name__)


class ProgressManager:
    """Manages progress tracking for image processing operations"""
    
    def __init__(self, image_upload: ImageUpload):
        self.image_upload = image_upload
        self.start_time = time.time()
    
    def update_progress(self, step: str, progress: int, description: str = "") -> None:
        """Update progress with real-time feedback"""
        try:
            self.image_upload.processing_step = step
            self.image_upload.processing_progress = progress
            self.image_upload.save(update_fields=["processing_step", "processing_progress"])
            logger.info(f"Progress Update: {step} - {progress}% - {description}")
        except Exception as e:
            logger.error(f"Error updating progress: {str(e)}")
    
    def gradual_progress(
        self, 
        start_progress: int, 
        end_progress: int, 
        step_name: str, 
        duration: float = 2.0, 
        description_prefix: str = ""
    ) -> None:
        """Simulate gradual progress over time"""
        steps = end_progress - start_progress
        if steps <= 0:
            return

        # Update progress immediately for real-time feedback
        for i in range(steps + 1):
            current_progress = start_progress + i
            current_description = f"{description_prefix}... {current_progress}%"
            self.update_progress(step_name, current_progress, current_description)
            # Small delay to allow frontend to catch up
            time.sleep(IMAGE_CONFIG["PROGRESS_UPDATE_DELAY"])
    
    def get_elapsed_time(self) -> float:
        """Get elapsed processing time in seconds"""
        return time.time() - self.start_time
    
    def complete_processing(self) -> None:
        """Mark processing as complete"""
        self.update_progress(
            ImageUpload.ProcessingStep.COMPLETE, 
            100, 
            "Processing complete"
        )
        self.image_upload.complete_processing()
        logger.info(f"Processing completed in {self.get_elapsed_time():.2f} seconds")



