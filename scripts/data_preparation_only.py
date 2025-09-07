#!/usr/bin/env python3
"""
STANDALONE: Chinese Egret Data Preparation Pipeline

This script demonstrates the EXACT step-by-step process used to prepare
the Chinese Egret training dataset and annotated data, completely separate
from the Platform Avicast web application.

USAGE:
    python data_preparation_only.py

This creates a standalone data preparation workflow that can run independently
of the full Django application.
"""

import shutil
import sys
import zipfile
from pathlib import Path


def step_1_collect_raw_data(base_path: Path):
    """Step 1: Collect and verify raw data sources"""
    print("\n" + "=" * 60)
    print("STEP 1: COLLECT RAW DATA")
    print("=" * 60)

    # Check for annotated datasets
    annotated_path = base_path / "exported_annotations/Chinese_Egret"
    training_path = base_path / "raw_images"

    print("Checking data sources...")

    if not annotated_path.exists():
        print(f"❌ {annotated_path} not found")
        print("   This should contain:")
        print("   - coco/ directory (COCO format annotations)")
        print("   - yolo/ directory (YOLO format annotation ZIPs)")
        return False

    if not training_path.exists():
        print(f"❌ {training_path} not found")
        print("   This should contain batch folders with PNG images")
        return False

    print(f"✅ Found {annotated_path}/")
    print(f"✅ Found {training_path}/")

    # Count YOLO zip files
    yolo_path = annotated_path / "yolo"
    if yolo_path.exists():
        zip_files = list(yolo_path.glob("*.zip"))
        print(f"✅ Found {len(zip_files)} YOLO annotation ZIPs:")
        for zip_file in zip_files:
            print(f"   - {zip_file.name}")

    # Count training batches
    batch_folders = [
        d
        for d in training_path.iterdir()
        if d.is_dir() and d.name.startswith("Chinese_Egret_Batch")
    ]
    print(f"✅ Found {len(batch_folders)} training batches:")
    for batch in sorted(batch_folders):
        png_count = len(list(batch.glob("*.png")))
        print(f"   - {batch.name}: {png_count} images")

    return True


def step_2_extract_annotations(base_path: Path):
    """Step 2: Extract YOLO format annotations"""
    print("\n" + "=" * 60)
    print("STEP 2: EXTRACT YOLO ANNOTATIONS")
    print("=" * 60)

    yolo_path = base_path / "exported_annotations/Chinese_Egret/yolo"
    output_labels = base_path / "prepared_dataset/labels"

    output_labels.mkdir(parents=True, exist_ok=True)

    print("Extracting YOLO annotation ZIP files...")

    zip_files = list(yolo_path.glob("*.zip"))
    total_extracted = 0

    for zip_file in zip_files:
        print(f"📦 Extracting {zip_file.name}...")

        try:
            with zipfile.ZipFile(zip_file, "r") as zip_ref:
                # Extract to temporary directory
                temp_dir = output_labels / f"temp_{zip_file.stem}"
                zip_ref.extractall(temp_dir)

                # Move all .txt files to main labels directory
                txt_files = list(temp_dir.rglob("*.txt"))
                for txt_file in txt_files:
                    target_file = output_labels / txt_file.name
                    if not target_file.exists():
                        shutil.move(str(txt_file), str(target_file))
                        total_extracted += 1

                # Clean up temp directory
                shutil.rmtree(temp_dir)

        except Exception as e:
            print(f"❌ Error extracting {zip_file.name}: {e}")

    print(f"✅ Extracted {total_extracted} annotation files to {output_labels}/")
    return True


def step_3_consolidate_images(base_path: Path):
    """Step 3: Consolidate all training images"""
    print("\n" + "=" * 60)
    print("STEP 3: CONSOLIDATE TRAINING IMAGES")
    print("=" * 60)

    training_path = base_path / "raw_images"
    output_images = base_path / "prepared_dataset/images"

    output_images.mkdir(parents=True, exist_ok=True)

    print("Consolidating images from all batch folders...")

    batch_folders = [
        d
        for d in training_path.iterdir()
        if d.is_dir() and d.name.startswith("Chinese_Egret_Batch")
    ]
    total_images = 0

    for batch_folder in sorted(batch_folders):
        print(f"📁 Processing {batch_folder.name}...")

        batch_images = 0
        image_extensions = [".png", ".jpg", ".jpeg", ".PNG", ".JPG", ".JPEG"]

        for ext in image_extensions:
            image_files = list(batch_folder.glob(f"*{ext}"))

            for image_file in image_files:
                target_file = output_images / image_file.name

                # Avoid duplicates
                if not target_file.exists():
                    shutil.copy2(str(image_file), str(target_file))
                    batch_images += 1

        print(f"   Copied {batch_images} images from {batch_folder.name}")
        total_images += batch_images

    print(f"✅ Consolidated {total_images} images to {output_images}/")
    return True


def step_4_verify_data_integrity(base_path: Path):
    """Step 4: Verify data integrity and matching"""
    print("\n" + "=" * 60)
    print("STEP 4: VERIFY DATA INTEGRITY")
    print("=" * 60)

    images_path = base_path / "prepared_dataset/images"
    labels_path = base_path / "prepared_dataset/labels"

    print("Verifying image-label pairs...")

    # Get all image files
    image_extensions = [".png", ".jpg", ".jpeg", ".PNG", ".JPG", ".JPEG"]
    image_files = []
    for ext in image_extensions:
        image_files.extend(images_path.glob(f"*{ext}"))

    print(f"📷 Found {len(image_files)} image files")

    # Get all label files
    label_files = list(labels_path.glob("*.txt"))
    print(f"🏷️  Found {len(label_files)} label files")

    # Check matching pairs
    matched = 0
    unmatched_images = []
    unmatched_labels = []

    for image_file in image_files:
        label_file = labels_path / f"{image_file.stem}.txt"
        if label_file.exists():
            matched += 1
        else:
            unmatched_images.append(image_file.name)

    for label_file in label_files:
        image_file = images_path / f"{label_file.stem}.png"
        if not image_file.exists():
            # Check other extensions
            found = False
            for ext in image_extensions[1:]:  # Skip .png since we already checked
                alt_image = images_path / f"{label_file.stem}{ext}"
                if alt_image.exists():
                    found = True
                    break
            if not found:
                unmatched_labels.append(label_file.name)

    print("\n📊 Matching Results:")
    print(f"   ✅ Matched pairs: {matched}")
    print(f"   ⚠️  Images without labels: {len(unmatched_images)}")
    print(f"   ⚠️  Labels without images: {len(unmatched_labels)}")

    if unmatched_images:
        print("\nImages missing labels:")
        for img in unmatched_images[:5]:
            print(f"   - {img}")
        if len(unmatched_images) > 5:
            print(f"   ... and {len(unmatched_images) - 5} more")

    if unmatched_labels:
        print("\nLabels missing images:")
        for lbl in unmatched_labels[:5]:
            print(f"   - {lbl}")
        if len(unmatched_labels) > 5:
            print(f"   ... and {len(unmatched_labels) - 5} more")

    return matched > 0


def step_5_create_dataset_structure(base_path: Path):
    """Step 5: Create YOLO dataset structure"""
    print("\n" + "=" * 60)
    print("STEP 5: CREATE YOLO DATASET STRUCTURE")
    print("=" * 60)

    output_path = base_path / "final_yolo_dataset/bird_dataset_v1"
    images_path = base_path / "prepared_dataset/images"
    labels_path = base_path / "prepared_dataset/labels"

    print(f"Creating YOLO dataset structure in {output_path}/...")

    # Create directory structure
    directories = [
        "train/images",
        "train/labels",
        "valid/images",
        "valid/labels",
        "test/images",
        "test/labels",
    ]

    for directory in directories:
        (output_path / directory).mkdir(parents=True, exist_ok=True)

    # Get all image-label pairs
    image_extensions = [".png", ".jpg", ".jpeg", ".PNG", ".JPG", ".JPEG"]
    pairs = []

    for ext in image_extensions:
        for image_file in images_path.glob(f"*{ext}"):
            label_file = labels_path / f"{image_file.stem}.txt"
            if label_file.exists():
                pairs.append((image_file, label_file))

    print(f"📋 Found {len(pairs)} valid image-label pairs")

    # Split dataset (80% train, 10% valid, 10% test)
    import random

    random.seed(42)  # For reproducible splits

    shuffled_pairs = pairs.copy()
    random.shuffle(shuffled_pairs)

    n_total = len(shuffled_pairs)
    n_train = int(n_total * 0.8)
    n_valid = int(n_total * 0.1)

    train_pairs = shuffled_pairs[:n_train]
    valid_pairs = shuffled_pairs[n_train : n_train + n_valid]
    test_pairs = shuffled_pairs[n_train + n_valid :]

    # Copy files to respective directories
    splits = [(train_pairs, "train"), (valid_pairs, "valid"), (test_pairs, "test")]

    total_files = 0
    for split_pairs, split_name in splits:
        print(f"📂 Creating {split_name} split ({len(split_pairs)} pairs)...")

        for image_file, label_file in split_pairs:
            # Copy image
            shutil.copy2(
                str(image_file), str(output_path / split_name / "images" / image_file.name)
            )
            # Copy label
            shutil.copy2(
                str(label_file), str(output_path / split_name / "labels" / label_file.name)
            )

        total_files += len(split_pairs) * 2

    print(f"✅ Created dataset with {total_files} files")

    # Create data.yaml configuration
    print("📝 Creating data.yaml configuration...")

    data_yaml_content = f"""# Chinese Egret Dataset Configuration
# Generated for YOLOv8 training

# Dataset paths
train: train/images
val: valid/images
test: test/images

# Number of classes
nc: 1

# Class names
names: ['Chinese_Egret']

# Dataset statistics
# Total images: {len(pairs)}
# Training: {len(train_pairs)} ({len(train_pairs)/len(pairs)*100:.1f}%)
# Validation: {len(valid_pairs)} ({len(valid_pairs)/len(pairs)*100:.1f}%)
# Test: {len(test_pairs)} ({len(test_pairs)/len(pairs)*100:.1f}%)
"""

    data_yaml_path = output_path / "data.yaml"
    with open(data_yaml_path, "w", encoding="utf-8") as f:
        f.write(data_yaml_content)

    print(f"✅ Created {data_yaml_path}")

    return True


def step_6_validate_final_dataset(base_path: Path):
    """Step 6: Validate the final dataset"""
    print("\n" + "=" * 60)
    print("STEP 6: VALIDATE FINAL DATASET")
    print("=" * 60)

    dataset_path = base_path / "final_yolo_dataset/bird_dataset_v1"

    print("Validating final dataset structure...")

    # Check directory structure
    required_dirs = [
        "train/images",
        "train/labels",
        "valid/images",
        "valid/labels",
        "test/images",
        "test/labels",
    ]

    for dir_path in required_dirs:
        full_path = dataset_path / dir_path
        if not full_path.exists():
            print(f"❌ Missing directory: {full_path}")
            return False
        print(f"✅ {dir_path}/ exists")

    # Count files in each split
    for split in ["train", "valid", "test"]:
        img_dir = dataset_path / split / "images"
        lbl_dir = dataset_path / split / "labels"

        image_count = len(list(img_dir.glob("*")))
        label_count = len(list(lbl_dir.glob("*.txt")))

        print(f"📊 {split.capitalize()}: {image_count} images, {label_count} labels")

        if image_count != label_count:
            print(
                f"⚠️  Warning: Mismatch in {split} split ({image_count} images vs {label_count} labels)"
            )

    # Validate data.yaml
    yaml_path = dataset_path / "data.yaml"
    if yaml_path.exists():
        print("✅ data.yaml exists")
    else:
        print("❌ data.yaml missing")
        return False

    print("\n🎉 Dataset preparation completed successfully!")
    print(f"📍 Dataset location: {dataset_path.absolute()}")

    return True


def create_standalone_data_prep_script(base_path: Path):
    """Create a standalone script with just the data preparation steps"""
    print("\n" + "=" * 60)
    print("CREATING STANDALONE DATA PREPARATION SCRIPT")
    print("=" * 60)

    script_content = '''#!/usr/bin/env python3
"""
MINIMAL: Chinese Egret Data Preparation Only

This is a stripped-down version containing ONLY the data preparation steps,
completely separate from the Platform Avicast web application.

Run this to prepare your Chinese Egret training data independently.
"""

import os
import sys
import shutil
from pathlib import Path
import zipfile
import random

def prepare_chinese_egret_data(base_path: Path):
    """Minimal data preparation pipeline"""

    print("🦆 Chinese Egret Data Preparation (Standalone)")
    print("=" * 50)

    # 1. Extract YOLO annotations
    print("\n1. Extracting YOLO annotations...")
    yolo_path = base_path / "exported_annotations/Chinese_Egret/yolo"
    labels_output = base_path / "prepared_dataset/labels"
    labels_output.mkdir(parents=True, exist_ok=True)

    if yolo_path.exists():
        zip_files = list(yolo_path.glob("*.zip"))
        for zip_file in zip_files:
            try:
                with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                    temp_dir = labels_output / f"temp_{zip_file.stem}"
                    zip_ref.extractall(temp_dir)

                    txt_files = list(temp_dir.rglob("*.txt"))
                    for txt_file in txt_files:
                        target = labels_output / txt_file.name
                        if not target.exists():
                            shutil.move(str(txt_file), str(target))

                    shutil.rmtree(temp_dir)
            except Exception as e:
                print(f"Error extracting {zip_file.name}: {e}")

    # 2. Consolidate images
    print("\n2. Consolidating images...")
    training_path = base_path / "raw_images"
    images_output = base_path / "prepared_dataset/images"
    images_output.mkdir(parents=True, exist_ok=True)

    if training_path.exists():
        batch_folders = [d for d in training_path.iterdir()
                        if d.is_dir() and d.name.startswith("Chinese_Egret_Batch")]

        for batch in sorted(batch_folders):
            for ext in ['.png', '.jpg', '.jpeg', '.PNG', '.JPG', '.JPEG']:
                for img_file in batch.glob(f"*{ext}"):
                    target = images_output / img_file.name
                    if not target.exists():
                        shutil.copy2(str(img_file), str(target))

    # 3. Create dataset structure
    print("\n3. Creating YOLO dataset structure...")
    dataset_path = base_path / "final_yolo_dataset/bird_dataset_v1"

    # Create directories
    for split in ['train', 'valid', 'test']:
        for subdir in ['images', 'labels']:
            (dataset_path / split / subdir).mkdir(parents=True, exist_ok=True)

    # Get image-label pairs
    images_path = base_path / "prepared_dataset/images"
    labels_path = base_path / "prepared_dataset/labels"

    pairs = []
    for ext in ['.png', '.jpg', '.jpeg', '.PNG', '.JPG', '.JPEG']:
        for img_file in images_path.glob(f"*{ext}"):
            lbl_file = labels_path / f"{img_file.stem}.txt"
            if lbl_file.exists():
                pairs.append((img_file, lbl_file))

    # Split and copy files
    random.seed(42)
    random.shuffle(pairs)

    n_train = int(len(pairs) * 0.8)
    n_valid = int(len(pairs) * 0.1)

    splits_data = [
        (pairs[:n_train], 'train'),
        (pairs[n_train:n_train + n_valid], 'valid'),
        (pairs[n_train + n_valid:], 'test')
    ]

    for split_pairs, split_name in splits_data:
        for img_file, lbl_file in split_pairs:
            shutil.copy2(str(img_file), str(dataset_path / split_name / 'images' / img_file.name))
            shutil.copy2(str(lbl_file), str(dataset_path / split_name / 'labels' / lbl_file.name))

    # Create data.yaml
    yaml_content = f"""train: train/images
val: valid/images
test: test/images
nc: 1
names: ['Chinese_Egret']
"""

    with open(dataset_path / "data.yaml", 'w', encoding='utf-8') as f:
        f.write(yaml_content)

    print("\n✅ Data preparation complete!")
    print(f"📊 Created dataset with {len(pairs)} image-label pairs")
    print(f"📍 Dataset: {dataset_path.absolute()}")

if __name__ == "__main__":
    base_path = Path("training_data")
    prepare_chinese_egret_data(base_path)
'''

    script_path = base_path / "scripts/prepare_data_minimal.py"
    script_path.parent.mkdir(parents=True, exist_ok=True)
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script_content)

    print(f"✅ Created standalone script: {script_path}")
    print("\n📝 This script contains ONLY the data preparation steps")
    print("   - No web application dependencies")
    print("   - No Django framework")
    print("   - Just pure data processing")

    return script_path


def main():
    """Main data preparation pipeline"""

    print("🦆 CHINESE EGRET DATA PREPARATION PIPELINE")
    print("=" * 60)
    print("This demonstrates the STANDALONE data preparation process")
    print("used to create the training dataset, separate from Platform Avicast")
    print("=" * 60)

    # Define base path for all training data
    base_path = Path("training_data")

    # Execute steps
    steps = [
        (step_1_collect_raw_data, [base_path]),
        (step_2_extract_annotations, [base_path]),
        (step_3_consolidate_images, [base_path]),
        (step_4_verify_data_integrity, [base_path]),
        (step_5_create_dataset_structure, [base_path]),
        (step_6_validate_final_dataset, [base_path]),
    ]

    for step, args in steps:
        try:
            success = step(*args)
            if not success:
                print(f"\n❌ Step failed: {step.__name__}")
                sys.exit(1)
        except Exception as e:
            print(f"\n❌ Error in {step.__name__}: {e}")
            sys.exit(1)

    # Create standalone script
    standalone_script = create_standalone_data_prep_script(base_path)

    print("\n" + "=" * 60)
    print("🎉 COMPLETE DATA PREPARATION PIPELINE FINISHED!")
    print("=" * 60)
    print("\n📋 What was accomplished:")
    print("   ✅ Extracted YOLO annotations from ZIP files")
    print("   ✅ Consolidated images from all training batches")
    print("   ✅ Verified data integrity and matching")
    print("   ✅ Created YOLO dataset structure (train/valid/test)")
    print("   ✅ Generated data.yaml configuration")
    print("   ✅ Created standalone preparation script")
    print("\n📁 Output locations:")
    print(f"   - Prepared data: {base_path / 'prepared_dataset'}")
    print(f"   - Final dataset: {base_path / 'final_yolo_dataset' / 'bird_dataset_v1'}")
    print(f"   - Standalone script: {standalone_script}")
    print("\n🚀 Ready for training with:")
    print("   python prepare_data_minimal.py  # To recreate from scratch")
    print("   python train_chinese_egret.py --model-size s --epochs 100  # To train")


if __name__ == "__main__":
    main()
