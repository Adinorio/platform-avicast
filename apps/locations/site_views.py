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
from django.utils import timezone

from django.contrib.admin.views.decorators import staff_member_required as staff_required
from .forms import SiteForm
from .models import Site, SiteSpeciesCount, CensusObservation, SpeciesObservation


@login_required
def site_dashboard(request):
    """Main site management dashboard with tabs and overview"""
    from datetime import timedelta

    # Get dashboard statistics
    total_sites = Site.objects.count()
    active_sites = Site.objects.filter(status='active').count()

    # Recent observations (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_observations = SpeciesObservation.objects.filter(
        created_at__gte=thirty_days_ago
    ).count()

    # Total species observed (unique species across all sites)
    total_species = SiteSpeciesCount.objects.values('species').distinct().count()

    # Get recent sites (last 10 updated)
    recent_sites = Site.objects.all().order_by('-updated_at')[:10]

    # Get recent activity (mock data for now - could be expanded)
    recent_activity = [
        {
            'type': 'site_created',
            'title': 'New Site Added',
            'description': 'Lakawon observation site was created',
            'timestamp': timezone.now() - timedelta(days=2)
        }
    ] if total_sites > 0 else []

    # Handle tab parameter for URL consistency
    current_tab = request.GET.get('tab', 'overview')

    # Handle sites list tab if requested
    sites_list_data = None
    if current_tab == 'sites':
        # Get sites list data for the dashboard tab
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

        # Pagination for dashboard tab
        paginator = Paginator(sites, 12)  # Smaller page size for dashboard
        page_number = request.GET.get("page", 1)
        page_obj = paginator.get_page(page_number)

        sites_list_data = {
            "page_obj": page_obj,
            "search_query": search_query,
            "site_type": site_type,
            "status": status,
            "site_types": Site.SITE_TYPES,
            "site_statuses": Site.STATUS_CHOICES,
            "current_tab": current_tab,
        }

    context = {
        'total_sites': total_sites,
        'active_sites': active_sites,
        'recent_observations': recent_observations,
        'total_species': total_species,
        'recent_sites': recent_sites,
        'recent_activity': recent_activity,
        'current_tab': current_tab,
        'sites_list_data': sites_list_data,
    }

    return render(request, 'locations/dashboard.html', context)


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

    # Handle tab parameter for dashboard integration
    current_tab = request.GET.get("tab", "sites")

    context = {
        "page_obj": page_obj,
        "search_query": search_query,
        "site_type": site_type,
        "status": status,
        "site_types": Site.SITE_TYPES,
        "site_statuses": Site.SITE_STATUS,
        "current_tab": current_tab,
    }
    return render(request, "locations/site_list.html", context)


@login_required
def site_detail(request, site_id):
    """Display detailed site information with integrated census data and species tracking"""
    site = get_object_or_404(Site, id=site_id)

    # Get census summary organized by year and month
    census_summary = site.get_census_summary()

    # Get recent census observations (excluding archived)
    recent_census = site.census_observations.filter(is_archived=False).order_by("-observation_date")[:10]

    # Get the most recent census for display purposes
    most_recent_census = recent_census.first() if recent_census.exists() else None

    # Get archived census observations
    archived_census = site.census_observations.filter(is_archived=True).order_by("-observation_date")[:5]

    # Get species counts for this site
    from .models import SiteSpeciesCount
    site_species_counts = SiteSpeciesCount.objects.filter(
        site=site,
        is_verified=True
    ).select_related('species').order_by('-total_count')

    # Calculate site statistics
    total_verified_species = site_species_counts.count()
    total_verified_birds = site_species_counts.aggregate(
        total=Sum('total_count')
    )['total'] or 0

    # Get unverified species counts for admin review
    unverified_counts = SiteSpeciesCount.objects.filter(
        site=site,
        is_verified=False
    ).select_related('species')

    # Monthly data for charts (last 12 months)
    monthly_data = {}
    current_date = timezone.now().date()
    for i in range(12):
        month_date = current_date.replace(day=1) - timezone.timedelta(days=i*30)
        month_key = month_date.strftime('%Y-%m')

        # Get total birds for this month
        month_total = 0
        for species_count in site_species_counts:
            if month_key in species_count.monthly_counts:
                month_total += species_count.monthly_counts[month_key]

        monthly_data[month_key] = month_total

    # Reverse to show chronological order
    monthly_data = dict(reversed(list(monthly_data.items())))

    # Check if user is admin for enhanced features
    is_admin = request.user.role in ['SUPERADMIN', 'ADMIN']

    # Enhanced data aggregation for Admin views
    if is_admin:
        # Get all census observations for this site (including archived for completeness)
        all_census = site.census_observations.all().order_by('observation_date')

        # Calculate yearly totals
        yearly_totals = {}
        for census in all_census:
            year = census.observation_date.year
            if year not in yearly_totals:
                yearly_totals[year] = {
                    'total_species': 0,
                    'total_birds': 0,
                    'census_count': 0,
                    'months': {}
                }

            yearly_totals[year]['total_species'] += census.get_total_species_count()
            yearly_totals[year]['total_birds'] += census.get_total_birds_count()
            yearly_totals[year]['census_count'] += 1

            # Monthly breakdown
            month = census.observation_date.month
            if month not in yearly_totals[year]['months']:
                yearly_totals[year]['months'][month] = {
                    'total_species': 0,
                    'total_birds': 0,
                    'census_count': 0
                }

            yearly_totals[year]['months'][month]['total_species'] += census.get_total_species_count()
            yearly_totals[year]['months'][month]['total_birds'] += census.get_total_birds_count()
            yearly_totals[year]['months'][month]['census_count'] += 1

        # Calculate overall site statistics
        site_stats = {
            'total_census_records': all_census.count(),
            'total_species_ever': len(site_species_counts),
            'total_birds_ever': sum(sc.total_count for sc in site_species_counts),
            'first_observation': all_census.first().observation_date if all_census.exists() else None,
            'last_observation': all_census.last().observation_date if all_census.exists() else None,
        }

    context = {
        "site": site,
        "census_summary": census_summary,
        "recent_census": recent_census,
        "most_recent_census": most_recent_census,
        "archived_census": archived_census,
        "site_species_counts": site_species_counts,
        "unverified_counts": unverified_counts,
        "total_verified_species": total_verified_species,
        "total_verified_birds": total_verified_birds,
        "monthly_data": monthly_data,
        "yearly_totals": yearly_totals if is_admin else {},
        "site_stats": site_stats if is_admin else {},
        "is_admin": request.user.role in ['SUPERADMIN', 'ADMIN'],
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


@login_required
@staff_required
def verify_species_count(request, count_id):
    """Verify a species count (admin only)"""
    species_count = get_object_or_404(SiteSpeciesCount, id=count_id)

    if request.method == "POST":
        species_count.verify_count(request.user)
        messages.success(
            request,
            f'Species count for {species_count.species.name} at {species_count.site.name} has been verified!'
        )
        return redirect("locations:site_detail", site_id=species_count.site.id)

    return redirect("locations:site_detail", site_id=species_count.site.id)
