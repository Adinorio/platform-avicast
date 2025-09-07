#!/usr/bin/env python
import os
import sys

import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "avicast_project.settings.development")
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from django.test import Client
from django.urls import resolve, reverse


def test_endpoint():
    print("🔍 Testing image processing endpoint...")

    # Test URL resolution
    try:
        match = resolve("/image-processing/process/test-uuid/start/")
        print("✅ URL resolution successful")
        print(f"   View function: {match.func}")
        print(f"   Kwargs: {match.kwargs}")
    except Exception as e:
        print(f"❌ URL resolution error: {e}")

    # Test reverse lookup
    try:
        url = reverse("image_processing:start_processing", args=["test-uuid"])
        print(f"✅ Reverse lookup successful: {url}")
    except Exception as e:
        print(f"❌ Reverse lookup error: {e}")

    # Test with client (GET request - will redirect to login)
    client = Client()
    try:
        response = client.get("/image-processing/process/test-uuid/start/", follow=True)
        print(f"GET request status: {response.status_code}")
        if response.status_code == 302:
            print("   (302 is expected - redirects to login since not authenticated)")
    except Exception as e:
        print(f"❌ GET request error: {e}")


if __name__ == "__main__":
    test_endpoint()
