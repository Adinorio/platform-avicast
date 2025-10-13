"""
Management command to fix year totals calculations
"""
from django.core.management.base import BaseCommand
from django.db.models import Count, Sum
from apps.locations.models import CensusYear, CensusObservation


class Command(BaseCommand):
    help = 'Fix year totals calculations for all census years'

    def handle(self, *args, **options):
        self.stdout.write("Fixing year totals calculations...")
        
        years_updated = 0
        
        for year in CensusYear.objects.all():
            # Calculate actual counts
            observations = CensusObservation.objects.filter(census__month__year=year)
            
            actual_census_count = year.census_months.aggregate(
                count=Count('census')
            )['count'] or 0
            
            actual_birds = observations.aggregate(
                total=Sum('count')
            )['total'] or 0
            
            actual_species = observations.values('species').distinct().count()
            
            # Check if updates are needed
            needs_update = (
                year.total_census_count != actual_census_count or
                year.total_birds_recorded != actual_birds or
                year.total_species_recorded != actual_species
            )
            
            if needs_update:
                self.stdout.write(
                    f"Updating year {year.year} for site {year.site.name}:"
                )
                self.stdout.write(f"  Census: {year.total_census_count} → {actual_census_count}")
                self.stdout.write(f"  Birds: {year.total_birds_recorded} → {actual_birds}")
                self.stdout.write(f"  Species: {year.total_species_recorded} → {actual_species}")
                
                # Update the year
                year.total_census_count = actual_census_count
                year.total_birds_recorded = actual_birds
                year.total_species_recorded = actual_species
                year.save()
                
                years_updated += 1
                self.stdout.write(self.style.SUCCESS("  ✓ Updated"))
            else:
                self.stdout.write(
                    self.style.SUCCESS(f"Year {year.year} for site {year.site.name} is correct")
                )
        
        self.stdout.write(
            self.style.SUCCESS(f"\nCompleted! Updated {years_updated} years.")
        )
