"""
Dashboard views for weather app
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from django.contrib.admin.views.decorators import staff_member_required as staff_required
from apps.locations.models import Site
from .models import FieldWorkSchedule, WeatherAlert, WeatherAPI, WeatherForecast


@login_required
@staff_required
def dashboard(request):
    """Weather dashboard with forecasts and optimization"""
    # Get all active sites
    sites = Site.objects.filter(status="active").order_by("name")

    # Get recent forecasts
    recent_forecasts = WeatherForecast.objects.select_related("site").order_by("-created_at")[:10]

    # Get active alerts
    active_alerts = WeatherAlert.objects.filter(
        valid_from__lte=timezone.now(), valid_until__gte=timezone.now()
    ).prefetch_related("sites").order_by("severity", "-issued_at")[:5]

    # Get upcoming field work schedules
    upcoming_schedules = (
        FieldWorkSchedule.objects.select_related("site", "supervisor", "created_by")
        .filter(planned_date__gte=timezone.now().date())
        .order_by("planned_date", "planned_start_time")[:5]
    )

    context = {
        "sites": sites,
        "recent_forecasts": recent_forecasts,
        "active_alerts": active_alerts,
        "upcoming_schedules": upcoming_schedules,
        "weather_apis": WeatherAPI.choices,
    }

    return render(request, "weather/dashboard.html", context)
