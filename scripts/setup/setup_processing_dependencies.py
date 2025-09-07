#!/usr/bin/env python
"""
Setup script for image processing dependencies
Run this to ensure all AI/ML packages are properly installed
"""

import platform
import subprocess
import sys


def run_command(command, description):
    """Run a command and return success status"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - SUCCESS")
            if result.stdout.strip():
                print(f"   Output: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ {description} - FAILED")
            if result.stderr.strip():
                print(f"   Error: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False


def check_gpu():
    """Check if GPU support is available"""
    print("\n🔍 Checking GPU availability...")
    try:
        import torch

        if torch.cuda.is_available():
            print(f"✅ GPU detected: {torch.cuda.get_device_name(0)}")
            print(f"   CUDA version: {torch.version.cuda}")
            return True
        else:
            print("❌ No GPU detected - using CPU only")
            return False
    except ImportError:
        print("⚠️  PyTorch not installed yet")
        return False


def main():
    print("🚀 Setting up Platform Avicast Image Processing Dependencies")
    print("=" * 60)

    # Check Python version
    print(f"🐍 Python version: {sys.version}")
    print(f"🖥️  Platform: {platform.system()} {platform.release()}")

    # Check GPU first
    gpu_available = check_gpu()

    # Install processing dependencies
    if run_command("pip install -r requirements-processing.txt", "Installing AI/ML dependencies"):
        print("\n✅ Core processing dependencies installed successfully!")

        # Verify installations
        print("\n🔍 Verifying installations...")
        verifications = [
            ("import torch; print(f'PyTorch: {torch.__version__}')", "PyTorch"),
            ("import torchvision; print('TorchVision: OK')", "TorchVision"),
            ("from ultralytics import YOLO; print('Ultralytics: OK')", "Ultralytics"),
            ("import cv2; print('OpenCV: OK')", "OpenCV"),
            ("import numpy; print(f'NumPy: {numpy.__version__}')", "NumPy"),
        ]

        all_good = True
        for cmd, name in verifications:
            if not run_command(f'python -c "{cmd}"', f"Verifying {name}"):
                all_good = False

        if all_good:
            print("\n🎉 All processing dependencies are working!")
            print("\n📋 Next steps:")
            print("   1. Start the server: python manage.py runserver")
            print("   2. Test image processing at: http://localhost:8000/image-processing/")
            print("   3. Upload an image and try processing it")

            if not gpu_available:
                print("\n⚡ For faster processing, consider installing GPU support:")
                print("   pip uninstall torch torchvision torchaudio")
                print(
                    "   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118"
                )
        else:
            print("\n❌ Some dependencies failed to install properly")
            print("   Try installing individually: pip install ultralytics opencv-python")
    else:
        print("\n❌ Failed to install processing dependencies")
        print("   Check your internet connection and try again")
        sys.exit(1)


if __name__ == "__main__":
    main()
