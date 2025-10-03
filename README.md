# AVICAST Platform

A comprehensive wildlife monitoring and analytics platform designed for local deployment with strict data privacy controls.

## 🚀 Features

- **User Management**: Role-based access control (SUPERADMIN, ADMIN, USER)
- **Location Management**: Site and census data tracking
- **Fauna Monitoring**: Species observation and population tracking
- **Analytics Dashboard**: Data visualization and reporting
- **Mobile App Ready**: RESTful API endpoints for mobile integration
- **Local Deployment**: Designed for offline/local network use
- **Data Privacy**: Strict controls preventing external data transmission

## 📋 Prerequisites

- **Python**: 3.8 or higher
- **Operating System**: Windows, macOS, or Linux
- **Memory**: Minimum 4GB RAM (8GB recommended)
- **Storage**: 2GB free space minimum

## ⚠️ Important: Large Files Not Included

This repository is configured to **NOT** include large files that should not be pushed to GitHub:

### **Excluded Files & Folders:**
- **ML Models**: All `.pt` files (YOLO models) - these are very large (18MB to 131MB each)
- **Datasets**: `dataset/` folder with training images and labels
- **Training Outputs**: `runs/` folder with model training results
- **Compressed Files**: `.zip`, `.tar.gz`, `.rar` files
- **Media Files**: Large image, video, and audio files
- **Database Files**: `.sqlite3`, `.db` files

### **Why These Are Excluded:**
- **Repository Size**: These files would make the repo extremely large (potentially GBs)
- **Git Performance**: Large files slow down Git operations
- **GitHub Limits**: GitHub has file size limits and repository size recommendations
- **Collaboration**: Large files make cloning and pulling very slow

### **How to Get These Files:**
- **Models**: Download YOLO models from official sources or your training runs
- **Datasets**: Download from your data sources or recreate from scripts
- **Training Outputs**: These are generated during training runs

## 🛠️ Quick Setup

### **Option 1: Automated Setup (Recommended)**

#### **Windows Users:**
```bash
# Download and run the setup script
setup.bat
```

#### **Linux/macOS Users:**
```bash
# Make script executable and run
chmod +x setup.sh
./setup.sh
```

**The automated setup will:**
- ✅ Create virtual environment
- ✅ Install all dependencies
- ✅ Set up database
- ✅ Create default superadmin user
- ✅ Configure static files

### **Option 2: Manual Setup**

#### **1. Clone and Navigate**
```bash
git clone <repository-url>
cd platform-avicast
```

#### **2. Create Virtual Environment**
```bash
# Windows
python -m venv venv
venv\Scripts\activate.bat

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

#### **3. Install Dependencies**
```bash
pip install -r requirements.txt
```

#### **4. Environment Configuration**
```bash
# Copy example environment file
copy env.example .env

# Edit .env with your settings
# Required: SECRET_KEY, DEBUG
# Optional: DATABASE_URL, ALLOWED_HOSTS
```

#### **5. Database Setup**
```bash
# Create and apply migrations
python manage.py makemigrations
python manage.py migrate

# Create default superadmin user
python create_default_user.py
```

#### **6. Start Server**
```bash
python manage.py runserver
```

## 🔑 Default Login Credentials

After setup, you can login with:
- **Username**: `010101`
- **Password**: `avicast123`
- **Role**: `SUPERADMIN`

## 🌐 Access Points

- **Main Application**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin
- **API Endpoints**: http://localhost:8000/api/

## 📱 Mobile App Integration

The platform includes:
- **RESTful APIs** for mobile data sync
- **Authentication endpoints** for user management
- **Offline data collection** capabilities
- **Local network synchronization**

## 🗄️ Database Options

### **Development (Default)**
- **SQLite**: `db.sqlite3` (included)
- **No additional setup required**

### **Production (Recommended)**
- **PostgreSQL**: For robust data handling
- **Install**: `pip install psycopg2-binary`
- **Configure**: Update `.env` with `DATABASE_URL`

## 🔧 Development Commands

```bash
# Check system health
python manage.py check

# View migrations
python manage.py showmigrations

# Create superuser
python manage.py createsuperuser

# Django shell
python manage.py shell

# Collect static files
python manage.py collectstatic
```

### Weather app tests (unit stubs)

```bash
python manage.py test apps.weather -v 2
```

## 📁 Project Structure

```
platform-avicast/
├── apps/                    # Django applications
│   ├── users/              # User management
│   ├── locations/          # Site and census data
│   ├── fauna/              # Species monitoring
│   └── analytics/          # Data visualization
├── avicast_project/        # Project configuration
├── templates/              # HTML templates
├── static/                 # CSS, JS, images
├── requirements.txt        # Python dependencies
├── setup.bat              # Windows setup script
├── setup.sh               # Linux/macOS setup script
└── create_default_user.py # Default user creation
```

## 🚨 Common Issues & Solutions

### **ModuleNotFoundError: No module named 'openpyxl'**
```bash
# Activate virtual environment and install
venv\Scripts\activate.bat  # Windows
source venv/bin/activate   # Linux/macOS
pip install openpyxl
```

### **PowerShell Execution Policy Error**
```powershell
# Run as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### **Missing Static Directory**
```bash
# Create static directory
mkdir static
```

### **Database Migration Issues**
```bash
# Reset migrations (WARNING: Data loss)
python manage.py migrate --fake-initial
# Or recreate database
del db.sqlite3
python manage.py migrate
```

### **Port Already in Use**
```bash
# Use different port
python manage.py runserver 8001
```

## 🔒 Security Features

- **Role-based access control**
- **Secure password hashing**
- **CSRF protection**
- **Session security**
- **Input validation**
- **SQL injection prevention**

## 📊 Data Management

- **Excel import/export** capabilities
- **Data validation** and integrity checks
- **Backup and recovery** procedures
- **Data migration** tools

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is proprietary software. All rights reserved.

## 🆘 Support

For technical support:
1. Check the troubleshooting guide
2. Review common issues above
3. Check Django documentation
4. Contact the development team

---

**Last Updated**: August 2025
**Version**: 1.0.0
**Django Version**: 4.2.23
