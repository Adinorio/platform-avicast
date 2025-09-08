from functools import wraps

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.views.generic import ListView

from .models import Species

# Create your views here.


# Import the shared decorator from analytics app
from apps.analytics.views import role_required


class SpeciesListView(LoginRequiredMixin, ListView):
    model = Species
    template_name = "fauna/species_list.html"

    @role_required(["ADMIN", "FIELD_WORKER"])
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        # Only show non-archived species
        return Species.objects.filter(is_archived=False).order_by("name")
