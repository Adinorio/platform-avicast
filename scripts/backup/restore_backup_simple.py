#!/usr/bin/env python3
"""
AVICAST Simple Restore Script
Restores system from backup files
"""

import os
import sys
import json
import zipfile
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'avicast_project.settings.development')
django.setup()

from django.core.management import call_command
from django.conf import settings


class SimpleRestore:
    def __init__(self):
        self.backup_dir = Path("backups")
        
    def list_backups(self):
        """List all available backup files"""
        print("[LIST] Available backups:")
        
        backups = list(self.backup_dir.glob('*.zip'))
        if not backups:
            print("   No backups found")
            return []
        
        backup_list = []
        for i, backup in enumerate(sorted(backups, key=lambda x: x.stat().st_mtime, reverse=True)):
            size_mb = backup.stat().st_size / (1024 * 1024)
            mod_time = datetime.fromtimestamp(backup.stat().st_mtime)
            print(f"   {i+1}. {backup.name} ({size_mb:.1f} MB) - {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
            backup_list.append(backup)
        
        return backup_list
    
    def restore_backup(self, backup_file):
        """Restore from a backup file"""
        print(f"[RESTORE] Starting restore from: {backup_file}")
        
        if not backup_file.exists():
            print(f"[ERROR] Backup file not found: {backup_file}")
            return False
        
        try:
            # Extract backup
            temp_dir = Path("temp_restore")
            temp_dir.mkdir(exist_ok=True)
            
            print(f"[EXTRACT] Extracting backup...")
            with zipfile.ZipFile(backup_file, 'r') as zipf:
                zipf.extractall(temp_dir)
            
            # Find database backup
            db_files = list(temp_dir.glob("database_*.json"))
            if db_files:
                print(f"[DB] Restoring database from {db_files[0].name}...")
                
                # Delete existing database
                db_path = Path(settings.DATABASES['default']['NAME'])
                if db_path.exists():
                    db_path.unlink()
                    print(f"[DB] Deleted existing database: {db_path}")
                
                # Run migrations
                call_command('migrate', interactive=False)
                print("[DB] Database schema migrated")
                
                # Load data
                call_command('loaddata', str(db_files[0]), verbosity=0)
                print("[OK] Database restored successfully")
            
            # Find media backup
            media_files = list(temp_dir.glob("media_*.zip"))
            if media_files:
                print(f"[MEDIA] Restoring media files from {media_files[0].name}...")
                
                media_root = Path(settings.MEDIA_ROOT)
                if media_root.exists():
                    import shutil
                    shutil.rmtree(media_root)
                    print(f"[MEDIA] Deleted existing media directory")
                
                media_root.mkdir(parents=True, exist_ok=True)
                
                with zipfile.ZipFile(media_files[0], 'r') as zipf:
                    zipf.extractall(media_root)
                print("[OK] Media files restored successfully")
            
            # Find config backup
            config_files = list(temp_dir.glob("config_*.zip"))
            if config_files:
                print(f"[CONFIG] Restoring configuration from {config_files[0].name}...")
                
                with zipfile.ZipFile(config_files[0], 'r') as zipf:
                    for member in zipf.namelist():
                        zipf.extract(member, path='.')
                print("[OK] Configuration restored successfully")
            
            # Cleanup
            import shutil
            shutil.rmtree(temp_dir)
            print(f"[CLEANUP] Cleaned up temporary files")
            
            print("[OK] Full system restore completed successfully!")
            return True
            
        except Exception as e:
            print(f"[ERROR] Restore failed: {e}")
            return False
    
    def interactive_restore(self):
        """Interactive restore process"""
        print("=== AVICAST System Restore ===")
        print()
        
        # List available backups
        backups = self.list_backups()
        if not backups:
            print("[ERROR] No backups available for restore")
            return
        
        print()
        try:
            choice = input("Enter backup number to restore (or 'q' to quit): ").strip()
            
            if choice.lower() == 'q':
                print("[INFO] Restore cancelled")
                return
            
            backup_index = int(choice) - 1
            if 0 <= backup_index < len(backups):
                selected_backup = backups[backup_index]
                
                print(f"\n[RESTORE] Selected: {selected_backup.name}")
                print("[WARNING] This will replace your current system data!")
                
                confirm = input("Type 'YES' to confirm restore: ").strip()
                if confirm == 'YES':
                    self.restore_backup(selected_backup)
                else:
                    print("[INFO] Restore cancelled")
            else:
                print("[ERROR] Invalid backup number")
                
        except ValueError:
            print("[ERROR] Please enter a valid number")
        except KeyboardInterrupt:
            print("\n[INFO] Restore cancelled")


def main():
    restore = SimpleRestore()
    
    if len(sys.argv) > 1:
        # Direct restore
        backup_name = sys.argv[1]
        backup_file = restore.backup_dir / backup_name
        
        if not backup_file.exists():
            print(f"[ERROR] Backup file not found: {backup_name}")
            return
        
        restore.restore_backup(backup_file)
    else:
        # Interactive restore
        restore.interactive_restore()


if __name__ == "__main__":
    main()
