#!/usr/bin/env python3
"""
Database Maintenance Script for Platform Avicast
Handles backups, optimization, and health checks for local-only deployment
"""

import os
import sys
import subprocess
import schedule
import time
from datetime import datetime, timedelta
from pathlib import Path
import shutil
import json

class DatabaseMaintenance:
    def __init__(self):
        self.backup_dir = Path('backups')
        self.backup_dir.mkdir(exist_ok=True)
        self.log_dir = Path('logs')
        self.log_dir.mkdir(exist_ok=True)
        
        # Load configuration
        self.config = self.load_config()
    
    def load_config(self):
        """Load configuration from environment or use defaults"""
        config = {
            'backup_retention_days': 30,
            'backup_time': '02:00',
            'database_name': 'avicast_db',
            'database_user': 'avicast',
            'backup_compression': True,
            'auto_optimization': True,
        }
        
        # Try to load from .env file
        env_file = Path('.env')
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        if key == 'DATABASE_URL':
                            # Extract database name from URL
                            if 'postgresql://' in value:
                                try:
                                    db_name = value.split('/')[-1]
                                    config['database_name'] = db_name
                                except:
                                    pass
                        elif key == 'BACKUP_RETENTION_DAYS':
                            try:
                                config['backup_retention_days'] = int(value)
                            except:
                                pass
        
        return config
    
    def log_message(self, message, level='INFO'):
        """Log a message to file and console"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] {level}: {message}"
        
        # Console output
        print(log_message)
        
        # File output
        log_file = self.log_dir / 'database_maintenance.log'
        with open(log_file, 'a') as f:
            f.write(log_message + '\n')
    
    def run_command(self, command, check=True):
        """Run a shell command and return the result"""
        try:
            result = subprocess.run(command, shell=True, check=check, 
                                  capture_output=True, text=True)
            return result
        except subprocess.CalledProcessError as e:
            self.log_message(f"Error running command: {command}", 'ERROR')
            self.log_message(f"Error details: {e}", 'ERROR')
            return None
    
    def create_backup(self):
        """Create a database backup"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"avicast_backup_{timestamp}.sql"
        backup_path = self.backup_dir / backup_filename
        
        self.log_message(f"Starting database backup: {backup_filename}")
        
        # Create backup using pg_dump
        backup_cmd = f"pg_dump -U {self.config['database_user']} -d {self.config['database_name']} -f {backup_path}"
        result = self.run_command(backup_cmd, check=False)
        
        if result and result.returncode == 0:
            # Compress backup if enabled
            if self.config['backup_compression']:
                compressed_path = backup_path.with_suffix('.sql.gz')
                compress_cmd = f"gzip {backup_path}"
                self.run_command(compress_cmd)
                backup_path = compressed_path
                self.log_message(f"Backup compressed: {compressed_path}")
            
            file_size = backup_path.stat().st_size / (1024 * 1024)  # MB
            self.log_message(f"Backup completed successfully: {backup_filename} ({file_size:.2f} MB)")
            
            # Clean old backups
            self.cleanup_old_backups()
            
            return True
        else:
            self.log_message("Backup failed", 'ERROR')
            return False
    
    def cleanup_old_backups(self):
        """Remove old backup files based on retention policy"""
        retention_days = self.config['backup_retention_days']
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        self.log_message(f"Cleaning up backups older than {retention_days} days")
        
        deleted_count = 0
        for backup_file in self.backup_dir.glob('avicast_backup_*.sql*'):
            try:
                # Extract date from filename
                filename = backup_file.stem
                if filename.startswith('avicast_backup_'):
                    date_str = filename.replace('avicast_backup_', '')
                    file_date = datetime.strptime(date_str, '%Y%m%d_%H%M%S')
                    
                    if file_date < cutoff_date:
                        backup_file.unlink()
                        deleted_count += 1
                        self.log_message(f"Deleted old backup: {backup_file.name}")
            except Exception as e:
                self.log_message(f"Error processing backup file {backup_file}: {e}", 'WARNING')
        
        self.log_message(f"Cleanup completed: {deleted_count} old backups removed")
    
    def check_database_health(self):
        """Check database health and performance"""
        self.log_message("Checking database health...")
        
        # Check database size
        size_cmd = f"psql -U {self.config['database_user']} -d {self.config['database_name']} -c \"SELECT pg_size_pretty(pg_database_size('{self.config['database_name']}'));\""
        result = self.run_command(size_cmd, check=False)
        
        if result and result.returncode == 0:
            size_output = result.stdout.strip()
            self.log_message(f"Database size: {size_output}")
        
        # Check active connections
        connections_cmd = f"psql -U {self.config['database_user']} -d {self.config['database_name']} -c \"SELECT count(*) as active_connections FROM pg_stat_activity WHERE state = 'active';\""
        result = self.run_command(connections_cmd, check=False)
        
        if result and result.returncode == 0:
            conn_output = result.stdout.strip()
            self.log_message(f"Active connections: {conn_output}")
        
        # Check table statistics
        tables_cmd = f"psql -U {self.config['database_user']} -d {self.config['database_name']} -c \"SELECT schemaname, tablename, n_tup_ins, n_tup_upd, n_tup_del FROM pg_stat_user_tables ORDER BY n_tup_ins DESC LIMIT 10;\""
        result = self.run_command(tables_cmd, check=False)
        
        if result and result.returncode == 0:
            self.log_message("Table statistics retrieved successfully")
        
        self.log_message("Database health check completed")
    
    def optimize_database(self):
        """Run database optimization tasks"""
        if not self.config['auto_optimization']:
            return
        
        self.log_message("Starting database optimization...")
        
        # Analyze tables for better query planning
        analyze_cmd = f"psql -U {self.config['database_user']} -d {self.config['database_name']} -c \"ANALYZE;\""
        result = self.run_command(analyze_cmd, check=False)
        
        if result and result.returncode == 0:
            self.log_message("Table analysis completed")
        else:
            self.log_message("Table analysis failed", 'WARNING')
        
        # Vacuum tables to reclaim storage
        vacuum_cmd = f"psql -U {self.config['database_user']} -d {self.config['database_name']} -c \"VACUUM ANALYZE;\""
        result = self.run_command(vacuum_cmd, check=False)
        
        if result and result.returncode == 0:
            self.log_message("Table vacuum completed")
        else:
            self.log_message("Table vacuum failed", 'WARNING')
        
        self.log_message("Database optimization completed")
    
    def restore_backup(self, backup_filename):
        """Restore database from backup"""
        backup_path = self.backup_dir / backup_filename
        
        if not backup_path.exists():
            self.log_message(f"Backup file not found: {backup_filename}", 'ERROR')
            return False
        
        self.log_message(f"Starting database restore from: {backup_filename}")
        
        # Check if backup is compressed
        if backup_path.suffix == '.gz':
            # Decompress first
            decompress_cmd = f"gunzip -c {backup_path}"
            restore_cmd = f"psql -U {self.config['database_user']} -d {self.config['database_name']}"
            full_cmd = f"{decompress_cmd} | {restore_cmd}"
        else:
            restore_cmd = f"psql -U {self.config['database_user']} -d {self.config['database_name']} -f {backup_path}"
            full_cmd = restore_cmd
        
        result = self.run_command(full_cmd, check=False)
        
        if result and result.returncode == 0:
            self.log_message("Database restore completed successfully")
            return True
        else:
            self.log_message("Database restore failed", 'ERROR')
            return False
    
    def list_backups(self):
        """List available backup files"""
        self.log_message("Available backup files:")
        
        backup_files = list(self.backup_dir.glob('avicast_backup_*.sql*'))
        backup_files.sort(reverse=True)
        
        if not backup_files:
            self.log_message("No backup files found")
            return
        
        for backup_file in backup_files:
            file_size = backup_file.stat().st_size / (1024 * 1024)  # MB
            modified_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
            self.log_message(f"  {backup_file.name} - {file_size:.2f} MB - {modified_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    def schedule_maintenance(self):
        """Schedule automatic maintenance tasks"""
        self.log_message("Setting up scheduled maintenance tasks...")
        
        # Schedule daily backup at 2 AM
        schedule.every().day.at(self.config['backup_time']).do(self.create_backup)
        
        # Schedule weekly optimization
        schedule.every().sunday.at("03:00").do(self.optimize_database)
        
        # Schedule daily health check
        schedule.every().day.at("06:00").do(self.check_database_health)
        
        self.log_message("Scheduled maintenance tasks:")
        self.log_message(f"  - Daily backup at {self.config['backup_time']}")
        self.log_message("  - Weekly optimization on Sunday at 03:00")
        self.log_message("  - Daily health check at 06:00")
        
        # Run the scheduler
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def run_manual_maintenance(self):
        """Run maintenance tasks manually"""
        self.log_message("Running manual maintenance tasks...")
        
        # Create backup
        self.create_backup()
        
        # Check health
        self.check_database_health()
        
        # Optimize if enabled
        if self.config['auto_optimization']:
            self.optimize_database()
        
        self.log_message("Manual maintenance completed")

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python database_maintenance.py [command]")
        print("Commands:")
        print("  backup     - Create a manual backup")
        print("  restore <filename> - Restore from backup")
        print("  health     - Check database health")
        print("  optimize   - Run database optimization")
        print("  list       - List available backups")
        print("  schedule   - Start scheduled maintenance")
        print("  manual     - Run all maintenance tasks")
        sys.exit(1)
    
    maintenance = DatabaseMaintenance()
    command = sys.argv[1]
    
    if command == 'backup':
        maintenance.create_backup()
    elif command == 'restore':
        if len(sys.argv) < 3:
            print("Error: Please specify backup filename")
            sys.exit(1)
        maintenance.restore_backup(sys.argv[2])
    elif command == 'health':
        maintenance.check_database_health()
    elif command == 'optimize':
        maintenance.optimize_database()
    elif command == 'list':
        maintenance.list_backups()
    elif command == 'schedule':
        maintenance.schedule_maintenance()
    elif command == 'manual':
        maintenance.run_manual_maintenance()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
