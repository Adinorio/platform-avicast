"""
OptimizableImageMixin
Mixin for Django models to automatically handle image optimization
"""

import logging
from typing import Optional

from django.core.files.base import ContentFile
from django.db import models

from apps.common.services.image_optimizer import UniversalImageOptimizer

logger = logging.getLogger(__name__)


class OptimizableImageMixin(models.Model):
    """
    Mixin that adds automatic image optimization to Django models.

    Usage:
        class MyModel(OptimizableImageMixin):
            image = models.ImageField(upload_to='my_images/')
            # Automatically gets: optimized_image, thumbnail, ai_processed_image

    Features:
    - Automatic optimization on save
    - Separate optimized versions for different use cases
    - Storage tier management
    - Optimization statistics
    """

    # Optimization fields (added automatically when mixin is used)
    optimized_image = models.ImageField(
        upload_to='optimized/',
        null=True,
        blank=True,
        help_text="Web-optimized version for fast delivery"
    )
    thumbnail = models.ImageField(
        upload_to='thumbnails/',
        null=True,
        blank=True,
        help_text="Thumbnail version for previews"
    )
    ai_processed_image = models.ImageField(
        upload_to='ai_processed/',
        null=True,
        blank=True,
        help_text="AI-optimized version for processing"
    )

    # Optimization metadata
    optimization_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='pending',
        help_text="Status of image optimization"
    )
    original_size = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Original image file size in bytes"
    )
    optimized_size = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Optimized image file size in bytes"
    )
    thumbnail_size = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Thumbnail file size in bytes"
    )

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._optimizer = UniversalImageOptimizer()
        self._original_image_content = None

    def save(self, *args, **kwargs):
        """Override save to handle image optimization."""
        # Store original image content before saving
        if hasattr(self, 'image') and self.image and not self.image.closed:
            try:
                self.image.seek(0)
                self._original_image_content = self.image.read()
                self.original_size = len(self._original_image_content)
                self.image.seek(0)  # Reset file pointer
            except Exception as e:
                logger.warning(f"Could not read image content for optimization: {e}")

        # Call parent save first to ensure image is saved
        super().save(*args, **kwargs)

        # Optimize images after save if we have content
        if self._original_image_content and self._should_optimize():
            self._optimize_images_async()

    def _should_optimize(self) -> bool:
        """Determine if images should be optimized."""
        # Don't optimize if already completed
        if self.optimization_status == 'completed':
            return False

        # Don't optimize if no original image
        if not hasattr(self, 'image') or not self.image:
            return False

        # Don't optimize if optimization is disabled
        if getattr(self, '_disable_optimization', False):
            return False

        return True

    def _optimize_images_async(self):
        """Optimize images asynchronously or synchronously based on settings."""
        try:
            self.optimization_status = 'processing'
            self.save(update_fields=['optimization_status'])

            # Determine app name from model
            app_name = self._get_app_name()

            # Run optimization
            result = self._optimizer.optimize_for_app(
                self._original_image_content,
                app_name
            )

            # Save optimized versions
            self._save_optimized_versions(result)

            self.optimization_status = 'completed'

        except Exception as e:
            logger.error(f"Image optimization failed for {self.__class__.__name__} {self.pk}: {e}")
            self.optimization_status = 'failed'

        finally:
            self.save(update_fields=[
                'optimization_status', 'optimized_size', 'thumbnail_size'
            ])

    def _save_optimized_versions(self, result: dict):
        """Save the optimized image versions."""
        try:
            # Save optimized version
            if result.get('optimized'):
                filename = f"{self._get_base_filename()}_optimized.webp"
                self.optimized_image.save(
                    filename,
                    ContentFile(result['optimized']),
                    save=False
                )
                self.optimized_size = len(result['optimized'])

            # Save thumbnail
            if result.get('thumbnail'):
                filename = f"{self._get_base_filename()}_thumb.jpg"
                self.thumbnail.save(
                    filename,
                    ContentFile(result['thumbnail']),
                    save=False
                )
                self.thumbnail_size = len(result['thumbnail'])

            # Save AI-processed version
            if result.get('ai_ready'):
                filename = f"{self._get_base_filename()}_ai.jpg"
                self.ai_processed_image.save(
                    filename,
                    ContentFile(result['ai_ready']),
                    save=False
                )

        except Exception as e:
            logger.error(f"Failed to save optimized versions: {e}")

    def _get_app_name(self) -> str:
        """Get the app name from the model's meta."""
        return self._meta.app_label

    def _get_base_filename(self) -> str:
        """Get base filename for optimized images."""
        if hasattr(self, 'image') and self.image:
            name = str(self.pk)
            if hasattr(self, 'name'):
                name = getattr(self, 'name', str(self.pk))
            return name.replace(' ', '_').lower()
        return str(self.pk)

    # ============================================================================
    # PUBLIC METHODS
    # ============================================================================

    def reoptimize_images(self):
        """Manually trigger image re-optimization."""
        if hasattr(self, 'image') and self.image:
            try:
                self.image.seek(0)
                self._original_image_content = self.image.read()
                self.image.seek(0)
                self._optimize_images_async()
                return True
            except Exception as e:
                logger.error(f"Re-optimization failed: {e}")
                return False
        return False

    def get_optimization_stats(self) -> dict:
        """Get optimization statistics."""
        if not self.original_size:
            return {}

        stats = {
            'original_size': self.original_size,
            'has_optimized': bool(self.optimized_image),
            'has_thumbnail': bool(self.thumbnail),
            'has_ai_processed': bool(self.ai_processed_image),
            'optimization_status': self.optimization_status,
        }

        if self.optimized_size and self.original_size:
            stats['web_optimization'] = self._optimizer.get_optimization_stats(
                self.original_size, self.optimized_size
            )

        if self.thumbnail_size and self.original_size:
            stats['thumbnail_optimization'] = self._optimizer.get_optimization_stats(
                self.original_size, self.thumbnail_size
            )

        return stats

    def disable_optimization(self):
        """Disable automatic optimization for this instance."""
        self._disable_optimization = True

    def enable_optimization(self):
        """Enable automatic optimization for this instance."""
        self._disable_optimization = False

    # ============================================================================
    # PROPERTIES
    # ============================================================================

    @property
    def image_url(self) -> Optional[str]:
        """Get the best available image URL for web display."""
        if self.optimized_image:
            return self.optimized_image.url
        elif hasattr(self, 'image') and self.image:
            return self.image.url
        return None

    @property
    def thumbnail_url(self) -> Optional[str]:
        """Get thumbnail URL, fallback to optimized or original."""
        if self.thumbnail:
            return self.thumbnail.url
        elif self.optimized_image:
            return self.optimized_image.url
        elif hasattr(self, 'image') and self.image:
            return self.image.url
        return None

    @property
    def is_optimized(self) -> bool:
        """Check if image has been optimized."""
        return self.optimization_status == 'completed' and bool(self.optimized_image)

    @property
    def optimization_savings_percent(self) -> Optional[float]:
        """Get the percentage of space saved by optimization."""
        if self.original_size and self.optimized_size and self.original_size > 0:
            saved = self.original_size - self.optimized_size
            return round((saved / self.original_size) * 100, 1)
        return None
