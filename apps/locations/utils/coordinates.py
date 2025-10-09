"""
Coordinate conversion utilities for the locations app.
Handles conversion between DMS (Degrees, Minutes, Seconds) and decimal degrees.
"""

import re
from typing import Tuple, Optional


def dms_to_decimal(dms_str: str) -> Optional[float]:
    """
    Convert DMS (Degrees, Minutes, Seconds) to decimal degrees.
    
    Supports formats like:
    - 11°2'33"N or 11°2'33″N (with various degree/minute/second symbols)
    - 123°12'4"E or 123°12'4″E
    - 11d2m33sN or 11d2'33"N
    
    Args:
        dms_str: String in DMS format
        
    Returns:
        Decimal degrees as float, or None if parsing fails
    """
    if not dms_str:
        return None
        
    # Normalize the string by replacing various symbols
    normalized = dms_str.strip()
    # Replace degree symbols
    normalized = re.sub(r'[°º˚]', 'd', normalized)
    # Replace minute symbols (using unicode escapes)
    normalized = re.sub(r'[\u2032\u0027\u0060]', 'm', normalized)
    # Replace second symbols (using unicode escapes)
    normalized = re.sub(r'[\u2033\u0022]', 's', normalized)
    
    # Pattern to match DMS format: degrees, minutes, seconds, direction
    # Examples: 11d2m33sN, 123d12m4sE
    pattern = r'(\d+(?:\.\d+)?)d(\d+(?:\.\d+)?)m(\d+(?:\.\d+)?)s([NSEW])'
    match = re.search(pattern, normalized, re.IGNORECASE)
    
    if not match:
        # Try simpler format without seconds
        pattern = r'(\d+(?:\.\d+)?)d(\d+(?:\.\d+)?)m([NSEW])'
        match = re.search(pattern, normalized, re.IGNORECASE)
        if match:
            degrees = float(match.group(1))
            minutes = float(match.group(2))
            seconds = 0.0
            direction = match.group(3).upper()
        else:
            return None
    else:
        degrees = float(match.group(1))
        minutes = float(match.group(2))
        seconds = float(match.group(3))
        direction = match.group(4).upper()
    
    # Convert to decimal
    decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
    
    # Apply direction (S and W are negative)
    if direction in ['S', 'W']:
        decimal = -decimal
        
    return decimal


def parse_coordinates(coord_string: str) -> Optional[Tuple[float, float]]:
    """
    Parse coordinate string into (latitude, longitude) tuple.
    
    Handles multiple formats:
    - Decimal: "14.5995, 120.9842" or "14.5995,120.9842"
    - DMS: "11°2'33"N, 123°12'4"E" or similar
    - Mixed formats
    
    Args:
        coord_string: Coordinate string to parse
        
    Returns:
        Tuple of (latitude, longitude) as floats, or None if parsing fails
    """
    if not coord_string:
        return None
        
    try:
        # Split by comma
        parts = coord_string.split(',')
        if len(parts) != 2:
            return None
            
        lat_str = parts[0].strip()
        lon_str = parts[1].strip()
        
        # Try decimal format first
        try:
            lat = float(lat_str)
            lon = float(lon_str)
            return (lat, lon)
        except ValueError:
            pass
        
        # Try DMS format
        lat = dms_to_decimal(lat_str)
        lon = dms_to_decimal(lon_str)
        
        if lat is not None and lon is not None:
            return (lat, lon)
            
        return None
        
    except Exception:
        return None


def decimal_to_dms(decimal: float, is_latitude: bool = True) -> str:
    """
    Convert decimal degrees to DMS (Degrees, Minutes, Seconds) string.
    
    Args:
        decimal: Decimal degrees
        is_latitude: True for latitude (N/S), False for longitude (E/W)
        
    Returns:
        DMS string like "11°2'33"N" or "123°12'4"E"
    """
    # Determine direction
    if is_latitude:
        direction = 'N' if decimal >= 0 else 'S'
    else:
        direction = 'E' if decimal >= 0 else 'W'
    
    # Work with absolute value
    decimal = abs(decimal)
    
    # Extract degrees, minutes, seconds
    degrees = int(decimal)
    minutes_decimal = (decimal - degrees) * 60
    minutes = int(minutes_decimal)
    seconds = (minutes_decimal - minutes) * 60
    
    return f"{degrees}°{minutes}'{seconds:.0f}\"{direction}"


def format_coordinates_for_display(lat: float, lon: float) -> str:
    """
    Format coordinates for user-friendly display.
    
    Args:
        lat: Latitude in decimal degrees
        lon: Longitude in decimal degrees
        
    Returns:
        Formatted string like "14.5995°N, 120.9842°E"
    """
    lat_dir = 'N' if lat >= 0 else 'S'
    lon_dir = 'E' if lon >= 0 else 'W'
    return f"{abs(lat):.4f}°{lat_dir}, {abs(lon):.4f}°{lon_dir}"

