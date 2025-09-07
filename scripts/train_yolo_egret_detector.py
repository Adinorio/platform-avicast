#!/usr/bin/env python3
"""
Train YOLO detector for egret species identification.

This script trains a YOLO model on the unified egret dataset with 4 classes:
- Chinese Egret
- Great Egret
- Intermediate Egret
- Little Egret
"""

import sys
from pathlib import Path


def check_dataset():
    """Verify dataset structure and files."""
    print("🔍 Checking dataset structure...")

    base_path = Path("training_data/final_yolo_dataset/unified_egret_dataset")

    for split in ["train", "val", "test"]:
        img_dir = base_path / split / "images"
        label_dir = base_path / split / "labels"

        if not img_dir.exists():
            print(f"❌ Missing: {img_dir}")
            return False

        if not label_dir.exists():
            print(f"❌ Missing: {label_dir}")
            return False

        # Count images and labels
        images = (
            list(img_dir.glob("*.png")) + list(img_dir.glob("*.jpg")) + list(img_dir.glob("*.jpeg"))
        )
        labels = list(label_dir.glob("*.txt"))

        print(f"✅ {split}: {len(images)} images, {len(labels)} labels")

        if len(images) != len(labels):
            print(f"⚠️  Warning: {split} has {len(images)} images but {len(labels)} labels")

    return True


def create_training_command():
    """Create the YOLO training command."""
    print("\n🚀 YOLO Training Command:")
    print("=" * 60)

    cmd = """
yolo detect train \\
    data=egret_training_config.yaml \\
    model=yolo11m.pt \\
    epochs=100 \\
    imgsz=640 \\
    batch=8 \\
    workers=4 \\
    optimizer=AdamW \\
    lr0=0.001 \\
    lrf=0.01 \\
    cache=disk \\
    project=runs/egret_detection \\
    name=egret_yolo11m_baseline \\
    save=True \\
    save_period=10 \\
    val=True
"""

    print(cmd)
    return cmd


def main():
    print("🐦 Egret YOLO Detector Training Setup")
    print("=" * 50)

    # Check if required files exist
    config_file = Path("egret_training_config.yaml")
    if not config_file.exists():
        print("❌ Missing egret_training_config.yaml")
        print("Please ensure the config file exists in the project root.")
        sys.exit(1)

    # Check dataset
    if not check_dataset():
        print("❌ Dataset issues found. Please fix before training.")
        sys.exit(1)

    print("✅ Dataset structure OK")

    # Create training command
    create_training_command()

    print("\n📝 Training Notes:")
    print("-" * 30)
    print("• Model will be saved to: runs/egret_detection/egret_yolo11m_baseline/weights/")
    print("• Best model: best.pt")
    print("• Last model: last.pt")
    print("• Training logs: results.csv, train_batch*.jpg")
    print("• Expected training time: 4-8 hours (depending on GPU)")

    print("\n🔍 After training, you can:")
    print(
        "• Run inference: yolo detect predict model=runs/egret_detection/egret_yolo11m_baseline/weights/best.pt source=your_images/"
    )
    print("• Analyze results: Check runs/egret_detection/egret_yolo11m_baseline/results.csv")
    print("• Use in pipeline: Copy best.pt to models/ and update bird_detection_service.py")

    print("\n✅ Ready to start training!")
    print("Run the command above to begin YOLO training on your egret dataset.")


if __name__ == "__main__":
    main()
