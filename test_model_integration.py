#!/usr/bin/env python3
"""
Test script to verify the trained YOLO11m model integration
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_service_initialization():
    """Test BirdDetectionService initialization with trained model"""
    print("🔍 Testing BirdDetectionService initialization...")

    try:
        # Configure Django settings first
        import django
        from django.conf import settings

        if not settings.configured:
            settings.configure(
                DEBUG=True,
                MAX_FILE_SIZE_MB=50,
                SECRET_KEY="debug-key-for-testing",
                INSTALLED_APPS=[
                    "django.contrib.contenttypes",
                    "django.contrib.auth",
                ],
            )
            django.setup()

        from apps.image_processing.bird_detection_service import BirdDetectionService

        print("Initializing BirdDetectionService...")
        service = BirdDetectionService()

        print("✅ Service initialized successfully")
        print(f"Available models: {list(service.models.keys())}")

        # Check if our trained model is loaded
        if "YOLO11M_EGRET_MAX_ACCURACY" in service.models:
            print("✅ YOLO11M_EGRET_MAX_ACCURACY model found in service")
            model = service.models["YOLO11M_EGRET_MAX_ACCURACY"]
            print(f"Model type: {type(model)}")
            print("✅ Model loaded successfully!")
            return True
        else:
            print("❌ YOLO11M_EGRET_MAX_ACCURACY model NOT found in service")
            print(f"Available models: {list(service.models.keys())}")
            return False

    except Exception as e:
        print(f"❌ Service initialization error: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_inference():
    """Test inference with the trained model"""
    print("\n🔍 Testing inference...")

    try:
        # Configure Django settings first
        import django
        from django.conf import settings

        if not settings.configured:
            settings.configure(
                DEBUG=True,
                MAX_FILE_SIZE_MB=50,
                SECRET_KEY="debug-key-for-testing",
                INSTALLED_APPS=[
                    "django.contrib.contenttypes",
                    "django.contrib.auth",
                ],
            )
            django.setup()

        import io

        from PIL import Image

        from apps.image_processing.bird_detection_service import BirdDetectionService

        service = BirdDetectionService()

        # Create a dummy test image (since we don't have real images handy)
        test_image = Image.new("RGB", (640, 480), color="white")

        # Convert to bytes as expected by detect_birds
        buffer = io.BytesIO()
        test_image.save(buffer, format="JPEG")
        image_bytes = buffer.getvalue()

        print("Running inference on test image...")
        results = service.detect_birds(image_bytes, image_filename="test.jpg")

        print("✅ Inference completed successfully")
        print(f"Number of detections: {len(results) if results else 0}")

        if results:
            for i, detection in enumerate(results):
                print(f"Detection {i+1}: {detection}")

        return True

    except Exception as e:
        print(f"❌ Inference error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🚀 Testing YOLO11m Model Integration")
    print("=" * 50)

    # Test service initialization
    service_ok = test_service_initialization()

    if service_ok:
        # Test inference
        inference_ok = test_inference()

        if inference_ok:
            print("\n🎉 ALL INTEGRATION TESTS PASSED!")
            print("✅ The trained YOLO11m model is successfully integrated!")
        else:
            print("\n❌ Inference test failed")
    else:
        print("\n❌ Service initialization failed")
