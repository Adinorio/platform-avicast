#!/usr/bin/env python3
"""
Consolidate all Chinese Egret data from multiple sources for maximum dataset size
"""

import os
import shutil
from pathlib import Path
import random

def consolidate_maximum_chinese_egret():
    """Consolidate all available Chinese Egret data"""

    print("🦆 CONSOLIDATING MAXIMUM CHINESE EGRET DATASET")
    print("=" * 60)

    # Paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent

    # Source directories
    prepared_images = project_root / "training_data" / "prepared_dataset" / "chinese_egret_dataset" / "images"
    prepared_labels = project_root / "training_data" / "prepared_dataset" / "chinese_egret_dataset" / "labels"
    temp_extracted = project_root / "training_data" / "temp_extracted"

    # Destination
    final_dataset = project_root / "training_data" / "final_yolo_dataset" / "chinese_egret_maximum"

    print("📂 SOURCES:")
    print(f"  🖼️  Prepared images: {prepared_images}")
    print(f"  🏷️  Prepared labels: {prepared_labels}")
    print(f"  📦 Extracted labels: {temp_extracted}")

    # Create destination structure
    for split in ['train', 'val', 'test']:
        (final_dataset / split / 'images').mkdir(parents=True, exist_ok=True)
        (final_dataset / split / 'labels').mkdir(parents=True, exist_ok=True)

    # Get all available images from prepared dataset
    image_extensions = ['*.png', '*.jpg', '*.jpeg', '*.PNG', '*.JPG', '*.JPEG']
    all_images = []

    for ext in image_extensions:
        all_images.extend(list(prepared_images.glob(ext)))

    print(f"\n📊 FOUND {len(all_images)} IMAGES IN PREPARED DATASET")

    # Get all available labels (prepared + extracted)
    all_labels = []

    # From prepared dataset
    prepared_label_files = list(prepared_labels.glob("*.txt"))
    all_labels.extend(prepared_label_files)
    print(f"📊 FOUND {len(prepared_label_files)} LABELS IN PREPARED DATASET")

    # From extracted YOLO files
    extracted_labels = 0
    for yolo_dir in temp_extracted.glob("yolo_*"):
        obj_train_data = yolo_dir / "obj_train_data"
        if obj_train_data.exists():
            yolo_labels = list(obj_train_data.glob("*.txt"))
            all_labels.extend(yolo_labels)
            extracted_labels += len(yolo_labels)
            print(f"📊 FOUND {len(yolo_labels)} LABELS IN {yolo_dir.name}")

    print(f"\n📊 TOTAL LABELS: {len(all_labels)}")

    # Create image-label pairs
    image_label_pairs = []
    matched_images = 0
    matched_labels = 0

    for image_path in all_images:
        label_path = prepared_labels / f"{image_path.stem}.txt"

        # Try to find matching label in any of the sources
        found_label = False

        # First check prepared labels
        if label_path.exists():
            image_label_pairs.append((image_path, label_path))
            matched_images += 1
            matched_labels += 1
            found_label = True

        # If not found in prepared, check extracted labels
        if not found_label:
            for yolo_dir in temp_extracted.glob("yolo_*"):
                obj_train_data = yolo_dir / "obj_train_data"
                extracted_label = obj_train_data / f"{image_path.stem}.txt"
                if extracted_label.exists():
                    image_label_pairs.append((image_path, extracted_label))
                    matched_images += 1
                    matched_labels += 1
                    found_label = True
                    break

    print("\n🔗 MATCHING RESULTS:")
    print(f"   ✅ Matched pairs: {len(image_label_pairs)}")
    print(f"   🖼️  Images matched: {matched_images}")
    print(f"   🏷️  Labels matched: {matched_labels}")

    # Analyze label content for mixed species
    mixed_species_count = 0
    chinese_only_count = 0
    other_species_labels = set()

    for _, label_path in image_label_pairs:
        with open(label_path, 'r') as f:
            lines = f.readlines()

        classes_in_image = set()
        for line in lines:
            if line.strip():
                parts = line.strip().split()
                if len(parts) >= 1:
                    class_id = int(parts[0])
                    classes_in_image.add(class_id)
                    if class_id not in [0, 3, 5]:  # Chinese=0, Little=3, Intermediate=5
                        other_species_labels.add(class_id)

        if len(classes_in_image) > 1:
            mixed_species_count += 1
        else:
            chinese_only_count += 1

    print("\n📊 DATASET COMPOSITION:")
    print(f"   🦆 Pure Chinese Egret: {chinese_only_count}")
    print(f"   🔄 Mixed species: {mixed_species_count}")
    print(f"   📈 Mixed percentage: {(mixed_species_count / len(image_label_pairs) * 100):.1f}%")

    if other_species_labels:
        print(f"   🎯 Other species found: {sorted(other_species_labels)}")

    # Split data: 80-10-10
    random.seed(42)
    random.shuffle(image_label_pairs)

    n_total = len(image_label_pairs)
    n_train = int(n_total * 0.8)
    n_val = int(n_total * 0.1)
    n_test = n_total - n_train - n_val

    train_pairs = image_label_pairs[:n_train]
    val_pairs = image_label_pairs[n_train:n_train + n_val]
    test_pairs = image_label_pairs[n_train + n_val:]

    print("\n📊 DATA SPLIT (80-10-10):")
    print(f"   🏋️  Train: {len(train_pairs)} pairs")
    print(f"   ✅ Val: {len(val_pairs)} pairs")
    print(f"   🧪 Test: {len(test_pairs)} pairs")

    # Copy files to respective directories
    def copy_files(pairs, img_dest, label_dest, split_name):
        copied = 0
        for img_path, label_path in pairs:
            # Copy image
            shutil.copy2(str(img_path), str(img_dest / img_path.name))
            # Copy label
            shutil.copy2(str(label_path), str(label_dest / label_path.name))
            copied += 1
        print(f"   ✅ Copied {copied} pairs to {split_name}")
        return copied

    # Copy train files
    train_img_dest = final_dataset / "train" / "images"
    train_label_dest = final_dataset / "train" / "labels"
    copy_files(train_pairs, train_img_dest, train_label_dest, "train")

    # Copy val files
    val_img_dest = final_dataset / "val" / "images"
    val_label_dest = final_dataset / "val" / "labels"
    copy_files(val_pairs, val_img_dest, val_label_dest, "val")

    # Copy test files
    test_img_dest = final_dataset / "test" / "images"
    test_label_dest = final_dataset / "test" / "labels"
    copy_files(test_pairs, test_img_dest, test_label_dest, "test")

    # Create data.yaml
    data_yaml_content = f"""train: train/images
val: val/images
test: test/images
nc: 1
names: ['Chinese_Egret']
"""

    data_yaml_path = final_dataset / "data.yaml"
    with open(data_yaml_path, 'w') as f:
        f.write(data_yaml_content)

    print("\n✅ DATA.YAML CREATED")
    print(f"📁 Dataset location: {final_dataset}")
    print(f"📊 Total images: {len(image_label_pairs)}")
    print(f"📊 Mixed species: {mixed_species_count} ({(mixed_species_count / len(image_label_pairs) * 100):.1f}%)")

    return final_dataset, len(image_label_pairs), mixed_species_count

if __name__ == "__main__":
    dataset_path, total_images, mixed_count = consolidate_maximum_chinese_egret()

    print("\n🎯 READY FOR MAXIMUM ACCURACY TRAINING!")
    print(f"📁 Dataset: {dataset_path}")
    print("🚀 Next: Run training with 200 epochs, batch size 20")
