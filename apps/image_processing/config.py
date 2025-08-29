"""
Central Configuration for Image Processing App
Consolidates all hardcoded values into configurable settings
"""

from django.conf import settings

# =============================================================================
# IMAGE PROCESSING CONFIGURATION
# =============================================================================

IMAGE_CONFIG = {
    # File Size Limits
    'MAX_FILE_SIZE_MB': getattr(settings, 'MAX_FILE_SIZE_MB', 50),
    'MAX_FILE_SIZE_BYTES': getattr(settings, 'MAX_FILE_SIZE_BYTES', 52428800),

    # File Extensions
    'ALLOWED_EXTENSIONS': getattr(settings, 'ALLOWED_EXTENSIONS', ['jpg', 'jpeg', 'png', 'gif']),

    # Image Dimensions
    'AI_DIMENSIONS': getattr(settings, 'AI_DIMENSIONS', (640, 640)),  # For YOLO processing
    'STORAGE_DIMENSIONS': getattr(settings, 'STORAGE_DIMENSIONS', (1024, 768)),  # For storage
    'THUMBNAIL_SIZE': getattr(settings, 'THUMBNAIL_SIZE', (150, 150)),  # Thumbnail dimensions
    'MIN_IMAGE_DIMENSIONS': getattr(settings, 'MIN_IMAGE_DIMENSIONS', (50, 50)),  # Minimum allowed
    'MAX_IMAGE_DIMENSIONS': getattr(settings, 'MAX_IMAGE_DIMENSIONS', (4000, 4000)),  # Maximum allowed

    # Image Quality Settings
    'QUALITY_SETTINGS': getattr(settings, 'IMAGE_QUALITY', {
        'JPEG': 85,
        'PNG': 95,
        'WEBP': 80
    }),
    'AI_PROCESSING_QUALITY': getattr(settings, 'AI_PROCESSING_QUALITY', 95),  # High quality for AI
    'THUMBNAIL_QUALITY': getattr(settings, 'THUMBNAIL_QUALITY', 85),  # Thumbnail quality

    # AI Model Settings
    'DEFAULT_CONFIDENCE_THRESHOLD': getattr(settings, 'DEFAULT_CONFIDENCE_THRESHOLD', 0.5),
    'VARIANCE_THRESHOLDS': getattr(settings, 'VARIANCE_THRESHOLDS', {
        'VERY_LOW': 100,   # Very low variance (uniform image)
        'LOW': 500,        # Low variance threshold
    }),

    # Storage Settings
    'MAX_LOCAL_STORAGE_GB': getattr(settings, 'MAX_LOCAL_STORAGE_GB', 50),
    'STORAGE_WARNING_THRESHOLD': getattr(settings, 'STORAGE_WARNING_THRESHOLD', 0.8),  # 80%
    'DEFAULT_RETENTION_DAYS': getattr(settings, 'DEFAULT_RETENTION_DAYS', 365),
    'UPLOAD_PATH_PATTERN': getattr(settings, 'UPLOAD_PATH_PATTERN', 'bird_images/%Y/%m/%d/'),

    # Processing Settings
    'PROGRESS_UPDATE_DELAY': getattr(settings, 'PROGRESS_UPDATE_DELAY', 0.1),  # seconds
    'DUPLICATE_CHECK_HOURS': getattr(settings, 'DUPLICATE_CHECK_HOURS', 24),
    'CLEANUP_DEFAULT_DAYS': getattr(settings, 'CLEANUP_DEFAULT_DAYS', 30),
    'OPTIMIZATION_PROGRESS_INTERVAL': getattr(settings, 'OPTIMIZATION_PROGRESS_INTERVAL', 10),
}

# =============================================================================
# SPECIES AND MODEL DEFINITIONS
# =============================================================================

BIRD_SPECIES = {
    'CHINESE_EGRET': {'id': 0, 'name': 'Chinese Egret', 'class_id': 0},
    'WHISKERED_TERN': {'id': 1, 'name': 'Whiskered Tern', 'class_id': 1},
    'GREAT_KNOT': {'id': 2, 'name': 'Great Knot', 'class_id': 2}
}

AI_MODELS = {
    'YOLO_V5': {'version': 'v5', 'display': 'YOLOv5'},
    'YOLO_V8': {'version': 'v8', 'display': 'YOLOv8'},
    'YOLO_V9': {'version': 'v9', 'display': 'YOLOv9'}
}

STORAGE_TIERS = [
    ('HOT', 'Hot Storage'),
    ('WARM', 'Warm Storage'),
    ('COLD', 'Cold Storage'),
    ('ARCHIVE', 'Archive')
]

# =============================================================================
# MODEL DOWNLOAD CONFIGURATION
# =============================================================================

YOLO_MODEL_CONFIG = {
    'v5': {
        'url': 'https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov5s.pt',
        'filename': 'yolov5s.pt',
        'size_mb': 14.1
    },
    'v8': {
        'url': 'https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8s.pt',
        'filename': 'yolov8s.pt',
        'size_mb': 22.6
    },
    'v9': {
        'url': 'https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov9c.pt',
        'filename': 'yolov9c.pt',
        'size_mb': 20.1
    }
}

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def calculate_file_size_mb(bytes_size):
    """Convert bytes to MB with consistent rounding"""
    return round(bytes_size / (1024 * 1024), 2)

def format_file_size_mb(bytes_size):
    """Format file size for display"""
    mb = calculate_file_size_mb(bytes_size)
    return f"{mb:.1f}"

def get_supported_formats():
    """Get list of supported image formats"""
    return ['jpg', 'jpeg', 'png', 'gif']

def get_species_choices():
    """Get species choices for Django model fields"""
    return [(key, species['name']) for key, species in BIRD_SPECIES.items()]

def get_model_choices():
    """Get AI model choices for Django model fields"""
    return [(key, model['display']) for key, model in AI_MODELS.items()]

def validate_image_dimensions(width, height):
    """Validate image dimensions against configured limits"""
    min_w, min_h = IMAGE_CONFIG['MIN_IMAGE_DIMENSIONS']
    max_w, max_h = IMAGE_CONFIG['MAX_IMAGE_DIMENSIONS']

    if width < min_w or height < min_h:
        return False, f"Image too small: {width}x{height}, minimum {min_w}x{min_h}"

    if width > max_w or height > max_h:
        return False, f"Image too large: {width}x{height}, maximum {max_w}x{max_h}"

    return True, "Valid dimensions"

def get_quality_for_format(format_name):
    """Get quality setting for image format"""
    return IMAGE_CONFIG['QUALITY_SETTINGS'].get(format_name.upper(), 85)
