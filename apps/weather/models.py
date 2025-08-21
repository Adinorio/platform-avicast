import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

User = get_user_model()

class WeatherAPI(models.TextChoices):
    """Supported weather APIs"""
    OPENWEATHER = 'OPENWEATHER', 'OpenWeather'
    WEATHERAPI = 'WEATHERAPI', 'WeatherAPI'
    ACCUWEATHER = 'ACCUWEATHER', 'AccuWeather'
    METEO = 'METEO', 'Meteo'

class WeatherCondition(models.TextChoices):
    """Weather condition categories"""
    CLEAR = 'CLEAR', 'Clear'
    CLOUDY = 'CLOUDY', 'Cloudy'
    RAINY = 'RAINY', 'Rainy'
    STORMY = 'STORMY', 'Stormy'
    WINDY = 'WINDY', 'Windy'
    FOGGY = 'FOGGY', 'Foggy'

class TideCondition(models.TextChoices):
    """Tide condition categories"""
    LOW_TIDE = 'LOW_TIDE', 'Low Tide'
    RISING_TIDE = 'RISING_TIDE', 'Rising Tide'
    HIGH_TIDE = 'HIGH_TIDE', 'High Tide'
    FALLING_TIDE = 'FALLING_TIDE', 'Falling Tide'

class FieldWorkRecommendation(models.TextChoices):
    """Field work recommendation levels"""
    EXCELLENT = 'EXCELLENT', 'Excellent'
    GOOD = 'GOOD', 'Good'
    MODERATE = 'MODERATE', 'Moderate'
    POOR = 'POOR', 'Poor'
    NOT_RECOMMENDED = 'NOT_RECOMMENDED', 'Not Recommended'

class WeatherForecast(models.Model):
    """Model for storing weather forecast data"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Location and timing
    site = models.ForeignKey('locations.Site', on_delete=models.CASCADE, related_name='weather_forecasts')
    forecast_date = models.DateField()
    forecast_time = models.TimeField()

    # Weather data
    temperature = models.DecimalField(max_digits=4, decimal_places=1, help_text="Temperature in Celsius")
    humidity = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)], help_text="Humidity percentage")
    wind_speed = models.DecimalField(max_digits=4, decimal_places=1, help_text="Wind speed in km/h")
    wind_direction = models.CharField(max_length=10, help_text="Wind direction (N, S, E, W, NE, etc.)")
    precipitation = models.DecimalField(max_digits=5, decimal_places=2, help_text="Precipitation in mm")
    pressure = models.DecimalField(max_digits=6, decimal_places=2, help_text="Atmospheric pressure in hPa")

    # Condition classifications
    weather_condition = models.CharField(max_length=20, choices=WeatherCondition.choices)
    visibility = models.DecimalField(max_digits=4, decimal_places=1, help_text="Visibility in km")

    # Tide information (for coastal sites)
    tide_condition = models.CharField(max_length=20, choices=TideCondition.choices, null=True, blank=True)
    tide_height = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True, help_text="Tide height in meters")

    # API source and data
    api_source = models.CharField(max_length=20, choices=WeatherAPI.choices)
    api_response_data = models.JSONField(default=dict, blank=True)  # Store raw API response
    last_updated = models.DateTimeField(auto_now=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['forecast_date', 'forecast_time']
        verbose_name = 'Weather Forecast'
        verbose_name_plural = 'Weather Forecasts'
        unique_together = ['site', 'forecast_date', 'forecast_time']
        indexes = [
            models.Index(fields=['site', 'forecast_date']),
            models.Index(fields=['forecast_date', 'weather_condition']),
            models.Index(fields=['api_source', 'created_at']),
        ]

    def __str__(self):
        return f"{self.site.name} - {self.forecast_date} {self.forecast_time}"

    @property
    def is_coastal_site(self):
        """Check if this is a coastal site with tide data"""
        return self.site.site_type == 'coastal'

    @property
    def field_work_score(self):
        """Calculate field work suitability score (0-100)"""
        score = 100
        
        # Temperature penalty (ideal: 15-25°C)
        if self.temperature < 10 or self.temperature > 30:
            score -= 20
        elif self.temperature < 15 or self.temperature > 25:
            score -= 10
        
        # Humidity penalty (ideal: 40-70%)
        if self.humidity > 80 or self.humidity < 30:
            score -= 15
        elif self.humidity > 70 or self.humidity < 40:
            score -= 5
        
        # Wind penalty (ideal: < 20 km/h)
        if self.wind_speed > 30:
            score -= 25
        elif self.wind_speed > 20:
            score -= 15
        
        # Precipitation penalty
        if self.precipitation > 5:
            score -= 30
        elif self.precipitation > 2:
            score -= 15
        
        # Visibility penalty
        if self.visibility < 5:
            score -= 20
        elif self.visibility < 10:
            score -= 10
        
        # Tide penalty for coastal sites
        if self.is_coastal_site and self.tide_condition:
            if self.tide_condition in [self.TideCondition.HIGH_TIDE, self.TideCondition.LOW_TIDE]:
                score -= 10
        
        return max(0, score)

    @property
    def field_work_recommendation(self):
        """Get field work recommendation based on score"""
        score = self.field_work_score
        if score >= 80:
            return self.FieldWorkRecommendation.EXCELLENT
        elif score >= 60:
            return self.FieldWorkRecommendation.GOOD
        elif score >= 40:
            return self.FieldWorkRecommendation.MODERATE
        elif score >= 20:
            return self.FieldWorkRecommendation.POOR
        else:
            return self.FieldWorkRecommendation.NOT_RECOMMENDED

class FieldWorkSchedule(models.Model):
    """Model for scheduling and optimizing field work"""
    
    class ScheduleStatus(models.TextChoices):
        PLANNED = 'PLANNED', 'Planned'
        CONFIRMED = 'CONFIRMED', 'Confirmed'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'
        POSTPONED = 'POSTPONED', 'Postponed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Schedule details
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    site = models.ForeignKey('locations.Site', on_delete=models.CASCADE, related_name='field_work_schedules')
    
    # Timing
    planned_date = models.DateField()
    planned_start_time = models.TimeField()
    planned_end_time = models.TimeField()
    actual_start_time = models.TimeField(null=True, blank=True)
    actual_end_time = models.TimeField(null=True, blank=True)
    
    # Personnel
    assigned_personnel = models.ManyToManyField(User, related_name='assigned_field_work')
    supervisor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='supervised_field_work')
    
    # Status and optimization
    status = models.CharField(max_length=20, choices=ScheduleStatus.choices, default=ScheduleStatus.PLANNED)
    weather_score = models.IntegerField(null=True, blank=True, help_text="Weather suitability score (0-100)")
    weather_recommendation = models.CharField(max_length=20, choices=FieldWorkRecommendation.choices, null=True, blank=True)
    
    # Notes and results
    planning_notes = models.TextField(blank=True)
    execution_notes = models.TextField(blank=True)
    results_summary = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_field_work')
    
    class Meta:
        ordering = ['planned_date', 'planned_start_time']
        verbose_name = 'Field Work Schedule'
        verbose_name_plural = 'Field Work Schedules'
        indexes = [
            models.Index(fields=['site', 'planned_date']),
            models.Index(fields=['status', 'planned_date']),
            # Removed invalid index on ManyToMany field 'assigned_personnel'
        ]

    def __str__(self):
        return f"{self.title} - {self.site.name} - {self.planned_date}"

    def update_weather_optimization(self, weather_forecast):
        """Update weather optimization data based on forecast"""
        self.weather_score = weather_forecast.field_work_score
        self.weather_recommendation = weather_forecast.field_work_recommendation
        self.save(update_fields=['weather_score', 'weather_recommendation'])

    def start_field_work(self):
        """Mark field work as started"""
        self.status = self.ScheduleStatus.IN_PROGRESS
        self.actual_start_time = timezone.now().time()
        self.save(update_fields=['status', 'actual_start_time'])

    def complete_field_work(self):
        """Mark field work as completed"""
        self.status = self.ScheduleStatus.COMPLETED
        self.actual_end_time = timezone.now().time()
        self.save(update_fields=['status', 'actual_end_time'])

    def postpone_field_work(self, new_date, reason=""):
        """Postpone field work to a new date"""
        self.status = self.ScheduleStatus.POSTPONED
        self.planned_date = new_date
        self.planning_notes += f"\n[POSTPONED] {reason}"
        self.save(update_fields=['status', 'planned_date', 'planning_notes'])

    @property
    def is_optimized(self):
        """Check if field work is optimized for weather conditions"""
        return self.weather_recommendation in [
            self.FieldWorkRecommendation.EXCELLENT,
            self.FieldWorkRecommendation.GOOD
        ]

    @property
    def duration_hours(self):
        """Calculate planned duration in hours"""
        if self.planned_start_time and self.planned_end_time:
            start = self.planned_start_time
            end = self.planned_end_time
            return (end.hour - start.hour) + (end.minute - start.minute) / 60
        return 0

class WeatherAlert(models.Model):
    """Model for weather alerts and warnings"""
    
    class AlertSeverity(models.TextChoices):
        LOW = 'LOW', 'Low'
        MEDIUM = 'MEDIUM', 'Medium'
        HIGH = 'HIGH', 'High'
        CRITICAL = 'CRITICAL', 'Critical'

    class AlertType(models.TextChoices):
        WEATHER = 'WEATHER', 'Weather'
        TIDE = 'TIDE', 'Tide'
        WIND = 'WIND', 'Wind'
        VISIBILITY = 'VISIBILITY', 'Visibility'
        GENERAL = 'GENERAL', 'General'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Alert details
    title = models.CharField(max_length=200)
    description = models.TextField()
    alert_type = models.CharField(max_length=20, choices=AlertType.choices)
    severity = models.CharField(max_length=20, choices=AlertSeverity.choices)
    
    # Affected areas
    sites = models.ManyToManyField('locations.Site', related_name='weather_alerts')
    
    # Timing
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    issued_at = models.DateTimeField(auto_now_add=True)
    
    # Source and metadata
    source = models.CharField(max_length=50, blank=True)
    external_id = models.CharField(max_length=100, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-issued_at', 'severity']
        verbose_name = 'Weather Alert'
        verbose_name_plural = 'Weather Alerts'
        indexes = [
            models.Index(fields=['alert_type', 'severity']),
            models.Index(fields=['valid_from', 'valid_until']),
            # Removed invalid index on ManyToMany field 'sites'
        ]

    def __str__(self):
        return f"{self.title} - {self.severity} - {self.alert_type}"

    @property
    def is_active(self):
        """Check if alert is currently active"""
        now = timezone.now()
        return self.valid_from <= now <= self.valid_until

    @property
    def affects_field_work(self):
        """Check if alert affects field work scheduling"""
        return self.severity in [self.AlertSeverity.HIGH, self.AlertSeverity.CRITICAL]
