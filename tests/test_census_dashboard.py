#!/usr/bin/env python3
"""
Simple test script for the new Census Dashboard functionality
This script tests URL resolution and basic Django functionality
"""

import os
import sys
import django
from django.urls import reverse, resolve
from django.conf import settings

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'avicast_project.settings.development')
django.setup()

def test_census_dashboard_url():
    """Test that the census dashboard URL is properly configured"""
    print("[OK] Testing census dashboard URL resolution...")

    try:
        # Test URL reversal
        url = reverse('locations:census_dashboard')
        print(f"[OK] Census dashboard URL: {url}")

        # Test URL resolution
        resolved = resolve(url)
        print(f"[OK] URL resolves to view: {resolved.view_name}")
        print(f"[OK] View function: {resolved.func.__name__}")

        return True

    except Exception as e:
        print(f"[ERROR] URL test failed: {e}")
        return False

def test_census_dashboard_template():
    """Test that the census dashboard template exists and is valid"""
    print("[OK] Testing census dashboard template...")

    try:
        template_path = 'templates/locations/census_dashboard.html'

        # Check if template file exists
        if os.path.exists(template_path):
            print(f"[OK] Template file exists: {template_path}")

            # Check template content
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Basic content checks
            if 'Bird Census Management' in content:
                print("[OK] Template contains expected title")
            else:
                print("[ERROR] Template missing expected title")
                return False

            if 'Total Census Records' in content:
                print("[OK] Template contains statistics section")
            else:
                print("[ERROR] Template missing statistics section")
                return False

            if 'monthlyChart' in content:
                print("[OK] Template contains chart integration")
            else:
                print("[ERROR] Template missing chart integration")
                return False

            if 'addCensusModal' in content:
                print("[OK] Template contains census creation modal")
            else:
                print("[ERROR] Template missing census creation modal")
                return False

            return True
        else:
            print(f"[ERROR] Template file not found: {template_path}")
            return False

    except Exception as e:
        print(f"[ERROR] Template test failed: {e}")
        return False

def test_navigation_integration():
    """Test that census dashboard is properly integrated into navigation"""
    print("[OK] Testing navigation integration...")

    try:
        # Check if base template contains census link
        base_template_path = 'templates/base.html'

        if os.path.exists(base_template_path):
            with open(base_template_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if 'census_dashboard' in content:
                print("[OK] Census dashboard link found in navigation")
            else:
                print("[ERROR] Census dashboard link not found in navigation")
                return False

            if 'Bird Census' in content:
                print("[OK] Census dashboard has proper menu label")
            else:
                print("[ERROR] Census dashboard missing proper menu label")
                return False

            return True
        else:
            print(f"[ERROR] Base template not found: {base_template_path}")
            return False

    except Exception as e:
        print(f"[ERROR] Navigation test failed: {e}")
        return False

def run_tests():
    """Run all tests"""
    print("Running Census Dashboard Integration Tests...")
    print("=" * 50)

    tests = [
        test_census_dashboard_url,
        test_census_dashboard_template,
        test_navigation_integration,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"[ERROR] {test.__name__} failed")
        except Exception as e:
            print(f"[ERROR] {test.__name__} raised exception: {e}")
        print()

    print("=" * 50)
    print(f"Tests passed: {passed}/{total}")

    if passed == total:
        print("[SUCCESS] All integration tests passed! Census Dashboard is properly configured.")
        return True
    else:
        print(f"[WARNING] {total - passed} tests failed. Please check the implementation.")
        return False

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
