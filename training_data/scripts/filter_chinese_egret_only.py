#!/usr/bin/env python3
"""
Filter dataset to keep only Chinese Egret images (class 0)
Remove images that contain other egret species (class 3, 5)
"""

import os
import shutil
from pathlib import Path

def filter_chinese_egret_only():
    """Filter dataset to keep only images with Chinese Egret labels (class 0)"""

    print("🧹 FILTERING CHINESE EGRET DATASET - REMOVING OTHER SPECIES")
    print("=" * 70)

    # Dataset paths - use absolute path
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    base_path = project_root / "training_data" / "final_yolo_dataset" / "chinese_egret_dataset"

    print(f"🔍 Base path: {base_path}")
    print(f"🔍 Exists: {base_path.exists()}")

    splits = ['train', 'val', 'test']
    total_removed = 0
    total_kept = 0

    for split in splits:
        print(f"\n🔍 Processing {split} split...")

        images_path = base_path / split / "images"
        labels_path = base_path / split / "labels"

        # Get all label files
        label_files = list(labels_path.glob("*.txt"))
        print(f"🔍 Found {len(label_files)} label files in {labels_path}")
        if len(label_files) > 0:
            print(f"🔍 First few: {[f.name for f in label_files[:3]]}")
        else:
            print(f"❌ No label files found in {labels_path}")
            print(f"❌ Labels path exists: {labels_path.exists()}")
            continue

        removed_count = 0
        kept_count = 0

        for label_file in label_files:
            # Read label file
            with open(label_file, 'r') as f:
                lines = f.readlines()

            # Check if all classes in this file are Chinese Egret (class 0)
            all_chinese_egret = True
            has_chinese_egret = False

            for line in lines:
                if line.strip():
                    parts = line.strip().split()
                    if len(parts) >= 1:
                        class_id = int(parts[0])
                        if class_id == 0:
                            has_chinese_egret = True
                        elif class_id in [3, 5]:  # Little Egret or Intermediate Egret
                            all_chinese_egret = False
                            break

            # Decision logic
            if all_chinese_egret and has_chinese_egret:
                # Keep this image - it only contains Chinese Egrets
                kept_count += 1
            else:
                # Remove this image - contains other species
                image_file = images_path / f"{label_file.stem}.PNG"  # or .png/.jpg

                # Try different extensions
                for ext in ['.PNG', '.png', '.jpg', '.jpeg', '.JPG', '.JPEG']:
                    img_path = images_path / f"{label_file.stem}{ext}"
                    if img_path.exists():
                        os.remove(str(img_path))
                        break

                # Remove label file
                os.remove(str(label_file))
                removed_count += 1
                print(f"  ❌ Removed: {label_file.stem} (mixed/other species)")

        print(f"  ✅ Kept: {kept_count} images")
        print(f"  🗑️  Removed: {removed_count} images")

        total_kept += kept_count
        total_removed += removed_count

    print("\n" + "=" * 70)
    print("🎯 FILTERING COMPLETE!")
    print(f"📊 Total kept: {total_kept} Chinese Egret images")
    print(f"📊 Total removed: {total_removed} mixed/other species images")
    print(f"📊 Purity: {(total_kept / (total_kept + total_removed) * 100):.1f}%")

    return total_kept, total_removed

if __name__ == "__main__":
    kept, removed = filter_chinese_egret_only()

    if kept > 0:
        print("\n🚀 READY FOR TRAINING!")
        print("Now run: yolo train model=models/yolov8x.pt data=training_data/final_yolo_dataset/chinese_egret_dataset/data.yaml [training args]")
    else:
        print("\n❌ No Chinese Egret images found!")
