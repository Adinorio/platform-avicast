# Scripts Directory

This directory contains utility scripts organized by functionality for the AVICAST platform.

## Directory Structure

### `database/`
Database maintenance, setup, and utility scripts:
- `add_all_columns.py` - Add missing database columns
- `add_column.py` - Add individual database columns
- `check_table.py` - Verify table structure
- `fix_db.py` - Database repair utilities
- `check_data.py` - Data validation scripts
- `database_maintenance.py` - Database maintenance tasks
- `setup_database.py` - Database initialization

### `debugging/`
Debugging and troubleshooting scripts:
- `fix_image_processing.py` - Image processing URL debugging
- `debug_urls.py` - URL pattern debugging

### `setup/`
System setup and user management scripts:
- `create_default_user.py` - Create initial admin user
- `check_current_users.py` - User verification scripts

### `testing/`
Testing and verification scripts:
- `check_ai_status.py` - AI dependency verification
- `test_image_processing.py` - Image processing system tests

## Usage

Run scripts from the project root directory:
```bash
python scripts/database/setup_database.py
python scripts/debugging/fix_image_processing.py
```

## Note
These scripts are development utilities and should not be run in production without proper review.
