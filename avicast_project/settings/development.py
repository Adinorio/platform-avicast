from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"]

# Force HTTP for development server
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SECURE_CONTENT_TYPE_NOSNIFF = False
SECURE_BROWSER_XSS_FILTER = False
SECURE_REFERRER_POLICY = None

# Add any development specific apps here
INSTALLED_APPS += []

# --- TEMPLATE DEBUGGING SETTINGS ---
# Force template reloading and disable caching
TEMPLATES[0]['OPTIONS']['debug'] = True

# --- END TEMPLATE DEBUGGING SETTINGS ---

# --- TEMPORARY SETTINGS FOR DEVELOPMENT ---
# TODO: Create a .env file with these values
# SECRET_KEY will be loaded from environment or .env file
# --- END TEMPORARY SETTINGS ---
