#!/usr/bin/env python3
"""
Validate YOLO training configuration
"""

from pathlib import Path

import yaml

# Load and validate the YAML
with open("egret_training_config.yaml") as f:
    config = yaml.safe_load(f)

print("YAML loaded successfully:")
print(f'nc: {config.get("nc")}')
print(f'names: {config.get("names")}')

# Check paths
for split in ["train", "val", "test"]:
    path = config.get(split)
    if path:
        full_path = Path(path)
        exists = full_path.exists()
        print(f'{split}: {path} -> {"EXISTS" if exists else "NOT FOUND"}')

        if exists:
            # Count files
            png_count = len(list(full_path.glob("*.png")))
            npy_count = len(list(full_path.glob("*.npy")))
            jpg_count = len(list(full_path.glob("*.jpg")))
            total = png_count + npy_count + jpg_count
            print(f"  Files: {total} total ({png_count} PNG, {npy_count} NPY, {jpg_count} JPG)")
