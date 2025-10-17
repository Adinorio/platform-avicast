from django.core.management.base import BaseCommand
from apps.fauna.models import Species, BirdFamily


class Command(BaseCommand):
    help = 'Link existing species to their appropriate BirdFamily objects based on species names'

    def handle(self, *args, **options):
        self.stdout.write("Linking species to families...")
        
        # Get all families
        families = BirdFamily.objects.all()
        family_map = {family.name: family for family in families}
        
        # Define family patterns for automatic detection
        family_patterns = {
            'HERONS AND EGRETS': ['HERON', 'EGRET', 'BITTERN', 'NIGHT HERON', 'POND HERON', 'REEF EGRET'],
            'SHOREBIRDS-WADERS': ['SANDPIPER', 'PLOVER', 'GODWIT', 'CURLEW', 'WHIMBREL', 'REDSHANK', 'GREENSHANK', 'TATTLER', 'TURNSTONE', 'KNOT', 'STINT', 'DOWITCHER', 'PHALAROPE', 'STILT', 'SNIPE', 'AVOCET'],
            'RAILS, GALLINULES & COOTS': ['RAIL', 'CRAKE', 'GALLINULE', 'COOT', 'MOORHEN', 'WATER HEN', 'WATERCOCK'],
            'GULLS, TERNS & SKIMMERRS': ['GULL', 'TERN', 'SKIMMER'],
            'GEESE & DUCKS': ['GOOSE', 'DUCK', 'TEAL', 'WIGEON', 'SHOVELER', 'GADWALL'],
            'IBISES & SPOONBILLS': ['IBIS', 'SPOONBILL'],
            'ADDITIONAL SPECIES': ['KITE', 'KINGFISHER', 'SWALLOW', 'OSPREY', 'DOVE', 'PIGEON', 'OWL', 'EAGLE', 'HAWK', 'FALCON', 'UNIDENTIFIED']
        }
        
        linked_count = 0
        total_species = Species.objects.filter(family__isnull=True).count()
        
        for species in Species.objects.filter(family__isnull=True):
            species_upper = species.name.upper()
            family_found = False
            
            # Try to match species to family based on patterns
            for family_name, patterns in family_patterns.items():
                if family_name in family_map and any(pattern in species_upper for pattern in patterns):
                    species.family = family_map[family_name]
                    species.save()
                    linked_count += 1
                    family_found = True
                    self.stdout.write(f"  Linked '{species.name}' to '{family_name}'")
                    break
            
            # If no pattern match, assign to ADDITIONAL SPECIES
            if not family_found and 'ADDITIONAL SPECIES' in family_map:
                species.family = family_map['ADDITIONAL SPECIES']
                species.save()
                linked_count += 1
                self.stdout.write(f"  Linked '{species.name}' to 'ADDITIONAL SPECIES' (default)")
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully linked {linked_count} out of {total_species} species to families!"
            )
        )
        
        # Show summary
        remaining_unlinked = Species.objects.filter(family__isnull=True).count()
        if remaining_unlinked > 0:
            self.stdout.write(
                self.style.WARNING(
                    f"Warning: {remaining_unlinked} species still have no family assigned"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("All species now have family assignments!")
            )
