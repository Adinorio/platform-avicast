#!/usr/bin/env python
"""
Script to check allocation status and census records
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'avicast_project.settings.development')
django.setup()

from apps.locations.models import Census, CensusMonth, CensusYear
from apps.image_processing.models import ProcessingResult
from apps.locations.models import Site

def check_allocation_status():
    """Check current allocation status and census records"""

    print("=== ALLOCATION STATUS CHECK ===")

    # Check all sites
    sites = Site.objects.filter(status="active")
    print(f"\nActive Sites: {sites.count()}")
    for site in sites:
        print(f"  - {site.name} (ID: {site.id})")

    # Check all census years
    census_years = CensusYear.objects.all()
    print(f"\nCensus Years: {census_years.count()}")
    for year in census_years:
        print(f"  - {year.year} at {year.site.name}")

    # Check all census months
    census_months = CensusMonth.objects.all()
    print(f"\nCensus Months: {census_months.count()}")
    for month in census_months:
        print(f"  - {month.get_month_display()} {month.year.year} at {month.year.site.name}")

    # Check all census records
    census_records = Census.objects.all()
    print(f"\nCensus Records: {census_records.count()}")
    for record in census_records.order_by('-census_date')[:10]:  # Show latest 10
        print(f"  - {record.census_date}: {record.total_birds} birds, {record.total_species} species (ID: {record.id})")

    # Check processing results
    processing_results = ProcessingResult.objects.filter(review_decision="APPROVED")
    print(f"\nApproved Processing Results: {processing_results.count()}")
    for result in processing_results.order_by('-created_at')[:10]:  # Show latest 10
        status_text = "ALLOCATED" if result.image_upload.upload_status == 'ENGAGED' else "NOT ALLOCATED"
        upload_status = result.image_upload.upload_status
        print(f"  - {result.image_upload.title}: {result.final_count} birds - {status_text} (status: {upload_status})")

    # Check for recent allocations (based on image upload status)
    from apps.image_processing.models import ImageUpload
    allocated_images = ImageUpload.objects.filter(upload_status='ENGAGED')
    print(f"\nImages with ENGAGED status (allocated): {allocated_images.count()}")

    # Check CensusObservation records
    from apps.locations.models import CensusObservation
    observations = CensusObservation.objects.all()
    print(f"\nCensusObservation Records: {observations.count()}")

    # Show observations for 2025 dates (recent allocations)
    recent_observations = observations.filter(census__census_date__year=2025).order_by('-created_at')
    print(f"\n2025 CensusObservation Records: {recent_observations.count()}")
    for obs in recent_observations:
        census_date = obs.census.census_date if obs.census else "No Census"
        site_name = obs.census.month.year.site.name if obs.census and obs.census.month and obs.census.month.year else "No Site"
        print(f"  - {obs.species_name}: {obs.count} birds on {census_date} at {site_name}")

    # Show a few other recent observations for context
    other_observations = observations.exclude(census__census_date__year=2025).order_by('-created_at')[:5]
    if other_observations.count() > 0:
        print(f"\nOther Recent CensusObservation Records: {other_observations.count()}")
        for obs in other_observations:
            census_date = obs.census.census_date if obs.census else "No Census"
            site_name = obs.census.month.year.site.name if obs.census and obs.census.month and obs.census.month.year else "No Site"
            print(f"  - {obs.species_name}: {obs.count} birds on {census_date} at {site_name}")

    # Check allocation history
    try:
        from apps.locations.models import AllocationHistory
        allocation_history = AllocationHistory.objects.all()
        print(f"\nAllocation History Records: {allocation_history.count()}")
        for record in allocation_history.order_by('-allocated_at')[:5]:  # Show latest 5
            print(f"  - {record.allocated_at.strftime('%Y-%m-%d %H:%M')}: {record.processing_result.image_upload.title} -> {record.bird_count} birds")
    except ImportError:
        print("\nAllocationHistory model not available (migration may be pending)")

    print("\n=== CHECK COMPLETE ===")

if __name__ == "__main__":
    check_allocation_status()
