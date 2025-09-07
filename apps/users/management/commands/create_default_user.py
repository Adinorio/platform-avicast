from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Creates the default superadmin user if it doesn't exist"

    def handle(self, *args, **options):
        User = get_user_model()

        # Check if default user already exists
        if User.objects.filter(username="010101").exists():
            self.stdout.write(
                self.style.SUCCESS('✅ Default superadmin user "010101" already exists.')
            )
            return

        # Check if any users exist at all
        if User.objects.count() == 0:
            self.stdout.write("🆕 No users found. Creating default superadmin...")

            try:
                # Create the default superadmin user
                user = User.objects.create_user(
                    username="010101",
                    employee_id="010101",
                    email="admin@avicast.local",
                    password="avicast123",
                    role="SUPERADMIN",
                    is_staff=True,
                    is_superuser=True,
                    is_active=True,
                )

                self.stdout.write(
                    self.style.SUCCESS("✅ Default superadmin user created successfully!")
                )
                self.stdout.write(f"   Username: {user.username}")
                self.stdout.write(f"   Employee ID: {user.employee_id}")
                self.stdout.write(f"   Role: {user.role}")
                self.stdout.write("   Password: avicast123")
                self.stdout.write("\n🔑 You can now login with these credentials!")

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Error creating default user: {e}"))
                return False
        else:
            self.stdout.write("ℹ️  Users already exist in the database.")
