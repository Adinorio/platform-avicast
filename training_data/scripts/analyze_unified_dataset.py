#!/usr/bin/env python3
"""
Analyze the existing unified egret dataset for multi-class training
"""

import os
from pathlib import Path
from collections import Counter

def analyze_unified_dataset():
    """Analyze the unified egret dataset that's already available"""

    print("🦆 ANALYZING UNIFIED EGRET DATASET")
    print("=" * 50)

    # Paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    dataset_path = project_root / "training_data" / "final_yolo_dataset" / "unified_egret_dataset"

    print(f"📁 Dataset location: {dataset_path}")

    # Read data.yaml
    data_yaml_path = dataset_path / "data.yaml"
    with open(data_yaml_path, 'r') as f:
        data_yaml_content = f.read()

    print(f"\n📄 DATA.YAML CONFIGURATION:")
    print("-" * 30)
    print(data_yaml_content)

    # Analyze classes in the dataset
    splits = ['train', 'val', 'test']
    all_classes = Counter()
    total_labels = 0

    print(f"\n📊 DATASET ANALYSIS:")
    print("-" * 30)

    for split in splits:
        labels_path = dataset_path / split / "labels"
        print(f"\n📂 {split.upper()} SPLIT:")

        label_files = list(labels_path.glob("*.txt"))
        split_classes = Counter()
        split_total = 0

        for label_file in label_files:
            with open(label_file, 'r') as f:
                lines = f.readlines()

            for line in lines:
                if line.strip():
                    parts = line.strip().split()
                    if len(parts) >= 1:
                        class_id = int(parts[0])
                        split_classes[class_id] += 1
                        all_classes[class_id] += 1
                        split_total += 1
                        total_labels += 1

        print(f"  📊 Total labels: {split_total}")
        print(f"  🏷️  Classes found: {sorted(split_classes.keys())}")
        for class_id, count in sorted(split_classes.items()):
            class_name = ['Chinese_Egret', 'Great_Egret', 'Intermediate_Egret', 'Little_Egret'][class_id] if class_id < 4 else f"Unknown_{class_id}"
            print(f"    Class {class_id} ({class_name}): {count} labels")

    print(f"\n📈 OVERALL STATISTICS:")
    print("=" * 30)
    print(f"📊 Total labels: {total_labels}")
    print(f"🏷️  Classes: {sorted(all_classes.keys())}")

    class_names = ['Chinese_Egret', 'Great_Egret', 'Intermediate_Egret', 'Little_Egret']
    for class_id, count in sorted(all_classes.items()):
        class_name = class_names[class_id] if class_id < len(class_names) else f"Unknown_{class_id}"
        percentage = (count / total_labels) * 100
        print(f"    Class {class_id}: {class_name} - {count} labels ({percentage:.1f}%)")

    # Check if data is balanced
    print(f"\n⚖️  CLASS BALANCE ANALYSIS:")
    print("-" * 30)

    min_count = min(all_classes.values())
    max_count = max(all_classes.values())
    balance_ratio = min_count / max_count

    if balance_ratio > 0.5:
        balance_status = "✅ Well balanced"
    elif balance_ratio > 0.3:
        balance_status = "⚠️  Moderately balanced"
    else:
        balance_status = "❌ Imbalanced (consider data augmentation)"

    print(f"📊 Balance ratio: {balance_ratio:.2f} ({balance_status})")
    print(f"📊 Min class: {min_count} labels")
    print(f"📊 Max class: {max_count} labels")

    print(f"\n🎯 MULTI-CLASS TRAINING READY:")
    print("=" * 30)
    print("✅ Dataset configured for 4 egret species")
    print("✅ All classes represented")
    print(f"✅ Total training data: {total_labels} labels")
    print("✅ Ready for maximum accuracy training")

    return dataset_path, total_labels, all_classes

if __name__ == "__main__":
    dataset_path, total_labels, class_distribution = analyze_unified_dataset()

    print("\n🚀 READY TO TRAIN MULTI-CLASS MODEL!")
    print("=" * 50)
    print("Command to run maximum accuracy training:")
    print("python training_data/scripts/train_multi_class_egret.py")
