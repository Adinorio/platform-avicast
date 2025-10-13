#!/usr/bin/env python
"""
Test script to verify the Django template syntax fix
"""
import os
import sys
import django
from django.conf import settings
from django.test import RequestFactory
from django.contrib.auth import get_user_model

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'avicast_project.settings.development')

# Setup Django
django.setup()

from apps.locations.models import Site
from apps.locations.site_views import site_detail

def test_template_fix():
    """Test that the site detail template loads without syntax errors"""
    print("Testing Django template syntax fix...")

    # Create a test user
    User = get_user_model()
    try:
        # Use a unique employee ID to avoid conflicts
        import uuid
        unique_id = f'TEST{uuid.uuid4().hex[:8].upper()}'
        user = User.objects.create_user(
            username=f'testuser_{unique_id}',
            password='testpass123',
            employee_id=unique_id,
            role='ADMIN'
        )
        print(f"[OK] Test user created with ID: {unique_id}")
    except Exception as e:
        print(f"[FAIL] Failed to create test user: {e}")
        return False

    # Create a test site
    try:
        site = Site.objects.create(
            name="Test Site",
            site_type="forest",
            coordinates="14.5995,120.9842",  # Manila coordinates
            description="Test site for template fix verification",
            created_by=user
        )
        print("[OK] Test site created")
    except Exception as e:
        print(f"[FAIL] Failed to create test site: {e}")
        return False

    # Test the view function
    try:
        factory = RequestFactory()
        request = factory.get(f'/locations/sites/{site.id}/')
        request.user = user

        # This should not raise a TemplateSyntaxError
        response = site_detail(request, site.id)

        if response.status_code == 200:
            print("[OK] Template renders successfully without syntax errors")
            print("[OK] Site detail page loads correctly")

            # Check if the response contains expected content
            if 'Census Overview' in response.content.decode():
                print("[OK] Census Overview section is present in template")
            else:
                print("[FAIL] Census Overview section missing from template")
                return False

            if 'Individual Bird Records' in response.content.decode():
                print("[OK] Individual Bird Records section is present in template")
            else:
                print("[FAIL] Individual Bird Records section missing from template")
                return False

        else:
            print(f"[FAIL] Template rendering failed with status {response.status_code}")
            return False

    except Exception as e:
        print(f"[FAIL] Template rendering failed: {e}")
        return False

    # Cleanup
    try:
        site.delete()
        user.delete()
        print("[OK] Test data cleaned up")
    except Exception as e:
        print(f"[WARN] Warning during cleanup: {e}")

    print("[SUCCESS] All tests passed! Template syntax fix is working correctly.")
    return True

if __name__ == "__main__":
    success = test_template_fix()
    sys.exit(0 if success else 1)
