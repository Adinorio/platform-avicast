#!/usr/bin/env python3
"""
YOLOv11x Training Script for Egret Species Identification
Optimized for Chinese Egret conservation and multi-species detection
"""

import os
import sys
import subprocess
from pathlib import Path

def train_chinese_egret_specialist():
    """Train YOLOv11x on Chinese Egret specialist dataset for maximum conservation accuracy"""

    print("🦆 TRAINING: Chinese Egret Specialist Model")
    print("=" * 60)
    print("🎯 Goal: Maximum accuracy for critically endangered Chinese Egrets")
    print("📊 Dataset: Single-class Chinese Egret detection")
    print()

    # Check if dataset exists
    dataset_path = Path("../../training_data/prepared_dataset/chinese_egret_dataset")
    if not dataset_path.exists():
        print("❌ Chinese Egret dataset not found!")
        return False

    # Create data.yaml for single class
    data_yaml_content = """train: training_data/prepared_dataset/chinese_egret_dataset/images
val: training_data/prepared_dataset/chinese_egret_dataset/images
test: training_data/prepared_dataset/chinese_egret_dataset/images
nc: 1
names: ['Chinese_Egret']
"""

    data_yaml_path = Path("../../training_data/chinese_egret_single_class.yaml")
    with open(data_yaml_path, 'w') as f:
        f.write(data_yaml_content)

    print("📋 Dataset configuration:")
    print(f"   📁 Images: {len(list(dataset_path.glob('images/*.png')))} PNG files")
    print(f"   🏷️  Labels: {len(list(dataset_path.glob('labels/*.txt')))} annotation files")
    print()

    # Optimal training command for conservation accuracy
    train_cmd = [
        "yolo", "train",
        "model=../../models/yolov11x.pt",
        f"data={data_yaml_path}",
        "epochs=150",  # Longer training for conservation accuracy
        "imgsz=1280",  # Higher resolution for small bird details
        "batch=8",     # Smaller batch for stability
        "lr0=0.001",   # Conservative learning rate
        "lrf=0.01",    # Final learning rate
        "momentum=0.937",
        "weight_decay=0.0005",
        "warmup_epochs=3.0",
        "warmup_momentum=0.8",
        "warmup_bias_lr=0.1",
        "box=7.5",     # Higher box loss weight for precise localization
        "cls=0.5",     # Classification loss weight
        "dfl=1.5",     # Distribution focal loss
        "patience=50", # Early stopping patience
        "save=True",
        "save_period=25",  # Save every 25 epochs
        "project=../../training_results",
        "name=chinese_egret_specialist_yolov11x",
        "exist_ok=True",
        "pretrained=True",
        "optimizer=SGD",  # SGD often better for fine-tuning
        "amp=True",      # Automatic mixed precision for speed
        "workers=4"      # Data loading workers
    ]

    print("🚀 Training Command:")
    print(" ".join(train_cmd))
    print()

    # Execute training
    try:
        print("🔥 Starting training...")
        result = subprocess.run(train_cmd, cwd="../../", capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ Training completed successfully!")
            print("📊 Results saved to: training_results/chinese_egret_specialist_yolov11x/")
            return True
        else:
            print("❌ Training failed!")
            print("Error output:", result.stderr)
            return False

    except Exception as e:
        print(f"❌ Error during training: {e}")
        return False

def train_unified_multi_species():
    """Train YOLOv11x on unified multi-species egret dataset"""

    print("🦆 TRAINING: Unified Multi-Species Egret Model")
    print("=" * 60)
    print("🎯 Goal: Comprehensive egret species identification")
    print("📊 Dataset: 4-class (Chinese, Great, Intermediate, Little Egrets)")
    print()

    # Check if unified dataset exists
    data_yaml_path = Path("../../training_data/final_yolo_dataset/unified_egret_dataset/data.yaml")
    if not data_yaml_path.exists():
        print("❌ Unified egret dataset not found!")
        return False

    # Count images in each split
    train_images = len(list(Path("../../training_data/final_yolo_dataset/unified_egret_dataset/train/images").glob("*")))
    val_images = len(list(Path("../../training_data/final_yolo_dataset/unified_egret_dataset/val/images").glob("*")))
    test_images = len(list(Path("../../training_data/final_yolo_dataset/unified_egret_dataset/test/images").glob("*")))

    print("📋 Dataset configuration:")
    print(f"   📁 Train: {train_images} images")
    print(f"   📁 Val: {val_images} images")
    print(f"   📁 Test: {test_images} images")
    print(f"   🏷️  Classes: 4 (Chinese, Great, Intermediate, Little Egrets)")
    print()

    # Optimal training command for multi-class
    train_cmd = [
        "yolo", "train",
        "model=../../models/yolov11x.pt",
        f"data={data_yaml_path}",
        "epochs=100",   # Standard epochs for multi-class
        "imgsz=1024",   # Good balance of detail and speed
        "batch=12",     # Larger batch for multi-class stability
        "lr0=0.01",     # Standard learning rate
        "lrf=0.01",
        "momentum=0.937",
        "weight_decay=0.0005",
        "warmup_epochs=3.0",
        "warmup_momentum=0.8",
        "warmup_bias_lr=0.1",
        "box=7.5",
        "cls=0.5",
        "dfl=1.5",
        "patience=30",
        "save=True",
        "save_period=20",
        "project=../../training_results",
        "name=unified_egret_yolov11x",
        "exist_ok=True",
        "pretrained=True",
        "optimizer=AdamW",  # AdamW often better for multi-class
        "amp=True",
        "workers=4",
        "cos_lr=True",   # Cosine learning rate scheduling
        "close_mosaic=10"  # Close mosaic augmentation later
    ]

    print("🚀 Training Command:")
    print(" ".join(train_cmd))
    print()

    # Execute training
    try:
        print("🔥 Starting training...")
        result = subprocess.run(train_cmd, cwd="../../", capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ Training completed successfully!")
            print("📊 Results saved to: training_results/unified_egret_yolov11x/")
            return True
        else:
            print("❌ Training failed!")
            print("Error output:", result.stderr)
            return False

    except Exception as e:
        print(f"❌ Error during training: {e}")
        return False

def train_hybrid_approach():
    """Two-stage training: Specialist model + Fine-tuning on multi-class"""

    print("🦆 TRAINING: Hybrid Two-Stage Approach")
    print("=" * 60)
    print("🎯 Stage 1: Train specialist model")
    print("🎯 Stage 2: Fine-tune on multi-class dataset")
    print()

    # Stage 1: Train specialist
    print("📍 STAGE 1: Chinese Egret Specialist Training")
    specialist_success = train_chinese_egret_specialist()

    if not specialist_success:
        print("❌ Stage 1 failed. Aborting hybrid training.")
        return False

    print("\n📍 STAGE 2: Multi-Class Fine-tuning")

    # Find the best specialist model
    results_dir = Path("../../training_results/chinese_egret_specialist_yolov11x")
    if not results_dir.exists():
        print("❌ Specialist model results not found!")
        return False

    # Find the best weights file
    best_weights = results_dir / "weights" / "best.pt"
    if not best_weights.exists():
        print("❌ Best weights not found!")
        return False

    print(f"🔄 Fine-tuning from specialist model: {best_weights}")

    # Fine-tune on multi-class dataset
    finetune_cmd = [
        "yolo", "train",
        f"model={best_weights}",
        "data=../../training_data/final_yolo_dataset/unified_egret_dataset/data.yaml",
        "epochs=50",    # Shorter fine-tuning
        "imgsz=1024",
        "batch=8",
        "lr0=0.0001",   # Very low learning rate for fine-tuning
        "lrf=0.0001",
        "patience=20",
        "save=True",
        "project=../../training_results",
        "name=hybrid_egret_yolov11x",
        "exist_ok=True",
        "freeze=10",    # Freeze first 10 layers
        "amp=True",
        "workers=4"
    ]

    try:
        print("🔥 Starting fine-tuning...")
        result = subprocess.run(finetune_cmd, cwd="../../", capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ Hybrid training completed successfully!")
            print("📊 Results saved to: training_results/hybrid_egret_yolov11x/")
            return True
        else:
            print("❌ Fine-tuning failed!")
            print("Error output:", result.stderr)
            return False

    except Exception as e:
        print(f"❌ Error during fine-tuning: {e}")
        return False

def main():
    """Main training menu"""

    print("🦆 YOLOv11x Egret Training Options")
    print("=" * 60)
    print("1. 🏆 Chinese Egret Specialist (Maximum conservation accuracy)")
    print("2. 🌍 Unified Multi-Species (Comprehensive identification)")
    print("3. 🔄 Hybrid Two-Stage (Best of both worlds)")
    print("4. 📊 Show training recommendations")
    print()

    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        choice = input("Select training approach (1-4): ").strip()

    if choice == "1":
        train_chinese_egret_specialist()
    elif choice == "2":
        train_unified_multi_species()
    elif choice == "3":
        train_hybrid_approach()
    elif choice == "4":
        show_recommendations()
    else:
        print("❌ Invalid choice. Please select 1-4.")

def show_recommendations():
    """Show training recommendations"""

    print("📚 YOLOv11x Training Recommendations for Bird Identification")
    print("=" * 60)

    print("\n🎯 FOR CHINESE EGRET CONSERVATION:")
    print("   • Use specialist training (Option 1)")
    print("   • Higher image size (1280px) for detail preservation")
    print("   • Longer training (150 epochs)")
    print("   • Conservative learning rate (0.001)")
    print("   • Focus on precision over speed")

    print("\n🌍 FOR FIELD IDENTIFICATION:")
    print("   • Use unified training (Option 2)")
    print("   • Balanced image size (1024px)")
    print("   • Standard training (100 epochs)")
    print("   • Optimize for real-time performance")

    print("\n🔄 FOR BEST ACCURACY:")
    print("   • Use hybrid approach (Option 3)")
    print("   • Combines specialist precision with multi-species capability")
    print("   • Recommended for conservation + field work")

    print("\n⚙️  GENERAL TIPS:")
    print("   • Monitor validation mAP for overfitting")
    print("   • Use early stopping patience (30-50 epochs)")
    print("   • Save checkpoints every 20-25 epochs")
    print("   • Consider class weights if imbalanced")

if __name__ == "__main__":
    main()




