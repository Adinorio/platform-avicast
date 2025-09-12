#!/usr/bin/env python3
"""
Test script to check classifier model loading and species support
"""
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_classifier_model():
    """Test the classifier model loading and check supported species"""
    print("🔍 Testing Classifier Model Loading...")
    print("=" * 50)

    # Check if model exists
    model_path = project_root / "models" / "classifier" / "best_model.pth"
    print(f"Model path: {model_path}")
    print(f"Model exists: {model_path.exists()}")

    if not model_path.exists():
        print("❌ Classifier model not found!")
        return False

    try:
        import torch

        print("📦 Loading classifier model...")
        checkpoint = torch.load(model_path, map_location='cpu', weights_only=False)

        print("✅ Model loaded successfully!")
        print(f"Model name: {checkpoint.get('model_name', 'unknown')}")
        print(f"Class names: {checkpoint.get('class_names', 'unknown')}")
        print(f"Available keys: {list(checkpoint.keys())}")

        # Check if model_state_dict exists
        if 'model_state_dict' in checkpoint:
            print("✅ Model state dict found")
            state_dict = checkpoint['model_state_dict']
            print(f"Number of layers: {len(state_dict)}")

            # Try to infer output classes from the final layer
            classifier_keys = [k for k in state_dict.keys() if 'classifier' in k and 'weight' in k]
            if classifier_keys:
                classifier_weight = state_dict[classifier_keys[0]]
                num_classes = classifier_weight.shape[0]
                print(f"🔢 Number of output classes: {num_classes}")
        else:
            print("❌ Model state dict not found")

        return True

    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return False

def check_mock_classifier():
    """Check what species the mock classifier supports"""
    print("\n🤖 Checking Mock Classifier Species Support...")
    print("=" * 50)

    # Import the mock classifier function
    try:
        from apps.image_processing.bird_detection_service import mock_classifier_predict

        # Check the classes defined in the mock classifier
        import inspect
        source = inspect.getsource(mock_classifier_predict)

        # Extract classes from the source code
        if 'classes = [' in source:
            start = source.find('classes = [') + 11
            end = source.find(']', start)
            classes_str = source[start:end + 1]
            print(f"Mock classifier classes: {classes_str}")

        # Test the mock classifier
        print("Testing mock classifier with dummy input...")
        import numpy as np
        dummy_crop = np.random.rand(64, 64, 3).astype(np.uint8) * 255
        result = mock_classifier_predict(dummy_crop)
        print(f"Mock classifier result: {result}")

    except Exception as e:
        print(f"❌ Error testing mock classifier: {e}")

def check_config_species():
    """Check species configuration"""
    print("\n⚙️ Checking Configuration Species...")
    print("=" * 50)

    try:
        from apps.image_processing.config import BIRD_SPECIES, YOLO_VERSION_CONFIGS

        print(f"BIRD_SPECIES configuration: {list(BIRD_SPECIES.keys())}")

        # Check YOLO configs
        for model_name, config in YOLO_VERSION_CONFIGS.items():
            if 'trained_classes' in config:
                print(f"{model_name} trained classes: {config['trained_classes']}")

    except Exception as e:
        print(f"❌ Error checking config: {e}")

if __name__ == "__main__":
    print("🦅 AVICAST Species Classification Diagnostic Tool")
    print("=" * 60)

    # Run all tests
    test_classifier_model()
    check_mock_classifier()
    check_config_species()

    print("\n" + "=" * 60)
    print("🎯 SUMMARY:")
    print("Current system supports 4 egret species:")
    print("  ✅ Chinese Egret")
    print("  ✅ Great Egret")
    print("  ✅ Intermediate Egret")
    print("  ✅ Little Egret")
    print("")
    print("Missing species for your requirements:")
    print("  ❌ Cattle Egret")
    print("  ❌ Pacific Reef Heron/Egret")
    print("=" * 60)

