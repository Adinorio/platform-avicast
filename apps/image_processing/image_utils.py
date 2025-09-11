"""
Image Utilities for Common Image Operations
Centralizes image manipulation and dimension calculations
"""

import io
import logging
from typing import Tuple, Dict, Any

from PIL import Image

logger = logging.getLogger(__name__)


class ImageUtils:
    """Utility class for common image operations"""
    
    @staticmethod
    def get_image_dimensions(file_content: bytes) -> Tuple[int, int]:
        """Get image dimensions from file content"""
        try:
            image = Image.open(io.BytesIO(file_content))
            return image.size  # Returns (width, height)
        except Exception as e:
            logger.error(f"Error getting image dimensions: {str(e)}")
            return (0, 0)
    
    @staticmethod
    def validate_image_dimensions(width: int, height: int, min_dims: Tuple[int, int], max_dims: Tuple[int, int]) -> Tuple[bool, str]:
        """Validate image dimensions against configured limits"""
        min_w, min_h = min_dims
        max_w, max_h = max_dims
        
        if width < min_w or height < min_h:
            return False, f"Image too small: {width}x{height}, minimum {min_w}x{min_h}"
        
        if width > max_w or height > max_h:
            return False, f"Image too large: {width}x{height}, maximum {max_w}x{max_h}"
        
        return True, "Valid dimensions"
    
    @staticmethod
    def create_image_analysis(file_content: bytes, filename: str) -> Dict[str, Any]:
        """Create comprehensive image analysis data"""
        try:
            image = Image.open(io.BytesIO(file_content))
            return {
                "dimensions": f"{image.size[0]}x{image.size[1]}",
                "file_size_bytes": len(file_content),
                "format": image.format,
                "mode": image.mode,
                "filename": filename,
                "width": image.size[0],
                "height": image.size[1]
            }
        except Exception as e:
            logger.error(f"Error creating image analysis: {str(e)}")
            return {
                "dimensions": "unknown",
                "file_size_bytes": len(file_content),
                "format": "unknown",
                "mode": "unknown",
                "filename": filename,
                "width": 0,
                "height": 0,
                "error": str(e)
            }
    
    @staticmethod
    def is_valid_image_format(file_content: bytes) -> bool:
        """Check if file content is a valid image format"""
        try:
            Image.open(io.BytesIO(file_content))
            return True
        except Exception:
            return False
    
    @staticmethod
    def get_image_format(file_content: bytes) -> str:
        """Get image format from file content"""
        try:
            image = Image.open(io.BytesIO(file_content))
            return image.format or "unknown"
        except Exception:
            return "unknown"



