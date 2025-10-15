#!/usr/bin/env python
"""
AVICAST Executable Builder
Creates a standalone Windows executable for AVICAST
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def build_avicast_exe():
    """Build AVICAST as a standalone executable"""
    print("🚀 AVICAST Executable Builder")
    print("=" * 40)
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
        print("✅ PyInstaller is installed")
    except ImportError:
        print("❌ PyInstaller not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✅ PyInstaller installed")
    
    # Create PyInstaller spec file
    create_pyinstaller_spec()
    
    # Build the executable
    print("\n🔨 Building executable...")
    subprocess.run([
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        "avicast.spec"
    ])
    
    # Create installer package
    create_installer_package()
    
    print("\n🎉 AVICAST executable build complete!")
    print("📁 Output: dist/AVICAST-Setup.exe")
    print("🚀 Ready for deployment!")

def create_pyinstaller_spec():
    """Create PyInstaller specification file"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Data files to include
datas = [
    ('templates', 'templates'),
    ('static', 'static'),
    ('media', 'media'),
    ('apps', 'apps'),
    ('avicast_project', 'avicast_project'),
    ('manage.py', '.'),
    ('requirements.txt', '.'),
    ('env.example', '.'),
    ('pyproject.toml', '.'),
]

# Hidden imports (Django modules)
hiddenimports = [
    'django',
    'django.contrib',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.db',
    'django.db.backends.sqlite3',
    'django.core',
    'django.core.management',
    'django.core.management.commands',
    'django.core.management.commands.migrate',
    'django.core.management.commands.collectstatic',
    'apps.users',
    'apps.fauna',
    'apps.locations',
    'apps.image_processing',
    'apps.analytics_new',
    'apps.weather',
    'apps.common',
    'apps.admin_system',
]

a = Analysis(
    ['manage.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AVICAST',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='static/favicon.svg' if os.path.exists('static/favicon.svg') else None,
)
'''
    
    with open('avicast.spec', 'w') as f:
        f.write(spec_content)
    
    print("✅ PyInstaller spec file created")

def create_installer_package():
    """Create a simple installer package"""
    print("\n📦 Creating installer package...")
    
    # Create installer directory
    installer_dir = Path("installer")
    installer_dir.mkdir(exist_ok=True)
    
    # Create batch file to run AVICAST
    startup_script = installer_dir / "start-avicast.bat"
    with open(startup_script, 'w') as f:
        f.write('''@echo off
echo Starting AVICAST Wildlife Monitoring System...
echo.
echo Please wait while the system initializes...
echo.

REM Check if database exists, if not run migrations
if not exist "db.sqlite3" (
    echo Setting up database...
    AVICAST.exe migrate
)

REM Start the server
echo Starting server...
echo.
echo AVICAST is now running!
echo.
echo Access the system at: http://localhost:8000
echo.
echo Default Login:
echo   Employee ID: 010101
echo   Password: avicast123
echo.
echo Press Ctrl+C to stop the server
echo.
AVICAST.exe runserver 0.0.0.0:8000

pause
''')
    
    # Create uninstaller
    uninstall_script = installer_dir / "uninstall.bat"
    with open(uninstall_script, 'w') as f:
        f.write('''@echo off
echo Uninstalling AVICAST...
echo.

REM Stop any running processes
taskkill /f /im AVICAST.exe 2>nul

REM Remove files
if exist "AVICAST.exe" del /q "AVICAST.exe"
if exist "db.sqlite3" del /q "db.sqlite3"
if exist "media" rmdir /s /q "media"
if exist "staticfiles" rmdir /s /q "staticfiles"

echo AVICAST has been uninstalled.
pause
''')
    
    # Create README for installer
    readme_file = installer_dir / "README.txt"
    with open(readme_file, 'w') as f:
        f.write('''AVICAST Wildlife Monitoring System
=====================================

INSTALLATION:
1. Copy all files to your desired installation directory
2. Run "start-avicast.bat" to start the system
3. Open your web browser and go to: http://localhost:8000

DEFAULT LOGIN:
Employee ID: 010101
Password: avicast123
(Change password on first login!)

NETWORK ACCESS:
To allow other computers on your network to access AVICAST:
1. Find your computer's IP address (run "ipconfig" in command prompt)
2. Other computers can access: http://YOUR_IP_ADDRESS:8000

UNINSTALLATION:
Run "uninstall.bat" to remove AVICAST

SUPPORT:
For technical support, contact your system administrator.

Happy bird monitoring! 🐦
''')
    
    print("✅ Installer package created")

if __name__ == '__main__':
    build_avicast_exe()
