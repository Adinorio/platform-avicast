#!/usr/bin/env python3
"""
Enhanced Bird Detection Test Script
Tests the bird detection service and shows results with bounding boxes
"""

import os
import sys
import cv2
import numpy as np
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Add the bird_detection directory to Python path
bird_detection_path = project_root / 'bird_detection'
sys.path.insert(0, str(bird_detection_path))

def test_bird_detection_service():
    """Test the bird detection service"""
    try:
        from apps.image_processing.bird_detection_service import get_bird_detection_service
        
        print("Testing Bird Detection Service...")
        service = get_bird_detection_service()
        
        if not service.is_available():
            print("❌ Bird detection service is not available")
            return False
        
        print("✅ Bird detection service is available")
        print(f"Model path: {service.model_path}")
        print(f"Device: {service.device}")
        print(f"Confidence threshold: {service.confidence_threshold}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing bird detection service: {e}")
        return False

def test_model_loading():
    """Test if the trained model can be loaded"""
    try:
        from ultralytics import YOLO
        
        # Check for trained models
        possible_model_paths = [
            project_root / 'runs' / 'detect' / 'train4' / 'weights' / 'best.pt',
            project_root / 'runs' / 'detect' / 'train3' / 'weights' / 'best.pt',
            project_root / 'runs' / 'detect' / 'train2' / 'weights' / 'best.pt',
            project_root / 'runs' / 'detect' / 'train' / 'weights' / 'best.pt',
            project_root / 'models' / 'yolov8x.pt',
        ]
        
        model_loaded = False
        for model_path in possible_model_paths:
            if model_path.exists():
                print(f"Found model at: {model_path}")
                try:
                    model = YOLO(str(model_path))
                    print(f"✅ Successfully loaded model: {model_path.name}")
                    model_loaded = True
                    break
                except Exception as e:
                    print(f"❌ Failed to load model {model_path}: {e}")
        
        if not model_loaded:
            print("❌ No models could be loaded")
            return False
        
        return True
        
    except ImportError:
        print("❌ Ultralytics not available")
        return False
    except Exception as e:
        print(f"❌ Error testing model loading: {e}")
        return False

def test_dataset():
    """Test if the dataset is properly configured"""
    try:
        dataset_path = project_root / 'dataset'
        data_yaml = dataset_path / 'data.yaml'
        
        if not dataset_path.exists():
            print("❌ Dataset directory not found")
            return False
        
        if not data_yaml.exists():
            print("❌ data.yaml not found in dataset directory")
            return False
        
        # Check dataset structure
        train_path = dataset_path / 'train' / 'images'
        val_path = dataset_path / 'val' / 'images'
        test_path = dataset_path / 'test' / 'images'
        
        print("Dataset structure:")
        print(f"  Train images: {len(list(train_path.glob('*.jpg')))} images")
        print(f"  Validation images: {len(list(val_path.glob('*.jpg')))} images")
        print(f"  Test images: {len(list(test_path.glob('*.jpg')))} images")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing dataset: {e}")
        return False

def test_detection_on_sample_image():
    """Test detection on a sample image from the dataset"""
    try:
        from apps.image_processing.bird_detection_service import get_bird_detection_service
        
        service = get_bird_detection_service()
        if not service.is_available():
            print("❌ Service not available for testing")
            return False
        
        # Find a sample image
        dataset_path = project_root / 'dataset'
        sample_image_path = None
        
        for img_path in dataset_path.rglob('*.jpg'):
            if img_path.is_file():
                sample_image_path = img_path
                break
        
        if not sample_image_path:
            print("❌ No sample images found in dataset")
            return False
        
        print(f"Testing detection on: {sample_image_path.name}")
        
        # Read image and test detection
        with open(sample_image_path, 'rb') as f:
            image_content = f.read()
        
        result = service.detect_birds(image_content, sample_image_path.name)
        
        if result['success']:
            print("✅ Detection successful!")
            print(f"  Total detections: {result['total_detections']}")
            print(f"  Model used: {result['model_used']}")
            print(f"  Device used: {result['device_used']}")
            
            if result['detections']:
                print("  Detections:")
                for i, detection in enumerate(result['detections']):
                    print(f"    {i+1}. {detection['species']} - Confidence: {detection['confidence']:.2%}")
                    bbox = detection['bounding_box']
                    print(f"       Bounding box: ({bbox['x']}, {bbox['y']}) - {bbox['width']}x{bbox['height']}")
            
            return True
        else:
            print(f"❌ Detection failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing detection: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("Enhanced Bird Detection Test Suite")
    print("=" * 60)
    
    tests = [
        ("Bird Detection Service", test_bird_detection_service),
        ("Model Loading", test_model_loading),
        ("Dataset Configuration", test_dataset),
        ("Sample Image Detection", test_detection_on_sample_image),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 Testing: {test_name}")
        print("-" * 40)
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Bird detection system is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
