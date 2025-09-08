import io
import logging
import os

from django.conf import settings
from PIL import Image

logger = logging.getLogger(__name__)

# Import configuration at module level
try:
    from .config import IMAGE_CONFIG
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


class ImageOptimizer:
    """Handles image optimization and compression for local storage"""

    def __init__(self):
        # Use module-level configuration
        self.max_dimensions = IMAGE_CONFIG["STORAGE_DIMENSIONS"]
        self.ai_dimensions = IMAGE_CONFIG["AI_DIMENSIONS"]
        self.image_quality = IMAGE_CONFIG["QUALITY_SETTINGS"]
        self.default_format = getattr(settings, "DEFAULT_IMAGE_FORMAT", "WEBP")
        self.enable_webp = getattr(settings, "ENABLE_WEBP", True)

    def optimize_for_ai(self, image_content):
        """
        Optimize image specifically for AI processing (640x640 for YOLO models)

        Args:
            image_content: Raw image bytes

        Returns:
            tuple: (ai_optimized_content, original_size, ai_size, ai_dimensions)
        """
        try:
            # Open image from bytes
            image = Image.open(io.BytesIO(image_content))
            original_size = len(image_content)
            original_width, original_height = image.size

            # Convert to RGB if necessary for AI processing
            if image.mode not in ["RGB", "L"]:
                image = image.convert("RGB")

            # Resize for AI processing (640x640 is standard for YOLO)
            image.thumbnail(self.ai_dimensions, Image.Resampling.LANCZOS)

            # Save optimized for AI
            ai_buffer = io.BytesIO()
            image.save(
                ai_buffer,
                format="JPEG",
                quality=IMAGE_CONFIG["AI_PROCESSING_QUALITY"],
                optimize=True,
            )
            ai_buffer.seek(0)
            ai_content = ai_buffer.getvalue()
            ai_size = len(ai_content)

            return ai_content, original_size, ai_size, image.size

        except Exception as e:
            logger.error(f"AI optimization failed: {str(e)}")
            return image_content, len(image_content), len(image_content), None

    def optimize_image(self, image_content, target_format=None, max_dimensions=None, quality=None):
        """
        Optimize image for storage with configurable parameters

        Args:
            image_content: Raw image bytes
            target_format: Target format (JPEG, PNG, WEBP)
            max_dimensions: Maximum dimensions as (width, height)
            quality: Quality setting (0-100)

        Returns:
            tuple: (optimized_content, new_size, format_used)
        """
        try:
            # Open image
            image = Image.open(io.BytesIO(image_content))
            original_size = len(image_content)

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

            if target_format == "JPEG":
                # Convert to RGB for JPEG
                if image.mode in ["RGBA", "LA", "P"]:
                    background = Image.new("RGB", image.size, (255, 255, 255))
                    if image.mode == "P":
                        image = image.convert("RGBA")
                    background.paste(image, mask=image.split()[-1] if image.mode == "RGBA" else None)
                    image = background
                image.save(output_buffer, format=target_format, quality=quality, optimize=True)

            elif target_format == "WEBP" and self.enable_webp:
                image.save(output_buffer, format=target_format, quality=quality, lossless=False)

            else:
                # PNG or fallback
                image.save(output_buffer, format="PNG", optimize=True)

            output_buffer.seek(0)
            optimized_content = output_buffer.getvalue()
            new_size = len(optimized_content)

            return optimized_content, new_size, target_format

        except Exception as e:
            logger.error(f"Image optimization failed: {str(e)}")
            return image_content, original_size, "ORIGINAL"

    def _resize_image(self, image, max_dimensions):
        """Resize image maintaining aspect ratio"""
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

    def _get_best_format(self, image):
        """Determine best format based on image characteristics"""
        if image.mode == "RGBA" or (hasattr(image, 'info') and 'transparency' in image.info):
            return "PNG"
        elif self.enable_webp:
            return "WEBP"
        else:
            return "JPEG"

    def get_optimization_stats(self, original_size, optimized_size):
        """Calculate optimization statistics"""
        if original_size == 0:
            return {"compression_ratio": 0, "space_saved_percent": 0, "space_saved_bytes": 0}

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

    def batch_optimize(self, image_paths, output_directory, target_format=None):
        """Optimize multiple images in batch"""
        results = []

        for image_path in image_paths:
            try:
                # Read image
                with open(image_path, "rb") as f:
                    image_content = f.read()

                # Optimize
                optimized_content, new_size, format_used = self.optimize_image(
                    image_content, target_format
                )

                # Save optimized image
                filename = os.path.basename(image_path)
                name, ext = os.path.splitext(filename)
                new_filename = f"{name}_optimized.{format_used.lower()}"
                output_path = os.path.join(output_directory, new_filename)

                with open(output_path, "wb") as f:
                    f.write(optimized_content)

                # Calculate stats
                original_size = len(image_content)
                stats = self.get_optimization_stats(original_size, new_size)

                results.append(
                    {
                        "original_path": image_path,
                        "output_path": output_path,
                        "original_size": original_size,
                        "optimized_size": new_size,
                        "format_used": format_used,
                        "stats": stats,
                        "success": True,
                    }
                )

            except Exception as e:
                results.append(
                    {
                        "original_path": image_path,
                        "error": str(e),
                        "success": False,
                    }
                )

        return results

    def create_thumbnail(self, image_content, size=(150, 150)):
        """Create a thumbnail from image content"""
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
            image.save(output_buffer, format="JPEG", quality=85, optimize=True)
            output_buffer.seek(0)

            return output_buffer.getvalue()

        except Exception as e:
            logger.error(f"Thumbnail creation failed: {str(e)}")
            return None

    def validate_image(self, image_content):
        """Validate image content"""
        try:
            image = Image.open(io.BytesIO(image_content))
            image.verify()
            return True, None
        except Exception as e:
            return False, str(e)

    def get_image_info(self, image_content):
        """Get basic image information"""
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
