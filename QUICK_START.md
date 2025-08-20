# Quick Start Guide - Production Setup

## 🚀 **Get Started in 5 Steps**

### 1. **Install PostgreSQL**
```bash
# Windows: Download from https://www.postgresql.org/download/windows/
# macOS: brew install postgresql
# Ubuntu: sudo apt-get install postgresql postgresql-contrib
```

### 2. **Run Database Setup**
```bash
python setup_database.py
```
This will:
- Create PostgreSQL database and user
- Generate secure .env file
- Install all dependencies
- Run initial migrations

### 3. **Start the Server**
```bash
python manage.py runserver 0.0.0.0:8000
```
Your app will be available at `http://your-local-ip:8000`

### 4. **Configure Mobile App**
- Set base URL to your local server IP
- Use employee ID + password for authentication
- Implement offline data caching
- Sync when connected to local network

### 5. **Set Up Automated Maintenance**
```bash
# Schedule daily backups and optimization
python database_maintenance.py schedule
```

## 🔒 **Security Features Enabled**

✅ **Local Network Only** - No internet access  
✅ **Rate Limiting** - Prevents brute force attacks  
✅ **Login Tracking** - Locks accounts after 5 failed attempts  
✅ **Role-Based Access** - SUPERADMIN, ADMIN, FIELD_WORKER  
✅ **Encrypted Backups** - Automatic daily backups  
✅ **Audit Logging** - All actions logged  

## 📱 **Mobile Integration Ready**

- **API Endpoints**: `/api/v1/` for all mobile operations
- **Authentication**: Employee ID + password
- **CORS**: Configured for local network only
- **Offline Support**: Local data caching recommended

## 🗄️ **Database Management**

```bash
# Create backup
python database_maintenance.py backup

# Check health
python database_maintenance.py health

# Optimize performance
python database_maintenance.py optimize

# List backups
python database_maintenance.py list
```

## 🌐 **Network Configuration**

Your system will be accessible from:
- `localhost:8000`
- `192.168.1.x:8000` (local network)
- `10.0.0.x:8000` (private network)

**Never expose to internet!**

## 📋 **Next Steps**

1. **Create superuser**: `python manage.py createsuperuser`
2. **Configure firewall** to block external connections
3. **Set up monitoring** for system health
4. **Test mobile app** connection
5. **Schedule regular backups**

## 🆘 **Need Help?**

- **Setup Issues**: Check `TROUBLESHOOTING.md`
- **Security**: Review `SECURITY_DEPLOYMENT.md`
- **Database**: Use `database_maintenance.py` commands
- **General**: Check `README.md`

---

**Your data is now secure and local-only! 🎉**
