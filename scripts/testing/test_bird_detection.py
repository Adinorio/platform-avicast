#!/usr/bin/env python
"""
Test script for the bird detection service
"""
import os
import sys
import django
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'avicast_project.settings.development')
django.setup()

def test_bird_detection_service():
    """Test the bird detection service"""
    try:
        from apps.image_processing.bird_detection_service import get_bird_detection_service
        
        print("Testing Bird Detection Service...")
        print("=" * 50)
        
        # Get the service
        service = get_bird_detection_service()
        
        # Check if service is available
        if service.is_available():
            print("✅ Bird detection service is available!")
            
            # Get model info
            model_info = service.get_model_info()
            print(f"📊 Model Info: {model_info}")
            
            # Test with a sample image if available
            sample_image_path = project_root / 'media' / 'bird_images'
            if sample_image_path.exists():
                print(f"🔍 Looking for sample images in: {sample_image_path}")
                
                # Find first image file
                image_files = list(sample_image_path.glob('*.jpg')) + list(sample_image_path.glob('*.png'))
                
                if image_files:
                    test_image = image_files[0]
                    print(f"🧪 Testing with image: {test_image.name}")
                    
                    # Read image and test detection
                    with open(test_image, 'rb') as f:
                        image_content = f.read()
                    
                    # Run detection
                    result = service.detect_birds(image_content, test_image.name)
                    
                    if result['success']:
                        print(f"✅ Detection successful!")
                        print(f"   Total detections: {result['total_detections']}")
                        print(f"   Best detection: {result['best_detection']}")
                        print(f"   Model used: {result['model_used']}")
                        print(f"   Device: {result['device_used']}")
                    else:
                        print(f"❌ Detection failed: {result.get('error', 'Unknown error')}")
                else:
                    print("⚠️  No sample images found for testing")
            else:
                print("⚠️  Sample image directory not found")
                
        else:
            print("❌ Bird detection service is not available")
            print("   This could be due to:")
            print("   - Missing YOLO model files")
            print("   - Missing dependencies (ultralytics, torch, etc.)")
            print("   - Model loading errors")
            
            # Check what's available
            print("\n🔍 Checking available files:")
            model_paths = [
                project_root / 'bird_detection' / 'chinese_egret_model.pt',
                project_root / 'runs' / 'detect' / 'train' / 'weights' / 'best.pt',
                project_root / 'runs' / 'detect' / 'train2' / 'weights' / 'best.pt',
                project_root / 'runs' / 'detect' / 'train3' / 'weights' / 'best.pt',
                project_root / 'runs' / 'detect' / 'train4' / 'weights' / 'best.pt',
                project_root / 'models' / 'yolov8x.pt',
            ]
            
            for path in model_paths:
                if path.exists():
                    print(f"   ✅ {path}")
                else:
                    print(f"   ❌ {path}")
                    
    except Exception as e:
        print(f"❌ Error testing bird detection service: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_bird_detection_service()
