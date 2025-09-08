"""
Account management views for users app
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render


@login_required
def change_password(request):
    """Handle password change for current user"""
    if request.method == "POST":
        current_password = request.POST.get("current_password")
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        if not request.user.check_password(current_password):
            messages.error(request, "Current password is incorrect.")
            return redirect("users:change_password")

        if new_password != confirm_password:
            messages.error(request, "New passwords do not match.")
            return redirect("users:change_password")

        if len(new_password) < 8:
            messages.error(request, "Password must be at least 8 characters long.")
            return redirect("users:change_password")

        request.user.set_password(new_password)
        request.user.mark_password_changed()
        request.user.save()

        messages.success(request, "Password changed successfully!")
        return redirect("home")

    return render(request, "users/change_password.html")
