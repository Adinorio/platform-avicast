"""
Site management views for locations app
"""

import csv
import io
import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render

from apps.image_processing.permissions import staff_required
from .forms import SiteForm
from .models import Site


@login_required
@staff_required
def site_list(request):
    """Display list of all sites with search and filtering"""
    sites = Site.objects.all()

    # Search functionality
    search_query = request.GET.get("search", "")
    if search_query:
        sites = sites.filter(
            Q(name__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(site_type__icontains=search_query)
        )

    # Filter by site type
    site_type = request.GET.get("site_type", "")
    if site_type:
        sites = sites.filter(site_type=site_type)

    # Filter by status
    status = request.GET.get("status", "")
    if status:
        sites = sites.filter(status=status)

    # Pagination
    paginator = Paginator(sites, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "search_query": search_query,
        "site_type": site_type,
        "status": status,
        "site_types": Site.SITE_TYPES,
        "site_statuses": Site.SITE_STATUS,
    }
    return render(request, "locations/site_list.html", context)


@login_required
@staff_required
def site_detail(request, site_id):
    """Display detailed site information with integrated census data"""
    site = get_object_or_404(Site, id=site_id)

    # Get census summary organized by year and month
    census_summary = site.get_census_summary()

    # Get recent census observations
    recent_census = site.census_observations.order_by("-observation_date")[:10]

    # Get species diversity stats
    total_species_observed = (
        site.census_observations.values("species_observations__species_name")
        .distinct()
        .count()
    )

    total_birds_observed = (
        site.census_observations.values_list("species_observations__count", flat=True)
        .aggregate(total=Sum("species_observations__count"))["total"]
        or 0
    )

    context = {
        "site": site,
        "census_summary": census_summary,
        "recent_census": recent_census,
        "total_species_observed": total_species_observed,
        "total_birds_observed": total_birds_observed,
    }
    return render(request, "locations/site_detail.html", context)


@login_required
@staff_required
def site_create(request):
    """Create a new site"""
    if request.method == "POST":
        form = SiteForm(request.POST)
        if form.is_valid():
            site = form.save(commit=False)
            site.created_by = request.user
            site.save()
            messages.success(request, f'Site "{site.name}" created successfully!')
            return redirect("locations:site_detail", site_id=site.id)
    else:
        form = SiteForm()

    context = {"form": form, "action": "Create"}
    return render(request, "locations/site_form.html", context)


@login_required
@staff_required
def site_update(request, site_id):
    """Update an existing site"""
    site = get_object_or_404(Site, id=site_id)

    if request.method == "POST":
        form = SiteForm(request.POST, instance=site)
        if form.is_valid():
            form.save()
            messages.success(request, f'Site "{site.name}" updated successfully!')
            return redirect("locations:site_detail", site_id=site.id)
    else:
        form = SiteForm(instance=site)

    context = {"form": form, "site": site, "action": "Update"}
    return render(request, "locations/site_form.html", context)


@login_required
@staff_required
def site_delete(request, site_id):
    """Delete a site"""
    site = get_object_or_404(Site, id=site_id)

    if request.method == "POST":
        site_name = site.name
        site.delete()
        messages.success(request, f'Site "{site_name}" deleted successfully!')
        return redirect("locations:site_list")

    context = {"site": site}
    return render(request, "locations/site_confirm_delete.html", context)
