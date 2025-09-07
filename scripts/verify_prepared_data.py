#!/usr/bin/env python3
"""
Data Integrity Verification Script

This script verifies the integrity of the prepared dataset by:
1. Counting the total number of images and labels.
2. Finding and reporting all matching image-label pairs.
3. Reporting any orphan files (images without labels or vice-versa).
4. Validating the format of a sample of label files to ensure they
   contain a class ID and valid bounding box coordinates.
"""

import random
from pathlib import Path


def verify_data_integrity():
    """Verifies the prepared dataset."""

    print("🕵️  Starting Data Integrity Verification...")
    print("=" * 60)

    base_path = Path("training_data")
    images_path = base_path / "prepared_dataset/images"
    labels_path = base_path / "prepared_dataset/labels"

    if not images_path.exists() or not labels_path.exists():
        print("❌ Error: Prepared data paths not found.")
        print(f"   Checked for: {images_path}")
        print(f"   Checked for: {labels_path}")
        return

    # 1. Count Files
    print("1. Counting image and label files...")
    image_extensions = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".PNG", ".JPG", ".JPEG"}

    image_files = {p.stem: p for p in images_path.iterdir() if p.suffix in image_extensions}
    label_files = {p.stem: p for p in labels_path.iterdir() if p.suffix == ".txt"}

    print(f"   - Found {len(image_files)} image files.")
    print(f"   - Found {len(label_files)} label files.")

    # 2. Find Matching Pairs and Orphans
    print("\n2. Checking for matching pairs and orphans...")

    image_stems = set(image_files.keys())
    label_stems = set(label_files.keys())

    matched_stems = image_stems.intersection(label_stems)
    orphan_images = image_stems - label_stems
    orphan_labels = label_stems - image_stems

    print(f"   - ✅ Found {len(matched_stems)} matching image-label pairs.")
    if orphan_images:
        print(f"   - ⚠️  Found {len(orphan_images)} images without labels.")
        for i, stem in enumerate(list(orphan_images)[:5]):
            print(f"     - Example {i+1}: {image_files[stem].name}")
    else:
        print("   - ✅ No orphan images found.")

    if orphan_labels:
        print(f"   - ⚠️  Found {len(orphan_labels)} labels without images.")
        for i, stem in enumerate(list(orphan_labels)[:5]):
            print(f"     - Example {i+1}: {label_files[stem].name}")
    else:
        print("   - ✅ No orphan labels found.")

    # 3. Validate Label File Format
    print("\n3. Validating format of a sample of 5 label files...")

    if not matched_stems:
        print("   - ⏩ Skipping validation, no matched pairs found.")
        return

    sample_stems = random.sample(list(matched_stems), min(5, len(matched_stems)))

    all_samples_valid = True
    for stem in sample_stems:
        label_file_path = label_files[stem]
        is_valid = True
        try:
            with open(label_file_path) as f:
                lines = f.readlines()
                if not lines:
                    is_valid = False
                    print(f"   - ❌ FAILED: {label_file_path.name} is empty.")
                    continue

                for i, line in enumerate(lines):
                    parts = line.strip().split()
                    if len(parts) != 5:
                        is_valid = False
                        print(
                            f"   - ❌ FAILED: {label_file_path.name} (Line {i+1}) has {len(parts)} parts, expected 5."
                        )
                        break

                    class_id_str, x_center_str, y_center_str, width_str, height_str = parts

                    # Check class ID
                    if not class_id_str.isdigit():
                        is_valid = False
                        print(
                            f"   - ❌ FAILED: {label_file_path.name} (Line {i+1}) class ID is not an integer."
                        )
                        break

                    # Check coordinates
                    coords = [
                        float(x_center_str),
                        float(y_center_str),
                        float(width_str),
                        float(height_str),
                    ]
                    if not all(0.0 <= c <= 1.0 for c in coords):
                        is_valid = False
                        print(
                            f"   - ❌ FAILED: {label_file_path.name} (Line {i+1}) coordinates are out of [0, 1] range."
                        )
                        break

            if is_valid:
                print(f"   - ✅ PASSED: {label_file_path.name} format is valid.")

        except ValueError as e:
            is_valid = False
            print(f"   - ❌ FAILED: {label_file_path.name} contains non-numeric values. Error: {e}")
        except Exception as e:
            is_valid = False
            print(f"   - ❌ FAILED: Could not read or process {label_file_path.name}. Error: {e}")

        if not is_valid:
            all_samples_valid = False

    if all_samples_valid:
        print("\n   ✅ All tested samples have a valid format.")

    print("\n" + "=" * 60)
    print("✅ Verification Complete.")
    print("=" * 60)


if __name__ == "__main__":
    verify_data_integrity()
