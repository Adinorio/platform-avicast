"""
Test script to verify analytics dashboard rendering without authentication.
This bypasses @login_required to test if templates render correctly.
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'avicast_project.settings.development')
django.setup()

from django.test import RequestFactory
from apps.users.models import User
from apps.analytics.views import dashboard

# Create a mock request
factory = RequestFactory()
request = factory.get('/analytics/')

# Get or create a test user
user = User.objects.filter(employee_id='010101').first()
if not user:
    print("[ERROR] Default superadmin user not found!")
    print("Run: python create_default_user.py")
    exit(1)

# Attach user to request (simulate authentication)
request.user = user

# Call the view
try:
    response = dashboard(request)
    
    print("[OK] SUCCESS: Analytics view executed")
    print(f"Status Code: {response.status_code}")
    print(f"Content Type: {response.get('Content-Type', 'Not set')}")
    print(f"\nFirst 1000 characters of rendered HTML:")
    print("="*80)
    
    content = response.content.decode('utf-8')
    print(content[:1000])
    
    print("\n" + "="*80)
    print(f"\nTotal HTML length: {len(content)} characters")
    
    # Check for key elements
    checks = {
        'Has DOCTYPE': '<!DOCTYPE html>' in content,
        'Has Analytics Dashboard title': 'Analytics Dashboard' in content,
        'Has metric cards': 'metric-card' in content,
        'Has charts': 'chart-container' in content,
        'Has Plotly script': 'plotly' in content.lower(),
        'Has Bootstrap': 'bootstrap' in content.lower(),
    }
    
    print("\nContent Checks:")
    for check, result in checks.items():
        icon = "[OK]" if result else "[FAIL]"
        print(f"{icon} {check}: {result}")
        
except Exception as e:
    print(f"[ERROR] {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()

