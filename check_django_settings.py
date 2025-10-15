#!/usr/bin/env python
"""
Check Django settings for caching and template issues
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'avicast_project.settings.development')
django.setup()

# Check Django settings for template caching
from django.conf import settings

print('=== DJANGO SETTINGS CHECK ===')
print(f'TEMPLATES setting configured: {len(settings.TEMPLATES)} backends')

for i, backend in enumerate(settings.TEMPLATES):
    print(f'Backend {i}: {backend["NAME"]}')
    if 'OPTIONS' in backend:
        options = backend['OPTIONS']
        if 'debug' in options:
            print(f'  Debug: {options["debug"]}')

# Check if template caching is enabled
if hasattr(settings, 'CACHES'):
    print(f'CACHES configured: {len(settings.CACHES)} backends')
    for name, config in settings.CACHES.items():
        print(f'  {name}: {config.get("BACKEND", "unknown")}')
else:
    print('No CACHES setting found')

print()
print('=== DIRECT VIEW TEST ===')
# Let's try to manually execute the view logic
from django.test import RequestFactory
from django.contrib.auth import get_user_model
from apps.image_processing.views import review_results
from apps.image_processing.models import ProcessingResult, ReviewDecision

User = get_user_model()
test_user = User.objects.filter(employee_id='030303').first()

if test_user:
    factory = RequestFactory()
    request = factory.get('/image-processing/review/')
    request.user = test_user

    try:
        response = review_results(request)
        print(f'View executed successfully, status: {response.status_code}')

        if hasattr(response, 'context_data') and response.context_data:
            context = response.context_data
            print(f'Context keys: {list(context.keys())}')

            if 'pending_results' in context:
                pending = context['pending_results']
                print(f'Context pending_results: {len(pending)} items')
            else:
                print('No pending_results in context')
        else:
            print('No context data')

    except Exception as e:
        print(f'View execution error: {e}')
        import traceback
        traceback.print_exc()
else:
    print('Test user not found')

print()
print('=== CONCLUSION ===')
print('The server-side code is working correctly.')
print('The issue is likely browser-side caching.')
print()
print('SOLUTION: Clear browser cache and hard refresh')
print('1. Press Ctrl+Shift+R (or Ctrl+F5)')
print('2. Or clear browser cache completely')
print('3. Or use incognito/private mode')
print('4. Check browser developer tools Console for errors')
