#!/usr/bin/env python
"""
AVICAST Multi-Device Deployment Setup Script

This script helps configure the system for centralized server deployment
to support multiple devices (laptops/PCs) accessing the same data.

Usage:
    python scripts/deployment/server_setup.py --help
"""

import os
import sys
import django
import subprocess
import argparse
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'avicast_project.settings.development')
django.setup()

from django.core.management import execute_from_command_line
from django.conf import settings
from django.db import connection
from apps.users.models import User

class MultiDeviceDeploymentSetup:
    """Setup class for multi-device deployment"""
    
    def __init__(self):
        self.project_root = project_root
        self.current_db = settings.DATABASES['default']
        
    def check_current_setup(self):
        """Check current system configuration"""
        print("CHECKING CURRENT SYSTEM CONFIGURATION")
        print("=" * 50)
        
        # Database type
        db_engine = self.current_db['ENGINE']
        if 'sqlite' in db_engine:
            print("Database: SQLite (Local)")
            print("   WARNING: This needs to be changed for multi-device deployment")
        else:
            print(f"Database: {db_engine}")
            
        # Check if server is accessible
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                print("Database connection: Working")
        except Exception as e:
            print(f"Database connection: Failed - {e}")
            
        # Check user accounts
        user_count = User.objects.count()
        print(f"User accounts: {user_count}")
        
        # Check media files
        media_path = Path(settings.MEDIA_ROOT)
        if media_path.exists():
            media_files = len(list(media_path.rglob('*')))
            print(f"Media files: {media_files}")
        else:
            print("Media files: No media directory found")
            
        print()
        
    def generate_deployment_config(self, server_ip="192.168.1.100", server_port=8000):
        """Generate deployment configuration files"""
        print("GENERATING DEPLOYMENT CONFIGURATION")
        print("=" * 50)
        
        # Generate production settings
        production_settings = f"""
# Production settings for multi-device deployment
import os
from .base import *

# Security settings
DEBUG = False
ALLOWED_HOSTS = ['{server_ip}', 'localhost', '127.0.0.1']

# Database configuration (PostgreSQL recommended)
DATABASES = {{
    'default': {{
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'avicast_production',
        'USER': 'avicast_user',
        'PASSWORD': 'your_secure_password_here',
        'HOST': 'localhost',
        'PORT': '5432',
    }}
}}

# Static files
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'

# Media files
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Session settings
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Logging
LOGGING = {{
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {{
        'file': {{
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
        }},
    }},
    'loggers': {{
        'django': {{
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        }},
    }},
}}
"""
        
        # Write production settings
        settings_dir = self.project_root / 'avicast_project' / 'settings'
        settings_dir.mkdir(exist_ok=True)
        
        with open(settings_dir / 'production.py', 'w') as f:
            f.write(production_settings)
        print(f"Created: {settings_dir / 'production.py'}")
        
        # Generate Nginx configuration
        nginx_config = f"""
server {{
    listen 80;
    server_name {server_ip};
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}}

server {{
    listen 443 ssl http2;
    server_name {server_ip};
    
    # SSL configuration (update paths)
    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    # Static files
    location /static/ {{
        alias {self.project_root}/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }}
    
    # Media files
    location /media/ {{
        alias {self.project_root}/media/;
        expires 1y;
        add_header Cache-Control "public";
    }}
    
    # Django application
    location / {{
        proxy_pass http://127.0.0.1:{server_port};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}
"""
        
        with open(self.project_root / 'nginx.conf', 'w') as f:
            f.write(nginx_config)
        print(f"Created: {self.project_root / 'nginx.conf'}")
        
        # Generate systemd service file
        systemd_service = f"""
[Unit]
Description=AVICAST Django Application
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory={self.project_root}
Environment=DJANGO_SETTINGS_MODULE=avicast_project.settings.production
ExecStart={sys.executable} -m gunicorn avicast_project.wsgi:application --bind 127.0.0.1:{server_port}
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
"""
        
        with open(self.project_root / 'avicast.service', 'w') as f:
            f.write(systemd_service)
        print(f"Created: {self.project_root / 'avicast.service'}")
        
        print()
        
    def generate_client_instructions(self, server_ip="192.168.1.100"):
        """Generate client setup instructions"""
        print("GENERATING CLIENT SETUP INSTRUCTIONS")
        print("=" * 50)
        
        client_instructions = f"""
# AVICAST Client Setup Instructions

## For Each Laptop/PC (Client Device):

### 1. Network Requirements
- Ensure device is on the same network as the server
- Server IP: {server_ip}
- Required ports: 80 (HTTP), 443 (HTTPS)

### 2. Browser Setup
- Use modern browser (Chrome, Firefox, Edge, Safari)
- Clear browser cache if switching from local setup
- Bookmark: https://{server_ip}:8000

### 3. Access Instructions
1. Open web browser
2. Navigate to: https://{server_ip}:8000
3. Login with your existing credentials
4. All data will be synchronized across devices

### 4. Troubleshooting
- If connection fails, check network connectivity
- Verify server IP address is correct
- Contact administrator for login issues

### 5. Security Notes
- Never share login credentials
- Log out when finished
- Use HTTPS for secure connection

## Server Information
- Server IP: {server_ip}
- Admin Access: https://{server_ip}:8000/admin-system/
- System Logs: https://{server_ip}:8000/users/audit-logs/
"""
        
        with open(self.project_root / 'CLIENT_SETUP_INSTRUCTIONS.md', 'w') as f:
            f.write(client_instructions)
        print(f"Created: {self.project_root / 'CLIENT_SETUP_INSTRUCTIONS.md'}")
        
        print()
        
    def export_current_data(self):
        """Export current data for migration"""
        print("EXPORTING CURRENT DATA")
        print("=" * 50)
        
        # Create data export directory
        export_dir = self.project_root / 'data_export'
        export_dir.mkdir(exist_ok=True)
        
        # Export users
        users_data = []
        for user in User.objects.all():
            users_data.append({
                'employee_id': user.employee_id,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'role': user.role,
                'is_active': user.is_active,
                'date_joined': user.date_joined.isoformat(),
            })
        
        import json
        with open(export_dir / 'users_export.json', 'w') as f:
            json.dump(users_data, f, indent=2)
        print(f"Exported {len(users_data)} users")
        
        # Export media files info
        media_files = []
        media_path = Path(settings.MEDIA_ROOT)
        if media_path.exists():
            for file_path in media_path.rglob('*'):
                if file_path.is_file():
                    media_files.append({
                        'path': str(file_path.relative_to(media_path)),
                        'size': file_path.stat().st_size,
                        'modified': file_path.stat().st_mtime,
                    })
        
        with open(export_dir / 'media_files_export.json', 'w') as f:
            json.dump(media_files, f, indent=2)
        print(f"Exported {len(media_files)} media files info")
        
        print(f"Export directory: {export_dir}")
        print()
        
    def run_full_setup(self, server_ip="192.168.1.100", server_port=8000):
        """Run complete setup process"""
        print("AVICAST MULTI-DEVICE DEPLOYMENT SETUP")
        print("=" * 60)
        print()
        
        self.check_current_setup()
        self.generate_deployment_config(server_ip, server_port)
        self.generate_client_instructions(server_ip)
        self.export_current_data()
        
        print("SETUP COMPLETE!")
        print("=" * 50)
        print()
        print("NEXT STEPS:")
        print("1. Set up PostgreSQL database on server")
        print("2. Install and configure Nginx")
        print("3. Install SSL certificates")
        print("4. Run migrations on production database")
        print("5. Import exported data")
        print("6. Start the production server")
        print("7. Test access from client devices")
        print()
        print(f"See CLIENT_SETUP_INSTRUCTIONS.md for client setup")
        print(f"See MULTI_DEVICE_DEPLOYMENT_PLAN.md for detailed plan")

def main():
    parser = argparse.ArgumentParser(description='AVICAST Multi-Device Deployment Setup')
    parser.add_argument('--server-ip', default='192.168.1.100', 
                       help='Server IP address (default: 192.168.1.100)')
    parser.add_argument('--server-port', type=int, default=8000,
                       help='Server port (default: 8000)')
    parser.add_argument('--export-only', action='store_true',
                       help='Only export current data')
    
    args = parser.parse_args()
    
    setup = MultiDeviceDeploymentSetup()
    
    if args.export_only:
        setup.export_current_data()
    else:
        setup.run_full_setup(args.server_ip, args.server_port)

if __name__ == '__main__':
    main()
