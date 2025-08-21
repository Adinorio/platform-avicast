import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import datetime, timedelta
from .models import (
    WeatherForecast, WeatherAlert, WeatherAPI,
    FieldWorkSchedule, WeatherCondition
)
from .weather_service import (
    get_weather_service, get_field_work_optimizer
)
from apps.locations.models import Site
from apps.users.models import UserActivity

logger = logging.getLogger(__name__)

@login_required
def dashboard(request):
    """Weather dashboard with forecasts and optimization"""
    # Get all sites
    sites = Site.objects.filter(status='active')

    # Get recent forecasts
    recent_forecasts = WeatherForecast.objects.select_related('site').order_by('-created_at')[:10]

    # Get active alerts
    active_alerts = WeatherAlert.objects.filter(
        valid_from__lte=timezone.now(),
        valid_until__gte=timezone.now()
    ).order_by('severity', '-issued_at')[:5]

    # Get upcoming field work schedules
    upcoming_schedules = FieldWorkSchedule.objects.select_related(
        'site', 'supervisor'
    ).filter(
        planned_date__gte=timezone.now().date()
    ).order_by('planned_date', 'planned_start_time')[:5]

    context = {
        'sites': sites,
        'recent_forecasts': recent_forecasts,
        'active_alerts': active_alerts,
        'upcoming_schedules': upcoming_schedules,
        'weather_apis': WeatherAPI.choices,
    }

    return render(request, 'weather/dashboard.html', context)

@login_required
def fetch_weather(request):
    """AJAX endpoint to fetch weather data for a site"""
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            site_id = data.get('site_id')
            api_source = data.get('api_source', 'METEO')

            site = get_object_or_404(Site, id=site_id)

            # Get coordinates
            if not site.coordinates:
                return JsonResponse({'error': 'Site coordinates not available'})

            try:
                lat, lon = map(float, site.coordinates.split(','))
            except ValueError:
                return JsonResponse({'error': 'Invalid coordinates format'})

            # Fetch weather data
            weather_service = get_weather_service(api_source)
            weather_data = weather_service.fetch_weather_data(lat, lon, days=3)

            if weather_data:
                # Save current weather
                current = weather_data.get('current', {})
                if current:
                    WeatherForecast.objects.update_or_create(
                        site=site,
                        forecast_date=timezone.now().date(),
                        forecast_time=timezone.now().time().replace(second=0, microsecond=0),
                        defaults={
                            'temperature': current.get('temperature', 20.0),
                            'humidity': current.get('humidity', 60),
                            'wind_speed': current.get('wind_speed', 10.0),
                            'wind_direction': current.get('wind_direction', 'N'),
                            'precipitation': current.get('precipitation', 0.0),
                            'pressure': current.get('pressure', 1013.0),
                            'weather_condition': current.get('weather_condition', 'CLEAR'),
                            'visibility': current.get('visibility', 10.0),
                            'api_source': api_source,
                            'api_response_data': weather_data.get('raw_response', {}),
                        }
                    )

                return JsonResponse({
                    'success': True,
                    'message': f'Weather data fetched successfully from {api_source}',
                    'data': weather_data
                })

            else:
                return JsonResponse({'error': 'Failed to fetch weather data'})

        except Exception as e:
            logger.error(f"Weather fetch error: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
def optimize_field_work(request):
    """AJAX endpoint to optimize field work schedule"""
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            site_id = data.get('site_id')
            planned_date = data.get('planned_date')
            planned_time = data.get('planned_time')

            site = get_object_or_404(Site, id=site_id)

            # Parse date and time
            planned_date = datetime.strptime(planned_date, '%Y-%m-%d').date()
            planned_time = datetime.strptime(planned_time, '%H:%M').time()

            # Get optimization service
            optimizer = get_field_work_optimizer()
            optimization = optimizer.optimize_schedule(site, planned_date, planned_time)

            return JsonResponse({
                'success': True,
                'optimization': optimization
            })

        except Exception as e:
            logger.error(f"Field work optimization error: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
def alerts_view(request):
    """Weather alerts and warnings view"""
    # Get all alerts
    alerts = WeatherAlert.objects.select_related('sites').order_by('-issued_at')

    # Filter by status
    status_filter = request.GET.get('status', 'ALL')
    if status_filter == 'ACTIVE':
        alerts = alerts.filter(
            valid_from__lte=timezone.now(),
            valid_until__gte=timezone.now()
        )
    elif status_filter == 'UPCOMING':
        alerts = alerts.filter(valid_from__gt=timezone.now())
    elif status_filter == 'EXPIRED':
        alerts = alerts.filter(valid_until__lt=timezone.now())

    # Pagination
    paginator = Paginator(alerts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
    }

    return render(request, 'weather/alerts.html', context)

@login_required
def forecast_view(request, site_id=None):
    """Weather forecast view for specific site or all sites"""
    if site_id:
        site = get_object_or_404(Site, id=site_id)
        sites = [site]
    else:
        sites = Site.objects.filter(status='active')

    # Get date range (today + 7 days)
    today = timezone.now().date()
    date_range = [(today + timedelta(days=i)) for i in range(7)]

    # Get forecasts for all sites
    forecasts = {}
    for site in sites:
        site_forecasts = WeatherForecast.objects.filter(
            site=site,
            forecast_date__gte=today,
            forecast_date__lte=today + timedelta(days=6)
        ).order_by('forecast_date', 'forecast_time')

        forecasts[site.id] = {}
        for forecast in site_forecasts:
            date_key = forecast.forecast_date.isoformat()
            if date_key not in forecasts[site.id]:
                forecasts[site.id][date_key] = []
            forecasts[site.id][date_key].append(forecast)

    context = {
        'sites': sites,
        'date_range': date_range,
        'forecasts': forecasts,
        'selected_site': site if site_id else None,
    }

    return render(request, 'weather/forecast.html', context)

@login_required
def schedule_view(request):
    """Field work schedule management"""
    # Get all schedules
    schedules = FieldWorkSchedule.objects.select_related(
        'site', 'supervisor', 'created_by'
    ).order_by('-planned_date', '-planned_start_time')

    # Filter by status
    status_filter = request.GET.get('status', 'ALL')
    if status_filter != 'ALL':
        schedules = schedules.filter(status=status_filter)

    # Filter by site
    site_filter = request.GET.get('site')
    if site_filter:
        schedules = schedules.filter(site_id=site_filter)

    # Pagination
    paginator = Paginator(schedules, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get sites for filter dropdown
    sites = Site.objects.filter(status='active')

    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'site_filter': site_filter,
        'sites': sites,
    }

    return render(request, 'weather/schedule.html', context)

@login_required
def create_schedule(request):
    """Create new field work schedule"""
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)

            site = get_object_or_404(Site, id=data['site_id'])

            # Create schedule
            schedule = FieldWorkSchedule.objects.create(
                title=data['title'],
                description=data.get('description', ''),
                site=site,
                planned_date=datetime.strptime(data['planned_date'], '%Y-%m-%d').date(),
                planned_start_time=datetime.strptime(data['start_time'], '%H:%M').time(),
                planned_end_time=datetime.strptime(data['end_time'], '%H:%M').time(),
                supervisor_id=data.get('supervisor_id'),
                created_by=request.user
            )

            return JsonResponse({
                'success': True,
                'message': 'Schedule created successfully',
                'schedule_id': str(schedule.id)
            })

        except Exception as e:
            logger.error(f"Schedule creation error: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)
