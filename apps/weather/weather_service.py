import logging
from typing import Any

import requests
from django.conf import settings
from django.utils import timezone

from .models import (
    WeatherForecast,
)

logger = logging.getLogger(__name__)


class WeatherAPIService:
    """Service for fetching weather data from multiple APIs"""

    # API endpoints and configurations
    API_CONFIGS = {
        "OPENWEATHER": {
            "base_url": "https://api.openweathermap.org/data/2.5",
            "api_key_required": True,
            "endpoints": {"current": "/weather", "forecast": "/forecast", "onecall": "/onecall"},
        },
        "WEATHERAPI": {
            "base_url": "https://api.weatherapi.com/v1",
            "api_key_required": True,
            "endpoints": {
                "current": "/current.json",
                "forecast": "/forecast.json",
                "astronomy": "/astronomy.json",
            },
        },
        "METEO": {
            "base_url": "https://api.open-meteo.com/v1",
            "api_key_required": False,
            "endpoints": {"forecast": "/forecast"},
        },
    }

    def __init__(self, api_source: str = "METEO"):
        self.api_source = api_source
        self.config = self.API_CONFIGS.get(api_source, self.API_CONFIGS["METEO"])
        self.api_key = self._get_api_key()

    def _get_api_key(self) -> str | None:
        """Get API key from settings"""
        if not self.config["api_key_required"]:
            return None

        key_map = {
            "OPENWEATHER": "OPENWEATHER_API_KEY",
            "WEATHERAPI": "WEATHERAPI_API_KEY",
        }

        key_name = key_map.get(self.api_source)
        if key_name:
            return getattr(settings, key_name, None)

        return None

    def fetch_weather_data(
        self, latitude: float, longitude: float, days: int = 3
    ) -> dict[str, Any] | None:
        """
        Fetch weather data for given coordinates
        Returns: Dict with current weather and forecast data
        """
        try:
            if self.api_source == "METEO":
                return self._fetch_open_meteo_data(latitude, longitude, days)
            elif self.api_source == "OPENWEATHER":
                return self._fetch_openweather_data(latitude, longitude)
            elif self.api_source == "WEATHERAPI":
                return self._fetch_weatherapi_data(latitude, longitude, days)

        except Exception as e:
            logger.error(f"Failed to fetch weather data from {self.api_source}: {str(e)}")
            return None

    def _fetch_open_meteo_data(self, lat: float, lon: float, days: int) -> dict[str, Any]:
        """Fetch data from Open-Meteo API (free, no API key required)"""
        url = f"{self.config['base_url']}{self.config['endpoints']['forecast']}"

        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": [
                "temperature_2m",
                "precipitation_probability",
                "rain",
                "showers",
                "pressure_msl",
                "weather_code",
                "cloud_cover",
                "relative_humidity_2m",
                "wind_speed_10m",
                "wind_direction_10m",
                "visibility",
            ],
            "daily": ["sunrise", "sunset"],
            "forecast_days": min(days, 16),  # Open-Meteo limit
            "timezone": "auto",
            "windspeed_unit": "kmh",
            "precipitation_unit": "mm",
            "timeformat": "iso8601",
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        # Process and structure the data
        processed_data = {
            "api_source": "METEO",
            "current": self._extract_current_weather_meteo(data),
            "forecast": self._extract_forecast_meteo(data),
            "daily": self._extract_daily_forecast_meteo(data),
            "raw_response": data,
        }

        return processed_data

    def _extract_current_weather_meteo(self, data: dict) -> dict[str, Any]:
        """Extract current weather from Open-Meteo response"""
        hourly = data.get("hourly", {})

        # Find the closest hourly data point
        times = hourly.get("time", [])
        if not times:
            return {}

        # For demo purposes, return first data point
        weather_code = hourly.get("weather_code", [0])[0]
        rain = hourly.get("rain", [0.0])[0]
        showers = hourly.get("showers", [0.0])[0]
        total_precipitation = rain + showers

        return {
            "temperature": hourly.get("temperature_2m", [20.0])[0],
            "humidity": hourly.get("relative_humidity_2m", [60])[0],
            "wind_speed": hourly.get("wind_speed_10m", [10.0])[0],
            "wind_direction": self._to_cardinal(hourly.get("wind_direction_10m", [180])[0]),
            "precipitation": total_precipitation,
            "precipitation_probability": hourly.get("precipitation_probability", [0])[0],
            "pressure": hourly.get("pressure_msl", [1013.0])[0],
            # Open-Meteo visibility is meters → convert to km
            "visibility": (hourly.get("visibility", [10000])[0] or 0) / 1000,
            "weather_code": weather_code,
            "cloud_cover": hourly.get("cloud_cover", [0])[0],
            "weather_condition": self._classify_weather_condition_from_code(weather_code),
        }

    def _extract_forecast_meteo(self, data: dict) -> list[dict[str, Any]]:
        """Extract forecast data from Open-Meteo response"""
        hourly = data.get("hourly", {})
        forecast = []

        times = hourly.get("time", [])
        temperatures = hourly.get("temperature_2m", [])
        humidities = hourly.get("relative_humidity_2m", [])
        wind_speeds = hourly.get("wind_speed_10m", [])
        wind_directions = hourly.get("wind_direction_10m", [])
        rains = hourly.get("rain", [])
        showers = hourly.get("showers", [])
        weather_codes = hourly.get("weather_code", [])
        cloud_covers = hourly.get("cloud_cover", [])
        precipitation_probabilities = hourly.get("precipitation_probability", [])
        pressures = hourly.get("pressure_msl", [])
        visibilities = hourly.get("visibility", [])

        for i, time_str in enumerate(times):
            # Keep all available hours (up to API provided ~16 days * 24)

            rain = rains[i] if i < len(rains) else 0.0
            showers_val = showers[i] if i < len(showers) else 0.0
            total_precipitation = rain + showers_val
            weather_code = weather_codes[i] if i < len(weather_codes) else 0

            forecast.append(
                {
                    "datetime": time_str,
                    "temperature": temperatures[i] if i < len(temperatures) else 20.0,
                    "humidity": humidities[i] if i < len(humidities) else 60,
                    "wind_speed": wind_speeds[i] if i < len(wind_speeds) else 10.0,
                    "wind_direction": self._to_cardinal(
                        wind_directions[i] if i < len(wind_directions) else 180
                    ),
                    "precipitation": total_precipitation,
                    "precipitation_probability": precipitation_probabilities[i] if i < len(precipitation_probabilities) else 0,
                    "weather_code": weather_code,
                    "cloud_cover": cloud_covers[i] if i < len(cloud_covers) else 0,
                    "weather_condition": self._classify_weather_condition_from_code(weather_code),
                    "pressure": pressures[i] if i < len(pressures) else 1013.0,
                    # Convert meters to km
                    "visibility": (visibilities[i] if i < len(visibilities) else 10000) / 1000,
                }
            )

        return forecast

    def _extract_daily_forecast_meteo(self, data: dict) -> list[dict[str, Any]]:
        """Extract daily forecast data from Open-Meteo response"""
        daily = data.get("daily", {})
        daily_forecast = []

        times = daily.get("time", [])
        sunrises = daily.get("sunrise", [])
        sunsets = daily.get("sunset", [])

        for i, time_str in enumerate(times):
            if i >= 7:  # Limit to first 7 days
                break

            daily_forecast.append(
                {
                    "date": time_str,
                    "sunrise": sunrises[i] if i < len(sunrises) else None,
                    "sunset": sunsets[i] if i < len(sunsets) else None,
                }
            )

        return daily_forecast

    def _fetch_openweather_data(self, lat: float, lon: float) -> dict[str, Any]:
        """Fetch data from OpenWeather API"""
        if not self.api_key:
            logger.warning("OpenWeather API key not configured")
            return {}

        url = f"{self.config['base_url']}{self.config['endpoints']['current']}"

        params = {"lat": lat, "lon": lon, "appid": self.api_key, "units": "metric"}

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        return {
            "api_source": "OPENWEATHER",
            "current": {
                "temperature": data.get("main", {}).get("temp", 20.0),
                "humidity": data.get("main", {}).get("humidity", 60),
                "wind_speed": data.get("wind", {}).get("speed", 10.0),
                "wind_direction": data.get("wind", {}).get("deg", 180),
                "precipitation": 0.0,  # OpenWeather current doesn't provide this
                "pressure": data.get("main", {}).get("pressure", 1013.0),
                "visibility": data.get("visibility", 10000) / 1000,  # Convert to km
                "weather_condition": self._classify_weather_condition(
                    0.0, data.get("wind", {}).get("speed", 10.0)
                ),
            },
            "forecast": [],  # Would need separate forecast API call
            "raw_response": data,
        }

    def _fetch_weatherapi_data(self, lat: float, lon: float, days: int) -> dict[str, Any]:
        """Fetch data from WeatherAPI"""
        if not self.api_key:
            logger.warning("WeatherAPI key not configured")
            return {}

        url = f"{self.config['base_url']}{self.config['endpoints']['forecast']}"

        params = {
            "key": self.api_key,
            "q": f"{lat},{lon}",
            "days": min(days, 10),  # WeatherAPI limit
            "hourly": 1,
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        return {
            "api_source": "WEATHERAPI",
            "current": self._extract_current_weatherapi(data),
            "forecast": self._extract_forecast_weatherapi(data),
            "raw_response": data,
        }

    def _extract_current_weatherapi(self, data: dict) -> dict[str, Any]:
        """Extract current weather from WeatherAPI response"""
        current = data.get("current", {})

        return {
            "temperature": current.get("temp_c", 20.0),
            "humidity": current.get("humidity", 60),
            "wind_speed": current.get("wind_kph", 10.0),
            "wind_direction": current.get("wind_degree", 180),
            "precipitation": current.get("precip_mm", 0.0),
            "pressure": current.get("pressure_mb", 1013.0),
            "visibility": current.get("vis_km", 10.0),
            "weather_condition": self._classify_weather_condition(
                current.get("precip_mm", 0.0), current.get("wind_kph", 10.0)
            ),
        }

    def _extract_forecast_weatherapi(self, data: dict) -> list[dict[str, Any]]:
        """Extract forecast data from WeatherAPI response"""
        forecast_data = []
        forecast = data.get("forecast", {}).get("forecastday", [])

        for day in forecast:
            date = day.get("date")
            hourly = day.get("hour", [])

            for hour in hourly:
                forecast_data.append(
                    {
                        "datetime": f"{date} {hour.get('time', '').split()[-1]}",
                        "temperature": hour.get("temp_c", 20.0),
                        "humidity": hour.get("humidity", 60),
                        "wind_speed": hour.get("wind_kph", 10.0),
                        "wind_direction": hour.get("wind_degree", 180),
                        "precipitation": hour.get("precip_mm", 0.0),
                        "weather_condition": self._classify_weather_condition(
                            hour.get("precip_mm", 0.0), hour.get("wind_kph", 10.0)
                        ),
                    }
                )

        return forecast_data[:24]  # Limit to first 24 hours

    def _classify_weather_condition_from_code(self, weather_code: int) -> str:
        """Classify weather condition based on WMO weather code"""
        # WMO Weather interpretation codes (WW)
        if weather_code == 0:
            return "CLEAR"
        elif weather_code in [1, 2, 3]:
            return "CLOUDY"
        elif weather_code in [45, 48]:
            return "FOGGY"
        elif weather_code in [51, 53, 55, 56, 57]:
            return "RAINY"
        elif weather_code in [61, 63, 65, 66, 67]:
            return "RAINY"
        elif weather_code in [71, 73, 75, 77]:
            return "RAINY"  # Snow conditions treated as rainy for field work
        elif weather_code in [80, 81, 82]:
            return "RAINY"
        elif weather_code in [85, 86]:
            return "RAINY"  # Snow showers treated as rainy
        elif weather_code in [95, 96, 99]:
            return "STORMY"
        else:
            return "CLEAR"  # Default fallback

    def _classify_weather_condition(self, precipitation: float, wind_speed: float) -> str:
        """Classify weather condition based on precipitation and wind"""
        if precipitation > 5.0:
            return "RAINY"
        elif wind_speed > 20.0:
            return "WINDY"
        elif precipitation > 0.1:
            return "CLOUDY"
        else:
            return "CLEAR"

    def _to_cardinal(self, degrees: float) -> str:
        """Convert wind direction in degrees to cardinal direction (8-wind)."""
        if degrees is None:
            return "N"
        deg = float(degrees) % 360
        dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        idx = int((deg + 22.5) // 45) % 8
        return dirs[idx]


class FieldWorkOptimizationService:
    """Service for optimizing field work based on weather conditions"""

    def calculate_field_work_score(self, weather_data: dict) -> int:
        """Calculate field work suitability score (0-100)"""
        score = 100

        # Temperature penalty (ideal: 15-25°C)
        temperature = weather_data.get("temperature", 20.0)
        if temperature < 10 or temperature > 30:
            score -= 20
        elif temperature < 15 or temperature > 25:
            score -= 10

        # Humidity penalty (ideal: 40-70%)
        humidity = weather_data.get("humidity", 60)
        if humidity > 80 or humidity < 30:
            score -= 15
        elif humidity > 70 or humidity < 40:
            score -= 5

        # Wind penalty (ideal: < 20 km/h)
        wind_speed = weather_data.get("wind_speed", 10.0)
        if wind_speed > 30:
            score -= 25
        elif wind_speed > 20:
            score -= 15

        # Precipitation penalty
        precipitation = weather_data.get("precipitation", 0.0)
        if precipitation > 5:
            score -= 30
        elif precipitation > 2:
            score -= 15

        # Visibility penalty
        visibility = weather_data.get("visibility", 10.0)
        if visibility < 5:
            score -= 20
        elif visibility < 10:
            score -= 10

        return max(0, score)

    def get_work_recommendation(self, score: int) -> str:
        """Get work recommendation based on score"""
        if score >= 80:
            return "EXCELLENT"
        elif score >= 60:
            return "GOOD"
        elif score >= 40:
            return "MODERATE"
        elif score >= 20:
            return "POOR"
        else:
            return "NOT_RECOMMENDED"

    def optimize_schedule(self, site, planned_date, planned_time):
        """Optimize field work schedule based on weather forecast"""
        # Get weather forecast for the site and time
        try:
            forecast = WeatherForecast.objects.filter(
                site=site, forecast_date=planned_date, forecast_time__hour=planned_time.hour
            ).first()

            if forecast:
                score = self.calculate_field_work_score(
                    {
                        "temperature": forecast.temperature,
                        "humidity": forecast.humidity,
                        "wind_speed": forecast.wind_speed,
                        "precipitation": forecast.precipitation,
                        "visibility": forecast.visibility,
                    }
                )

                recommendation = self.get_work_recommendation(score)

                return {
                    "score": score,
                    "recommendation": recommendation,
                    "forecast": forecast,
                    "is_optimized": recommendation in ["EXCELLENT", "GOOD"],
                }

        except Exception as e:
            logger.error(f"Failed to optimize schedule: {str(e)}")

        return {"score": 50, "recommendation": "MODERATE", "forecast": None, "is_optimized": False}


def get_weather_service(api_source: str = "METEO") -> WeatherAPIService:
    """Get weather service instance"""
    return WeatherAPIService(api_source)


def get_field_work_optimizer() -> FieldWorkOptimizationService:
    """Get field work optimization service instance"""
    return FieldWorkOptimizationService()
