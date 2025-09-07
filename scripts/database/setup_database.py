#!/usr/bin/env python3
"""
Database Setup Script for Platform Avicast
This script helps set up PostgreSQL database for local-only deployment
"""

import getpass
import subprocess
import sys
from pathlib import Path


def run_command(command, check=True):
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(command, shell=True, check=check, capture_output=True, text=True)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}")
        print(f"Error: {e}")
        return None


def check_postgresql():
    """Check if PostgreSQL is installed and running"""
    print("Checking PostgreSQL installation...")

    # Check if psql is available
    result = run_command("psql --version", check=False)
    if result and result.returncode == 0:
        print("✓ PostgreSQL client found")
        return True
    else:
        print("✗ PostgreSQL client not found")
        return False


def create_database():
    """Create the database and user"""
    print("\nSetting up database...")

    # Get database credentials
    db_name = input("Enter database name (default: avicast_db): ").strip() or "avicast_db"
    db_user = input("Enter database user (default: avicast): ").strip() or "avicast"
    db_password = getpass.getpass("Enter database password: ")

    if not db_password:
        print("Error: Database password is required")
        return False

    # Create database user
    print(f"Creating database user '{db_user}'...")
    create_user_cmd = (
        f"psql -U postgres -c \"CREATE USER {db_user} WITH PASSWORD '{db_password}';\""
    )
    result = run_command(create_user_cmd, check=False)

    if result and result.returncode == 0:
        print("✓ Database user created successfully")
    else:
        print("! User might already exist or there was an error")

    # Create database
    print(f"Creating database '{db_name}'...")
    create_db_cmd = f'psql -U postgres -c "CREATE DATABASE {db_name} OWNER {db_user};"'
    result = run_command(create_db_cmd, check=False)

    if result and result.returncode == 0:
        print("✓ Database created successfully")
    else:
        print("! Database might already exist or there was an error")

    # Grant privileges
    print("Granting privileges...")
    grant_cmd = f'psql -U postgres -d {db_name} -c "GRANT ALL PRIVILEGES ON DATABASE {db_name} TO {db_user};"'
    result = run_command(grant_cmd, check=False)

    if result and result.returncode == 0:
        print("✓ Privileges granted successfully")
    else:
        print("! Error granting privileges")

    # Create .env file
    create_env_file(db_name, db_user, db_password)

    return True


def create_env_file(db_name, db_user, db_password):
    """Create or update .env file with database configuration"""
    env_content = f"""# Django Settings
DEBUG=False
SECRET_KEY={generate_secret_key()}

# Database Configuration
DATABASE_URL=postgresql://{db_user}:{db_password}@localhost:5432/{db_name}

# Host Configuration (restrict to local network)
ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.0/24,10.0.0.0/8,172.16.0.0/12

# Redis Cache (optional)
REDIS_URL=redis://127.0.0.1:6379/1

# Security Settings
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://192.168.1.0:3000

# Email Configuration (for local notifications)
EMAIL_HOST=localhost
EMAIL_PORT=587
EMAIL_USE_TLS=False
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=noreply@avicast.local

# Logging
LOG_LEVEL=INFO
TIME_ZONE=UTC
LANGUAGE_CODE=en-us
"""

    env_file = Path(".env")
    with open(env_file, "w") as f:
        f.write(env_content)

    print(f"✓ Environment file created: {env_file}")


def generate_secret_key():
    """Generate a secure secret key"""
    from django.core.management.utils import get_random_secret_key

    return get_random_secret_key()


def setup_directories():
    """Create necessary directories"""
    print("\nCreating necessary directories...")

    directories = ["logs", "backups", "media", "staticfiles", "temp"]

    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✓ Created directory: {directory}")


def install_requirements():
    """Install Python requirements"""
    print("\nInstalling Python requirements...")

    result = run_command("pip install -r requirements.txt", check=False)
    if result and result.returncode == 0:
        print("✓ Requirements installed successfully")
    else:
        print("✗ Error installing requirements")
        return False

    return True


def run_migrations():
    """Run Django migrations"""
    print("\nRunning database migrations...")

    result = run_command("python manage.py makemigrations", check=False)
    if result and result.returncode == 0:
        print("✓ Migrations created successfully")
    else:
        print("! Error creating migrations")

    result = run_command("python manage.py migrate", check=False)
    if result and result.returncode == 0:
        print("✓ Migrations applied successfully")
    else:
        print("✗ Error applying migrations")
        return False

    return True


def create_superuser():
    """Create a superuser account"""
    print("\nCreating superuser account...")

    create_superuser_cmd = "python manage.py createsuperuser"
    print(f"Please run: {create_superuser_cmd}")
    print("Or press Enter to skip for now...")
    input()


def main():
    """Main setup function"""
    print("=" * 60)
    print("Platform Avicast - Database Setup")
    print("=" * 60)
    print("This script will help you set up PostgreSQL for local-only deployment")
    print()

    # Check if we're in the right directory
    if not Path("manage.py").exists():
        print("Error: Please run this script from the project root directory")
        sys.exit(1)

    # Check PostgreSQL
    if not check_postgresql():
        print("\nPlease install PostgreSQL first:")
        print("Windows: Download from https://www.postgresql.org/download/windows/")
        print("macOS: brew install postgresql")
        print("Ubuntu: sudo apt-get install postgresql postgresql-contrib")
        sys.exit(1)

    # Setup database
    if not create_database():
        print("Error: Failed to create database")
        sys.exit(1)

    # Setup directories
    setup_directories()

    # Install requirements
    if not install_requirements():
        print("Error: Failed to install requirements")
        sys.exit(1)

    # Run migrations
    if not run_migrations():
        print("Error: Failed to run migrations")
        sys.exit(1)

    # Create superuser
    create_superuser()

    print("\n" + "=" * 60)
    print("Setup completed successfully!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Start the Django server: python manage.py runserver")
    print("2. Access the admin interface at: http://localhost:8000/admin/")
    print("3. Configure your mobile app to connect to: http://localhost:8000/api/")
    print("\nSecurity notes:")
    print("- Database is configured for local-only access")
    print("- CORS is restricted to local network")
    print("- Rate limiting and login attempt tracking enabled")
    print("- All data stays within your local network")


if __name__ == "__main__":
    main()
