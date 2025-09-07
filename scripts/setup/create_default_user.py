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
    """Create the default superadmin user if it doesn't exist."""

    # Check if default user already exists
    if User.objects.filter(username="010101").exists():
        print("✅ Default superadmin user '010101' already exists.")
        return

    # Check if any users exist at all
    if User.objects.count() == 0:
        print("🆕 No users found. Creating default superadmin...")

        try:
            # Create the default superadmin user
            user = User.objects.create_user(
                username="010101",
                employee_id="010101",
                email="admin@avicast.local",
                password="ChangeMe123!",  # Temporary password - MUST be changed on first login
                role="SUPERADMIN",
                is_staff=True,
                is_superuser=True,
                is_active=True,
            )

            print("✅ Default superadmin user created successfully!")
            print(f"   Username: {user.username}")
            print(f"   Employee ID: {user.employee_id}")
            print(f"   Role: {user.role}")
            print("   Password: avicast123")
            print("\n🔑 You can now login with these credentials!")

        except Exception as e:
            print(f"❌ Error creating default user: {e}")
            return False
    else:
        print("ℹ️  Users already exist in the database.")

    return True


if __name__ == "__main__":
    print("🚀 Setting up default superadmin user...")
    create_default_superadmin()
    print("✨ Setup complete!")
