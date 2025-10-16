from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Creates the default superadmin user if it doesn't exist"

    def handle(self, *args, **options):
        User = get_user_model()

        # ALWAYS ensure the default user 010101 exists with the correct password
        self.stdout.write("Ensuring default superadmin user '010101' exists with correct password...")

        try:
            # Check if default user already exists
            if User.objects.filter(employee_id="010101").exists():
                user = User.objects.get(employee_id="010101")
                # ALWAYS update password to ensure it's correct
                user.set_password("avicast123")
                user.save()
                self.stdout.write(
                    self.style.SUCCESS("Default superadmin user '010101' exists - password updated to 'avicast123'")
                )
            else:
                # Create the default superadmin user
                self.stdout.write("Creating default superadmin user '010101'...")
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
                self.stdout.write(
                    self.style.SUCCESS("Default superadmin user created successfully!")
                )

            self.stdout.write(f"   Employee ID: {user.employee_id}")
            self.stdout.write(f"   Role: {user.role}")
            self.stdout.write("   Password: avicast123")
            self.stdout.write("\nALWAYS login with: Employee ID='010101', Password='avicast123'")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error creating/updating default user: {e}"))
            return False
