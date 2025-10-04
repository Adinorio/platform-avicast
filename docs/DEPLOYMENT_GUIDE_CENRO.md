# AVICAST Deployment Guide for CENRO

**Version**: 1.0  
**Date**: January 2025  
**Purpose**: Complete deployment guide for CENRO (Community Environment and Natural Resources Office)  
**Target**: Government-ready MVP deployment  
**Reference**: Based on `TECHNICAL_AUDIT_REPORT.md` and `IMPLEMENTATION_ROADMAP.md`

---

## Overview

This guide provides step-by-step instructions for deploying the AVICAST wildlife monitoring platform at CENRO facilities. The system is designed for local network deployment with strict security controls.

**Key Features**:
- Local-only deployment (no internet required)
- Role-based access control (SUPERADMIN, ADMIN, FIELD_WORKER)
- AI-powered bird species identification (6 egret species)
- Weather forecasting for field work scheduling
- Comprehensive reporting and data export

---

## System Requirements

### Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **CPU** | 4 cores, 2.0 GHz | 8 cores, 3.0 GHz |
| **RAM** | 4 GB | 8 GB |
| **Storage** | 50 GB free space | 100 GB SSD |
| **Network** | Local network adapter | Gigabit Ethernet |

### Software Requirements

| Component | Version | Notes |
|-----------|---------|-------|
| **Operating System** | Windows Server 2019+ or Ubuntu 20.04+ | Linux preferred |
| **Python** | 3.11+ | Required for Django |
| **PostgreSQL** | 14+ | Database server |
| **Git** | Latest | Code repository |

### Network Requirements

- **Local Network Access**: System must be accessible only on local network
- **No Internet Access**: System must not connect to external networks
- **Firewall Configuration**: Port 8000 accessible only from local network
- **IP Range**: Typically 192.168.x.x or 10.x.x.x networks

---

## Pre-Deployment Checklist

### Security Verification

- [ ] **Local Network Only**: Confirm no external network access
- [ ] **Firewall Rules**: Configure to block external connections
- [ ] **User Accounts**: Prepare CENRO user accounts
- [ ] **Backup Strategy**: Plan for daily automated backups
- [ ] **Access Control**: Verify role-based permissions

### Environment Preparation

- [ ] **Server Setup**: Install required software
- [ ] **Database Configuration**: PostgreSQL setup
- [ ] **Network Configuration**: Local network access
- [ ] **SSL Certificates**: Self-signed certificates for HTTPS
- [ ] **Monitoring**: System health monitoring setup

---

## Installation Steps

### Step 1: Server Preparation

#### Ubuntu Server Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install python3.11 python3.11-venv python3.11-dev python3-pip

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Install Git
sudo apt install git

# Install additional dependencies
sudo apt install build-essential libpq-dev
```

#### Windows Server Setup
```powershell
# Install Python 3.11 from python.org
# Install PostgreSQL from postgresql.org
# Install Git from git-scm.com
# Install Visual Studio Build Tools for C++ compilation
```

### Step 2: Database Setup

#### Create Database and User
```bash
# Switch to postgres user
sudo -u postgres psql

# Create database
CREATE DATABASE avicast_prod;

# Create user
CREATE USER avicast_user WITH PASSWORD 'your_secure_password_here';

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE avicast_prod TO avicast_user;

# Exit PostgreSQL
\q
```

#### Configure PostgreSQL
```bash
# Edit postgresql.conf
sudo nano /etc/postgresql/14/main/postgresql.conf

# Set listen addresses
listen_addresses = 'localhost,192.168.1.0/24,10.0.0.0/8'

# Edit pg_hba.conf
sudo nano /etc/postgresql/14/main/pg_hba.conf

# Add local network access
host    avicast_prod    avicast_user    192.168.1.0/24    md5
host    avicast_prod    avicast_user    10.0.0.0/8        md5

# Restart PostgreSQL
sudo systemctl restart postgresql
```

### Step 3: Application Deployment

#### Clone Repository
```bash
# Create application directory
sudo mkdir -p /opt/avicast
sudo chown $USER:$USER /opt/avicast
cd /opt/avicast

# Clone repository
git clone <repository-url> .

# Or copy files from deployment package
# Extract deployment package to /opt/avicast
```

#### Setup Virtual Environment
```bash
# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

#### Install Dependencies
```bash
# Install core dependencies
pip install -r requirements.txt

# Install AI/ML dependencies
pip install -r requirements-processing.txt

# Install production server
pip install gunicorn
```

### Step 4: Environment Configuration

#### Create Environment File
```bash
# Copy example environment file
cp env.example .env

# Edit environment file
nano .env
```

#### Environment Configuration
```bash
# .env file contents
DEBUG=False
SECRET_KEY=your_very_secure_secret_key_here
DATABASE_URL=postgresql://avicast_user:your_secure_password_here@localhost:5432/avicast_prod
ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.0/24,10.0.0.0/8
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://192.168.1.0:3000

# Email configuration (optional)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# Security settings
SECURE_BROWSER_XSS_FILTER=True
SECURE_CONTENT_TYPE_NOSNIFF=True
X_FRAME_OPTIONS=DENY
```

### Step 5: Initialize System

#### Run Migrations
```bash
# Activate virtual environment
source venv/bin/activate

# Run database migrations
python manage.py migrate

# Create superadmin user
python create_default_user.py
```

#### Collect Static Files
```bash
# Collect static files for production
python manage.py collectstatic --noinput

# Create necessary directories
mkdir -p media logs backups
```

#### System Health Check
```bash
# Run Django system checks
python manage.py check --deploy

# Test database connection
python manage.py dbshell

# Verify static files
ls -la static/
```

### Step 6: Production Server Setup

#### Gunicorn Configuration
```bash
# Create Gunicorn configuration file
nano gunicorn.conf.py
```

```python
# gunicorn.conf.py
bind = "0.0.0.0:8000"
workers = 4
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
preload_app = True
```

#### Systemd Service (Linux)
```bash
# Create systemd service file
sudo nano /etc/systemd/system/avicast.service
```

```ini
[Unit]
Description=AVICAST Wildlife Monitoring Platform
After=network.target postgresql.service

[Service]
Type=notify
User=avicast
Group=avicast
WorkingDirectory=/opt/avicast
Environment=PATH=/opt/avicast/venv/bin
ExecStart=/opt/avicast/venv/bin/gunicorn --config gunicorn.conf.py avicast_project.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

#### Start Service
```bash
# Create system user
sudo useradd -r -s /bin/false avicast

# Set ownership
sudo chown -R avicast:avicast /opt/avicast

# Enable and start service
sudo systemctl enable avicast
sudo systemctl start avicast

# Check status
sudo systemctl status avicast
```

---

## Security Configuration

### Firewall Setup

#### Ubuntu (UFW)
```bash
# Install UFW
sudo apt install ufw

# Allow SSH
sudo ufw allow ssh

# Allow local network access to port 8000
sudo ufw allow from 192.168.1.0/24 to any port 8000
sudo ufw allow from 10.0.0.0/8 to any port 8000

# Deny all other access to port 8000
sudo ufw deny 8000

# Enable firewall
sudo ufw enable
```

#### Windows Firewall
```powershell
# Allow inbound connections on port 8000 only from local network
New-NetFirewallRule -DisplayName "AVICAST Local Network" -Direction Inbound -Protocol TCP -LocalPort 8000 -RemoteAddress 192.168.1.0/24,10.0.0.0/8 -Action Allow

# Block external access to port 8000
New-NetFirewallRule -DisplayName "AVICAST Block External" -Direction Inbound -Protocol TCP -LocalPort 8000 -RemoteAddress Any -Action Block
```

### SSL Configuration (Optional)

#### Self-Signed Certificate
```bash
# Generate private key
openssl genrsa -out avicast.key 2048

# Generate certificate
openssl req -new -x509 -key avicast.key -out avicast.crt -days 365 -subj "/C=PH/ST=State/L=City/O=CENRO/CN=avicast.local"

# Set permissions
chmod 600 avicast.key
chmod 644 avicast.crt
```

#### Nginx Configuration (Optional)
```bash
# Install Nginx
sudo apt install nginx

# Create Nginx configuration
sudo nano /etc/nginx/sites-available/avicast
```

```nginx
server {
    listen 80;
    server_name avicast.local;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name avicast.local;

    ssl_certificate /opt/avicast/avicast.crt;
    ssl_certificate_key /opt/avicast/avicast.key;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /opt/avicast/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /opt/avicast/media/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

---

## User Management

### Default Login Credentials

After deployment, use these credentials for initial access:

- **Username**: `010101`
- **Password**: `avicast123`
- **Role**: `SUPERADMIN`

**⚠️ IMPORTANT**: Change the default password immediately after first login.

### User Roles

| Role | Permissions | Access Level |
|------|-------------|--------------|
| **SUPERADMIN** | User management only | Cannot access main system |
| **ADMIN** | Full system access | Can manage all data except users |
| **FIELD_WORKER** | Read-only access | Can view data, request changes |

### Creating Users

#### Via Web Interface
1. Login as SUPERADMIN
2. Navigate to User Management
3. Click "Add User"
4. Fill in user details:
   - Employee ID (unique)
   - First Name
   - Last Name
   - Password
   - Role (ADMIN or FIELD_WORKER)

#### Via Command Line
```bash
# Activate virtual environment
source venv/bin/activate

# Create user via Django shell
python manage.py shell
```

```python
from django.contrib.auth import get_user_model
User = get_user_model()

# Create admin user
admin_user = User.objects.create_user(
    employee_id='020202',
    password='secure_password',
    first_name='Admin',
    last_name='User',
    role='ADMIN'
)

# Create field worker
field_worker = User.objects.create_user(
    employee_id='030303',
    password='secure_password',
    first_name='Field',
    last_name='Worker',
    role='FIELD_WORKER'
)
```

---

## Maintenance

### Daily Backups

#### Automated Backup Script
```bash
# Create backup script
nano /opt/avicast/backup.sh
```

```bash
#!/bin/bash
# AVICAST Daily Backup Script

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/avicast/backups"
DB_NAME="avicast_prod"
DB_USER="avicast_user"

# Create backup directory
mkdir -p $BACKUP_DIR

# Database backup
pg_dump -h localhost -U $DB_USER $DB_NAME > $BACKUP_DIR/db_backup_$DATE.sql

# Media files backup
tar -czf $BACKUP_DIR/media_backup_$DATE.tar.gz media/

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
```

#### Setup Cron Job
```bash
# Make script executable
chmod +x /opt/avicast/backup.sh

# Add to crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * /opt/avicast/backup.sh >> /opt/avicast/logs/backup.log 2>&1
```

### Health Monitoring

#### System Health Check
```bash
# Check Django system
python manage.py check --deploy

# Check database health
python database_maintenance.py health

# Check disk space
df -h

# Check memory usage
free -h

# Check service status
sudo systemctl status avicast
```

#### Log Monitoring
```bash
# View application logs
sudo journalctl -u avicast -f

# View backup logs
tail -f /opt/avicast/logs/backup.log

# View error logs
tail -f /opt/avicast/logs/error.log
```

### Performance Optimization

#### Database Optimization
```bash
# Run database maintenance
python database_maintenance.py optimize

# Analyze database performance
python manage.py dbshell
```

```sql
-- Check slow queries
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- Check table sizes
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

#### Application Optimization
```bash
# Clear cache
python manage.py clear_cache

# Optimize static files
python manage.py collectstatic --noinput --clear

# Check for unused files
python management/commands/cleanup_storage.py
```

---

## Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check service status
sudo systemctl status avicast

# Check logs
sudo journalctl -u avicast -n 50

# Common fixes
sudo systemctl restart avicast
sudo systemctl reload avicast
```

#### Database Connection Issues
```bash
# Test database connection
python manage.py dbshell

# Check PostgreSQL status
sudo systemctl status postgresql

# Restart PostgreSQL
sudo systemctl restart postgresql
```

#### Permission Issues
```bash
# Fix ownership
sudo chown -R avicast:avicast /opt/avicast

# Fix permissions
sudo chmod -R 755 /opt/avicast
sudo chmod -R 644 /opt/avicast/media
```

#### Performance Issues
```bash
# Check system resources
htop
iostat -x 1

# Check database connections
ps aux | grep postgres

# Restart services
sudo systemctl restart avicast
sudo systemctl restart postgresql
```

### Emergency Recovery

#### Complete System Reset
```bash
# Stop services
sudo systemctl stop avicast

# Restore from backup
cd /opt/avicast/backups
psql -h localhost -U avicast_user avicast_prod < db_backup_latest.sql
tar -xzf media_backup_latest.tar.gz

# Restart services
sudo systemctl start avicast
```

#### Database Recovery
```bash
# Restore database
psql -h localhost -U avicast_user avicast_prod < backup_file.sql

# Run migrations
python manage.py migrate

# Create superadmin
python create_default_user.py
```

---

## Support and Maintenance

### Contact Information

- **Technical Lead**: [Name]
- **Email**: [Email]
- **Phone**: [Phone]
- **Emergency Contact**: [Phone]

### Regular Maintenance Schedule

| Task | Frequency | Responsible |
|------|-----------|-------------|
| **System Health Check** | Daily | CENRO IT |
| **Database Backup** | Daily | Automated |
| **Log Review** | Weekly | CENRO IT |
| **Security Update** | Monthly | CENRO IT |
| **Performance Review** | Quarterly | Technical Lead |

### Training Materials

- **User Manual**: `docs/USER_MANUAL.md`
- **Administrator Guide**: `docs/ADMINISTRATOR_GUIDE.md`
- **API Documentation**: Available at `/api/docs/`
- **Video Tutorials**: [Link to training videos]

---

## Deployment Verification

### Post-Deployment Checklist

- [ ] **System Access**: Can access web interface from local network
- [ ] **User Login**: Default credentials work
- [ ] **User Management**: Can create new users
- [ ] **Species Management**: Can add/edit species
- [ ] **Site Management**: Can create/edit sites
- [ ] **Image Processing**: AI detection works
- [ ] **Report Generation**: Reports generate correctly
- [ ] **API Endpoints**: Mobile app can connect
- [ ] **Backup System**: Automated backups working
- [ ] **Security**: Firewall rules active
- [ ] **Performance**: System responds within 2 seconds
- [ ] **Documentation**: All guides accessible

### Acceptance Criteria

- **Functionality**: 100% of core features working
- **Security**: All security measures active
- **Performance**: <2s page load time, 10+ concurrent users
- **Reliability**: 99% uptime target
- **Documentation**: Complete user and admin guides

---

## Conclusion

This deployment guide provides comprehensive instructions for deploying the AVICAST platform at CENRO facilities. The system is designed for local network deployment with strict security controls and government-grade reliability.

**Key Success Factors**:
1. Follow all security configurations
2. Test thoroughly before going live
3. Train users on system operation
4. Maintain regular backups
5. Monitor system health continuously

**Next Steps**:
1. Complete deployment using this guide
2. Conduct user acceptance testing
3. Train CENRO personnel
4. Go live with production data
5. Schedule regular maintenance

---

*This deployment guide is based on the technical audit findings and implementation roadmap. For technical support, contact the development team.*
