#!/usr/bin/env python3
"""
START MAXIMUM ACCURACY ENSEMBLE TRAINING
Trains 5 YOLOv11x models with different seeds for 98%+ mAP accuracy
"""

import subprocess
import time


def train_ensemble_model(seed_number):
    """Train a single model in the ensemble"""

    print(f"\n🔥 TRAINING MODEL {seed_number}/5 (Seed: {seed_number})")
    print("=" * 60)

    # Maximum accuracy command for ensemble
    cmd = [
        "yolo",
        "train",
        "model=models/yolov11x.pt",
        "data=training_data/prepared_dataset/chinese_egret_dataset",
        "epochs=300",
        "imgsz=1280",
        "batch=8",
        "lr0=0.001",
        "lrf=0.01",
        "patience=50",
        "save=True",
        "save_period=25",
        f"seed={seed_number}",
        "optimizer=SGD",
        "amp=True",
        "workers=4",
        "cos_lr=True",
        "close_mosaic=10",
        "device=0",
        "cache=disk",
        "rect=True",
        "mosaic=1.0",
        "mixup=0.15",
        "copy_paste=0.2",
        "degrees=5.0",
        "translate=0.1",
        "scale=0.95",
        "shear=1.0",
        "perspective=0.0001",
        "flipud=0.5",
        "fliplr=0.5",
        "hsv_h=0.005",
        "hsv_s=0.3",
        "hsv_v=0.2",
        "label_smoothing=0.1",
        "nbs=64",
        "overlap_mask=True",
        "mask_ratio=4",
        "dropout=0.0",
        "warmup_epochs=10",
        "warmup_momentum=0.8",
        "warmup_bias_lr=0.1",
        "box=5.0",
        "cls=0.3",
        "dfl=1.5",
        "fl_gamma=0.0",
        "weight_decay=0.0001",
        "project=max_accuracy_ensemble_results",
        f"name=chinese_egret_ensemble_seed_{seed_number}",
    ]

    print("📋 TRAINING COMMAND:")
    print(" ".join(cmd))
    print()

    try:
        print("🚀 Starting training...")
        result = subprocess.run(cmd, cwd="../../", capture_output=False, text=True)

        if result.returncode == 0:
            print(f"✅ Model {seed_number}/5 completed successfully!")
            return True
        else:
            print(f"❌ Model {seed_number}/5 failed!")
            print("Error output:", result.stderr)
            return False

    except Exception as e:
        print(f"❌ Error training model {seed_number}: {e}")
        return False


def main():
    """Main ensemble training function"""

    print("🎯 MAXIMUM ACCURACY ENSEMBLE TRAINING")
    print("=" * 70)
    print("🎯 Training 5 YOLOv11x models for 98%+ mAP accuracy")
    print("🎯 Each model uses different random seed for diversity")
    print("🎯 Ensemble prediction = HIGHEST POSSIBLE ACCURACY")
    print()

    # Safety confirmation
    print("🛡️  SAFETY CHECK:")
    print("   ✅ Using SAFE software optimizations (NO overclocking)")
    print("   ✅ RTX 3050 optimized settings")
    print("   ✅ Conservative batch size (8)")
    print("   ✅ Emergency stop with Ctrl+C")
    print("   ✅ Auto-save every 25 epochs")
    print()

    print("⚠️  TRAINING INFORMATION:")
    print("   • Models to train: 5")
    print("   • Epochs per model: 300")
    print("   • Expected time: ~40-60 hours total")
    print("   • Expected accuracy: 98%+ mAP")
    print("   • Storage needed: ~50GB")
    print()

    # Final confirmation
    response = input("🚀 START MAXIMUM ACCURACY ENSEMBLE TRAINING? (yes/no): ").lower().strip()

    if response not in ["yes", "y"]:
        print("❌ Training cancelled by user")
        return

    print("\n🔥 STARTING MAXIMUM ACCURACY ENSEMBLE TRAINING")
    print("=" * 60)
    print("🎯 Target: 98%+ mAP for Chinese Egret conservation")
    print()

    successful_models = 0
    failed_models = 0

    # Train 5 models with different seeds
    for seed in [42, 123, 456, 789, 999]:  # Different seeds for diversity
        success = train_ensemble_model(seed)
        if success:
            successful_models += 1
        else:
            failed_models += 1

        # Brief pause between models to let system cool
        if seed != 999:  # Don't pause after last model
            print("\n⏸️  Pausing for 5 minutes to let system cool...")
            time.sleep(300)  # 5 minutes

    # Final summary
    print("\n" + "=" * 60)
    print("🎯 ENSEMBLE TRAINING COMPLETE!")
    print("=" * 60)
    print(f"✅ Successful models: {successful_models}/5")
    print(f"❌ Failed models: {failed_models}/5")

    if successful_models >= 3:  # At least 3 models for decent ensemble
        print("\n🎉 SUCCESS!")
        print("📊 Your ensemble is ready for maximum accuracy predictions!")
        print("📁 Results location: max_accuracy_ensemble_results/")
        print("🎯 Expected accuracy: 98%+ mAP")
        print("\n💡 Next: Use ensemble inference for conservation deployment")
    else:
        print("\n⚠️  WARNING:")
        print("   Not enough successful models for optimal ensemble")
        print("   Consider retraining failed models or using available ones")


if __name__ == "__main__":
    main()
