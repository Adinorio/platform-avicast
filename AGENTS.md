# AGENTS.md

## Project Overview

AVICAST is a comprehensive wildlife monitoring and analytics platform built with Django. It's designed for local deployment with strict data privacy controls, featuring bird detection using YOLO models, user management, location tracking, and analytics dashboards.

**Key Technologies:**
- Django 4.2.23 (Python web framework)
- PostgreSQL/SQLite (database)
- YOLO/Ultralytics (AI bird detection)
- Plotly (data visualization)
- Local deployment only (no cloud storage)

**Mobile Integration:**
- Separate Flutter/Dart application for mobile functionality
- Django backend provides API endpoints for data import/export
- Focus on bird/species data, user management, and location tracking APIs

## Setup Commands

### Initial Setup
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate.bat
# Linux/macOS:
source venv/bin/activate

# Install core dependencies
pip install -r requirements.txt

# Install AI/ML dependencies (for image processing)
pip install -r requirements-processing.txt

# Copy environment file
copy env.example .env  # Windows
cp env.example .env    # Linux/macOS
```

### Database Setup
```bash
# Create and apply migrations
python manage.py makemigrations
python manage.py migrate

# Create default superadmin user
python create_default_user.py
```

### Development Server
```bash
# Start development server (local only)
python manage.py runserver 127.0.0.1:8000

# Check system health
python manage.py check
```

## Code Style

- **Python**: Follow PEP 8 with Ruff formatting
- **Line length**: 100 characters (configured in pyproject.toml)
- **Quotes**: Double quotes for strings
- **Django**: Use Django best practices and conventions
- **Security**: Always validate user input, use Django's built-in security features
- **Local-first**: Never implement cloud storage or external API calls

## File Organization & Size Guidelines

### File Size Limits
- **Python files**: Maximum 500 lines per file
- **JavaScript files**: Maximum 300 lines per file
- **CSS files**: Maximum 400 lines per file
- **HTML templates**: Maximum 200 lines per file
- **Configuration files**: Maximum 100 lines per file

### Separation of Concerns
- **Views**: Split large view files into multiple files by functionality
- **Models**: One model per file for complex models, group related simple models
- **Templates**: Break large templates into reusable components
- **Static files**: Separate CSS, JS, and images into logical directories
- **API endpoints**: Group related endpoints in separate view files

### File Structure Best Practices
```
apps/example/
├── models/
│   ├── __init__.py
│   ├── user.py          # User model only
│   ├── profile.py       # Profile model only
│   └── permissions.py   # Permission models
├── views/
│   ├── __init__.py
│   ├── user_views.py    # User-related views
│   ├── profile_views.py # Profile-related views
│   └── api_views.py     # API endpoints
├── templates/example/
│   ├── base.html        # Base template
│   ├── components/      # Reusable components
│   │   ├── navbar.html
│   │   └── sidebar.html
│   ├── user/           # User-specific templates
│   └── profile/        # Profile-specific templates
└── static/example/
    ├── css/
    │   ├── main.css     # Main styles
    │   ├── components/  # Component-specific styles
    │   └── pages/       # Page-specific styles
    ├── js/
    │   ├── main.js      # Main JavaScript
    │   ├── components/  # Component-specific JS
    │   └── utils/       # Utility functions
    └── images/
```

### Refactoring Guidelines
- **Split large files**: When a file exceeds size limits, split by functionality
- **Extract common code**: Create utility modules for repeated code
- **Component-based**: Use Django template inheritance and includes
- **Modular JavaScript**: Use ES6 modules or separate script files
- **CSS organization**: Use BEM methodology and separate concerns

## Testing Instructions

### Run Tests
```bash
# Run all Django tests
python manage.py test

# Run specific app tests
python manage.py test apps.users
python manage.py test apps.locations
python manage.py test apps.fauna
python manage.py test apps.analytics

# Run AI/ML integration tests
python tests/test_model_integration.py
python tests/test_pipeline_integration.py
python tests/test_classifier_integration.py

# Run image processing tests
python scripts/testing/test_image_processing.py
python scripts/testing/test_bird_detection.py
```

### Test Coverage
- Always add tests for new features
- Test both success and failure scenarios
- Include integration tests for AI/ML components
- Test API endpoints with proper authentication

## Development Guidelines

### Django Apps Structure
- `apps/users/` - User management and authentication
- `apps/locations/` - Site and census data management
- `apps/fauna/` - Species monitoring and observations
- `apps/analytics/` - Data visualization and reporting
- `apps/image_processing/` - AI/ML bird detection pipeline
- `apps/weather/` - Weather data integration
- `apps/common/` - Shared utilities and services

### Security Requirements
- **Local deployment only** - No external network access
- **Role-based access control** - SUPERADMIN, ADMIN, USER roles
- **Input validation** - Always validate and sanitize user input
- **CSRF protection** - Use Django's built-in CSRF middleware
- **Rate limiting** - Implement for API endpoints
- **Audit logging** - Log all user actions

### AI/ML Integration
- **Model storage**: Store YOLO models in `models/` directory
- **Training data**: Use `training_data/` for datasets
- **Processing**: All image processing in `apps/image_processing/`
- **Testing**: Always test model integration before deployment

### Large File Management
- **Split large Python files**: Break into logical modules (max 500 lines)
- **Separate concerns**: Keep models, views, and utilities in separate files
- **Template components**: Use Django template includes for reusable UI components
- **Static file organization**: Group CSS/JS by functionality, not by size
- **Configuration files**: Keep settings modular and environment-specific

## Database Management

### Migrations
```bash
# Create migrations for changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Check migration status
python manage.py showmigrations

# Reset migrations (WARNING: Data loss)
python manage.py migrate --fake-initial
```

### Database Maintenance
```bash
# Create backup
python database_maintenance.py backup

# Check database health
python database_maintenance.py health

# Optimize performance
python database_maintenance.py optimize
```

## File Organization

### Excluded Files (Git)
- **ML Models**: `.pt` files (YOLO models) - too large for Git
- **Datasets**: `dataset/` folder with training images
- **Training Outputs**: `runs/` folder with model results
- **Media Files**: Large images, videos, audio files
- **Database Files**: `.sqlite3`, `.db` files

### Important Directories
- `media/` - User uploaded files (excluded from Git)
- `static/` - Static assets (CSS, JS, images)
- `templates/` - Django HTML templates
- `docs/` - Project documentation
- `scripts/` - Utility and setup scripts

## API Development

### RESTful Endpoints
- Base URL: `/api/v1/`
- Authentication: Employee ID + password
- CORS: Configured for local network only
- Rate limiting: Implemented for security

### Mobile Integration (Secondary Priority)
- **Separate Flutter/Dart app**: Mobile functionality handled by external application
- **Data import/export**: Focus on API endpoints for data exchange between Django backend and Flutter app
- **Authentication**: Use Django's session-based auth for API access
- **Local network sync**: API endpoints for data synchronization
- **Core focus**: Bird/species data, user management, and location tracking APIs

## Deployment

### Local Network Setup
```bash
# Production server (local network access)
python manage.py runserver 0.0.0.0:8000

# Configure firewall to block external connections
# Access via: http://your-local-ip:8000
```

### Environment Configuration
- **Development**: Use `avicast_project/settings/development.py`
- **Production**: Use `avicast_project/settings/production.py`
- **Environment variables**: Store in `.env` file (excluded from Git)

## Troubleshooting

### Common Issues
- **ModuleNotFoundError**: Activate virtual environment first
- **Database errors**: Run migrations and check database connection
- **Static files**: Run `python manage.py collectstatic`
- **Port conflicts**: Use different port with `--port` flag

### Debug Commands
```bash
# Django shell for debugging
python manage.py shell

# Check system configuration
python manage.py check --deploy

# View current settings
python manage.py diffsettings
```

## Contributing

### Code Changes
1. Create feature branch from main
2. Follow code style guidelines
3. Add comprehensive tests
4. Update documentation if needed
5. Test locally before submitting

### Pull Request Guidelines
- **Title format**: `[APP_NAME] Brief description`
- **Description**: Include what changed and why
- **Testing**: Confirm all tests pass
- **Security**: Review for security implications

### File Size Enforcement
- **Pre-commit checks**: Use tools to detect oversized files
- **Code review**: Flag files that exceed size limits
- **Refactoring**: Split large files before merging
- **Documentation**: Update file structure docs when reorganizing

## Security Checklist

- [ ] No external API calls or cloud storage
- [ ] Input validation on all user inputs
- [ ] CSRF protection enabled
- [ ] Rate limiting implemented
- [ ] Audit logging for sensitive operations
- [ ] Role-based access control enforced
- [ ] Local network access only

## Performance Considerations

- **Database**: Use PostgreSQL for production
- **Static files**: Serve via web server (nginx/Apache)
- **Caching**: Implement Django caching for frequently accessed data
- **Image processing**: Optimize YOLO model inference
- **Memory**: Monitor memory usage with large datasets

## Development Efficiency & Problem Prevention

### Common Issues & Quick Fixes
```bash
# ModuleNotFoundError: No module named 'openpyxl'
pip install openpyxl

# PowerShell Execution Policy Error
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Port Already in Use
python manage.py runserver 8001

# Database Migration Issues
python manage.py migrate --fake-initial
# Or recreate database
del db.sqlite3 && python manage.py migrate

# Missing Static Directory
mkdir static

# Virtual Environment Issues
python -m venv venv --clear
venv\Scripts\activate.bat  # Windows
source venv/bin/activate   # Linux/macOS
```

### Development Workflow Optimization
```bash
# Quick development cycle
python manage.py runserver 127.0.0.1:8000  # Start server
python manage.py check                     # Check for issues
python manage.py test                      # Run tests
python manage.py makemigrations           # Create migrations
python manage.py migrate                   # Apply migrations
```

### Debugging & Troubleshooting
```bash
# Django shell for debugging
python manage.py shell

# Check system configuration
python manage.py check --deploy

# View current settings
python manage.py diffsettings

# Check database connection
python manage.py dbshell

# View migration status
python manage.py showmigrations
```

### Code Quality & Maintenance
```bash
# Format code with Ruff
ruff format .

# Check code quality
ruff check .

# Sort imports
ruff check --select I --fix

# Run all quality checks
ruff check . && ruff format --check .
```

### Database Management & Maintenance
```bash
# Create backup
python database_maintenance.py backup

# Check database health
python database_maintenance.py health

# Optimize performance
python database_maintenance.py optimize

# List backups
python database_maintenance.py list

# Schedule maintenance
python database_maintenance.py schedule
```

### AI/ML Model Management
```bash
# Test model integration
python tests/test_model_integration.py

# Test pipeline integration
python tests/test_pipeline_integration.py

# Test classifier integration
python tests/test_classifier_integration.py

# Test image processing
python scripts/testing/test_image_processing.py

# Test bird detection
python scripts/testing/test_bird_detection.py
```

### Environment & Configuration
```bash
# Copy environment file
copy env.example .env  # Windows
cp env.example .env    # Linux/macOS

# Check environment variables
python -c "import os; print(os.environ.get('SECRET_KEY', 'Not set'))"

# Validate configuration
python scripts/validate_config.py
```

### File Organization & Cleanup
```bash
# Check file sizes (Windows)
for /f %i in ('dir /s /b *.py') do @echo %i: %~zi bytes

# Check file sizes (Linux/macOS)
find . -name "*.py" -exec wc -l {} + | sort -n

# Clean up temporary files
python management/commands/cleanup_storage.py

# Remove __pycache__ directories
find . -type d -name "__pycache__" -exec rm -rf {} +
```

### Git & Version Control
```bash
# Check for large files before committing
git ls-files | xargs ls -la | sort -k5 -rn | head -10

# Check repository size
du -sh .git

# Clean up Git history
git gc --prune=now
```

### Monitoring & Health Checks
```bash
# Check system health
python manage.py check

# Monitor model usage
python scripts/monitor_model_usage.py

# Check user accounts
python scripts/check_users.py

# Analyze Git files
python scripts/analyze_git_files.py
```

### Development Best Practices
- **Always activate virtual environment** before working
- **Run tests before committing** changes
- **Check file sizes** before adding to repository
- **Use descriptive commit messages** with app name prefix
- **Keep dependencies updated** but test thoroughly
- **Document complex logic** with clear comments
- **Use type hints** for better code clarity
- **Implement proper error handling** for all user inputs

### Emergency Recovery
```bash
# Reset to clean state
git clean -fd
git reset --hard HEAD

# Recreate virtual environment
rm -rf venv
python -m venv venv
venv\Scripts\activate.bat  # Windows
source venv/bin/activate   # Linux/macOS
pip install -r requirements.txt

# Reset database
del db.sqlite3
python manage.py migrate
python create_default_user.py
```

---

**Remember**: This is a local-only platform. Never implement features that require external network access or cloud storage.
