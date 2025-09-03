#!/usr/bin/env python3
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

def prepare_chinese_egret_data():
    """Minimal data preparation pipeline"""

    print("🦆 Chinese Egret Data Preparation (Standalone)")
    print("=" * 50)

    # 1. Extract YOLO annotations
    print("
1. Extracting YOLO annotations...")
    yolo_path = Path("annotated_datasets/Chinese_Egret/yolo")
    labels_output = Path("prepared_data/labels")
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
    print("
2. Consolidating images...")
    training_path = Path("Chinese_Egret_Training")
    images_output = Path("prepared_data/images")
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
    print("
3. Creating YOLO dataset structure...")
    dataset_path = Path("bird_dataset_v1")

    # Create directories
    for split in ['train', 'valid', 'test']:
        for subdir in ['images', 'labels']:
            (dataset_path / split / subdir).mkdir(parents=True, exist_ok=True)

    # Get image-label pairs
    images_path = Path("prepared_data/images")
    labels_path = Path("prepared_data/labels")

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
    yaml_content = f"""train: {dataset_path}/train
val: {dataset_path}/valid
test: {dataset_path}/test
nc: 1
names: ['Chinese_Egret']
"""

    with open(dataset_path / "data.yaml", 'w', encoding='utf-8') as f:
        f.write(yaml_content)

    print("
✅ Data preparation complete!")
    print(f"📊 Created dataset with {len(pairs)} image-label pairs")
    print(f"📍 Dataset: {dataset_path.absolute()}")

if __name__ == "__main__":
    prepare_chinese_egret_data()
