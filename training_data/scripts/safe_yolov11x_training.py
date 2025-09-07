#!/usr/bin/env python3
"""
SAFE YOLOv11x Training with GPU/CPU Support and Resource Management
Optimized for laptop training with RTX 3050 GPU
"""

import os
import sys
import psutil
import GPUtil
import torch
from pathlib import Path
import subprocess
import time

def check_system_resources():
    """Check system resources and GPU availability"""
    print("🖥️  SYSTEM RESOURCE CHECK")
    print("=" * 50)

    # CPU Info
    cpu_count = psutil.cpu_count()
    cpu_logical = psutil.cpu_count(logical=True)
    cpu_percent = psutil.cpu_percent(interval=1)

    print(f"🖥️  CPU Cores: {cpu_count} physical, {cpu_logical} logical")
    print(f"📊 CPU Usage: {cpu_percent}%")

    # Memory Info
    memory = psutil.virtual_memory()
    print(f"🧠 RAM: {memory.total / (1024**3):.1f} GB total")
    print(f"📊 RAM Usage: {memory.percent}%")

    # GPU Info
    try:
        gpus = GPUtil.getGPUs()
        if gpus:
            gpu = gpus[0]
            print(f"🎮 GPU: {gpu.name}")
            print(f"📊 GPU Memory: {gpu.memoryTotal} MB")
            print(f"🔥 GPU Temperature: {gpu.temperature}°C")
            print(f"⚡ GPU Usage: {gpu.load * 100:.1f}%")
            return True
        else:
            print("❌ No GPU detected")
            return False
    except:
        print("❌ GPU monitoring not available")
        return False

def get_optimal_training_settings():
    """Get optimal training settings based on hardware"""

    print("\n🎯 OPTIMIZING TRAINING SETTINGS")
    print("=" * 50)

    # Check GPU memory
    gpu_memory = None
    try:
        gpus = GPUtil.getGPUs()
        if gpus:
            gpu_memory = gpus[0].memoryTotal
    except:
        pass

    # Get system memory
    system_memory = psutil.virtual_memory().total / (1024**3)  # GB

    # RTX 3050 Laptop GPU optimization
    if gpu_memory and gpu_memory >= 4000:  # 4GB+ GPU memory
        print("🎮 RTX 3050 detected - using GPU optimization")

        # Safe batch sizes for RTX 3050
        batch_size = 8  # Conservative for 4GB VRAM
        img_size = 1024  # Good balance for bird details
        workers = 4  # Reasonable for laptop

        print("📊 GPU Settings:")
        print(f"   • Batch size: {batch_size}")
        print(f"   • Image size: {img_size}px")
        print(f"   • Workers: {workers}")

    else:
        print("🖥️  CPU-only mode - using conservative settings")
        batch_size = 4
        img_size = 640
        workers = 2

        print("📊 CPU Settings:")
        print(f"   • Batch size: {batch_size}")
        print(f"   • Image size: {img_size}px")
        print(f"   • Workers: {workers}")

    return {
        'batch_size': batch_size,
        'img_size': img_size,
        'workers': workers,
        'gpu_available': torch.cuda.is_available()
    }

def create_safe_training_command(dataset_type="specialist"):
    """Create safe training command with resource management"""

    settings = get_optimal_training_settings()

    print(f"\n🚀 SAFE TRAINING COMMAND ({dataset_type.upper()})")
    print("=" * 50)

    if dataset_type == "specialist":
        data_path = "training_data/prepared_dataset/chinese_egret_dataset"
        epochs = 150
        lr = 0.001
        optimizer = "SGD"
        name = "chinese_egret_specialist_yolov11x_safe"
    else:
        data_path = "training_data/final_yolo_dataset/unified_egret_dataset/data.yaml"
        epochs = 100
        lr = 0.01
        optimizer = "AdamW"
        name = "unified_egret_yolov11x_safe"

    # Build command with safety settings
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
        "save_period=25",
        "project=training_results_safe",
        f"name={name}",
        "exist_ok=True",
        "pretrained=True",
        f"optimizer={optimizer}",
        "amp=True",  # Automatic mixed precision for efficiency
        f"workers={settings['workers']}",
        "cos_lr=True",  # Cosine learning rate scheduling
        "close_mosaic=10",  # Close mosaic augmentation
        "cache=disk"  # Disk caching for memory efficiency
    ]

    # GPU-specific settings
    if settings['gpu_available']:
        cmd_parts.append("device=0")  # Use GPU 0
        print("🎮 GPU Mode: Using CUDA device 0 (RTX 3050)")
    else:
        cmd_parts.append("device=cpu")
        print("🖥️  CPU Mode: Using CPU only")

    command = " ".join(cmd_parts)

    print("\n📋 TRAINING COMMAND:")
    print(command)
    print()

    return command

def monitor_training_resources(duration_minutes=5):
    """Monitor system resources during training simulation"""

    print(f"\n📊 MONITORING SYSTEM RESOURCES ({duration_minutes} minutes)")
    print("=" * 50)

    for i in range(duration_minutes * 6):  # Check every 10 seconds
        try:
            # CPU and Memory
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()

            # GPU (if available)
            gpu_info = ""
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]
                    gpu_info = f" | GPU: {gpu.load*100:.1f}% | VRAM: {gpu.memoryUsed}/{gpu.memoryTotal}MB | Temp: {gpu.temperature}°C"
            except:
                pass

            print(".1f" % (i/6, cpu_percent, memory.percent, gpu_info))
            time.sleep(10)

        except KeyboardInterrupt:
            print("\n⏹️  Monitoring stopped by user")
            break

    print("\n✅ Resource monitoring completed")

def show_safety_features():
    """Show safety features built into the training"""

    print("\n🛡️  SAFETY FEATURES")
    print("=" * 50)

    safety_features = [
        "✅ Automatic GPU/CPU detection",
        "✅ Conservative batch sizes for RTX 3050",
        "✅ Early stopping with patience=30",
        "✅ Automatic mixed precision (AMP)",
        "✅ Cosine learning rate scheduling",
        "✅ Disk caching for memory efficiency",
        "✅ Regular checkpoint saving",
        "✅ Resource monitoring capability",
        "✅ Graceful fallback to CPU mode"
    ]

    for feature in safety_features:
        print(feature)

    print("\n⚠️  LAPTOP PROTECTION:")
    print("   • Conservative GPU memory usage")
    print("   • Thermal monitoring capability")
    print("   • CPU usage monitoring")
    print("   • Emergency stop with Ctrl+C")

def main():
    """Main training menu"""

    print("🦆 SAFE YOLOv11x TRAINING FOR EGRET IDENTIFICATION")
    print("=" * 60)
    print("🎯 Optimized for RTX 3050 Laptop GPU with safety features")
    print()

    # Check resources
    check_system_resources()

    print("\n📋 TRAINING OPTIONS:")
    print("1. 🏆 Chinese Egret Specialist (Recommended for conservation)")
    print("2. 🌍 Unified Multi-Species (Comprehensive identification)")
    print("3. 📊 Monitor system resources (5-minute test)")
    print("4. 🛡️  Show safety features")
    print()

    choice = input("Select option (1-4): ").strip()

    if choice == "1":
        command = create_safe_training_command("specialist")
        print("\n🎯 Ready to start training!")
        print("💡 Tip: Monitor your laptop temperature during training")
        print("💡 Tip: Use Ctrl+C to stop training anytime")
        print("\n🚀 START TRAINING? (y/n): ", end="")
        if input().lower().startswith('y'):
            print(f"\n🔥 Executing: {command}")
            # subprocess.run(command, shell=True)

    elif choice == "2":
        command = create_safe_training_command("unified")
        print("\n🎯 Ready to start training!")
        print("💡 Tip: Monitor your laptop temperature during training")
        print("💡 Tip: Use Ctrl+C to stop training anytime")
        print("\n🚀 START TRAINING? (y/n): ", end="")
        if input().lower().startswith('y'):
            print(f"\n🔥 Executing: {command}")
            # subprocess.run(command, shell=True)

    elif choice == "3":
        monitor_training_resources(5)

    elif choice == "4":
        show_safety_features()

    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    main()
