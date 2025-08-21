#!/usr/bin/env python
import os
import sys
import django
from django.conf import settings
from django.test import Client
from django.urls import reverse

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'avicast_project.settings.development')
django.setup()

def test_urls():
    client = Client()

    # Test URLs
    urls_to_test = [
        '/image-processing/',
        '/image-processing/upload/',
        '/image-processing/process/',
        '/image-processing/review/',
    ]

    print("🔍 Testing URL accessibility...")
    for url in urls_to_test:
        try:
            response = client.get(url, follow=True)
            print(f"✅ {url} - Status: {response.status_code}")
        except Exception as e:
            print(f"❌ {url} - Error: {e}")

    # Test named URLs
    try:
        # Test different naming patterns
        url_patterns = [
            'image_processing:start_processing',
            'start_processing',
        ]

        for pattern in url_patterns:
            try:
                url = reverse(pattern, args=['test-uuid'])
                print(f"✅ {pattern} URL: {url}")
                break
            except Exception as e:
                print(f"❌ {pattern}: {e}")
    except Exception as e:
        print(f"❌ URL reverse error: {e}")

    # Test URL resolution
    from django.urls import resolve
    try:
        match = resolve('/image-processing/process/test-uuid/start/')
        print(f"✅ URL resolution: {match}")
        print(f"   View function: {match.func}")
        print(f"   Args: {match.args}")
        print(f"   Kwargs: {match.kwargs}")
    except Exception as e:
        print(f"❌ URL resolution error: {e}")

if __name__ == '__main__':
    test_urls()
