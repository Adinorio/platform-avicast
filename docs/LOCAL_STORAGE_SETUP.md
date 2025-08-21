# 🏠 AVICAST Local Storage Setup Guide
**Complete Installation & Configuration for CENRO WiFi-Only System**

## 📋 **Table of Contents**
1. [System Requirements](#system-requirements)
2. [Installation Steps](#installation-steps)
3. [Configuration](#configuration)
4. [Database Setup](#database-setup)
5. [Testing & Verification](#testing--verification)
6. [Troubleshooting](#troubleshooting)
7. [Maintenance Schedule](#maintenance-schedule)

---

## 🖥️ **System Requirements**

### **Hardware Requirements:**
```
🖥️ Minimum Server Specifications:
├── 💾 Primary Storage: 500GB SSD (recommended)
├── 📦 Secondary Storage: 2TB HDD (for archives)
├── 🧠 RAM: 8GB minimum, 16GB recommended
├── 🔌 USB Ports: 4+ USB 3.0 ports for backup drives
├── 🌐 Network: WiFi router (802.11ac recommended)
└── 💻 OS: Windows 10/11 or Ubuntu 20.04+
```

### **Software Requirements:**
```
📦 Required Software:
├── Python 3.8+ with pip
├── Django 3.2+ framework
├── Pillow (PIL) for image processing
├── psutil for system monitoring
├── Git for version control
└── Web browser (Chrome/Firefox recommended)
```

### **Network Requirements:**
```
🌐 Local Network Setup:
├── WiFi Router: 802.11ac or better
├── IP Range: 192.168.1.x (recommended)
├── DHCP: Enabled for automatic IP assignment
├── Bandwidth: 100Mbps+ for fast file transfers
└── Coverage: Entire CENRO office area
```

---

## 🚀 **Installation Steps**

### **Step 1: Prepare Storage Drives**
```bash
# 1. Create archive directory on secondary drive
mkdir D:\avicast_archive
mkdir D:\avicast_archive\bird_images
mkdir D:\avicast_archive\backups

# 2. Set proper permissions (Windows)
icacls "D:\avicast_archive" /grant "Everyone:(OI)(CI)F"

# 3. Verify drive space
dir D:\
```

### **Step 2: Install Python Dependencies**
```bash
# Activate virtual environment
cd C:\Users\QUARTZ\Documents\Github\platform-avicast
venv\Scripts\activate

# Install required packages
pip install Pillow psutil django-storages

# Verify installation
python -c "import PIL, psutil; print('Dependencies installed successfully')"
```

### **Step 3: Clone/Update Codebase**
```bash
# If updating existing installation
git pull origin main

# If fresh installation
git clone https://github.com/your-repo/platform-avicast.git
cd platform-avicast
```

---

## ⚙️ **Configuration**

### **Step 1: Update Django Settings**
```python
# settings/production.py or settings/local.py

# Local Storage Configuration
USE_CLOUD_STORAGE = False
CLOUD_STORAGE_PROVIDER = 'local'

# Storage Paths
MAX_LOCAL_STORAGE_GB = 50
ARCHIVE_STORAGE_PATH = 'D:/avicast_archive'
STORAGE_WARNING_THRESHOLD = 0.8

# Image Optimization
AUTO_OPTIMIZE_IMAGES = True
DEFAULT_IMAGE_FORMAT = 'WEBP'
MAX_IMAGE_DIMENSIONS = (2048, 1536)
IMAGE_QUALITY = {
    'JPEG': 85,
    'PNG': 95,
    'WEBP': 80
}

# Deduplication
ENABLE_HASH_DEDUPLICATION = True
HASH_ALGORITHM = 'SHA256'

# Storage Tiers (Government Compliance)
STORAGE_TIERS = {
    'HOT_TO_WARM': 30,      # 30 days on fast storage
    'WARM_TO_COLD': 90,     # 90 days total on main drive
    'COLD_TO_ARCHIVE': 365, # 1 year before external backup
    'ARCHIVE_DELETE': 2555, # 7 years retention
}

# Local Network Optimization
WIFI_ONLY_MODE = True
LOCAL_NETWORK_OPTIMIZED = True
OFFLINE_CAPABLE = True

# Government Compliance
GOVERNMENT_RETENTION_YEARS = 7
AUDIT_TRAIL_ENABLED = True
DATA_SOVEREIGNTY = True
```

### **Step 2: Environment Variables**
```bash
# Create .env file in project root
echo "MAX_LOCAL_STORAGE_GB=50" > .env
echo "ARCHIVE_STORAGE_PATH=D:/avicast_archive" >> .env
echo "STORAGE_WARNING_THRESHOLD=0.8" >> .env
echo "AUTO_OPTIMIZE_IMAGES=True" >> .env
echo "ENABLE_HASH_DEDUPLICATION=True" >> .env
```

### **Step 3: Media Directory Setup**
```bash
# Create media directories
mkdir media\bird_images
mkdir media\bird_images\2025
mkdir media\bird_images\2025\08
mkdir media\bird_images\2025\08\21

# Set permissions
icacls "media" /grant "Everyone:(OI)(CI)F"
```

---

## 🗄️ **Database Setup**

### **Step 1: Create Database Migrations**
```bash
# Generate migrations for new storage fields
python manage.py makemigrations image_processing

# Apply migrations
python manage.py migrate

# Verify migration status
python manage.py showmigrations image_processing
```

### **Step 2: Verify Database Schema**
```sql
-- Check new fields were added
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'image_processing_imageupload' 
AND column_name IN ('file_hash', 'storage_tier', 'archive_path', 'is_compressed');

-- Expected output:
-- file_hash | character varying
-- storage_tier | character varying  
-- archive_path | character varying
-- is_compressed | boolean
```

### **Step 3: Create Database Indexes**
```sql
-- Create indexes for performance
CREATE INDEX idx_image_file_hash ON image_processing_imageupload(file_hash);
CREATE INDEX idx_image_storage_tier ON image_processing_imageupload(storage_tier);
CREATE INDEX idx_image_upload_date ON image_processing_imageupload(uploaded_at);
CREATE INDEX idx_image_compressed ON image_processing_imageupload(is_compressed);
```

---

## 🧪 **Testing & Verification**

### **Step 1: Test Storage System**
```bash
# Check storage status
python manage.py storage_status

# Expected output:
# ✅ Storage system initialized successfully
# 📊 Main storage: 0GB / 50GB (0%)
# 📦 Archive storage: 0GB / 200GB (0%)
# 🗜️ Image optimization: Enabled
# 🔍 Deduplication: Enabled
```

### **Step 2: Test Image Upload**
```bash
# Upload a test image through the web interface
# Navigate to: http://localhost:8000/image-processing/upload/

# Check if optimization worked
python manage.py storage_status
# Should show compression statistics
```

### **Step 3: Test Cleanup System**
```bash
# Dry run cleanup (safe)
python manage.py cleanup_storage --dry-run --days=30

# Expected output:
# 🔍 DRY RUN - No files will be deleted
# 📁 Would archive 0 files
# 💾 Would free 0 MB
```

### **Step 4: Test Archive System**
```bash
# Check archive directory structure
dir D:\avicast_archive

# Should show:
# bird_images/
# backups/
# archive_manifest.json
```

---

## 🔧 **Troubleshooting**

### **Common Issues & Solutions:**

#### **Issue 1: Permission Denied Errors**
```bash
# Solution: Fix directory permissions
icacls "D:\avicast_archive" /grant "Everyone:(OI)(CI)F"
icacls "media" /grant "Everyone:(OI)(CI)F"
```

#### **Issue 2: Image Optimization Fails**
```bash
# Check Pillow installation
python -c "from PIL import Image; print('Pillow OK')"

# Reinstall if needed
pip uninstall Pillow
pip install Pillow
```

#### **Issue 3: Storage Not Detected**
```bash
# Check drive letters
wmic logicaldisk get size,freespace,caption

# Verify paths in settings
python manage.py shell
>>> from django.conf import settings
>>> print(settings.ARCHIVE_STORAGE_PATH)
```

#### **Issue 4: Database Migration Errors**
```bash
# Reset migrations if needed
python manage.py migrate image_processing zero
python manage.py makemigrations image_processing
python manage.py migrate image_processing
```

### **Log Files to Check:**
```
📁 Log Locations:
├── Django logs: logs/django.log
├── Storage logs: logs/storage.log
├── System logs: Event Viewer (Windows)
└── Application logs: %APPDATA%\AVICAST\logs\
```

---

## 📅 **Maintenance Schedule**

### **Daily Tasks (Automated):**
```bash
# Automatic cleanup (can be scheduled with Windows Task Scheduler)
python manage.py cleanup_storage --days=30

# Storage monitoring
python manage.py storage_status
```

### **Weekly Tasks:**
```bash
# Full storage report
python manage.py storage_report --detailed

# Backup to external drive
python manage.py backup_to_external --drive=E:
```

### **Monthly Tasks:**
```bash
# Archive verification
python manage.py verify_archive

# Performance optimization
python manage.py cleanup_storage --optimize-images
```

### **Quarterly Tasks:**
```bash
# External drive rotation
python manage.py export_archive --drive=F: --date=2025-Q1

# Full system backup
python manage.py full_backup --destination=G:\avicast_backup
```

---

## ✅ **Installation Checklist**

### **Pre-Installation:**
- [ ] Hardware requirements met
- [ ] Secondary drive (D:) available
- [ ] WiFi router configured
- [ ] Python 3.8+ installed
- [ ] Git installed

### **Installation:**
- [ ] Codebase cloned/updated
- [ ] Dependencies installed
- [ ] Storage directories created
- [ ] Permissions set correctly
- [ ] Settings configured

### **Database:**
- [ ] Migrations created
- [ ] Migrations applied
- [ ] Indexes created
- [ ] Schema verified

### **Testing:**
- [ ] Storage system initialized
- [ ] Test image uploaded
- [ ] Optimization working
- [ ] Cleanup system tested
- [ ] Archive system working

### **Production:**
- [ ] Automated tasks scheduled
- [ ] Backup routine established
- [ ] Monitoring configured
- [ ] Staff trained
- [ ] Documentation distributed

---

## 📞 **Support & Contact**

### **For Technical Issues:**
- **System Administrator**: [Your Name]
- **Email**: [admin@cenro.gov.ph]
- **Phone**: [Your Phone]

### **Emergency Procedures:**
1. **Storage Full**: Run `python manage.py cleanup_storage --force`
2. **System Down**: Check logs in `logs/` directory
3. **Data Loss**: Restore from external backup drive
4. **Performance Issues**: Check `python manage.py storage_status`

### **Useful Commands Reference:**
```bash
# Quick status check
python manage.py storage_status

# Emergency cleanup
python manage.py cleanup_storage --force --days=7

# Restore specific file
python manage.py restore_file --id=12345

# Full system backup
python manage.py full_backup --destination=E:\
```

---

## 🎯 **Next Steps After Installation**

1. **Train Staff** on new storage system
2. **Set up Monitoring** dashboard
3. **Establish Backup** routine
4. **Create Disaster Recovery** plan
5. **Schedule Regular** maintenance
6. **Document Procedures** for staff

**Your AVICAST local storage system is now ready for production use! 🚀**
