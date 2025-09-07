#!/usr/bin/env python3
"""
Analyze mixed-species images to understand their training value
"""

import os
from pathlib import Path

def analyze_mixed_images():
    """Analyze what we lost by filtering mixed images"""

    print("🔍 ANALYZING MIXED-SPECIES IMAGES VALUE")
    print("=" * 50)

    # Paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    base_path = project_root / "training_data" / "final_yolo_dataset" / "chinese_egret_dataset"

    splits = ['train', 'val', 'test']
    total_mixed = 0
    total_chinese_only = 0

    print("\n📊 MIXED VS PURE IMAGE ANALYSIS:")
    print("-" * 50)

    for split in splits:
        print(f"\n🔍 {split.upper()} SPLIT:")

        labels_path = base_path / split / "labels"
        label_files = list(labels_path.glob("*.txt"))

        mixed_count = 0
        chinese_count = 0
        chinese_in_mixed = 0

        for label_file in label_files:
            if not label_file.exists():  # Was removed during filtering
                continue

            with open(label_file, 'r') as f:
                lines = f.readlines()

            classes_in_image = set()
            chinese_egrets = 0

            for line in lines:
                if line.strip():
                    parts = line.strip().split()
                    if len(parts) >= 1:
                        class_id = int(parts[0])
                        classes_in_image.add(class_id)
                        if class_id == 0:  # Chinese Egret
                            chinese_egrets += 1

            if len(classes_in_image) > 1:  # Mixed species
                mixed_count += 1
                chinese_in_mixed += chinese_egrets
                print(f"  🦆 {label_file.name}: {chinese_egrets} Chinese + {len(classes_in_image)-1} other species")
            else:  # Pure Chinese Egret
                chinese_count += 1

        print(f"  ✅ Pure Chinese images: {chinese_count}")
        print(f"  🔄 Mixed species images: {mixed_count} (with {chinese_in_mixed} Chinese Egrets)")

        total_mixed += mixed_count
        total_chinese_only += chinese_count

    print("\n" + "=" * 50)
    print("🎯 ANALYSIS SUMMARY:")
    print(f"📊 Pure Chinese Egret images: {total_chinese_only}")
    print(f"📊 Mixed species images removed: {total_mixed}")
    total_images = total_mixed + total_chinese_only
    if total_images > 0:
        data_loss_pct = (total_mixed / total_images) * 100
        print(f"📈 Data loss: {total_mixed}/{total_images} = {data_loss_pct:.1f}%")
    else:
        print("📈 Data loss: No images found")

    print("\n💡 TRAINING VALUE OF MIXED IMAGES:")
    print("✅ Help model learn species discrimination")
    print("✅ Provide more diverse training examples")
    print("✅ Better generalization to real-world scenarios")
    print("✅ More robust feature learning")

    print("\n⚖️  TRADE-OFFS:")
    print("❌ YOLO ignores mixed images in single-class training")
    print("❌ May confuse model if species are very similar")
    print("❌ Harder to evaluate performance per species")

    return total_mixed, total_chinese_only

if __name__ == "__main__":
    analyze_mixed_images()
