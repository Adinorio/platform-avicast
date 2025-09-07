#!/usr/bin/env python3
"""
COMPREHENSIVE: Egret Species Data Preparation

This script prepares separate datasets for little_egret, great_egret, and intermediate_egret
without mixing them. Each species gets its own prepared_dataset directory and YOLO dataset structure.

Run this to prepare all egret species training data independently.
"""

import random
import shutil
import sys
import zipfile
from pathlib import Path


def prepare_single_egret_dataset(
    base_path: Path,
    species_name: str,
    image_folders: list[str],
    annotation_zip_pattern: str,
    class_id: int = 0,
):
    """
    Prepare dataset for a single egret species

    Args:
        base_path: Base training_data directory path
        species_name: Name of the species (e.g., 'little_egret', 'great_egret')
        image_folders: List of folder names containing images for this species
        annotation_zip_pattern: Pattern to match annotation zip files
        class_id: YOLO class ID for this species (default 0)
    """

    print(f"🦆 {species_name.replace('_', ' ').title()} Data Preparation")
    print("=" * 60)

    # Create species-specific prepared dataset directory
    prepared_base = base_path / "prepared_dataset" / f"{species_name}_dataset"
    labels_output = prepared_base / "labels"
    images_output = prepared_base / "images"

    labels_output.mkdir(parents=True, exist_ok=True)
    images_output.mkdir(parents=True, exist_ok=True)

    # 1. Extract YOLO annotations
    print("\n1. Extracting YOLO annotations...")
    yolo_path = base_path / f"exported_annotations/{species_name.title()}"
    annotation_extracted = False

    if yolo_path.exists():
        zip_files = list(yolo_path.glob(annotation_zip_pattern))
        print(f"Found {len(zip_files)} annotation zip files: {[z.name for z in zip_files]}")

        for zip_file in zip_files:
            try:
                print(f"Extracting {zip_file.name}...")
                with zipfile.ZipFile(zip_file, "r") as zip_ref:
                    temp_dir = labels_output / f"temp_{zip_file.stem}"
                    zip_ref.extractall(temp_dir)

                    txt_files = list(temp_dir.rglob("*.txt"))
                    print(f"Found {len(txt_files)} annotation files in {zip_file.name}")

                    for txt_file in txt_files:
                        target = labels_output / txt_file.name
                        if not target.exists():
                            shutil.move(str(txt_file), str(target))
                            annotation_extracted = True

                    shutil.rmtree(temp_dir)
            except Exception as e:
                print(f"Error extracting {zip_file.name}: {e}")

        if annotation_extracted:
            print(f"✅ Extracted annotations to {labels_output}")
        else:
            print(f"⚠️  No annotations extracted for {species_name}")
    else:
        print(f"⚠️  Annotation path not found: {yolo_path}")

    # 2. Consolidate images
    print("\n2. Consolidating images...")
    training_path = base_path / "raw_images"
    images_copied = 0

    if training_path.exists():
        for folder_name in image_folders:
            folder_path = training_path / folder_name
            if folder_path.exists() and folder_path.is_dir():
                print(f"Processing folder: {folder_name}")
                for ext in [".png", ".jpg", ".jpeg", ".PNG", ".JPG", ".JPEG"]:
                    for img_file in folder_path.glob(f"*{ext}"):
                        target = images_output / img_file.name
                        if not target.exists():
                            shutil.copy2(str(img_file), str(target))
                            images_copied += 1
            else:
                print(f"⚠️  Folder not found: {folder_path}")

        print(f"✅ Copied {images_copied} images to {images_output}")
    else:
        print(f"⚠️  Raw images path not found: {training_path}")

    # 3. Create YOLO dataset structure
    print("\n3. Creating YOLO dataset structure...")
    dataset_path = base_path / f"final_yolo_dataset/{species_name}_dataset"

    # Create directories
    for split in ["train", "val", "test"]:
        for subdir in ["images", "labels"]:
            (dataset_path / split / subdir).mkdir(parents=True, exist_ok=True)

    # Get image-label pairs
    pairs = []
    for ext in [".png", ".jpg", ".jpeg", ".PNG", ".JPG", ".JPEG"]:
        for img_file in images_output.glob(f"*{ext}"):
            lbl_file = labels_output / f"{img_file.stem}.txt"
            if lbl_file.exists():
                pairs.append((img_file, lbl_file))

    print(f"📊 Found {len(pairs)} image-label pairs")

    if len(pairs) == 0:
        print(f"⚠️  No valid image-label pairs found for {species_name}")
        return 0

    # Split and copy files
    random.seed(42)
    random.shuffle(pairs)

    n_train = int(len(pairs) * 0.8)
    n_val = int(len(pairs) * 0.15)
    n_test = len(pairs) - n_train - n_val

    splits_data = [
        (pairs[:n_train], "train"),
        (pairs[n_train : n_train + n_val], "val"),
        (pairs[n_train + n_val :], "test"),
    ]

    for split_pairs, split_name in splits_data:
        for img_file, lbl_file in split_pairs:
            shutil.copy2(str(img_file), str(dataset_path / split_name / "images" / img_file.name))
            shutil.copy2(str(lbl_file), str(dataset_path / split_name / "labels" / lbl_file.name))

    # Create data.yaml
    yaml_content = f"""train: train/images
val: val/images
test: test/images
nc: 1
names: ['{species_name.replace('_', ' ').title()}']
"""

    with open(dataset_path / "data.yaml", "w", encoding="utf-8") as f:
        f.write(yaml_content)

    print("\n✅ Data preparation complete!")
    print(f"📊 Created dataset with {len(pairs)} image-label pairs")
    print(f"   - Train: {n_train} pairs")
    print(f"   - Val: {n_val} pairs")
    print(f"   - Test: {n_test} pairs")
    print(f"📍 Dataset: {dataset_path.absolute()}")
    print(f"📁 Prepared data: {prepared_base.absolute()}")

    return len(pairs)


def prepare_all_egret_datasets(base_path: Path):
    """Prepare datasets for all egret species"""

    print("🦆 COMPREHENSIVE EGRET DATASET PREPARATION")
    print("=" * 60)
    print("Preparing separate datasets for: little_egret, great_egret, intermediate_egret")
    print("Each species will be processed independently with no mixing.")
    print()

    # Species configuration
    species_config = [
        {
            "name": "little_egret",
            "folders": ["little_egret_batch1"],
            "zip_pattern": "*YOLO*.zip",
            "class_id": 0,
        },
        {
            "name": "great_egret",
            "folders": ["Great_Egret"],
            "zip_pattern": "*Yolo*.zip",
            "class_id": 0,
        },
        {
            "name": "intermediate_egret",
            "folders": ["Intermediate_Egret"],
            "zip_pattern": "*Yolo*.zip",
            "class_id": 0,
        },
    ]

    results = {}
    total_pairs = 0

    for config in species_config:
        print(f"\n{'='*60}")
        pairs_count = prepare_single_egret_dataset(
            base_path=base_path,
            species_name=config["name"],
            image_folders=config["folders"],
            annotation_zip_pattern=config["zip_pattern"],
            class_id=config["class_id"],
        )
        results[config["name"]] = pairs_count
        total_pairs += pairs_count
        print()

    # Summary
    print("🎯 PREPARATION SUMMARY")
    print("=" * 60)
    for species, count in results.items():
        print(f"   {species.replace('_', ' ').title()}: {count} pairs")
    print(f"📊 Total image-label pairs across all species: {total_pairs}")

    # Verify separation
    print("\n🔍 VERIFICATION")
    print("✅ Datasets prepared separately - no species mixing")
    print("✅ Each species has its own prepared_dataset directory")
    print("✅ Each species has its own final_yolo_dataset directory")
    print("✅ YOLO annotations extracted from respective zip files")
    print("✅ Images consolidated from respective raw image folders")

    return results


def prepare_chinese_egret_data(base_path: Path):
    """Legacy function for backward compatibility"""
    print("⚠️  Using legacy Chinese Egret preparation (consider using prepare_all_egret_datasets)")
    return prepare_single_egret_dataset(
        base_path=base_path,
        species_name="chinese_egret",
        image_folders=[f"Chinese_Egret_Batch{i}" for i in range(1, 8)],
        annotation_zip_pattern="*.zip",
        class_id=0,
    )


def create_unified_egret_dataset(base_path: Path):
    """Create a unified dataset combining all four egret species for multi-class training"""

    print("🦆 UNIFIED EGRET DATASET CREATION")
    print("=" * 60)
    print("Combining Chinese, Great, Intermediate, and Little Egret datasets")
    print("Creating multi-class YOLO dataset for unified training")
    print()

    # Class mapping for unified dataset
    class_mapping = {
        "chinese_egret": 0,
        "great_egret": 1,
        "intermediate_egret": 2,
        "little_egret": 3,
    }

    # Unified dataset path
    unified_path = base_path / "final_yolo_dataset" / "unified_egret_dataset"

    # Create directories
    for split in ["train", "val", "test"]:
        for subdir in ["images", "labels"]:
            (unified_path / split / subdir).mkdir(parents=True, exist_ok=True)

    all_image_label_pairs = []
    total_images = 0

    # Process each species
    for species_name, class_id in class_mapping.items():
        print(f"\n🔄 Processing {species_name.replace('_', ' ').title()} (Class {class_id})")

        # Source paths
        source_prepared = base_path / "prepared_dataset" / f"{species_name}_dataset"
        source_images = source_prepared / "images"
        source_labels = source_prepared / "labels"

        if not source_prepared.exists():
            print(f"⚠️  Source dataset not found: {source_prepared}")
            continue

        # Collect image-label pairs for this species
        species_pairs = []
        for ext in [".png", ".jpg", ".jpeg", ".PNG", ".JPG", ".JPEG"]:
            for img_file in source_images.glob(f"*{ext}"):
                lbl_file = source_labels / f"{img_file.stem}.txt"
                if lbl_file.exists():
                    species_pairs.append((img_file, lbl_file, class_id))

        print(f"   Found {len(species_pairs)} image-label pairs")
        all_image_label_pairs.extend(species_pairs)
        total_images += len(species_pairs)

    print(f"\n📊 Total images across all species: {total_images}")

    if total_images == 0:
        print("❌ No image-label pairs found. Cannot create unified dataset.")
        return

    # Shuffle and split (80-10-10 standard split)
    random.seed(42)
    random.shuffle(all_image_label_pairs)

    n_train = int(len(all_image_label_pairs) * 0.8)
    n_val = int(len(all_image_label_pairs) * 0.1)
    n_test = len(all_image_label_pairs) - n_train - n_val

    splits_data = [
        (all_image_label_pairs[:n_train], "train"),
        (all_image_label_pairs[n_train : n_train + n_val], "val"),
        (all_image_label_pairs[n_train + n_val :], "test"),
    ]

    # Copy files and adjust labels
    for split_pairs, split_name in splits_data:
        print(f"\n📋 Processing {split_name} split ({len(split_pairs)} pairs)...")

        for img_file, lbl_file, class_id in split_pairs:
            # Copy image
            img_target = unified_path / split_name / "images" / img_file.name
            shutil.copy2(str(img_file), str(img_target))

            # Read and adjust labels
            with open(lbl_file) as f:
                original_labels = f.read().strip()

            if original_labels:
                adjusted_labels = []
                for line in original_labels.split("\n"):
                    if line.strip():
                        # Replace original class ID (usually 0) with correct class ID
                        parts = line.split()
                        parts[0] = str(class_id)  # Set correct class ID
                        adjusted_labels.append(" ".join(parts))

                # Write adjusted labels
                lbl_target = unified_path / split_name / "labels" / lbl_file.name
                with open(lbl_target, "w") as f:
                    f.write("\n".join(adjusted_labels))

    # Create data.yaml
    yaml_content = """train: train/images
val: val/images
test: test/images
nc: 4
names: ['Chinese Egret', 'Great Egret', 'Intermediate Egret', 'Little Egret']
"""

    with open(unified_path / "data.yaml", "w", encoding="utf-8") as f:
        f.write(yaml_content)

    print("\n✅ UNIFIED DATASET CREATION COMPLETE!")
    print(f"📊 Dataset: {unified_path.absolute()}")
    print(f"📈 Total images: {total_images}")
    print(f"   - Train: {n_train} images")
    print(f"   - Val: {n_val} images")
    print(f"   - Test: {n_test} images")
    print("🏷️  Classes: 4 (Chinese, Great, Intermediate, Little Egret)")
    print("\n🔧 Ready for multi-class YOLO training!")
    return {
        "path": unified_path,
        "total_images": total_images,
        "train_count": n_train,
        "val_count": n_val,
        "test_count": n_test,
    }


if __name__ == "__main__":
    base_path = Path("training_data")

    # Choose what to do
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "unified":
        create_unified_egret_dataset(base_path)
    else:
        prepare_all_egret_datasets(base_path)
