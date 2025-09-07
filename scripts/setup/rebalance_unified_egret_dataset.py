#!/usr/bin/env python3
"""
Rebalance YOLO dataset splits for unified egret dataset.

Targets for train split (images count per class):
- Chinese Egret: 400
- Great Egret: 200
- Intermediate Egret: 80
- Little Egret: 15

It will:
- Scan existing split folders under training_data/final_yolo_dataset/unified_egret_dataset
- For each class, gather available image+label pairs from train/val/test
- Move pairs into train until target is met, prefer existing train, then val, then test
- Keep remaining pairs in val/test (unchanged order)

Run:
  python scripts/setup/rebalance_unified_egret_dataset.py
"""
from pathlib import Path
import shutil
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[2]
DATASET = ROOT / "training_data/final_yolo_dataset/unified_egret_dataset"

CLASS_TO_ID = {
    "Chinese Egret": 0,
    "Great Egret": 1,
    "Intermediate Egret": 2,
    "Little Egret": 3,
}

NAME_PATTERNS = {
    0: ["chinese_egret_"],
    1: ["great_egret_"],
    2: ["intermediate_egret_"],
    3: ["little_egret_"],
}

TRAIN_TARGETS = {
    0: 400,
    1: 200,
    2: 80,
    3: 15,
}

def is_image(p: Path) -> bool:
    return p.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp"}

def collect_pairs(split: str):
    img_dir = DATASET / split / "images"
    lbl_dir = DATASET / split / "labels"
    pairs = []
    if not img_dir.exists():
        return pairs
    for img in img_dir.iterdir():
        if not is_image(img):
            continue
        lbl = lbl_dir / (img.stem + ".txt")
        if lbl.exists():
            pairs.append((img, lbl))
    return pairs

def infer_class_from_name(stem: str) -> int | None:
    for cid, prefixes in NAME_PATTERNS.items():
        if any(stem.startswith(pref) for pref in prefixes):
            return cid
    return None

def classify_pairs(pairs):
    by_class = defaultdict(list)
    for img, lbl in pairs:
        cid = infer_class_from_name(img.stem)
        if cid is None:
            # fallback: read first class id from label
            try:
                first = lbl.read_text().strip().split()[0]
                cid = int(first)
            except Exception:
                continue
        by_class[cid].append((img, lbl))
    return by_class

def ensure_dirs():
    for split in ["train", "val", "test"]:
        (DATASET / split / "images").mkdir(parents=True, exist_ok=True)
        (DATASET / split / "labels").mkdir(parents=True, exist_ok=True)

def move_pair(img: Path, lbl: Path, dst_split: str):
    dst_img = DATASET / dst_split / "images" / img.name
    dst_lbl = DATASET / dst_split / "labels" / lbl.name
    shutil.move(str(img), str(dst_img))
    shutil.move(str(lbl), str(dst_lbl))

def main():
    ensure_dirs()

    # Gather all pairs by split
    splits = {s: collect_pairs(s) for s in ["train", "val", "test"]}
    by_class = {s: classify_pairs(pairs) for s, pairs in splits.items()}

    # Current train counts
    train_counts = {cid: len(by_class["train"].get(cid, [])) for cid in CLASS_TO_ID.values()}

    print("Current train counts:", train_counts)

    # For each class, move from val/test to train until target
    for cid, target in TRAIN_TARGETS.items():
        have = train_counts.get(cid, 0)
        if have >= target:
            continue
        needed = target - have
        print(f"Class {cid}: need {needed} more for train")

        for src_split in ["val", "test"]:
            pool = list(by_class[src_split].get(cid, []))
            while needed > 0 and pool:
                img, lbl = pool.pop(0)
                move_pair(img, lbl, "train")
                needed -= 1

        if needed > 0:
            print(f"Warning: not enough samples available for class {cid}. Missing {needed}")

    # Report final counts
    final = {s: defaultdict(int) for s in ["train", "val", "test"]}
    for s in final.keys():
        pairs = collect_pairs(s)
        cls_map = classify_pairs(pairs)
        for cid, items in cls_map.items():
            final[s][cid] = len(items)

    print("Final counts per split:")
    for s in ["train", "val", "test"]:
        print(s, dict(final[s]))

if __name__ == "__main__":
    main()



