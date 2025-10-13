# Maintenance Scripts

This directory contains database maintenance and utility scripts for the AVICAST platform.

## Scripts

### Database Field Management
- `add_missing_fields.py` - Adds missing fields to database tables
- `add_optimization_status.py` - Adds optimization status tracking fields
- `add_remaining_fields.py` - Adds remaining required fields to models

### Database Maintenance
- `check_db.py` - Checks database integrity and structure
- `fix_table_name.py` - Fixes incorrect table names in database
- `rename_table.py` - Renames database tables

## Usage

These scripts are typically run once during database migrations or when fixing database issues. Always backup your database before running any maintenance scripts.

```bash
# Backup database first
python scripts/database/database_maintenance.py backup

# Run maintenance script
python scripts/maintenance/script_name.py
```

## Safety

- Always test on development database first
- Create backups before running
- Review script changes before applying to production
- Log all maintenance operations

For more information, see: [AGENTS.md §Database Management](../../AGENTS.md)

