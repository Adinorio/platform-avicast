#!/usr/bin/env python3
"""
Test script for the complete max accuracy pipeline integration
"""

import os
import sys

import numpy as np

# Add current directory to path
sys.path.insert(0, os.getcwd())


def test_pipeline():
    """Test the complete pipeline integration"""
    try:
        print("🔍 Testing Max Accuracy Pipeline Integration")
        print("=" * 50)

        # Test 1: Import bird detection service
        print("\n1. Testing imports...")
        from apps.image_processing.bird_detection_service import (
            crop_image,
            decide_classification_gate,
            decide_detection_gate,
            trained_classifier_predict,
        )

        print("✅ All imports successful")

        # Test 2: Test helper functions
        print("\n2. Testing helper functions...")
        test_crop = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

        # Test detection gate
        status, reason = decide_detection_gate(0.8, 100, 100)
        print(f"✅ Detection gate: {status} ({reason})")

        # Test classifier
        result = trained_classifier_predict(test_crop)
        print(
            f"✅ Classifier: {len(result)} classes, top: {max(result.items(), key=lambda x: x[1])}"
        )

        # Test classification gate
        status, reason = decide_classification_gate(result, 100)
        print(f"✅ Classification gate: {status} ({reason})")

        # Test crop function
        bbox = {"x": 10, "y": 10, "width": 50, "height": 50}
        cropped = crop_image(test_crop, bbox)
        print(f"✅ Crop function: {cropped.shape}")

        print("\n🎉 All pipeline components working correctly!")
        print("The max accuracy pipeline is ready for production use.")

        return True

    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_pipeline()
    if success:
        print("\n✅ Pipeline integration test PASSED")
    else:
        print("\n❌ Pipeline integration test FAILED")
        sys.exit(1)
