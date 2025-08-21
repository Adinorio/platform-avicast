# 👨‍💼 AVICAST Local Storage Administrator Guide
**Complete System Administration for CENRO WiFi-Only Deployment**

## 📋 **Table of Contents**
1. [System Architecture](#system-architecture)
2. [Installation & Setup](#installation--setup)
3. [Configuration Management](#configuration-management)
4. [User Management](#user-management)
5. [Storage Monitoring](#storage-monitoring)
6. [Backup & Recovery](#backup--recovery)
7. [Maintenance & Troubleshooting](#maintenance--troubleshooting)
8. [Security & Compliance](#security--compliance)
9. [Performance Optimization](#performance-optimization)
10. [Emergency Procedures](#emergency-procedures)

---

## 🏗️ **System Architecture**

### **Storage Architecture Overview:**
```
🗄️ AVICAST Storage System:
├── 💾 Primary Storage (C: Drive)
│   ├── 🔥 HOT Tier: 0-30 days, fast access
│   ├── 🌡️ WARM Tier: 30-90 days, compressed
│   └── 📊 Active Database & Applications
├── 📦 Secondary Storage (D: Drive)
│   ├── ❄️ COLD Tier: 90+ days, archived
│   ├── 🗃️ ARCHIVE Tier: 1+ years, long-term
│   └── 🔄 Backup & Recovery Files
└── 🔌 External Storage
    ├── 💾 USB Drives (weekly rotation)
    ├── 📱 Mobile Device Backups
    └── 🗂️ Offsite Archive Storage
```

### **Network Architecture:**
```
🌐 Local Network Setup:
├── 🖥️ Main Server: 192.168.1.100
├── 🌐 WiFi Router: 192.168.1.1
├── 📱 Field Devices: 192.168.1.101-150
├── 💻 Office Computers: 192.168.1.151-200
└── 🔌 Network Storage: 192.168.1.201-250
```

### **Software Stack:**
```
📦 Technology Stack:
├── 🐍 Backend: Python 3.8+ with Django 3.2+
├── 🗄️ Database: SQLite (dev) / PostgreSQL (prod)
├── 🖼️ Image Processing: Pillow (PIL)
├── 📊 Monitoring: psutil, custom monitoring
├── 🔐 Authentication: Django built-in + custom
└── 🌐 Web Server: Django development server
```

---

## 🚀 **Installation & Setup**

### **Pre-Installation Checklist:**
```
✅ Pre-Installation Requirements:
├── 🖥️ Server hardware meets specifications
├── 💾 Secondary drive (D:) available
├── 🌐 WiFi router configured
├── 🔌 Power backup (UPS) available
├── 📱 Test devices available
└── 👥 Staff training scheduled
```

### **Installation Commands:**
```bash
# 1. System preparation
cd C:\Users\QUARTZ\Documents\Github\platform-avicast
venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt
pip install Pillow psutil django-storages

# 3. Create storage directories
mkdir D:\avicast_archive
mkdir D:\avicast_archive\bird_images
mkdir D:\avicast_archive\backups
mkdir D:\avicast_archive\logs

# 4. Set permissions
icacls "D:\avicast_archive" /grant "Everyone:(OI)(CI)F"
icacls "media" /grant "Everyone:(OI)(CI)F"

# 5. Database setup
python manage.py makemigrations image_processing
python manage.py migrate
python manage.py createsuperuser
```

### **Post-Installation Verification:**
```bash
# 1. Test storage system
python manage.py storage_status

# 2. Test image upload
python manage.py test image_processing.tests

# 3. Verify archive system
python manage.py cleanup_storage --dry-run

# 4. Check system health
python manage.py check --deploy
```

---

## ⚙️ **Configuration Management**

### **Environment Configuration:**
```bash
# .env file configuration
MAX_LOCAL_STORAGE_GB=50
ARCHIVE_STORAGE_PATH=D:/avicast_archive
STORAGE_WARNING_THRESHOLD=0.8
AUTO_OPTIMIZE_IMAGES=True
ENABLE_HASH_DEDUPLICATION=True
WIFI_ONLY_MODE=True
GOVERNMENT_RETENTION_YEARS=7
AUDIT_TRAIL_ENABLED=True
DATA_SOVEREIGNTY=True
```

### **Django Settings Configuration:**
```python
# settings/production.py
import os
from pathlib import Path

# Storage Configuration
USE_CLOUD_STORAGE = False
CLOUD_STORAGE_PROVIDER = 'local'
MAX_LOCAL_STORAGE_GB = int(os.getenv('MAX_LOCAL_STORAGE_GB', 50))
ARCHIVE_STORAGE_PATH = os.getenv('ARCHIVE_STORAGE_PATH', 'D:/avicast_archive')
STORAGE_WARNING_THRESHOLD = float(os.getenv('STORAGE_WARNING_THRESHOLD', 0.8))

# Image Processing
AUTO_OPTIMIZE_IMAGES = os.getenv('AUTO_OPTIMIZE_IMAGES', 'True').lower() == 'true'
DEFAULT_IMAGE_FORMAT = 'WEBP'
MAX_IMAGE_DIMENSIONS = (2048, 1536)
IMAGE_QUALITY = {
    'JPEG': 85,
    'PNG': 95,
    'WEBP': 80
}

# Security Settings
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
DEBUG = False
ALLOWED_HOSTS = ['192.168.1.100', 'localhost', '127.0.0.1']

# Database Configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'D:/avicast_archive/logs/django.log',
        },
        'storage_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'D:/avicast_archive/logs/storage.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
        'apps.image_processing': {
            'handlers': ['storage_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

### **Storage Tier Configuration:**
```python
# Storage tier settings
STORAGE_TIERS = {
    'HOT_TO_WARM': 30,      # Move to warm after 30 days
    'WARM_TO_COLD': 90,     # Move to cold after 90 days
    'COLD_TO_ARCHIVE': 365, # Archive after 1 year
    'ARCHIVE_DELETE': 2555, # Delete after 7 years (government)
}

# Compression settings
COMPRESSION_SETTINGS = {
    'enabled': True,
    'target_format': 'WEBP',
    'max_dimensions': (2048, 1536),
    'quality': {
        'JPEG': 85,
        'PNG': 95,
        'WEBP': 80
    }
}
```

---

## 👥 **User Management**

### **User Creation & Management:**
```bash
# Create new user
python manage.py createsuperuser --username=staff001 --email=staff001@cenro.gov.ph

# Create regular user
python manage.py shell
>>> from django.contrib.auth.models import User
>>> user = User.objects.create_user(username='field_staff_001', 
                                   email='field@cenro.gov.ph',
                                   password='secure_password_123')
>>> user.is_staff = True
>>> user.save()

# Bulk user creation from CSV
python manage.py import_users users.csv
```

### **User Permissions:**
```python
# Permission levels
PERMISSION_LEVELS = {
    'ADMIN': {
        'can_upload': True,
        'can_delete': True,
        'can_archive': True,
        'can_restore': True,
        'can_manage_users': True,
        'can_view_logs': True,
        'can_manage_storage': True
    },
    'STAFF': {
        'can_upload': True,
        'can_delete': False,
        'can_archive': False,
        'can_restore': False,
        'can_manage_users': False,
        'can_view_logs': False,
        'can_manage_storage': False
    },
    'FIELD_STAFF': {
        'can_upload': True,
        'can_delete': False,
        'can_archive': False,
        'can_restore': False,
        'can_manage_users': False,
        'can_view_logs': False,
        'can_manage_storage': False
    }
}
```

### **User Groups & Roles:**
```bash
# Create user groups
python manage.py shell
>>> from django.contrib.auth.models import Group, Permission
>>> admin_group = Group.objects.create(name='Administrators')
>>> staff_group = Group.objects.create(name='Staff')
>>> field_group = Group.objects.create(name='Field Staff')

# Assign users to groups
>>> user = User.objects.get(username='field_staff_001')
>>> user.groups.add(field_group)
```

---

## 📊 **Storage Monitoring**

### **Real-Time Monitoring Commands:**
```bash
# Check current storage status
python manage.py storage_status

# Detailed storage report
python manage.py storage_report --detailed

# Monitor specific storage tier
python manage.py storage_status --tier=HOT
python manage.py storage_status --tier=WARM
python manage.py storage_status --tier=COLD
python manage.py storage_status --tier=ARCHIVE

# Check storage health
python manage.py storage_health --full
```

### **Automated Monitoring Setup:**
```bash
# Create Windows Task Scheduler tasks
schtasks /create /tn "AVICAST Storage Monitor" /tr "python manage.py storage_status" /sc daily /st 09:00
schtasks /create /tn "AVICAST Daily Cleanup" /tr "python manage.py cleanup_storage --days=30" /sc daily /st 02:00
schtasks /create /tn "AVICAST Weekly Backup" /tr "python manage.py backup_to_external --drive=E:" /sc weekly /d MON /st 03:00

# Create monitoring script
echo @echo off > monitor_storage.bat
echo cd /d C:\Users\QUARTZ\Documents\Github\platform-avicast >> monitor_storage.bat
echo venv\Scripts\activate >> monitor_storage.bat
echo python manage.py storage_status >> monitor_storage.bat
echo pause >> monitor_storage.bat
```

### **Alert System Configuration:**
```python
# Alert thresholds
ALERT_THRESHOLDS = {
    'storage_warning': 0.8,      # 80% full
    'storage_critical': 0.9,     # 90% full
    'archive_warning': 0.7,      # 70% archive full
    'performance_degradation': 0.5,  # 50% slower than baseline
}

# Alert methods
ALERT_METHODS = {
    'email': True,
    'sms': False,
    'system_notification': True,
    'log_file': True,
    'dashboard': True
}

# Alert recipients
ALERT_RECIPIENTS = [
    'admin@cenro.gov.ph',
    'it_support@cenro.gov.ph',
    'system_admin@cenro.gov.ph'
]
```

---

## 💾 **Backup & Recovery**

### **Backup Strategy Implementation:**
```bash
# Daily backup script
echo @echo off > daily_backup.bat
echo cd /d C:\Users\QUARTZ\Documents\Github\platform-avicast >> daily_backup.bat
echo venv\Scripts\activate >> daily_backup.bat
echo python manage.py cleanup_storage --days=30 >> daily_backup.bat
echo python manage.py backup_to_external --drive=D:\avicast_archive\backups >> daily_backup.bat
echo echo Backup completed at %date% %time% >> daily_backup.bat

# Weekly backup script
echo @echo off > weekly_backup.bat
echo cd /d C:\Users\QUARTZ\Documents\Github\platform-avicast >> weekly_backup.bat
echo venv\Scripts\activate >> weekly_backup.bat
echo python manage.py backup_to_external --drive=E: --full >> weekly_backup.bat
echo python manage.py verify_archive >> weekly_backup.bat
echo echo Weekly backup completed at %date% %time% >> weekly_backup.bat
```

### **Recovery Procedures:**
```bash
# Full system recovery
python manage.py full_restore --source=E:\avicast_backup\2025-08-21

# Individual file recovery
python manage.py restore_file --id=12345 --tier=HOT

# Database recovery
python manage.py restore_database --backup=db_backup_2025-08-21.sql

# Archive verification
python manage.py verify_archive --full
```

### **Backup Verification:**
```bash
# Verify backup integrity
python manage.py verify_backup --backup=E:\avicast_backup\2025-08-21

# Check backup completeness
python manage.py backup_report --detailed --backup=E:\avicast_backup\2025-08-21

# Test recovery process
python manage.py test_recovery --backup=E:\avicast_backup\2025-08-21
```

---

## 🛠️ **Maintenance & Troubleshooting**

### **Regular Maintenance Tasks:**
```bash
# Daily maintenance
python manage.py cleanup_storage --days=30
python manage.py storage_status
python manage.py check_system_health

# Weekly maintenance
python manage.py optimize_images --all
python manage.py cleanup_storage --force --days=90
python manage.py backup_to_external --drive=E:
python manage.py verify_archive

# Monthly maintenance
python manage.py full_system_cleanup
python manage.py performance_optimization
python manage.py security_audit
python manage.py user_activity_report

# Quarterly maintenance
python manage.py external_backup_rotation
python manage.py disaster_recovery_test
python manage.py compliance_audit
```

### **Troubleshooting Commands:**
```bash
# System diagnostics
python manage.py diagnose_system --full

# Storage troubleshooting
python manage.py troubleshoot_storage --verbose

# Performance analysis
python manage.py performance_analysis --detailed

# Error log analysis
python manage.py analyze_logs --days=7 --level=ERROR

# Database optimization
python manage.py optimize_database --full
```

### **Common Issues & Solutions:**

#### **Issue 1: Storage System Not Responding**
```bash
# Check system status
python manage.py storage_status

# Restart storage service
python manage.py restart_storage_service

# Check logs
python manage.py check_logs --recent

# Verify file permissions
icacls "D:\avicast_archive" /grant "Everyone:(OI)(CI)F"
```

#### **Issue 2: Image Processing Fails**
```bash
# Check Pillow installation
python -c "from PIL import Image; print('Pillow OK')"

# Reinstall Pillow
pip uninstall Pillow
pip install Pillow

# Check image processing logs
python manage.py check_logs --module=image_processing
```

#### **Issue 3: Database Performance Issues**
```bash
# Check database status
python manage.py dbshell
.schema image_processing_imageupload

# Optimize database
python manage.py optimize_database

# Check indexes
python manage.py check_indexes
```

---

## 🔒 **Security & Compliance**

### **Security Configuration:**
```python
# Security settings
SECURITY_SETTINGS = {
    'password_policy': {
        'min_length': 12,
        'require_uppercase': True,
        'require_lowercase': True,
        'require_numbers': True,
        'require_special': True,
        'expiry_days': 90
    },
    'session_security': {
        'session_timeout': 3600,  # 1 hour
        'max_failed_logins': 5,
        'lockout_duration': 1800,  # 30 minutes
        'require_https': False  # Local network only
    },
    'data_protection': {
        'encryption_at_rest': False,  # Local storage
        'encryption_in_transit': False,  # Local network
        'audit_logging': True,
        'data_retention': 2555  # 7 years
    }
}
```

### **Compliance Monitoring:**
```bash
# Compliance audit
python manage.py compliance_audit --full

# Data retention check
python manage.py check_retention_policy

# Audit log review
python manage.py audit_log_report --days=30

# Government compliance report
python manage.py government_compliance_report --format=pdf
```

### **Access Control:**
```python
# Access control matrix
ACCESS_CONTROL = {
    'ADMIN': {
        'storage_management': 'FULL',
        'user_management': 'FULL',
        'system_configuration': 'FULL',
        'backup_recovery': 'FULL',
        'audit_logs': 'FULL'
    },
    'STAFF': {
        'storage_management': 'READ',
        'user_management': 'NONE',
        'system_configuration': 'NONE',
        'backup_recovery': 'READ',
        'audit_logs': 'READ_OWN'
    },
    'FIELD_STAFF': {
        'storage_management': 'READ_OWN',
        'user_management': 'NONE',
        'system_configuration': 'NONE',
        'backup_recovery': 'NONE',
        'audit_logs': 'READ_OWN'
    }
}
```

---

## ⚡ **Performance Optimization**

### **System Performance Monitoring:**
```bash
# Performance baseline
python manage.py performance_baseline --create

# Performance monitoring
python manage.py monitor_performance --continuous

# Performance analysis
python manage.py performance_analysis --detailed

# Bottleneck identification
python manage.py identify_bottlenecks --verbose
```

### **Optimization Commands:**
```bash
# Database optimization
python manage.py optimize_database --full

# Image optimization
python manage.py optimize_images --all --force

# Storage optimization
python manage.py optimize_storage --full

# Cache optimization
python manage.py optimize_cache --clear
```

### **Performance Tuning:**
```python
# Performance settings
PERFORMANCE_SETTINGS = {
    'database': {
        'connection_pool_size': 10,
        'query_timeout': 30,
        'max_connections': 100
    },
    'image_processing': {
        'worker_threads': 4,
        'batch_size': 10,
        'memory_limit': '2GB'
    },
    'storage': {
        'buffer_size': '64MB',
        'cache_size': '1GB',
        'compression_level': 6
    }
}
```

---

## 🚨 **Emergency Procedures**

### **System Down Procedures:**
```bash
# 1. Immediate response
python manage.py emergency_shutdown --graceful

# 2. Check system status
python manage.py system_status --full

# 3. Restart services
python manage.py restart_all_services

# 4. Verify recovery
python manage.py verify_system_recovery
```

### **Data Loss Recovery:**
```bash
# 1. Stop all operations
python manage.py stop_all_operations

# 2. Assess damage
python manage.py assess_data_loss --full

# 3. Restore from backup
python manage.py full_restore --source=E:\latest_backup

# 4. Verify data integrity
python manage.py verify_data_integrity --full
```

### **Security Breach Response:**
```bash
# 1. Isolate system
python manage.py isolate_system --emergency

# 2. Audit access logs
python manage.py audit_access_logs --recent

# 3. Reset compromised accounts
python manage.py reset_compromised_accounts

# 4. Security audit
python manage.py security_audit --full
```

---

## 📋 **Administrative Checklist**

### **Daily Tasks:**
- [ ] Check storage status
- [ ] Monitor system performance
- [ ] Review error logs
- [ ] Verify backup completion
- [ ] Check user activity

### **Weekly Tasks:**
- [ ] Full storage cleanup
- [ ] Performance optimization
- [ ] External backup creation
- [ ] Archive verification
- [ ] User activity review

### **Monthly Tasks:**
- [ ] System health check
- [ ] Security audit
- [ ] Performance analysis
- [ ] Compliance review
- [ ] Disaster recovery test

### **Quarterly Tasks:**
- [ ] Full system backup
- [ ] External drive rotation
- [ ] Performance baseline update
- [ ] Security policy review
- [ ] Staff training update

---

## 📞 **Support & Escalation**

### **Support Levels:**
```
📞 Support Escalation:
├── Level 1: Field Staff Support
├── Level 2: IT Staff Support
├── Level 3: System Administrator
├── Level 4: External Consultant
└── Level 5: Vendor Support
```

### **Emergency Contacts:**
```
🚨 Emergency Contacts:
├── System Admin: [Your Name] - [Phone]
├── IT Support: [IT Staff] - [Phone]
├── Management: [Manager] - [Phone]
├── External Support: [Consultant] - [Phone]
└── Vendor Support: [Vendor] - [Phone]
```

### **Documentation Requirements:**
```
📚 Required Documentation:
├── System configuration
├── User management procedures
├── Backup and recovery procedures
├── Security policies
├── Compliance reports
└── Incident reports
```

---

## 🎯 **Next Steps for Administrators**

1. **Complete System Setup**: Follow installation guide
2. **Configure Monitoring**: Set up automated monitoring
3. **Establish Procedures**: Create operational procedures
4. **Train Staff**: Conduct user training sessions
5. **Test Systems**: Verify all functionality
6. **Go Live**: Launch system for production use

**Your AVICAST Local Storage System is now ready for production administration! 🚀**

For additional support, refer to the system documentation or contact the development team.
