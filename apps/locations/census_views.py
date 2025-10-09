"""
Census management views for locations app
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.db.models import Q, Sum, Count
from django.http import JsonResponse

from django.contrib.admin.views.decorators import staff_member_required as staff_required
from .forms import CensusObservationForm, SpeciesObservationFormSet
from .models import CensusObservation, Site, SiteSpeciesCount, MobileDataImport, DataChangeRequest, log_census_activity


@login_required
@staff_required
def census_create(request, site_id):
    """Create a new census observation for a site"""
    site = get_object_or_404(Site, id=site_id)

    if request.method == "POST":
        census_form = CensusObservationForm(request.POST, site=site)
        species_formset = SpeciesObservationFormSet(request.POST, instance=census_form.instance)

        if census_form.is_valid() and species_formset.is_valid():
            with transaction.atomic():
                census = census_form.save(commit=False)
                census.site = site
                census.observer = request.user
                census.save()

                species_formset.instance = census
                species_formset.save()

                # Log activity
                log_census_activity(
                    census=census,
                    activity_type="create",
                    description=f"Created census observation for {site.name} on {census.observation_date}",
                    user=request.user,
                    request=request
                )

                messages.success(
                    request, f"Census observation for {site.name} created successfully!"
                )
                return redirect("locations:site_detail", site_id=site.id)
    else:
        census_form = CensusObservationForm(site=site)
        species_formset = SpeciesObservationFormSet()

    context = {
        "site": site,
        "census_form": census_form,
        "species_formset": species_formset,
        "action": "Create",
    }
    return render(request, "locations/census_form.html", context)


@login_required
@staff_required
def census_update(request, census_id):
    """Update an existing census observation"""
    census = get_object_or_404(CensusObservation, id=census_id)

    if request.method == "POST":
        census_form = CensusObservationForm(request.POST, instance=census, site=census.site)
        species_formset = SpeciesObservationFormSet(request.POST, instance=census)

        if census_form.is_valid() and species_formset.is_valid():
            with transaction.atomic():
                # Capture old values before saving
                old_values = {
                    'observation_date': str(census.observation_date),
                    'weather_conditions': census.weather_conditions,
                    'notes': census.notes,
                    'species_count': census.get_total_species_count(),
                    'birds_count': census.get_total_birds_count()
                }

                census_form.save()
                species_formset.save()

                # Capture new values after saving
                new_values = {
                    'observation_date': str(census.observation_date),
                    'weather_conditions': census.weather_conditions,
                    'notes': census.notes,
                    'species_count': census.get_total_species_count(),
                    'birds_count': census.get_total_birds_count()
                }

                # Log activity
                log_census_activity(
                    census=census,
                    activity_type="update",
                    description=f"Updated census observation for {census.site.name} on {census.observation_date}",
                    user=request.user,
                    old_values=old_values,
                    new_values=new_values,
                    request=request
                )

                messages.success(request, "Census observation updated successfully!")
                return redirect("locations:site_detail", site_id=census.site.id)
    else:
        census_form = CensusObservationForm(instance=census, site=census.site)
        species_formset = SpeciesObservationFormSet(instance=census)

    context = {
        "census": census,
        "site": census.site,
        "census_form": census_form,
        "species_formset": species_formset,
        "action": "Update",
    }
    return render(request, "locations/census_form.html", context)


@login_required
@staff_required
def census_delete(request, census_id):
    """Delete a census observation"""
    census = get_object_or_404(CensusObservation, id=census_id)
    site_id = census.site.id

    if request.method == "POST":
        # Log activity before deletion
        log_census_activity(
            census=census,
            activity_type="delete",
            description=f"Permanently deleted census observation for {census.site.name} on {census.observation_date}",
            user=request.user,
            request=request
        )

        census.delete()
        messages.success(request, "Census observation deleted successfully!")
        return redirect("locations:site_detail", site_id=site_id)

    context = {"census": census}
    return render(request, "locations/census_confirm_delete.html", context)


@login_required
@staff_required
def census_archive(request, census_id):
    """Archive a census observation"""
    census = get_object_or_404(CensusObservation, id=census_id)
    site_id = census.site.id

    if request.method == "POST":
        reason = request.POST.get("archive_reason", "")
        old_values = {
            'is_archived': False,
            'archived_by': None,
            'archived_at': None,
            'archived_reason': ""
        }
        census.archive(request.user, reason)

        # Log activity
        log_census_activity(
            census=census,
            activity_type="archive",
            description=f"Archived census observation for {census.site.name} on {census.observation_date}. Reason: {reason}",
            user=request.user,
            old_values=old_values,
            new_values={
                'is_archived': True,
                'archived_by': str(request.user.id),
                'archived_at': str(timezone.now()),
                'archived_reason': reason
            },
            request=request
        )

        messages.success(request, f"Census observation archived successfully!")
        return redirect("locations:site_detail", site_id=site_id)

    context = {
        "census": census,
        "action": "Archive"
    }
    return render(request, "locations/census_archive.html", context)


@login_required
@staff_required
def census_restore(request, census_id):
    """Restore an archived census observation"""
    census = get_object_or_404(CensusObservation, id=census_id, is_archived=True)
    site_id = census.site.id

    if request.method == "POST":
        old_values = {
            'is_archived': True,
            'archived_by': str(census.archived_by.id) if census.archived_by else None,
            'archived_at': str(census.archived_at) if census.archived_at else None,
            'archived_reason': census.archived_reason
        }
        census.restore()

        # Log activity
        log_census_activity(
            census=census,
            activity_type="restore",
            description=f"Restored archived census observation for {census.site.name} on {census.observation_date}",
            user=request.user,
            old_values=old_values,
            new_values={
                'is_archived': False,
                'archived_by': None,
                'archived_at': None,
                'archived_reason': ""
            },
            request=request
        )

        messages.success(request, f"Census observation restored successfully!")
        return redirect("locations:site_detail", site_id=site_id)

    context = {
        "census": census,
        "action": "Restore"
    }
    return render(request, "locations/census_restore.html", context)


@login_required
def census_dashboard(request):
    """Main census management dashboard with overview and filtering"""
    # Get user's role for permissions
    user_role = getattr(request.user, 'role', 'FIELD_WORKER')
    is_admin = user_role in ['SUPERADMIN', 'ADMIN']

    # Base queryset
    if is_admin:
        sites = Site.objects.filter(status='active')
    else:
        # Field workers can only see sites they've observed
        sites = Site.objects.filter(
            status='active',
            census_observations__observer=request.user
        ).distinct()

    # Filter by site if specified
    selected_site_id = request.GET.get('site')
    if selected_site_id:
        sites = sites.filter(id=selected_site_id)

    # Filter by year if specified
    selected_year = request.GET.get('year')
    if selected_year:
        sites = sites.filter(census_observations__observation_date__year=selected_year)

    # Get all available sites for filter dropdown
    all_sites = Site.objects.filter(status='active')
    available_years = CensusObservation.objects.values_list('observation_date__year', flat=True).distinct()

    # Get census statistics
    total_census_records = CensusObservation.objects.filter(site__in=sites).count()
    total_species_observed = SiteSpeciesCount.objects.filter(
        site__in=sites,
        is_verified=True
    ).aggregate(total=Sum('total_count'))['total'] or 0

    # Recent activity
    recent_census = CensusObservation.objects.filter(
        site__in=sites
    ).select_related('site', 'observer').order_by('-observation_date')[:10]

    # Monthly summary for current year
    current_year = timezone.now().year
    monthly_summary = {}
    for month in range(1, 13):
        month_census = CensusObservation.objects.filter(
            site__in=sites,
            observation_date__year=current_year,
            observation_date__month=month
        )
        total_birds = 0
        total_species = 0
        for census in month_census:
            total_birds += census.get_total_birds_count()
            total_species += census.get_total_species_count()

        monthly_summary[month] = {
            'census_count': month_census.count(),
            'total_birds': total_birds,
            'total_species': total_species
        }

    # Pending requests for admins
    pending_requests = []
    if is_admin:
        pending_requests = DataChangeRequest.objects.filter(
            status='pending',
            request_type__in=['add_census', 'edit_census', 'add_species', 'edit_species']
        ).select_related('requested_by', 'site').order_by('-requested_at')[:5]

    context = {
        'sites': sites,
        'all_sites': all_sites,
        'available_years': sorted(available_years, reverse=True),
        'selected_site_id': selected_site_id,
        'selected_year': selected_year,
        'total_census_records': total_census_records,
        'total_species_observed': total_species_observed,
        'recent_census': recent_census,
        'monthly_summary': monthly_summary,
        'pending_requests': pending_requests,
        'is_admin': is_admin,
        'current_year': current_year,
    }

    return render(request, 'locations/census_dashboard.html', context)


@login_required
def get_individual_birds_api(request, census_id):
    """API endpoint to get individual bird records for a census"""
    census = get_object_or_404(CensusObservation, id=census_id)

    # Check if user has permission to view this census
    if not (request.user.role in ['SUPERADMIN', 'ADMIN'] or census.observer == request.user):
        return JsonResponse({'error': 'Permission denied'}, status=403)

    species_observations = []
    for obs in census.species_observations.select_related('species').all():
        species_data = {
            'id': obs.id,
            'species_name': obs.species.name if obs.species else obs.species_name,
            'species_scientific_name': obs.species.scientific_name if obs.species else '',
            'count': obs.count,
            'behavior_notes': obs.behavior_notes,
            'created_at': obs.created_at.isoformat() if obs.created_at else None,
        }
        species_observations.append(species_data)

    return JsonResponse({
        'census_id': census.id,
        'observation_date': census.observation_date.isoformat(),
        'site_name': census.site.name,
        'species_observations': species_observations,
        'total_species': len(species_observations),
        'total_birds': sum(obs['count'] for obs in species_observations),
    })
