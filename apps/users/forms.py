from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User, DataRequest

class UserCreationForm(forms.ModelForm):
    """Form for creating new users"""
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text="Minimum 8 characters"
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Confirm Password"
    )

    class Meta:
        model = User
        fields = ('employee_id', 'first_name', 'last_name', 'role', 'email')
        widgets = {
            'employee_id': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("Passwords do not match")

        if password and len(password) < 8:
            raise forms.ValidationError("Password must be at least 8 characters long")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user

class UserUpdateForm(forms.ModelForm):
    """Form for updating existing users"""

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'role', 'account_status', 'email')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'account_status': forms.Select(attrs={'class': 'form-select'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class ChangePasswordForm(forms.Form):
    """Form for changing password"""
    current_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Current Password"
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="New Password",
        help_text="Minimum 8 characters"
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Confirm New Password"
    )

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')

        if new_password and confirm_password and new_password != confirm_password:
            raise forms.ValidationError("New passwords do not match")

        if new_password and len(new_password) < 8:
            raise forms.ValidationError("Password must be at least 8 characters long")

        return cleaned_data

class DataRequestForm(forms.ModelForm):
    """Form for field workers to submit data requests"""

    class Meta:
        model = DataRequest
        fields = ('request_type', 'title', 'description', 'priority', 'request_data')
        widgets = {
            'request_type': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'request_data': forms.HiddenInput(),
        }

class DataRequestApprovalForm(forms.Form):
    """Form for admins to approve/reject requests"""
    action = forms.ChoiceField(
        choices=[('approve', 'Approve'), ('reject', 'Reject')],
        widget=forms.RadioSelect
    )
    admin_notes = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Add notes (optional)'}),
        required=False
    )
