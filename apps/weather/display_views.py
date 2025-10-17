"""
Display views for weather app
"""

from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

# Removed Django admin dependency - using custom role-based permissions
from apps.locations.models import Site
from .models import FieldWorkSchedule, WeatherAlert, WeatherForecast


@login_required
# Removed Django admin decorator - using custom role-based permissions
def alerts_view(request):
    """Weather alerts and warnings view"""
    # Get all alerts
    alerts = WeatherAlert.objects.select_related("sites").order_by("-issued_at")

    # Filter by status
    status_filter = request.GET.get("status", "ALL")
    if status_filter == "ACTIVE":
        alerts = alerts.filter(valid_from__lte=timezone.now(), valid_until__gte=timezone.now())
    elif status_filter == "UPCOMING":
        alerts = alerts.filter(valid_from__gt=timezone.now())
    elif status_filter == "EXPIRED":
        alerts = alerts.filter(valid_until__lt=timezone.now())

    # Pagination
    paginator = Paginator(alerts, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "status_filter": status_filter,
    }

    return render(request, "weather/alerts.html", context)


@login_required
# Removed Django admin decorator - using custom role-based permissions
def forecast_view(request, site_id=None):
    """Weather forecast view for specific site or all sites"""
    if site_id:
        site = get_object_or_404(Site, id=site_id)
        sites = [site]
    else:
        sites = Site.objects.filter(status="active")

    # Get date range (today + 7 days)
    today = timezone.now().date()
    date_range = [(today + timedelta(days=i)) for i in range(7)]

    # Get forecasts for all sites
    forecasts = {}
    for site in sites:
        site_forecasts = WeatherForecast.objects.filter(
            site=site, forecast_date__gte=today, forecast_date__lte=today + timedelta(days=6)
        ).order_by("forecast_date", "forecast_time")

        forecasts[site.id] = {}
        for forecast in site_forecasts:
            date_key = forecast.forecast_date.isoformat()
            if date_key not in forecasts[site.id]:
                forecasts[site.id][date_key] = []
            forecasts[site.id][date_key].append(forecast)

    context = {
        "sites": sites,
        "date_range": date_range,
        "forecasts": forecasts,
        "selected_site": site if site_id else None,
    }

    return render(request, "weather/forecast.html", context)


@login_required
# Removed Django admin decorator - using custom role-based permissions
def schedule_view(request):
    """Field work schedule management"""
    # Get all schedules
    schedules = FieldWorkSchedule.objects.select_related(
        "site", "supervisor", "created_by"
    ).order_by("-planned_date", "-planned_start_time")

    # Filter by status
    status_filter = request.GET.get("status", "ALL")
    if status_filter != "ALL":
        schedules = schedules.filter(status=status_filter)

    # Filter by site
    site_filter = request.GET.get("site")
    if site_filter:
        schedules = schedules.filter(site_id=site_filter)

    # Pagination
    paginator = Paginator(schedules, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Get sites for filter dropdown
    sites = Site.objects.filter(status="active")

    context = {
        "page_obj": page_obj,
        "status_filter": status_filter,
        "site_filter": site_filter,
        "sites": sites,
    }

    return render(request, "weather/schedule.html", context)
