#!/usr/bin/env python3
"""
Refactoring Script for Training Data Architecture

This script restructures the training data into a clean, self-contained
'training_data' directory, following a logical data flow architecture.

It performs the following actions:
1. Creates the new directory structure.
2. Moves existing raw data (images, annotations) to the new structure.
3. Cleans up the old directories from the project root.
4. Creates a README.md explaining the new architecture.
"""

import shutil
from pathlib import Path


def refactor_training_data_structure():
    """Refactors the training data into a new clean architecture."""

    print("🚀 Starting Training Data Refactoring...")
    print("=" * 60)

    # Define new paths
    base_path = Path("training_data")
    paths = {
        "base": base_path,
        "raw_images": base_path / "raw_images",
        "exported_annotations": base_path / "exported_annotations",
        "prepared_dataset": base_path / "prepared_dataset",
        "final_yolo_dataset": base_path / "final_yolo_dataset",
    }

    # Define old paths
    old_paths = {
        "training_images": Path("Chinese_Egret_Training"),
        "annotations": Path("annotated_datasets/Chinese_Egret"),
        "prepared_data": Path("prepared_data"),
        "final_dataset": Path("bird_dataset_v1"),
    }

    # 1. Create new directory structure
    print("1. Creating new directory structure...")
    for key, path in paths.items():
        path.mkdir(parents=True, exist_ok=True)
        print(f"   ✅ Created: {path}")

    # 2. Move existing data
    print("\n2. Moving existing data to new locations...")

    # Move raw training images
    if old_paths["training_images"].exists():
        print(f"   🚚 Moving {old_paths['training_images']} -> {paths['raw_images']}")
        # Move contents of the directory to avoid nested folder
        for item in old_paths["training_images"].iterdir():
            shutil.move(str(item), str(paths["raw_images"] / item.name))
        try:
            old_paths["training_images"].rmdir()
        except OSError:
            # The directory might not be empty if there are hidden files
            shutil.rmtree(str(old_paths["training_images"]))

        print("   ✅ Moved raw images.")
    else:
        print(f"   ⚠️  Warning: {old_paths['training_images']} not found, skipping.")

    # Move exported annotations
    if old_paths["annotations"].exists():
        target_path = paths["exported_annotations"] / "Chinese_Egret"
        print(f"   🚚 Moving {old_paths['annotations']} -> {target_path}")
        if target_path.exists():
            shutil.rmtree(target_path)
        shutil.move(str(old_paths["annotations"]), str(target_path))
        # Clean up empty parent if it exists
        if Path("annotated_datasets").exists() and not any(Path("annotated_datasets").iterdir()):
            Path("annotated_datasets").rmdir()
        print("   ✅ Moved annotations.")
    else:
        print(f"   ⚠️  Warning: {old_paths['annotations']} not found, skipping.")

    # Move prepared data
    if old_paths["prepared_data"].exists():
        print(f"   🚚 Moving {old_paths['prepared_data']} -> {paths['prepared_dataset']}")
        # Move contents to avoid nesting
        for item in old_paths["prepared_data"].iterdir():
            shutil.move(str(item), str(paths["prepared_dataset"] / item.name))
        try:
            old_paths["prepared_data"].rmdir()
        except OSError:
            shutil.rmtree(str(old_paths["prepared_data"]))
        print("   ✅ Moved prepared data.")
    else:
        print(f"   ⚠️  Warning: {old_paths['prepared_data']} not found, skipping.")

    # Move final dataset
    if old_paths["final_dataset"].exists():
        target_path = paths["final_yolo_dataset"] / "bird_dataset_v1"
        print(f"   🚚 Moving {old_paths['final_dataset']} -> {target_path}")
        if target_path.exists():
            shutil.rmtree(target_path)
        shutil.move(str(old_paths["final_dataset"]), str(target_path))
        print("   ✅ Moved final YOLO dataset.")
    else:
        print(f"   ⚠️  Warning: {old_paths['final_dataset']} not found, skipping.")

    # 3. Create README for the new structure
    print("\n3. Creating documentation for the new structure...")
    readme_content = """# 🦆 Chinese Egret Training Data Architecture

This directory contains all data, scripts, and configurations related to training
the Chinese Egret detection model. It follows a clean, logical data flow.

## 📁 Directory Structure

- **`raw_images/`**: Contains the original, unprocessed training images organized in batch folders. This is the raw input.

- **`exported_annotations/`**: Contains the original annotation files as exported from labeling tools (e.g., COCO JSON, YOLO ZIPs).

- **`prepared_dataset/`**: This is an intermediate directory holding the consolidated data after initial processing.
  - `images/`: All raw images copied into a single folder.
  - `labels/`: All annotations extracted into `.txt` format in a single folder.

- **`final_yolo_dataset/`**: Contains the final, analysis-ready dataset, split into training, validation, and test sets in the format required by YOLOv8.
  - `bird_dataset_v1/`: The final dataset, ready for training.

## 🔄 Data Flow

1.  **Raw Data**: Starts in `raw_images/` and `exported_annotations/`.
2.  **Preparation**: Scripts process this raw data and place the consolidated, clean files into `prepared_dataset/`.
3.  **Organization**: Scripts then split the prepared data into `train/`, `valid/`, and `test/` sets, creating the `final_yolo_dataset/`.
4.  **Training**: The training pipeline reads directly from `final_yolo_dataset/`.

## 🚀 How to Use

1.  **Place Data**: Add raw images to `raw_images/` and annotations to `exported_annotations/`.
2.  **Run Preparation**: Execute the data preparation scripts (e.g., `prepare_data_minimal.py`).
3.  **Train Model**: Run the training script, which will automatically find the dataset in `final_yolo_dataset/`.
"""
    with open(base_path / "README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)
    print("   ✅ Created README.md")

    print("\n" + "=" * 60)
    print("🎉 Refactoring Complete!")
    print("   All training data is now organized under the 'training_data/' directory.")
    print("   Next step is to update the scripts to use these new paths.")
    print("=" * 60)


if __name__ == "__main__":
    refactor_training_data_structure()
