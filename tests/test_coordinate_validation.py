"""
Tests for coordinate validation and normalization
"""

import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError
from apps.locations.models import Site


class CoordinateValidationTest(TestCase):
    """Test coordinate validation and normalization"""

    def test_parse_coordinate_input_decimal_comma(self):
        """Test parsing decimal coordinates with comma separator"""
        result = Site.parse_coordinate_input("14.5995, 120.9842")
        self.assertEqual(result, "14.599500, 120.984200")

    def test_parse_coordinate_input_decimal_semicolon(self):
        """Test parsing decimal coordinates with semicolon separator"""
        result = Site.parse_coordinate_input("14.5995; 120.9842")
        self.assertEqual(result, "14.599500, 120.984200")

    def test_parse_coordinate_input_decimal_pipe(self):
        """Test parsing decimal coordinates with pipe separator"""
        result = Site.parse_coordinate_input("14.5995|120.9842")
        self.assertEqual(result, "14.599500, 120.984200")

    def test_parse_coordinate_input_space_separated(self):
        """Test parsing space-separated coordinates"""
        result = Site.parse_coordinate_input("14.5995 120.9842")
        self.assertEqual(result, "14.599500, 120.984200")

    def test_parse_coordinate_input_no_spaces(self):
        """Test parsing coordinates without spaces"""
        result = Site.parse_coordinate_input("14.5995,120.9842")
        self.assertEqual(result, "14.599500, 120.984200")

    def test_parse_coordinate_input_dms_format(self):
        """Test parsing DMS format coordinates"""
        result = Site.parse_coordinate_input("14°35'58.2\"N, 120°59'3.1\"E")
        # Should convert to decimal format
        self.assertIn("14.", result)
        self.assertIn("120.", result)
        self.assertIn(",", result)

    def test_parse_coordinate_input_invalid_format(self):
        """Test parsing invalid coordinate format"""
        with self.assertRaises(ValueError):
            Site.parse_coordinate_input("invalid coordinates")

    def test_parse_coordinate_input_empty(self):
        """Test parsing empty coordinates"""
        with self.assertRaises(ValueError):
            Site.parse_coordinate_input("")

    def test_parse_coordinate_input_whitespace_only(self):
        """Test parsing whitespace-only coordinates"""
        with self.assertRaises(ValueError):
            Site.parse_coordinate_input("   ")

    def test_validate_latitude_range(self):
        """Test latitude validation range"""
        # Valid latitude
        result = Site.parse_coordinate_input("0, 0")
        self.assertEqual(result, "0.000000, 0.000000")

        # Invalid latitude (too high)
        with self.assertRaises(ValueError):
            Site.parse_coordinate_input("91, 0")

        # Invalid latitude (too low)
        with self.assertRaises(ValueError):
            Site.parse_coordinate_input("-91, 0")

    def test_validate_longitude_range(self):
        """Test longitude validation range"""
        # Valid longitude
        result = Site.parse_coordinate_input("0, 0")
        self.assertEqual(result, "0.000000, 0.000000")

        # Invalid longitude (too high)
        with self.assertRaises(ValueError):
            Site.parse_coordinate_input("0, 181")

        # Invalid longitude (too low)
        with self.assertRaises(ValueError):
            Site.parse_coordinate_input("0, -181")

    def test_coordinate_precision(self):
        """Test coordinate precision (6 decimal places)"""
        result = Site.parse_coordinate_input("14.123456789, 120.987654321")
        # Should be rounded to 6 decimal places
        self.assertEqual(result, "14.123457, 120.987654")

    def test_site_model_coordinate_parsing(self):
        """Test Site model coordinate parsing methods"""
        site = Site(name="Test Site", coordinates="14.5995, 120.9842")
        
        # Test parse_coordinates method
        lat, lon = site.parse_coordinates()
        self.assertEqual(lat, 14.5995)
        self.assertEqual(lon, 120.9842)

    def test_site_model_coordinate_display(self):
        """Test Site model coordinate display method"""
        site = Site(name="Test Site", coordinates="14.5995, 120.9842")
        
        # Test get_coordinates_display method
        display = site.get_coordinates_display()
        self.assertEqual(display, "14.599500, 120.984200")

    def test_site_model_save_normalization(self):
        """Test that Site model normalizes coordinates on save"""
        site = Site(name="Test Site", coordinates="14.5995, 120.9842")
        site.save()
        
        # Coordinates should be normalized
        self.assertEqual(site.coordinates, "14.599500, 120.984200")

    def test_site_model_save_invalid_coordinates(self):
        """Test that Site model raises error for invalid coordinates"""
        site = Site(name="Test Site", coordinates="invalid")
        
        with self.assertRaises(ValueError):
            site.save()

    def test_philippines_coordinates(self):
        """Test coordinates for Philippines locations"""
        # Manila coordinates
        result = Site.parse_coordinate_input("14.5995, 120.9842")
        self.assertEqual(result, "14.599500, 120.984200")

        # Cebu coordinates
        result = Site.parse_coordinate_input("10.3157, 123.8854")
        self.assertEqual(result, "10.315700, 123.885400")

        # Davao coordinates
        result = Site.parse_coordinate_input("7.1907, 125.4553")
        self.assertEqual(result, "7.190700, 125.455300")


if __name__ == '__main__':
    # Run tests if executed directly
    import django
    from django.conf import settings
    from django.test.utils import get_runner

    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(["tests.test_coordinate_validation"])
