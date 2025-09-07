#!/usr/bin/env python3
"""
Extract all Chinese Egret annotations from both COCO and YOLO formats
"""

import os
import zipfile
import shutil
from pathlib import Path

def extract_all_chinese_egret():
    """Extract all Chinese Egret annotation files"""

    print("🦆 EXTRACTING ALL CHINESE EGRET ANNOTATIONS")
    print("=" * 60)

    # Paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent

    exported_annotations = project_root / "training_data" / "exported_annotations" / "Chinese_Egret"
    temp_extract_dir = project_root / "training_data" / "temp_extracted"

    # Create temp directory for extraction
    temp_extract_dir.mkdir(exist_ok=True)

    # Extract all COCO files
    coco_dir = exported_annotations / "coco"
    print(f"\n📦 Extracting COCO files from {coco_dir}")

    coco_files = list(coco_dir.glob("*.zip"))
    print(f"Found {len(coco_files)} COCO files")

    for i, coco_file in enumerate(coco_files, 1):
        print(f"  📂 Extracting: {coco_file.name}")
        with zipfile.ZipFile(coco_file, 'r') as zip_ref:
            zip_ref.extractall(temp_extract_dir / f"coco_{i}")

    # Extract all YOLO files
    yolo_dir = exported_annotations / "yolo"
    print(f"\n📦 Extracting YOLO files from {yolo_dir}")

    yolo_files = list(yolo_dir.glob("*.zip"))
    print(f"Found {len(yolo_files)} YOLO files")

    for i, yolo_file in enumerate(yolo_files, 1):
        print(f"  📂 Extracting: {yolo_file.name}")
        with zipfile.ZipFile(yolo_file, 'r') as zip_ref:
            zip_ref.extractall(temp_extract_dir / f"yolo_{i}")

    print("\n✅ EXTRACTION COMPLETE")
    print(f"📁 Extracted to: {temp_extract_dir}")

    # Count total files
    total_images = 0
    total_labels = 0

    for subdir in temp_extract_dir.glob("*"):
        if subdir.is_dir():
            images = list(subdir.glob("*.png")) + list(subdir.glob("*.jpg")) + list(subdir.glob("*.jpeg")) + list(subdir.glob("*.PNG")) + list(subdir.glob("*.JPG"))
            labels = list(subdir.glob("*.txt"))
            total_images += len(images)
            total_labels += len(labels)
            print(f"  📊 {subdir.name}: {len(images)} images, {len(labels)} labels")

    print("\n📊 TOTAL EXTRACTED:")
    print(f"   🖼️  Images: {total_images}")
    print(f"   🏷️  Labels: {total_labels}")

    return temp_extract_dir

if __name__ == "__main__":
    temp_dir = extract_all_chinese_egret()
    print(f"\n🔄 Next: Consolidate all annotations into single dataset")
    print(f"📁 Use temp directory: {temp_dir}")
