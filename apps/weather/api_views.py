"""
API views for weather app
"""

import json
import logging
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.image_processing.permissions import staff_required
from apps.locations.models import Site
from .models import FieldWorkSchedule, WeatherForecast
from .weather_service import get_field_work_optimizer, get_weather_service

logger = logging.getLogger(__name__)


@login_required
@staff_required
@csrf_exempt
@require_http_methods(["POST"])
def fetch_weather(request):
    """AJAX endpoint to fetch weather data for a site"""

    try:
        data = json.loads(request.body)
        site_id = data.get("site_id")
        api_source = data.get("api_source", "METEO")

        site = get_object_or_404(Site, id=site_id)

        # Get coordinates
        if not site.coordinates:
            return JsonResponse({"error": "Site coordinates not available"})

        try:
            lat, lon = map(float, site.coordinates.split(","))
        except ValueError:
            return JsonResponse({"error": "Invalid coordinates format"})

        # Fetch weather data
        weather_service = get_weather_service(api_source)
        weather_data = weather_service.fetch_weather_data(lat, lon, days=3)

        if weather_data:
            # Save current weather
            current = weather_data.get("current", {})
            if current:
                WeatherForecast.objects.update_or_create(
                    site=site,
                    forecast_date=timezone.now().date(),
                    forecast_time=timezone.now().time().replace(second=0, microsecond=0),
                    defaults={
                        "temperature": current.get("temperature", 20.0),
                        "humidity": current.get("humidity", 60),
                        "wind_speed": current.get("wind_speed", 10.0),
                        "wind_direction": current.get("wind_direction", "N"),
                        "precipitation": current.get("precipitation", 0.0),
                        "pressure": current.get("pressure", 1013.0),
                        "weather_condition": current.get("weather_condition", "CLEAR"),
                        "visibility": current.get("visibility", 10.0),
                        "api_source": api_source,
                        "api_response_data": weather_data.get("raw_response", {}),
                    },
                )

            return JsonResponse(
                {
                    "success": True,
                    "message": f"Weather data fetched successfully from {api_source}",
                    "data": weather_data,
                }
            )

        else:
            return JsonResponse({"error": "Failed to fetch weather data"})

    except Exception as e:
        logger.error(f"Weather fetch error: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)


@login_required
@staff_required
@csrf_exempt
@require_http_methods(["POST"])
def optimize_field_work(request):
    """AJAX endpoint to optimize field work schedule"""

    try:
        data = json.loads(request.body)
        site_id = data.get("site_id")
        planned_date = data.get("planned_date")
        planned_time = data.get("planned_time")

        site = get_object_or_404(Site, id=site_id)

        # Parse date and time
        planned_date = datetime.strptime(planned_date, "%Y-%m-%d").date()
        planned_time = datetime.strptime(planned_time, "%H:%M").time()

        # Get optimization service
        optimizer = get_field_work_optimizer()
        optimization = optimizer.optimize_schedule(site, planned_date, planned_time)

        return JsonResponse({"success": True, "optimization": optimization})

    except Exception as e:
        logger.error(f"Field work optimization error: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)


@login_required
@staff_required
@csrf_exempt
@require_http_methods(["POST"])
def create_schedule(request):
    """Create new field work schedule"""

    try:
        data = json.loads(request.body)

        site = get_object_or_404(Site, id=data["site_id"])

        # Create schedule
        schedule = FieldWorkSchedule.objects.create(
            title=data["title"],
            description=data.get("description", ""),
            site=site,
            planned_date=datetime.strptime(data["planned_date"], "%Y-%m-%d").date(),
            planned_start_time=datetime.strptime(data["start_time"], "%H:%M").time(),
            planned_end_time=datetime.strptime(data["end_time"], "%H:%M").time(),
            supervisor_id=data.get("supervisor_id"),
            created_by=request.user,
        )

        return JsonResponse(
            {
                "success": True,
                "message": "Schedule created successfully",
                "schedule_id": str(schedule.id),
            }
        )

    except Exception as e:
        logger.error(f"Schedule creation error: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)
