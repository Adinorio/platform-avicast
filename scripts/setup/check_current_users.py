#!/usr/bin/env python
import os

import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "avicast_project.settings.development")
django.setup()

from django.contrib.auth.models import Group, Permission

from apps.users.models import User

print("=== Current Users ===")
for user in User.objects.all():
    print(f"Employee ID: {user.employee_id}")
    print(f"  Role: {user.role}")
    print(f"  Is Superuser: {user.is_superuser}")
    print(f"  Is Staff: {user.is_staff}")
    print(f"  Is Active: {user.is_active}")
    print(f"  Name: {user.first_name} {user.last_name}")
    print("---")

print("\n=== Current Groups ===")
for group in Group.objects.all():
    print(f"Group: {group.name}")
    print(f"  Permissions: {[p.codename for p in group.permissions.all()]}")
    print("---")

print("\n=== Current Permissions ===")
for perm in Permission.objects.all():
    print(f"{perm.content_type.app_label}.{perm.codename} - {perm.name}")
