from django.core.management.base import BaseCommand
from django.db.models import Q
from apps.fauna.models import Species
from apps.locations.models import CensusObservation

class Command(BaseCommand):
    help = 'Merge duplicate species entries'

    def handle(self, *args, **options):
        self.stdout.write("Merging Duplicate Species Entries")
        self.stdout.write("=" * 40)
        
        # Find the duplicate Chinese Egret entries
        chinese_egrets = Species.objects.filter(
            Q(name__icontains='chinese') & Q(name__icontains='egret')
        )
        
        self.stdout.write(f"Found {chinese_egrets.count()} Chinese Egret entries:")
        for species in chinese_egrets:
            self.stdout.write(f"  - {species.name} | {species.scientific_name} | ID: {species.id}")
        
        if chinese_egrets.count() >= 2:
            # Keep the properly formatted one (Chinese Egret with Egretta eulophotes)
            proper_species = chinese_egrets.filter(
                name='Chinese Egret',
                scientific_name='Egretta eulophotes'
            ).first()
            
            # Find the duplicate to merge
            duplicate_species = chinese_egrets.exclude(
                name='Chinese Egret'
            ).first()
            
            if proper_species and duplicate_species:
                self.stdout.write(f"\nMerging:")
                self.stdout.write(f"  KEEP: {proper_species.name} | {proper_species.scientific_name}")
                self.stdout.write(f"  MERGE: {duplicate_species.name} | {duplicate_species.scientific_name}")
                
                # Check for census observations that reference the duplicate
                duplicate_observations = CensusObservation.objects.filter(
                    species_name=duplicate_species.name
                )
                
                self.stdout.write(f"\nFound {duplicate_observations.count()} census observations to update")
                
                if duplicate_observations.count() > 0:
                    self.stdout.write("Updating census observations...")
                    duplicate_observations.update(species_name=proper_species.name)
                    self.stdout.write(f"Updated {duplicate_observations.count()} census observations")
                
                # Delete the duplicate species
                duplicate_name = duplicate_species.name
                duplicate_species.delete()
                self.stdout.write(f"Deleted duplicate species: {duplicate_name}")
                
                self.stdout.write(f"\nMerge complete! Now there's only one Chinese Egret entry:")
                remaining = Species.objects.filter(
                    Q(name__icontains='chinese') & Q(name__icontains='egret')
                )
                for species in remaining:
                    self.stdout.write(f"  - {species.name} | {species.scientific_name}")
            else:
                self.stdout.write("Could not find proper species to keep")
        else:
            self.stdout.write("No duplicates found or already merged")
        
        self.stdout.write(self.style.SUCCESS("Merge operation complete!"))
