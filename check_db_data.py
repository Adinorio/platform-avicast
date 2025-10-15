import sqlite3
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'avicast_project.settings.development')
django.setup()

from apps.image_processing.models import ImageUpload, ProcessingResult

print("Checking ImageUpload records:")
uploads = ImageUpload.objects.all()
print(f"Total uploads: {uploads.count()}")

for upload in uploads:
    print(f"  - {upload.title}: {upload.get_upload_status_display()} (uploaded: {upload.uploaded_at})")

print("\nChecking ProcessingResult records:")
results = ProcessingResult.objects.all()
print(f"Total results: {results.count()}")

for result in results:
    print(f"  - {result.image_upload.title}: {result.get_detected_species_display()} (confidence: {result.confidence_score}, review: {result.get_review_decision_display()})")
    print(f"    Uploaded by: {result.image_upload.uploaded_by.employee_id} ({result.image_upload.uploaded_by.email})")

# Check if there are any uploads that should have results but don't
print("\nChecking for uploads without results:")
uploads_without_results = ImageUpload.objects.filter(
    upload_status__in=['ORGANIZED', 'REFLECTED', 'ENGAGED']
).exclude(
    processing_result__isnull=False
)

print(f"Uploads with status but no results: {uploads_without_results.count()}")

for upload in uploads_without_results:
    print(f"  - {upload.title}: {upload.get_upload_status_display()} (no processing result)")
