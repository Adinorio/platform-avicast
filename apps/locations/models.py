"""
Simplified locations and census models for AVICAST
Following the new card-based user flow: Site -> Year -> Month -> Census Table
"""

import uuid
import os
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone

from apps.common.mixins.optimizable_image import OptimizableImageMixin

User = get_user_model()


def site_image_upload_path(instance, filename):
    """Generate upload path for site images"""
    ext = filename.split('.')[-1]
    filename = f"{instance.id}.{ext}"
    return os.path.join('sites', filename)


class Site(OptimizableImageMixin):
    """Site model for wildlife monitoring locations"""

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

    # Image support
    image = models.ImageField(
        upload_to=site_image_upload_path,
        null=True,
        blank=True,
        help_text="Site image for card display"
    )

    status = models.CharField(max_length=20, choices=SITE_STATUS, default="active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        app_label = "locations"
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

    def get_years_with_census(self):
        """Get all years that have census data for this site"""
        return CensusYear.objects.filter(site=self).order_by('-year')


class CensusYear(models.Model):
    """Year-based grouping for census data"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name="census_years")
    year = models.PositiveIntegerField()

    # Summary data (computed fields)
    total_census_count = models.PositiveIntegerField(default=0, help_text="Total census records for this year")
    total_birds_recorded = models.PositiveIntegerField(default=0, help_text="Total birds recorded this year")
    total_species_recorded = models.PositiveIntegerField(default=0, help_text="Total species recorded this year")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "locations"
        ordering = ["-year"]
        unique_together = ["site", "year"]
        verbose_name = "Census Year"
        verbose_name_plural = "Census Years"

    def __str__(self):
        return f"{self.site.name} - {self.year}"

    def get_months_with_census(self):
        """Get all months that have census data for this year"""
        return CensusMonth.objects.filter(year=self).order_by('month')

    def update_summary(self):
        """Update summary statistics for this year"""
        months = self.get_months_with_census()
        self.total_census_count = sum(month.total_census_count for month in months)
        self.total_birds_recorded = sum(month.total_birds_recorded for month in months)
        self.total_species_recorded = sum(month.total_species_recorded for month in months)
        self.save(update_fields=['total_census_count', 'total_birds_recorded', 'total_species_recorded', 'updated_at'])


class CensusMonth(models.Model):
    """Month-based grouping for census data"""

    MONTH_CHOICES = [
        (1, "January"), (2, "February"), (3, "March"), (4, "April"),
        (5, "May"), (6, "June"), (7, "July"), (8, "August"),
        (9, "September"), (10, "October"), (11, "November"), (12, "December"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    year = models.ForeignKey(CensusYear, on_delete=models.CASCADE, related_name="census_months")
    month = models.PositiveIntegerField(choices=MONTH_CHOICES)

    # Summary data (computed fields)
    total_census_count = models.PositiveIntegerField(default=0, help_text="Total census records for this month")
    total_birds_recorded = models.PositiveIntegerField(default=0, help_text="Total birds recorded this month")
    total_species_recorded = models.PositiveIntegerField(default=0, help_text="Total species recorded this month")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "locations"
        ordering = ["month"]
        unique_together = ["year", "month"]
        verbose_name = "Census Month"
        verbose_name_plural = "Census Months"

    def __str__(self):
        return f"{self.year.site.name} - {self.get_month_display()} {self.year.year}"

    def get_census_records(self):
        """Get all census records for this month"""
        return Census.objects.filter(month=self).order_by('-census_date')

    def update_summary(self):
        """Update summary statistics for this month"""
        census_records = self.get_census_records()
        self.total_census_count = census_records.count()
        self.total_birds_recorded = sum(census.total_birds for census in census_records)
        self.total_species_recorded = sum(census.total_species for census in census_records)
        self.save(update_fields=['total_census_count', 'total_birds_recorded', 'total_species_recorded', 'updated_at'])


class Census(models.Model):
    """Individual census record with bird observations and personnel"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    month = models.ForeignKey(CensusMonth, on_delete=models.CASCADE, related_name="census_records")
    census_date = models.DateField(help_text="Date when census was conducted")

    # Personnel who conducted the fieldwork
    lead_observer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lead_census",
        help_text="Primary observer who led the fieldwork"
    )
    field_team = models.ManyToManyField(
        User,
        blank=True,
        related_name="census_team",
        help_text="All personnel who participated in the fieldwork"
    )

    # Weather and conditions
    weather_conditions = models.CharField(
        max_length=200,
        blank=True,
        help_text="Weather conditions during census"
    )
    notes = models.TextField(blank=True, help_text="General census notes")

    # Census data (computed fields)
    total_birds = models.PositiveIntegerField(default=0, help_text="Total birds observed")
    total_species = models.PositiveIntegerField(default=0, help_text="Total species observed")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "locations"
        ordering = ["-census_date"]
        unique_together = ["month", "census_date"]
        verbose_name = "Census"
        verbose_name_plural = "Census Records"

    def __str__(self):
        return f"{self.month} - {self.census_date}"

    def get_observations(self):
        """Get all bird observations for this census"""
        return CensusObservation.objects.filter(census=self)

    def update_totals(self):
        """Update total birds and species counts"""
        observations = self.get_observations()
        self.total_birds = sum(obs.count for obs in observations)
        self.total_species = observations.values('species').distinct().count()
        self.save(update_fields=['total_birds', 'total_species', 'updated_at'])


class CensusObservation(models.Model):
    """Individual bird species observation within a census"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    census = models.ForeignKey(Census, on_delete=models.CASCADE, related_name="observations")

    # Species information
    species = models.ForeignKey(
        "fauna.Species",
        on_delete=models.CASCADE,
        related_name="census_observations",
        null=True,
        blank=True
    )
    species_name = models.CharField(max_length=200, help_text="Common or scientific name")
    count = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    # Additional notes removed - behavior_notes field deleted

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "locations"
        ordering = ["species_name"]
        verbose_name = "Census Observation"
        verbose_name_plural = "Census Observations"

    def __str__(self):
        return f"{self.species.name if self.species else self.species_name} - {self.count} birds"

    def save(self, *args, **kwargs):
        """Override save to update census totals"""
        super().save(*args, **kwargs)
        # Update census totals after saving
        if self.census:
            self.census.update_totals()


# Signal handlers to automatically update summary data
@receiver([post_save, post_delete], sender=Census)
def update_census_month_summary(sender, instance, **kwargs):
    """Update month summary when census records change"""
    if instance.month:
        instance.month.update_summary()


@receiver([post_save, post_delete], sender=CensusObservation)
def update_census_totals(sender, instance, **kwargs):
    """Update census totals when observations change"""
    if instance.census:
        instance.census.update_totals()


@receiver([post_save, post_delete], sender=CensusMonth)
def update_census_year_summary(sender, instance, **kwargs):
    """Update year summary when month records change"""
    if instance.year:
        instance.year.update_summary()
