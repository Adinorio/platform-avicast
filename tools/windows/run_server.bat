@echo off
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Checking if requests is installed...
python -c "import requests; print('✅ requests is installed')" 2>nul
if errorlevel 1 (
    echo Installing requests...
    pip install requests
)

echo Starting Django server...
echo.
echo Server will be available at: http://127.0.0.1:8000/
echo Press Ctrl+C to stop the server
echo.
python manage.py runserver
