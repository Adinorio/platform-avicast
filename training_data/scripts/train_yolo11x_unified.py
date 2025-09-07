#!/usr/bin/env python3
"""
Train YOLOv11x on the unified egret dataset with maximum-accuracy settings.
Bypasses pip update checks to avoid network interruptions.
"""

import os
import sys


def main() -> int:
    # Optional: make runs reproducible
    os.environ.setdefault("PYTHONHASHSEED", "42")

    # Import here so we can patch checks before train()
    from ultralytics.utils import checks

    # Bypass online pip/version check which may block in offline environments
    try:
        checks.check_pip_update_available = lambda: None  # type: ignore[attr-defined]
    except Exception:
        pass

    from ultralytics import YOLO

    model_path = "models/yolo11x.pt"
    data_yaml = "training_data/final_yolo_dataset/unified_egret_dataset/data.yaml"

    print("\n=== YOLOv11x Unified Egret Training (Max Accuracy) ===")
    print(f"Model: {model_path}")
    print(f"Data:  {data_yaml}")

    model = YOLO(model_path)

    overrides = dict(
        data=data_yaml,
        epochs=200,
        imgsz=1280,
        batch=20,
        device=0,
        optimizer="SGD",
        lr0=0.001,
        lrf=0.01,
        patience=50,
        amp=True,
        workers=4,
        cos_lr=True,
        close_mosaic=10,
        cache="disk",
        rect=True,
        mosaic=1.0,
        mixup=0.15,
        copy_paste=0.2,
        degrees=5.0,
        translate=0.1,
        scale=0.95,
        shear=1.0,
        perspective=0.0001,
        flipud=0.5,
        fliplr=0.5,
        hsv_h=0.005,
        hsv_s=0.3,
        hsv_v=0.2,
        nbs=64,
        # Segmentation-related args are harmless for detect; kept for compatibility
        overlap_mask=True,
        mask_ratio=4,
        dropout=0.0,
        warmup_epochs=10,
        warmup_momentum=0.8,
        warmup_bias_lr=0.1,
        box=5.0,
        cls=0.5,
        dfl=1.5,
        weight_decay=0.0001,
        project="yolov11x_max_accuracy_results",
        name="unified_egret_max_accuracy_200",
        seed=42,
        save=True,
        save_period=25,
    )

    print("\nOverrides:")
    for k, v in overrides.items():
        print(f"  {k} = {v}")

    print("\nStarting training...")
    model.train(**overrides)
    print("\nTraining completed.")
    print("Results saved under:", os.path.join(overrides["project"], overrides["name"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())






