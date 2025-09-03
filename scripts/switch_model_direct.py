#!/usr/bin/env python3
"""
Direct Model Switching Script

This script allows you to switch AI models directly without needing Django admin permissions.
Perfect for testing the Chinese Egret model integration.
"""

import os
import sys
from pathlib import Path
import logging

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set up logging to see model loading messages
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def switch_to_chinese_egret():
    """Switch to the Chinese Egret model directly"""
    print("🏆 SWITCHING TO CHINESE EGRET SPECIALIST MODEL")
    print("=" * 60)

    try:
        from apps.image_processing.bird_detection_service import get_bird_detection_service

        # Get the bird detection service
        service = get_bird_detection_service()

        # Show current model
        current_model = service.get_model_info()
        print(f"🎯 Current model: {current_model['current_version']}")

        # Switch to Chinese Egret model
        print("🔄 Switching to Chinese Egret Specialist...")
        switch_result = service.switch_model('CHINESE_EGRET_V1')

        if switch_result:
            # Verify the switch
            updated_info = service.get_model_info()
            print("✅ SUCCESS: Switched to Chinese Egret model!")
            print(f"🎯 New current model: {updated_info['current_version']}")
            print(f"📊 Performance: {updated_info['current_performance']}")

            # Show available models
            available_models = list(service.models.keys())
            print(f"📋 Available models: {available_models}")

            # Show Chinese Egret info
            chinese_info = updated_info.get('chinese_egret_specialist', {})
            print(f"🏆 Chinese Egret status: {chinese_info.get('status', 'Unknown')}")

            return True
        else:
            print("❌ FAILED: Could not switch to Chinese Egret model")
            return False

    except Exception as e:
        print(f"❌ Error switching model: {e}")
        return False

def test_inference():
    """Test inference with the current model"""
    print("\n🧪 TESTING INFERENCE")
    print("=" * 40)

    try:
        from apps.image_processing.bird_detection_service import get_bird_detection_service
        from PIL import Image
        import numpy as np

        service = get_bird_detection_service()

        # Create a test image
        test_image = Image.fromarray(np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8))
        test_image_path = project_root / 'test_inference.jpg'
        test_image.save(test_image_path)

        # Convert to bytes
        import io
        img_buffer = io.BytesIO()
        test_image.save(img_buffer, format='JPEG')
        img_bytes = img_buffer.getvalue()

        # Get current model info
        model_info = service.get_model_info()
        current_model = model_info['current_version']

        print(f"🎯 Testing with model: {current_model}")

        # Run inference
        result = service.detect_birds(img_bytes, "test_inference.jpg")

        if result['success']:
            print("✅ Inference successful!")
            print(f"📊 Detections found: {result.get('total_detections', 0)}")
            print(f"⚡ Processing time: {result.get('inference_time', 0):.3f}s")
            print(f"🔧 Model used: {result.get('model_used', 'Unknown')}")
        else:
            print(f"❌ Inference failed: {result.get('error', 'Unknown error')}")

        # Clean up
        if test_image_path.exists():
            test_image_path.unlink()

    except Exception as e:
        print(f"❌ Inference test failed: {e}")

def show_model_info():
    """Show detailed information about available models"""
    print("📊 MODEL INFORMATION")
    print("=" * 40)

    try:
        from apps.image_processing.bird_detection_service import get_bird_detection_service

        service = get_bird_detection_service()

        # Get model info
        model_info = service.get_model_info()

        print(f"🎯 Current model: {model_info['current_version']}")
        print(f"📊 Current performance: {model_info['current_performance']}")
        print(f"🔧 Device: {model_info['device']}")

        # Show available models
        available_models = list(service.models.keys())
        print(f"\n📋 Available models: {available_models}")

        # Show Chinese Egret info
        chinese_info = model_info.get('chinese_egret_specialist', {})
        print(f"\n🏆 CHINESE EGRET SPECIALIST:")
        print(f"   Status: {chinese_info.get('status', 'Unknown')}")
        print(f"   Available: {chinese_info.get('available', False)}")
        if chinese_info.get('performance'):
            perf = chinese_info['performance']
            print(f"   Performance: {perf.get('mAP', 0):.1f}% mAP, {perf.get('fps', 0)} FPS")

        # Show all model configurations
        print(f"\n🔧 MODEL CONFIGURATIONS:")
        for model_name, config in service.version_configs.items():
            if model_name in available_models:
                status = "✅ LOADED" if model_name in service.models else "❌ NOT LOADED"
                description = config.get('description', 'No description')
                performance = config.get('performance', {})
                print(f"   {model_name}: {description} - {status}")
                if performance:
                    print(f"      Performance: {performance.get('mAP', 0):.1f}% mAP, {performance.get('fps', 0)} FPS")

    except Exception as e:
        print(f"❌ Error getting model info: {e}")

def main():
    """Main function"""
    print("🔄 DIRECT MODEL SWITCHING TOOL")
    print("=" * 50)
    print("This tool allows you to switch AI models without Django permissions.")
    print()

    while True:
        print("Choose an option:")
        print("1. Switch to Chinese Egret Specialist model")
        print("2. Test inference with current model")
        print("3. Show detailed model information")
        print("4. Exit")

        choice = input("\nEnter choice (1-4): ").strip()

        if choice == '1':
            success = switch_to_chinese_egret()
            if success:
                print("\n🎉 Chinese Egret model is now active!")
                print("   Upload Chinese Egret images to see the 99.46% accuracy boost!")
        elif choice == '2':
            test_inference()
        elif choice == '3':
            show_model_info()
        elif choice == '4':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice!")

        print("\n" + "=" * 50)

if __name__ == "__main__":
    main()
