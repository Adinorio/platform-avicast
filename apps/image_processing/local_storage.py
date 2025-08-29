"""
Local Storage Management for AVICAST System
WiFi-only, local network deployment for CENRO
"""

import os
import shutil
import logging
from pathlib import Path
from typing import Optional, Tuple
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import json

logger = logging.getLogger(__name__)

# Import configuration at module level
try:
    from .config import IMAGE_CONFIG
except ImportError:
    # Fallback configuration
    IMAGE_CONFIG = {
        'MAX_LOCAL_STORAGE_GB': 50,
        'STORAGE_WARNING_THRESHOLD': 0.8,
    }

class LocalStorageManager:
    """Manages local storage optimization for WiFi-only systems"""
    
    def __init__(self):
        self.media_root = Path(settings.MEDIA_ROOT)
        # Use module-level configuration
        self.max_storage_gb = IMAGE_CONFIG['MAX_LOCAL_STORAGE_GB']
        self.archive_path = Path(getattr(settings, 'ARCHIVE_STORAGE_PATH', 'media/archive'))
        self.warning_threshold = IMAGE_CONFIG['STORAGE_WARNING_THRESHOLD']
        
        # Create archive directory if it doesn't exist (safely)
        try:
            self.archive_path.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as e:
            logger.warning(f"Could not create archive directory {self.archive_path}: {e}")
            # Fallback to media subdirectory
            self.archive_path = self.media_root / 'archive'
            self.archive_path.mkdir(parents=True, exist_ok=True)
        
    def get_storage_usage(self) -> dict:
        """Get detailed storage usage for local system"""
        # Main storage usage
        main_total, main_used, main_free = shutil.disk_usage(self.media_root)
        
        # Archive storage usage (safely)
        try:
            archive_total, archive_used, archive_free = shutil.disk_usage(self.archive_path)
        except (OSError, FileNotFoundError):
            # Archive path doesn't exist or not accessible
            archive_total = archive_used = archive_free = 0
        
        # AVICAST specific usage
        from .models import ImageUpload
        from django.db.models import Sum, Count
        
        active_files = ImageUpload.objects.filter(storage_tier__in=['HOT', 'WARM'])
        archived_files = ImageUpload.objects.filter(storage_tier__in=['COLD', 'ARCHIVE'])
        
        active_usage = active_files.aggregate(
            total_size=Sum('file_size'),
            count=Count('id')
        )
        
        archived_usage = archived_files.aggregate(
            total_size=Sum('file_size'), 
            count=Count('id')
        )
        
        return {
            'main_storage': {
                'total_gb': round(main_total / (1024**3), 2),
                'used_gb': round(main_used / (1024**3), 2),
                'free_gb': round(main_free / (1024**3), 2),
                'usage_percentage': round((main_used / main_total) * 100, 1)
            },
            'archive_storage': {
                'total_gb': round(archive_total / (1024**3), 2),
                'used_gb': round(archive_used / (1024**3), 2),
                'free_gb': round(archive_free / (1024**3), 2),
                'usage_percentage': round((archive_used / archive_total) * 100, 1)
            },
            'avicast_usage': {
                'active_files': {
                    'count': active_usage['count'] or 0,
                    'size_mb': round((active_usage['total_size'] or 0) / (1024**2), 2)
                },
                'archived_files': {
                    'count': archived_usage['count'] or 0,
                    'size_mb': round((archived_usage['total_size'] or 0) / (1024**2), 2)
                },
                'compression_savings_mb': self._calculate_compression_savings(),
                'compression_savings_percent': self._calculate_compression_percentage()
            },
            'recommendations': self._get_storage_recommendations()
        }
    
    def _get_storage_recommendations(self) -> list:
        """Generate storage optimization recommendations"""
        recommendations = []
        
        # Get main storage usage directly without recursion
        try:
            main_total, main_used, main_free = shutil.disk_usage(self.media_root)
            main_usage_percent = (main_used / main_total) * 100
        except (OSError, FileNotFoundError):
            main_usage_percent = 0
        
        if main_usage_percent > 90:
            recommendations.append({
                'level': 'critical',
                'message': 'Main storage almost full! Archive old files immediately.',
                'action': 'archive_old_files'
            })
        elif main_usage_percent > self.warning_threshold * 100:
            recommendations.append({
                'level': 'warning', 
                'message': f'Main storage {main_usage_percent:.1f}% full. Consider archiving files.',
                'action': 'review_storage'
            })
        
        # Check for unoptimized images
        from .models import ImageUpload
        unoptimized_count = ImageUpload.objects.filter(is_compressed=False).count()
        if unoptimized_count > 0:
            recommendations.append({
                'level': 'info',
                'message': f'{unoptimized_count} images can be optimized to save space.',
                'action': 'optimize_images'
            })
        
        return recommendations
    
    def archive_old_files(self, days_old: int = 30) -> dict:
        """Archive old files to secondary storage"""
        from .models import ImageUpload
        
        cutoff_date = timezone.now() - timedelta(days=days_old)
        old_files = ImageUpload.objects.filter(
            uploaded_at__lt=cutoff_date,
            storage_tier__in=['HOT', 'WARM']
        )
        
        archived_count = 0
        freed_space = 0
        errors = []
        
        for file_obj in old_files:
            try:
                if file_obj.image_file and os.path.exists(file_obj.image_file.path):
                    # Create archive directory structure
                    archive_dir = self.archive_path / 'bird_images' / str(file_obj.uploaded_at.year) / str(file_obj.uploaded_at.month)
                    archive_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Move file to archive
                    archive_file_path = archive_dir / file_obj.image_file.name.split('/')[-1]
                    shutil.move(file_obj.image_file.path, archive_file_path)
                    
                    # Update database record
                    file_obj.storage_tier = 'ARCHIVE'
                    file_obj.archive_path = str(archive_file_path)
                    file_obj.image_file = None  # Clear active file reference
                    file_obj.save()
                    
                    archived_count += 1
                    freed_space += file_obj.file_size
                    
            except Exception as e:
                errors.append(f"Failed to archive {file_obj.id}: {str(e)}")
                logger.error(f"Archive error: {e}")
        
        # Create archive manifest
        self._create_archive_manifest()
        
        return {
            'archived_count': archived_count,
            'freed_space_mb': round(freed_space / (1024**2), 2),
            'errors': errors
        }
    
    def _create_archive_manifest(self):
        """Create a manifest file for archived data"""
        from .models import ImageUpload
        
        archived_files = ImageUpload.objects.filter(storage_tier='ARCHIVE')
        
        manifest = {
            'created_at': timezone.now().isoformat(),
            'total_archived_files': archived_files.count(),
            'total_size_mb': round(sum(f.file_size for f in archived_files) / (1024**2), 2),
            'files': []
        }
        
        for file_obj in archived_files:
            manifest['files'].append({
                'id': str(file_obj.id),
                'original_filename': file_obj.original_filename,
                'uploaded_at': file_obj.uploaded_at.isoformat(),
                'uploaded_by': file_obj.uploaded_by.employee_id,
                'file_size': file_obj.file_size,
                'archive_path': getattr(file_obj, 'archive_path', None)
            })
        
        # Save manifest
        manifest_path = self.archive_path / 'archive_manifest.json'
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        logger.info(f"Archive manifest created: {manifest_path}")
    
    def restore_from_archive(self, file_id: str) -> bool:
        """Restore a specific file from archive back to active storage"""
        from .models import ImageUpload
        
        try:
            file_obj = ImageUpload.objects.get(id=file_id, storage_tier='ARCHIVE')
            archive_path = getattr(file_obj, 'archive_path', None)
            
            if archive_path and os.path.exists(archive_path):
                # Restore file to main storage
                restore_dir = self.media_root / 'bird_images' / str(file_obj.uploaded_at.year) / str(file_obj.uploaded_at.month) / str(file_obj.uploaded_at.day)
                restore_dir.mkdir(parents=True, exist_ok=True)
                
                restore_path = restore_dir / os.path.basename(archive_path)
                shutil.move(archive_path, restore_path)
                
                # Update database
                file_obj.image_file = str(restore_path.relative_to(self.media_root))
                file_obj.storage_tier = 'HOT'
                file_obj.archive_path = None
                file_obj.save()
                
                logger.info(f"File {file_id} restored from archive")
                return True
                
        except Exception as e:
            logger.error(f"Failed to restore file {file_id}: {e}")
            
        return False
    
    def export_archive_to_external_drive(self, drive_path: str) -> dict:
        """Export archive to external drive for backup"""
        try:
            external_path = Path(drive_path) / 'avicast_backup' / timezone.now().strftime('%Y%m%d')
            external_path.mkdir(parents=True, exist_ok=True)
            
            # Copy archive to external drive
            shutil.copytree(self.archive_path, external_path / 'archive', dirs_exist_ok=True)
            
            # Create backup info
            backup_info = {
                'created_at': timezone.now().isoformat(),
                'source_path': str(self.archive_path),
                'backup_path': str(external_path),
                'total_size_gb': round(shutil.disk_usage(self.archive_path)[1] / (1024**3), 2)
            }
            
            with open(external_path / 'backup_info.json', 'w') as f:
                json.dump(backup_info, f, indent=2)
            
            return {
                'success': True,
                'backup_path': str(external_path),
                'size_gb': backup_info['total_size_gb']
            }
            
        except Exception as e:
            logger.error(f"External backup failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _calculate_compression_savings(self) -> float:
        """Calculate total space saved through compression in MB"""
        from .models import ImageUpload
        
        try:
            compressed_files = ImageUpload.objects.filter(is_compressed=True)
            total_savings = 0
            
            for file_obj in compressed_files:
                if file_obj.file_size and file_obj.compressed_size:
                    savings = file_obj.file_size - file_obj.compressed_size
                    total_savings += savings
            
            return round(total_savings / (1024**2), 2)  # Convert to MB
        except (AttributeError, TypeError, ValueError):
            return 0.0
    
    def _calculate_compression_percentage(self) -> float:
        """Calculate percentage of space saved through compression"""
        from .models import ImageUpload
        
        try:
            compressed_files = ImageUpload.objects.filter(is_compressed=True)
            total_original = 0
            total_compressed = 0
            
            for file_obj in compressed_files:
                if file_obj.file_size and file_obj.compressed_size:
                    total_original += file_obj.file_size
                    total_compressed += file_obj.compressed_size
            
            if total_original > 0:
                savings_percent = ((total_original - total_compressed) / total_original) * 100
                return round(savings_percent, 1)
            else:
                return 0.0
        except (AttributeError, TypeError, ValueError):
            return 0.0

class LocalNetworkOptimizer:
    """Optimizations specific to WiFi-only local networks"""
    
    @staticmethod
    def optimize_for_local_network():
        """Configure system for optimal local network performance"""
        recommendations = []
        
        # Check for SSD vs HDD
        if LocalNetworkOptimizer._is_ssd_storage():
            recommendations.append("✅ SSD detected - optimal for frequent access")
        else:
            recommendations.append("⚠️ Consider SSD for main storage for better performance")
        
        # Check available RAM
        ram_gb = LocalNetworkOptimizer._get_available_ram()
        if ram_gb >= 8:
            recommendations.append("✅ Sufficient RAM for image processing")
        else:
            recommendations.append("⚠️ Consider 8GB+ RAM for better image processing")
        
        return recommendations
    
    @staticmethod
    def _is_ssd_storage() -> bool:
        """Check if main storage is SSD (Windows-specific)"""
        try:
            import subprocess
            result = subprocess.run(['wmic', 'diskdrive', 'get', 'MediaType'], 
                                  capture_output=True, text=True)
            return 'SSD' in result.stdout
        except:
            return False
    
    @staticmethod
    def _get_available_ram() -> float:
        """Get available RAM in GB"""
        try:
            import psutil
            return round(psutil.virtual_memory().total / (1024**3), 1)
        except ImportError:
            # psutil not available, return default value
            return 8.0  # Assume 8GB as default
        except Exception:
            return 0
