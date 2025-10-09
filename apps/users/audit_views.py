"""
Audit and logging views for users app
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import redirect, render

from .models import UserActivity


@login_required
def system_logs(request):
    """View system activity logs"""

    # Get filter parameters
    activity_filter = request.GET.get("activity_type", "")
    user_filter = request.GET.get("user", "")
    date_filter = request.GET.get("date", "")

    logs = UserActivity.objects.select_related("user").order_by("-timestamp")

    if activity_filter:
        logs = logs.filter(activity_type=activity_filter)

    if user_filter:
        logs = logs.filter(user_id=user_filter)

    if date_filter:
        logs = logs.filter(timestamp__date=date_filter)

    # Pagination
    paginator = Paginator(logs, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "activity_filter": activity_filter,
        "user_filter": user_filter,
        "date_filter": date_filter,
    }

    return render(request, "users/system_logs.html", context)
