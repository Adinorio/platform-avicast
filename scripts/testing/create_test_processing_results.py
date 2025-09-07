#!/usr/bin/env python
"""
Create test processing results for testing the review functionality
"""

import os
import sys
from pathlib import Path

import django

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "avicast_project.settings.development")
django.setup()

import uuid

from django.utils import timezone

from apps.image_processing.models import ImageProcessingResult, ImageUpload
from apps.users.models import User


def create_test_processing_results():
    """Create test processing results for existing image uploads"""

    # Get existing image uploads
    uploads = ImageUpload.objects.filter(upload_status="PROCESSED")

    if not uploads.exists():
        print("No processed image uploads found. Please upload and process some images first.")
        return

    # Get or create a test user for reviewing
    try:
        reviewer = User.objects.filter(is_staff=True).first()
        if not reviewer:
            print("No staff users found. Please create a staff user first.")
            return
    except Exception as e:
        print(f"Error getting reviewer: {e}")
        return

    created_count = 0

    for upload in uploads:
        # Check if processing result already exists
        if hasattr(upload, "processing_result"):
            print(f"Processing result already exists for {upload.title}")
            continue

        try:
            # Create a mock processing result
            result = ImageProcessingResult.objects.create(
                id=uuid.uuid4(),
                image_upload=upload,
                detected_species="CHINESE_EGRET",  # Mock species
                confidence_score=0.85,  # Mock confidence
                bounding_box={"x": 100, "y": 100, "width": 200, "height": 150},
                processing_status="COMPLETED",
                ai_model="YOLO_V8",
                model_version="v8.0",
                processing_device="cpu",
                inference_time=2.5,
                model_confidence_threshold=0.25,
                review_status="PENDING",  # Ready for review
                review_notes="",
                is_overridden=False,
                created_at=timezone.now(),
                updated_at=timezone.now(),
            )

            print(f"Created processing result for: {upload.title}")
            created_count += 1

        except Exception as e:
            print(f"Error creating result for {upload.title}: {e}")

    print(f"\nCreated {created_count} test processing results.")
    print("You can now test the review functionality!")


if __name__ == "__main__":
    create_test_processing_results()
