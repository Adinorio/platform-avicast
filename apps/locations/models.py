import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

User = get_user_model()

# Create your models here.

class Site(models.Model):
    SITE_TYPES = [
        ('wetland', 'Wetland'),
        ('forest', 'Forest'),
        ('grassland', 'Grassland'),
        ('urban', 'Urban'),
        ('coastal', 'Coastal'),
        ('mountain', 'Mountain'),
        ('other', 'Other'),
    ]
    
    SITE_STATUS = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('monitoring', 'Under Monitoring'),
        ('restricted', 'Restricted Access'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    site_type = models.CharField(max_length=20, choices=SITE_TYPES, default='other')
    coordinates = models.CharField(max_length=100, blank=True, help_text="Latitude, Longitude")
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=SITE_STATUS, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Site'
        verbose_name_plural = 'Sites'
    
    def __str__(self):
        return self.name
    
    def get_coordinates_display(self):
        """Return formatted coordinates for display"""
        if self.coordinates:
            try:
                lat, lon = self.coordinates.split(',')
                return f"{float(lat):.6f}, {float(lon):.6f}"
            except:
                return self.coordinates
        return "Coordinates not set"
    
    def get_census_summary(self):
        """Get summary of census data by year and month"""
        from .models import CensusObservation
        
        summary = {}
        observations = CensusObservation.objects.filter(site=self).order_by('-observation_date')
        
        for obs in observations:
            year = obs.observation_date.year
            month = obs.observation_date.month
            
            if year not in summary:
                summary[year] = {}
            
            if month not in summary[year]:
                summary[year][month] = {
                    'total_species': 0,
                    'total_birds': 0,
                    'observations': []
                }
            
            summary[year][month]['total_species'] += obs.species_observations.count()
            summary[year][month]['total_birds'] += sum(
                so.count for so in obs.species_observations.all()
            )
            summary[year][month]['observations'].append(obs)
        
        return summary

class CensusObservation(models.Model):
    """Main census observation record for a site"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='census_observations')
    observation_date = models.DateField()
    observer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    weather_conditions = models.CharField(max_length=200, blank=True, help_text="Weather during observation")
    notes = models.TextField(blank=True, help_text="General observation notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-observation_date']
        unique_together = ['site', 'observation_date']
        verbose_name = 'Census Observation'
        verbose_name_plural = 'Census Observations'
    
    def __str__(self):
        return f"{self.site.name} - {self.observation_date}"
    
    def get_total_species_count(self):
        """Get total number of species observed"""
        return self.species_observations.count()
    
    def get_total_birds_count(self):
        """Get total number of birds observed"""
        return sum(so.count for so in self.species_observations.all())
    
    def get_month_name(self):
        """Get month name for display"""
        return self.observation_date.strftime('%B')
    
    def get_year(self):
        """Get year for display"""
        return self.observation_date.year

class SpeciesObservation(models.Model):
    """Individual species observation within a census"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    census = models.ForeignKey(CensusObservation, on_delete=models.CASCADE, related_name='species_observations')
    species_name = models.CharField(max_length=200, help_text="Common or scientific name")
    count = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    behavior_notes = models.TextField(blank=True, help_text="Behavior, age, sex, etc.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['species_name']
        verbose_name = 'Species Observation'
        verbose_name_plural = 'Species Observations'
    
    def __str__(self):
        return f"{self.species_name} - {self.count} birds"
