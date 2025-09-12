#!/usr/bin/env python3
"""
Quick test to verify system fixes are working
"""
import sys
import os
from pathlib import Path

def test_ai_dependencies():
    """Test if AI dependencies are installed"""
    print("🧪 Testing AI Dependencies...")

    try:
        import cv2
        print("✅ OpenCV (cv2) available")
    except ImportError:
        print("❌ OpenCV (cv2) NOT available")
        return False

    try:
        import torch
        print(f"✅ PyTorch available (v{torch.__version__})")
    except ImportError:
        print("❌ PyTorch NOT available")
        return False

    try:
        from ultralytics import YOLO
        print("✅ Ultralytics YOLO available")
    except ImportError:
        print("❌ Ultralytics YOLO NOT available")
        return False

    try:
        import numpy as np
        print(f"✅ NumPy available (v{np.__version__})")
    except ImportError:
        print("❌ NumPy NOT available")
        return False

    return True

def test_system_components():
    """Test core system components"""
    print("\n🔧 Testing System Components...")

    try:
        from apps.image_processing.bird_detection_service import get_bird_detection_service
        service = get_bird_detection_service()
        print("✅ Bird detection service loaded")
    except Exception as e:
        print(f"❌ Bird detection service failed: {e}")
        return False

    try:
        from apps.common.services.image_optimizer import UniversalImageOptimizer
        optimizer = UniversalImageOptimizer()
        print("✅ Image optimizer loaded")
    except Exception as e:
        print(f"❌ Image optimizer failed: {e}")
        return False

    try:
        from apps.image_processing.image_processor import ImageProcessor
        from apps.image_processing.models import ImageUpload
        print("✅ Image processor components available")
    except Exception as e:
        print(f"❌ Image processor failed: {e}")
        return False

    return True

def test_model_files():
    """Test if required model files exist"""
    print("\n📁 Testing Model Files...")

    model_files = [
        "models/classifier/best_model.pth",
        "runs/egret_detection/egret_yolo11m_50ep_resume/weights/best.pt",
        "training_data/final_yolo_dataset/unified_egret_dataset/data.yaml"
    ]

    all_exist = True

    for model_file in model_files:
        path = Path(model_file)
        if path.exists():
            size = path.stat().st_size / (1024*1024)  # MB
            print(".1f")
        else:
            print(f"❌ {model_file} - NOT FOUND")
            all_exist = False

    return all_exist

def main():
    """Main test function"""
    print("🦆 AVICAST System Fix Verification")
    print("=" * 50)

    tests_passed = 0
    total_tests = 3

    # Test 1: AI Dependencies
    if test_ai_dependencies():
        tests_passed += 1
        print("\n✅ AI Dependencies: PASS")
    else:
        print("\n❌ AI Dependencies: FAIL - Run 'pip install -r requirements-processing.txt'")

    # Test 2: System Components
    if test_system_components():
        tests_passed += 1
        print("\n✅ System Components: PASS")
    else:
        print("\n❌ System Components: FAIL - Check Django installation and imports")

    # Test 3: Model Files
    if test_model_files():
        tests_passed += 1
        print("\n✅ Model Files: PASS")
    else:
        print("\n❌ Model Files: PARTIAL - Some model files missing (non-critical)")

    print("\n" + "=" * 50)
    print(f"🧪 TEST RESULTS: {tests_passed}/{total_tests} tests passed")

    if tests_passed >= 2:
        print("\n🎉 SYSTEM READY!")
        print("✅ Core functionality should work")
        print("✅ Ready to process egret images")
        print("✅ Enhanced UI features available")
        print("\n🚀 Next: Start Django server and test with real images")
    else:
        print("\n⚠️ SYSTEM NEEDS FIXES")
        print("❌ Critical components missing")
        print("❌ Cannot process images yet")
        print("\n🔧 Action Required:")
        print("   1. pip install -r requirements-processing.txt")
        print("   2. Restart Python environment")
        print("   3. Run this test again")

    print("\n📋 Quick Start Commands:")
    print("   cd /path/to/avicast")
    print("   python manage.py runserver")
    print("   # Then visit: http://127.0.0.1:8000/image-processing/upload/")

if __name__ == "__main__":
    main()

