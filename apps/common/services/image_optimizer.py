"""
Universal Image Optimization Service
Repository-wide image optimization with app-specific strategies
"""

import io
import logging
import os
from typing import Dict, Optional, Tuple, Union

from django.conf import settings
from django.core.files.base import ContentFile
from PIL import Image

logger = logging.getLogger(__name__)

# Import configuration at module level
try:
    from apps.image_processing.config import IMAGE_CONFIG
except ImportError:
    # Fallback configuration
    IMAGE_CONFIG = {
        "STORAGE_DIMENSIONS": (1024, 768),
        "AI_DIMENSIONS": (640, 640),
        "QUALITY_SETTINGS": {"JPEG": 85, "PNG": 95, "WEBP": 80},
        "AI_PROCESSING_QUALITY": 95,
        "THUMBNAIL_QUALITY": 85,
        "THUMBNAIL_SIZE": (150, 150),
    }


class UniversalImageOptimizer:
    """
    Universal image optimization service for the entire repository.
    Provides consistent image optimization across all Django apps.
    """

    def __init__(self):
        """Initialize with universal optimization settings."""
        self.max_dimensions = IMAGE_CONFIG["STORAGE_DIMENSIONS"]
        self.ai_dimensions = IMAGE_CONFIG["AI_DIMENSIONS"]
        self.image_quality = IMAGE_CONFIG["QUALITY_SETTINGS"]
        self.default_format = getattr(settings, "DEFAULT_IMAGE_FORMAT", "WEBP")
        self.enable_webp = getattr(settings, "ENABLE_WEBP", True)

    def optimize_for_app(
        self,
        image_content: bytes,
        app_name: str,
        **kwargs
    ) -> Dict[str, Union[bytes, None]]:
        """
        App-specific optimization strategy.

        Args:
            image_content: Raw image bytes
            app_name: Name of the app ('fauna', 'locations', 'image_processing', etc.)
            **kwargs: Additional app-specific parameters

        Returns:
            Dict with optimized versions: 'original', 'optimized', 'thumbnail', 'ai_ready'
        """
        try:
            # Always keep original for reference
            result = {
                'original': image_content,
                'optimized': None,
                'thumbnail': None,
                'ai_ready': None,
            }

            if app_name == 'fauna':
                result.update(self._optimize_species_image(image_content, **kwargs))
            elif app_name == 'locations':
                result.update(self._optimize_location_image(image_content, **kwargs))
            elif app_name == 'image_processing':
                result.update(self._optimize_processing_image(image_content, **kwargs))
            elif app_name == 'users':
                result.update(self._optimize_user_image(image_content, **kwargs))
            else:
                result.update(self._optimize_generic_image(image_content, **kwargs))

            return result

        except Exception as e:
            logger.error(f"Universal optimization failed for {app_name}: {str(e)}")
            return {
                'original': image_content,
                'optimized': None,
                'thumbnail': None,
                'ai_ready': None,
            }

    def _optimize_species_image(self, image_content: bytes, **kwargs) -> Dict[str, bytes]:
        """
        Species-specific optimization.
        Focus: Quality preservation for scientific reference, fast web delivery.
        """
        result = {}

        # Optimized for web (balance quality/speed)
        result['optimized'] = self.optimize_for_web(
            image_content,
            quality=90,  # Higher quality for species identification
            max_dimensions=(800, 600)
        )

        # Thumbnail for species lists
        result['thumbnail'] = self.create_thumbnail(
            image_content,
            size=(200, 200)  # Larger thumbnails for species identification
        )

        return result

    def _optimize_location_image(self, image_content: bytes, **kwargs) -> Dict[str, bytes]:
        """
        Location/site-specific optimization.
        Focus: Documentation quality, web performance.
        """
        result = {}

        # Optimized for web delivery
        result['optimized'] = self.optimize_for_web(
            image_content,
            quality=85,
            max_dimensions=(1024, 768)
        )

        # Standard thumbnail for location lists
        result['thumbnail'] = self.create_thumbnail(
            image_content,
            size=(150, 150)
        )

        return result

    def _optimize_processing_image(self, image_content: bytes, **kwargs) -> Dict[str, bytes]:
        """
        Image processing specific optimization.
        Focus: AI processing efficiency, coordinate preservation.
        """
        result = {}

        # AI-optimized version for future processing
        result['ai_ready'] = self.optimize_for_ai(image_content)

        # Web-optimized version for UI
        result['optimized'] = self.optimize_for_web(image_content)

        # Thumbnail for processing lists
        result['thumbnail'] = self.create_thumbnail(image_content)

        return result

    def _optimize_user_image(self, image_content: bytes, **kwargs) -> Dict[str, bytes]:
        """
        User profile/avatar optimization.
        Focus: Small file sizes, fast loading.
        """
        result = {}

        # Highly optimized for avatars
        result['optimized'] = self.optimize_for_web(
            image_content,
            quality=80,
            max_dimensions=(400, 400)
        )

        # Small thumbnail for user lists
        result['thumbnail'] = self.create_thumbnail(
            image_content,
            size=(100, 100)
        )

        return result

    def _optimize_generic_image(self, image_content: bytes, **kwargs) -> Dict[str, bytes]:
        """
        Generic optimization for any app.
        Balanced approach for unknown use cases.
        """
        result = {}

        result['optimized'] = self.optimize_for_web(image_content)
        result['thumbnail'] = self.create_thumbnail(image_content)

        return result

    # ============================================================================
    # CORE OPTIMIZATION METHODS
    # ============================================================================

    def optimize_for_web(
        self,
        image_content: bytes,
        quality: Optional[int] = None,
        max_dimensions: Optional[Tuple[int, int]] = None,
        target_format: Optional[str] = None
    ) -> Optional[bytes]:
        """
        Optimize image for web delivery.
        Focus: Small file size, good quality, fast loading.
        """
        try:
            image = Image.open(io.BytesIO(image_content))

            # Use defaults if not specified
            if target_format is None:
                target_format = self._get_best_format(image)
            if max_dimensions is None:
                max_dimensions = self.max_dimensions
            if quality is None:
                quality = self.image_quality.get(target_format, 85)

            # Resize if necessary
            image = self._resize_image(image, max_dimensions)

            # Optimize and save
            output_buffer = io.BytesIO()

            if target_format.upper() == "JPEG":
                if image.mode in ["RGBA", "LA", "P"]:
                    background = Image.new("RGB", image.size, (255, 255, 255))
                    if image.mode == "P":
                        image = image.convert("RGBA")
                    background.paste(image, mask=image.split()[-1] if image.mode == "RGBA" else None)
                    image = background
                image.save(output_buffer, format=target_format, quality=quality, optimize=True)

            elif target_format.upper() == "WEBP" and self.enable_webp:
                image.save(output_buffer, format=target_format, quality=quality, lossless=False)

            else:
                image.save(output_buffer, format="PNG", optimize=True)

            output_buffer.seek(0)
            return output_buffer.getvalue()

        except Exception as e:
            logger.error(f"Web optimization failed: {str(e)}")
            return None

    def optimize_for_ai(self, image_content: bytes) -> Optional[bytes]:
        """
        Optimize image specifically for AI processing.
        Focus: Consistent dimensions, minimal artifacts.
        """
        try:
            image = Image.open(io.BytesIO(image_content))

            # Convert to RGB for AI processing
            if image.mode not in ["RGB", "L"]:
                image = image.convert("RGB")

            # Resize for AI processing (640x640 is standard for YOLO)
            image.thumbnail(self.ai_dimensions, Image.Resampling.LANCZOS)

            # Save with high quality for AI processing
            ai_buffer = io.BytesIO()
            image.save(
                ai_buffer,
                format="JPEG",
                quality=IMAGE_CONFIG["AI_PROCESSING_QUALITY"],
                optimize=True,
            )
            ai_buffer.seek(0)
            return ai_buffer.getvalue()

        except Exception as e:
            logger.error(f"AI optimization failed: {str(e)}")
            return None

    def create_thumbnail(
        self,
        image_content: bytes,
        size: Tuple[int, int] = (150, 150)
    ) -> Optional[bytes]:
        """
        Create a thumbnail version of the image.
        Focus: Small size, fast loading, good quality.
        """
        try:
            image = Image.open(io.BytesIO(image_content))

            # Convert to RGB if necessary
            if image.mode in ["RGBA", "LA", "P"]:
                background = Image.new("RGB", image.size, (255, 255, 255))
                if image.mode == "P":
                    image = image.convert("RGBA")
                background.paste(image, mask=image.split()[-1] if image.mode == "RGBA" else None)
                image = background

            # Create thumbnail
            image.thumbnail(size, Image.Resampling.LANCZOS)

            # Save as JPEG
            output_buffer = io.BytesIO()
            image.save(
                output_buffer,
                format="JPEG",
                quality=IMAGE_CONFIG["THUMBNAIL_QUALITY"],
                optimize=True
            )
            output_buffer.seek(0)
            return output_buffer.getvalue()

        except Exception as e:
            logger.error(f"Thumbnail creation failed: {str(e)}")
            return None

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================

    def _resize_image(self, image: Image.Image, max_dimensions: Tuple[int, int]) -> Image.Image:
        """Resize image maintaining aspect ratio."""
        width, height = image.size
        max_width, max_height = max_dimensions

        # Calculate scaling factor
        width_ratio = max_width / width if width > max_width else 1
        height_ratio = max_height / height if height > max_height else 1
        scale_factor = min(width_ratio, height_ratio)

        if scale_factor < 1:
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        return image

    def _get_best_format(self, image: Image.Image) -> str:
        """Determine best format based on image characteristics."""
        if image.mode == "RGBA" or (hasattr(image, 'info') and 'transparency' in image.info):
            return "PNG"
        elif self.enable_webp:
            return "WEBP"
        else:
            return "JPEG"

    def get_optimization_stats(self, original_size: int, optimized_size: int) -> Dict[str, Union[float, int]]:
        """Calculate optimization statistics."""
        if original_size == 0:
            return {
                "compression_ratio": 0,
                "space_saved_percent": 0,
                "space_saved_bytes": 0
            }

        compression_ratio = optimized_size / original_size
        space_saved_bytes = original_size - optimized_size
        space_saved_percent = (space_saved_bytes / original_size) * 100

        return {
            "compression_ratio": round(compression_ratio, 3),
            "space_saved_percent": round(space_saved_percent, 1),
            "space_saved_bytes": space_saved_bytes,
            "original_size": original_size,
            "optimized_size": optimized_size,
        }

    def validate_image(self, image_content: bytes) -> Tuple[bool, Optional[str]]:
        """Validate image content."""
        try:
            image = Image.open(io.BytesIO(image_content))
            image.verify()
            return True, None
        except Exception as e:
            return False, str(e)

    def get_image_info(self, image_content: bytes) -> Optional[Dict]:
        """Get basic image information."""
        try:
            image = Image.open(io.BytesIO(image_content))
            return {
                "format": image.format,
                "mode": image.mode,
                "size": image.size,
                "width": image.width,
                "height": image.height,
                "info": image.info,
            }
        except Exception as e:
            logger.error(f"Failed to get image info: {str(e)}")
            return None


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def optimize_image_for_app(image_content: bytes, app_name: str, **kwargs) -> Dict[str, Union[bytes, None]]:
    """
    Convenience function for optimizing images across apps.

    Usage:
        from apps.common.services.image_optimizer import optimize_image_for_app

        result = optimize_image_for_app(image_bytes, 'fauna')
        thumbnail = result['thumbnail']
        optimized = result['optimized']
    """
    optimizer = UniversalImageOptimizer()
    return optimizer.optimize_for_app(image_content, app_name, **kwargs)


def create_image_thumbnail(image_content: bytes, size: Tuple[int, int] = (150, 150)) -> Optional[bytes]:
    """
    Convenience function for creating thumbnails.

    Usage:
        from apps.common.services.image_optimizer import create_image_thumbnail

        thumbnail = create_image_thumbnail(image_bytes, size=(100, 100))
    """
    optimizer = UniversalImageOptimizer()
    return optimizer.create_thumbnail(image_content, size)
