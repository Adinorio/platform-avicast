import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'avicast_project.settings.development')
django.setup()

from apps.users.models import User

print("All users in the system:")
users = User.objects.all()
for user in users:
    print(f"  - {user.employee_id}: {user.email} (role: {user.role})")

print(f"\nTotal users: {users.count()}")


