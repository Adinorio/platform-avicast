#!/usr/bin/env python3
"""
Restore mixed-species images to analyze their training value
"""

import shutil
from pathlib import Path


def restore_mixed_images():
    """Restore the mixed-species images that were removed during filtering"""

    print("🔄 RESTORING MIXED-SPECIES IMAGES FOR ANALYSIS")
    print("=" * 55)

    # Paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent

    # Source: original prepared dataset
    source_images = (
        project_root / "training_data" / "prepared_dataset" / "chinese_egret_dataset" / "images"
    )
    source_labels = (
        project_root / "training_data" / "prepared_dataset" / "chinese_egret_dataset" / "labels"
    )

    # Destination: final dataset
    dest_base = project_root / "training_data" / "final_yolo_dataset" / "chinese_egret_dataset"

    splits = ["train", "val", "test"]

    print("\n📋 RESTORATION PLAN:")
    print("1. Copy all original images back")
    print("2. Copy all original labels back")
    print("3. Re-run the split logic")

    # Get all original image-label pairs
    image_extensions = ["*.png", "*.jpg", "*.jpeg", "*.PNG", "*.JPG", "*.JPEG"]
    all_images = []

    for ext in image_extensions:
        all_images.extend(list(source_images.glob(ext)))

    print(f"\n📊 Found {len(all_images)} original images")

    # Get corresponding labels
    image_label_pairs = []
    for img_path in all_images:
        label_path = source_labels / f"{img_path.stem}.txt"
        if label_path.exists():
            image_label_pairs.append((img_path, label_path))

    print(f"📊 Found {len(image_label_pairs)} original image-label pairs")

    # Analyze mixed vs pure before restoration
    mixed_count = 0
    pure_count = 0
    total_chinese_in_mixed = 0

    print("\n🔍 ANALYZING ORIGINAL DATASET:")
    print("-" * 40)

    for img_path, label_path in image_label_pairs:
        with open(label_path) as f:
            lines = f.readlines()

        classes_in_image = set()
        chinese_egrets = 0

        for line in lines:
            if line.strip():
                parts = line.strip().split()
                if len(parts) >= 1:
                    class_id = int(parts[0])
                    classes_in_image.add(class_id)
                    if class_id == 0:  # Chinese Egret
                        chinese_egrets += 1

        if len(classes_in_image) > 1:  # Mixed species
            mixed_count += 1
            total_chinese_in_mixed += chinese_egrets
        else:  # Pure
            pure_count += 1

    print(f"✅ Pure Chinese Egret images: {pure_count}")
    print(f"🔄 Mixed species images: {mixed_count}")
    print(f"🦆 Chinese Egrets in mixed images: {total_chinese_in_mixed}")
    print(f"📊 Mixed image percentage: {(mixed_count / len(image_label_pairs) * 100):.1f}%")

    # Now restore the images
    print("\n🔄 RESTORING IMAGES...")

    restored = 0
    for split in splits:
        images_dest = dest_base / split / "images"
        labels_dest = dest_base / split / "labels"

        # Copy all images and labels back
        for img_path, label_path in image_label_pairs:
            # Copy image
            shutil.copy2(str(img_path), str(images_dest / img_path.name))
            # Copy label
            shutil.copy2(str(label_path), str(labels_dest / label_path.name))
            restored += 1

    print(f"✅ Restored {restored} image-label pairs")

    print("\n" + "=" * 55)
    print("🎯 RESTORATION COMPLETE!")
    print("\n💡 NOW YOU CAN:")
    print("1. Run training with mixed images (YOLO will ignore non-class-0)")
    print("2. Or keep only pure Chinese images for cleaner training")
    print("3. Or consider multi-class training for all egret species")

    return mixed_count, pure_count, total_chinese_in_mixed


if __name__ == "__main__":
    restore_mixed_images()
