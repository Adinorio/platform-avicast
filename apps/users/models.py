from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
import re
import uuid

# Create your models here.


class CustomUserManager(BaseUserManager):
    def create_user(self, employee_id=None, password=None, **extra_fields):
        # Auto-generate employee_id if not provided
        if not employee_id:
            employee_id = self.generate_employee_id()
        
        user = self.model(employee_id=employee_id, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def generate_employee_id(self):
        """Generate employee ID in format: YY-MMDD-NNN"""
        from datetime import date
        
        today = date.today()
        year = str(today.year)[-2:]  # Last 2 digits of year
        month_day = today.strftime("%m%d")  # MMDD format
        
        # Find the next sequential number for today
        prefix = f"{year}-{month_day}-"
        existing_ids = self.filter(employee_id__startswith=prefix).values_list('employee_id', flat=True)
        
        if existing_ids:
            # Extract numbers and find the highest
            numbers = []
            for emp_id in existing_ids:
                try:
                    num_part = emp_id.split('-')[-1]
                    numbers.append(int(num_part))
                except (ValueError, IndexError):
                    continue
            
            next_num = max(numbers) + 1 if numbers else 1
        else:
            next_num = 1
        
        # Format with zero padding
        return f"{prefix}{next_num:03d}"

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
        max_length=50, unique=True, verbose_name="Employee ID", null=True, blank=True,
        help_text="Format: YY-MMDD-NNN (e.g., 25-0118-001)"
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
        # Generate employee_id if not set (for new users)
        if not self.pk and not self.employee_id:
            self.employee_id = self.objects.generate_employee_id()
        
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
    
    def clean(self):
        """Validate employee_id format"""
        super().clean()
        if self.employee_id:
            # Validate format: YY-MMDD-NNN
            pattern = r'^\d{2}-\d{4}-\d{3}$'
            if not re.match(pattern, self.employee_id):
                raise ValidationError({
                    'employee_id': 'Employee ID must be in format YY-MMDD-NNN (e.g., 25-0118-001)'
                })

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
        # Authentication activities
        LOGIN = "LOGIN", "Login"
        LOGOUT = "LOGOUT", "Logout"
        PASSWORD_CHANGE = "PASSWORD_CHANGE", "Password Change"
        
        # User management activities
        USER_CREATED = "USER_CREATED", "User Created"
        USER_UPDATED = "USER_UPDATED", "User Updated"
        USER_ARCHIVED = "USER_ARCHIVED", "User Archived"
        USER_DISABLED = "USER_DISABLED", "User Disabled"
        
        # Species management activities
        SPECIES_ADDED = "SPECIES_ADDED", "Species Added"
        SPECIES_UPDATED = "SPECIES_UPDATED", "Species Updated"
        SPECIES_ARCHIVED = "SPECIES_ARCHIVED", "Species Archived"
        
        # Site management activities
        SITE_ADDED = "SITE_ADDED", "Site Added"
        SITE_UPDATED = "SITE_UPDATED", "Site Updated"
        
        # Census activities
        CENSUS_ADDED = "CENSUS_ADDED", "Census Added"
        CENSUS_UPDATED = "CENSUS_UPDATED", "Census Updated"
        
        # Image processing activities
        IMAGE_PROCESSED = "IMAGE_PROCESSED", "Image Processed"
        
        # Reporting and data activities
        REPORT_GENERATED = "REPORT_GENERATED", "Report Generated"
        DATA_IMPORTED = "DATA_IMPORTED", "Data Imported"
        DATA_EXPORTED = "DATA_EXPORTED", "Data Exported"
        
        # System activities (from middleware)
        ADMIN_ACTION = "ADMIN_ACTION", "Admin Action"
        USER_ACTION = "USER_ACTION", "User Action"
        CLIENT_ERROR = "CLIENT_ERROR", "Client Error"
        SYSTEM_ERROR = "SYSTEM_ERROR", "System Error"
        API_ACCESS = "API_ACCESS", "API Access"
        PAGE_VIEW = "PAGE_VIEW", "Page View"

    class Severity(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"
        CRITICAL = "CRITICAL", "Critical"
        INFO = "INFO", "Information"
        WARNING = "WARNING", "Warning"
        ERROR = "ERROR", "Error"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="activities")
    activity_type = models.CharField(max_length=50, choices=ActivityType.choices)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    severity = models.CharField(max_length=20, choices=Severity.choices, default=Severity.MEDIUM)
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
    # related_site = models.ForeignKey(  # Temporarily disabled during locations revamp
    #     "locations.Site", on_delete=models.SET_NULL, null=True, blank=True
    # )

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


class PasswordResetRequest(models.Model):
    """Model for handling password reset requests"""
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending Approval"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        COMPLETED = "COMPLETED", "Completed"
        EXPIRED = "EXPIRED", "Expired"

    class RequestType(models.TextChoices):
        FORGOTTEN = "FORGOTTEN", "Forgotten Password"
        ADMIN_RESET = "ADMIN_RESET", "Admin Reset"
        SECURITY_RESET = "SECURITY_RESET", "Security Reset"

    # Request details
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name="password_reset_requests")
    request_type = models.CharField(max_length=20, choices=RequestType.choices, default=RequestType.FORGOTTEN)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    
    # Request information
    requested_at = models.DateTimeField(auto_now_add=True)
    requested_by_ip = models.CharField(max_length=45, blank=True)
    reason = models.TextField(blank=True, help_text="Reason for password reset request")
    
    # Approval information
    approved_by = models.ForeignKey(
        'User', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="approved_password_resets"
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    approval_notes = models.TextField(blank=True)
    
    # Reset information
    reset_token = models.CharField(max_length=100, blank=True, unique=True)
    reset_token_expires = models.DateTimeField(null=True, blank=True)
    reset_completed_at = models.DateTimeField(null=True, blank=True)
    
    # Security information
    verification_questions = models.JSONField(default=list, blank=True)
    verification_answers = models.JSONField(default=list, blank=True)
    
    class Meta:
        ordering = ['-requested_at']
        verbose_name = "Password Reset Request"
        verbose_name_plural = "Password Reset Requests"

    def __str__(self):
        return f"Password Reset Request - {self.user.employee_id} ({self.status})"

    def is_expired(self):
        """Check if the reset request has expired"""
        if self.reset_token_expires:
            return timezone.now() > self.reset_token_expires
        return False

    def can_be_approved(self):
        """Check if the request can be approved"""
        return self.status == self.Status.PENDING and not self.is_expired()

    def generate_reset_token(self):
        """Generate a secure reset token"""
        import secrets
        self.reset_token = secrets.token_urlsafe(32)
        self.reset_token_expires = timezone.now() + timezone.timedelta(hours=24)
        self.save()

    def approve(self, approved_by, notes=""):
        """Approve the password reset request"""
        if not self.can_be_approved():
            return False
        
        self.status = self.Status.APPROVED
        self.approved_by = approved_by
        self.approved_at = timezone.now()
        self.approval_notes = notes
        self.generate_reset_token()
        self.save()
        return True

    def reject(self, approved_by, notes=""):
        """Reject the password reset request"""
        self.status = self.Status.REJECTED
        self.approved_by = approved_by
        self.approved_at = timezone.now()
        self.approval_notes = notes
        self.save()

    def complete_reset(self):
        """Mark the reset as completed"""
        self.status = self.Status.COMPLETED
        self.reset_completed_at = timezone.now()
        self.save()

    def get_verification_questions(self):
        """Get verification questions for the user"""
        questions = [
            "What is your Employee ID?",
            "What is your full name?",
            "What is your role in the organization?",
            "When was your account created? (approximate date)",
        ]
        return questions[:2]  # Use first 2 questions for security

    def verify_answers(self, answers):
        """Verify the provided answers"""
        if len(answers) != 2:
            return False
        
        # Check Employee ID
        if answers[0].strip().upper() != self.user.employee_id:
            return False
        
        # Check full name (case insensitive)
        if answers[1].strip().lower() != self.user.get_full_name().lower():
            return False
        
        return True
