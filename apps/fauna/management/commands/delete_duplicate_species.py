from django.core.management.base import BaseCommand
from django.db.models import Q
from apps.fauna.models import Species

class Command(BaseCommand):
    help = 'Delete duplicate species entries'

    def handle(self, *args, **options):
        self.stdout.write("Deleting Duplicate Species Entries")
        self.stdout.write("=" * 40)
        
        # Find the duplicate Chinese Egret entry
        duplicate_species = Species.objects.filter(
            name='CHINESE (SWINHOES) EGRET E. EULOPHOTES'
        ).first()
        
        if duplicate_species:
            self.stdout.write(f"Found duplicate species:")
            self.stdout.write(f"  - {duplicate_species.name}")
            self.stdout.write(f"  - {duplicate_species.scientific_name}")
            self.stdout.write(f"  - ID: {duplicate_species.id}")
            
            # Delete it
            duplicate_species.delete()
            self.stdout.write("Deleted duplicate species entry")
            
            # Verify deletion
            remaining = Species.objects.filter(
                Q(name__icontains='chinese') & Q(name__icontains='egret')
            )
            
            self.stdout.write(f"\nRemaining Chinese Egret entries: {remaining.count()}")
            for species in remaining:
                self.stdout.write(f"  - {species.name} | {species.scientific_name}")
        else:
            self.stdout.write("No duplicate found")
        
        self.stdout.write(self.style.SUCCESS("Operation complete!"))
