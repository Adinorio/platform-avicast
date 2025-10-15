@echo off
REM AVICAST Windows Installer Builder
REM Creates a complete Windows installer package

echo 🚀 AVICAST Windows Installer Builder
echo ====================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.11+ first.
    pause
    exit /b 1
)

echo ✅ Python is installed

REM Install PyInstaller if not present
echo 📦 Checking PyInstaller...
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
    echo ✅ PyInstaller installed
) else (
    echo ✅ PyInstaller is already installed
)

REM Clean previous builds
echo 🧹 Cleaning previous builds...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
if exist "AVICAST-Setup-*.exe" del /q "AVICAST-Setup-*.exe"

REM Build the executable
echo 🔨 Building AVICAST executable...
python build-exe.py

REM Create startup script
echo 📝 Creating startup script...
echo @echo off > start-avicast.bat
echo echo Starting AVICAST Wildlife Monitoring System... >> start-avicast.bat
echo echo. >> start-avicast.bat
echo echo Please wait while the system initializes... >> start-avicast.bat
echo echo. >> start-avicast.bat
echo. >> start-avicast.bat
echo REM Check if database exists, if not run migrations >> start-avicast.bat
echo if not exist "db.sqlite3" ( >> start-avicast.bat
echo     echo Setting up database... >> start-avicast.bat
echo     AVICAST.exe migrate >> start-avicast.bat
echo ^) >> start-avicast.bat
echo. >> start-avicast.bat
echo REM Start the server >> start-avicast.bat
echo echo Starting server... >> start-avicast.bat
echo echo. >> start-avicast.bat
echo echo AVICAST is now running! >> start-avicast.bat
echo echo. >> start-avicast.bat
echo echo Access the system at: http://localhost:8000 >> start-avicast.bat
echo echo. >> start-avicast.bat
echo echo Default Login: >> start-avicast.bat
echo echo   Employee ID: 010101 >> start-avicast.bat
echo echo   Password: avicast123 >> start-avicast.bat
echo echo. >> start-avicast.bat
echo echo Press Ctrl+C to stop the server >> start-avicast.bat
echo echo. >> start-avicast.bat
echo AVICAST.exe runserver 0.0.0.0:8000 >> start-avicast.bat
echo. >> start-avicast.bat
echo pause >> start-avicast.bat

REM Create uninstaller script
echo 📝 Creating uninstaller script...
echo @echo off > uninstall.bat
echo echo Uninstalling AVICAST... >> uninstall.bat
echo echo. >> uninstall.bat
echo. >> uninstall.bat
echo REM Stop any running processes >> uninstall.bat
echo taskkill /f /im AVICAST.exe 2^>nul >> uninstall.bat
echo. >> uninstall.bat
echo REM Remove files >> uninstall.bat
echo if exist "AVICAST.exe" del /q "AVICAST.exe" >> uninstall.bat
echo if exist "db.sqlite3" del /q "db.sqlite3" >> uninstall.bat
echo if exist "media" rmdir /s /q "media" >> uninstall.bat
echo if exist "staticfiles" rmdir /s /q "staticfiles" >> uninstall.bat
echo if exist "logs" rmdir /s /q "logs" >> uninstall.bat
echo. >> uninstall.bat
echo echo AVICAST has been uninstalled. >> uninstall.bat
echo pause >> uninstall.bat

REM Check if NSIS is available for advanced installer
echo 🔍 Checking for NSIS (Nullsoft Scriptable Install System)...
makensis /VERSION >nul 2>&1
if errorlevel 1 (
    echo ⚠️  NSIS not found. Creating simple installer package...
    echo.
    echo 📦 Creating simple installer package...
    
    REM Create installer directory
    if not exist "installer" mkdir "installer"
    
    REM Copy files to installer directory
    copy "dist\AVICAST.exe" "installer\"
    copy "start-avicast.bat" "installer\"
    copy "uninstall.bat" "installer\"
    copy "README.md" "installer\"
    xcopy "docs" "installer\docs\" /E /I
    
    echo ✅ Simple installer package created in 'installer' folder
    echo 📁 Copy the 'installer' folder to distribute AVICAST
) else (
    echo ✅ NSIS found. Creating professional installer...
    echo.
    echo 🔨 Building NSIS installer...
    makensis avicast-installer.nsi
    
    if exist "AVICAST-Setup-1.0.0.exe" (
        echo ✅ Professional installer created: AVICAST-Setup-1.0.0.exe
    ) else (
        echo ❌ NSIS installer creation failed
    )
)

echo.
echo 🎉 AVICAST Installer Build Complete!
echo ====================================
echo.
echo 📁 Output files:
if exist "installer" (
    echo    📦 Simple Package: installer\ folder
)
if exist "AVICAST-Setup-1.0.0.exe" (
    echo    💿 Professional Installer: AVICAST-Setup-1.0.0.exe
)
echo.
echo 🚀 Ready for deployment!
echo.
echo 📋 Next Steps:
echo    1. Test the installer on a clean Windows machine
echo    2. Distribute the installer to your users
echo    3. Users can install and run AVICAST without Python!
echo.
echo 🐦 Happy bird monitoring!
pause
