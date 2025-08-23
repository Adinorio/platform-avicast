@echo off
echo ========================================
echo    AVICAST Platform Setup Script
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

echo ✅ Python found
echo.

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo 🆕 Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ❌ Failed to create virtual environment
        pause
        exit /b 1
    )
    echo ✅ Virtual environment created
) else (
    echo ℹ️  Virtual environment already exists
)

REM Activate virtual environment
echo 🔄 Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ Failed to activate virtual environment
    pause
    exit /b 1
)

REM Install requirements
echo 📦 Installing requirements...
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ Failed to install requirements
    pause
    exit /b 1
)

REM Create static directory
if not exist "static" (
    echo 📁 Creating static directory...
    mkdir static
    echo ✅ Static directory created
)

REM Run Django checks
echo 🔍 Running Django checks...
python manage.py check
if errorlevel 1 (
    echo ❌ Django check failed
    pause
    exit /b 1
)

REM Run migrations
echo 🗄️  Running database migrations...
python manage.py migrate
if errorlevel 1 (
    echo ❌ Migrations failed
    pause
    exit /b 1
)

REM Create default superadmin user
echo 👤 Creating default superadmin user...
python create_default_user.py
if errorlevel 1 (
    echo ❌ Failed to create default user
    pause
    exit /b 1
)

echo.
echo ========================================
echo    ✅ Setup Complete!
echo ========================================
echo.
echo 🚀 To start the server:
echo    python manage.py runserver
echo.
echo 🔑 Default login credentials:
echo    Username: 010101
echo    Password: avicast123
echo.
echo 🌐 Access your app at: http://localhost:8000
echo.
pause
