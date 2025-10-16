"""
User Management and Password Reset Forms for AVICAST
Secure user management and password reset workflow for CENRO users
"""

from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import PasswordResetRequest

User = get_user_model()


class UserCreationForm(forms.ModelForm):
    """Form for creating new user accounts"""
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password',
            'autocomplete': 'new-password'
        }),
        label="Password",
        min_length=8,
        help_text="Password must be at least 8 characters long"
    )
    
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password',
            'autocomplete': 'new-password'
        }),
        label="Confirm Password"
    )

    class Meta:
        model = User
        fields = ['employee_id', 'first_name', 'last_name', 'email', 'role', 'account_status']
        widgets = {
            'employee_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '25-0118-001',
                'pattern': r'\d{2}-\d{4}-\d{3}',
                'title': 'Format: YY-MMDD-NNN (e.g., 25-0118-001)'
            }),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'account_status': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee_id'].required = True
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['email'].required = True
        self.fields['role'].required = True

    def clean_employee_id(self):
        employee_id = self.cleaned_data.get('employee_id')
        if not employee_id:
            raise ValidationError("Employee ID is required.")
        
        # Validate format
        import re
        pattern = r'^\d{2}-\d{4}-\d{3}$'
        if not re.match(pattern, employee_id):
            raise ValidationError("Employee ID must be in format YY-MMDD-NNN (e.g., 25-0118-001)")
        
        # Check if employee_id already exists
        if User.objects.filter(employee_id=employee_id).exists():
            raise ValidationError("A user with this Employee ID already exists.")
        
        return employee_id

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise ValidationError("A user with this email already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password:
            if password != confirm_password:
                raise ValidationError("Passwords do not match.")
            
            # Check password strength
            if len(password) < 8:
                raise ValidationError("Password must be at least 8 characters long.")
            
            # Check for common passwords
            common_passwords = ['password', '123456', 'qwerty', 'admin', 'avicast']
            if password.lower() in common_passwords:
                raise ValidationError("Please choose a stronger password.")
        
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class UserUpdateForm(forms.ModelForm):
    """Form for updating existing user accounts"""
    
    class Meta:
        model = User
        fields = ['employee_id', 'first_name', 'last_name', 'email', 'role', 'account_status']
        widgets = {
            'employee_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '25-0118-001',
                'pattern': r'\d{2}-\d{4}-\d{3}',
                'title': 'Format: YY-MMDD-NNN (e.g., 25-0118-001)'
            }),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'account_status': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee_id'].required = True
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['email'].required = True
        self.fields['role'].required = True

    def clean_employee_id(self):
        employee_id = self.cleaned_data.get('employee_id')
        if not employee_id:
            raise ValidationError("Employee ID is required.")
        
        # Validate format
        import re
        pattern = r'^\d{2}-\d{4}-\d{3}$'
        if not re.match(pattern, employee_id):
            raise ValidationError("Employee ID must be in format YY-MMDD-NNN (e.g., 25-0118-001)")
        
        # Check if employee_id already exists (excluding current user)
        if User.objects.filter(employee_id=employee_id).exclude(id=self.instance.id).exists():
            raise ValidationError("A user with this Employee ID already exists.")
        
        return employee_id

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exclude(id=self.instance.id).exists():
            raise ValidationError("A user with this email already exists.")
        return email


class PasswordResetRequestForm(forms.ModelForm):
    """Form for requesting a password reset"""
    
    employee_id = forms.CharField(
        max_length=50,
        label="Employee ID",
        help_text="Enter your Employee ID (e.g., 25-0118-001)",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '25-0118-001',
            'autocomplete': 'username'
        })
    )
    
    reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Please explain why you need a password reset...'
        }),
        label="Reason for Reset",
        help_text="Please provide a brief explanation for your password reset request"
    )

    class Meta:
        model = PasswordResetRequest
        fields = ['reason']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee_id'].required = True

    def clean_employee_id(self):
        employee_id = self.cleaned_data.get('employee_id')
        if not employee_id:
            raise ValidationError("Employee ID is required.")
        
        # Validate format
        import re
        pattern = r'^\d{2}-\d{4}-\d{3}$'
        if not re.match(pattern, employee_id):
            raise ValidationError("Employee ID must be in format YY-MMDD-NNN (e.g., 25-0118-001)")
        
        # Check if user exists
        try:
            user = User.objects.get(employee_id=employee_id)
            if not user.is_account_active():
                raise ValidationError("Your account is not active. Please contact your administrator.")
        except User.DoesNotExist:
            raise ValidationError("No account found with this Employee ID.")
        
        return employee_id

    def clean(self):
        cleaned_data = super().clean()
        employee_id = cleaned_data.get('employee_id')
        
        if employee_id:
            # Check for recent reset requests
            recent_requests = PasswordResetRequest.objects.filter(
                user__employee_id=employee_id,
                requested_at__gte=timezone.now() - timezone.timedelta(hours=1),
                status__in=[PasswordResetRequest.Status.PENDING, PasswordResetRequest.Status.APPROVED]
            )
            
            if recent_requests.exists():
                raise ValidationError("You have a pending password reset request. Please wait before submitting another request.")
        
        return cleaned_data

    def save(self, request=None):
        """Save the password reset request"""
        employee_id = self.cleaned_data['employee_id']
        user = User.objects.get(employee_id=employee_id)
        
        reset_request = super().save(commit=False)
        reset_request.user = user
        reset_request.requested_by_ip = self.get_client_ip(request) if request else ""
        reset_request.save()
        
        return reset_request

    def get_client_ip(self, request):
        """Get client IP address"""
        if request:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR')
            return ip
        return ""


class PasswordResetVerificationForm(forms.Form):
    """Form for verifying identity before password reset"""
    
    def __init__(self, reset_request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reset_request = reset_request
        
        # Add verification question fields
        questions = reset_request.get_verification_questions()
        for i, question in enumerate(questions):
            self.fields[f'answer_{i}'] = forms.CharField(
                label=question,
                widget=forms.TextInput(attrs={
                    'class': 'form-control',
                    'placeholder': f'Answer to: {question}'
                }),
                required=True
            )

    def clean(self):
        cleaned_data = super().clean()
        
        # Collect answers
        answers = []
        for key, value in cleaned_data.items():
            if key.startswith('answer_'):
                answers.append(value)
        
        # Verify answers
        if not self.reset_request.verify_answers(answers):
            raise ValidationError("Verification failed. Please check your answers and try again.")
        
        return cleaned_data


class PasswordResetApprovalForm(forms.ModelForm):
    """Form for admin approval of password reset requests"""
    
    approval_notes = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Add any notes about this approval...'
        }),
        label="Approval Notes",
        required=False,
        help_text="Optional notes about this approval decision"
    )

    class Meta:
        model = PasswordResetRequest
        fields = ['approval_notes']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add action choice
        self.fields['action'] = forms.ChoiceField(
            choices=[
                ('approve', 'Approve Request'),
                ('reject', 'Reject Request'),
            ],
            widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
            label="Action",
            required=True
        )


class NewPasswordForm(forms.Form):
    """Form for setting new password after reset approval"""
    
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new password',
            'autocomplete': 'new-password'
        }),
        label="New Password",
        min_length=8,
        help_text="Password must be at least 8 characters long"
    )
    
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new password',
            'autocomplete': 'new-password'
        }),
        label="Confirm Password"
    )

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if new_password and confirm_password:
            if new_password != confirm_password:
                raise ValidationError("Passwords do not match.")
            
            # Check password strength
            if len(new_password) < 8:
                raise ValidationError("Password must be at least 8 characters long.")
            
            # Check for common passwords
            common_passwords = ['password', '123456', 'qwerty', 'admin', 'avicast']
            if new_password.lower() in common_passwords:
                raise ValidationError("Please choose a stronger password.")
        
        return cleaned_data