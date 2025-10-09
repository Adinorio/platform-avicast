"""
Data change request views for locations app.
Field workers can submit requests, admins can review and approve/reject.
"""

import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from django.contrib.admin.views.decorators import staff_member_required as staff_required
from .models import DataChangeRequest, Site, CensusObservation, SpeciesObservation
from apps.fauna.models import Species


@login_required
def request_list(request):
    """List all data change requests (filtered by role)"""
    # Admins see all requests, field workers see only their own
    if request.user.role in ['ADMIN', 'SUPERADMIN']:
        requests = DataChangeRequest.objects.all()
    else:
        requests = DataChangeRequest.objects.filter(requested_by=request.user)

    # Calculate statistics
    stats = {
        'total': requests.count(),
        'pending': requests.filter(status='pending').count(),
        'approved': requests.filter(status='approved').count(),
        'rejected': requests.filter(status='rejected').count(),
        'completed': requests.filter(status='completed').count(),
    }

    # Filter by status
    status_filter = request.GET.get("status", "")
    if status_filter:
        requests = requests.filter(status=status_filter)

    # Filter by request type
    type_filter = request.GET.get("type", "")
    if type_filter:
        requests = requests.filter(request_type=type_filter)

    # Filter by site
    site_filter = request.GET.get("site", "")
    if site_filter:
        requests = requests.filter(site_id=site_filter)

    # Order by most recent first
    requests = requests.select_related(
        'site', 'census', 'requested_by', 'reviewed_by'
    ).order_by('-requested_at')

    # Pagination
    paginator = Paginator(requests, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Get all sites for filter
    sites = Site.objects.all().order_by('name')

    context = {
        "page_obj": page_obj,
        "status_filter": status_filter,
        "type_filter": type_filter,
        "site_filter": site_filter,
        "status_choices": DataChangeRequest.REQUEST_STATUS,
        "type_choices": DataChangeRequest.REQUEST_TYPES,
        "stats": stats,
        "sites": sites,
        "is_admin": request.user.role in ['ADMIN', 'SUPERADMIN'],
    }

    return render(request, "locations/request_list.html", context)


@login_required
def submit_request(request):
    """Submit a new data change request"""
    if request.method == "POST":
        try:
            request_type = request.POST.get("request_type")
            site_id = request.POST.get("site_id")
            census_id = request.POST.get("census_id", None)
            reason = request.POST.get("reason", "")

            # Build request_data based on request_type
            request_data = {}

            if request_type == "add_census":
                request_data = {
                    "observation_date": request.POST.get("observation_date"),
                    "weather_conditions": request.POST.get("weather_conditions", ""),
                    "notes": request.POST.get("notes", ""),
                    "species": []  # Will be added separately
                }
                
                # Parse species data from form
                species_count = int(request.POST.get("species_count", 0))
                for i in range(species_count):
                    species_data = {
                        "species_id": request.POST.get(f"species_{i}_id"),
                        "species_name": request.POST.get(f"species_{i}_name"),
                        "count": int(request.POST.get(f"species_{i}_count", 1)),
                        "behavior_notes": request.POST.get(f"species_{i}_notes", ""),
                    }
                    request_data["species"].append(species_data)

            elif request_type == "edit_census":
                request_data = {
                    "observation_date": request.POST.get("observation_date"),
                    "weather_conditions": request.POST.get("weather_conditions", ""),
                    "notes": request.POST.get("notes", ""),
                }

            elif request_type == "add_species":
                request_data = {
                    "species_id": request.POST.get("species_id"),
                    "species_name": request.POST.get("species_name"),
                    "count": int(request.POST.get("count", 1)),
                    "behavior_notes": request.POST.get("behavior_notes", ""),
                }

            elif request_type == "edit_species":
                request_data = {
                    "species_observation_id": request.POST.get("species_observation_id"),
                    "count": int(request.POST.get("count", 1)),
                    "behavior_notes": request.POST.get("behavior_notes", ""),
                }

            elif request_type == "edit_site":
                request_data = {
                    "name": request.POST.get("site_name"),
                    "description": request.POST.get("description", ""),
                    "coordinates": request.POST.get("coordinates", ""),
                }

            # Create the request
            change_request = DataChangeRequest.objects.create(
                request_type=request_type,
                site_id=site_id,
                census_id=census_id if census_id else None,
                request_data=request_data,
                reason=reason,
                requested_by=request.user,
            )

            messages.success(
                request,
                f"Request submitted successfully! Your {change_request.get_request_type_display()} "
                f"request is pending admin review."
            )
            return redirect("locations:request_list")

        except Exception as e:
            messages.error(request, f"Error submitting request: {str(e)}")

    # GET request - show form
    sites = Site.objects.all().order_by('name')
    species_list = Species.objects.all().order_by('name')
    
    # Get census observations for the selected site (via AJAX)
    context = {
        "sites": sites,
        "species_list": species_list,
        "request_types": DataChangeRequest.REQUEST_TYPES,
    }

    return render(request, "locations/submit_request.html", context)


@login_required
@staff_required
def review_request(request, request_id):
    """Review and approve/reject data change request (admin only)"""
    change_request = get_object_or_404(DataChangeRequest, id=request_id)

    # Parse request data for preview
    request_data = change_request.request_data

    if request.method == "POST":
        action = request.POST.get("action")
        notes = request.POST.get("review_notes", "")

        try:
            if action == "approve":
                change_request.approve(request.user, notes)
                messages.success(
                    request,
                    f"{change_request.get_request_type_display()} request approved. "
                    f"Click 'Execute' to apply the changes."
                )
            elif action == "reject":
                change_request.reject(request.user, notes)
                messages.warning(request, "Request rejected.")
            elif action == "execute":
                if change_request.status != "approved":
                    messages.error(request, "Only approved requests can be executed.")
                else:
                    with transaction.atomic():
                        change_request.execute_request()
                    messages.success(
                        request,
                        f"Request executed successfully! {change_request.get_request_type_display()} completed."
                    )
                    # Redirect to site detail if applicable
                    if change_request.site:
                        return redirect("locations:site_detail", site_id=change_request.site.id)

            return redirect("locations:request_list")

        except Exception as e:
            messages.error(request, f"Error processing request: {str(e)}")

    context = {
        "change_request": change_request,
        "request_data_json": json.dumps(request_data, indent=2),
        "is_admin": request.user.role in ['ADMIN', 'SUPERADMIN'],
        "can_edit": change_request.status == 'pending' and request.user.role in ['ADMIN', 'SUPERADMIN'],
    }

    return render(request, "locations/review_request.html", context)


@login_required
@staff_required
def bulk_request_actions(request):
    """Handle bulk actions on requests (admin only)"""
    if request.method == "POST":
        request_ids = request.POST.getlist("request_ids")
        action = request.POST.get("bulk_action")

        requests = DataChangeRequest.objects.filter(id__in=request_ids)
        processed = 0

        for change_request in requests:
            try:
                if action == "approve":
                    change_request.approve(request.user, "Bulk approved")
                    processed += 1
                elif action == "reject":
                    change_request.reject(request.user, "Bulk rejected")
                    processed += 1
            except Exception:
                continue

        messages.success(request, f"{processed} request(s) processed successfully.")

    return redirect("locations:request_list")




