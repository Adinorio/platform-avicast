#!/usr/bin/env python
"""
Debug script to check allocation status
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'avicast_project.settings.development')
django.setup()

from apps.image_processing.models import ProcessingResult
from apps.locations.models import CensusObservation

# Check what detected_species values exist for approved results
results = ProcessingResult.objects.filter(review_decision='APPROVED')
print('Approved results and their detected_species:')
for result in results[:10]:
    print(f'  {result.image_upload.title}: detected_species="{result.detected_species}", final_count={result.final_count}')

# Check if any CensusObservation records exist for these results
print(f'\nTotal CensusObservation records: {CensusObservation.objects.count()}')

# Check if any 2025 census observations exist
obs_2025 = CensusObservation.objects.filter(census__census_date__year=2025)
print(f'2025 CensusObservation records: {obs_2025.count()}')

# Show a few recent census observations
print('\nRecent CensusObservation records:')
for obs in CensusObservation.objects.order_by('-created_at')[:5]:
    census_date = obs.census.census_date if obs.census else "No Census"
    print(f'  {obs.species_name}: {obs.count} birds on {census_date}')
