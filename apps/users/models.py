from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone

# Create your models here.


class CustomUserManager(BaseUserManager):
    def create_user(self, employee_id, password=None, **extra_fields):
        if not employee_id:
            raise ValueError("The Employee ID must be set")
        user = self.model(employee_id=employee_id, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, employee_id, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(employee_id, password, **extra_fields)


class User(AbstractUser):
    class Role(models.TextChoices):
        SUPERADMIN = "SUPERADMIN", "Superadmin"
        ADMIN = "ADMIN", "Admin"
        FIELD_WORKER = "FIELD_WORKER", "Field Worker"

    class AccountStatus(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        DISABLED = "DISABLED", "Disabled"
        ARCHIVED = "ARCHIVED", "Archived"

    base_role = Role.SUPERADMIN

    # Override username to use employee_id instead
    employee_id = models.CharField(
        max_length=50, unique=True, verbose_name="Employee ID", null=True, blank=True
    )
    role = models.CharField(max_length=50, choices=Role.choices)
    account_status = models.CharField(
        max_length=20, choices=AccountStatus.choices, default=AccountStatus.ACTIVE
    )

    # Password management
    password_changed = models.BooleanField(default=False)
    password_changed_date = models.DateTimeField(null=True, blank=True)
    password_change_required = models.BooleanField(default=False)

    # Account management
    is_archived = models.BooleanField(default=False)
    archived_date = models.DateTimeField(null=True, blank=True)
    archived_by = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="archived_users"
    )

    # Activity tracking
    last_activity = models.DateTimeField(null=True, blank=True)
    login_count = models.IntegerField(default=0)

    # Make username field not required since we're using employee_id
    username = models.CharField(max_length=150, blank=True, null=True)

    # Make email optional as per blueprint
    email = models.EmailField(blank=True, null=True)

    # Use employee_id as the username field for authentication
    USERNAME_FIELD = "employee_id"
    REQUIRED_FIELDS = ["first_name", "last_name"]  # Removed email

    # Use our custom manager
    objects = CustomUserManager()

    def save(self, *args, **kwargs):
        if not self.pk and not self.role:
            # Only set default role if it's a new user AND no role is specified
            self.role = self.base_role

        # Set Django permissions based on role
        if self.role == self.Role.SUPERADMIN:
            self.is_staff = True
            self.is_superuser = True
        elif self.role == self.Role.ADMIN:
            self.is_staff = True
            self.is_superuser = False
        elif self.role == self.Role.FIELD_WORKER:
            self.is_staff = False
            self.is_superuser = False

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee_id} - {self.get_full_name()}"

    def get_role_display(self):
        return dict(self.Role.choices)[self.role]

    def get_status_display(self):
        return dict(self.AccountStatus.choices)[self.account_status]

    def is_account_active(self):
        return self.account_status == self.AccountStatus.ACTIVE and not self.is_archived

    def can_access_feature(self, feature_name):
        """Check if user can access specific features based on role"""
        if self.role == self.Role.SUPERADMIN:
            # Superadmin has access to everything
            return True
        elif self.role == self.Role.ADMIN:
            # Admin has access to everything EXCEPT superadmin user management
            if feature_name == "superadmin_user_management":
                return False
            return True
        elif self.role == self.Role.FIELD_WORKER:
            # Field workers have limited view access
            return feature_name in [
                "species_view",
                "site_view",
                "census_view",
                "image_processing_view",
            ]
        return False

    def can_manage_user(self, target_user):
        """Check if user can manage another user based on roles"""
        if self.role == self.Role.SUPERADMIN:
            # Superadmin can manage everyone
            return True
        elif self.role == self.Role.ADMIN:
            # Admin can manage everyone EXCEPT superadmins
            return target_user.role != self.Role.SUPERADMIN
        elif self.role == self.Role.FIELD_WORKER:
            # Field workers cannot manage users
            return False
        return False

    def update_activity(self):
        """Update user's last activity timestamp"""
        self.last_activity = timezone.now()
        self.save(update_fields=["last_activity"])

    def increment_login_count(self):
        """Increment user's login count"""
        self.login_count += 1
        self.save(update_fields=["login_count"])

    def mark_password_changed(self):
        """Mark that user has changed their password"""
        self.password_changed = True
        self.password_changed_date = timezone.now()
        self.password_change_required = False
        self.save(
            update_fields=["password_changed", "password_changed_date", "password_change_required"]
        )

    def archive_account(self, archived_by_user):
        """Archive the user account"""
        self.is_archived = True
        self.archived_date = timezone.now()
        self.archived_by = archived_by_user
        self.account_status = self.AccountStatus.ARCHIVED
        self.save(update_fields=["is_archived", "archived_date", "archived_by", "account_status"])

    def disable_account(self, disabled_by_user):
        """Disable the user account"""
        self.account_status = self.AccountStatus.DISABLED
        self.save(update_fields=["account_status"])

    def activate_account(self):
        """Activate the user account"""
        self.account_status = self.AccountStatus.ACTIVE
        self.save(update_fields=["account_status"])


class UserActivity(models.Model):
    """Model to track user activities and system logs"""

    class ActivityType(models.TextChoices):
        LOGIN = "LOGIN", "Login"
        LOGOUT = "LOGOUT", "Logout"
        PASSWORD_CHANGE = "PASSWORD_CHANGE", "Password Change"
        USER_CREATED = "USER_CREATED", "User Created"
        USER_UPDATED = "USER_UPDATED", "User Updated"
        USER_ARCHIVED = "USER_ARCHIVED", "User Archived"
        USER_DISABLED = "USER_DISABLED", "User Disabled"
        SPECIES_ADDED = "SPECIES_ADDED", "Species Added"
        SPECIES_UPDATED = "SPECIES_UPDATED", "Species Updated"
        SPECIES_ARCHIVED = "SPECIES_ARCHIVED", "Species Archived"
        SITE_ADDED = "SITE_ADDED", "Site Added"
        SITE_UPDATED = "SITE_UPDATED", "Site Updated"
        CENSUS_ADDED = "CENSUS_ADDED", "Census Added"
        CENSUS_UPDATED = "CENSUS_UPDATED", "Census Updated"
        IMAGE_PROCESSED = "IMAGE_PROCESSED", "Image Processed"
        REPORT_GENERATED = "REPORT_GENERATED", "Report Generated"
        DATA_IMPORTED = "DATA_IMPORTED", "Data Imported"
        DATA_EXPORTED = "DATA_EXPORTED", "Data Exported"

    class Severity(models.TextChoices):
        INFO = "INFO", "Information"
        WARNING = "WARNING", "Warning"
        ERROR = "ERROR", "Error"
        CRITICAL = "CRITICAL", "Critical"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="activities")
    activity_type = models.CharField(max_length=50, choices=ActivityType.choices)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    severity = models.CharField(max_length=20, choices=Severity.choices, default=Severity.INFO)
    metadata = models.JSONField(default=dict, blank=True)  # Store additional data
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]
        verbose_name = "User Activity"
        verbose_name_plural = "User Activities"
        indexes = [
            models.Index(fields=["user", "activity_type", "timestamp"]),
            models.Index(fields=["activity_type", "timestamp"]),
            models.Index(fields=["severity", "timestamp"]),
        ]

    def __str__(self):
        return f"{self.user.employee_id} - {self.activity_type} - {self.timestamp}"

    @classmethod
    def log_activity(
        cls,
        user,
        activity_type,
        description,
        ip_address=None,
        user_agent=None,
        severity=Severity.INFO,
        metadata=None,
    ):
        """Helper method to log user activities"""
        return cls.objects.create(
            user=user,
            activity_type=activity_type,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            severity=severity,
            metadata=metadata or {},
        )


class DataRequest(models.Model):
    """Model to handle field worker requests for data modifications"""

    class RequestType(models.TextChoices):
        SPECIES_ADD = "SPECIES_ADD", "Add Species"
        SPECIES_UPDATE = "SPECIES_UPDATE", "Update Species"
        SITE_ADD = "SITE_ADD", "Add Site"
        SITE_UPDATE = "SITE_UPDATE", "Update Site"
        CENSUS_ADD = "CENSUS_ADD", "Add Census"
        CENSUS_UPDATE = "CENSUS_UPDATE", "Update Census"
        DATA_IMPORT = "DATA_IMPORT", "Import Data"
        REPORT_REQUEST = "REPORT_REQUEST", "Report Request"

    class RequestStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        CANCELLED = "CANCELLED", "Cancelled"

    class Priority(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"
        URGENT = "URGENT", "Urgent"

    # Request details
    request_type = models.CharField(max_length=50, choices=RequestType.choices)
    title = models.CharField(max_length=200)
    description = models.TextField()
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.MEDIUM)
    status = models.CharField(
        max_length=20, choices=RequestStatus.choices, default=RequestStatus.PENDING
    )

    # Requestor and approver
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="requests_made")
    approved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="requests_approved"
    )

    # Timestamps
    requested_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    # Request data (JSON field for flexibility)
    request_data = models.JSONField(
        default=dict, blank=True
    )  # Store the actual data being requested
    admin_notes = models.TextField(blank=True)  # Admin's notes on approval/rejection
    field_worker_notes = models.TextField(blank=True)  # Field worker's additional notes

    # Related objects (optional, for tracking what the request affects)
    related_species = models.ForeignKey(
        "fauna.Species", on_delete=models.SET_NULL, null=True, blank=True
    )
    related_site = models.ForeignKey(
        "locations.Site", on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ["-requested_at"]
        verbose_name = "Data Request"
        verbose_name_plural = "Data Requests"
        indexes = [
            models.Index(fields=["requested_by", "status", "requested_at"]),
            models.Index(fields=["status", "priority", "requested_at"]),
            models.Index(fields=["request_type", "status"]),
        ]

    def __str__(self):
        return f"{self.title} - {self.requested_by.employee_id} - {self.status}"

    def approve(self, approved_by_user, admin_notes=""):
        """Approve the request"""
        self.status = self.RequestStatus.APPROVED
        self.approved_by = approved_by_user
        self.approved_at = timezone.now()
        self.admin_notes = admin_notes
        self.save(update_fields=["status", "approved_by", "approved_at", "admin_notes"])

        # Log the approval activity
        UserActivity.log_activity(
            user=approved_by_user,
            activity_type=UserActivity.ActivityType.USER_UPDATED,
            description=f"Approved request: {self.title}",
            metadata={"request_id": self.id, "request_type": self.request_type},
        )

    def reject(self, approved_by_user, admin_notes=""):
        """Reject the request"""
        self.status = self.RequestStatus.REJECTED
        self.approved_by = approved_by_user
        self.approved_at = timezone.now()
        self.admin_notes = admin_notes
        self.save(update_fields=["status", "approved_by", "approved_at", "admin_notes"])

        # Log the rejection activity
        UserActivity.log_activity(
            user=approved_by_user,
            activity_type=UserActivity.ActivityType.USER_UPDATED,
            description=f"Rejected request: {self.title}",
            metadata={"request_id": self.id, "request_type": self.request_type},
        )

    def cancel(self):
        """Cancel the request (by the requestor)"""
        self.status = self.RequestStatus.CANCELLED
        self.save(update_fields=["status"])

        # Log the cancellation activity
        UserActivity.log_activity(
            user=self.requested_by,
            activity_type=UserActivity.ActivityType.USER_UPDATED,
            description=f"Cancelled request: {self.title}",
            metadata={"request_id": self.id, "request_type": self.request_type},
        )

    @property
    def is_pending(self):
        return self.status == self.RequestStatus.PENDING

    @property
    def is_approved(self):
        return self.status == self.RequestStatus.APPROVED

    @property
    def is_rejected(self):
        return self.status == self.RequestStatus.REJECTED

    @property
    def can_be_approved(self):
        return self.status == self.RequestStatus.PENDING

    @property
    def can_be_cancelled(self):
        return self.status == self.RequestStatus.PENDING
