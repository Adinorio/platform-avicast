#!/usr/bin/env python
"""
Check processing results to diagnose species detection issues
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'avicast_project.settings.development')
django.setup()

from apps.image_processing.models import ProcessingResult

print("=== PROCESSING RESULTS ANALYSIS ===")

# Check all processing results
all_results = ProcessingResult.objects.all()
print(f"\nTotal Processing Results: {all_results.count()}")

# Check by review decision
approved = ProcessingResult.objects.filter(review_decision='APPROVED')
rejected = ProcessingResult.objects.filter(review_decision='REJECTED')
pending = ProcessingResult.objects.filter(review_decision='PENDING')

print("\nBy Review Decision:")
print(f"  Approved: {approved.count()}")
print(f"  Rejected: {rejected.count()}")
print(f"  Pending: {pending.count()}")

# Check recent approved results
print("\nRecent Approved Results (last 10):")
recent_approved = approved.order_by('-created_at')[:10]
for result in recent_approved:
    status = "ALLOCATED" if result.image_upload.upload_status == 'ENGAGED' else "NOT ALLOCATED"
    print(f"  {result.image_upload.title}:")
    print(f"    Species: '{result.detected_species}'")
    print(f"    Confidence: {result.confidence_score}")
    print(f"    Count: {result.final_count}")
    print(f"    Status: {status}")
    print(f"    AI Model: {result.ai_model_used}")
    print()

# Check for results with blank/unknown species
blank_species = ProcessingResult.objects.filter(detected_species='UNKNOWN')
print(f"\nResults with UNKNOWN species: {blank_species.count()}")

unknown_species = ProcessingResult.objects.filter(detected_species='')
print(f"Results with blank species: {unknown_species.count()}")

# Check confidence scores
high_confidence = ProcessingResult.objects.filter(confidence_score__gte=0.8)
low_confidence = ProcessingResult.objects.filter(confidence_score__lt=0.5)

print("\nConfidence Analysis:")
print(f"  High confidence (≥0.8): {high_confidence.count()}")
print(f"  Low confidence (<0.5): {low_confidence.count()}")

# Check AI models used
print("\nAI Models Used:")
models_used = ProcessingResult.objects.values_list('ai_model_used', flat=True).distinct()
for model in models_used:
    count = ProcessingResult.objects.filter(ai_model_used=model).count()
    print(f"  {model}: {count} results")

print("\n=== ANALYSIS COMPLETE ===")
