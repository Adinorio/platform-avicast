@echo off
REM AVICAST Portable Version Builder
REM Creates a portable version that doesn't need installation

echo 🚀 AVICAST Portable Builder
echo ==========================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.11+ first.
    pause
    exit /b 1
)

echo ✅ Python is installed

REM Install PyInstaller if not present
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

REM Clean previous builds
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
if exist "AVICAST-Portable" rmdir /s /q "AVICAST-Portable"

REM Build the executable
echo 🔨 Building AVICAST executable...
python build-exe.py

REM Create portable directory structure
echo 📦 Creating portable package...
mkdir "AVICAST-Portable"
mkdir "AVICAST-Portable\data"
mkdir "AVICAST-Portable\logs"
mkdir "AVICAST-Portable\backups"

REM Copy executable
copy "dist\AVICAST.exe" "AVICAST-Portable\"

REM Copy essential files
xcopy "templates" "AVICAST-Portable\templates\" /E /I
xcopy "static" "AVICAST-Portable\static\" /E /I
xcopy "apps" "AVICAST-Portable\apps\" /E /I
xcopy "avicast_project" "AVICAST-Portable\avicast_project\" /E /I
xcopy "management" "AVICAST-Portable\management\" /E /I
xcopy "config" "AVICAST-Portable\config\" /E /I

REM Copy configuration files
copy "env.example" "AVICAST-Portable\"
copy "requirements.txt" "AVICAST-Portable\"
copy "pyproject.toml" "AVICAST-Portable\"

REM Create portable launcher
echo @echo off > "AVICAST-Portable\Start AVICAST.bat"
echo echo 🚀 Starting AVICAST Portable... >> "AVICAST-Portable\Start AVICAST.bat"
echo echo. >> "AVICAST-Portable\Start AVICAST.bat"
echo. >> "AVICAST-Portable\Start AVICAST.bat"
echo REM Check if database exists >> "AVICAST-Portable\Start AVICAST.bat"
echo if not exist "data\db.sqlite3" ( >> "AVICAST-Portable\Start AVICAST.bat"
echo     echo Setting up database... >> "AVICAST-Portable\Start AVICAST.bat"
echo     AVICAST.exe migrate >> "AVICAST-Portable\Start AVICAST.bat"
echo ^) >> "AVICAST-Portable\Start AVICAST.bat"
echo. >> "AVICAST-Portable\Start AVICAST.bat"
echo echo Starting AVICAST server... >> "AVICAST-Portable\Start AVICAST.bat"
echo echo. >> "AVICAST-Portable\Start AVICAST.bat"
echo echo 🌐 Access: http://localhost:8000 >> "AVICAST-Portable\Start AVICAST.bat"
echo echo 👤 Login: 010101 / avicast123 >> "AVICAST-Portable\Start AVICAST.bat"
echo echo. >> "AVICAST-Portable\Start AVICAST.bat"
echo AVICAST.exe runserver 0.0.0.0:8000 >> "AVICAST-Portable\Start AVICAST.bat"
echo pause >> "AVICAST-Portable\Start AVICAST.bat"

REM Create README
echo AVICAST Portable - Wildlife Monitoring System > "AVICAST-Portable\README.txt"
echo ============================================= >> "AVICAST-Portable\README.txt"
echo. >> "AVICAST-Portable\README.txt"
echo QUICK START: >> "AVICAST-Portable\README.txt"
echo 1. Double-click "Start AVICAST.bat" >> "AVICAST-Portable\README.txt"
echo 2. Open browser: http://localhost:8000 >> "AVICAST-Portable\README.txt"
echo 3. Login: Employee ID: 010101, Password: avicast123 >> "AVICAST-Portable\README.txt"
echo. >> "AVICAST-Portable\README.txt"
echo NETWORK ACCESS: >> "AVICAST-Portable\README.txt"
echo - Other computers: http://YOUR_IP:8000 >> "AVICAST-Portable\README.txt"
echo - Find your IP: Run 'ipconfig' in command prompt >> "AVICAST-Portable\README.txt"
echo. >> "AVICAST-Portable\README.txt"
echo DATA STORAGE: >> "AVICAST-Portable\README.txt"
echo - Database: data\db.sqlite3 >> "AVICAST-Portable\README.txt"
echo - Uploads: data\media\ >> "AVICAST-Portable\README.txt"
echo - Logs: logs\ >> "AVICAST-Portable\README.txt"
echo. >> "AVICAST-Portable\README.txt"
echo No installation required! Just run and go! 🐦 >> "AVICAST-Portable\README.txt"

REM Copy documentation
xcopy "docs" "AVICAST-Portable\docs\" /E /I

echo.
echo 🎉 AVICAST Portable Build Complete!
echo ==================================
echo.
echo 📁 Output: AVICAST-Portable\ folder
echo 🚀 Ready to distribute!
echo.
echo 📋 Features:
echo    ✅ No installation required
echo    ✅ Portable - runs from any folder
echo    ✅ Self-contained executable
echo    ✅ All data stored locally
echo    ✅ Easy to backup and move
echo.
echo 🐦 Happy bird monitoring!
pause
