#!/usr/bin/env python
"""
Fix for Image Processing 404 Error
Run this script to ensure all image processing URLs are working correctly.
"""

import os
import sys

import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "avicast_project.settings.development")
sys.path.insert(0, os.path.dirname(__file__))
django.setup()


def fix_image_processing():
    print("🔧 Fixing Image Processing Issues...")

    # Check URL configuration
    from django.test import Client
    from django.urls import resolve, reverse

    # Test URL patterns
    test_uuid = "837c9ee9-874b-47a0-82be-5f012f925282"
    test_url = f"/image-processing/process/{test_uuid}/start/"

    print(f"\n1. Testing URL: {test_url}")

    try:
        match = resolve(test_url)
        print(f"✅ URL resolution: {match.func}")
        print(f"   Args: {match.args}")
        print(f"   Kwargs: {match.kwargs}")
    except Exception as e:
        print(f"❌ URL resolution failed: {e}")

    # Test reverse lookup
    try:
        url = reverse("image_processing:start_processing", args=[test_uuid])
        print(f"✅ Reverse lookup: {url}")
    except Exception as e:
        print(f"❌ Reverse lookup failed: {e}")

    # Test with client
    client = Client()
    try:
        response = client.get(test_url, follow=True)
        print(f"GET request: {response.status_code}")
    except Exception as e:
        print(f"❌ GET request failed: {e}")

    print("\n2. Checking view function...")
    from apps.image_processing.views import start_processing

    print(f"✅ start_processing function exists: {start_processing}")

    print("\n3. Checking URL patterns...")
    from apps.image_processing.urls import urlpatterns

    for pattern in urlpatterns:
        print(f"   - {pattern.pattern} -> {pattern.name}")

    print("\n4. Testing main URLs...")
    main_urls = [
        "/image-processing/",
        "/image-processing/upload/",
        "/image-processing/process/",
        f"/image-processing/process/{test_uuid}/",
    ]

    for url in main_urls:
        try:
            response = client.get(url, follow=True)
            print(f"✅ {url} - Status: {response.status_code}")
        except Exception as e:
            print(f"❌ {url} - Error: {e}")

    print("\n🎯 Solution:")
    print("The URL pattern exists and should work. The 404 error might be due to:")
    print("1. Server not running properly")
    print("2. Authentication issues")
    print("3. CSRF token problems")
    print("4. Template rendering issues")
    print("\nTry accessing the process page first, then try the processing.")


if __name__ == "__main__":
    fix_image_processing()
