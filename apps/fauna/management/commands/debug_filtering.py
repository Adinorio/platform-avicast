from django.core.management.base import BaseCommand
from django.db.models import Q
from apps.fauna.models import Species

class Command(BaseCommand):
    help = 'Debug species filtering functionality'

    def handle(self, *args, **options):
        self.stdout.write("Testing Species Filtering Functionality")
        self.stdout.write("=" * 50)
        
        # Test 1: Get all species
        all_species = Species.objects.filter(is_archived=False)
        self.stdout.write(f"Total active species: {all_species.count()}")
        
        # Test 2: Get unique families
        families = sorted(
            all_species.exclude(family='').values_list('family', flat=True).distinct()
        )
        self.stdout.write(f"\nAvailable families ({len(families)}):")
        for i, family in enumerate(families, 1):
            count = all_species.filter(family=family).count()
            self.stdout.write(f"  {i}. {family} ({count} species)")
        
        # Test 3: Test family filtering
        self.stdout.write(f"\nTesting family filter: 'HERONS AND EGRETS'")
        heron_species = all_species.filter(family__iexact='HERONS AND EGRETS')
        self.stdout.write(f"   Found: {heron_species.count()} species")
        
        if heron_species.exists():
            self.stdout.write("   Sample species:")
            for species in heron_species[:5]:
                self.stdout.write(f"     - {species.name} ({species.family})")
            if heron_species.count() > 5:
                self.stdout.write(f"     ... and {heron_species.count() - 5} more")
        
        # Test 4: Test exact family match
        self.stdout.write(f"\nTesting exact family match:")
        exact_match = all_species.filter(family='HERONS AND EGRETS')
        self.stdout.write(f"   Exact match: {exact_match.count()} species")
        
        # Test 5: Check for case sensitivity
        self.stdout.write(f"\nTesting case sensitivity:")
        case_variations = [
            'HERONS AND EGRETS',
            'herons and egrets', 
            'Herons And Egrets',
            'herons AND egrets'
        ]
        
        for variation in case_variations:
            count = all_species.filter(family__iexact=variation).count()
            self.stdout.write(f"   '{variation}': {count} species")
        
        # Test 6: Check family field values
        self.stdout.write(f"\nChecking family field values:")
        sample_species = all_species[:10]
        for species in sample_species:
            self.stdout.write(f"   {species.name}: family='{species.family}'")
        
        # Test 7: Debug the filtering query
        self.stdout.write(f"\nDebugging the filtering query:")
        family_filter = 'HERONS AND EGRETS'
        queryset = all_species.filter(family__iexact=family_filter)
        self.stdout.write(f"   Query: {queryset.query}")
        self.stdout.write(f"   Result count: {queryset.count()}")
        
        # Test 8: Check if there are any species with similar family names
        self.stdout.write(f"\nChecking for similar family names:")
        similar_families = all_species.filter(
            family__icontains='HERON'
        ).values_list('family', flat=True).distinct()
        self.stdout.write(f"   Families containing 'HERON': {list(similar_families)}")
        
        similar_families = all_species.filter(
            family__icontains='EGRET'
        ).values_list('family', flat=True).distinct()
        self.stdout.write(f"   Families containing 'EGRET': {list(similar_families)}")
        
        # Test the exact view filtering logic
        self.stdout.write(f"\nTesting View Filtering Logic:")
        
        def get_queryset(family_filter='', search_query='', iucn_filter=''):
            queryset = Species.objects.filter(is_archived=False)

            # Apply search filter if provided
            if search_query:
                queryset = queryset.filter(
                    Q(name__icontains=search_query) |
                    Q(scientific_name__icontains=search_query) |
                    Q(family__icontains=search_query) |
                    Q(description__icontains=search_query)
                )

            # Apply family filter if provided
            if family_filter:
                queryset = queryset.filter(family__iexact=family_filter)

            # Apply IUCN status filter if provided
            if iucn_filter:
                queryset = queryset.filter(iucn_status=iucn_filter)

            return queryset.order_by("name")
        
        # Test family filter
        self.stdout.write(f"\nTesting family filter: 'HERONS AND EGRETS'")
        queryset = get_queryset(family_filter='HERONS AND EGRETS')
        self.stdout.write(f"   Filtered species: {queryset.count()}")
        
        if queryset.exists():
            self.stdout.write("   First 5 species:")
            for species in queryset[:5]:
                self.stdout.write(f"     - {species.name} ({species.family})")
        
        # Test search filter
        self.stdout.write(f"\nTesting search filter: 'egret'")
        queryset = get_queryset(search_query='egret')
        self.stdout.write(f"   Filtered species: {queryset.count()}")
        
        if queryset.exists():
            self.stdout.write("   First 5 species:")
            for species in queryset[:5]:
                self.stdout.write(f"     - {species.name} ({species.family})")
        
        # Test combined filters
        self.stdout.write(f"\nTesting combined filters: family='HERONS AND EGRETS' + search='egret'")
        queryset = get_queryset(family_filter='HERONS AND EGRETS', search_query='egret')
        self.stdout.write(f"   Filtered species: {queryset.count()}")
        
        if queryset.exists():
            self.stdout.write("   All matching species:")
            for species in queryset:
                self.stdout.write(f"     - {species.name} ({species.family})")
        
        self.stdout.write(self.style.SUCCESS("Debugging complete!"))
