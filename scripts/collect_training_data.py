#!/usr/bin/env python3
"""
Collect and organize training data for Stage-2 classifier retraining.

This script:
1. Scans review_queue/ for ABSTAIN cases
2. Allows manual labeling of ambiguous detections
3. Organizes labeled data for retraining
4. Balances classes with augmentation
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, List
import numpy as np
from PIL import Image
import cv2
import albumentations as A
from tqdm import tqdm


class TrainingDataCollector:
    """Collect and prepare training data from review queue."""

    def __init__(self, review_queue_dir: str = "review_queue",
                 output_dir: str = "expanded_training_data"):
        self.review_queue = Path(review_queue_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Setup augmentation for minority classes
        self.setup_augmentations()

        # Class mapping
        self.classes = ['Chinese Egret', 'Great Egret', 'Intermediate Egret', 'Little Egret']
        self.class_to_idx = {cls: i for i, cls in enumerate(self.classes)}

    def setup_augmentations(self):
        """Setup data augmentation pipeline."""
        self.augment = A.Compose([
            A.Rotate(limit=20, p=0.7),
            A.HorizontalFlip(p=0.5),
            A.VerticalFlip(p=0.3),
            A.GaussianBlur(blur_limit=3, p=0.3),
            A.GaussNoise(var_limit=(10, 50), p=0.3),
            A.RandomBrightnessContrast(brightness_limit=0.2, contrast_limit=0.2, p=0.6),
            A.HueSaturationValue(hue_shift_limit=15, sat_shift_limit=20, val_shift_limit=10, p=0.4),
            A.RandomResizedCrop(height=224, width=224, scale=(0.8, 1.0), p=0.5),
        ])

    def scan_review_queue(self) -> List[Dict]:
        """Scan review queue for unlabeled cases."""
        unlabeled_cases = []

        if not self.review_queue.exists():
            print(f"Review queue not found: {self.review_queue}")
            return unlabeled_cases

        for date_dir in sorted(self.review_queue.iterdir()):
            if date_dir.is_dir():
                metadata_file = date_dir / "metadata.json"
                if metadata_file.exists():
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)

                    for case in metadata:
                        if 'human_label' not in case:  # Not yet labeled
                            case['date_dir'] = date_dir
                            unlabeled_cases.append(case)

        print(f"Found {len(unlabeled_cases)} unlabeled cases in review queue")
        return unlabeled_cases

    def create_labeling_interface(self, cases: List[Dict]):
        """Simple command-line interface for labeling."""
        print("\n" + "="*60)
        print("EGRET SPECIES LABELING INTERFACE")
        print("="*60)
        print("Classes: 1=Chinese, 2=Great, 3=Intermediate, 4=Little, S=Skip, Q=Quit")
        print("="*60)

        labeled_count = 0

        for i, case in enumerate(cases):
            print(f"\nCase {i+1}/{len(cases)}")
            print(f"ID: {case['id']}")
            print(f"Stage-1: {case['stage1_decision']['status']} ({case['stage1_decision']['reason']})")
            print(f"Stage-2: {case['stage2_decision']['status']} ({case['stage2_decision']['reason']})")

            # Show classifier probabilities
            probs = case.get('classifier_probs', {})
            if probs:
                sorted_probs = sorted(probs.items(), key=lambda x: x[1], reverse=True)
                print("Top predictions:")
                for cls, prob in sorted_probs[:3]:
                    print(".3f")

            # Try to open image for visual inspection
            image_path = case['date_dir'] / case['image_file']
            if image_path.exists():
                print(f"Image: {image_path}")
                # Could add image display here if running in GUI environment

            while True:
                choice = input("\nLabel (1-4/S/Q): ").strip().upper()

                if choice == 'Q':
                    print(f"Labeled {labeled_count} cases. Exiting...")
                    return labeled_count
                elif choice == 'S':
                    print("Skipped")
                    break
                elif choice in ['1', '2', '3', '4']:
                    class_idx = int(choice) - 1
                    case['human_label'] = self.classes[class_idx]
                    labeled_count += 1
                    print(f"Labeled as: {self.classes[class_idx]}")
                    break
                else:
                    print("Invalid choice. Use 1-4, S, or Q.")

        return labeled_count

    def organize_labeled_data(self, cases: List[Dict]):
        """Organize labeled cases into training directories."""
        # Create class directories
        for cls in self.classes:
            class_dir = self.output_dir / 'train' / cls
            class_dir.mkdir(parents=True, exist_ok=True)

        labeled_cases = [case for case in cases if 'human_label' in case]

        print(f"\nOrganizing {len(labeled_cases)} labeled cases...")

        for case in tqdm(labeled_cases, desc="Copying images"):
            src_path = case['date_dir'] / case['image_file']
            dst_dir = self.output_dir / 'train' / case['human_label']

            if src_path.exists():
                # Copy original
                dst_path = dst_dir / f"{case['id']}_orig.png"
                shutil.copy2(src_path, dst_path)

                # Generate augmentations for minority classes
                if case['human_label'] in ['Great Egret', 'Little Egret']:
                    self.generate_augmentations(src_path, dst_dir, case['id'])

    def generate_augmentations(self, image_path: Path, output_dir: Path, case_id: str, num_aug: int = 5):
        """Generate augmentations for minority classes."""
        # Load image
        image = cv2.imread(str(image_path))
        if image is None:
            return

        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        for i in range(num_aug):
            # Apply augmentation
            augmented = self.augment(image=image)['image']

            # Save
            output_path = output_dir / f"{case_id}_aug{i}.png"
            cv2.imwrite(str(output_path), cv2.cvtColor(augmented, cv2.COLOR_RGB2BGR))

    def create_dataset_summary(self):
        """Create summary of the collected dataset."""
        summary = {
            'classes': self.classes,
            'total_samples': 0,
            'class_counts': {}
        }

        for cls in self.classes:
            class_dir = self.output_dir / 'train' / cls
            if class_dir.exists():
                count = len(list(class_dir.glob('*.png')))
                summary['class_counts'][cls] = count
                summary['total_samples'] += count

        # Save summary
        with open(self.output_dir / 'dataset_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)

        print("\n" + "="*40)
        print("DATASET SUMMARY")
        print("="*40)
        print(f"Total samples: {summary['total_samples']}")
        for cls, count in summary['class_counts'].items():
            print(f"  {cls}: {count}")
        print("="*40)

    def run_collection_pipeline(self):
        """Run the complete data collection pipeline."""
        print("🔍 Starting training data collection...")

        # Scan for unlabeled cases
        cases = self.scan_review_queue()

        if not cases:
            print("No unlabeled cases found. Run the pipeline first to generate ABSTAIN cases.")
            return

        # Label the cases
        labeled_count = self.create_labeling_interface(cases)

        if labeled_count > 0:
            # Organize the data
            self.organize_labeled_data(cases)

            # Create summary
            self.create_dataset_summary()

            print("
✅ Training data collection complete!"            print(f"Labeled {labeled_count} cases")
            print(f"Data saved to: {self.output_dir}")
        else:
            print("No cases were labeled.")


def main():
    collector = TrainingDataCollector()
    collector.run_collection_pipeline()


if __name__ == '__main__':
    main()
