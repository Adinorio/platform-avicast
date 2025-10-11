"""
Locations app configuration
"""

from django.apps import AppConfig


class LocationsConfig(AppConfig):
    """Configuration for locations app"""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.locations"
    verbose_name = "Locations & Census Management"

    def ready(self):
        """Called when Django is ready - ensures proper registration"""
        # Import here to avoid circular imports
        from . import urls  # noqa: F401
        print(f"Locations app ready: {self.name}")
