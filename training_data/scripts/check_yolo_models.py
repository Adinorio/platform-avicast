#!/usr/bin/env python3
"""
Check available YOLO models and download YOLOv11x
"""

import sys
import os
sys.path.append('../../')

try:
    from ultralytics import YOLO
    print("✅ Ultralytics library found")
except ImportError:
    print("❌ Ultralytics library not found")
    exit(1)

def check_available_models():
    """Check what YOLO models are available"""

    print("🔍 Checking available YOLO models...")

    # Common model names to try
    models_to_try = [
        'yolov11n.pt',
        'yolov11s.pt',
        'yolov11m.pt',
        'yolov11l.pt',
        'yolov11x.pt',
        'yolo11n.pt',
        'yolo11s.pt',
        'yolo11m.pt',
        'yolo11l.pt',
        'yolo11x.pt'
    ]

    available_models = []

    for model_name in models_to_try:
        try:
            print(f"🔄 Trying {model_name}...")
            model = YOLO(model_name)
            print(f"✅ {model_name} - Available!")
            available_models.append(model_name)
        except Exception as e:
            print(f"❌ {model_name} - Not available")

    print(f"\n📊 Available models: {available_models}")

    if available_models:
        # Try to download the largest available model
        largest_model = None
        if 'yolov11x.pt' in available_models:
            largest_model = 'yolov11x.pt'
        elif 'yolo11x.pt' in available_models:
            largest_model = 'yolo11x.pt'
        elif 'yolov11l.pt' in available_models:
            largest_model = 'yolov11l.pt'
        elif 'yolo11l.pt' in available_models:
            largest_model = 'yolo11l.pt'

        if largest_model:
            print(f"\n🎯 Downloading largest available model: {largest_model}")
            try:
                model = YOLO(largest_model)
                print(f"✅ Successfully downloaded {largest_model}")

                # Copy to models directory
                import shutil
                from pathlib import Path

                source_path = Path(model.ckpt_path)
                target_dir = Path("../../models")
                target_dir.mkdir(exist_ok=True)
                target_path = target_dir / largest_model

                if source_path != target_path:
                    print(f"📋 Copying to models directory...")
                    shutil.copy2(source_path, target_path)
                    print(f"✅ Model copied to: {target_path.absolute()}")

                return True
            except Exception as e:
                print(f"❌ Error downloading {largest_model}: {e}")

    return False

if __name__ == "__main__":
    check_available_models()




