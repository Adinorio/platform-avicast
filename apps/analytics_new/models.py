"""
New Analytics Models for AVICAST
Focused on 6 target bird species for CENRO monitoring
"""

import uuid
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

User = get_user_model()


class SpeciesAnalytics(models.Model):
    """Computed analytics for any species (reads from fauna.Species)"""

    # Link to actual species data
    species = models.OneToOneField(
        "fauna.Species",
        on_delete=models.CASCADE,
        related_name="analytics",
        help_text="Link to main species record"
    )

    # Computed population data (updated by management commands)
    total_count = models.PositiveIntegerField(default=0, help_text="Total count across all sites")
    sites_with_presence = models.PositiveIntegerField(default=0, help_text="Number of sites where this species is present")
    last_observation_date = models.DateField(null=True, blank=True, help_text="Most recent observation date")

    # Geographic distribution (computed from census data)
    primary_habitats = models.JSONField(default=list, help_text="List of primary habitat types")
    site_distribution = models.JSONField(default=dict, help_text="Count by site")

    # Population trends (computed over time)
    population_trend = models.CharField(max_length=20, default="STABLE", help_text="Population trend")
    trend_confidence = models.DecimalField(max_digits=3, decimal_places=2, default=0.5, help_text="Confidence in trend analysis")

    # Analytics metadata
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["species__name"]
        verbose_name = "Species Analytics"
        verbose_name_plural = "Species Analytics"

    def __str__(self):
        return f"{self.species.name} Analytics"

    def get_target_species(self):
        """Get target egret species for CENRO monitoring"""
        target_names = ["egret", "heron"]  # Can be expanded
        return any(name.lower() in self.species.name.lower() for name in target_names)

    def update_from_census_data(self):
        """Update analytics from census observations"""
        from django.db.models import Sum, Count
        from apps.locations.models import CensusObservation

        # Get all observations for this species
        observations = CensusObservation.objects.filter(species=self.species)

        # Calculate totals
        self.total_count = observations.aggregate(total=Sum('count'))['total'] or 0
        self.sites_with_presence = observations.values('census__month__year__site').distinct().count()

        # Get most recent observation
        recent_obs = observations.order_by('-census__census_date').first()
        if recent_obs:
            self.last_observation_date = recent_obs.census.census_date

        # Calculate site distribution
        site_data = {}
        for obs in observations:
            site_name = obs.census.month.year.site.name
            site_data[site_name] = site_data.get(site_name, 0) + obs.count
        self.site_distribution = site_data

        self.save()

    def update_count(self, new_count):
        """Update total count and last updated timestamp"""
        self.total_count = new_count
        self.last_updated = timezone.now()
        self.save(update_fields=["total_count", "last_updated"])


# class SiteAnalytics(models.Model):  # Temporarily disabled during locations revamp
#     """Computed analytics for observation sites (reads from locations.Site)"""
#
#     # Link to actual site data
#     site = models.OneToOneField(
#         "locations.Site",
#         on_delete=models.CASCADE,
#         related_name="analytics",
#         help_text="Link to main site record"
#     )

    # Computed bird population data
    total_birds_recorded = models.PositiveIntegerField(default=0, help_text="Total birds recorded at this site")
    species_diversity = models.PositiveIntegerField(default=0, help_text="Number of different species recorded")
    target_species_count = models.PositiveIntegerField(default=0, help_text="Number of target species present")

    # Species composition (computed from census data)
    dominant_species = models.CharField(max_length=200, blank=True, help_text="Most abundant species")
    species_composition = models.JSONField(default=dict, help_text="Species distribution by count")

    # Monitoring analytics
    total_census_observations = models.PositiveIntegerField(default=0, help_text="Total census observations")
    last_survey_date = models.DateField(null=True, blank=True, help_text="Most recent survey date")
    survey_frequency_days = models.PositiveIntegerField(default=30, help_text="Average days between surveys")

    # Environmental trends (computed from census data)
    avg_temperature = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    avg_humidity = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    # Analytics metadata
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["site__name"]
        verbose_name = "Site Analytics"
        verbose_name_plural = "Site Analytics"

    def __str__(self):
        return f"{self.site.name} Analytics"

    def update_from_census_data(self):
        """Update analytics from census observations"""
        from django.db.models import Sum, Count, Avg
        from apps.locations.models import CensusObservation, SpeciesObservation

        # Get all census observations for this site
        census_observations = CensusObservation.objects.filter(site=self.site)

        if not census_observations.exists():
            return

        # Calculate totals
        species_observations = SpeciesObservation.objects.filter(census__site=self.site)
        self.total_birds_recorded = species_observations.aggregate(total=Sum('count'))['total'] or 0
        self.species_diversity = species_observations.values('species').distinct().count()
        self.total_census_observations = census_observations.count()

        # Get most recent survey
        recent_census = census_observations.order_by('-observation_date').first()
        if recent_census:
            self.last_survey_date = recent_census.observation_date

        # Calculate species composition
        species_data = {}
        for obs in species_observations:
            species_name = obs.species.name if obs.species else obs.species_name
            species_data[species_name] = species_data.get(species_name, 0) + obs.count

        if species_data:
            self.dominant_species = max(species_data.items(), key=lambda x: x[1])[0]
            self.species_composition = species_data

        # Calculate environmental averages
        if census_observations:
            # Note: Weather data would need to be added to CensusObservation
            # For now, we'll skip environmental calculations
            pass

        self.save()


# class CensusAnalytics(models.Model):  # Temporarily disabled during locations revamp
#     """Computed analytics for census observations (reads from locations.CensusObservation)"""
#
#     # Link to actual census data
#     census_observation = models.OneToOneField(
#         "locations.CensusObservation",
#         on_delete=models.CASCADE,
#         related_name="analytics",
#         help_text="Link to main census observation"
#     )

    # Computed totals and analytics
    total_birds = models.PositiveIntegerField(default=0, help_text="Total birds observed")
    species_richness = models.PositiveIntegerField(default=0, help_text="Number of different species")
    dominant_species = models.CharField(max_length=200, blank=True, help_text="Most abundant species")

    # Species breakdown (computed from SpeciesObservation)
    species_breakdown = models.JSONField(default=dict, help_text="Count by species")

    # Data quality and verification
    data_quality_score = models.DecimalField(max_digits=3, decimal_places=2, default=1.0, help_text="Data quality score")
    verification_status = models.CharField(max_length=20, default="PENDING", help_text="Verification status")

    # Analytics metadata
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # ordering = ["-census_observation__observation_date"]  # Temporarily disabled during locations revamp
        verbose_name = "Census Analytics"
        verbose_name_plural = "Census Analytics"

    # def __str__(self):  # Temporarily disabled during locations revamp
    #     return f"Census Analytics - {self.census_observation.observation_date}"

    # def update_from_species_observations(self):  # Temporarily disabled during locations revamp
    #     """Update analytics from associated SpeciesObservation records"""
    #     from apps.locations.models import SpeciesObservation

        # Get all species observations for this census (temporarily disabled during locations revamp)
        # species_observations = SpeciesObservation.objects.filter(census=self.census_observation)
        #
        # if not species_observations.exists():
        #     return
        #
        # # Calculate totals
        # self.total_birds = species_observations.aggregate(total=Sum('count'))['total'] or 0
        # self.species_richness = species_observations.count()
        #
        # # Calculate species breakdown
        # species_data = {}
        # for obs in species_observations:
        #     species_name = obs.species.name if obs.species else obs.species_name
        #     species_data[species_name] = obs.count
        #
        # if species_data:
        #     self.dominant_species = max(species_data.items(), key=lambda x: x[1])[0]
        #     self.species_breakdown = species_data
        #
        # # Calculate data quality (basic implementation)
        # # Could be enhanced with more sophisticated quality metrics
        # self.data_quality_score = min(1.0, self.species_richness / 10.0)  # Simple heuristic
        #
        # self.save()


class PopulationTrend(models.Model):
    """Population trend analysis for species (computed from census data)"""

    # Link to species being analyzed
    species_analytics = models.ForeignKey(
        SpeciesAnalytics,
        on_delete=models.CASCADE,
        related_name="population_trends"
    )

    # Trend period
    period_start = models.DateField()
    period_end = models.DateField()
    period_length_days = models.PositiveIntegerField()

    # Population metrics (computed from census data)
    average_count = models.DecimalField(max_digits=10, decimal_places=2)
    peak_count = models.PositiveIntegerField()
    minimum_count = models.PositiveIntegerField()

    # Trend analysis results
    trend_direction = models.CharField(max_length=20, help_text="INCREASING, DECREASING, STABLE, FLUCTUATING")
    trend_strength = models.CharField(max_length=20, help_text="STRONG, MODERATE, WEAK")
    confidence_level = models.DecimalField(max_digits=5, decimal_places=2, help_text="0.0 to 1.0")

    # Statistical data
    standard_deviation = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    coefficient_variation = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    sample_size = models.PositiveIntegerField()

    # Environmental correlations (computed from census weather data)
    correlated_factors = models.JSONField(default=list, help_text="Environmental factors that correlate with population")
    seasonal_pattern = models.CharField(max_length=100, blank=True)

    # Analysis metadata
    analysis_date = models.DateTimeField(auto_now_add=True)
    analyzed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    methodology = models.TextField(blank=True, help_text="Analysis methodology description")
    data_sources = models.JSONField(default=list, help_text="List of census observations used")

    class Meta:
        ordering = ["-analysis_date"]
        unique_together = ["species_analytics", "period_start", "period_end"]
        verbose_name = "Population Trend"
        verbose_name_plural = "Population Trends"

    def __str__(self):
        return f"{self.species_analytics.species.name} Trend ({self.period_start} to {self.period_end})"

    def calculate_trend_from_census_data(self):
        """Calculate population trend from historical census data"""
        from apps.locations.models import CensusObservation
        from datetime import timedelta

        # Get species observations within the period
        observations = CensusObservation.objects.filter(
            species=self.species_analytics.species,
            census__census_date__gte=self.period_start,
            census__census_date__lte=self.period_end
        )

        if not observations.exists():
            return False

        # Calculate basic statistics
        counts = [obs.count for obs in observations]
        self.sample_size = len(counts)
        self.average_count = sum(counts) / len(counts)
        self.peak_count = max(counts)
        self.minimum_count = min(counts)

        # Calculate standard deviation
        if len(counts) > 1:
            mean = self.average_count
            variance = sum((x - mean) ** 2 for x in counts) / (len(counts) - 1)
            self.standard_deviation = variance ** 0.5
            self.coefficient_variation = (self.standard_deviation / mean) if mean > 0 else 0

        # Simple trend analysis (could be enhanced with more sophisticated methods)
        if len(counts) >= 3:
            first_half = counts[:len(counts)//2]
            second_half = counts[len(counts)//2:]

            first_avg = sum(first_half) / len(first_half)
            second_avg = sum(second_half) / len(second_half)

            change_ratio = second_avg / first_avg if first_avg > 0 else 1

            if change_ratio > 1.2:
                self.trend_direction = "INCREASING"
                self.trend_strength = "MODERATE" if change_ratio < 2 else "STRONG"
            elif change_ratio < 0.8:
                self.trend_direction = "DECREASING"
                self.trend_strength = "MODERATE" if change_ratio > 0.5 else "STRONG"
            else:
                self.trend_direction = "STABLE"

            # Confidence based on sample size and consistency
            self.confidence_level = min(0.95, len(counts) / 20.0)
        else:
            self.trend_direction = "INSUFFICIENT_DATA"
            self.confidence_level = 0.1

        # Store data sources
        self.data_sources = [
            {
                'census_id': str(obs.census.id),
                'date': obs.census.census_date.isoformat(),
                'count': obs.count,
                'site': obs.census.month.year.site.name
            }
            for obs in observations
        ]

        return True


class ReportConfiguration(models.Model):
    """Configuration for generating analytics reports"""

    REPORT_TYPES = [
        ("SPECIES_SUMMARY", "Species Summary Report"),
        ("SITE_COMPARISON", "Site Comparison Report"),
        ("POPULATION_TRENDS", "Population Trends Report"),
        ("CONSERVATION_STATUS", "Conservation Status Report"),
        ("MONTHLY_SUMMARY", "Monthly Summary Report"),
        ("ANNUAL_REVIEW", "Annual Review Report"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=30, choices=REPORT_TYPES)
    description = models.TextField(blank=True)

    # Report parameters
    include_species = models.JSONField(default=list, help_text="List of species to include")
    include_sites = models.JSONField(default=list, help_text="List of sites to include")
    date_range_start = models.DateField(null=True, blank=True)
    date_range_end = models.DateField(null=True, blank=True)

    # Output format
    output_format = models.CharField(max_length=10, default="HTML", help_text="HTML, PDF, EXCEL")
    include_charts = models.BooleanField(default=True)
    include_maps = models.BooleanField(default=True)
    include_raw_data = models.BooleanField(default=False)

    # Scheduling
    is_scheduled = models.BooleanField(default=False)
    schedule_frequency = models.CharField(max_length=20, blank=True, help_text="DAILY, WEEKLY, MONTHLY")
    next_generation = models.DateTimeField(null=True, blank=True)

    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Report Configuration"
        verbose_name_plural = "Report Configurations"

    def __str__(self):
        return f"{self.name} ({self.get_report_type_display()})"


class GeneratedReport(models.Model):
    """Records of generated analytics reports"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    configuration = models.ForeignKey(ReportConfiguration, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)

    # Generation details
    generation_date = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    file_path = models.CharField(max_length=500, blank=True)
    file_size_bytes = models.PositiveIntegerField(null=True, blank=True)

    # Report content summary
    species_included = models.JSONField(default=list)
    sites_included = models.JSONField(default=list)
    total_records = models.PositiveIntegerField(default=0)
    date_range = models.CharField(max_length=100, blank=True)
    output_format = models.CharField(max_length=10, default="HTML", help_text="HTML, PDF, EXCEL")

    # Status
    status = models.CharField(max_length=20, default="GENERATING")
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ["-generation_date"]
        verbose_name = "Generated Report"
        verbose_name_plural = "Generated Reports"

    def __str__(self):
        return f"{self.title} - {self.generation_date.strftime('%Y-%m-%d')}"
