#!/usr/bin/env python3
"""
Download YOLO Models Script

This script downloads the necessary YOLO models that are not included in the repository
due to their large size. Run this script after cloning the repository to get the models.
"""

import os
import urllib.request
from pathlib import Path

# Model URLs and their expected file sizes
MODELS = {
    # YOLOv5 Models - using correct ultralytics URLs
    "yolov5n.pt": {
        "url": "https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov5n.pt",
        "size_mb": 3.8,
    },
    "yolov5s.pt": {
        "url": "https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov5s.pt",
        "size_mb": 14.1,
    },
    "yolov5m.pt": {
        "url": "https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov5m.pt",
        "size_mb": 40.7,
    },
    "yolov5l.pt": {
        "url": "https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov5l.pt",
        "size_mb": 89.4,
    },
    "yolov5x.pt": {
        "url": "https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov5x.pt",
        "size_mb": 166.7,
    },
    # YOLOv8 Models
    "yolov8n.pt": {
        "url": "https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt",
        "size_mb": 6.2,
    },
    "yolov8s.pt": {
        "url": "https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8s.pt",
        "size_mb": 22,
    },
    "yolov8m.pt": {
        "url": "https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8m.pt",
        "size_mb": 52,
    },
    "yolov8l.pt": {
        "url": "https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8l.pt",
        "size_mb": 87,
    },
    "yolov8x.pt": {
        "url": "https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8x.pt",
        "size_mb": 131,
    },
    # YOLOv9 Models - using correct WongKinYiu URLs
    "yolov9c.pt": {
        "url": "https://github.com/WongKinYiu/yolov9/releases/download/v0.1/yolov9-c.pt",
        "size_mb": 20.1,
    },
    "yolov9e.pt": {
        "url": "https://github.com/WongKinYiu/yolov9/releases/download/v0.1/yolov9-e.pt",
        "size_mb": 55.2,
    },
    "yolov9s.pt": {
        "url": "https://github.com/WongKinYiu/yolov9/releases/download/v0.1/yolov9-s.pt",
        "size_mb": 37.4,
    },
    "yolov9m.pt": {
        "url": "https://github.com/WongKinYiu/yolov9/releases/download/v0.1/yolov9-m.pt",
        "size_mb": 76.8,
    },
    "yolov9l.pt": {
        "url": "https://github.com/WongKinYiu/yolov9/releases/download/v0.1/yolov9-l.pt",
        "size_mb": 131.9,
    },
}


def download_file(url, filename, expected_size_mb):
    """Download a file with progress indication."""
    print(f"Downloading {filename} ({expected_size_mb}MB)...")

    try:
        urllib.request.urlretrieve(url, filename)

        # Verify file size
        actual_size_mb = os.path.getsize(filename) / (1024 * 1024)
        if abs(actual_size_mb - expected_size_mb) < 1:  # Allow 1MB tolerance
            print(f"✅ {filename} downloaded successfully ({actual_size_mb:.1f}MB)")
            return True
        else:
            print(
                f"⚠️  {filename} size mismatch: expected {expected_size_mb}MB, got {actual_size_mb:.1f}MB"
            )
            return False

    except Exception as e:
        print(f"❌ Error downloading {filename}: {e}")
        return False


def main():
    """Main function to download all models."""
    print("🚀 YOLO Models Downloader (v5, v8, v9)")
    print("=" * 50)
    print("This script will download YOLO models that are not included in the repository.")
    print("Models will be downloaded to the current directory.\n")

    # Create models directory if it doesn't exist
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)

    # Change to models directory
    os.chdir(models_dir)

    downloaded_count = 0
    total_count = len(MODELS)

    for model_name, model_info in MODELS.items():
        if os.path.exists(model_name):
            print(f"⏭️  {model_name} already exists, skipping...")
            downloaded_count += 1
            continue

        if download_file(model_info["url"], model_name, model_info["size_mb"]):
            downloaded_count += 1

    print("\n" + "=" * 50)
    print(f"📊 Download Summary: {downloaded_count}/{total_count} models ready")

    if downloaded_count == total_count:
        print("🎉 All models downloaded successfully!")
        print("\nAvailable YOLO versions:")
        print("  🟢 YOLOv5: yolov5n.pt, yolov5s.pt, yolov5m.pt, yolov5l.pt, yolov5x.pt")
        print("  🟡 YOLOv8: yolov8n.pt, yolov8s.pt, yolov8m.pt, yolov8l.pt, yolov8x.pt")
        print("  🔴 YOLOv9: yolov9c.pt, yolov9e.pt, yolov9s.pt, yolov9m.pt, yolov9l.pt")
        print("\nYou can now run the bird detection system with all YOLO versions!")
    else:
        print("⚠️  Some models failed to download. Check the errors above.")
        print("You may need to download them manually or check your internet connection.")


if __name__ == "__main__":
    main()
