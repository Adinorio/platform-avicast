#!/usr/bin/env python3
"""
Model Integration Verification Script

This script verifies which model is currently being used by the system
and provides detailed logging to confirm the Chinese Egret model integration.
"""

import logging
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set up logging to see model loading messages
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def verify_model_files():
    """Verify that model files exist and are accessible"""
    print("🔍 VERIFICATION: Checking Model Files")
    print("=" * 60)

    models_dir = project_root / "models"
    chinese_egret_dir = models_dir / "chinese_egret_v1"

    # Check model files
    model_files = [
        ("PyTorch Model", chinese_egret_dir / "chinese_egret_best.pt"),
        ("ONNX Model", chinese_egret_dir / "chinese_egret_best.onnx"),
        ("Model Info", chinese_egret_dir / "model_info.json"),
    ]

    all_files_exist = True
    for name, file_path in model_files:
        if file_path.exists():
            size_mb = file_path.stat().st_size / (1024 * 1024)
            print(f"✅ {name}: {file_path} ({size_mb:.1f} MB)")
        else:
            print(f"❌ {name}: {file_path} (NOT FOUND)")
            all_files_exist = False

    print()
    return all_files_exist


def verify_model_service():
    """Verify the bird detection service can load the Chinese Egret model"""
    print("🔍 VERIFICATION: Testing Model Service")
    print("=" * 60)

    try:
        from apps.image_processing.bird_detection_service import get_bird_detection_service

        # Get the service
        service = get_bird_detection_service()

        # Check available models
        available_models = list(service.models.keys())
        print(f"📋 Available models: {available_models}")

        # Check if Chinese Egret model is loaded
        chinese_egret_loaded = "CHINESE_EGRET_V1" in available_models
        print(f"🏆 Chinese Egret V1 loaded: {'✅ YES' if chinese_egret_loaded else '❌ NO'}")

        # Get current model info
        model_info = service.get_model_info()
        print(f"🎯 Current model: {model_info['current_version']}")
        print(f"📊 Current performance: {model_info['current_performance']}")

        # Check Chinese Egret specialist info
        chinese_egret_info = model_info.get("chinese_egret_specialist", {})
        print(
            f"🏆 Chinese Egret Specialist available: {chinese_egret_info.get('available', False)}"
        )
        print(f"🏆 Chinese Egret Specialist status: {chinese_egret_info.get('status', 'Unknown')}")

        # Test model switching
        print("\n🔄 Testing model switching...")
        switch_result = service.switch_model("CHINESE_EGRET_V1")
        print(f"🏆 Switch to Chinese Egret V1: {'✅ SUCCESS' if switch_result else '❌ FAILED'}")

        if switch_result:
            updated_info = service.get_model_info()
            print(f"🎯 New current model: {updated_info['current_version']}")
            print(f"📊 New performance: {updated_info['current_performance']}")

        return chinese_egret_loaded

    except Exception as e:
        print(f"❌ Error testing model service: {e}")
        return False


def verify_form_defaults():
    """Verify that forms are using Chinese Egret as default"""
    print("🔍 VERIFICATION: Checking Form Defaults")
    print("=" * 60)

    try:
        from apps.image_processing.forms import ModelSelectionForm
        from apps.image_processing.models import AIModel

        # Check default model
        form = ModelSelectionForm()
        default_model = form.fields["ai_model"].initial
        print(f"📝 Form default model: {default_model}")

        # Check if Chinese Egret is the default
        is_chinese_egret_default = default_model == AIModel.CHINESE_EGRET_V1
        print(f"🏆 Chinese Egret is default: {'✅ YES' if is_chinese_egret_default else '❌ NO'}")

        # Show all available choices
        choices = form.fields["ai_model"].choices
        print("📋 All available choices:")
        for choice in choices:
            print(f"   • {choice[0]}: {choice[1]}")

        return is_chinese_egret_default

    except Exception as e:
        print(f"❌ Error checking form defaults: {e}")
        return False


def test_model_inference():
    """Test actual inference with the Chinese Egret model"""
    print("🔍 VERIFICATION: Testing Inference")
    print("=" * 60)

    try:
        from apps.image_processing.bird_detection_service import get_bird_detection_service

        service = get_bird_detection_service()

        # Switch to Chinese Egret model
        service.switch_model("CHINESE_EGRET_V1")

        # Create a small test image (just for testing the pipeline)
        import numpy as np
        from PIL import Image

        # Create a small test image
        test_image = Image.fromarray(np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8))
        test_image_path = project_root / "test_image.jpg"
        test_image.save(test_image_path)

        print(f"🖼️  Created test image: {test_image_path}")

        # Test inference
        import io

        img_buffer = io.BytesIO()
        test_image.save(img_buffer, format="JPEG")
        img_bytes = img_buffer.getvalue()

        print("🚀 Running inference test...")
        result = service.detect_birds(img_bytes, "test_image.jpg")

        if result["success"]:
            print("✅ Inference test successful!")
            print(f"🎯 Model used: {result.get('model_used', 'Unknown')}")
            print(f"📊 Detections found: {result.get('total_detections', 0)}")
            print(f"⚡ Inference time: {result.get('inference_time', 0):.3f}s")
            print(f"🔧 Device used: {result.get('device_used', 'Unknown')}")
        else:
            print(f"❌ Inference test failed: {result.get('error', 'Unknown error')}")

        # Clean up
        if test_image_path.exists():
            test_image_path.unlink()

        return result["success"]

    except Exception as e:
        print(f"❌ Error testing inference: {e}")
        return False


def main():
    """Main verification function"""
    print("🏆 CHINESE EGRET MODEL INTEGRATION VERIFICATION")
    print("=" * 70)
    print("This script verifies that your new Chinese Egret model is properly integrated.")
    print()

    # Run all verifications
    verifications = [
        ("Model Files Exist", verify_model_files),
        ("Model Service Works", verify_model_service),
        ("Form Defaults Correct", verify_form_defaults),
        ("Inference Works", test_model_inference),
    ]

    results = []
    for name, func in verifications:
        print(f"\n🔍 RUNNING: {name}")
        result = func()
        results.append((name, result))
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"📊 {name}: {status}")

    # Summary
    print("\n" + "=" * 70)
    print("🎯 VERIFICATION SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")

    if passed == total:
        print("\n🎉 ALL VERIFICATIONS PASSED!")
        print("🏆 Your Chinese Egret model is properly integrated and working!")
        print("🎯 The system is using the 99.46% accuracy model for detection.")
    else:
        print("\n⚠️  SOME VERIFICATIONS FAILED!")
        print("🔧 Check the failed items above and fix the issues.")

    # Additional recommendations
    print("\n💡 RECOMMENDATIONS:")
    print("   • Check Django logs for detailed model loading messages")
    print("   • Restart your Django application if models aren't loading")
    print("   • Verify file permissions on model files")
    print("   • Test with real Chinese Egret images to see the performance boost")


if __name__ == "__main__":
    main()
