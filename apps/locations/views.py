"""
Main views module for locations app
Imports and organizes views from specialized modules
"""

# Import all view functions from specialized modules
from .census_views import *
from .import_views import *
from .site_views import *

# Re-export key functions for backward compatibility and URL configuration
__all__ = [
    # Site views
    'site_list', 'site_detail', 'site_create', 'site_update', 'site_delete',

    # Census views
    'census_create', 'census_update', 'census_delete',

    # Import/export views
    'census_import', 'census_export_csv', 'census_export_excel',
    'mobile_import_list', 'submit_mobile_import', 'review_mobile_import',
    'bulk_import_actions',
]