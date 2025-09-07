#!/usr/bin/env python3
"""
Analyze the distribution of labels in our dataset to understand class distribution
"""

from collections import Counter
from pathlib import Path


def analyze_label_distribution():
    """Analyze what classes are actually present in our dataset"""

    print("📊 ANALYZING LABEL DISTRIBUTION IN CHINESE EGRET DATASET")
    print("=" * 70)

    # Paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    dataset_path = project_root / "training_data" / "final_yolo_dataset" / "chinese_egret_maximum"

    splits = ["train", "val", "test"]
    all_classes = Counter()
    total_labels = 0

    print("\n🔍 SCANNING ALL LABEL FILES:")
    print("-" * 40)

    for split in splits:
        labels_path = dataset_path / split / "labels"
        print(f"\n📂 {split.upper()} SPLIT:")

        label_files = list(labels_path.glob("*.txt"))
        split_classes = Counter()
        split_total = 0

        for label_file in label_files:
            with open(label_file) as f:
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
            print(f"    Class {class_id}: {count} labels")

    print("\n📈 OVERALL STATISTICS:")
    print("=" * 40)
    print(f"📊 Total labels analyzed: {total_labels}")
    print(f"🏷️  Unique classes found: {sorted(all_classes.keys())}")

    print("\n🎯 CLASS INTERPRETATION:")
    print("-" * 40)

    class_names = {
        0: "Chinese Egret",
        1: "Whiskered Tern",
        2: "Great Knot",
        3: "Little Egret",
        4: "Great Egret",
        5: "Intermediate Egret",
    }

    for class_id, count in sorted(all_classes.items()):
        class_name = class_names.get(class_id, f"Unknown Class {class_id}")
        percentage = (count / total_labels) * 100
        print(f"    Class {class_id}: {class_name} - {count} labels ({percentage:.1f}%)")

    print("\n💡 TRAINING IMPLICATIONS:")
    print("=" * 40)
    print("1. Single-class (Chinese Egret only):")
    print("   ✅ Simpler model, focused training")
    print("   ❌ Ignores other species data")
    print("   📊 Uses only Class 0 labels")

    print("\n2. Multi-class (all egret species):")
    print("   ✅ Uses ALL training data")
    print("   ✅ Better species discrimination")
    print("   ✅ More comprehensive conservation tool")
    print("   ⚠️  More complex model")

    print("\n3. Filtered multi-class (remove other labels from mixed images):")
    print("   ✅ Uses all images with Chinese Egrets")
    print("   ✅ More training data for Chinese Egret")
    print("   ⚠️  Complex preprocessing required")

    print("\n🎯 RECOMMENDATION:")
    print("=" * 40)
    print("For your conservation goal, consider:")
    print("→ Single-class: Simpler, faster deployment")
    print("→ Multi-class: Better discrimination, uses all data")
    print("→ Your choice depends on deployment scenario!")


if __name__ == "__main__":
    analyze_label_distribution()
