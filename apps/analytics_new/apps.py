"""
Analytics App Configuration
Focused on 6 target bird species for CENRO monitoring
"""

from django.apps import AppConfig


class AnalyticsNewConfig(AppConfig):
    """Configuration for the new focused analytics app"""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.analytics_new"
    verbose_name = "Analytics & Reports (Target Species)"

    def ready(self):
        """Initialize app when Django is ready"""
        pass

