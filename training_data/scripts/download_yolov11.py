#!/usr/bin/env python3
"""
Download YOLOv11x model for bird identification
"""

import os
import sys

sys.path.append("../../")

try:
    from ultralytics import YOLO

    print("✅ Ultralytics library found")
except ImportError:
    print("❌ Ultralytics library not found. Installing...")
    os.system("pip install ultralytics")
    from ultralytics import YOLO


def download_yolov11x():
    """Download YOLOv11x model using Ultralytics"""

    print("🦆 Downloading YOLOv11x model using Ultralytics...")
    print("📁 This will download to the default Ultralytics cache directory")

    try:
        # Load YOLOv11x (this will download if not present)
        model = YOLO("yolov11x.pt")

        print("✅ YOLOv11x loaded successfully!")
        print(f"📍 Model path: {model.ckpt_path}")
        print(f"📊 Model info: {model.info()}")

        # Copy to our models directory for consistency
        import shutil
        from pathlib import Path

        source_path = Path(model.ckpt_path)
        target_dir = Path("../../models")
        target_dir.mkdir(exist_ok=True)
        target_path = target_dir / "yolov11x.pt"

        if source_path != target_path:
            print(f"📋 Copying to models directory: {target_path}")
            shutil.copy2(source_path, target_path)
            print(f"✅ YOLOv11x copied to: {target_path.absolute()}")

        return True

    except Exception as e:
        print(f"❌ Error downloading YOLOv11x: {e}")
        print("💡 Alternative: Try downloading manually from https://github.com/ultralytics/assets")
        return False


if __name__ == "__main__":
    download_yolov11x()
