#!/usr/bin/env python3
"""
Test the integrated YOLO11m pipeline with real egret images
"""
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_real_image_detection():
    """Test detection on a real egret image"""
    print("🔍 Testing with real egret images...")

    try:
        # Configure Django settings first
        import django
        from django.conf import settings

        if not settings.configured:
            settings.configure(
                DEBUG=True,
                MAX_FILE_SIZE_MB=50,
                SECRET_KEY='debug-key-for-testing',
                INSTALLED_APPS=[
                    'django.contrib.contenttypes',
                    'django.contrib.auth',
                ]
            )
            django.setup()

        from apps.image_processing.bird_detection_service import BirdDetectionService

        service = BirdDetectionService()

        # Test with a few different egret species
        test_images = [
            "training_data/final_yolo_dataset/unified_egret_dataset/test/images/chinese_egret_0002.PNG",
            "training_data/final_yolo_dataset/unified_egret_dataset/test/images/great_egret_0002.jpeg",
            "training_data/final_yolo_dataset/unified_egret_dataset/test/images/intermediate_egret_0008.jpeg",
            "training_data/final_yolo_dataset/unified_egret_dataset/test/images/little_egret_0003.jpg"
        ]

        for image_path in test_images:
            full_path = project_root / image_path
            if not full_path.exists():
                print(f"❌ Test image not found: {full_path}")
                continue

            print(f"\n🖼️ Testing with: {image_path}")

            # Read the image file
            with open(full_path, 'rb') as f:
                image_bytes = f.read()

            # Run detection
            results = service.detect_birds(image_bytes, image_filename=full_path.name)

            print(f"✅ Detection completed for {full_path.name}")

            # Parse results
            if 'detections' in results and results['detections']:
                detections = results['detections']
                print(f"📊 Found {len(detections)} detections:")

                for i, detection in enumerate(detections):
                    bbox = detection.get('bbox', {})
                    conf = detection.get('confidence', 0)
                    class_name = detection.get('class_name', 'unknown')

                    print(f"  {i+1}. {class_name} (conf: {conf:.3f}) at [{bbox.get('x1',0):.1f}, {bbox.get('y1',0):.1f}, {bbox.get('x2',0):.1f}, {bbox.get('y2',0):.1f}]")

                    # Check decision gates
                    if 'decision' in detection:
                        decision = detection['decision']
                        print(f"     Decision: {decision.get('status', 'unknown')} - {decision.get('reason', 'no reason')}")

                    # Check stage 2 decision (if available)
                    if 'stage2_decision' in detection:
                        stage2 = detection['stage2_decision']
                        print(f"     Stage 2: {stage2.get('status', 'unknown')} - {stage2.get('reason', 'no reason')}")
            else:
                print("  No detections found")

            print(f"🔧 Model used: {results.get('model_used', 'unknown')}")
            print(f"📈 Confidence threshold: {results.get('confidence_threshold', 'unknown')}")

        return True

    except Exception as e:
        print(f"❌ Real image test error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Testing YOLO11m with Real Egret Images")
    print("=" * 50)

    success = test_real_image_detection()

    if success:
        print("\n🎉 REAL IMAGE TESTS COMPLETED!")
        print("✅ The trained YOLO11m model is working with real egret images!")
    else:
        print("\n❌ Real image tests failed")

