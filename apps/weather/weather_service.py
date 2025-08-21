import requests
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from django.conf import settings
from django.utils import timezone
from .models import (
    WeatherForecast, WeatherAlert, WeatherAPI, WeatherCondition,
    TideCondition, FieldWorkSchedule
)

logger = logging.getLogger(__name__)

class WeatherAPIService:
    """Service for fetching weather data from multiple APIs"""

    # API endpoints and configurations
    API_CONFIGS = {
        'OPENWEATHER': {
            'base_url': 'https://api.openweathermap.org/data/2.5',
            'api_key_required': True,
            'endpoints': {
                'current': '/weather',
                'forecast': '/forecast',
                'onecall': '/onecall'
            }
        },
        'WEATHERAPI': {
            'base_url': 'https://api.weatherapi.com/v1',
            'api_key_required': True,
            'endpoints': {
                'current': '/current.json',
                'forecast': '/forecast.json',
                'astronomy': '/astronomy.json'
            }
        },
        'METEO': {
            'base_url': 'https://api.open-meteo.com/v1',
            'api_key_required': False,
            'endpoints': {
                'forecast': '/forecast'
            }
        }
    }

    def __init__(self, api_source: str = 'METEO'):
        self.api_source = api_source
        self.config = self.API_CONFIGS.get(api_source, self.API_CONFIGS['METEO'])
        self.api_key = self._get_api_key()

    def _get_api_key(self) -> Optional[str]:
        """Get API key from settings"""
        if not self.config['api_key_required']:
            return None

        key_map = {
            'OPENWEATHER': 'OPENWEATHER_API_KEY',
            'WEATHERAPI': 'WEATHERAPI_API_KEY',
        }

        key_name = key_map.get(self.api_source)
        if key_name:
            return getattr(settings, key_name, None)

        return None

    def fetch_weather_data(self, latitude: float, longitude: float,
                          days: int = 3) -> Optional[Dict[str, Any]]:
        """
        Fetch weather data for given coordinates
        Returns: Dict with current weather and forecast data
        """
        try:
            if self.api_source == 'METEO':
                return self._fetch_open_meteo_data(latitude, longitude, days)
            elif self.api_source == 'OPENWEATHER':
                return self._fetch_openweather_data(latitude, longitude)
            elif self.api_source == 'WEATHERAPI':
                return self._fetch_weatherapi_data(latitude, longitude, days)

        except Exception as e:
            logger.error(f"Failed to fetch weather data from {self.api_source}: {str(e)}")
            return None

    def _fetch_open_meteo_data(self, lat: float, lon: float, days: int) -> Dict[str, Any]:
        """Fetch data from Open-Meteo API (free, no API key required)"""
        url = f"{self.config['base_url']}{self.config['endpoints']['forecast']}"

        params = {
            'latitude': lat,
            'longitude': lon,
            'hourly': [
                'temperature_2m', 'relative_humidity_2m', 'wind_speed_10m',
                'wind_direction_10m', 'precipitation', 'pressure_msl', 'visibility'
            ],
            'daily': ['sunrise', 'sunset'],
            'forecast_days': min(days, 16),  # Open-Meteo limit
            'timezone': 'auto'
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        # Process and structure the data
        processed_data = {
            'api_source': 'METEO',
            'current': self._extract_current_weather_meteo(data),
            'forecast': self._extract_forecast_meteo(data),
            'raw_response': data
        }

        return processed_data

    def _extract_current_weather_meteo(self, data: Dict) -> Dict[str, Any]:
        """Extract current weather from Open-Meteo response"""
        hourly = data.get('hourly', {})
        current_time = timezone.now()

        # Find the closest hourly data point
        times = hourly.get('temperatures', [])
        if not times:
            return {}

        # For demo purposes, return first data point
        return {
            'temperature': hourly.get('temperature_2m', [20.0])[0],
            'humidity': hourly.get('relative_humidity_2m', [60])[0],
            'wind_speed': hourly.get('wind_speed_10m', [10.0])[0],
            'wind_direction': hourly.get('wind_direction_10m', [180])[0],
            'precipitation': hourly.get('precipitation', [0.0])[0],
            'pressure': hourly.get('pressure_msl', [1013.0])[0],
            'visibility': hourly.get('visibility', [10.0])[0],
            'weather_condition': self._classify_weather_condition(
                hourly.get('precipitation', [0.0])[0],
                hourly.get('wind_speed_10m', [10.0])[0]
            )
        }

    def _extract_forecast_meteo(self, data: Dict) -> List[Dict[str, Any]]:
        """Extract forecast data from Open-Meteo response"""
        hourly = data.get('hourly', {})
        forecast = []

        times = hourly.get('time', [])
        temperatures = hourly.get('temperature_2m', [])
        humidities = hourly.get('relative_humidity_2m', [])
        wind_speeds = hourly.get('wind_speed_10m', [])
        wind_directions = hourly.get('wind_direction_10m', [])
        precipitations = hourly.get('precipitation', [])

        for i, time_str in enumerate(times):
            if i >= 24:  # Limit to first 24 hours for demo
                break

            forecast.append({
                'datetime': time_str,
                'temperature': temperatures[i] if i < len(temperatures) else 20.0,
                'humidity': humidities[i] if i < len(humidities) else 60,
                'wind_speed': wind_speeds[i] if i < len(wind_speeds) else 10.0,
                'wind_direction': wind_directions[i] if i < len(wind_directions) else 180,
                'precipitation': precipitations[i] if i < len(precipitations) else 0.0,
                'weather_condition': self._classify_weather_condition(
                    precipitations[i] if i < len(precipitations) else 0.0,
                    wind_speeds[i] if i < len(wind_speeds) else 10.0
                )
            })

        return forecast

    def _fetch_openweather_data(self, lat: float, lon: float) -> Dict[str, Any]:
        """Fetch data from OpenWeather API"""
        if not self.api_key:
            logger.warning("OpenWeather API key not configured")
            return {}

        url = f"{self.config['base_url']}{self.config['endpoints']['current']}"

        params = {
            'lat': lat,
            'lon': lon,
            'appid': self.api_key,
            'units': 'metric'
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        return {
            'api_source': 'OPENWEATHER',
            'current': {
                'temperature': data.get('main', {}).get('temp', 20.0),
                'humidity': data.get('main', {}).get('humidity', 60),
                'wind_speed': data.get('wind', {}).get('speed', 10.0),
                'wind_direction': data.get('wind', {}).get('deg', 180),
                'precipitation': 0.0,  # OpenWeather current doesn't provide this
                'pressure': data.get('main', {}).get('pressure', 1013.0),
                'visibility': data.get('visibility', 10000) / 1000,  # Convert to km
                'weather_condition': self._classify_weather_condition(
                    0.0, data.get('wind', {}).get('speed', 10.0)
                )
            },
            'forecast': [],  # Would need separate forecast API call
            'raw_response': data
        }

    def _fetch_weatherapi_data(self, lat: float, lon: float, days: int) -> Dict[str, Any]:
        """Fetch data from WeatherAPI"""
        if not self.api_key:
            logger.warning("WeatherAPI key not configured")
            return {}

        url = f"{self.config['base_url']}{self.config['endpoints']['forecast']}"

        params = {
            'key': self.api_key,
            'q': f"{lat},{lon}",
            'days': min(days, 10),  # WeatherAPI limit
            'hourly': 1
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        return {
            'api_source': 'WEATHERAPI',
            'current': self._extract_current_weatherapi(data),
            'forecast': self._extract_forecast_weatherapi(data),
            'raw_response': data
        }

    def _extract_current_weatherapi(self, data: Dict) -> Dict[str, Any]:
        """Extract current weather from WeatherAPI response"""
        current = data.get('current', {})

        return {
            'temperature': current.get('temp_c', 20.0),
            'humidity': current.get('humidity', 60),
            'wind_speed': current.get('wind_kph', 10.0),
            'wind_direction': current.get('wind_degree', 180),
            'precipitation': current.get('precip_mm', 0.0),
            'pressure': current.get('pressure_mb', 1013.0),
            'visibility': current.get('vis_km', 10.0),
            'weather_condition': self._classify_weather_condition(
                current.get('precip_mm', 0.0),
                current.get('wind_kph', 10.0)
            )
        }

    def _extract_forecast_weatherapi(self, data: Dict) -> List[Dict[str, Any]]:
        """Extract forecast data from WeatherAPI response"""
        forecast_data = []
        forecast = data.get('forecast', {}).get('forecastday', [])

        for day in forecast:
            date = day.get('date')
            hourly = day.get('hour', [])

            for hour in hourly:
                forecast_data.append({
                    'datetime': f"{date} {hour.get('time', '').split()[-1]}",
                    'temperature': hour.get('temp_c', 20.0),
                    'humidity': hour.get('humidity', 60),
                    'wind_speed': hour.get('wind_kph', 10.0),
                    'wind_direction': hour.get('wind_degree', 180),
                    'precipitation': hour.get('precip_mm', 0.0),
                    'weather_condition': self._classify_weather_condition(
                        hour.get('precip_mm', 0.0),
                        hour.get('wind_kph', 10.0)
                    )
                })

        return forecast_data[:24]  # Limit to first 24 hours

    def _classify_weather_condition(self, precipitation: float, wind_speed: float) -> str:
        """Classify weather condition based on precipitation and wind"""
        if precipitation > 5.0:
            return 'RAINY'
        elif wind_speed > 20.0:
            return 'WINDY'
        elif precipitation > 0.1:
            return 'CLOUDY'
        else:
            return 'CLEAR'

class FieldWorkOptimizationService:
    """Service for optimizing field work based on weather conditions"""

    def calculate_field_work_score(self, weather_data: Dict) -> int:
        """Calculate field work suitability score (0-100)"""
        score = 100

        # Temperature penalty (ideal: 15-25°C)
        temperature = weather_data.get('temperature', 20.0)
        if temperature < 10 or temperature > 30:
            score -= 20
        elif temperature < 15 or temperature > 25:
            score -= 10

        # Humidity penalty (ideal: 40-70%)
        humidity = weather_data.get('humidity', 60)
        if humidity > 80 or humidity < 30:
            score -= 15
        elif humidity > 70 or humidity < 40:
            score -= 5

        # Wind penalty (ideal: < 20 km/h)
        wind_speed = weather_data.get('wind_speed', 10.0)
        if wind_speed > 30:
            score -= 25
        elif wind_speed > 20:
            score -= 15

        # Precipitation penalty
        precipitation = weather_data.get('precipitation', 0.0)
        if precipitation > 5:
            score -= 30
        elif precipitation > 2:
            score -= 15

        # Visibility penalty
        visibility = weather_data.get('visibility', 10.0)
        if visibility < 5:
            score -= 20
        elif visibility < 10:
            score -= 10

        return max(0, score)

    def get_work_recommendation(self, score: int) -> str:
        """Get work recommendation based on score"""
        if score >= 80:
            return 'EXCELLENT'
        elif score >= 60:
            return 'GOOD'
        elif score >= 40:
            return 'MODERATE'
        elif score >= 20:
            return 'POOR'
        else:
            return 'NOT_RECOMMENDED'

    def optimize_schedule(self, site, planned_date, planned_time):
        """Optimize field work schedule based on weather forecast"""
        # Get weather forecast for the site and time
        try:
            forecast = WeatherForecast.objects.filter(
                site=site,
                forecast_date=planned_date,
                forecast_time__hour=planned_time.hour
            ).first()

            if forecast:
                score = self.calculate_field_work_score({
                    'temperature': forecast.temperature,
                    'humidity': forecast.humidity,
                    'wind_speed': forecast.wind_speed,
                    'precipitation': forecast.precipitation,
                    'visibility': forecast.visibility
                })

                recommendation = self.get_work_recommendation(score)

                return {
                    'score': score,
                    'recommendation': recommendation,
                    'forecast': forecast,
                    'is_optimized': recommendation in ['EXCELLENT', 'GOOD']
                }

        except Exception as e:
            logger.error(f"Failed to optimize schedule: {str(e)}")

        return {
            'score': 50,
            'recommendation': 'MODERATE',
            'forecast': None,
            'is_optimized': False
        }

def get_weather_service(api_source: str = 'METEO') -> WeatherAPIService:
    """Get weather service instance"""
    return WeatherAPIService(api_source)

def get_field_work_optimizer() -> FieldWorkOptimizationService:
    """Get field work optimization service instance"""
    return FieldWorkOptimizationService()
