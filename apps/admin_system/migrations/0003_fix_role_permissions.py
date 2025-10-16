# Generated migration to fix role permissions

from django.db import migrations


def fix_role_permissions(apps, schema_editor):
    """Set correct default permissions for each role"""
    RolePermission = apps.get_model('admin_system', 'RolePermission')
    
    # Get or create permissions for each role
    for role in ['SUPERADMIN', 'ADMIN', 'FIELD_WORKER']:
        permission, created = RolePermission.objects.get_or_create(role=role)
        
        if role == 'SUPERADMIN':
            # SUPERADMIN: Only user management access
            permission.can_generate_reports = False
            permission.can_modify_species = False
            permission.can_add_sites = False
            permission.can_add_birds = False
            permission.can_process_images = False
            permission.can_access_weather = False
            permission.can_access_analytics = False
            permission.can_manage_users = True
        elif role == 'ADMIN':
            # ADMIN: All main system features
            permission.can_generate_reports = True
            permission.can_modify_species = True
            permission.can_add_sites = True
            permission.can_add_birds = True
            permission.can_process_images = True
            permission.can_access_weather = True
            permission.can_access_analytics = True
            permission.can_manage_users = False
        elif role == 'FIELD_WORKER':
            # FIELD_WORKER: View-only access to all main system features
            permission.can_generate_reports = False  # Cannot generate reports
            permission.can_modify_species = False    # Cannot modify species data
            permission.can_add_sites = False         # Cannot add sites
            permission.can_add_birds = False         # Cannot add birds
            permission.can_process_images = False    # Cannot process images
            permission.can_access_weather = True     # Can view weather data
            permission.can_access_analytics = True   # Can view analytics
            permission.can_manage_users = False      # Cannot manage users
        
        permission.save()


def reverse_fix_role_permissions(apps, schema_editor):
    """Reverse migration - set all permissions to default"""
    RolePermission = apps.get_model('admin_system', 'RolePermission')
    
    for role in ['SUPERADMIN', 'ADMIN', 'FIELD_WORKER']:
        try:
            permission = RolePermission.objects.get(role=role)
            # Reset to defaults
            permission.can_generate_reports = True
            permission.can_modify_species = True
            permission.can_add_sites = True
            permission.can_add_birds = True
            permission.can_process_images = True
            permission.can_access_weather = True
            permission.can_access_analytics = True
            permission.can_manage_users = False
            permission.save()
        except RolePermission.DoesNotExist:
            pass


class Migration(migrations.Migration):

    dependencies = [
        ('admin_system', '0002_rolepermission'),
    ]

    operations = [
        migrations.RunPython(fix_role_permissions, reverse_fix_role_permissions),
    ]
