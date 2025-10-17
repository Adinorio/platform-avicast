"""
API views for weather app
"""

import json
import logging
from datetime import datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

# Removed Django admin dependency - using custom role-based permissions
from apps.locations.models import Site
from .models import FieldWorkSchedule, WeatherForecast
from .weather_service import get_field_work_optimizer, get_weather_service

logger = logging.getLogger(__name__)


def _parse_coordinates(coord_str):
    """Parse coordinates from various formats to decimal degrees.
    
    Supports:
    - Decimal degrees: "11.0425, 123.2011"
    - DMS format: "11°2′33″N, 123°12′4″E"
    - Mixed formats
    """
    import re
    
    coord_str = coord_str.strip()
    
    # Try decimal degrees first (simple case)
    if ',' in coord_str and '°' not in coord_str:
        try:
            parts = coord_str.split(',')
            if len(parts) == 2:
                lat = float(parts[0].strip())
                lon = float(parts[1].strip())
                return lat, lon
        except ValueError:
            pass
    
    # Parse DMS format: "11°2′33″N, 123°12′4″E"
    dms_pattern = r'(\d+)°(\d+)[′\'](\d+)[″"]([NSEW]),?\s*(\d+)°(\d+)[′\'](\d+)[″"]([NSEW])'
    match = re.search(dms_pattern, coord_str)
    
    if match:
        lat_deg, lat_min, lat_sec, lat_dir = int(match.group(1)), int(match.group(2)), int(match.group(3)), match.group(4)
        lon_deg, lon_min, lon_sec, lon_dir = int(match.group(5)), int(match.group(6)), int(match.group(7)), match.group(8)
        
        # Convert to decimal degrees
        lat_decimal = lat_deg + lat_min/60 + lat_sec/3600
        lon_decimal = lon_deg + lon_min/60 + lon_sec/3600
        
        # Apply direction
        if lat_dir == 'S':
            lat_decimal = -lat_decimal
        if lon_dir == 'W':
            lon_decimal = -lon_decimal
            
        return lat_decimal, lon_decimal
    
    # Try simpler DMS patterns
    simple_patterns = [
        r'(\d+)°(\d+)[′\']([NSEW]),?\s*(\d+)°(\d+)[′\']([NSEW])',  # Without seconds
        r'(\d+)°([NSEW]),?\s*(\d+)°([NSEW])',  # Degrees only
    ]
    
    for pattern in simple_patterns:
        match = re.search(pattern, coord_str)
        if match:
            groups = match.groups()
            if len(groups) == 6:  # With minutes
                lat_deg, lat_min, lat_dir, lon_deg, lon_min, lon_dir = groups
                lat_decimal = int(lat_deg) + int(lat_min)/60
                lon_decimal = int(lon_deg) + int(lon_min)/60
            else:  # Degrees only
                lat_deg, lat_dir, lon_deg, lon_dir = groups
                lat_decimal = int(lat_deg)
                lon_decimal = int(lon_deg)
            
            if lat_dir == 'S':
                lat_decimal = -lat_decimal
            if lon_dir == 'W':
                lon_decimal = -lon_decimal
                
            return lat_decimal, lon_decimal
    
    raise ValueError(f"Unable to parse coordinates: {coord_str}")


@login_required
# Removed Django admin decorator - using custom role-based permissions
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
            lat, lon = _parse_coordinates(site.coordinates)
        except ValueError as e:
            return JsonResponse({"error": f"Invalid coordinates format: {str(e)}"})

        # Fetch weather data for 16 days (Open-Meteo maximum)
        weather_service = get_weather_service(api_source)
        weather_data = weather_service.fetch_weather_data(lat, lon, days=16)

        if weather_data:
            # Save hourly forecast data (all available hours)
            # This includes current weather as the first hour, so we don't need separate current weather saving
            forecast_items = weather_data.get("forecast", [])
            saved_count = 0
            
            for item in forecast_items:
                dt_str = item.get("datetime")
                if not dt_str:
                    continue
                try:
                    # Expecting ISO8601 like "YYYY-MM-DDTHH:MM"
                    dt_obj = datetime.fromisoformat(dt_str)
                except ValueError:
                    # Fallback to common format
                    dt_obj = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")

                WeatherForecast.objects.update_or_create(
                    site=site,
                    forecast_date=dt_obj.date(),
                    forecast_time=dt_obj.time().replace(second=0, microsecond=0),
                    defaults={
                        "temperature": item.get("temperature"),
                        "humidity": item.get("humidity"),
                        "wind_speed": item.get("wind_speed"),
                        "wind_direction": item.get("wind_direction") or "N",
                        "precipitation": item.get("precipitation") or 0.0,
                        "precipitation_probability": item.get("precipitation_probability"),
                        "pressure": item.get("pressure"),
                        "weather_code": item.get("weather_code"),
                        "cloud_cover": item.get("cloud_cover"),
                        "weather_condition": item.get("weather_condition") or "CLEAR",
                        "visibility": item.get("visibility"),
                        "api_source": api_source,
                        "api_response_data": {},
                    },
                )
                saved_count += 1

            return JsonResponse(
                {
                    "success": True,
                    "message": f"Weather data fetched successfully from {api_source}. Saved {saved_count} forecast records.",
                    "data": weather_data,
                }
            )

        else:
            return JsonResponse({"error": "Failed to fetch weather data"})

    except Exception as e:
        logger.error(f"Weather fetch error: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)


@login_required
# Removed Django admin decorator - using custom role-based permissions
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
# Removed Django admin decorator - using custom role-based permissions
@csrf_exempt
@require_http_methods(["POST"])
def best_days(request):
    """Compute best field work days for the next period using Open-Meteo data.

    Request JSON:
      - site_id (required)
      - days (optional, default 30)
    Response: { success, period_days, best_days: [ { date, score_mean, score_max } ] }
    """
    try:
        data = json.loads(request.body)
        site_id = data.get("site_id")
        period_days = int(data.get("days", 30))

        site = get_object_or_404(Site, id=site_id)
        
        if not site.coordinates:
            return JsonResponse({"error": "Site coordinates not available"}, status=400)

        try:
            lat, lon = _parse_coordinates(site.coordinates)
        except ValueError as e:
            return JsonResponse({"error": f"Invalid coordinates format: {str(e)}"}, status=400)

        # Fetch forecast (Open-Meteo supports up to 16 days)
        weather_service = get_weather_service("METEO")
        weather_data = weather_service.fetch_weather_data(lat, lon, days=min(period_days, 16))
        if not weather_data:
            return JsonResponse({"error": "Failed to fetch weather data"}, status=502)

        forecast = weather_data.get("forecast", [])
        daily_info = {d["date"]: d for d in weather_data.get("daily", [])}

        # Score per day using FieldWorkOptimizationService
        optimizer = get_field_work_optimizer()
        scores_by_date = {}
        counts_by_date = {}

        for item in forecast:
            dt_str = item.get("datetime")
            if not dt_str:
                continue
            try:
                dt_obj = datetime.fromisoformat(dt_str)
            except ValueError:
                continue

            date_key = dt_obj.date().isoformat()

            # Restrict to daylight hours if sunrise/sunset available
            allow = True
            day_meta = daily_info.get(date_key)
            if day_meta and day_meta.get("sunrise") and day_meta.get("sunset"):
                try:
                    sr = datetime.fromisoformat(day_meta["sunrise"]).time()
                    ss = datetime.fromisoformat(day_meta["sunset"]).time()
                    t = dt_obj.time()
                    allow = sr <= t <= ss
                except Exception:
                    allow = True
            else:
                # Fallback: 06:00-18:00 window
                t = dt_obj.time()
                allow = (6 <= t.hour <= 18)

            if not allow:
                continue

            score = optimizer.calculate_field_work_score(
                {
                    "temperature": item.get("temperature"),
                    "humidity": item.get("humidity"),
                    "wind_speed": item.get("wind_speed"),
                    "precipitation": item.get("precipitation"),
                    "visibility": item.get("visibility"),
                }
            )

            scores_by_date.setdefault(date_key, {"sum": 0, "max": 0})
            counts_by_date[date_key] = counts_by_date.get(date_key, 0) + 1
            scores_by_date[date_key]["sum"] += score
            if score > scores_by_date[date_key]["max"]:
                scores_by_date[date_key]["max"] = score

        results = []
        for date_key, agg in scores_by_date.items():
            cnt = counts_by_date.get(date_key, 1)
            results.append(
                {
                    "date": date_key,
                    "score_mean": round(agg["sum"] / cnt, 1),
                    "score_max": agg["max"],
                }
            )

        results.sort(key=lambda x: (x["score_mean"], x["score_max"]), reverse=True)

        return JsonResponse({
            "success": True,
            "period_days": period_days,
            "best_days": results[:10],
        })

    except Exception as e:
        logger.error(f"Best days error: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)


@login_required
# Removed Django admin decorator - using custom role-based permissions
@csrf_exempt
@require_http_methods(["POST"])
def daily_summary(request):
    """Get daily weather summary for a site (today, tomorrow, etc.)"""
    try:
        data = json.loads(request.body)
        site_id = data.get("site_id")
        days = int(data.get("days", 7))  # Default to 7 days

        site = get_object_or_404(Site, id=site_id)
        
        # Get forecasts for the site
        forecasts = WeatherForecast.objects.filter(
            site=site,
            forecast_date__gte=timezone.now().date(),
            forecast_date__lte=timezone.now().date() + timedelta(days=days-1)
        ).order_by("forecast_date", "forecast_time")

        # Group by date and calculate daily summaries
        daily_summaries = {}
        optimizer = get_field_work_optimizer()
        
        for forecast in forecasts:
            date_key = forecast.forecast_date.isoformat()
            
            if date_key not in daily_summaries:
                daily_summaries[date_key] = {
                    "date": date_key,
                    "day_name": forecast.forecast_date.strftime("%A"),
                    "temperatures": [],
                    "humidities": [],
                    "wind_speeds": [],
                    "precipitations": [],
                    "visibilities": [],
                    "weather_conditions": [],
                    "scores": [],
                    "hours": []
                }
            
            # Collect hourly data
            daily_summaries[date_key]["temperatures"].append(float(forecast.temperature))
            daily_summaries[date_key]["humidities"].append(forecast.humidity)
            daily_summaries[date_key]["wind_speeds"].append(float(forecast.wind_speed))
            daily_summaries[date_key]["precipitations"].append(float(forecast.precipitation))
            daily_summaries[date_key]["visibilities"].append(float(forecast.visibility))
            daily_summaries[date_key]["weather_conditions"].append(forecast.weather_condition)
            daily_summaries[date_key]["hours"].append(forecast.forecast_time.strftime("%H:%M"))
            
            # Calculate field work score for this hour
            score = optimizer.calculate_field_work_score({
                "temperature": forecast.temperature,
                "humidity": forecast.humidity,
                "wind_speed": forecast.wind_speed,
                "precipitation": forecast.precipitation,
                "visibility": forecast.visibility,
            })
            daily_summaries[date_key]["scores"].append(score)

        # Calculate daily averages and recommendations
        result = []
        for date_key, data in daily_summaries.items():
            if data["temperatures"]:  # Only include days with data
                avg_temp = sum(data["temperatures"]) / len(data["temperatures"])
                avg_humidity = sum(data["humidities"]) / len(data["humidities"])
                avg_wind = sum(data["wind_speeds"]) / len(data["wind_speeds"])
                total_precip = sum(data["precipitations"])
                avg_visibility = sum(data["visibilities"]) / len(data["visibilities"])
                avg_score = sum(data["scores"]) / len(data["scores"])
                max_score = max(data["scores"])
                
                # Most common weather condition
                weather_counts = {}
                for condition in data["weather_conditions"]:
                    weather_counts[condition] = weather_counts.get(condition, 0) + 1
                dominant_weather = max(weather_counts.items(), key=lambda x: x[1])[0]
                
                result.append({
                    "date": date_key,
                    "day_name": data["day_name"],
                    "temperature_avg": round(avg_temp, 1),
                    "temperature_min": round(min(data["temperatures"]), 1),
                    "temperature_max": round(max(data["temperatures"]), 1),
                    "humidity_avg": round(avg_humidity),
                    "wind_speed_avg": round(avg_wind, 1),
                    "precipitation_total": round(total_precip, 1),
                    "visibility_avg": round(avg_visibility, 1),
                    "weather_condition": dominant_weather,
                    "field_work_score_avg": round(avg_score, 1),
                    "field_work_score_max": max_score,
                    "recommendation": optimizer.get_work_recommendation(int(avg_score)),
                    "hours_count": len(data["hours"]),
                    "best_hours": [data["hours"][i] for i, score in enumerate(data["scores"]) if score >= max_score - 5]
                })

        # Sort by date
        result.sort(key=lambda x: x["date"])
        
        return JsonResponse({
            "success": True,
            "site_name": site.name,
            "daily_summaries": result,
            "total_days": len(result)
        })

    except Exception as e:
        logger.error(f"Daily summary error: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)


@login_required
# Removed Django admin decorator - using custom role-based permissions
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
