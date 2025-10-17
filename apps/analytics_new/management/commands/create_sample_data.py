from django.core.management.base import BaseCommand
from apps.locations.models import Site, CensusYear, CensusMonth, Census, CensusObservation
from apps.fauna.models import Species
from apps.users.models import User
from datetime import date
from django.db.models import Sum

class Command(BaseCommand):
    help = 'Create sample data for testing report generation'

    def handle(self, *args, **options):
        self.stdout.write("Creating sample data for report generation...")
        
        # Use existing user
        user = User.objects.first()
        if user:
            self.stdout.write(self.style.SUCCESS(f"Using existing user: {user.employee_id} - {user.first_name} {user.last_name}"))
        else:
            self.stdout.write(self.style.ERROR("No users found in database"))
            return
        
        # Create sample sites
        sites_data = [
            {'name': 'Main Observation Point', 'description': 'Primary bird watching location', 'site_type': 'grassland', 'coordinates': '14.5995, 120.9842'},
            {'name': 'Wetland Reserve', 'description': 'Protected wetland area', 'site_type': 'wetland', 'coordinates': '14.5895, 120.9742'},
            {'name': 'Coastal Site', 'description': 'Coastal bird observation site', 'site_type': 'coastal', 'coordinates': '14.6095, 120.9942'},
        ]

        sites = []
        for site_data in sites_data:
            site, created = Site.objects.get_or_create(name=site_data['name'], defaults=site_data)
            sites.append(site)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created site: {site.name}"))

        # Create sample species
        species_data = [
            {'name': 'Great Egret', 'scientific_name': 'Ardea alba', 'iucn_status': 'LC'},
            {'name': 'Little Egret', 'scientific_name': 'Egretta garzetta', 'iucn_status': 'LC'},
            {'name': 'Black-crowned Night Heron', 'scientific_name': 'Nycticorax nycticorax', 'iucn_status': 'LC'},
            {'name': 'Purple Heron', 'scientific_name': 'Ardea purpurea', 'iucn_status': 'LC'},
            {'name': 'Grey Heron', 'scientific_name': 'Ardea cinerea', 'iucn_status': 'LC'},
        ]

        species = []
        for species_info in species_data:
            species_obj, created = Species.objects.get_or_create(
                name=species_info['name'], 
                defaults=species_info
            )
            species.append(species_obj)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created species: {species_obj.name}"))

        # Create census years and months for each site
        census_count = 0
        for i, site in enumerate(sites):
            # Create census year for this site
            year, created = CensusYear.objects.get_or_create(site=site, year=2024)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created census year: {site.name} - {year.year}"))
            
            # Create census month for this year
            month, created = CensusMonth.objects.get_or_create(
                year=year,
                month=1
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created census month: January {month.year.year}"))

            # Create census record
            census, created = Census.objects.get_or_create(
                month=month,
                defaults={
                    'census_date': date(2024, 1, 15 + i),
                    'lead_observer': user,
                    'weather_conditions': 'Clear',
                    'notes': f'Sample census at {site.name}'
                }
            )
            if created:
                census_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created census: {site.name} - {census.census_date}"))
                
                # Add observations for this census
                for j, species_obj in enumerate(species):
                    count = (i + 1) * (j + 1) * 5  # Sample counts
                    observation, obs_created = CensusObservation.objects.get_or_create(
                        census=census,
                        species=species_obj,
                        defaults={'count': count}
                    )
                    if obs_created:
                        self.stdout.write(f"  Added observation: {species_obj.name} - {count} individuals")

        self.stdout.write(self.style.SUCCESS(f"\n=== Summary ==="))
        self.stdout.write(self.style.SUCCESS(f"Created {len(sites)} sites"))
        self.stdout.write(self.style.SUCCESS(f"Created {len(species)} species"))
        self.stdout.write(self.style.SUCCESS(f"Created {census_count} census records"))
        
        total_observations = CensusObservation.objects.count()
        total_birds = CensusObservation.objects.aggregate(total=Sum('count'))['total'] or 0
        self.stdout.write(self.style.SUCCESS(f"Created {total_observations} observations"))
        self.stdout.write(self.style.SUCCESS(f"Total birds observed: {total_birds}"))
        
        self.stdout.write(self.style.SUCCESS(f"\nReport generation should now work with sample data!"))
