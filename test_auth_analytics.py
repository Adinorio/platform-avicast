"""
Direct template test - bypasses authentication to test rendering
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'avicast_project.settings.development')
django.setup()

from django.test import RequestFactory, Client
from apps.users.models import User

# Create a test client
client = Client()

# Get the superadmin user
user = User.objects.get(employee_id='030303')
print(f"Testing with user: {user.employee_id} ({user.first_name} {user.last_name})")

# Login the user
login_success = client.login(employee_id='030303', password='avicast123')
print(f"Login successful: {login_success}")

if login_success:
    # Make request to analytics
    response = client.get('/analytics/')
    print(f"Status Code: {response.status_code}")
    print(f"Content Type: {response.get('Content-Type', 'Not set')}")
    
    content = response.content.decode('utf-8')
    print(f"Content Length: {len(content)} characters")
    
    # Check for the problematic include tags
    if '{% include' in content:
        print("[FAIL] PROBLEM: {% include %} tags found in output!")
        print("First occurrence:")
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if '{% include' in line:
                print(f"Line {i+1}: {line.strip()}")
                break
    else:
        print("[OK] SUCCESS: No {% include %} tags in output")
    
    # Check for success banner
    if 'Success! Analytics dashboard rendered correctly' in content:
        print("[OK] SUCCESS: Success banner found")
    else:
        print("[FAIL] PROBLEM: Success banner not found")
    
    # Check for metric cards
    if 'metric-card' in content:
        print("[OK] SUCCESS: Metric cards found")
    else:
        print("[FAIL] PROBLEM: Metric cards not found")
        
    # Save output to file for inspection
    with open('analytics_output.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("[FILE] Full output saved to analytics_output.html")
    
else:
    print("[FAIL] LOGIN FAILED - Check password")
