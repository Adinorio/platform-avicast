# Configuration Directory

This directory contains configuration files and settings for the AVICAST platform.

## Configuration Files

### `storage_optimization_settings.py`
Storage optimization configuration including:
- Storage tier definitions (HOT, WARM, COLD, ARCHIVE)
- Storage lifecycle policies
- Optimization thresholds and parameters
- Storage monitoring settings

## Usage

Import configuration in your Django settings:
```python
from config.storage_optimization_settings import *
```

## Configuration Management

- Keep configuration separate from application code
- Use environment variables for sensitive settings
- Document all configuration options
- Version control configuration templates, not production values

## Note
Configuration files should be reviewed and updated when deploying to different environments.
