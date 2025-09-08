"""
User management views for users app
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.image_processing.permissions import superadmin_required
from .forms import UserCreationForm, UserUpdateForm
from .models import User


@login_required
@superadmin_required
def create_user(request):
    """Create new user account"""

    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"User {user.employee_id} created successfully!")
            return redirect("users:user_management_list")
    else:
        form = UserCreationForm()

    return render(request, "users/create_user.html", {"form": form})


@login_required
@superadmin_required
def update_user(request, user_id):
    """Update existing user account"""

    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        form = UserUpdateForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f"User {user.employee_id} updated successfully!")
            return redirect("users:user_management_list")
    else:
        form = UserUpdateForm(instance=user)

    return render(request, "users/update_user.html", {"form": form, "user": user})
