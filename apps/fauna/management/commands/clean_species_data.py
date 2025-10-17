from django.core.management.base import BaseCommand
from django.db import transaction
from apps.fauna.models import Species
from apps.locations.models import CensusObservation


class Command(BaseCommand):
    help = 'Clean species data with various options'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset-families',
            action='store_true',
            help='Reset all family links to None',
        )
        parser.add_argument(
            '--clear-unused',
            action='store_true',
            help='Clear species that have no census observations',
        )
        parser.add_argument(
            '--clear-all',
            action='store_true',
            help='Clear ALL species (WARNING: This will delete everything)',
        )
        parser.add_argument(
            '--clear-observations',
            action='store_true',
            help='Clear all census observations (keeps species)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Skip confirmation prompts',
        )

    def handle(self, *args, **options):
        if options['reset_families']:
            self.reset_families(options['force'])
        elif options['clear_unused']:
            self.clear_unused_species(options['force'])
        elif options['clear_all']:
            self.clear_all_species(options['force'])
        elif options['clear_observations']:
            self.clear_observations(options['force'])
        else:
            self.show_options()

    def show_options(self):
        self.stdout.write("Species Data Cleaning Options:")
        self.stdout.write("")
        self.stdout.write("1. Reset family links:")
        self.stdout.write("   python manage.py clean_species_data --reset-families")
        self.stdout.write("")
        self.stdout.write("2. Clear unused species (no census data):")
        self.stdout.write("   python manage.py clean_species_data --clear-unused")
        self.stdout.write("")
        self.stdout.write("3. Clear all census observations:")
        self.stdout.write("   python manage.py clean_species_data --clear-observations")
        self.stdout.write("")
        self.stdout.write("4. Clear ALL species (WARNING - Nuclear option):")
        self.stdout.write("   python manage.py clean_species_data --clear-all --force")
        self.stdout.write("")
        self.stdout.write("Current stats:")
        species_count = Species.objects.count()
        obs_count = CensusObservation.objects.count()
        species_with_families = Species.objects.exclude(family__isnull=True).count()
        species_with_census = Species.objects.filter(census_observations__isnull=False).distinct().count()
        
        self.stdout.write(f"  Total species: {species_count}")
        self.stdout.write(f"  Species with families: {species_with_families}")
        self.stdout.write(f"  Species with census data: {species_with_census}")
        self.stdout.write(f"  Total observations: {obs_count}")

    def reset_families(self, force):
        count = Species.objects.count()
        if not force:
            confirm = input(f"Reset family links for {count} species? (y/N): ")
            if confirm.lower() != 'y':
                self.stdout.write("Cancelled.")
                return
        
        Species.objects.all().update(family=None)
        self.stdout.write(self.style.SUCCESS(f"Reset family links for {count} species."))

    def clear_unused_species(self, force):
        species_with_census = Species.objects.filter(census_observations__isnull=False).distinct()
        species_without_census = Species.objects.exclude(id__in=species_with_census)
        count = species_without_census.count()
        
        if count == 0:
            self.stdout.write(self.style.WARNING("No unused species found."))
            return
            
        if not force:
            confirm = input(f"Delete {count} species with no census data? (y/N): ")
            if confirm.lower() != 'y':
                self.stdout.write("Cancelled.")
                return
        
        with transaction.atomic():
            species_without_census.delete()
        
        self.stdout.write(self.style.SUCCESS(f"Deleted {count} unused species."))

    def clear_all_species(self, force):
        species_count = Species.objects.count()
        obs_count = CensusObservation.objects.count()
        
        if not force:
            confirm = input(f"Delete ALL {species_count} species and {obs_count} observations? (y/N): ")
            if confirm.lower() != 'y':
                self.stdout.write("Cancelled.")
                return
        
        with transaction.atomic():
            CensusObservation.objects.all().delete()
            Species.objects.all().delete()
        
        self.stdout.write(self.style.SUCCESS(f"Deleted ALL {species_count} species and {obs_count} observations."))

    def clear_observations(self, force):
        obs_count = CensusObservation.objects.count()
        
        if not force:
            confirm = input(f"Delete {obs_count} census observations? (y/N): ")
            if confirm.lower() != 'y':
                self.stdout.write("Cancelled.")
                return
        
        with transaction.atomic():
            CensusObservation.objects.all().delete()
        
        self.stdout.write(self.style.SUCCESS(f"Deleted {obs_count} census observations."))
