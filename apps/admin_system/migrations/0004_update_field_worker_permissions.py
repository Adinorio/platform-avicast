# Generated migration to update FIELD_WORKER permissions

from django.db import migrations


def update_field_worker_permissions(apps, schema_editor):
    """Update FIELD_WORKER permissions to have view-only access to main features"""
    RolePermission = apps.get_model('admin_system', 'RolePermission')
    
    try:
        field_worker_permission = RolePermission.objects.get(role='FIELD_WORKER')
        # FIELD_WORKER: View-only access to all main system features
        field_worker_permission.can_generate_reports = False  # Cannot generate reports
        field_worker_permission.can_modify_species = False    # Cannot modify species data
        field_worker_permission.can_add_sites = False         # Cannot add sites
        field_worker_permission.can_add_birds = False         # Cannot add birds
        field_worker_permission.can_process_images = False    # Cannot process images
        field_worker_permission.can_access_weather = True     # Can view weather data
        field_worker_permission.can_access_analytics = True   # Can view analytics
        field_worker_permission.can_manage_users = False      # Cannot manage users
        field_worker_permission.save()
        print("Updated FIELD_WORKER permissions for view-only access")
    except RolePermission.DoesNotExist:
        print("FIELD_WORKER permission not found")


def reverse_update_field_worker_permissions(apps, schema_editor):
    """Reverse migration"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('admin_system', '0003_fix_role_permissions'),
    ]

    operations = [
        migrations.RunPython(update_field_worker_permissions, reverse_update_field_worker_permissions),
    ]
