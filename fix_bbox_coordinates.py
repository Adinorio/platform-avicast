#!/usr/bin/env python
"""
Fix Bounding Box Coordinates
Updates existing ProcessingResult records with actual YOLO model detections
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'avicast_project.settings.development')
django.setup()

from apps.image_processing.models import ProcessingResult, ImageUpload
from apps.image_processing.bird_detection_service import get_bird_detection_service

def fix_bounding_boxes():
    """
    Re-process all images with incorrect bounding boxes
    """
    print("=" * 60)
    print("BOUNDING BOX COORDINATE FIX SCRIPT")
    print("=" * 60)
    print()
    
    # Get bird detection service
    service = get_bird_detection_service()
    
    if not service.is_available():
        print("ERROR: AI Model not available!")
        print("Cannot fix coordinates without the model.")
        return
    
    print(f"✅ AI Model loaded: {service.model_path}")
    print()
    
    # Find results with dummy coordinates (likely test data)
    results = ProcessingResult.objects.all()
    print(f"Found {results.count()} processing result(s)")
    print()
    
    fixed_count = 0
    error_count = 0
    
    for result in results:
        print(f"Checking result: {result.id}")
        print(f"  Image: {result.image_upload.title}")
        print(f"  Current bbox: {result.bounding_box}")
        
        # Check if coordinates look like dummy data
        bbox = result.bounding_box
        is_dummy = (
            bbox.get('x') == 100 and 
            bbox.get('y') == 100 and 
            bbox.get('width') == 200 and 
            bbox.get('height') == 200
        )
        
        if is_dummy:
            print("  ⚠️  Detected dummy coordinates - Re-processing...")
            
            try:
                # Re-run detection
                with open(result.image_upload.image_file.path, 'rb') as f:
                    image_data = f.read()
                
                detection = service.detect_birds(
                    image_data, 
                    result.image_upload.original_filename
                )
                
                if detection['success'] and detection['detections']:
                    # Update with real coordinates
                    first_detection = detection['detections'][0]
                    
                    result.bounding_box = first_detection['bounding_box']
                    result.detected_species = first_detection['species']
                    result.confidence_score = first_detection['confidence']
                    result.total_detections = detection['total_detections']
                    result.ai_model_used = detection['model_used']
                    result.processing_device = detection['device_used']
                    result.save()
                    
                    print(f"  ✅ FIXED!")
                    print(f"     New bbox: {result.bounding_box}")
                    print(f"     Species: {result.detected_species}")
                    print(f"     Confidence: {result.confidence_score:.2%}")
                    fixed_count += 1
                else:
                    print(f"  ❌ No detections found")
                    error_count += 1
                    
            except Exception as e:
                print(f"  ❌ Error: {e}")
                error_count += 1
        else:
            print("  ✅ Coordinates look correct (not dummy data)")
        
        print()
    
    print("=" * 60)
    print("FIX COMPLETE")
    print("=" * 60)
    print(f"✅ Fixed: {fixed_count}")
    print(f"❌ Errors: {error_count}")
    print(f"📊 Total checked: {results.count()}")
    print()
    
    if fixed_count > 0:
        print("🎉 SUCCESS! Bounding boxes have been updated with real YOLO coordinates.")
        print()
        print("Next steps:")
        print("1. Go to: http://127.0.0.1:8000/image-processing/review/")
        print("2. Check that bounding boxes are now accurately positioned")
        print("3. Toggle between 'Box' and 'Original' views to verify")
    
    print()

if __name__ == "__main__":
    fix_bounding_boxes()




