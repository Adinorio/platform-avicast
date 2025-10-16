"""
Backup Management Views for Superadmin Dashboard
"""

import os
import json
import zipfile
from pathlib import Path
from datetime import datetime

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.conf import settings

from apps.users.models import User


@login_required
def backup_management(request):
    """Backup management dashboard for superadmins"""
    
    # Only superadmins can access backup management
    if request.user.role != User.Role.SUPERADMIN:
        messages.error(request, "Access denied. Superadmin privileges required.")
        return redirect('admin_system:admin_dashboard')
    
    # Check for custom backup location
    config_file = Path('backup_config.json')
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                backup_dir = Path(config_data.get('backup_location', 'backups'))
        except Exception:
            backup_dir = Path("backups")
    else:
        backup_dir = Path("backups")
    
    backup_dir.mkdir(exist_ok=True)
    
    # Get backup files
    backup_files = []
    for backup_file in backup_dir.glob('*.zip'):
        size_mb = backup_file.stat().st_size / (1024 * 1024)
        mod_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
        
        backup_files.append({
            'name': backup_file.name,
            'size_mb': round(size_mb, 2),
            'created': mod_time.strftime('%Y-%m-%d %H:%M:%S'),
            'type': 'full' if 'full' in backup_file.name else 'partial'
        })
    
    # Sort by creation time (newest first)
    backup_files.sort(key=lambda x: x['created'], reverse=True)
    
    # Get backup statistics
    total_backups = len(backup_files)
    total_size = sum(f['size_mb'] for f in backup_files)
    
    context = {
        'backup_files': backup_files,
        'total_backups': total_backups,
        'total_size_mb': round(total_size, 2),
        'backup_dir': str(backup_dir.absolute()),
        'page_title': 'Backup Management'
    }
    
    return render(request, 'admin_system/backup_management.html', context)


@login_required
@require_http_methods(["POST"])
def create_backup(request):
    """Create a new backup"""
    
    # Only superadmins can create backups
    if request.user.role != User.Role.SUPERADMIN:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    backup_type = request.POST.get('type', 'full')
    
    try:
        # Import backup system
        import sys
        sys.path.append(str(Path(__file__).parent.parent.parent))
        from scripts.backup.create_backup import AVICASTBackup
        
        backup = AVICASTBackup()
        
        if backup_type == 'full':
            result = backup.create_full_backup()
        elif backup_type == 'database':
            result = backup.create_database_backup()
        elif backup_type == 'media':
            result = backup.create_media_backup()
        elif backup_type == 'config':
            result = backup.create_config_backup()
        else:
            return JsonResponse({'error': 'Invalid backup type'}, status=400)
        
        if result:
            messages.success(request, f"Backup created successfully: {result.name}")
            return JsonResponse({'success': True, 'message': f"Backup created: {result.name}"})
        else:
            return JsonResponse({'error': 'Backup creation failed'}, status=500)
            
    except Exception as e:
        return JsonResponse({'error': f"Backup failed: {str(e)}"}, status=500)


@login_required
@require_http_methods(["POST"])
def delete_backup(request):
    """Delete a backup file"""
    
    # Only superadmins can delete backups
    if request.user.role != User.Role.SUPERADMIN:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    backup_name = request.POST.get('backup_name')
    if not backup_name:
        return JsonResponse({'error': 'Backup name required'}, status=400)
    
    try:
        backup_file = Path("backups") / backup_name
        if backup_file.exists():
            backup_file.unlink()
            messages.success(request, f"Backup deleted: {backup_name}")
            return JsonResponse({'success': True, 'message': f"Backup deleted: {backup_name}"})
        else:
            return JsonResponse({'error': 'Backup file not found'}, status=404)
            
    except Exception as e:
        return JsonResponse({'error': f"Delete failed: {str(e)}"}, status=500)


@login_required
def download_backup(request, backup_name):
    """Download a backup file"""
    
    # Only superadmins can download backups
    if request.user.role != User.Role.SUPERADMIN:
        messages.error(request, "Access denied. Superadmin privileges required.")
        return redirect('admin_system:admin_dashboard')
    
    try:
        backup_file = Path("backups") / backup_name
        if not backup_file.exists():
            messages.error(request, "Backup file not found.")
            return redirect('admin_system:backup_management')
        
        # Create response
        response = HttpResponse(backup_file.read_bytes(), content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="{backup_name}"'
        
        return response
        
    except Exception as e:
        messages.error(request, f"Download failed: {str(e)}")
        return redirect('admin_system:backup_management')


@login_required
def backup_status(request):
    """Get backup system status"""
    
    # Only superadmins can view backup status
    if request.user.role != User.Role.SUPERADMIN:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    try:
        backup_dir = Path("backups")
        backup_dir.mkdir(exist_ok=True)
        
        # Get backup files
        backup_files = list(backup_dir.glob('*.zip'))
        
        # Calculate statistics
        total_size = sum(f.stat().st_size for f in backup_files)
        total_size_mb = total_size / (1024 * 1024)
        
        # Get latest backup
        latest_backup = None
        if backup_files:
            latest_backup = max(backup_files, key=lambda x: x.stat().st_mtime)
            latest_backup_time = datetime.fromtimestamp(latest_backup.stat().st_mtime)
            latest_backup = {
                'name': latest_backup.name,
                'created': latest_backup_time.strftime('%Y-%m-%d %H:%M:%S'),
                'size_mb': round(latest_backup.stat().st_size / (1024 * 1024), 2)
            }
        
        status = {
            'total_backups': len(backup_files),
            'total_size_mb': round(total_size_mb, 2),
            'latest_backup': latest_backup,
            'backup_dir_exists': backup_dir.exists(),
            'backup_dir_writable': os.access(backup_dir, os.W_OK)
        }
        
        return JsonResponse(status)
        
    except Exception as e:
        return JsonResponse({'error': f"Status check failed: {str(e)}"}, status=500)


@login_required
@require_http_methods(["POST"])
def update_backup_location(request):
    """Update the backup location"""
    
    # Only superadmins can update backup location
    if request.user.role != User.Role.SUPERADMIN:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    new_location = request.POST.get('new_location', '').strip()
    
    if not new_location:
        return JsonResponse({'error': 'Backup location is required'}, status=400)
    
    try:
        # Validate the path
        backup_path = Path(new_location)
        
        # Try to create the directory if it doesn't exist
        backup_path.mkdir(parents=True, exist_ok=True)
        
        # Test if the directory is writable
        test_file = backup_path / 'test_write.tmp'
        try:
            test_file.write_text('test')
            test_file.unlink()
        except Exception as e:
            return JsonResponse({'error': f'Directory is not writable: {str(e)}'}, status=400)
        
        # Update the backup location in settings or configuration
        # For now, we'll store it in a simple config file
        config_file = Path('backup_config.json')
        config_data = {
            'backup_location': str(backup_path.absolute()),
            'updated_by': request.user.employee_id,
            'updated_at': timezone.now().isoformat()
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2)
        
        return JsonResponse({
            'success': True, 
            'message': f'Backup location updated to: {backup_path.absolute()}',
            'new_location': str(backup_path.absolute())
        })
        
    except Exception as e:
        return JsonResponse({'error': f'Failed to update backup location: {str(e)}'}, status=500)


@login_required
@require_http_methods(["POST"])
def restore_backup(request):
    """Restore system from a backup file"""
    
    # Only superadmins can restore backups
    if request.user.role != User.Role.SUPERADMIN:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    restore_type = request.POST.get('restore_type', 'existing')
    restore_options_json = request.POST.get('restore_options', '{}')
    
    try:
        import json
        restore_options = json.loads(restore_options_json)
        
        backup_file = None
        
        if restore_type == 'existing':
            # Restore from existing backup
            backup_name = request.POST.get('backup_name', '').strip()
            if not backup_name:
                return JsonResponse({'error': 'Backup name is required'}, status=400)
            
            # Check for custom backup location
            config_file = Path('backup_config.json')
            if config_file.exists():
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config_data = json.load(f)
                        backup_dir = Path(config_data.get('backup_location', 'backups'))
                except Exception:
                    backup_dir = Path("backups")
            else:
                backup_dir = Path("backups")
            
            backup_file = backup_dir / backup_name
            
            if not backup_file.exists():
                return JsonResponse({'error': f'Backup file not found: {backup_name}'}, status=404)
                
        elif restore_type == 'path':
            # Restore from drive path
            backup_path = request.POST.get('backup_path', '').strip()
            if not backup_path:
                return JsonResponse({'error': 'Backup path is required'}, status=400)
            
            backup_file = Path(backup_path)
            
            if not backup_file.exists():
                return JsonResponse({'error': f'Backup file not found: {backup_path}'}, status=404)
            
            if not backup_file.is_file():
                return JsonResponse({'error': f'Path is not a file: {backup_path}'}, status=400)
                
        elif restore_type == 'upload':
            # Restore from uploaded file
            uploaded_file = request.FILES.get('backup_file')
            if not uploaded_file:
                return JsonResponse({'error': 'No backup file uploaded'}, status=400)
            
            # Save uploaded file to temporary location
            temp_dir = Path('temp_restore_uploads')
            temp_dir.mkdir(exist_ok=True)
            
            backup_file = temp_dir / uploaded_file.name
            
            # Write uploaded file to disk
            with open(backup_file, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
        else:
            return JsonResponse({'error': 'Invalid restore type'}, status=400)
        
        # Check if database is locked (server running)
        db_path = Path(settings.DATABASES['default']['NAME'])
        if db_path.exists():
            try:
                # Try to open the database file exclusively
                with open(db_path, 'r+b') as f:
                    pass
            except (IOError, OSError) as e:
                if "being used by another process" in str(e) or "WinError 32" in str(e):
                    return JsonResponse({
                        'error': 'Database is locked. Please stop the Django server first, then run the restore from command line.'
                    }, status=400)
        
        # Import the restore functionality
        import sys
        sys.path.append(str(Path(__file__).parent.parent.parent))
        from scripts.backup.restore_backup_simple import SimpleRestore
        
        restore_manager = SimpleRestore()
        
        # Execute restore
        success = restore_manager.restore_backup(backup_file)
        
        # Clean up temporary uploaded file
        if restore_type == 'upload' and backup_file.exists():
            backup_file.unlink()
        
        if success:
            return JsonResponse({
                'success': True,
                'message': f'System restored successfully from {backup_file.name}. Please restart the server.',
                'restore_options': restore_options
            })
        else:
            return JsonResponse({'error': 'Restore process failed. Check server logs for details.'}, status=500)
            
    except Exception as e:
        return JsonResponse({'error': f'Restore failed: {str(e)}'}, status=500)
