#!/usr/bin/env python
"""
Script to create default superadmin user for first-time setup.
This should be run after migrations are complete.
"""

import os

import django

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "avicast_project.settings.development")
django.setup()

from apps.users.models import User


def create_default_superadmin():
    """Create the default superadmin user - ALWAYS ensure 010101 exists with correct password."""

    # ALWAYS ensure the default user 010101 exists with the correct password
    print("🔧 Ensuring default superadmin user '010101' exists with correct password...")

    try:
        # Check if default user already exists
        if User.objects.filter(employee_id="010101").exists():
            user = User.objects.get(employee_id="010101")
            # ALWAYS update password to ensure it's correct
            user.set_password("avicast123")
            user.save()
            print("✅ Default superadmin user '010101' exists - password updated to 'avicast123'")
        else:
            # Create the default superadmin user
            print("🆕 Creating default superadmin user '010101'...")
            user = User.objects.create_user(
                employee_id="010101",
                password="avicast123",  # CORRECT default password
                first_name="Default",
                last_name="Admin", 
                email="admin@avicast.local",
                role="SUPERADMIN",
                is_staff=True,
                is_superuser=True,
                is_active=True,
            )
            print("✅ Default superadmin user created successfully!")

        print(f"   Employee ID: {user.employee_id}")
        print(f"   Role: {user.role}")
        print("   Password: avicast123")
        print("\n🔑 ALWAYS login with: Employee ID='010101', Password='avicast123'")

    except Exception as e:
        print(f"❌ Error creating/updating default user: {e}")
        return False

    return True


if __name__ == "__main__":
    print("🚀 Setting up default superadmin user...")
    create_default_superadmin()
    print("✨ Setup complete!")
