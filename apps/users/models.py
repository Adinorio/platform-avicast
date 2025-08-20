from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

# Create your models here.

class CustomUserManager(BaseUserManager):
    def create_user(self, employee_id, password=None, **extra_fields):
        if not employee_id:
            raise ValueError('The Employee ID must be set')
        user = self.model(employee_id=employee_id, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, employee_id, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(employee_id, password, **extra_fields)

class User(AbstractUser):
    class Role(models.TextChoices):
        SUPERADMIN = 'SUPERADMIN', 'Superadmin'
        ADMIN = 'ADMIN', 'Admin'
        FIELD_WORKER = 'FIELD_WORKER', 'Field Worker'

    base_role = Role.SUPERADMIN

    # Override username to use employee_id instead
    employee_id = models.CharField(max_length=50, unique=True, verbose_name="Employee ID", null=True, blank=True)
    role = models.CharField(max_length=50, choices=Role.choices)
    
    # Make username field not required since we're using employee_id
    username = models.CharField(max_length=150, blank=True, null=True)
    
    # Make email optional as per blueprint
    email = models.EmailField(blank=True, null=True)
    
    # Use employee_id as the username field for authentication
    USERNAME_FIELD = 'employee_id'
    REQUIRED_FIELDS = ['first_name', 'last_name']  # Removed email
    
    # Use our custom manager
    objects = CustomUserManager()

    def save(self, *args, **kwargs):
        if not self.pk and not self.role:
            # Only set default role if it's a new user AND no role is specified
            self.role = self.base_role
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee_id} - {self.get_full_name()}"
