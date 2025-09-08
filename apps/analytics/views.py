"""
Main views module for analytics app
Imports and organizes views from specialized modules
"""

# Import all view functions from specialized modules
from .chart_views import *
from .dashboard_views import *
from .report_views import *

# Re-export key functions for backward compatibility and URL configuration
__all__ = [
    # Dashboard views
    'analytics_dashboard', 'chart_gallery',

    # Chart views
    'species_diversity_chart', 'population_trends_chart',
    'seasonal_analysis_chart', 'site_comparison_chart',

    # Report views
    'generate_census_report',
]
