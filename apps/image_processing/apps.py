from django.apps import AppConfig


class ImageProcessingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.image_processing'
    verbose_name = 'Image Processing & Bird Identification'
    
    def ready(self):
        """Import models when app is ready"""
        try:
            from . import analytics_models  # noqa
        except ImportError:
            pass
