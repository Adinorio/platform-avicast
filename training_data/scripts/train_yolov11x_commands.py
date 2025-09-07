#!/usr/bin/env python3
"""
YOLOv11x Training Commands for Egret Species Identification
Shows optimal training commands without executing them
"""

def show_training_options():
    """Display all training options and commands"""

    print("🦆 YOLOv11x TRAINING COMMANDS FOR EGRET IDENTIFICATION")
    print("=" * 70)
    print("Choose the best approach for your Chinese Egret conservation project")
    print()

    print("🎯 OPTION 1: CHINESE EGRET SPECIALIST (RECOMMENDED)")
    print("-" * 50)
    print("🏆 Best for: Maximum accuracy on critically endangered Chinese Egrets")
    print("📊 Single-class training with conservation-optimized parameters")
    print()
    print("🚀 TRAINING COMMAND:")
    print("yolo train model=models/yolov11x.pt \\")
    print("           data=training_data/prepared_dataset/chinese_egret_dataset \\")
    print("           epochs=150 imgsz=1280 batch=8 \\")
    print("           lr0=0.001 lrf=0.01 patience=50 \\")
    print("           optimizer=SGD amp=True workers=4 \\")
    print("           project=training_results \\")
    print("           name=chinese_egret_specialist_yolov11x")
    print()

    print("🌍 OPTION 2: UNIFIED MULTI-SPECIES")
    print("-" * 50)
    print("🌍 Best for: Comprehensive egret species identification")
    print("📊 4-class training (Chinese, Great, Intermediate, Little Egrets)")
    print()
    print("🚀 TRAINING COMMAND:")
    print("yolo train model=models/yolov11x.pt \\")
    print("           data=training_data/final_yolo_dataset/unified_egret_dataset/data.yaml \\")
    print("           epochs=100 imgsz=1024 batch=12 \\")
    print("           lr0=0.01 lrf=0.01 patience=30 \\")
    print("           optimizer=AdamW amp=True workers=4 \\")
    print("           cos_lr=True close_mosaic=10 \\")
    print("           project=training_results \\")
    print("           name=unified_egret_yolov11x")
    print()

    print("🔄 OPTION 3: HYBRID TWO-STAGE (BEST OF BOTH)")
    print("-" * 50)
    print("🔄 Best for: Conservation accuracy + field identification")
    print("📊 Stage 1: Specialist → Stage 2: Multi-class fine-tuning")
    print()
    print("🚀 STAGE 1 COMMAND (Specialist):")
    print("yolo train model=models/yolov11x.pt \\")
    print("           data=training_data/prepared_dataset/chinese_egret_dataset \\")
    print("           epochs=150 imgsz=1280 batch=8 \\")
    print("           lr0=0.001 lrf=0.01 patience=50 \\")
    print("           optimizer=SGD amp=True workers=4 \\")
    print("           project=training_results \\")
    print("           name=chinese_egret_specialist_yolov11x")
    print()
    print("🚀 STAGE 2 COMMAND (Fine-tuning):")
    print("yolo train model=training_results/chinese_egret_specialist_yolov11x/weights/best.pt \\")
    print("           data=training_data/final_yolo_dataset/unified_egret_dataset/data.yaml \\")
    print("           epochs=50 imgsz=1024 batch=8 \\")
    print("           lr0=0.0001 lrf=0.0001 patience=20 \\")
    print("           freeze=10 amp=True workers=4 \\")
    print("           project=training_results \\")
    print("           name=hybrid_egret_yolov11x")
    print()

    print("📊 TRAINING PARAMETERS EXPLAINED")
    print("-" * 50)
    print("🎯 imgsz=1280/1024: Higher resolution preserves bird details")
    print("⏰ epochs=150/100/50: Training duration (longer = better accuracy)")
    print("📦 batch=8/12: Batch size (smaller = more stable training)")
    print("🎓 lr0=0.001/0.01: Learning rate (lower = more precise)")
    print("⏸️  patience=50/30/20: Early stopping (prevents overfitting)")
    print("🔧 optimizer=SGD/AdamW: Optimization algorithm")
    print("⚡ amp=True: Automatic mixed precision (faster training)")
    print("👥 workers=4: Data loading workers")
    print()

    print("💡 RECOMMENDATION FOR YOUR PROJECT")
    print("-" * 50)
    print("🎯 For Chinese Egret conservation: Use OPTION 1 (Specialist)")
    print("🌍 For field identification: Use OPTION 2 (Unified)")
    print("🔄 For best results: Use OPTION 3 (Hybrid)")
    print()
    print("📈 Expected Results:")
    print("   • Specialist: ~95%+ mAP on Chinese Egrets")
    print("   • Unified: ~85-90% mAP across all species")
    print("   • Hybrid: ~92%+ mAP with multi-species capability")
    print()

def show_quick_commands():
    """Show quick copy-paste commands"""

    print("⚡ QUICK COMMANDS (Copy & Paste)")
    print("=" * 40)

    print("\n1️⃣ CHINESE EGRET SPECIALIST:")
    print('yolo train model=models/yolov11x.pt data=training_data/prepared_dataset/chinese_egret_dataset epochs=150 imgsz=1280 batch=8 lr0=0.001 lrf=0.01 patience=50 optimizer=SGD amp=True workers=4 project=training_results name=chinese_egret_specialist_yolov11x')

    print("\n2️⃣ UNIFIED MULTI-SPECIES:")
    print('yolo train model=models/yolov11x.pt data=training_data/final_yolo_dataset/unified_egret_dataset/data.yaml epochs=100 imgsz=1024 batch=12 lr0=0.01 lrf=0.01 patience=30 optimizer=AdamW amp=True workers=4 cos_lr=True close_mosaic=10 project=training_results name=unified_egret_yolov11x')

    print("\n3️⃣ HYBRID STAGE 1 (Specialist):")
    print('yolo train model=models/yolov11x.pt data=training_data/prepared_dataset/chinese_egret_dataset epochs=150 imgsz=1280 batch=8 lr0=0.001 lrf=0.01 patience=50 optimizer=SGD amp=True workers=4 project=training_results name=chinese_egret_specialist_yolov11x')

    print("\n3️⃣ HYBRID STAGE 2 (Fine-tuning):")
    print('yolo train model=training_results/chinese_egret_specialist_yolov11x/weights/best.pt data=training_data/final_yolo_dataset/unified_egret_dataset/data.yaml epochs=50 imgsz=1024 batch=8 lr0=0.0001 lrf=0.0001 patience=20 freeze=10 amp=True workers=4 project=training_results name=hybrid_egret_yolov11x')

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        show_quick_commands()
    else:
        show_training_options()




