"""
Main views module for users app
Imports and organizes views from specialized modules
"""

# Import remaining view functions from specialized modules
from .audit_views import *

# Re-export key functions for backward compatibility and URL configuration
__all__ = [
    # Audit views
    'system_logs',
]