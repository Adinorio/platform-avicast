#!/usr/bin/env python3
"""
Management command to sync analytics data from existing fauna, locations, and census data.

This command populates the analytics models (SpeciesAnalytics, SiteAnalytics, CensusAnalytics)
from the existing operational data in the fauna and locations apps.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.fauna.models import Species
from apps.locations.models import Site, CensusObservation, SpeciesObservation


class Command(BaseCommand):
    help = 'Sync analytics data from existing species, sites, and census data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update all analytics records even if they exist',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be synced without making changes',
        )

    def handle(self, *args, **options):
        force = options['force']
        dry_run = options['dry_run']

        self.stdout.write(
            self.style.SUCCESS(
                f"{'DRY RUN: ' if dry_run else ''}Syncing analytics data..."
            )
        )

        with transaction.atomic():
            # Sync species analytics
            self.sync_species_analytics(force, dry_run)

            # Sync site analytics
            self.sync_site_analytics(force, dry_run)

            # Sync census analytics
            self.sync_census_analytics(force, dry_run)

        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS("✅ Analytics data sync completed!")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("✅ Dry run completed - no changes made")
            )

    def sync_species_analytics(self, force, dry_run):
        """Sync SpeciesAnalytics from fauna.Species"""
        from apps.analytics_new.models import SpeciesAnalytics

        # Get target species (egrets and herons for CENRO)
        target_species = Species.objects.filter(
            name__icontains='egret'
        ) | Species.objects.filter(
            name__icontains='heron'
        )

        created = 0
        updated = 0

        for species in target_species:
            analytics, created_flag = SpeciesAnalytics.objects.get_or_create(
                species=species,
                defaults={'is_active': True}
            )

            if created_flag:
                created += 1
                if not dry_run:
                    analytics.update_from_census_data()
            elif force:
                updated += 1
                if not dry_run:
                    analytics.update_from_census_data()

        self.stdout.write(
            f"  Species Analytics: {created} created, {updated} updated"
        )

    def sync_site_analytics(self, force, dry_run):
        """Sync SiteAnalytics from locations.Site"""
        from apps.analytics_new.models import SiteAnalytics

        # Get all active sites
        sites = Site.objects.filter(status='active')

        created = 0
        updated = 0

        for site in sites:
            analytics, created_flag = SiteAnalytics.objects.get_or_create(
                site=site,
                defaults={'is_active': True}
            )

            if created_flag:
                created += 1
                if not dry_run:
                    analytics.update_from_census_data()
            elif force:
                updated += 1
                if not dry_run:
                    analytics.update_from_census_data()

        self.stdout.write(
            f"  Site Analytics: {created} created, {updated} updated"
        )

    def sync_census_analytics(self, force, dry_run):
        """Sync CensusAnalytics from locations.CensusObservation"""
        from apps.analytics_new.models import CensusAnalytics

        # Get census observations that don't have analytics yet
        census_observations = CensusObservation.objects.filter(
            analytics__isnull=True
        )[:100]  # Process in batches

        created = 0

        for census in census_observations:
            if not dry_run:
                analytics = CensusAnalytics.objects.create(
                    census_observation=census,
                    total_birds=0,  # Will be updated by update_from_species_observations
                    species_richness=0,
                    verification_status='PENDING'
                )
                analytics.update_from_species_observations()
            created += 1

        self.stdout.write(
            f"  Census Analytics: {created} created"
        )
