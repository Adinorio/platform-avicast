# Troubleshooting Guide

This guide covers common issues you might encounter when setting up or running the Platform Avicast project.

## Common Setup Issues

### 1. ModuleNotFoundError: No module named 'openpyxl'

**Symptoms**: Django commands fail with import errors for openpyxl or other packages.

**Causes**:
- Virtual environment not activated
- Packages not installed
- Wrong Python interpreter being used

**Solutions**:
```bash
# 1. Activate virtual environment
venv\Scripts\activate.bat  # Windows
source venv/bin/activate   # Linux/macOS

# 2. Verify activation (should see (venv) in prompt)
# 3. Install requirements
pip install -r requirements.txt

# 4. Verify installation
pip list | grep openpyxl
```

### 2. PowerShell Execution Policy Error

**Symptoms**: 
```
File cannot be loaded because running scripts is disabled on this system.
```

**Solution**: Run PowerShell as Administrator and execute:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 3. Missing Static Directory Warning

**Symptoms**: 
```
System check identified some issues:
WARNINGS:
?: (staticfiles.W004) The directory '...\static' in the STATICFILES_DIRS setting does not exist.
```

**Solution**: Create the static directory:
```bash
mkdir static
```

### 4. Database Migration Issues

**Symptoms**: 
```
You have X unapplied migration(s). Your project may not work properly until you apply the migrations.
```

**Solution**: Apply pending migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Port Already in Use

**Symptoms**: 
```
Error: That port is already in use.
```

**Solution**: Use a different port or kill the process:
```bash
# Use different port
python manage.py runserver 8001

# Or kill process on port 8000 (Windows)
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

## Development Issues

### 1. Changes Not Reflecting

**Symptoms**: Code changes don't appear in the browser.

**Solutions**:
- Restart the Django server
- Clear browser cache
- Check if DEBUG=True in settings
- Verify file is saved

### 2. Import Errors in Views

**Symptoms**: Import errors when accessing certain pages.

**Solutions**:
- Check virtual environment is activated
- Verify all packages are installed
- Check import statements in views.py files
- Restart Django server

### 3. Template Not Found Errors

**Symptoms**: 
```
TemplateDoesNotExist at /url/
```

**Solutions**:
- Check template file exists in correct directory
- Verify template name in render() call
- Check TEMPLATES setting in settings.py
- Clear Python cache: `python manage.py clear_cache`

## Performance Issues

### 1. Slow Page Loads

**Symptoms**: Pages take a long time to load.

**Solutions**:
- Check database queries (use Django Debug Toolbar)
- Optimize database indexes
- Use select_related() and prefetch_related()
- Enable database connection pooling

### 2. Memory Issues

**Symptoms**: High memory usage or crashes.

**Solutions**:
- Check for memory leaks in views
- Use pagination for large datasets
- Optimize file uploads
- Monitor memory usage

## Database Issues

### 1. SQLite Lock Errors

**Symptoms**: Database locked errors.

**Solutions**:
- Close any database browsers
- Check for multiple Django processes
- Use PostgreSQL for production
- Restart Django server

### 2. Migration Conflicts

**Symptoms**: Migration errors or conflicts.

**Solutions**:
```bash
# Show migration status
python manage.py showmigrations

# Fake migrations if needed
python manage.py migrate --fake

# Reset migrations (DANGEROUS - only in development)
python manage.py migrate --fake-initial
```

## Environment Issues

### 1. Environment Variables Not Loading

**Symptoms**: Settings not reading from .env file.

**Solutions**:
- Check .env file exists in project root
- Verify django-environ is installed
- Check .env file format (no spaces around =)
- Restart Django server

### 2. Wrong Python Version

**Symptoms**: Compatibility errors or unexpected behavior.

**Solutions**:
```bash
# Check Python version
python --version

# Should be Python 3.11 or higher
# If not, install correct version and recreate venv
```

## Getting Help

If you encounter an issue not covered here:

1. Check the Django documentation
2. Search Django forums and Stack Overflow
3. Check the project's issue tracker
4. Provide detailed error messages and context

## Useful Commands

```bash
# Check Django status
python manage.py check

# Show all migrations
python manage.py showmigrations

# Collect static files
python manage.py collectstatic

# Create superuser
python manage.py createsuperuser

# Shell access
python manage.py shell

# Test database connection
python manage.py dbshell
```
