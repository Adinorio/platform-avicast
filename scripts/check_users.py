import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'avicast_project.settings.development')
django.setup()

from django.contrib.auth import get_user_model

def main():
    User = get_user_model()

    print("=== Checking Existing Users ===")
    users = User.objects.all()
    print(f"Total users: {users.count()}")

    for user in users:
        print(f"  - Username: {user.username}")
        print(f"    Email: {user.email}")
        print(f"    Superuser: {user.is_superuser}")
        print(f"    Active: {user.is_active}")
        print()

    # Create default user if none exists
    if users.count() == 0:
        print("=== Creating Default User ===")
        try:
            user = User.objects.create_user(
                username='admin',
                email='admin@avicast.local',
                password='avicast123',
                is_staff=True,
                is_superuser=True,
                is_active=True
            )
            print("✅ Created default user:")
            print(f"   Username: {user.username}")
            print(f"   Password: avicast123")
            print(f"   Email: {user.email}")
        except Exception as e:
            print(f"❌ Error creating user: {e}")

    print("\n=== Login Instructions ===")
    print("Go to: http://127.0.0.1:8000/")
    print("Login with:")
    if users.count() > 0:
        first_user = users.first()
        print(f"  Username: {first_user.username}")
        print("  Password: avicast123 (default)"
    else:
        print("  Username: admin")
        print("  Password: avicast123")

if __name__ == "__main__":
    main()
