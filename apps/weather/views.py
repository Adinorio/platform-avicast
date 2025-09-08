"""
Main views module for weather app
Imports and organizes views from specialized modules
"""

# Import all view functions from specialized modules
from .api_views import *
from .dashboard_views import *
from .display_views import *

# Re-export key functions for backward compatibility and URL configuration
__all__ = [
    # Dashboard views
    'dashboard',

    # Display views
    'alerts_view', 'forecast_view', 'schedule_view',

    # API views
    'fetch_weather', 'optimize_field_work', 'create_schedule',
]