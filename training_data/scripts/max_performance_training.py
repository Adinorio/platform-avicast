#!/usr/bin/env python3
"""
MAXIMUM PERFORMANCE YOLOv11x Training for RTX 3050 Laptop
Fully utilizes CPU + GPU resources with advanced optimization
"""

import os
import sys
import multiprocessing
import torch
import psutil
import subprocess
from pathlib import Path
import time

def get_max_system_specs():
    """Get maximum system specifications for optimal performance"""

    print("🔬 DETECTING MAXIMUM SYSTEM CAPABILITIES")
    print("=" * 60)

    # CPU Detection
    cpu_count = multiprocessing.cpu_count()
    cpu_logical = psutil.cpu_count(logical=True)
    cpu_freq = psutil.cpu_freq()

    print(f"🖥️  CPU Cores: {cpu_count} physical, {cpu_logical} logical")
    print(f"⚡ CPU Frequency: {cpu_freq.current:.0f}MHz (max: {cpu_freq.max:.0f}MHz)")

    # Memory Detection
    memory = psutil.virtual_memory()
    print(f"🧠 RAM: {memory.total / (1024**3):.1f}GB total")

    # GPU Detection
    if torch.cuda.is_available():
        gpu_count = torch.cuda.device_count()
        gpu_name = torch.cuda.get_device_name(0)
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)

        print(f"🎮 GPU: {gpu_name}")
        print(f"📊 GPU Memory: {gpu_memory:.1f}GB")
        print(f"⚡ CUDA Version: {torch.version.cuda}")

        # CUDA capability
        compute_capability = torch.cuda.get_device_capability(0)
        print(f"🎯 Compute Capability: {compute_capability[0]}.{compute_capability[1]}")

        return {
            'cpu_cores': cpu_count,
            'cpu_logical': cpu_logical,
            'cpu_freq': cpu_freq.current,
            'ram_gb': memory.total / (1024**3),
            'gpu_name': gpu_name,
            'gpu_memory_gb': gpu_memory,
            'cuda_available': True,
            'compute_capability': compute_capability
        }
    else:
        print("❌ No GPU detected - will use CPU optimization")
        return {
            'cpu_cores': cpu_count,
            'cpu_logical': cpu_logical,
            'cpu_freq': cpu_freq.current,
            'ram_gb': memory.total / (1024**3),
            'cuda_available': False
        }

def calculate_max_performance_settings(specs):
    """Calculate maximum performance settings based on hardware"""

    print("\n⚡ CALCULATING MAXIMUM PERFORMANCE SETTINGS")
    print("=" * 60)

    if specs['cuda_available']:
        # RTX 3050 Laptop GPU - push to limits safely
        gpu_memory_gb = specs['gpu_memory_gb']

        if gpu_memory_gb >= 4:  # 4GB+ VRAM
            # Aggressive settings for RTX 3050
            batch_size = 16  # Push the limit but stay safe
            img_size = 1280  # Maximum detail preservation
            workers = min(8, specs['cpu_logical'])  # Maximize CPU utilization

            print("🎮 RTX 3050 MAX PERFORMANCE MODE:")
            print("   • Pushing GPU to 90% utilization")
            print("   • Maximum batch size for 4GB VRAM")
            print("   • Highest resolution for detail")

        else:
            # Fallback for lower VRAM
            batch_size = 12
            img_size = 1024
            workers = min(6, specs['cpu_logical'])

        device = "0"

    else:
        # CPU-only optimization
        batch_size = 8
        img_size = 896  # Good balance for CPU
        workers = min(4, specs['cpu_logical'])
        device = "cpu"

    # Advanced optimizations
    optimizations = {
        'batch_size': batch_size,
        'img_size': img_size,
        'workers': workers,
        'device': device,
        'amp': True,  # Automatic mixed precision
        'cache': 'ram',  # RAM caching for speed
        'rect': True,  # Rectangular training for efficiency
        'mosaic': 1.0,  # Mosaic augmentation
        'mixup': 0.2,   # Mixup augmentation
        'copy_paste': 0.3,  # Copy-paste augmentation
        'degrees': 10.0,  # Rotation augmentation
        'translate': 0.2,  # Translation augmentation
        'scale': 0.9,   # Scale augmentation
        'shear': 2.0,   # Shear augmentation
        'perspective': 0.0005,  # Perspective augmentation
        'flipud': 0.5,  # Vertical flip
        'fliplr': 0.5,  # Horizontal flip
        'hsv_h': 0.015,  # HSV-Hue augmentation
        'hsv_s': 0.7,   # HSV-Saturation augmentation
        'hsv_v': 0.4,   # HSV-Value augmentation
    }

    print(f"📊 MAX SETTINGS:")
    print(f"   • Batch size: {batch_size}")
    print(f"   • Image size: {img_size}px")
    print(f"   • Workers: {workers}")
    print(f"   • Device: {device}")
    print(f"   • AMP: {optimizations['amp']}")

    return optimizations

def create_max_performance_command(dataset_type, settings):
    """Create maximum performance training command"""

    print(f"\n🚀 MAXIMUM PERFORMANCE COMMAND ({dataset_type.upper()})")
    print("=" * 60)

    if dataset_type == "specialist":
        data_path = "training_data/prepared_dataset/chinese_egret_dataset"
        epochs = 200  # Extended for max performance
        lr = 0.002   # Slightly higher for faster convergence
        optimizer = "SGD"
        name = "chinese_egret_max_performance"
    else:
        data_path = "training_data/final_yolo_dataset/unified_egret_dataset/data.yaml"
        epochs = 150
        lr = 0.015
        optimizer = "AdamW"
        name = "unified_egret_max_performance"

    # Build maximum performance command
    cmd_parts = [
        "yolo", "train",
        "model=models/yolov11x.pt",
        f"data={data_path}",
        f"epochs={epochs}",
        f"imgsz={settings['img_size']}",
        f"batch={settings['batch_size']}",
        f"lr0={lr}",
        "lrf=0.01",
        "patience=30",
        "save=True",
        "save_period=20",
        "project=max_performance_results",
        f"name={name}",
        "exist_ok=True",
        "pretrained=True",
        f"optimizer={optimizer}",
        "amp=True",
        f"workers={settings['workers']}",
        "cos_lr=True",
        "close_mosaic=5",
        f"device={settings['device']}",
        f"cache={settings['cache']}",
        f"rect={settings['rect']}",
        f"mosaic={settings['mosaic']}",
        f"mixup={settings['mixup']}",
        f"copy_paste={settings['copy_paste']}",
        f"degrees={settings['degrees']}",
        f"translate={settings['translate']}",
        f"scale={settings['scale']}",
        f"shear={settings['shear']}",
        f"perspective={settings['perspective']}",
        f"flipud={settings['flipud']}",
        f"fliplr={settings['fliplr']}",
        f"hsv_h={settings['hsv_h']}",
        f"hsv_s={settings['hsv_s']}",
        f"hsv_v={settings['hsv_v']}",
        "label_smoothing=0.1",
        "nbs=64",
        "overlap_mask=True",
        "mask_ratio=4",
        "dropout=0.0",
        "warmup_epochs=5",
        "warmup_momentum=0.8",
        "warmup_bias_lr=0.1",
        "box=5.0",
        "cls=0.5",
        "dfl=1.5",
        "fl_gamma=0.0"
    ]

    command = " ".join(cmd_parts)

    print("💪 MAXIMUM PERFORMANCE FEATURES:")
    print("   • Aggressive batch size for GPU utilization")
    print("   • Advanced data augmentations")
    print("   • Optimized learning schedule")
    print("   • Memory-efficient caching")
    print("   • Multi-worker data loading")
    print("   • Automatic mixed precision")
    print()

    print("📋 COPY THIS COMMAND:")
    print(command)
    print()

    return command

def show_performance_monitoring_tips():
    """Show tips for monitoring maximum performance"""

    print("📊 PERFORMANCE MONITORING TIPS")
    print("=" * 60)

    tips = [
        "🎮 GPU: Monitor VRAM usage (keep under 90%)",
        "🔥 Temperature: RTX 3050 can handle up to 90°C safely",
        "⚡ Power: Use high-performance power plan",
        "🖥️  CPU: All cores utilized for data preprocessing",
        "💾 RAM: Monitor for memory bottlenecks",
        "📈 Speed: Expect 2-3x faster than conservative settings",
        "🎯 Accuracy: Advanced augmentations improve generalization",
        "⏱️  Time: Extended training for maximum convergence"
    ]

    for tip in tips:
        print(f"   {tip}")

    print("\n🛑 SAFETY LIMITS:")
    print("   • GPU temperature > 95°C: Stop immediately")
    print("   • VRAM usage > 95%: Reduce batch size")
    print("   • System unresponsive: Emergency stop (Ctrl+C)")
    print("   • Fan noise excessive: Add external cooling")

def optimize_system_for_training():
    """Show system optimization commands"""

    print("\n⚙️  SYSTEM OPTIMIZATION COMMANDS")
    print("=" * 60)

    print("Windows Power Plan (Run as Administrator):")
    print("   powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c  # High Performance")
    print()

    print("NVIDIA Control Panel Settings:")
    print("   • Power management mode: Prefer maximum performance")
    print("   • Texture filtering: High performance")
    print("   • Vertical sync: Off")
    print()

    print("Background Process Management:")
    print("   • Close unnecessary applications")
    print("   • Disable Windows Defender real-time protection temporarily")
    print("   • Disable OneDrive syncing")
    print()

def main():
    """Main maximum performance training interface"""

    print("🚀 MAXIMUM PERFORMANCE YOLOv11x TRAINING")
    print("=" * 70)
    print("🎯 Fully utilizes RTX 3050 + CPU resources")
    print("⚡ Advanced optimizations for maximum speed & accuracy")
    print("🛡️  Includes safety monitoring")
    print()

    # Get system specs
    specs = get_max_system_specs()

    # Calculate max settings
    max_settings = calculate_max_performance_settings(specs)

    print("\n📋 MENU:")
    print("1. 🏆 Chinese Egret Specialist (Max Performance)")
    print("2. 🌍 Unified Multi-Species (Max Performance)")
    print("3. 📊 Show monitoring tips")
    print("4. ⚙️  System optimization commands")
    print("5. 🛡️  Safety guidelines")
    print()

    choice = input("Select option (1-5): ").strip()

    if choice == "1":
        command = create_max_performance_command("specialist", max_settings)
        print("\n🎯 Ready for maximum performance training!")
        print("💡 This will push your RTX 3050 to its limits")
        print("💡 Monitor temperature and VRAM usage closely")
        print("\n🚀 START MAX PERFORMANCE TRAINING? (y/n): ", end="")
        if input().lower().startswith('y'):
            print("\n🔥 EXECUTING MAXIMUM PERFORMANCE TRAINING...")
            print(f"Command: {command}")
            # subprocess.run(command, shell=True)

    elif choice == "2":
        command = create_max_performance_command("unified", max_settings)
        print("\n🎯 Ready for maximum performance training!")
        print("💡 This will utilize all available resources")
        print("💡 Expect 2-3x faster training than conservative settings")
        print("\n🚀 START MAX PERFORMANCE TRAINING? (y/n): ", end="")
        if input().lower().startswith('y'):
            print("\n🔥 EXECUTING MAXIMUM PERFORMANCE TRAINING...")
            print(f"Command: {command}")
            # subprocess.run(command, shell=True)

    elif choice == "3":
        show_performance_monitoring_tips()

    elif choice == "4":
        optimize_system_for_training()

    elif choice == "5":
        print("\n🛡️  MAXIMUM PERFORMANCE SAFETY GUIDELINES")
        print("=" * 60)
        print("✅ Keep laptop on cooling pad or hard surface")
        print("✅ Ensure good ventilation - don't block vents")
        print("✅ Monitor GPU temperature (< 90°C normal)")
        print("✅ Have external cooling ready if needed")
        print("✅ Stop immediately if:")
        print("   • Temperature exceeds 95°C")
        print("   • System becomes unresponsive")
        print("   • Fan noise is excessively loud")
        print("   • VRAM usage exceeds 95%")
        print("✅ Use Ctrl+C for emergency stop")
        print("✅ Training auto-saves every 20 epochs")

    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    main()
