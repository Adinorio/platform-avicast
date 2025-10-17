"""
Views for locations app
Following the card-based user flow: Site -> Year -> Month -> Census Table
"""

import json
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction, models
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods

from .forms import SiteForm, CensusYearForm, CensusMonthForm, CensusForm, CensusObservationForm, BatchObservationForm
from .models import Site, CensusYear, CensusMonth, Census, CensusObservation
from apps.common.permissions import permission_required


@login_required
@permission_required('can_add_sites')
def site_dashboard(request):
    """Main dashboard showing all sites as cards"""
    # Get view type parameter (card or list)
    view_type = request.GET.get('view', 'card')  # Default: card view
    
    # Get sorting parameter
    sort_by = request.GET.get('sort', 'name')  # Default: name
    
    # Validate view type parameter
    valid_views = ['card', 'list']
    if view_type not in valid_views:
        view_type = 'card'
    
    # Validate sort parameter
    valid_sorts = {
        'name': 'name',
        '-name': '-name',
        'site_type': 'site_type',
        '-site_type': '-site_type',
        'status': 'status',
        '-status': '-status',
        'created_at': 'created_at',
        '-created_at': '-created_at',
    }
    
    sort_field = valid_sorts.get(sort_by, 'name')
    sites = Site.objects.filter(status="active").order_by(sort_field)

    # Calculate statistics
    from apps.locations.models import CensusYear, CensusObservation
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    total_sites = sites.count()
    sites_with_coordinates = sites.exclude(coordinates__isnull=True).exclude(coordinates="").count()
    active_years = CensusYear.objects.filter(site__status="active").distinct().count()
    total_observations = CensusObservation.objects.filter(census__month__year__site__status="active").count()
    field_personnel = User.objects.filter(
        models.Q(lead_census__isnull=False) | 
        models.Q(census_team__isnull=False)
    ).distinct().count()

    context = {
        "sites": sites,
        "total_sites": total_sites,
        "sites_with_coordinates": sites_with_coordinates,
        "active_years": active_years,
        "total_observations": total_observations,
        "field_personnel": field_personnel,
        "current_view": view_type,
        "current_sort": sort_by,
    }
    return render(request, "locations/site_dashboard.html", context)




@login_required
@permission_required('can_add_sites')
def site_create(request):
    """Create a new site"""
    if request.method == "POST":
        form = SiteForm(request.POST, request.FILES)
        if form.is_valid():
            site = form.save(commit=False)
            site.created_by = request.user
            site.save()
            messages.success(request, f"Site '{site.name}' created successfully!")
            return redirect("locations:site_detail", site_id=site.id)
    else:
        form = SiteForm()

    context = {
        "form": form,
        "title": "Create New Site",
    }
    return render(request, "locations/site_form.html", context)


@login_required
def site_map(request, site_id):
    """View site location on map with census data overlay"""
    site = get_object_or_404(Site, id=site_id)
    
    # Get census years for this site
    census_years = site.get_years_with_census()
    
    context = {
        "site": site,
        "census_years": census_years,
    }
    return render(request, "locations/site_map.html", context)


@login_required
def site_detail(request, site_id):
    """View site details and its census years"""
    site = get_object_or_404(Site, id=site_id)
    
    # Get view type parameter (card or list)
    view_type = request.GET.get('view', 'card')  # Default: card view
    
    # Get sorting parameter
    sort_by = request.GET.get('sort', '-year')  # Default: newest first
    
    # Validate view type parameter
    valid_views = ['card', 'list']
    if view_type not in valid_views:
        view_type = 'card'
    
    # Validate sort parameter
    valid_sorts = {
        'year': 'year',
        '-year': '-year',
        'total_census_count': 'total_census_count',
        '-total_census_count': '-total_census_count',
        'total_birds_recorded': 'total_birds_recorded',
        '-total_birds_recorded': '-total_birds_recorded',
        'total_species_recorded': 'total_species_recorded',
        '-total_species_recorded': '-total_species_recorded',
        'created_at': 'created_at',
        '-created_at': '-created_at',
    }
    
    sort_field = valid_sorts.get(sort_by, '-year')
    years = site.get_years_with_census().order_by(sort_field)

    context = {
        "site": site,
        "years": years,
        "total_years": years.count(),
        "current_view": view_type,
        "current_sort": sort_by,
    }
    return render(request, "locations/site_detail.html", context)


@login_required
@permission_required('can_add_sites')
def site_edit(request, site_id):
    """Edit an existing site"""
    site = get_object_or_404(Site, id=site_id)

    if request.method == "POST":
        form = SiteForm(request.POST, request.FILES, instance=site)
        if form.is_valid():
            form.save()
            messages.success(request, f"Site '{site.name}' updated successfully!")
            return redirect("locations:site_detail", site_id=site.id)
    else:
        form = SiteForm(instance=site)

    context = {
        "form": form,
        "site": site,
        "title": f"Edit Site: {site.name}",
    }
    return render(request, "locations/site_form.html", context)


@login_required
def site_delete(request, site_id):
    """Delete a site"""
    site = get_object_or_404(Site, id=site_id)

    if request.method == "POST":
        site_name = site.name
        site.delete()
        messages.success(request, f"Site '{site_name}' deleted successfully!")
        return redirect("locations:dashboard")

    context = {
        "site": site,
        "title": f"Delete Site: {site.name}",
    }
    return render(request, "locations/site_confirm_delete.html", context)


@login_required
def site_archive(request, site_id):
    """Archive a site"""
    site = get_object_or_404(Site, id=site_id)
    
    if request.method == "POST":
        site.archive(user=request.user)
        messages.success(request, f"Site '{site.name}' archived successfully!")
        return redirect("locations:dashboard")
    
    context = {
        "site": site,
        "title": f"Archive Site: {site.name}",
    }
    return render(request, "locations/site_confirm_archive.html", context)


@login_required
def site_restore(request, site_id):
    """Restore an archived site"""
    site = get_object_or_404(Site, id=site_id)
    
    if request.method == "POST":
        site.restore()
        messages.success(request, f"Site '{site.name}' restored successfully!")
        return redirect("locations:dashboard")
    
    # If GET request, redirect to dashboard
    return redirect("locations:dashboard")


@login_required
def site_archived_list(request):
    """Display list of archived sites"""
    # Get view type parameter (card or list)
    view_type = request.GET.get('view', 'card')  # Default: card view
    
    # Get sorting parameter
    sort_by = request.GET.get('sort', 'name')  # Default: name
    
    # Validate view type parameter
    valid_views = ['card', 'list']
    if view_type not in valid_views:
        view_type = 'card'
    
    # Validate sort parameter
    valid_sorts = {
        'name': 'name',
        '-name': '-name',
        'site_type': 'site_type',
        '-site_type': '-site_type',
        'status': 'status',
        '-status': '-status',
        'archived_at': 'archived_at',
        '-archived_at': '-archived_at',
    }
    
    sort_field = valid_sorts.get(sort_by, 'name')
    sites = Site.objects.filter(is_archived=True).order_by(sort_field)

    # Calculate statistics
    from apps.locations.models import CensusYear, CensusObservation
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    total_archived_sites = sites.count()
    active_sites = Site.objects.filter(is_archived=False).count()
    total_sites = Site.objects.count()

    context = {
        "sites": sites,
        "view_type": view_type,
        "total_archived_sites": total_archived_sites,
        "active_sites": active_sites,
        "total_sites": total_sites,
        "current_sort": sort_by,
    }
    return render(request, "locations/site_archived_list.html", context)


@login_required
def year_list(request, site_id):
    """View all years for a specific site"""
    site = get_object_or_404(Site, id=site_id)
    years = site.get_years_with_census()

    context = {
        "site": site,
        "years": years,
        "total_years": years.count(),
    }
    return render(request, "locations/year_list.html", context)


@login_required
def year_create(request, site_id):
    """Create a new census year for a site"""
    site = get_object_or_404(Site, id=site_id)

    if request.method == "POST":
        form = CensusYearForm(request.POST)
        if form.is_valid():
            year = form.save(commit=False)
            year.site = site
            year.save()
            messages.success(request, f"Year {year.year} created for {site.name}!")
            return redirect("locations:year_detail", site_id=site.id, year=year.year)
    else:
        form = CensusYearForm()

    context = {
        "form": form,
        "site": site,
        "title": f"Create Year for {site.name}",
    }
    return render(request, "locations/year_form.html", context)


@login_required
def year_detail(request, site_id, year):
    """View year details and its months"""
    site = get_object_or_404(Site, id=site_id)
    year_obj = get_object_or_404(CensusYear, site=site, year=year)
    
    # Get view type parameter (card or list)
    view_type = request.GET.get('view', 'card')  # Default: card view
    
    # Get sorting parameter
    sort_by = request.GET.get('sort', 'month')  # Default: month order
    
    # Validate view type parameter
    valid_views = ['card', 'list']
    if view_type not in valid_views:
        view_type = 'card'
    
    # Validate sort parameter
    valid_sorts = {
        'month': 'month',
        '-month': '-month',
        'total_census_count': 'total_census_count',
        '-total_census_count': '-total_census_count',
        'total_birds_recorded': 'total_birds_recorded',
        '-total_birds_recorded': '-total_birds_recorded',
        'total_species_recorded': 'total_species_recorded',
        '-total_species_recorded': '-total_species_recorded',
        'created_at': 'created_at',
        '-created_at': '-created_at',
    }
    
    sort_field = valid_sorts.get(sort_by, 'month')
    months = year_obj.get_months_with_census().order_by(sort_field)

    context = {
        "site": site,
        "year": year_obj,
        "months": months,
        "total_months": months.count(),
        "current_view": view_type,
        "current_sort": sort_by,
    }
    return render(request, "locations/year_detail.html", context)


@login_required
def year_edit(request, site_id, year):
    """Edit a census year"""
    site = get_object_or_404(Site, id=site_id)
    year_obj = get_object_or_404(CensusYear, site=site, year=year)

    if request.method == "POST":
        form = CensusYearForm(request.POST, instance=year_obj)
        if form.is_valid():
            form.save()
            messages.success(request, f"Year {year_obj.year} updated successfully!")
            return redirect("locations:year_detail", site_id=site.id, year=year_obj.year)
    else:
        form = CensusYearForm(instance=year_obj)

    context = {
        "form": form,
        "site": site,
        "year_obj": year_obj,
        "title": f"Edit Year {year_obj.year}",
    }
    return render(request, "locations/year_form.html", context)


@login_required
def year_delete(request, site_id, year):
    """Delete a census year"""
    site = get_object_or_404(Site, id=site_id)
    year_obj = get_object_or_404(CensusYear, site=site, year=year)

    if request.method == "POST":
        year_num = year_obj.year
        year_obj.delete()
        messages.success(request, f"Year {year_num} deleted successfully!")
        return redirect("locations:site_detail", site_id=site.id)

    context = {
        "site": site,
        "year_obj": year_obj,
        "title": f"Delete Year {year_obj.year}",
    }
    return render(request, "locations/year_confirm_delete.html", context)


@login_required
def month_list(request, site_id, year):
    """View all months for a specific year"""
    site = get_object_or_404(Site, id=site_id)
    year_obj = get_object_or_404(CensusYear, site=site, year=year)
    months = year_obj.get_months_with_census()

    context = {
        "site": site,
        "year": year_obj,
        "months": months,
        "total_months": months.count(),
    }
    return render(request, "locations/month_list.html", context)


@login_required
def month_create(request, site_id, year):
    """Create a new census month for a year"""
    site = get_object_or_404(Site, id=site_id)
    year_obj = get_object_or_404(CensusYear, site=site, year=year)

    if request.method == "POST":
        form = CensusMonthForm(request.POST)
        if form.is_valid():
            month = form.save(commit=False)
            month.year = year_obj
            month.save()
            messages.success(request, f"{month.get_month_display()} {year_obj.year} created!")
            return redirect("locations:month_detail", site_id=site.id, year=year_obj.year, month=month.month)
    else:
        form = CensusMonthForm()

    context = {
        "form": form,
        "site": site,
        "year_obj": year_obj,
        "title": f"Create Month for {year_obj.year}",
    }
    return render(request, "locations/month_form.html", context)


@login_required
def month_detail(request, site_id, year, month):
    """View month details and its census records"""
    site = get_object_or_404(Site, id=site_id)
    year_obj = get_object_or_404(CensusYear, site=site, year=year)
    month_obj = get_object_or_404(CensusMonth, year=year_obj, month=month)
    
    # Get sorting parameter
    sort_by = request.GET.get('sort', '-census_date')  # Default: newest first
    
    # Get view type parameter (card or list)
    view_type = request.GET.get('view', 'card')  # Default: card view
    
    # Validate sort parameter to prevent injection
    valid_sorts = {
        'census_date': 'census_date',           # Oldest first
        '-census_date': '-census_date',         # Newest first
        'total_birds': 'total_birds',           # Fewest birds first
        '-total_birds': '-total_birds',         # Most birds first
        'total_species': 'total_species',       # Fewest species first
        '-total_species': '-total_species',     # Most species first
        'lead_observer': 'lead_observer__employee_id',  # Observer A-Z
        '-lead_observer': '-lead_observer__employee_id', # Observer Z-A
        'created_at': 'created_at',             # Created first
        '-created_at': '-created_at',           # Created last
    }
    
    # Validate view type parameter
    valid_views = ['card', 'list']
    if view_type not in valid_views:
        view_type = 'card'
    
    sort_field = valid_sorts.get(sort_by, '-census_date')
    census_records = month_obj.get_census_records().order_by(sort_field)

    context = {
        "site": site,
        "year": year_obj,
        "month": month_obj,
        "census_records": census_records,
        "total_census": census_records.count(),
        "current_sort": sort_by,
        "current_view": view_type,
    }
    return render(request, "locations/month_detail.html", context)


@login_required
def month_edit(request, site_id, year, month):
    """Edit a census month"""
    site = get_object_or_404(Site, id=site_id)
    year_obj = get_object_or_404(CensusYear, site=site, year=year)
    month_obj = get_object_or_404(CensusMonth, year=year_obj, month=month)

    if request.method == "POST":
        form = CensusMonthForm(request.POST, instance=month_obj)
        if form.is_valid():
            form.save()  # Year is already set on the instance
            messages.success(request, f"{month_obj.get_month_display()} {year_obj.year} updated!")
            return redirect("locations:month_detail", site_id=site.id, year=year_obj.year, month=month_obj.month)
    else:
        form = CensusMonthForm(instance=month_obj)

    context = {
        "form": form,
        "site": site,
        "year_obj": year_obj,
        "month_obj": month_obj,
        "title": f"Edit {month_obj.get_month_display()} {year_obj.year}",
    }
    return render(request, "locations/month_form.html", context)


@login_required
def month_delete(request, site_id, year, month):
    """Delete a census month"""
    site = get_object_or_404(Site, id=site_id)
    year_obj = get_object_or_404(CensusYear, site=site, year=year)
    month_obj = get_object_or_404(CensusMonth, year=year_obj, month=month)

    if request.method == "POST":
        month_name = f"{month_obj.get_month_display()} {year_obj.year}"
        month_obj.delete()
        messages.success(request, f"{month_name} deleted successfully!")
        return redirect("locations:year_detail", site_id=site.id, year=year_obj.year)

    context = {
        "site": site,
        "year_obj": year_obj,
        "month_obj": month_obj,
        "title": f"Delete {month_obj.get_month_display()} {year_obj.year}",
    }
    return render(request, "locations/month_confirm_delete.html", context)


@login_required
def census_list(request, site_id, year, month):
    """View all census records for a specific month"""
    site = get_object_or_404(Site, id=site_id)
    year_obj = get_object_or_404(CensusYear, site=site, year=year)
    month_obj = get_object_or_404(CensusMonth, year=year_obj, month=month)
    
    # Get sorting parameter
    sort_by = request.GET.get('sort', '-census_date')  # Default: newest first
    
    # Validate sort parameter to prevent injection
    valid_sorts = {
        'census_date': 'census_date',           # Oldest first
        '-census_date': '-census_date',         # Newest first
        'total_birds': 'total_birds',           # Fewest birds first
        '-total_birds': '-total_birds',         # Most birds first
        'total_species': 'total_species',       # Fewest species first
        '-total_species': '-total_species',     # Most species first
        'lead_observer': 'lead_observer__employee_id',  # Observer A-Z
        '-lead_observer': '-lead_observer__employee_id', # Observer Z-A
        'created_at': 'created_at',             # Created first
        '-created_at': '-created_at',           # Created last
    }
    
    sort_field = valid_sorts.get(sort_by, '-census_date')
    census_records = month_obj.get_census_records().order_by(sort_field)

    # Calculate monthly statistics for family-grouped data display
    from django.db.models import Sum, Count
    monthly_stats = {
        'total_birds': census_records.aggregate(total=Sum('total_birds'))['total'] or 0,
        'total_species': census_records.aggregate(total=Count('observations__species', distinct=True))['total'] or 0,
        'total_observations': census_records.aggregate(total=Count('observations'))['total'] or 0,
    }
    
    # Check if this month has family-grouped data (multiple census records on the 15th)
    family_grouped_data = census_records.filter(census_date__day=15).count() > 1

    context = {
        "site": site,
        "year": year_obj,
        "month": month_obj,
        "census_records": census_records,
        "total_census": census_records.count(),
        "current_sort": sort_by,
        "monthly_stats": monthly_stats,
        "family_grouped_data": family_grouped_data,
    }
    return render(request, "locations/census_list.html", context)


@login_required
@permission_required('can_add_birds')
def census_create(request, site_id, year, month):
    """Create a new census record"""
    site = get_object_or_404(Site, id=site_id)
    year_obj = get_object_or_404(CensusYear, site=site, year=year)
    month_obj = get_object_or_404(CensusMonth, year=year_obj, month=month)

    if request.method == "POST":
        form = CensusForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                census = form.save(commit=False)
                census.month = month_obj
                census.save()
                form.save_m2m()  # Save many-to-many relationships

                # Update month summary
                month_obj.update_summary()

                messages.success(request, f"Census for {census.census_date} created!")
                return redirect("locations:census_detail", site_id=site.id, year=year_obj.year, month=month_obj.month, census_id=census.id)
    else:
        form = CensusForm()

    context = {
        "form": form,
        "site": site,
        "year": year_obj,
        "month": month_obj,
        "title": f"Create Census for {month_obj.get_month_display()} {year_obj.year}",
    }
    return render(request, "locations/census_form.html", context)


@login_required
def census_detail(request, site_id, year, month, census_id):
    """View census details and observations"""
    site = get_object_or_404(Site, id=site_id)
    year_obj = get_object_or_404(CensusYear, site=site, year=year)
    month_obj = get_object_or_404(CensusMonth, year=year_obj, month=month)
    census = get_object_or_404(Census, id=census_id, month=month_obj)
    observations = census.get_observations()

    # Group observations by family
    family_groups = {}
    uncategorized_observations = []
    
    for obs in observations:
        family_name = obs.family.strip() if obs.family else None
        
        if family_name:
            if family_name not in family_groups:
                family_groups[family_name] = []
            family_groups[family_name].append(obs)
        else:
            uncategorized_observations.append(obs)

    # Define family order as shown in species detection summary
    family_order = [
        'HERONS AND EGRETS',
        'SHOREBIRDS-WADERS', 
        'RAILS, GALLINULES & COOTS',
        'GULLS, TERNS & SKIMMERRS',
        'ADDITIONAL SPECIES',
        'UNCATEGORIZED'
    ]
    
    # Sort family_groups by the defined order
    sorted_family_groups = {}
    for family_name in family_order:
        if family_name in family_groups:
            sorted_family_groups[family_name] = family_groups[family_name]
    
    # Add any remaining families not in the predefined order
    for family_name, obs_list in family_groups.items():
        if family_name not in sorted_family_groups:
            sorted_family_groups[family_name] = obs_list

    context = {
        "site": site,
        "year": year_obj,
        "month": month_obj,
        "census": census,
        "observations": observations,
        "family_groups": sorted_family_groups,
        "uncategorized_observations": uncategorized_observations,
        "total_observations": observations.count(),
        "has_family_data": bool(family_groups),
    }
    return render(request, "locations/census_detail.html", context)


@login_required
@permission_required('can_add_birds')
def census_edit(request, site_id, year, month, census_id):
    """Edit a census record"""
    site = get_object_or_404(Site, id=site_id)
    year_obj = get_object_or_404(CensusYear, site=site, year=year)
    month_obj = get_object_or_404(CensusMonth, year=year_obj, month=month)
    census = get_object_or_404(Census, id=census_id, month=month_obj)

    if request.method == "POST":
        form = CensusForm(request.POST, instance=census)
        if form.is_valid():
            form.save()
            messages.success(request, f"Census for {census.census_date} updated!")
            return redirect("locations:census_detail", site_id=site.id, year=year_obj.year, month=month_obj.month, census_id=census.id)
    else:
        form = CensusForm(instance=census)

    context = {
        "form": form,
        "site": site,
        "year": year_obj,
        "month": month_obj,
        "census": census,
        "title": f"Edit Census for {census.census_date}",
    }
    return render(request, "locations/census_form.html", context)


@login_required
def census_delete(request, site_id, year, month, census_id):
    """Delete a census record"""
    site = get_object_or_404(Site, id=site_id)
    year_obj = get_object_or_404(CensusYear, site=site, year=year)
    month_obj = get_object_or_404(CensusMonth, year=year_obj, month=month)
    census = get_object_or_404(Census, id=census_id, month=month_obj)

    if request.method == "POST":
        census_date = census.census_date
        census.delete()

        # Update month summary
        month_obj.update_summary()

        messages.success(request, f"Census for {census_date} deleted successfully!")
        return redirect("locations:census_list", site_id=site.id, year=year_obj.year, month=month_obj.month)

    context = {
        "site": site,
        "year": year_obj,
        "month": month_obj,
        "census": census,
        "title": f"Delete Census for {census.census_date}",
    }
    return render(request, "locations/census_confirm_delete.html", context)


# API endpoints for AJAX operations
@login_required
@require_http_methods(["POST"])
def update_coordinates(request, site_id):
    """Update site coordinates via AJAX"""
    site = get_object_or_404(Site, id=site_id)

    try:
        data = json.loads(request.body)
        coordinates = data.get("coordinates", "").strip()

        if coordinates:
            site.coordinates = coordinates
            site.save()
            return JsonResponse({
                "success": True,
                "coordinates": site.get_coordinates_display()
            })
        else:
            return JsonResponse({"success": False, "error": "Coordinates cannot be empty"})

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON data"})
    except Exception as e:  
        return JsonResponse({"success": False, "error": str(e)})


@login_required
def get_observations(request, census_id):
    """Get observations for a census (AJAX endpoint)"""
    census = get_object_or_404(Census, id=census_id)
    observations = census.get_observations()

    data = []
    for obs in observations:
        data.append({
            "id": str(obs.id),
            "species": obs.species.name if obs.species else obs.species_name,
            "count": obs.count,
            "behavior_notes": obs.behavior_notes,
        })

    return JsonResponse({"observations": data})


@login_required
@require_http_methods(["GET"])
def get_site_map_data(request, site_id):
    """Get map data for a specific site including census information"""
    site = get_object_or_404(Site, id=site_id)
    
    # Parse coordinates using the model's method
    coordinates = None
    if site.coordinates:
        try:
            lat, lon = site.parse_coordinates()
            coordinates = {
                "lat": lat,
                "lon": lon
            }
        except (ValueError, IndexError):
            pass
    
    # Get census data
    census_years = site.get_years_with_census()
    census_data = []
    
    for year in census_years:
        census_data.append({
            "year": year.year,
            "total_birds": year.total_birds_recorded,
            "total_species": year.total_species_recorded,
            "total_census": year.total_census_count
        })
    
    # Get all sites for context (if needed for multi-site view)
    all_sites = Site.objects.filter(status="active", coordinates__isnull=False).exclude(coordinates="")
    nearby_sites = []
    
    for other_site in all_sites:
        if other_site.id != site.id and other_site.coordinates:
            try:
                lat, lon = other_site.parse_coordinates()
                nearby_sites.append({
                    "id": str(other_site.id),
                    "name": other_site.name,
                    "site_type": other_site.site_type,
                    "coordinates": {
                        "lat": lat,
                        "lon": lon
                    },
                    "status": other_site.status
                })
            except (ValueError, IndexError):
                continue
    
    return JsonResponse({
        "site": {
            "id": str(site.id),
            "name": site.name,
            "site_type": site.site_type,
            "coordinates": coordinates,
            "description": site.description,
            "status": site.status
        },
        "census_data": census_data,
        "nearby_sites": nearby_sites
    })


@login_required
def observation_create(request, site_id, year, month, census_id):
    """Create a new observation for a census"""
    site = get_object_or_404(Site, id=site_id)
    year_obj = get_object_or_404(CensusYear, site=site, year=year)
    month_obj = get_object_or_404(CensusMonth, year=year_obj, month=month)
    census = get_object_or_404(Census, id=census_id, month=month_obj)

    if request.method == "POST":
        form = CensusObservationForm(request.POST)
        if form.is_valid():
            observation = form.save(commit=False)
            observation.census = census
            observation.save()

            # Update census totals
            census.update_totals()

            messages.success(request, f"Observation added for {observation.species_name}")
            return redirect("locations:census_detail", site_id=site.id, year=year_obj.year, month=month_obj.month, census_id=census.id)
    else:
        form = CensusObservationForm()

    context = {
        "form": form,
        "site": site,
        "year": year_obj,
        "month": month_obj,
        "census": census,
        "title": f"Add Observation to {census.census_date}",
    }
    return render(request, "locations/observation_form.html", context)


@login_required
def observation_edit(request, site_id, year, month, census_id, observation_id):
    """Edit an observation"""
    site = get_object_or_404(Site, id=site_id)
    year_obj = get_object_or_404(CensusYear, site=site, year=year)
    month_obj = get_object_or_404(CensusMonth, year=year_obj, month=month)
    census = get_object_or_404(Census, id=census_id, month=month_obj)
    observation = get_object_or_404(CensusObservation, id=observation_id, census=census)

    if request.method == "POST":
        form = CensusObservationForm(request.POST, instance=observation)
        if form.is_valid():
            form.save()

            # Update census totals
            census.update_totals()

            messages.success(request, f"Observation updated")
            return redirect("locations:census_detail", site_id=site.id, year=year_obj.year, month=month_obj.month, census_id=census.id)
    else:
        form = CensusObservationForm(instance=observation)

    context = {
        "form": form,
        "site": site,
        "year": year_obj,
        "month": month_obj,
        "census": census,
        "observation": observation,
        "title": f"Edit Observation",
    }
    return render(request, "locations/observation_form.html", context)


@login_required
def observation_delete(request, site_id, year, month, census_id, observation_id):
    """Delete an observation"""
    site = get_object_or_404(Site, id=site_id)
    year_obj = get_object_or_404(CensusYear, site=site, year=year)
    month_obj = get_object_or_404(CensusMonth, year=year_obj, month=month)
    census = get_object_or_404(Census, id=census_id, month=month_obj)
    observation = get_object_or_404(CensusObservation, id=observation_id, census=census)

    if request.method == "POST":
        observation.delete()

        # Update census totals
        census.update_totals()

        messages.success(request, "Observation deleted")
        return redirect("locations:census_detail", site_id=site.id, year=year_obj.year, month=month_obj.month, census_id=census.id)

    context = {
        "observation": observation,
        "census": census,
        "site": site,
        "year": year_obj,
        "month": month_obj,
    }
    return render(request, "locations/observation_confirm_delete.html", context)


@login_required
def batch_observation_create(request, site_id, year, month, census_id):
    """Batch create multiple observations for a census"""
    site = get_object_or_404(Site, id=site_id)
    year_obj = get_object_or_404(CensusYear, site=site, year=year)
    month_obj = get_object_or_404(CensusMonth, year=year_obj, month=month)
    census = get_object_or_404(Census, id=census_id, month=month_obj)

    if request.method == "POST":
        form = BatchObservationForm(request.POST, census=census)
        if form.is_valid():
            # Create observations from form data
            # Check how many observation groups we have from POST data
            max_groups = 0
            for field_name in request.POST:
                # Only look for species fields that have numeric suffixes (like species_0, species_1, etc.)
                if field_name.startswith('species_') and not field_name.startswith('species_name_'):
                    parts = field_name.split('_')
                    if len(parts) >= 2 and parts[1].isdigit():
                        index = int(parts[1])
                        max_groups = max(max_groups, index + 1)

            for i in range(max_groups):
                field_name = f'species_{i}'
                if field_name in request.POST:
                    species = request.POST.get(f'species_{i}')
                    species_name = request.POST.get(f'species_name_{i}')
                    count = request.POST.get(f'count_{i}')

                    # Convert count to int if it's a string
                    try:
                        count = int(count) if count else 0
                    except (ValueError, TypeError):
                        count = 0

                    if count and count > 0:
                        observation = CensusObservation.objects.create(
                            census=census,
                            species_id=species if species else None,
                            species_name=species_name,
                            count=count
                        )

            # Update census totals
            census.update_totals()

            messages.success(request, f"Batch observations added successfully!")
            return redirect("locations:census_detail", site_id=site.id, year=year_obj.year, month=month_obj.month, census_id=census.id)
    else:
        form = BatchObservationForm(census=census)

    context = {
        "form": form,
        "site": site,
        "year": year_obj,
        "month": month_obj,
        "census": census,
        "title": f"Batch Add Observations to {census.census_date}",
    }
    return render(request, "locations/batch_observation_form.html", context)