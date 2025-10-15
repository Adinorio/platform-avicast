@echo off
REM AVICAST Local Network Deployment Script for Windows
REM Quick setup for local network deployment

echo 🚀 AVICAST Local Network Deployment
echo ==================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.11+ first.
    pause
    exit /b 1
)

echo ✅ Python is installed

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo 📥 Installing dependencies...
pip install -r requirements.txt
pip install -r requirements-processing.txt

REM Create .env file if it doesn't exist
if not exist ".env" (
    echo ⚙️ Creating environment configuration...
    copy env.example .env
    echo 📝 Please edit .env file with your database settings
)

REM Run migrations
echo 🗄️ Setting up database...
python manage.py migrate

REM Create superuser if it doesn't exist
echo 👤 Creating superuser account...
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser(employee_id='010101', first_name='System', last_name='Administrator', email='admin@avicast.local', password='avicast123') if not User.objects.filter(employee_id='010101').exists() else print('Superuser already exists')"

REM Collect static files
echo 📁 Collecting static files...
python manage.py collectstatic --noinput

REM Get server IP address
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4 Address"') do (
    for /f "tokens=1" %%b in ("%%a") do set SERVER_IP=%%b
    goto :found
)
:found

echo.
echo 🎉 AVICAST Deployment Complete!
echo ===============================
echo.
echo 🌐 Server Information:
echo    Local Access:    http://localhost:8000
echo    Network Access:  http://%SERVER_IP%:8000
echo.
echo 👤 Default Login:
echo    Employee ID:     010101
echo    Password:        avicast123
echo    ⚠️  Change password on first login!
echo.
echo 📋 Next Steps:
echo    1. Open browser and go to: http://%SERVER_IP%:8000
echo    2. Login with the credentials above
echo    3. Change the default password
echo    4. Create user accounts for your team
echo.
echo 🔄 To start the server:
echo    venv\Scripts\activate.bat
echo    python manage.py runserver 0.0.0.0:8000
echo.
echo 🛑 To stop the server: Press Ctrl+C
echo.
echo 📚 For more deployment options, see: docs\LOCAL_NETWORK_DEPLOYMENT_GUIDE.md
echo.
echo Happy bird monitoring! 🐦
pause
