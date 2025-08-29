"""
Utility functions for image processing app
Reduces code duplication across views and models
"""
import os
import hashlib
from django.utils import timezone


def generate_unique_filename(original_name, timestamp=None):
    """Generate unique filename with timestamp"""
    if timestamp is None:
        timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
    base_name, ext = os.path.splitext(original_name)
    return f"{base_name}_{timestamp}{ext}"


def create_auto_title(filename):
    """Create title from filename by cleaning it up"""
    base_name = os.path.splitext(filename)[0]
    return base_name.replace('_', ' ').replace('-', ' ').title()


def calculate_file_hash(file_content):
    """Calculate SHA256 hash of file content"""
    return hashlib.sha256(file_content).hexdigest()


def get_file_extension(filename):
    """Get file extension from filename"""
    return os.path.splitext(filename)[1].lower().lstrip('.')


def validate_file_extension(filename, allowed_extensions):
    """Validate file extension against allowed list"""
    ext = get_file_extension(filename)
    return ext in allowed_extensions


def format_file_size_mb(bytes_size):
    """Format file size in MB with 2 decimal places"""
    return f"{bytes_size / (1024 * 1024):.2f}"


def get_image_dimensions(image_file):
    """Get image dimensions from PIL Image object"""
    from PIL import Image
    from io import BytesIO

    if hasattr(image_file, 'read'):
        # File-like object
        if hasattr(image_file, 'seek'):
            image_file.seek(0)
        img = Image.open(BytesIO(image_file.read()))
    else:
        # File path
        img = Image.open(image_file)

    return img.size  # (width, height)


def create_progress_updater(model_instance, step_field='processing_step', progress_field='processing_progress'):
    """Create a progress updater function for a model instance"""
    def update_progress(step, progress, description=""):
        """Update progress with real-time feedback"""
        setattr(model_instance, step_field, step)
        setattr(model_instance, progress_field, progress)
        model_instance.save(update_fields=[step_field, progress_field])
        return True
    return update_progress
