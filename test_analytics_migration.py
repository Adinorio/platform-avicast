#!/usr/bin/env python3
"""
Test script to verify that the new analytics system migration is working correctly.
This script tests that the new analytics models are available and functional.
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'avicast_project.settings.development')
django.setup()

def test_analytics_migration():
    """Test that the new analytics system is working"""
    print("Testing Analytics Migration...")
    print("=" * 50)

    try:
        # Test imports
        from apps.analytics_new.models import BirdSpeciesAnalytics, SiteAnalytics, CensusRecord, PopulationTrend
        print("Successfully imported new analytics models")

        # Test model instantiation
        species = BirdSpeciesAnalytics()
        site = SiteAnalytics()
        census = CensusRecord()
        trend = PopulationTrend()
        print("Successfully instantiated analytics models")

        # Test field access
        species.species = "CHINESE_EGRET"
        species.total_count = 100
        print("Successfully set model fields")

        # Test URL resolution
        from django.urls import reverse
        try:
            dashboard_url = reverse('analytics_new:dashboard')
            species_url = reverse('analytics_new:species_analytics')
            print(f"Successfully resolved URLs: {dashboard_url}, {species_url}")
        except Exception as e:
            print(f"URL resolution failed: {e}")
            return False

        print("\nAnalytics migration test PASSED!")
        print("The new analytics system is working correctly.")
        return True

    except ImportError as e:
        print(f"Import error: {e}")
        return False
    except Exception as e:
        print(f"Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_analytics_migration()
    sys.exit(0 if success else 1)
