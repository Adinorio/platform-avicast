from django.shortcuts import render
from django.views.generic import ListView
from django.contrib.auth.mixins import PermissionRequiredMixin
from .models import Species

# Create your views here.

class SpeciesListView(PermissionRequiredMixin, ListView):
    model = Species
    template_name = 'fauna/species_list.html'
    permission_required = 'fauna.view_species'
    
    def get_queryset(self):
        # Only show non-archived species
        return Species.objects.filter(is_archived=False).order_by('name')
