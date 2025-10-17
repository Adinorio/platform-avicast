"""
Dashboard views for users app
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .models import DataRequest, User, UserActivity


@login_required
def user_management_dashboard(request):
    """Enhanced user management dashboard for superadmins"""

    # Dashboard statistics
    total_users = User.objects.count()
    active_admins = User.objects.filter(role="ADMIN", account_status="ACTIVE").count()
    active_field_workers = User.objects.filter(role="FIELD_WORKER", account_status="ACTIVE").count()

    # Recent activities (last 5)
    recent_activities = UserActivity.objects.select_related("user").order_by("-timestamp")[:5]

    # Recent users
    recent_users = User.objects.order_by("-date_joined")[:5]

    # Pending requests
    pending_requests = DataRequest.objects.filter(status="PENDING").count()

    context = {
        "total_users": total_users,
        "active_admins": active_admins,
        "active_field_workers": active_field_workers,
        "recent_activities": recent_activities,
        "recent_users": recent_users,
        "pending_requests": pending_requests,
    }

    return render(request, "users/user_management_dashboard.html", context)


@login_required
def user_management_list(request):
    """Enhanced user list with filtering and search"""
    from django.core.paginator import Paginator
    from django.db.models import Q

    # Get filter parameters
    search_query = request.GET.get("search", "")
    role_filter = request.GET.get("role", "")
    status_filter = request.GET.get("status", "")
    archived_filter = request.GET.get("archived", "false").lower() == "true"

    # Build queryset
    users = User.objects.all()

    if search_query:
        users = users.filter(
            Q(employee_id__icontains=search_query)
            | Q(first_name__icontains=search_query)
            | Q(last_name__icontains=search_query)
        )

    if role_filter:
        users = users.filter(role=role_filter)

    if status_filter:
        users = users.filter(account_status=status_filter)

    if not archived_filter:
        users = users.filter(is_archived=False)

    # Pagination
    paginator = Paginator(users.order_by("-date_joined"), 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "search_query": search_query,
        "role_filter": role_filter,
        "status_filter": status_filter,
        "archived_filter": archived_filter,
    }

    return render(request, "users/user_management_list.html", context)
