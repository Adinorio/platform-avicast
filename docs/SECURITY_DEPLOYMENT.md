# Security & Deployment Guide

## Overview

This guide covers the security measures and deployment procedures for Platform Avicast, configured for **local-only access** with strict data protection requirements.

## Security Features

### 🔒 **Network Security**
- **Local Network Only**: Database and application restricted to local network
- **IP Whitelisting**: Only local network IPs can access the system
- **No Internet Access**: Database cannot be accessed from external networks
- **Firewall Protection**: Configured to block external connections

### 🛡️ **Application Security**
- **Rate Limiting**: Prevents brute force attacks
- **Login Attempt Tracking**: Locks accounts after 5 failed attempts
- **Session Security**: Secure cookies with expiration
- **CSRF Protection**: Cross-site request forgery prevention
- **XSS Protection**: Browser security headers enabled

### 🔐 **Authentication & Authorization**
- **Role-Based Access Control**: SUPERADMIN, ADMIN, FIELD_WORKER roles
- **Strong Password Hashing**: Argon2 + PBKDF2 algorithms
- **Employee ID Authentication**: Custom authentication backend
- **Session Management**: Secure session handling

### 📊 **Data Protection**
- **Local Storage Only**: All data stays within your network
- **Encrypted Backups**: Compressed and encrypted database backups
- **Audit Logging**: All actions logged for compliance
- **Data Validation**: Input sanitization and validation

## Database Configuration

### PostgreSQL Setup

1. **Install PostgreSQL**:
   ```bash
   # Windows: Download from https://www.postgresql.org/download/windows/
   # macOS: brew install postgresql
   # Ubuntu: sudo apt-get install postgresql postgresql-contrib
   ```

2. **Run Database Setup**:
   ```bash
   python setup_database.py
   ```

3. **Verify Installation**:
   ```bash
   psql --version
   ```

### Database Security Settings

```sql
-- Restrict connections to local network only
-- Edit postgresql.conf
listen_addresses = 'localhost,192.168.1.0/24,10.0.0.0/8'

-- Edit pg_hba.conf
# Local network access
host    avicast_db    avicast    192.168.1.0/24    md5
host    avicast_db    avicast    10.0.0.0/8        md5
host    avicast_db    avicast    172.16.0.0/12     md5

# Deny all other connections
host    all           all        0.0.0.0/0          reject
```

## Mobile App Integration

### API Endpoints

The system provides RESTful API endpoints for mobile app integration:

```
Base URL: http://your-local-ip:8000/api/v1/

Authentication:
POST /api/v1/auth/login/          - User login
POST /api/v1/auth/logout/         - User logout
POST /api/v1/auth/refresh/        - Refresh token

Users:
GET  /api/v1/users/profile/       - Get user profile
PUT  /api/v1/users/profile/       - Update user profile

Sites:
GET  /api/v1/sites/               - List observation sites
POST /api/v1/sites/               - Create new site
GET  /api/v1/sites/{id}/          - Get site details
PUT  /api/v1/sites/{id}/          - Update site

Census:
GET  /api/v1/census/              - List census observations
POST /api/v1/census/              - Create census observation
GET  /api/v1/census/{id}/         - Get census details
POST /api/v1/census/import/       - Import census data
```

### Mobile App Configuration

1. **Set Base URL**: Configure your mobile app to use your local server IP
2. **Authentication**: Use employee ID and password for login
3. **Offline Support**: Implement local data caching for field work
4. **Data Sync**: Sync data when connected to local network

### CORS Configuration

```python
# Only allow local network origins
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",      # Web frontend
    "http://192.168.1.0:3000",   # Local network
    "capacitor://localhost",      # Mobile app
    "ionic://localhost",          # Ionic app
]
```

## Deployment Checklist

### Pre-Deployment

- [ ] PostgreSQL installed and configured
- [ ] Virtual environment activated
- [ ] All dependencies installed
- [ ] Environment variables configured
- [ ] Database created and migrated
- [ ] Superuser account created

### Security Verification

- [ ] Firewall blocks external connections
- [ ] Database only accessible from local network
- [ ] Strong passwords configured
- [ ] SSL certificates installed (if using HTTPS)
- [ ] Regular backup schedule configured
- [ ] Monitoring and logging enabled

### Performance Optimization

- [ ] Database indexes created
- [ ] Connection pooling configured
- [ ] Static files collected
- [ ] Cache backend configured
- [ ] Database maintenance scheduled

## Backup & Recovery

### Automated Backups

```bash
# Schedule daily backups
python database_maintenance.py schedule

# Manual backup
python database_maintenance.py backup

# Check backup status
python database_maintenance.py list
```

### Backup Retention

- **Daily backups**: Kept for 30 days
- **Compression**: Automatic gzip compression
- **Verification**: Backup integrity checks
- **Restore testing**: Monthly restore tests

### Disaster Recovery

1. **Stop Django application**
2. **Restore from backup**:
   ```bash
   python database_maintenance.py restore avicast_backup_20241201_020000.sql.gz
   ```
3. **Verify data integrity**
4. **Restart application**

## Monitoring & Maintenance

### Health Checks

```bash
# Daily health check
python database_maintenance.py health

# Database optimization
python database_maintenance.py optimize

# View logs
tail -f logs/database_maintenance.log
```

### Performance Monitoring

- **Database size**: Monitor growth trends
- **Connection count**: Track active connections
- **Query performance**: Monitor slow queries
- **Disk space**: Ensure adequate storage

### Security Monitoring

- **Failed login attempts**: Monitor for suspicious activity
- **Access logs**: Review network access patterns
- **User activity**: Track user actions and permissions
- **System updates**: Keep dependencies updated

## Troubleshooting

### Common Issues

1. **Connection Refused**:
   - Check PostgreSQL service status
   - Verify network configuration
   - Check firewall settings

2. **Authentication Failed**:
   - Verify database credentials
   - Check user permissions
   - Reset user password if needed

3. **Performance Issues**:
   - Run database optimization
   - Check connection pool settings
   - Monitor system resources

### Emergency Procedures

1. **Database Corruption**:
   - Stop application immediately
   - Restore from latest backup
   - Investigate root cause

2. **Security Breach**:
   - Disconnect from network
   - Assess damage scope
   - Restore from clean backup
   - Review security measures

## Compliance & Auditing

### Data Protection

- **No External Access**: Data never leaves local network
- **Encrypted Storage**: Sensitive data encrypted at rest
- **Access Logging**: All data access logged
- **User Permissions**: Role-based access control

### Audit Requirements

- **User Activity Logs**: Track all user actions
- **Data Access Logs**: Monitor data retrieval
- **System Change Logs**: Document configuration changes
- **Backup Verification**: Regular backup testing

### Regular Reviews

- **Monthly**: Security configuration review
- **Quarterly**: Access permission audit
- **Annually**: Full security assessment
- **As Needed**: Incident response reviews

## Support & Maintenance

### Regular Tasks

- **Daily**: Monitor system health and logs
- **Weekly**: Run database optimization
- **Monthly**: Review security settings and access logs
- **Quarterly**: Update dependencies and security patches

### Contact Information

- **System Administrator**: [Your Contact Info]
- **Database Administrator**: [Your Contact Info]
- **Security Officer**: [Your Contact Info]

### Documentation Updates

- Keep this guide updated with any changes
- Document all configuration modifications
- Maintain change log for audit purposes
- Update procedures based on lessons learned

---

**Remember**: This system is designed for local-only access. Never expose it to the internet or external networks. All data must remain within your organization's secure network perimeter.
