import uuid

from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

User = get_user_model()

# Create your models here.


class Site(models.Model):
    SITE_TYPES = [
        ("wetland", "Wetland"),
        ("forest", "Forest"),
        ("grassland", "Grassland"),
        ("urban", "Urban"),
        ("coastal", "Coastal"),
        ("mountain", "Mountain"),
        ("other", "Other"),
    ]

    SITE_STATUS = [
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("monitoring", "Under Monitoring"),
        ("restricted", "Restricted Access"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    site_type = models.CharField(max_length=20, choices=SITE_TYPES, default="other")
    coordinates = models.CharField(max_length=100, blank=True, help_text="Latitude, Longitude")
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=SITE_STATUS, default="active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Site"
        verbose_name_plural = "Sites"

    def __str__(self):
        return self.name

    def get_coordinates_display(self):
        """Return formatted coordinates for display"""
        if self.coordinates:
            try:
                lat, lon = self.coordinates.split(",")
                return f"{float(lat):.6f}, {float(lon):.6f}"
            except (ValueError, IndexError):
                return self.coordinates
        return "Coordinates not set"

    def get_census_summary(self):
        """Get summary of census data by year and month"""
        summary = {}
        observations = CensusObservation.objects.filter(site=self).order_by("-observation_date")

        for obs in observations:
            year = obs.observation_date.year
            month = obs.observation_date.month

            if year not in summary:
                summary[year] = {}

            if month not in summary[year]:
                summary[year][month] = {"total_species": 0, "total_birds": 0, "observations": []}

            summary[year][month]["total_species"] += obs.species_observations.count()
            summary[year][month]["total_birds"] += sum(
                so.count for so in obs.species_observations.all()
            )
            summary[year][month]["observations"].append(obs)

        return summary


class CensusObservation(models.Model):
    """Main census observation record for a site"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name="census_observations")
    observation_date = models.DateField()
    observer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    weather_conditions = models.CharField(
        max_length=200, blank=True, help_text="Weather during observation"
    )
    notes = models.TextField(blank=True, help_text="General observation notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-observation_date"]
        unique_together = ["site", "observation_date"]
        verbose_name = "Census Observation"
        verbose_name_plural = "Census Observations"

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
        return self.observation_date.strftime("%B")

    def get_year(self):
        """Get year for display"""
        return self.observation_date.year


class SpeciesObservation(models.Model):
    """Individual species observation within a census"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    census = models.ForeignKey(
        CensusObservation, on_delete=models.CASCADE, related_name="species_observations"
    )
    species_name = models.CharField(max_length=200, help_text="Common or scientific name")
    count = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    behavior_notes = models.TextField(blank=True, help_text="Behavior, age, sex, etc.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["species_name"]
        verbose_name = "Species Observation"
        verbose_name_plural = "Species Observations"

    def __str__(self):
        return f"{self.species_name} - {self.count} birds"


class MobileDataImport(models.Model):
    """Handle data imports from mobile applications"""

    IMPORT_STATUS = [
        ("pending", "Pending Review"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("processed", "Processed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    import_data = models.JSONField(help_text="Raw data from mobile app in JSON format")
    site = models.ForeignKey(
        Site, on_delete=models.CASCADE, help_text="Target site for data import"
    )
    submitted_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="submitted_imports"
    )
    reviewed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="reviewed_imports"
    )
    status = models.CharField(max_length=20, choices=IMPORT_STATUS, default="pending")
    review_notes = models.TextField(blank=True, help_text="Notes from reviewer")
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Mobile Data Import"
        verbose_name_plural = "Mobile Data Imports"

    def __str__(self):
        return f"Import for {self.site.name} by {self.submitted_by.get_full_name()} - {self.get_status_display()}"

    def approve(self, reviewer):
        """Approve the import request"""
        self.status = "approved"
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.save()

    def reject(self, reviewer, notes=""):
        """Reject the import request"""
        self.status = "rejected"
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.review_notes = notes
        self.save()

    def process_import(self):
        """Process approved import and create census data"""
        if self.status != "approved":
            raise ValueError("Can only process approved imports")

        try:
            # Parse import data
            data = self.import_data

            # Create census observation
            census = CensusObservation.objects.create(
                site=self.site,
                observation_date=data.get("observation_date", timezone.now().date()),
                observer=self.submitted_by,
                weather_conditions=data.get("weather_conditions", ""),
                notes=f"Imported from mobile app on {timezone.now()}",
            )

            # Create species observations
            species_data = data.get("species_observations", [])
            for species in species_data:
                SpeciesObservation.objects.create(
                    census=census,
                    species_name=species["species_name"],
                    count=species["count"],
                    behavior_notes=species.get("behavior_notes", ""),
                )

            self.status = "processed"
            self.processed_at = timezone.now()
            self.save()

            return census

        except Exception as e:
            # Log error and mark as rejected
            self.status = "rejected"
            self.review_notes = f"Processing failed: {str(e)}"
            self.save()
            raise e
