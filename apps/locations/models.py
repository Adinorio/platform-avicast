import uuid

from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from apps.common.mixins.optimizable_image import OptimizableImageMixin

User = get_user_model()

# Create your models here.


class Site(OptimizableImageMixin):
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
    area_hectares = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Site area in hectares"
    )
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
    is_archived = models.BooleanField(default=False, help_text="Whether this census record is archived")
    archived_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="archived_census")
    archived_at = models.DateTimeField(null=True, blank=True, help_text="When this record was archived")
    archived_reason = models.TextField(blank=True, help_text="Reason for archiving this record")
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

    def archive(self, user, reason=""):
        """Archive this census observation"""
        from django.utils import timezone

        self.is_archived = True
        self.archived_by = user
        self.archived_at = timezone.now()
        self.archived_reason = reason
        self.save()

    def restore(self):
        """Restore this archived census observation"""
        self.is_archived = False
        self.archived_by = None
        self.archived_at = None
        self.archived_reason = ""
        self.save()

    def update_site_species_counts(self):
        """Update SiteSpeciesCount records based on this census observation"""
        # Only update if not archived
        if not self.is_archived:
            for species_obs in self.species_observations.all():
                if species_obs.species:
                    # Get or create SiteSpeciesCount record
                    site_count, created = SiteSpeciesCount.objects.get_or_create(
                        site=self.site,
                        species=species_obs.species,
                        defaults={'total_count': 0, 'observation_count': 0}
                    )

                    # Update the count
                    site_count.update_from_observation(species_obs.count, self.observation_date)

    def save(self, *args, **kwargs):
        """Override save to update site species counts"""
        super().save(*args, **kwargs)
        # Update site species counts after saving
        self.update_site_species_counts()


class SpeciesObservation(models.Model):
    """Individual species observation within a census"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    census = models.ForeignKey(
        CensusObservation, on_delete=models.CASCADE, related_name="species_observations"
    )
    species = models.ForeignKey(
        "fauna.Species", on_delete=models.CASCADE, related_name="site_observations", null=True, blank=True
    )
    species_name = models.CharField(max_length=200, help_text="Common or scientific name (legacy field)")
    count = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    behavior_notes = models.TextField(blank=True, help_text="Behavior, age, sex, etc.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["species_name"]
        verbose_name = "Species Observation"
        verbose_name_plural = "Species Observations"

    def __str__(self):
        return f"{self.species.name if self.species else self.species_name} - {self.count} birds"

    def save(self, *args, **kwargs):
        """Override save to update site species counts"""
        super().save(*args, **kwargs)
        # Update site species counts after saving
        if self.census:
            self.census.update_site_species_counts()


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


class SiteSpeciesCount(models.Model):
    """
    Tracks species presence and counts for each site.
    Updated from census observations and image processing allocations.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name="species_counts")
    species = models.ForeignKey("fauna.Species", on_delete=models.CASCADE, related_name="site_counts")

    # Count data
    total_count = models.PositiveIntegerField(default=0, help_text="Total birds of this species observed at this site")
    last_observation_date = models.DateField(null=True, blank=True, help_text="Most recent observation date")
    observation_count = models.PositiveIntegerField(default=0, help_text="Number of observations of this species")

    # Status and verification
    is_verified = models.BooleanField(default=False, help_text="Whether this species presence is verified")
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="verified_species_counts")
    verified_at = models.DateTimeField(null=True, blank=True)

    # Monthly/Yearly aggregations (computed fields)
    monthly_counts = models.JSONField(default=dict, help_text="Bird counts by month (YYYY-MM: count)")
    yearly_counts = models.JSONField(default=dict, help_text="Bird counts by year (YYYY: count)")

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_updated_from_census = models.DateTimeField(null=True, blank=True, help_text="Last time updated from census data")

    class Meta:
        unique_together = ["site", "species"]
        ordering = ["site", "species__name"]
        verbose_name = "Site Species Count"
        verbose_name_plural = "Site Species Counts"
        indexes = [
            models.Index(fields=["site", "species"]),
            models.Index(fields=["site", "is_verified"]),
            models.Index(fields=["species", "total_count"]),
        ]

    def __str__(self):
        return f"{self.site.name} - {self.species.name} ({self.total_count} birds)"

    def update_from_observation(self, count, observation_date):
        """Update counts from a new observation"""
        from django.utils import timezone

        self.total_count += count
        self.observation_count += 1

        if not self.last_observation_date or observation_date > self.last_observation_date:
            self.last_observation_date = observation_date

        # Update monthly/yearly counts
        year_month = observation_date.strftime('%Y-%m')
        year = str(observation_date.year)

        if year_month not in self.monthly_counts:
            self.monthly_counts[year_month] = 0
        self.monthly_counts[year_month] += count

        if year not in self.yearly_counts:
            self.yearly_counts[year] = 0
        self.yearly_counts[year] += count

        self.last_updated_from_census = timezone.now()
        self.save()

    def verify_count(self, verifier):
        """Mark species count as verified"""
        from django.utils import timezone

        self.is_verified = True
        self.verified_by = verifier
        self.verified_at = timezone.now()
        self.save()

    def get_monthly_summary(self, year=None):
        """Get monthly counts for a specific year or all years"""
        if year:
            return {k: v for k, v in self.monthly_counts.items() if k.startswith(str(year))}
        return self.monthly_counts

    def get_yearly_summary(self):
        """Get yearly counts"""
        return self.yearly_counts


class DataChangeRequest(models.Model):
    """
    Field workers can submit requests to add/edit/delete data.
    Admins review and approve/reject these requests.
    """

    REQUEST_TYPES = [
        ("add_census", "Add Census Observation"),
        ("edit_census", "Edit Census Observation"),
        ("delete_census", "Delete Census Observation"),
        ("add_species", "Add Species to Census"),
        ("edit_species", "Edit Species Count"),
        ("delete_species", "Remove Species from Census"),
        ("edit_site", "Edit Site Information"),
    ]

    REQUEST_STATUS = [
        ("pending", "Pending Review"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("completed", "Completed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request_type = models.CharField(max_length=50, choices=REQUEST_TYPES)
    status = models.CharField(max_length=20, choices=REQUEST_STATUS, default="pending")

    # Request details
    site = models.ForeignKey(
        Site,
        on_delete=models.CASCADE,
        related_name="change_requests",
        help_text="Site this request is related to"
    )
    census = models.ForeignKey(
        CensusObservation,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="change_requests",
        help_text="Census observation if applicable"
    )
    
    # Request data (stores JSON with the requested changes)
    request_data = models.JSONField(
        help_text="JSON data containing the requested changes"
    )
    reason = models.TextField(
        help_text="Reason for the request from field worker"
    )

    # Request tracking
    requested_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="submitted_requests"
    )
    requested_at = models.DateTimeField(auto_now_add=True)

    # Review tracking
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_requests"
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True, help_text="Admin's review notes")

    # Completion tracking
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the approved request was actually executed"
    )

    class Meta:
        ordering = ["-requested_at"]
        verbose_name = "Data Change Request"
        verbose_name_plural = "Data Change Requests"
        indexes = [
            models.Index(fields=["status", "requested_at"]),
            models.Index(fields=["requested_by", "status"]),
            models.Index(fields=["site", "status"]),
        ]

    def __str__(self):
        return f"{self.get_request_type_display()} by {self.requested_by.get_full_name()} - {self.get_status_display()}"

    def approve(self, reviewer, notes=""):
        """Approve the request"""
        from django.utils import timezone

        self.status = "approved"
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.review_notes = notes
        self.save()

    def reject(self, reviewer, notes=""):
        """Reject the request"""
        from django.utils import timezone

        self.status = "rejected"
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.review_notes = notes
        self.save()

    def complete(self):
        """Mark request as completed after execution"""
        from django.utils import timezone

        self.status = "completed"
        self.completed_at = timezone.now()
        self.save()

    def execute_request(self):
        """
        Execute the approved request based on request_type.
        Only approved requests can be executed.
        """
        if self.status != "approved":
            raise ValueError("Only approved requests can be executed")

        from django.utils import timezone

        try:
            if self.request_type == "add_census":
                # Create new census observation
                census = CensusObservation.objects.create(
                    site=self.site,
                    observation_date=self.request_data.get("observation_date"),
                    observer=self.requested_by,
                    weather_conditions=self.request_data.get("weather_conditions", ""),
                    notes=self.request_data.get("notes", ""),
                )
                
                # Add species observations
                for species_data in self.request_data.get("species", []):
                    SpeciesObservation.objects.create(
                        census=census,
                        species_id=species_data.get("species_id"),
                        species_name=species_data.get("species_name", ""),
                        count=species_data.get("count", 1),
                        behavior_notes=species_data.get("behavior_notes", ""),
                    )
                
                self.census = census
                self.save()

            elif self.request_type == "edit_census":
                # Update existing census
                if self.census:
                    for field, value in self.request_data.items():
                        if hasattr(self.census, field):
                            setattr(self.census, field, value)
                    self.census.save()

            elif self.request_type == "delete_census":
                # Delete census observation
                if self.census:
                    self.census.delete()

            elif self.request_type == "add_species":
                # Add species to existing census
                if self.census:
                    SpeciesObservation.objects.create(
                        census=self.census,
                        species_id=self.request_data.get("species_id"),
                        species_name=self.request_data.get("species_name", ""),
                        count=self.request_data.get("count", 1),
                        behavior_notes=self.request_data.get("behavior_notes", ""),
                    )

            elif self.request_type == "edit_species":
                # Edit species observation
                species_obs_id = self.request_data.get("species_observation_id")
                if species_obs_id:
                    species_obs = SpeciesObservation.objects.get(id=species_obs_id)
                    for field, value in self.request_data.items():
                        if hasattr(species_obs, field) and field != "species_observation_id":
                            setattr(species_obs, field, value)
                    species_obs.save()

            elif self.request_type == "delete_species":
                # Delete species observation
                species_obs_id = self.request_data.get("species_observation_id")
                if species_obs_id:
                    SpeciesObservation.objects.get(id=species_obs_id).delete()

            elif self.request_type == "edit_site":
                # Edit site information
                for field, value in self.request_data.items():
                    if hasattr(self.site, field):
                        setattr(self.site, field, value)
                self.site.save()

            # Mark as completed
            self.complete()
            return True

        except Exception as e:
            # Log error but don't mark as completed
            self.review_notes += f"\n\nExecution Error: {str(e)}"
            self.save()
            raise e


class CensusActivityLog(models.Model):
    """
    Activity log for tracking changes to census data.
    Provides audit trail for all census operations.
    """

    ACTIVITY_TYPES = [
        ("create", "Created"),
        ("update", "Updated"),
        ("delete", "Deleted"),
        ("archive", "Archived"),
        ("restore", "Restored"),
        ("import", "Imported"),
        ("bulk_import", "Bulk Imported"),
        ("verify", "Verified"),
        ("batch_edit", "Batch Edited"),
        ("export", "Exported"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    census = models.ForeignKey(
        CensusObservation,
        on_delete=models.CASCADE,
        related_name="activity_logs",
        help_text="Census observation this activity relates to"
    )
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    description = models.TextField(help_text="Description of the activity")
    old_values = models.JSONField(null=True, blank=True, help_text="Previous field values (for updates)")
    new_values = models.JSONField(null=True, blank=True, help_text="New field values (for updates)")
    performed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="census_activities"
    )
    performed_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, help_text="Browser/client information")

    class Meta:
        ordering = ["-performed_at"]
        verbose_name = "Census Activity Log"
        verbose_name_plural = "Census Activity Logs"
        indexes = [
            models.Index(fields=["census", "performed_at"]),
            models.Index(fields=["activity_type", "performed_at"]),
            models.Index(fields=["performed_by", "performed_at"]),
        ]

    def __str__(self):
        return f"{self.get_activity_type_display()} on {self.census} by {self.performed_by.get_full_name() if self.performed_by else 'System'}"

    def save(self, *args, **kwargs):
        # Set IP address if available from request context
        if not self.ip_address and hasattr(self, '_request'):
            self.ip_address = self._request.META.get('REMOTE_ADDR')
            self.user_agent = self._request.META.get('HTTP_USER_AGENT', '')

        super().save(*args, **kwargs)


class BulkCensusImport(models.Model):
    """
    Handles bulk import of historical census data from Excel/CSV files.
    Supports large datasets with multiple sites, species, and time periods.
    """

    IMPORT_STATUS = [
        ("pending", "Pending Review"),
        ("validating", "Validating Data"),
        ("validation_failed", "Validation Failed"),
        ("ready", "Ready for Import"),
        ("importing", "Importing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
    ]

    IMPORT_TYPES = [
        ("excel", "Excel File"),
        ("csv", "CSV File"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField(upload_to="bulk_census_imports/", help_text="Uploaded Excel/CSV file")
    file_type = models.CharField(max_length=20, choices=IMPORT_TYPES)
    original_filename = models.CharField(max_length=255)

    # Import metadata
    total_rows = models.PositiveIntegerField(default=0, help_text="Total rows in the file")
    valid_rows = models.PositiveIntegerField(default=0, help_text="Rows that passed validation")
    invalid_rows = models.PositiveIntegerField(default=0, help_text="Rows that failed validation")
    imported_records = models.PositiveIntegerField(default=0, help_text="Successfully imported census records")

    # Processing details
    status = models.CharField(max_length=20, choices=IMPORT_STATUS, default="pending")
    error_summary = models.JSONField(default=dict, help_text="Summary of validation errors")
    validation_errors = models.JSONField(default=list, help_text="Detailed validation errors")
    import_preview = models.JSONField(default=list, help_text="Preview of data to be imported")

    # User tracking
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bulk_imports")
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="processed_bulk_imports")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    # Import configuration
    site_column = models.CharField(max_length=50, blank=True, help_text="Column name for site identification")
    species_column = models.CharField(max_length=50, blank=True, help_text="Column name for species identification")
    count_column = models.CharField(max_length=50, blank=True, help_text="Column name for bird counts")
    date_column = models.CharField(max_length=50, blank=True, help_text="Column name for observation dates")
    notes_column = models.CharField(max_length=50, blank=True, help_text="Column name for observation notes")

    class Meta:
        ordering = ["-uploaded_at"]
        verbose_name = "Bulk Census Import"
        verbose_name_plural = "Bulk Census Imports"
        indexes = [
            models.Index(fields=["status", "uploaded_at"]),
            models.Index(fields=["uploaded_by", "status"]),
        ]

    def __str__(self):
        return f"Bulk Import: {self.original_filename} ({self.get_status_display()})"

    def get_progress_percentage(self):
        """Get import progress as percentage"""
        if self.total_rows == 0:
            return 0
        return int((self.imported_records / self.total_rows) * 100)

    def can_process(self, user):
        """Check if user can process this import"""
        return (self.status in ["ready", "failed"] and
                user.role in ['ADMIN', 'SUPERADMIN'])

    def mark_as_validating(self):
        """Mark import as being validated"""
        self.status = "validating"
        self.save()

    def mark_validation_failed(self, errors):
        """Mark import as validation failed"""
        self.status = "validation_failed"
        self.validation_errors = errors
        self.save()

    def mark_as_ready(self, preview_data):
        """Mark import as ready for processing"""
        self.status = "ready"
        self.import_preview = preview_data
        self.save()

    def mark_as_importing(self):
        """Mark import as being processed"""
        self.status = "importing"
        self.save()

    def mark_as_completed(self, imported_count):
        """Mark import as completed"""
        from django.utils import timezone
        self.status = "completed"
        self.imported_records = imported_count
        self.processed_at = timezone.now()
        self.save()

    def mark_as_failed(self, error):
        """Mark import as failed"""
        from django.utils import timezone
        self.status = "failed"
        self.error_summary = {"error": str(error)}
        self.processed_at = timezone.now()
        self.save()


def log_census_activity(census, activity_type, description, user=None, old_values=None, new_values=None, request=None):
    """
    Helper function to log census activities.

    Args:
        census: CensusObservation instance
        activity_type: Type of activity (from ACTIVITY_TYPES)
        description: Human-readable description of the activity
        user: User who performed the activity (optional)
        old_values: Previous field values for updates (optional)
        new_values: New field values for updates (optional)
        request: Django request object for IP/user agent (optional)
    """
    log_entry = CensusActivityLog(
        census=census,
        activity_type=activity_type,
        description=description,
        old_values=old_values,
        new_values=new_values,
        performed_by=user
    )

    if request:
        log_entry.ip_address = request.META.get('REMOTE_ADDR')
        log_entry.user_agent = request.META.get('HTTP_USER_AGENT', '')
        log_entry._request = request

    log_entry.save()
