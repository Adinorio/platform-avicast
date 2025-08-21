"""
Storage Optimization Settings for AVICAST System
Add these settings to your Django settings file
"""

# ============================================================================
# STORAGE OPTIMIZATION SETTINGS
# ============================================================================

# Local Storage Limits
MAX_LOCAL_STORAGE_GB = 10  # Maximum local storage in GB
STORAGE_WARNING_THRESHOLD = 0.8  # Warn when 80% full

# Image Optimization
AUTO_OPTIMIZE_IMAGES = True
DEFAULT_IMAGE_FORMAT = 'WEBP'  # WEBP for best compression
MAX_IMAGE_DIMENSIONS = (2048, 1536)  # Max width x height
IMAGE_QUALITY = {
    'JPEG': 85,
    'PNG': 95,
    'WEBP': 80
}

# Deduplication Settings
ENABLE_HASH_DEDUPLICATION = True
HASH_ALGORITHM = 'SHA256'  # or 'MD5' for faster but less secure

# Storage Tiers (in days)
STORAGE_TIERS = {
    'HOT_TO_WARM': 30,      # Move to warm storage after 30 days
    'WARM_TO_COLD': 90,     # Move to cold storage after 90 days  
    'COLD_TO_ARCHIVE': 365, # Archive after 1 year
    'ARCHIVE_DELETE': 2555, # Delete after 7 years (government retention)
}

# Local Storage Configuration (WiFi-Only System)
USE_CLOUD_STORAGE = False  # ALWAYS False for CENRO local deployment
CLOUD_STORAGE_PROVIDER = 'local'  # Local storage only

# Local Storage Paths
ARCHIVE_STORAGE_PATH = 'D:/avicast_archive'  # Secondary drive for archives
EXTERNAL_BACKUP_PATHS = [
    'E:/',  # USB Drive 1
    'F:/',  # USB Drive 2
    'G:/',  # Network attached storage (if available)
]

# Local Network Optimization
WIFI_ONLY_MODE = True          # Optimize for WiFi-only deployment
LOCAL_NETWORK_OPTIMIZED = True # Enable local network optimizations
OFFLINE_CAPABLE = True         # System works without internet

# Government Compliance Settings
GOVERNMENT_RETENTION_YEARS = 7  # Philippine government standard
AUDIT_TRAIL_ENABLED = True     # Full audit logging for compliance
DATA_SOVEREIGNTY = True        # All data stays within Philippines

# Automatic Cleanup Settings
AUTO_CLEANUP_ENABLED = True
AUTO_CLEANUP_SCHEDULE = 'daily'  # 'daily', 'weekly', 'monthly'
CLEANUP_DRY_RUN_FIRST = True  # Always do dry run before actual cleanup

# Performance Settings
DATABASE_INDEXES = True  # Enable database indexes for file hash lookups
THUMBNAIL_CACHE_ENABLED = True
THUMBNAIL_SIZES = {
    'small': (150, 150),
    'medium': (300, 300),
    'large': (600, 600)
}

# Monitoring and Alerts
STORAGE_MONITORING_ENABLED = True
ALERT_EMAIL_WHEN_STORAGE_FULL = True
STORAGE_ALERT_RECIPIENTS = ['admin@cenro.gov.ph']

# ============================================================================
# EXAMPLE CONFIGURATION FOR PRODUCTION
# ============================================================================

"""
# Production configuration example:

# For cloud storage (recommended for production)
USE_CLOUD_STORAGE = True
CLOUD_STORAGE_PROVIDER = 'aws'

# Stricter storage limits
MAX_LOCAL_STORAGE_GB = 5
STORAGE_WARNING_THRESHOLD = 0.7

# Aggressive optimization
AUTO_OPTIMIZE_IMAGES = True
DEFAULT_IMAGE_FORMAT = 'WEBP'
MAX_IMAGE_DIMENSIONS = (1920, 1080)

# Faster cleanup cycle
STORAGE_TIERS = {
    'HOT_TO_WARM': 15,      # Move to warm after 15 days
    'WARM_TO_COLD': 45,     # Cold after 45 days
    'COLD_TO_ARCHIVE': 180, # Archive after 6 months
    'ARCHIVE_DELETE': 2555, # Delete after 7 years
}

# Enable all monitoring
STORAGE_MONITORING_ENABLED = True
ALERT_EMAIL_WHEN_STORAGE_FULL = True
AUTO_CLEANUP_ENABLED = True
AUTO_CLEANUP_SCHEDULE = 'daily'
"""
