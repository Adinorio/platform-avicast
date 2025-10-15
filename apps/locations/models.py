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
    coordinates = models.CharField(max_length=100, blank=False, help_text="Latitude, Longitude (e.g., 14.5995, 120.9842)")
    description = models.TextField(blank=True)

    # Image support
    image = models.ImageField(
        upload_to=site_image_upload_path,
        null=True,
        blank=True,
        help_text="Site image for card display"
    )

    status = models.CharField(max_length=20, choices=SITE_STATUS, default="active")
    is_archived = models.BooleanField(default=False, help_text="Archive site instead of deleting")
    archived_at = models.DateTimeField(null=True, blank=True, help_text="When the site was archived")
    archived_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="archived_sites")
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
                lat, lon = self.parse_coordinates()
                return f"{lat:.6f}, {lon:.6f}"
            except (ValueError, IndexError):
                return self.coordinates
        return "Coordinates not set"

    def parse_coordinates(self):
        """Parse coordinates string and return (lat, lon) tuple"""
        if not self.coordinates:
            return None, None
        
        # Handle various coordinate formats
        coords_str = self.coordinates.strip()
        
        # Split by common delimiters
        for delimiter in [',', ';', '|', ' ']:
            if delimiter in coords_str:
                parts = coords_str.split(delimiter)
                if len(parts) >= 2:
                    lat = float(parts[0].strip())
                    lon = float(parts[1].strip())
                    return lat, lon
        
        # Try to parse as space-separated
        parts = coords_str.split()
        if len(parts) >= 2:
            lat = float(parts[0].strip())
            lon = float(parts[1].strip())
            return lat, lon
        
        raise ValueError(f"Invalid coordinate format: {coords_str}")

    def normalize_coordinates(self, lat, lon):
        """Normalize and validate coordinates, return standardized string"""
        # Validate latitude (-90 to 90)
        if not -90 <= lat <= 90:
            raise ValueError(f"Latitude must be between -90 and 90, got {lat}")
        
        # Validate longitude (-180 to 180)
        if not -180 <= lon <= 180:
            raise ValueError(f"Longitude must be between -180 and 180, got {lon}")
        
        # Round to 6 decimal places (approximately 0.1m precision)
        lat = round(lat, 6)
        lon = round(lon, 6)
        
        # Return standardized format: "lat, lon"
        return f"{lat}, {lon}"

    @classmethod
    def parse_coordinate_input(cls, coordinate_input):
        """
        Parse various coordinate input formats and return normalized coordinates string.
        
        Accepts formats like:
        - "14.5995, 120.9842"
        - "14.5995,120.9842"
        - "14.5995; 120.9842"
        - "14.5995 120.9842"
        - "14°35'58.2\"N, 120°59'3.1\"E" (basic DMS support)
        """
        if not coordinate_input or not coordinate_input.strip():
            raise ValueError("Coordinates cannot be empty")
        
        input_str = coordinate_input.strip()
        
        # Handle degree-minute-second format (basic)
        if any(char in input_str for char in ['°', "'", '"']):
            try:
                return cls._parse_dms_format(input_str)
            except ValueError:
                pass  # Fall back to decimal format
        
        # Handle decimal formats
        return cls._parse_decimal_format(input_str)

    @classmethod
    def _parse_decimal_format(cls, input_str):
        """Parse decimal coordinate formats"""
        # Split by common delimiters
        for delimiter in [',', ';', '|']:
            if delimiter in input_str:
                parts = input_str.split(delimiter)
                if len(parts) >= 2:
                    lat = float(parts[0].strip())
                    lon = float(parts[1].strip())
                    return cls().normalize_coordinates(lat, lon)
        
        # Try space-separated
        parts = input_str.split()
        if len(parts) >= 2:
            lat = float(parts[0].strip())
            lon = float(parts[1].strip())
            return cls().normalize_coordinates(lat, lon)
        
        raise ValueError(f"Invalid coordinate format: {input_str}")

    @classmethod
    def _parse_dms_format(cls, input_str):
        """Parse degree-minute-second format (basic implementation)"""
        # This is a simplified DMS parser
        # For production, consider using a library like pyproj
        import re
        
        # Basic regex for DMS format
        dms_pattern = r"(\d+)°(\d+)'([\d.]+)\"([NS])\s*,\s*(\d+)°(\d+)'([\d.]+)\"([EW])"
        match = re.match(dms_pattern, input_str)
        
        if match:
            lat_deg, lat_min, lat_sec, lat_dir, lon_deg, lon_min, lon_sec, lon_dir = match.groups()
            
            lat = float(lat_deg) + float(lat_min)/60 + float(lat_sec)/3600
            lon = float(lon_deg) + float(lon_min)/60 + float(lon_sec)/3600
            
            if lat_dir == 'S':
                lat = -lat
            if lon_dir == 'W':
                lon = -lon
            
            return cls().normalize_coordinates(lat, lon)
        
        raise ValueError(f"Invalid DMS format: {input_str}")

    def save(self, *args, **kwargs):
        """Override save to normalize coordinates"""
        if self.coordinates:
            try:
                lat, lon = self.parse_coordinates()
                self.coordinates = self.normalize_coordinates(lat, lon)
            except (ValueError, IndexError) as e:
                # Don't save if coordinates are invalid
                raise ValueError(f"Invalid coordinates: {e}")
        super().save(*args, **kwargs)

    def get_years_with_census(self):
        """Get all years that have census data for this site"""
        return CensusYear.objects.filter(site=self).order_by('-year')
    
    def archive(self, user=None):
        """Archive this site"""
        self.is_archived = True
        self.archived_at = timezone.now()
        if user:
            self.archived_by = user
        self.save()
    
    def restore(self):
        """Restore this site from archive"""
        self.is_archived = False
        self.archived_at = None
        self.archived_by = None
        self.save()


class CensusYear(models.Model):
    """Year-based grouping for census data"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name="census_years")
    year = models.PositiveIntegerField()

    # Summary data (computed fields)
    total_census_count = models.PositiveIntegerField(default=0, help_text="Total census records for this year")
    total_birds_recorded = models.PositiveIntegerField(default=0, help_text="Total birds recorded this year")
    total_species_recorded = models.PositiveIntegerField(default=0, help_text="Total species recorded this year")

    is_archived = models.BooleanField(default=False, help_text="Archive year instead of deleting")
    archived_at = models.DateTimeField(null=True, blank=True)
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

    is_archived = models.BooleanField(default=False, help_text="Archive month instead of deleting")
    archived_at = models.DateTimeField(null=True, blank=True)
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

    is_archived = models.BooleanField(default=False, help_text="Archive census instead of deleting")
    archived_at = models.DateTimeField(null=True, blank=True)
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

    def save(self, *args, **kwargs):
        """Override save to log census record changes"""
        is_new = self._state.adding
        action = "CREATING" if is_new else "UPDATING"
        print(f"DEBUG: Census.save() - {action} census record ID: {self.id}, Date: {self.census_date}, Birds: {self.total_birds}, Species: {self.total_species}")
        super().save(*args, **kwargs)

    def get_observations(self):
        """Get all bird observations for this census"""
        return CensusObservation.objects.filter(census=self)

    def update_totals(self):
        """Update total birds and species counts"""
        observations = self.get_observations()
        old_birds = self.total_birds
        old_species = self.total_species
        self.total_birds = sum(obs.count for obs in observations)
        self.total_species = observations.values('species').distinct().count()
        print(f"DEBUG: Census.update_totals() - ID: {self.id}, Old: {old_birds} birds, {old_species} species -> New: {self.total_birds} birds, {self.total_species} species")
        self.save(update_fields=['total_birds', 'total_species', 'updated_at'])


class AllocationHistory(models.Model):
    """Track allocation history for audit purposes"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # What was allocated
    processing_result = models.ForeignKey(
        "image_processing.ProcessingResult",
        on_delete=models.CASCADE,
        related_name="allocation_history"
    )
    census = models.ForeignKey(
        Census,
        on_delete=models.CASCADE,
        related_name="allocation_history"
    )

    # Who and when
    allocated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="allocation_history"
    )
    allocated_at = models.DateTimeField(auto_now_add=True)

    # Allocation details
    bird_count = models.PositiveIntegerField(help_text="Number of birds allocated")
    site = models.ForeignKey(
        "locations.Site",
        on_delete=models.CASCADE,
        related_name="allocation_history"
    )
    observation_date = models.DateField(help_text="Date of the census observation")

    # Additional context
    notes = models.TextField(blank=True, help_text="Optional notes about this allocation")

    class Meta:
        app_label = "locations"
        ordering = ["-allocated_at"]
        verbose_name = "Allocation History"
        verbose_name_plural = "Allocation History"

    def __str__(self):
        return f"Allocation: {self.processing_result.image_upload.title} -> {self.census} ({self.bird_count} birds)"


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
    family = models.CharField(max_length=100, blank=True, help_text="Bird family (optional)")
    count = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    # Additional notes removed - behavior_notes field deleted

    is_archived = models.BooleanField(default=False, help_text="Archive observation instead of deleting")
    archived_at = models.DateTimeField(null=True, blank=True)
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
        print(f"DEBUG: Saving CensusObservation - Species: {self.species_name if self.species_name else 'Unknown'}, Count: {self.count}")
        super().save(*args, **kwargs)
        # Update census totals after saving
        if self.census:
            print(f"DEBUG: Updating census totals for census ID: {self.census.id}")
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
