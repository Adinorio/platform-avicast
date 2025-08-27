import io
import os
from PIL import Image, ImageOps
from django.conf import settings
from django.core.files.base import ContentFile
import logging

logger = logging.getLogger(__name__)

class ImageOptimizer:
    """Handles image optimization and compression for local storage"""
    
    def __init__(self):
        self.max_dimensions = getattr(settings, 'MAX_IMAGE_DIMENSIONS', (1024, 768))  # Reduced for faster processing
        self.image_quality = getattr(settings, 'IMAGE_QUALITY', {
            'JPEG': 85,
            'PNG': 95,
            'WEBP': 80
        })
        self.default_format = getattr(settings, 'DEFAULT_IMAGE_FORMAT', 'WEBP')
        self.enable_webp = getattr(settings, 'ENABLE_WEBP', True)
    
    def optimize_image(self, image_content, target_format=None, max_dimensions=None, quality=None):
        """
        Optimize image content for storage
        
        Args:
            image_content: Raw image bytes
            target_format: Target format (JPEG, PNG, WEBP)
            max_dimensions: Maximum dimensions (width, height)
            quality: Quality setting (0-100)
        
        Returns:
            tuple: (optimized_content, new_size, format_used)
        """
        try:
            # Open image from bytes
            image = Image.open(io.BytesIO(image_content))
            
            # Convert to RGB if necessary (for JPEG/WebP)
            if target_format in ['JPEG', 'WEBP'] and image.mode in ['RGBA', 'LA', 'P']:
                # Create white background for transparent images
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            elif target_format == 'PNG' and image.mode != 'RGBA':
                image = image.convert('RGBA')
            
            # Resize if necessary
            if max_dimensions:
                image = self._resize_image(image, max_dimensions)
            else:
                image = self._resize_image(image, self.max_dimensions)
            
            # Determine target format
            if not target_format:
                target_format = self._get_best_format(image)
            
            # Set quality
            if not quality:
                quality = self.image_quality.get(target_format, 85)
            
            # Optimize and save
            output_buffer = io.BytesIO()
            
            if target_format == 'JPEG':
                image.save(output_buffer, format='JPEG', quality=quality, optimize=True)
            elif target_format == 'PNG':
                image.save(output_buffer, format='PNG', optimize=True)
            elif target_format == 'WEBP' and self.enable_webp:
                image.save(output_buffer, format='WEBP', quality=quality, method=6)
            else:
                # Fallback to JPEG
                image.save(output_buffer, format='JPEG', quality=quality, optimize=True)
                target_format = 'JPEG'
            
            # Get optimized content
            output_buffer.seek(0)
            optimized_content = output_buffer.getvalue()
            new_size = len(optimized_content)
            
            logger.info(f"Image optimized: {target_format}, Size: {new_size} bytes, Quality: {quality}")
            
            return optimized_content, new_size, target_format
            
        except Exception as e:
            logger.error(f"Image optimization failed: {str(e)}")
            # Return original content if optimization fails
            return image_content, len(image_content), 'ORIGINAL'
    
    def _resize_image(self, image, max_dimensions):
        """Resize image while maintaining aspect ratio"""
        if not max_dimensions:
            return image
        
        max_width, max_height = max_dimensions
        original_width, original_height = image.size
        
        # Calculate new dimensions
        if original_width <= max_width and original_height <= max_height:
            return image  # No resize needed
        
        # Calculate scaling factor
        width_ratio = max_width / original_width
        height_ratio = max_height / original_height
        scale_factor = min(width_ratio, height_ratio)
        
        new_width = int(original_width * scale_factor)
        new_height = int(original_height * scale_factor)
        
        # Resize image
        resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        logger.info(f"Image resized from {original_width}x{original_height} to {new_width}x{new_height}")
        
        return resized_image
    
    def _get_best_format(self, image):
        """Determine the best format for the image"""
        # Check if image has transparency
        has_transparency = False
        if image.mode in ['RGBA', 'LA', 'P']:
            if image.mode == 'P':
                # Check if palette has transparent colors
                if 'transparency' in image.info:
                    has_transparency = True
            else:
                # Check alpha channel
                alpha = image.split()[-1]
                if alpha.getextrema()[1] < 255:
                    has_transparency = True
        
        # Choose format based on characteristics
        if has_transparency:
            return 'PNG'  # PNG preserves transparency
        elif self.enable_webp:
            return 'WEBP'  # WebP for best compression
        else:
            return 'JPEG'  # JPEG as fallback
    
    def get_optimization_stats(self, original_size, optimized_size):
        """Calculate optimization statistics"""
        if original_size == 0:
            return {'compression_ratio': 0, 'space_saved_percent': 0, 'space_saved_bytes': 0}
        
        compression_ratio = optimized_size / original_size
        space_saved_bytes = original_size - optimized_size
        space_saved_percent = (space_saved_bytes / original_size) * 100
        
        return {
            'compression_ratio': round(compression_ratio, 3),
            'space_saved_percent': round(space_saved_percent, 1),
            'space_saved_bytes': space_saved_bytes,
            'original_size': original_size,
            'optimized_size': optimized_size
        }
    
    def batch_optimize(self, image_paths, output_directory, target_format=None):
        """Optimize multiple images in batch"""
        results = []
        
        for image_path in image_paths:
            try:
                # Read image
                with open(image_path, 'rb') as f:
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
                
                with open(output_path, 'wb') as f:
                    f.write(optimized_content)
                
                # Calculate stats
                original_size = len(image_content)
                stats = self.get_optimization_stats(original_size, new_size)
                
                results.append({
                    'original_path': image_path,
                    'optimized_path': output_path,
                    'format': format_used,
                    'stats': stats
                })
                
            except Exception as e:
                logger.error(f"Failed to optimize {image_path}: {str(e)}")
                results.append({
                    'original_path': image_path,
                    'error': str(e)
                })
        
        return results
    
    def create_thumbnail(self, image_content, size=(150, 150)):
        """Create a thumbnail from image content"""
        try:
            image = Image.open(io.BytesIO(image_content))
            
            # Convert to RGB if necessary
            if image.mode in ['RGBA', 'LA', 'P']:
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            
            # Create thumbnail
            image.thumbnail(size, Image.Resampling.LANCZOS)
            
            # Save as JPEG
            output_buffer = io.BytesIO()
            image.save(output_buffer, format='JPEG', quality=85, optimize=True)
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
                'format': image.format,
                'mode': image.mode,
                'size': image.size,
                'width': image.width,
                'height': image.height,
                'info': image.info
            }
        except Exception as e:
            logger.error(f"Failed to get image info: {str(e)}")
            return None
