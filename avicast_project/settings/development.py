from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"]

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
