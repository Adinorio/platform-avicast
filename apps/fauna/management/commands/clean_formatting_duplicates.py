from django.core.management.base import BaseCommand
from django.db.models import Q
from apps.fauna.models import Species
from apps.fauna.services import SpeciesMatcher

class Command(BaseCommand):
    help = 'Clean up formatting duplicates in species database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write("Cleaning Formatting Duplicates")
        self.stdout.write("=" * 40)
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be made"))
            self.stdout.write("")
        
        matcher = SpeciesMatcher()
        all_species = Species.objects.filter(is_archived=False)
        duplicates_found = []
        
        # Find formatting duplicates
        for i, species1 in enumerate(all_species):
            for species2 in all_species[i+1:]:
                if matcher.is_likely_same_species(species1.name, species2.name):
                    duplicates_found.append((species1, species2))
        
        if not duplicates_found:
            self.stdout.write(self.style.SUCCESS("No formatting duplicates found!"))
            return
        
        self.stdout.write(f"Found {len(duplicates_found)} formatting duplicate pairs:")
        self.stdout.write("")
        
        cleaned_count = 0
        for species1, species2 in duplicates_found:
            # Determine which one to keep (prefer the one with proper formatting)
            keep_species, remove_species = self._determine_keep_remove(species1, species2)
            
            self.stdout.write(f"Duplicate pair:")
            self.stdout.write(f"  Keep: {keep_species.name} ({keep_species.scientific_name})")
            self.stdout.write(f"  Remove: {remove_species.name} ({remove_species.scientific_name})")
            
            if not dry_run:
                # Archive the duplicate instead of deleting
                remove_species.is_archived = True
                remove_species.save()
                self.stdout.write(f"  -> Archived: {remove_species.name}")
                cleaned_count += 1
            else:
                self.stdout.write(f"  -> Would archive: {remove_species.name}")
            
            self.stdout.write("")
        
        if dry_run:
            self.stdout.write(self.style.WARNING(f"Would clean up {len(duplicates_found)} duplicates"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Successfully cleaned up {cleaned_count} duplicates"))
    
    def _determine_keep_remove(self, species1, species2):
        """Determine which species to keep and which to remove"""
        # Prefer species with:
        # 1. Proper capitalization (not all caps)
        # 2. Shorter, cleaner names
        # 3. Proper scientific name format
        
        name1 = species1.name
        name2 = species2.name
        sci1 = species1.scientific_name
        sci2 = species2.scientific_name
        
        # Check if one is all caps (usually imported data)
        if name1.isupper() and not name2.isupper():
            return species2, species1
        elif name2.isupper() and not name1.isupper():
            return species1, species2
        
        # Check if one has cleaner scientific name
        if len(sci1) < len(sci2) and '.' in sci1:
            return species1, species2
        elif len(sci2) < len(sci1) and '.' in sci2:
            return species2, species1
        
        # Check if one has cleaner common name
        if len(name1) < len(name2):
            return species1, species2
        else:
            return species2, species1
