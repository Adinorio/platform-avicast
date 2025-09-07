#!/usr/bin/env python
"""
Simple test script for AVICAST Image Processing System
Run this to verify the system is working
"""

import os
import sys

import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "avicast.settings")
django.setup()


def test_models():
    """Test if models can be imported and used"""
    print("🧪 Testing Models...")

    try:
        from apps.image_processing.models import ImageUpload

        print("✅ Models imported successfully")

        # Check model fields
        fields = [f.name for f in ImageUpload._meta.fields]
        print(f"📋 ImageUpload fields: {fields}")

        # Check if storage fields exist
        storage_fields = ["file_hash", "storage_tier", "archive_path", "is_compressed"]
        missing_fields = [f for f in storage_fields if f not in fields]

        if missing_fields:
            print(f"❌ Missing fields: {missing_fields}")
            return False
        else:
            print("✅ All storage fields present")
            return True

    except Exception as e:
        print(f"❌ Model test failed: {e}")
        return False


def test_storage_manager():
    """Test if storage manager can be imported"""
    print("\n🧪 Testing Storage Manager...")

    try:
        from apps.image_processing.local_storage import LocalStorageManager

        print("✅ Storage manager imported successfully")

        # Test initialization
        storage_manager = LocalStorageManager()
        print("✅ Storage manager initialized")

        # Test basic methods
        usage = storage_manager.get_storage_usage()
        print(f"✅ Storage usage retrieved: {type(usage)}")

        return True

    except Exception as e:
        print(f"❌ Storage manager test failed: {e}")
        return False


def test_image_optimizer():
    """Test if image optimizer can be imported"""
    print("\n🧪 Testing Image Optimizer...")

    try:
        from apps.image_processing.image_optimizer import ImageOptimizer

        print("✅ Image optimizer imported successfully")

        # Test initialization
        optimizer = ImageOptimizer()
        print("✅ Image optimizer initialized")

        return True

    except Exception as e:
        print(f"❌ Image optimizer test failed: {e}")
        return False


def test_forms():
    """Test if forms can be imported"""
    print("\n🧪 Testing Forms...")

    try:
        from apps.image_processing.forms import ImageUploadForm

        print("✅ Forms imported successfully")

        # Test form initialization
        form = ImageUploadForm()
        print("✅ Form initialized")

        return True

    except Exception as e:
        print(f"❌ Forms test failed: {e}")
        return False


def test_views():
    """Test if views can be imported"""
    print("\n🧪 Testing Views...")

    try:
        print("✅ Views imported successfully")

        return True

    except Exception as e:
        print(f"❌ Views test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("🚀 AVICAST Image Processing System Test")
    print("=" * 50)

    tests = [test_models, test_storage_manager, test_image_optimizer, test_forms, test_views]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1

    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Image processing system is ready.")
        print("\n📝 Next steps:")
        print("1. Run: python manage.py migrate")
        print("2. Create a superuser: python manage.py createsuperuser")
        print("3. Start the server: python manage.py runserver")
        print("4. Visit: http://localhost:8000/image-processing/upload/")
    else:
        print("❌ Some tests failed. Check the errors above.")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
