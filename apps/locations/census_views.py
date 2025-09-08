"""
Census management views for locations app
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from apps.image_processing.permissions import staff_required
from .forms import CensusObservationForm, SpeciesObservationFormSet
from .models import CensusObservation, Site


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
                census_form.save()
                species_formset.save()

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
        census.delete()
        messages.success(request, "Census observation deleted successfully!")
        return redirect("locations:site_detail", site_id=site_id)

    context = {"census": census}
    return render(request, "locations/census_confirm_delete.html", context)
