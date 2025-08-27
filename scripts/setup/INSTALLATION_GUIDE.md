# Platform Avicast - Installation Guide

## 📋 Requirements File Structure

This project now uses a **modular requirements structure** for better organization:

### Core Requirements (`requirements.txt`)
- Django framework and core functionality
- Database support (PostgreSQL/SQLite)
- UI components and form handling
- Security and performance packages
- Basic utilities

### Processing Requirements (`requirements-processing.txt`)
- AI/ML dependencies for bird detection
- YOLO object detection (Ultralytics)
- Computer vision (OpenCV)
- Deep learning (PyTorch)
- Data processing and analysis

## 🚀 Installation Options

### Option 1: Quick Setup (Recommended)
```bash
# 1. Install core dependencies
pip install -r requirements.txt

# 2. Install processing dependencies
pip install -r requirements-processing.txt

# 3. Run Django migrations
python manage.py migrate

# 4. Start the server
python manage.py runserver
```

### Option 2: Automated Setup
```bash
# Run the automated setup script
python scripts/setup/setup_processing_dependencies.py
```

### Option 3: Development Setup
```bash
# For development with all optional packages
pip install -r requirements.txt
pip install -r requirements-processing.txt

# Optional: Install development dependencies
# pip install pytest pytest-django coverage
```

## 🔧 Troubleshooting

### Processing Not Working?
If image processing appears slow or stuck:

1. **Check dependencies are installed:**
   ```bash
   python -c "from ultralytics import YOLO; import cv2; print('✅ All good')"
   ```

2. **Reinstall processing dependencies:**
   ```bash
   pip install -r requirements-processing.txt --force-reinstall
   ```

3. **Check GPU availability:**
   ```bash
   python -c "import torch; print('GPU:', torch.cuda.is_available())"
   ```

### GPU Acceleration (Optional)
For faster processing, install GPU-enabled PyTorch:
```bash
# Remove CPU-only version
pip uninstall torch torchvision torchaudio

# Install GPU version (requires NVIDIA GPU + CUDA)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

## 📦 Package Details

### Core Dependencies
- **Django**: Web framework
- **PostgreSQL/SQLite**: Database support
- **Pillow**: Basic image processing
- **Bootstrap**: UI framework

### Processing Dependencies
- **Ultralytics**: YOLO object detection
- **OpenCV**: Computer vision
- **PyTorch**: Deep learning framework
- **NumPy**: Numerical computing
- **scikit-learn**: Machine learning

## 🎯 Performance Notes

- **CPU Processing**: ~15-30 seconds per image
- **GPU Processing**: ~2-5 seconds per image
- **Batch Processing**: Faster for multiple images

## 🔍 Verification

After installation, test that everything works:
```bash
# Test Django server
python manage.py runserver

# Test processing dependencies
python -c "from apps.image_processing.bird_detection_service import get_bird_detection_service; print('Service available:', get_bird_detection_service().is_available())"
```

## 📚 Additional Resources

- [Ultralytics YOLO Documentation](https://docs.ultralytics.com/)
- [PyTorch Installation Guide](https://pytorch.org/get-started/locally/)
- [OpenCV Documentation](https://docs.opencv.org/)
