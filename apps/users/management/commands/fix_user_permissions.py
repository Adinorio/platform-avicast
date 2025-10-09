from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = "Fix Django permissions for existing users based on their roles"

    def handle(self, *args, **options):
        self.stdout.write("Fixing user permissions based on roles...")

        # Get all users
        users = User.objects.all()
        total_users = users.count()
        fixed_users = 0

        for user in users:
            original_staff = user.is_staff
            original_superuser = user.is_superuser

            # Set permissions based on role
            if user.role == User.Role.SUPERADMIN:
                user.is_staff = True
                user.is_superuser = True
            elif user.role == User.Role.ADMIN:
                user.is_staff = True
                user.is_superuser = False
            elif user.role == User.Role.FIELD_WORKER:
                user.is_staff = False
                user.is_superuser = False

            # Save if permissions changed
            if user.is_staff != original_staff or user.is_superuser != original_superuser:
                user.save(update_fields=['is_staff', 'is_superuser'])
                fixed_users += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Fixed {user.employee_id} ({user.role}): "
                        f"staff={user.is_staff}, superuser={user.is_superuser}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Fixed permissions for {fixed_users}/{total_users} users"
            )
        )
