from django.test import SimpleTestCase

from .weather_service import WeatherAPIService
from .api_views import _parse_coordinates


class WeatherServiceUnitTests(SimpleTestCase):
    def setUp(self):
        self.service = WeatherAPIService("METEO")

    def test_to_cardinal(self):
        to_cardinal = self.service._to_cardinal
        self.assertEqual(to_cardinal(0), "N")
        self.assertEqual(to_cardinal(45), "NE")
        self.assertEqual(to_cardinal(90), "E")
        self.assertEqual(to_cardinal(135), "SE")
        self.assertEqual(to_cardinal(180), "S")
        self.assertEqual(to_cardinal(225), "SW")
        self.assertEqual(to_cardinal(270), "W")
        self.assertEqual(to_cardinal(315), "NW")

    def test_classify_weather_code(self):
        classify = self.service._classify_weather_condition_from_code
        self.assertEqual(classify(0), "CLEAR")
        for code in [1, 2, 3]:
            self.assertEqual(classify(code), "CLOUDY")
        for code in [45, 48]:
            self.assertEqual(classify(code), "FOGGY")
        for code in [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82, 85, 86]:
            self.assertEqual(classify(code), "RAINY")
        for code in [95, 96, 99]:
            self.assertEqual(classify(code), "STORMY")


class CoordinateParsingTests(SimpleTestCase):
    def test_decimal_coordinates(self):
        """Test parsing decimal degree coordinates"""
        lat, lon = _parse_coordinates("11.0425, 123.2011")
        self.assertAlmostEqual(lat, 11.0425, places=4)
        self.assertAlmostEqual(lon, 123.2011, places=4)

    def test_dms_coordinates(self):
        """Test parsing DMS coordinates"""
        lat, lon = _parse_coordinates("11°2′33″N, 123°12′4″E")
        self.assertAlmostEqual(lat, 11.0425, places=3)
        self.assertAlmostEqual(lon, 123.2011, places=3)

    def test_invalid_coordinates(self):
        """Test invalid coordinate formats raise ValueError"""
        with self.assertRaises(ValueError):
            _parse_coordinates("invalid format")
        
        with self.assertRaises(ValueError):
            _parse_coordinates("")


