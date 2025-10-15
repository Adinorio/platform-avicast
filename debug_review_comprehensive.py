#!/usr/bin/env python
"""
Comprehensive debug of review view
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'avicast_project.settings.development')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from apps.image_processing.models import ProcessingResult, ReviewDecision

User = get_user_model()

print('=== COMPREHENSIVE REVIEW DEBUG ===')
print()

# Check current users
admin_users = User.objects.filter(role='ADMIN')
superadmin_users = User.objects.filter(role='SUPERADMIN')

print(f'ADMIN users: {admin_users.count()}')
print(f'SUPERADMIN users: {superadmin_users.count()}')

# Get test user
test_user = None
if admin_users.exists():
    test_user = admin_users.first()
    print(f'Using ADMIN user: {test_user.employee_id}')
elif superadmin_users.exists():
    test_user = superadmin_users.first()
    print(f'Using SUPERADMIN user: {test_user.employee_id}')
else:
    # Find any user
    all_users = User.objects.all()
    if all_users.exists():
        test_user = all_users.first()
        print(f'Using regular user: {test_user.employee_id} (role: {test_user.role})')

if not test_user:
    print('No users found!')
    exit()

print(f'User role: {test_user.role}')
print()

# Create client and login
client = Client()
client.force_login(test_user)

# Test the review view
response = client.get('/image-processing/review/')

print(f'Review page status: {response.status_code}')

if response.status_code == 200:
    # Check if context exists
    if hasattr(response, 'context_data') and response.context_data:
        context = response.context_data

        if 'pending_results' in context:
            pending_results = context['pending_results']
            print(f'Context pending_results: {len(pending_results)} items')

            # Show first few
            for i, result in enumerate(pending_results[:3], 1):
                print(f'  {i}. {result.image_upload.title} - {result.review_decision}')
        else:
            print('No pending_results in context')
            print('Available context keys:', list(context.keys()) if context else 'None')

        if 'title' in context:
            print(f'Context title: {context["title"]}')
    else:
        print('No context data available')

    # Check if there's an error in the response content
    content = response.content.decode()
    if 'error' in content.lower() or 'exception' in content.lower():
        print('ERROR found in response content!')
        print('Content preview:', content[:500])
else:
    print(f'View returned error status: {response.status_code}')
    print('Response content preview:', response.content.decode()[:500])

print()
print('=== DIRECT QUERY TEST ===')
# Test the query directly
if test_user.role in ['SUPERADMIN', 'ADMIN']:
    direct_results = ProcessingResult.objects.filter(review_decision=ReviewDecision.PENDING).order_by('-created_at')
else:
    direct_results = ProcessingResult.objects.filter(
        image_upload__uploaded_by=test_user,
        review_decision=ReviewDecision.PENDING
    ).order_by('-created_at')

print(f'Direct query results: {direct_results.count()}')
for i, result in enumerate(direct_results[:3], 1):
    print(f'  {i}. {result.image_upload.title} - {result.review_decision}')

print()
print('=== RECOMMENDED ACTIONS ===')
print('If the review page is not showing results:')
print('1. Check if user is logged in with correct permissions')
print('2. Try hard refresh: Ctrl+F5')
print('3. Clear browser cache completely')
print('4. Try incognito/private browsing mode')
print('5. Check browser developer tools for JavaScript errors')
print('6. Verify Django settings for template caching')

# Test URL directly
print()
print('Test URLs:')
print(f'  Review: http://127.0.0.1:8000/image-processing/review/')
print(f'  Login check: http://127.0.0.1:8000/accounts/login/')
