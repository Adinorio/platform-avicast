"""
Production settings for Platform Avicast
Configured for local-only deployment with enhanced security
"""

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")

# Local-only access - restrict to local network
ALLOWED_HOSTS = env.list(
    "ALLOWED_HOSTS",
    default=[
        "localhost",
        "127.0.0.1",
        "192.168.1.0/24",  # Local network range
        "10.0.0.0/8",  # Private network range
        "172.16.0.0/12",  # Private network range
    ],
)

# Database Configuration - PostgreSQL for production
DATABASES = {
    "default": env.db(
        "DATABASE_URL", default="postgresql://avicast:secure_password@localhost:5432/avicast_db"
    ),
}

# Database optimization for production
DATABASES["default"]["OPTIONS"] = {
    "CONN_MAX_AGE": 60,  # Persistent connections
    "CONN_HEALTH_CHECKS": True,
    "OPTIONS": {
        "application_name": "platform_avicast",
    },
}

# Security Settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

# Session Security
SESSION_COOKIE_SECURE = False  # Set to True if using HTTPS
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 3600  # 1 hour
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST = False

# CSRF Protection
CSRF_COOKIE_SECURE = False  # Set to True if using HTTPS
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_AGE = 31449600  # 1 year

# Password Security
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
]

# Rate Limiting Configuration
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = "default"
RATELIMIT_VIEW = "django_ratelimit.views.ratelimit"

# Rate Limiting Rules
RATELIMIT_RULES = {
    # Login attempts: 5 per minute per IP
    "login": "5/m",
    # API endpoints: 100 per hour per IP
    "api": "100/h", 
    # Image uploads: 10 per hour per user
    "upload": "10/h",
    # Admin actions: 50 per hour per user
    "admin": "50/h",
    # General requests: 200 per hour per IP
    "general": "200/h",
}

# Login Attempts Tracking (django-axes)
AXES_ENABLED = True
AXES_FAILURE_LIMIT = 5
AXES_LOCK_OUT_BY_COMBINATION_USER_AND_IP = True
AXES_COOLOFF_TIME = 1  # 1 hour
AXES_LOCK_OUT_BY_USER_OR_IP = True
AXES_LOCKOUT_TEMPLATE = "users/lockout.html"
AXES_LOCKOUT_URL = "/locked-out/"
AXES_VERBOSE = True

# CORS Settings (restrict to local network)
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # React/Node.js frontend
    "http://127.0.0.1:3000",
    "http://192.168.1.0:3000",  # Local network
    "http://10.0.0.0:3000",  # Private network
]

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]

# Logging Configuration
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": BASE_DIR / "logs" / "django.log",
            "formatter": "verbose",
        },
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["file"],
            "level": "INFO",
            "propagate": False,
        },
        "apps": {
            "handlers": ["file", "console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# Cache Configuration (Redis recommended for production)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env("REDIS_URL", default="redis://127.0.0.1:6379/1"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}

# Static and Media Files
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_ROOT = BASE_DIR / "media"

# File Upload Settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
FILE_UPLOAD_TEMP_DIR = BASE_DIR / "temp"

# Email Configuration (for local notifications)
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST", default="localhost")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@avicast.local")

# Mobile App Integration Settings
MOBILE_APP_SETTINGS = {
    "API_VERSION": "v1",
    "TOKEN_EXPIRE_HOURS": 24,
    "MAX_DEVICES_PER_USER": 3,
    "ALLOWED_MOBILE_ORIGINS": [
        "capacitor://localhost",
        "ionic://localhost",
        "http://localhost:8100",  # Ionic dev server
    ],
}

# Database Backup Settings
BACKUP_SETTINGS = {
    "BACKUP_DIR": BASE_DIR / "backups",
    "BACKUP_RETENTION_DAYS": 30,
    "AUTO_BACKUP": True,
    "BACKUP_TIME": "02:00",  # 2 AM
}

# Performance Settings
CONN_MAX_AGE = 60
OPTIMIZE_TABLE_QUERIES = True
