"""
Image Optimization Utilities
Helper functions for using the universal image optimizer across the repository
"""

from typing import Dict, Optional

from apps.common.services.image_optimizer import UniversalImageOptimizer


def optimize_species_image(image_content: bytes, **kwargs) -> Dict[str, bytes]:
    """
    Optimize an image for the fauna/species context.

    Args:
        image_content: Raw image bytes
        **kwargs: Additional optimization parameters

    Returns:
        Dict with optimized versions
    """
    optimizer = UniversalImageOptimizer()
    return optimizer.optimize_for_app(image_content, 'fauna', **kwargs)


def optimize_location_image(image_content: bytes, **kwargs) -> Dict[str, bytes]:
    """
    Optimize an image for the locations/sites context.

    Args:
        image_content: Raw image bytes
        **kwargs: Additional optimization parameters

    Returns:
        Dict with optimized versions
    """
    optimizer = UniversalImageOptimizer()
    return optimizer.optimize_for_app(image_content, 'locations', **kwargs)


def optimize_user_image(image_content: bytes, **kwargs) -> Dict[str, bytes]:
    """
    Optimize an image for user profiles/avatars.

    Args:
        image_content: Raw image bytes
        **kwargs: Additional optimization parameters

    Returns:
        Dict with optimized versions
    """
    optimizer = UniversalImageOptimizer()
    return optimizer.optimize_for_app(image_content, 'users', **kwargs)


def create_image_thumbnail(image_content: bytes, size: tuple = (150, 150)) -> Optional[bytes]:
    """
    Create a thumbnail from any image.

    Args:
        image_content: Raw image bytes
        size: Thumbnail size as (width, height)

    Returns:
        Thumbnail image bytes or None if failed
    """
    optimizer = UniversalImageOptimizer()
    return optimizer.create_thumbnail(image_content, size)


def get_image_optimization_stats(original_size: int, optimized_size: int) -> Dict[str, float]:
    """
    Calculate optimization statistics.

    Args:
        original_size: Original file size in bytes
        optimized_size: Optimized file size in bytes

    Returns:
        Dict with compression statistics
    """
    optimizer = UniversalImageOptimizer()
    return optimizer.get_optimization_stats(original_size, optimized_size)


def validate_image_content(image_content: bytes) -> tuple[bool, Optional[str]]:
    """
    Validate image content across all supported formats.

    Args:
        image_content: Raw image bytes

    Returns:
        Tuple of (is_valid, error_message)
    """
    optimizer = UniversalImageOptimizer()
    return optimizer.validate_image(image_content)


# ============================================================================
# MODEL INTEGRATION HELPERS
# ============================================================================

def get_optimized_image_url(model_instance) -> Optional[str]:
    """
    Get the best available optimized image URL for any model with images.

    Args:
        model_instance: Model instance with image fields

    Returns:
        URL string or None
    """
    # Try optimized image first
    if hasattr(model_instance, 'optimized_image') and model_instance.optimized_image:
        return model_instance.optimized_image.url

    # Fallback to original image
    if hasattr(model_instance, 'image') and model_instance.image:
        return model_instance.image.url

    return None


def get_thumbnail_url(model_instance) -> Optional[str]:
    """
    Get thumbnail URL with fallbacks.

    Args:
        model_instance: Model instance with image fields

    Returns:
        Thumbnail URL or None
    """
    # Try dedicated thumbnail first
    if hasattr(model_instance, 'thumbnail') and model_instance.thumbnail:
        return model_instance.thumbnail.url

    # Fallback to optimized image
    if hasattr(model_instance, 'optimized_image') and model_instance.optimized_image:
        return model_instance.optimized_image.url

    # Final fallback to original
    if hasattr(model_instance, 'image') and model_instance.image:
        return model_instance.image.url

    return None


# ============================================================================
# BATCH PROCESSING HELPERS
# ============================================================================

def batch_optimize_images(image_list: list, app_name: str = 'generic') -> Dict[str, int]:
    """
    Batch optimize multiple images.

    Args:
        image_list: List of image content bytes
        app_name: App context for optimization

    Returns:
        Dict with processing statistics
    """
    optimizer = UniversalImageOptimizer()
    results = []

    for image_content in image_list:
        try:
            result = optimizer.optimize_for_app(image_content, app_name)
            results.append(result)
        except Exception as e:
            print(f"Failed to optimize image: {e}")
            results.append(None)

    successful = sum(1 for r in results if r and r.get('optimized'))
    return {
        'total_processed': len(image_list),
        'successful': successful,
        'failed': len(image_list) - successful,
        'success_rate': successful / len(image_list) * 100 if image_list else 0
    }


# ============================================================================
# EXAMPLES AND USAGE PATTERNS
# ============================================================================

"""
USAGE EXAMPLES:

1. Basic optimization for any app:
```python
from apps.common.utils.image_optimization import optimize_species_image

# In your view or model
result = optimize_species_image(image_bytes)
thumbnail = result['thumbnail']
optimized = result['optimized']
```

2. Get optimized URLs for templates:
```python
from apps.common.utils.image_optimization import get_optimized_image_url

# In your template context
species.image_url = get_optimized_image_url(species)
```

3. Batch processing existing images:
```python
python manage.py optimize_images --app=all
# or programmatically:
from apps.common.utils.image_optimization import batch_optimize_images
stats = batch_optimize_images(image_list, 'fauna')
```

4. Manual re-optimization:
```python
# For any model with OptimizableImageMixin
species.reoptimize_images()
```

5. Check optimization status:
```python
stats = species.get_optimization_stats()
print(f"Space saved: {stats['optimization_savings_percent']}%")
```
"""
