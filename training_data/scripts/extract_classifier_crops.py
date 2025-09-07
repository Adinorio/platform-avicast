#!/usr/bin/env python3
"""
Extract crops from YOLO detections for Stage-2 classifier training.

This script:
1. Loads YOLO model and runs detections on training images
2. Extracts crops from bounding boxes
3. Saves crops organized by class for classifier training
4. Creates balanced dataset with data augmentation for minority classes
"""

import argparse
import json
import sys
from pathlib import Path

import albumentations as A
import cv2
import numpy as np
import yaml
from tqdm import tqdm
from ultralytics import YOLO


class CropExtractor:
    """Extract and organize crops for classifier training."""

    def __init__(self, data_yaml_path: str, output_dir: str = "classifier_training_data"):
        self.data_yaml_path = data_yaml_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Load data configuration
        with open(data_yaml_path) as f:
            self.data_config = yaml.safe_load(f)

        # Setup directories
        self.setup_directories()

        # Initialize data augmentation for minority classes
        self.setup_augmentations()

        # Load YOLO model
        self.model = YOLO("models/yolo11x.pt")  # Use your trained YOLO model

    def setup_directories(self):
        """Create output directory structure."""
        for split in ["train", "val", "test"]:
            for class_name in self.data_config["names"]:
                class_dir = self.output_dir / split / class_name
                class_dir.mkdir(parents=True, exist_ok=True)

        print(f"✅ Created directory structure in {self.output_dir}")

    def setup_augmentations(self):
        """Setup data augmentation for minority classes."""
        self.augment = A.Compose(
            [
                A.Rotate(limit=15, p=0.5),
                A.GaussianBlur(blur_limit=3, p=0.3),
                A.GaussNoise(var_limit=(10, 50), p=0.3),
                A.RandomBrightnessContrast(brightness_limit=0.1, contrast_limit=0.1, p=0.5),
                A.HueSaturationValue(
                    hue_shift_limit=10, sat_shift_limit=15, val_shift_limit=10, p=0.3
                ),
            ]
        )

    def extract_crops_from_split(self, split: str, max_crops_per_class: int = 2000):
        """Extract crops from a data split."""
        print(f"\n🔍 Processing {split} split...")

        # Handle relative paths from data.yaml
        data_yaml_dir = Path(self.data_yaml_path).parent
        split_path = Path(self.data_config[split])
        image_dir = data_yaml_dir / split_path
        label_dir = data_yaml_dir / split_path.parent / "labels"

        class_counts = {name: 0 for name in self.data_config["names"]}
        total_processed = 0

        # Get all image files
        image_files = []
        for ext in ["*.jpg", "*.jpeg", "*.png", "*.PNG", "*.npy"]:
            image_files.extend(list(image_dir.glob(ext)))

        print(f"Found {len(image_files)} images in {split}")

        for image_path in tqdm(image_files, desc=f"Processing {split} images"):
            try:
                # Load image
                if image_path.suffix.lower() == ".npy":
                    # Load numpy array
                    image = np.load(str(image_path))
                    if len(image.shape) == 2:
                        # Grayscale to RGB
                        image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
                    elif image.shape[-1] == 1:
                        # Single channel to RGB
                        image = cv2.cvtColor(image[:, :, 0], cv2.COLOR_GRAY2RGB)
                    image_rgb = image
                else:
                    # Load regular image
                    image = cv2.imread(str(image_path))
                    if image is None:
                        continue
                    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

                # Run YOLO detection
                results = self.model(image_rgb, conf=0.3, iou=0.5)

                # Process detections
                for result in results:
                    boxes = result.boxes
                    if boxes is not None:
                        for box in boxes:
                            # Get bounding box
                            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                            conf = float(box.conf[0].cpu().numpy())
                            class_id = int(box.cls[0].cpu().numpy())
                            class_name = self.data_config["names"][class_id]

                            # Skip if we've reached max crops for this class
                            if class_counts[class_name] >= max_crops_per_class:
                                continue

                            # Extract crop
                            crop = image_rgb[int(y1) : int(y2), int(x1) : int(x2)]

                            # Skip tiny crops
                            if crop.shape[0] < 32 or crop.shape[1] < 32:
                                continue

                            # Save original crop
                            self.save_crop(
                                crop,
                                class_name,
                                split,
                                f"{Path(image_path).stem}_orig_{class_counts[class_name]}",
                            )
                            class_counts[class_name] += 1

                            # Apply augmentations for minority classes
                            if (
                                class_name in ["Little Egret", "Intermediate Egret"]
                                and class_counts[class_name] < max_crops_per_class
                            ):
                                for aug_idx in range(3):  # 3 augmentations per original
                                    if class_counts[class_name] >= max_crops_per_class:
                                        break

                                    augmented = self.augment(image=crop)["image"]
                                    self.save_crop(
                                        augmented,
                                        class_name,
                                        split,
                                        f"{Path(image_path).stem}_aug{aug_idx}_{class_counts[class_name]}",
                                    )
                                    class_counts[class_name] += 1

                total_processed += 1

            except Exception as e:
                print(f"❌ Error processing {image_path}: {e}")
                continue

        # Print statistics
        print(f"\n📊 {split} split statistics:")
        for class_name, count in class_counts.items():
            print(f"  {class_name}: {count} crops")

        return class_counts

    def save_crop(self, crop: np.ndarray, class_name: str, split: str, filename: str):
        """Save a crop to the appropriate directory."""
        # Resize crop to standard size
        crop_resized = cv2.resize(crop, (224, 224))

        # Save as PNG
        output_path = self.output_dir / split / class_name / f"{filename}.png"
        cv2.imwrite(str(output_path), cv2.cvtColor(crop_resized, cv2.COLOR_RGB2BGR))

    def create_dataset_summary(self):
        """Create a summary of the extracted dataset."""
        summary = {"classes": self.data_config["names"], "splits": {}, "total_crops": 0}

        for split in ["train", "val", "test"]:
            split_counts = {}
            split_total = 0

            for class_name in self.data_config["names"]:
                class_dir = self.output_dir / split / class_name
                if class_dir.exists():
                    count = len(list(class_dir.glob("*.png")))
                    split_counts[class_name] = count
                    split_total += count

            summary["splits"][split] = {"counts": split_counts, "total": split_total}
            summary["total_crops"] += split_total

        # Save summary
        with open(self.output_dir / "dataset_summary.json", "w") as f:
            json.dump(summary, f, indent=2)

        print("\n📊 Dataset Summary:")
        print(f"Total crops: {summary['total_crops']}")
        for split, data in summary["splits"].items():
            print(f"{split}: {data['total']} crops")
            for class_name, count in data["counts"].items():
                print(f"  {class_name}: {count}")

        return summary


def main():
    parser = argparse.ArgumentParser(description="Extract crops for classifier training")
    parser.add_argument("--data-yaml", type=str, required=True, help="Path to data.yaml file")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="classifier_training_data",
        help="Output directory for crops",
    )
    parser.add_argument("--max-crops", type=int, default=2000, help="Maximum crops per class")

    args = parser.parse_args()

    # Check if data.yaml exists
    if not Path(args.data_yaml).exists():
        print(f"❌ Data YAML file not found: {args.data_yaml}")
        sys.exit(1)

    # Check if yaml is available
    try:
        yaml.safe_load  # Test if yaml is imported
    except NameError:
        print("❌ PyYAML not installed. Install with: pip install PyYAML")
        sys.exit(1)

    # Initialize extractor
    extractor = CropExtractor(args.data_yaml, args.output_dir)

    # Extract crops from each split
    all_counts = {}
    for split in ["train", "val", "test"]:
        counts = extractor.extract_crops_from_split(split, args.max_crops)
        all_counts[split] = counts

    # Create summary
    extractor.create_dataset_summary()

    print("\n✅ Crop extraction completed!")
    print(f"Crops saved to: {args.output_dir}")
    print("Next: Run the classifier training script on this data.")


if __name__ == "__main__":
    main()
