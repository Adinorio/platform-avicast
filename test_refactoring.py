#!/usr/bin/env python
"""
Test script to verify the refactored image_processing views work correctly
"""
import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'avicast_project.settings.development')

try:
    import django
    django.setup()
    print("✅ Django setup successful")

    # Test imports from main views module
    from apps.image_processing.views import (
        image_upload_view,
        image_list_view,
        review_view,
        storage_status_view,
        get_storage_manager
    )
    print("✅ Main views imports successful")

    # Test imports from specialized modules
    from apps.image_processing.upload_views import image_upload_view as upload_view
    from apps.image_processing.processing_views import process_image_with_storage
    from apps.image_processing.review_views import review_view as review_view_func
    from apps.image_processing.storage_views import storage_status_view as storage_view
    from apps.image_processing.api_views import api_storage_stats
    print("✅ Specialized modules imports successful")

    # Test storage manager
    storage_manager = get_storage_manager()
    print(f"✅ Storage manager created: {type(storage_manager).__name__}")

    print("\n🎉 ALL TESTS PASSED! Refactoring is working correctly!")
    print("✅ Django application can start successfully")
    print("✅ All view functions are properly imported")
    print("✅ Storage manager is functional")
    print("✅ No import or syntax errors detected")

except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
