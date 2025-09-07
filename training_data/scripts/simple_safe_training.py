#!/usr/bin/env python3
"""
SIMPLE SAFE YOLOv11x Training for RTX 3050 Laptop
No external dependencies - uses only standard libraries
"""

from pathlib import Path

import torch


def check_gpu_status():
    """Check GPU availability and status"""
    print("🖥️  GPU STATUS CHECK")
    print("=" * 50)

    if torch.cuda.is_available():
        device_count = torch.cuda.device_count()
        print(f"✅ CUDA Available: {torch.version.cuda}")
        print(f"📊 GPU Count: {device_count}")

        for i in range(device_count):
            gpu_name = torch.cuda.get_device_name(i)
            gpu_memory = torch.cuda.get_device_properties(i).total_memory / (1024**3)
            print(f"🎮 GPU {i}: {gpu_name} ({gpu_memory:.1f}GB)")

        return True
    else:
        print("❌ CUDA not available - will use CPU")
        return False


def show_training_commands():
    """Show optimized training commands for RTX 3050"""

    gpu_available = check_gpu_status()

    print("\n🚀 SAFE TRAINING COMMANDS FOR RTX 3050")
    print("=" * 60)
    print("🎯 Optimized batch sizes and settings for laptop GPU")
    print()

    # Base settings for RTX 3050 (4GB VRAM)
    if gpu_available:
        batch_size = 8  # Conservative for 4GB VRAM
        img_size = 1024  # Good detail preservation
        workers = 4  # Reasonable for laptop
        device = "0"  # Use GPU 0
        print("🎮 USING GPU MODE (RTX 3050 optimized)")
    else:
        batch_size = 4  # CPU mode
        img_size = 640  # Smaller for CPU
        workers = 2  # Fewer workers for CPU
        device = "cpu"
        print("🖥️  USING CPU MODE")

    print(f"📊 Batch size: {batch_size}")
    print(f"📊 Image size: {img_size}px")
    print(f"📊 Workers: {workers}")
    print(f"📊 Device: {device}")
    print()

    print("📋 COPY & PASTE TRAINING COMMANDS:")
    print("-" * 50)

    # Chinese Egret Specialist (Conservation Priority)
    specialist_cmd = f"""yolo train model=models/yolov11x.pt data=training_data/prepared_dataset/chinese_egret_dataset epochs=150 imgsz={img_size} batch={batch_size} lr0=0.001 lrf=0.01 patience=50 optimizer=SGD amp=True workers={workers} device={device} project=training_results_safe name=chinese_egret_specialist_yolov11x_safe"""

    print("\n🏆 CHINESE EGRET SPECIALIST (RECOMMENDED):")
    print(specialist_cmd)
    print()

    # Unified Multi-Species
    unified_cmd = f"""yolo train model=models/yolov11x.pt data=training_data/final_yolo_dataset/unified_egret_dataset/data.yaml epochs=100 imgsz={img_size} batch={batch_size} lr0=0.01 lrf=0.01 patience=30 optimizer=AdamW amp=True workers={workers} device={device} cos_lr=True close_mosaic=10 project=training_results_safe name=unified_egret_yolov11x_safe"""

    print("🌍 UNIFIED MULTI-SPECIES:")
    print(unified_cmd)
    print()


def show_safety_tips():
    """Show laptop safety tips"""
    print("\n🛡️  LAPTOP SAFETY TIPS")
    print("=" * 50)

    tips = [
        "✅ Keep laptop on a hard surface for ventilation",
        "✅ Monitor temperature (keep under 85°C)",
        "✅ Use external cooling if available",
        "✅ Don't block air vents",
        "✅ Stop if fan noise becomes excessive",
        "✅ Save work frequently (auto-save enabled)",
        "✅ Close unnecessary programs",
        "✅ Use Ctrl+C to stop training anytime",
        "✅ Training can be resumed from checkpoints",
    ]

    for tip in tips:
        print(tip)

    print("\n⚠️  EMERGENCY STOP:")
    print("   Press Ctrl+C to stop training immediately")
    print("   Models auto-save every 25 epochs")


def show_existing_training():
    """Show existing training runs"""
    print("\n📁 EXISTING TRAINING RUNS")
    print("=" * 50)

    training_dir = Path("../../training/runs")
    if training_dir.exists():
        runs = [d.name for d in training_dir.iterdir() if d.is_dir()]
        if runs:
            print("📊 Previous training runs found:")
            for run in runs:
                print(f"   • {run}")
        else:
            print("📭 No previous training runs found")
    else:
        print("📭 Training directory not found")


def main():
    """Main menu"""
    print("🦆 SAFE YOLOv11x TRAINING FOR RTX 3050 LAPTOP")
    print("=" * 60)
    print("🎯 GPU-optimized with safety features")
    print()

    show_existing_training()

    print("\n📋 MENU:")
    print("1. 🚀 Show training commands")
    print("2. 🛡️  Show safety tips")
    print("3. 📊 Check GPU status")
    print()

    choice = input("Select option (1-3): ").strip()

    if choice == "1":
        show_training_commands()
    elif choice == "2":
        show_safety_tips()
    elif choice == "3":
        check_gpu_status()
    else:
        print("❌ Invalid choice")


if __name__ == "__main__":
    main()
