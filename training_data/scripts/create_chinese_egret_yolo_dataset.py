#!/usr/bin/env python3
"""
Create proper YOLO dataset structure for Chinese Egret dataset
Splits data into train/val/test and creates final_yolo_dataset structure
"""

import os
import shutil
import random
from pathlib import Path
from sklearn.model_selection import train_test_split

def create_chinese_egret_yolo_dataset():
    """Create YOLO dataset structure for Chinese Egret"""

    print("🦆 CREATING CHINESE EGRET YOLO DATASET STRUCTURE")
    print("=" * 60)

    # Get the project root directory (where this script is located)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent

    # Source paths
    source_images = project_root / "training_data" / "prepared_dataset" / "chinese_egret_dataset" / "images"
    source_labels = project_root / "training_data" / "prepared_dataset" / "chinese_egret_dataset" / "labels"

    # Destination paths
    dest_base = project_root / "training_data" / "final_yolo_dataset" / "chinese_egret_dataset"

    print(f"🔍 Source images: {source_images}")
    print(f"🔍 Source labels: {source_labels}")
    print(f"🔍 Destination: {dest_base}")
    dest_train_images = dest_base / "train" / "images"
    dest_train_labels = dest_base / "train" / "labels"
    dest_val_images = dest_base / "val" / "images"
    dest_val_labels = dest_base / "val" / "labels"
    dest_test_images = dest_base / "test" / "images"
    dest_test_labels = dest_base / "test" / "labels"

    # Create directories
    for dir_path in [dest_train_images, dest_train_labels, dest_val_images,
                     dest_val_labels, dest_test_images, dest_test_labels]:
        dir_path.mkdir(parents=True, exist_ok=True)

    # Get all image files
    image_extensions = ['*.png', '*.jpg', '*.jpeg', '*.PNG', '*.JPG', '*.JPEG']
    all_images = []

    for ext in image_extensions:
        all_images.extend(list(source_images.glob(ext)))

    print(f"📊 Found {len(all_images)} images")

    if len(all_images) == 0:
        print("❌ No images found!")
        return False

    # Get corresponding labels
    image_label_pairs = []
    for img_path in all_images:
        label_path = source_labels / f"{img_path.stem}.txt"
        if label_path.exists():
            image_label_pairs.append((img_path, label_path))

    print(f"📊 Found {len(image_label_pairs)} image-label pairs")

    if len(image_label_pairs) == 0:
        print("❌ No valid image-label pairs found!")
        return False

    # Split data (80% train, 10% val, 10% test)
    train_pairs, temp_pairs = train_test_split(image_label_pairs, test_size=0.2, random_state=42)
    val_pairs, test_pairs = train_test_split(temp_pairs, test_size=0.5, random_state=42)

    print(f"📊 Train: {len(train_pairs)} pairs")
    print(f"📊 Val: {len(val_pairs)} pairs")
    print(f"📊 Test: {len(test_pairs)} pairs")

    # Copy files to respective directories
    def copy_files(pairs, img_dest, label_dest, split_name):
        for img_path, label_path in pairs:
            # Copy image
            shutil.copy2(str(img_path), str(img_dest / img_path.name))
            # Copy label
            shutil.copy2(str(label_path), str(label_dest / label_path.name))
        print(f"✅ Copied {len(pairs)} pairs to {split_name}")

    # Copy train files
    copy_files(train_pairs, dest_train_images, dest_train_labels, "train")

    # Copy val files
    copy_files(val_pairs, dest_val_images, dest_val_labels, "val")

    # Copy test files
    copy_files(test_pairs, dest_test_images, dest_test_labels, "test")

    # Create data.yaml
    data_yaml_content = f"""train: train/images
val: val/images
test: test/images
nc: 1
names: ['Chinese_Egret']
"""

    data_yaml_path = dest_base / "data.yaml"
    with open(data_yaml_path, 'w') as f:
        f.write(data_yaml_content)

    print("\n✅ CREATED DATA.YAML:")
    print(data_yaml_content)

    print("\n🎯 DATASET STRUCTURE CREATED!")
    print(f"📁 Location: {dest_base.absolute()}")
    print("📊 Total images: ", len(image_label_pairs))
    print("🏷️  Classes: 1 (Chinese Egret only)")

    return True

if __name__ == "__main__":
    success = create_chinese_egret_yolo_dataset()
    if success:
        print("\n🚀 READY FOR TRAINING!")
        print("Run: yolo train model=models/yolov8x.pt data=training_data/final_yolo_dataset/chinese_egret_dataset/data.yaml [other args]")
    else:
        print("\n❌ Dataset creation failed!")
