#!/usr/bin/env python3
"""
Quick Data Verification Script for Platform Avicast
Check if data is being transferred to the database
"""

import os
import sys
from pathlib import Path

import django

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "avicast_project.settings.development")
django.setup()


def check_database_data():
    """Check if data exists in the database"""
    print("🔍 Checking Platform Avicast Database...")
    print("=" * 50)

    try:
        # Import models
        from apps.analytics.models import Chart
        from apps.fauna.models import Species
        from apps.locations.models import CensusObservation, Site, SpeciesObservation
        from apps.users.models import User

        print("\n📊 DATABASE OVERVIEW:")
        print("-" * 30)

        # User data
        user_count = User.objects.count()
        print(f"👥 Users: {user_count}")
        if user_count > 0:
            recent_users = User.objects.order_by("-date_joined")[:3]
            print("   Recent users:")
            for user in recent_users:
                print(
                    f"     - {user.employee_id} ({user.get_full_name()}) - {user.date_joined.strftime('%Y-%m-%d')}"
                )

        # Site data
        site_count = Site.objects.count()
        print(f"\n📍 Sites: {site_count}")
        if site_count > 0:
            recent_sites = Site.objects.order_by("-created_at")[:3]
            print("   Recent sites:")
            for site in recent_sites:
                print(
                    f"     - {site.name} ({site.site_type}) - {site.created_at.strftime('%Y-%m-%d')}"
                )

        # Census data
        census_count = CensusObservation.objects.count()
        print(f"\n📋 Census Observations: {census_count}")
        if census_count > 0:
            recent_census = CensusObservation.objects.order_by("-created_at")[:3]
            print("   Recent census:")
            for census in recent_census:
                print(
                    f"     - {census.site.name} - {census.observation_date} - {census.created_at.strftime('%Y-%m-%d')}"
                )

        # Species data
        species_count = SpeciesObservation.objects.count()
        print(f"\n🦅 Species Observations: {species_count}")
        if species_count > 0:
            recent_species = SpeciesObservation.objects.order_by("-created_at")[:3]
            print("   Recent species observations:")
            for species in recent_species:
                print(
                    f"     - {species.species_name} (Count: {species.count}) - {species.created_at.strftime('%Y-%m-%d')}"
                )

        # Fauna data
        fauna_count = Species.objects.count()
        print(f"\n🐦 Fauna Species: {fauna_count}")

        # Analytics data
        chart_count = Chart.objects.count()
        print(f"\n📈 Charts: {chart_count}")

        print("\n" + "=" * 50)

        if user_count == 0 and site_count == 0 and census_count == 0:
            print("⚠️  No data found in database!")
            print("   This could mean:")
            print("   1. Database is empty (new installation)")
            print("   2. Data import hasn't happened yet")
            print("   3. Database connection issues")
            print("\n   To add test data:")
            print("   1. Create a superuser: python manage.py createsuperuser")
            print("   2. Access admin: http://localhost:8000/admin/")
            print("   3. Add some test sites and census data")
        else:
            print("✅ Database contains data!")
            print("   Your system is working correctly.")

        return True

    except Exception as e:
        print(f"❌ Error checking database: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure Django server is running")
        print("2. Check database connection")
        print("3. Verify migrations are applied")
        return False


def check_recent_activity():
    """Check recent database activity"""
    print("\n🕒 RECENT ACTIVITY (Last 24 hours):")
    print("-" * 40)

    try:
        from datetime import timedelta

        from django.utils import timezone

        from apps.locations.models import CensusObservation, Site

        # Get time 24 hours ago
        yesterday = timezone.now() - timedelta(hours=24)

        # Recent sites
        recent_sites = Site.objects.filter(created_at__gte=yesterday)
        print(f"📍 New sites: {recent_sites.count()}")

        # Recent census
        recent_census = CensusObservation.objects.filter(created_at__gte=yesterday)
        print(f"📋 New census: {recent_census.count()}")

        if recent_sites.count() == 0 and recent_census.count() == 0:
            print("   No recent activity in the last 24 hours")
        else:
            print("   Recent activity detected!")

    except Exception as e:
        print(f"   Error checking recent activity: {e}")


def main():
    """Main function"""
    print("Platform Avicast - Data Verification Tool")
    print("=" * 50)

    # Check if we're in the right directory
    if not Path("manage.py").exists():
        print("❌ Error: Please run this script from the project root directory")
        sys.exit(1)

    # Check database data
    if check_database_data():
        check_recent_activity()

    print("\n" + "=" * 50)
    print("💡 Tips:")
    print("• Run this script anytime to check data status")
    print("• Use 'python manage.py shell' for detailed queries")
    print("• Access admin interface at http://localhost:8000/admin/")
    print("• Check logs in the 'logs' directory")


if __name__ == "__main__":
    main()
