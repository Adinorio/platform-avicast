# 🦆 Chinese Egret Data Preparation - Complete Separation Guide

## 🎯 **What This Guide Shows**

This guide demonstrates **exactly how to separate** the Chinese Egret data preparation steps from the full Platform Avicast system, creating a standalone pipeline that can run independently.

---

## 📋 **Step-by-Step Data Preparation Process**

### **Step 1: Data Source Verification**
```bash
# Verify you have these source directories:
annotated_datasets/Chinese_Egret/
├── coco/           # COCO format annotations (JSON)
└── yolo/           # YOLO format annotations (ZIP files)
    ├── Chinese_Egret_Yolo_1.zip
    ├── Chinese_Egret_Yolo_2.zip
    └── ...

Chinese_Egret_Training/
├── Chinese_Egret_Batch1/     # 100 PNG images
├── Chinese_Egret_Batch2/     # 17 PNG images
├── Chinese_Egret_Batch3/     # Additional batches
└── ...
```

### **Step 2: Extract YOLO Annotations**
```python
# Extract all YOLO annotation ZIP files
import zipfile
from pathlib import Path

yolo_path = Path("annotated_datasets/Chinese_Egret/yolo")
labels_output = Path("prepared_data/labels")
labels_output.mkdir(parents=True, exist_ok=True)

for zip_file in yolo_path.glob("*.zip"):
    print(f"📦 Extracting {zip_file.name}...")
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        temp_dir = labels_output / f"temp_{zip_file.stem}"
        zip_ref.extractall(temp_dir)

        # Move all .txt files to main labels directory
        for txt_file in temp_dir.rglob("*.txt"):
            target = labels_output / txt_file.name
            if not target.exists():
                shutil.move(str(txt_file), str(target))

        shutil.rmtree(temp_dir)
```

**Result**: All YOLO annotation files (.txt) extracted to `prepared_data/labels/`

### **Step 3: Consolidate Training Images**
```python
# Consolidate images from all batch folders
training_path = Path("Chinese_Egret_Training")
images_output = Path("prepared_data/images")
images_output.mkdir(parents=True, exist_ok=True)

batch_folders = [d for d in training_path.iterdir()
                if d.is_dir() and d.name.startswith("Chinese_Egret_Batch")]

for batch in sorted(batch_folders):
    print(f"📁 Processing {batch.name}...")

    for ext in ['.png', '.jpg', '.jpeg', '.PNG', '.JPG', '.JPEG']:
        for img_file in batch.glob(f"*{ext}"):
            target = images_output / img_file.name
            if not target.exists():
                shutil.copy2(str(img_file), str(target))
```

**Result**: All training images consolidated to `prepared_data/images/`

### **Step 4: Verify Data Integrity**
```python
# Check that images and labels match
images_path = Path("prepared_data/images")
labels_path = Path("prepared_data/labels")

pairs = []
for ext in ['.png', '.jpg', '.jpeg', '.PNG', '.JPG', '.JPEG']:
    for img_file in images_path.glob(f"*{ext}"):
        lbl_file = labels_path / f"{img_file.stem}.txt"
        if lbl_file.exists():
            pairs.append((img_file, lbl_file))

print(f"✅ Found {len(pairs)} matched image-label pairs")
```

**Result**: Verification that all images have corresponding annotation files

### **Step 5: Create YOLO Dataset Structure**
```python
# Create train/valid/test splits (80/10/10)
dataset_path = Path("bird_dataset_v1")

# Create directory structure
for split in ['train', 'valid', 'test']:
    for subdir in ['images', 'labels']:
        (dataset_path / split / subdir).mkdir(parents=True, exist_ok=True)

# Split data
random.seed(42)
random.shuffle(pairs)

n_train = int(len(pairs) * 0.8)
n_valid = int(len(pairs) * 0.1)

train_pairs = pairs[:n_train]
valid_pairs = pairs[n_train:n_train + n_valid]
test_pairs = pairs[n_train + n_valid:]

# Copy files to respective directories
for img_file, lbl_file in train_pairs:
    shutil.copy2(str(img_file), str(dataset_path / 'train' / 'images' / img_file.name))
    shutil.copy2(str(lbl_file), str(dataset_path / 'train' / 'labels' / lbl_file.name))
```

**Result**: YOLO-compatible dataset structure created

### **Step 6: Generate Configuration File**
```python
# Create data.yaml configuration
yaml_content = f"""train: {dataset_path}/train
val: {dataset_path}/valid
test: {dataset_path}/test
nc: 1
names: ['Chinese_Egret']
"""

with open(dataset_path / "data.yaml", 'w', encoding='utf-8') as f:
    f.write(yaml_content)
```

**Result**: `bird_dataset_v1/data.yaml` configuration file

---

## 🗂️ **What Files Can Be Separated**

### **✅ CORE DATA PREPARATION FILES (Standalone)**
```
📁 Minimal Data Preparation Package:
├── prepare_data_minimal.py          # Standalone preparation script
├── annotated_datasets/              # Source annotations
├── Chinese_Egret_Training/          # Source images
├── prepared_data/                   # Intermediate processed data
└── bird_dataset_v1/                 # Final YOLO dataset
```

### **❌ FULL SYSTEM FILES (Can be excluded)**
```
📁 Platform Avicast Web Application (2GB+):
├── apps/                            # Django applications
├── avicast_project/                 # Django project settings
├── media/                           # User uploaded files
├── static/                          # Static assets
├── templates/                       # HTML templates
├── db.sqlite3                       # Database
├── manage.py                        # Django management script
└── requirements.txt                 # Full web app dependencies
```

### **🎯 TRAINING-ONLY FILES (Recommended Separation)**
```
📁 Standalone Training Environment:
├── train_chinese_egret.py           # Training script
├── bird_dataset_v1/                 # Dataset (1,198 images)
├── models/                          # YOLOv8 weights
├── prepare_data_minimal.py          # Data prep (standalone)
├── requirements-minimal.txt         # Minimal dependencies
└── README-training.md               # Training documentation
```

---

## 🚀 **How to Use the Separated Process**

### **Option 1: Use the Complete Standalone Script**
```bash
# Run the full data preparation pipeline
python data_preparation_only.py

# This creates:
# - prepared_data/ (intermediate)
# - bird_dataset_v1/ (final dataset)
# - prepare_data_minimal.py (standalone version)
```

### **Option 2: Use the Minimal Script**
```bash
# Use the stripped-down version
python prepare_data_minimal.py

# This contains ONLY:
# - YOLO annotation extraction
# - Image consolidation
# - Dataset structure creation
# - No web app dependencies
```

### **Option 3: Manual Step-by-Step**
```python
# Import and run individual steps
from data_preparation_only import (
    step_1_collect_raw_data,
    step_2_extract_annotations,
    step_3_consolidate_images,
    step_4_verify_data_integrity,
    step_5_create_dataset_structure,
    step_6_validate_final_dataset
)

# Run each step individually
step_1_collect_raw_data()
step_2_extract_annotations()
step_3_consolidate_images()
step_4_verify_data_integrity()
step_5_create_dataset_structure()
step_6_validate_final_dataset()
```

---

## 📊 **Data Flow Summary**

```
Raw Data Sources
├── annotated_datasets/Chinese_Egret/yolo/*.zip    # YOLO annotations (ZIP)
└── Chinese_Egret_Training/Batch*/                 # Training images (PNG)

Data Preparation Pipeline
├── Step 1: Extract YOLO .txt files from ZIPs
├── Step 2: Consolidate all images into single folder
├── Step 3: Verify image-label matching
├── Step 4: Create train/valid/test splits (80/10/10)
├── Step 5: Copy files to YOLO directory structure
└── Step 6: Generate data.yaml configuration

Final Output
└── bird_dataset_v1/
    ├── train/images/     # 958 images (80%)
    ├── train/labels/     # 958 labels
    ├── valid/images/     # 119 images (10%)
    ├── valid/labels/     # 119 labels
    ├── test/images/      # 121 images (10%)
    ├── test/labels/      # 121 labels
    └── data.yaml         # YOLO configuration
```

---

## 🛠️ **Required Dependencies (Minimal)**

```txt
# requirements-minimal.txt
torch>=2.0.0
torchvision>=0.15.0
ultralytics>=8.0.0
numpy>=1.24.0
opencv-python>=4.7.0
PyYAML>=6.0
```

**No Django, no web framework dependencies needed!**

---

## 🎯 **Benefits of This Separation**

1. **🚀 Independent Operation**: Data preparation runs without web app
2. **📦 Portable**: Easy to move, share, or run on different systems
3. **⚡ Fast Setup**: Minimal dependencies to install
4. **🎯 Focused**: Only what you need for training
5. **🔧 Maintainable**: Clear separation of concerns
6. **📈 Scalable**: Can be run on different hardware independently

---

## 📞 **Usage Examples**

### **Quick Data Preparation:**
```bash
# Prepare data only (no training)
python prepare_data_minimal.py
```

### **Full Pipeline (Data + Training):**
```bash
# Prepare data
python prepare_data_minimal.py

# Then train
python train_chinese_egret.py --model-size s --epochs 100
```

### **On Different Machine:**
```bash
# Copy these files to new machine:
# - prepare_data_minimal.py
# - annotated_datasets/
# - Chinese_Egret_Training/

# Install minimal requirements
pip install -r requirements-minimal.txt

# Run preparation
python prepare_data_minimal.py
```

---

**🎉 This gives you complete separation of the data preparation process from the Platform Avicast web application, allowing you to prepare training data independently!** 🦆✨






