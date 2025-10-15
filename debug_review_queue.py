#!/usr/bin/env python
"""
Debug why recent processed images aren't showing in review queue
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'avicast_project.settings.development')
django.setup()

from apps.image_processing.models import ImageUpload, ProcessingResult, ProcessingStatus, ReviewDecision

print('=== DETAILED WORKFLOW ANALYSIS ===')
print()

# Check the most recently processed image
most_recent = ImageUpload.objects.filter(upload_status=ProcessingStatus.ORGANIZED).order_by('-uploaded_at').first()
print(f'Most recent processed image: {most_recent.title if most_recent else "None"}')
if most_recent:
    print(f'  Status: {most_recent.upload_status}')
    print(f'  Uploaded: {most_recent.uploaded_at}')

    # Check if it has a processing result
    result = ProcessingResult.objects.filter(image_upload=most_recent).first()
    if result:
        print(f'  Has result: Yes')
        print(f'  Result status: {result.review_decision}')
        print(f'  Result created: {result.created_at}')
        print(f'  Detections: {result.total_detections}')
    else:
        print(f'  Has result: No')

print()
print('=== REVIEW QUERY SIMULATION ===')

# Simulate what the review_results view does
if most_recent and result:
    # Check if this result would appear in review queue
    is_pending = result.review_decision == ReviewDecision.PENDING
    print(f'Would appear in review queue: {is_pending}')

    # Check the ordering
    all_pending = ProcessingResult.objects.filter(review_decision=ReviewDecision.PENDING).order_by('-created_at')
    position = 0
    for i, r in enumerate(all_pending, 1):
        if r.id == result.id:
            position = i
            break

    print(f'Position in review queue: #{position} out of {all_pending.count()}')
else:
    print('No recent processed image or result found')

print()
print('=== DIRECT DATABASE CHECK ===')
# Check the actual database state
recent_uploads = ImageUpload.objects.filter(upload_status=ProcessingStatus.ORGANIZED).order_by('-uploaded_at')[:3]
for i, img in enumerate(recent_uploads, 1):
    result = ProcessingResult.objects.filter(image_upload=img).first()
    if result:
        print(f'{i}. {img.title} -> {result.review_decision} ({result.total_detections} birds)')
    else:
        print(f'{i}. {img.title} -> NO RESULT')

print()
print('=== CHECKING FOR CACHE ISSUES ===')
# Check if there are any caching issues by looking at template cache or session data
print('If the review page is not showing updated results, try:')
print('1. Hard refresh: Ctrl+F5')
print('2. Clear browser cache')
print('3. Try incognito/private mode')
print('4. Check if Django template caching is enabled')

print()
print('=== REVIEW VIEW DEBUG ===')
# Check what the review_results view actually returns
from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()
client = Client()
admin_user = User.objects.filter(role='ADMIN').first() or User.objects.filter(employee_id='030303').first()

if admin_user:
    client.force_login(admin_user)

    # Get the review page
    response = client.get('/image-processing/review/')

    if response.status_code == 200:
        # Parse the context to see what results are being returned
        context = response.context_data if hasattr(response, 'context_data') else {}

        if 'pending_results' in context:
            pending_results = context['pending_results']
            print(f'Review page context shows {len(pending_results)} pending results')

            # Show first few results
            for i, result in enumerate(pending_results[:3], 1):
                print(f'  {i}. {result.image_upload.title} - {result.review_decision}')
        else:
            print('No pending_results in context')
    else:
        print(f'Review page returned status {response.status_code}')
else:
    print('No admin user found for testing')
