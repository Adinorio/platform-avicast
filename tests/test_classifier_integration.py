#!/usr/bin/env python3
"""
Test script for classifier integration
"""

import os
import sys

import numpy as np

# Add current directory to path
sys.path.insert(0, os.getcwd())

try:
    from apps.image_processing.bird_detection_service import trained_classifier_predict

    print("✅ Import successful")

    # Test with a sample crop
    test_crop = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    result = trained_classifier_predict(test_crop)

    print("✅ Classifier working")
    print(f"Classes: {list(result.keys())}")
    print(f"Top prediction: {max(result.items(), key=lambda x: x[1])}")
    print("🎉 Integration test passed!")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()
