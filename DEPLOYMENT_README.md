# 🚀 AVICAST Local Network Deployment

## Quick Start (Recommended)

### For Windows:
```bash
# Run the deployment script
deploy-local.bat
```

### For Linux/Mac:
```bash
# Make script executable and run
chmod +x deploy-local.sh
./deploy-local.sh
```

### Manual Setup:
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Setup database
python manage.py migrate

# 3. Create superuser
python manage.py createsuperuser

# 4. Start server (accessible from network)
python manage.py runserver 0.0.0.0:8000
```

## 🌐 Access from Other PCs

1. **Find Server IP**: Run `ipconfig` (Windows) or `ifconfig` (Linux/Mac)
2. **Access URL**: `http://SERVER_IP_ADDRESS:8000`
3. **Login**: Employee ID: `010101`, Password: `avicast123`

## 📚 Advanced Deployment Options

See `docs/LOCAL_NETWORK_DEPLOYMENT_GUIDE.md` for:
- Docker deployment
- Production server setup
- Security configurations
- Performance optimization

## 🔧 Requirements

- **Python 3.11+**
- **4GB+ RAM**
- **Network access for all users**
- **Same local network (WiFi/LAN)**

---

**Ready to deploy AVICAST on your local network!** 🐦
