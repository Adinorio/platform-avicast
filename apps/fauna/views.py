"""
Views for fauna app - Species management
"""

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView
from django.utils.decorators import method_decorator

from .models import Species


class SpeciesListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    Display list of all non-archived species

    Accessible by: ADMIN, FIELD_WORKER
    """
    model = Species
    template_name = "fauna/species_list.html"
    context_object_name = "species_list"

    def test_func(self):
        """Check if user has required permissions"""
        user = self.request.user
        if not user.is_authenticated:
            return False

        if not hasattr(user, "role"):
            return False

        # Allow ADMIN and FIELD_WORKER roles
        return user.role in ["ADMIN", "FIELD_WORKER"]

    def handle_no_permission(self):
        """Handle unauthorized access"""
        if not self.request.user.is_authenticated:
            from django.shortcuts import redirect
            from django.contrib import messages
            messages.error(self.request, "Authentication required.")
            return redirect("login")

        from django.http import HttpResponse
        return HttpResponse("Access denied. Insufficient permissions.", status=403)

    def get_queryset(self):
        """Return only non-archived species ordered by name"""
        return Species.objects.filter(is_archived=False).order_by("name")

    def get_context_data(self, **kwargs):
        """Add additional context data"""
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        context["total_species"] = queryset.count()
        
        # Add IUCN status statistics
        context["iucn_stats"] = {
            'least_concern': queryset.filter(iucn_status='LC').count(),
            'near_threatened': queryset.filter(iucn_status='NT').count(),
            'vulnerable': queryset.filter(iucn_status='VU').count(),
            'endangered': queryset.filter(iucn_status='EN').count(),
            'critically_endangered': queryset.filter(iucn_status='CR').count(),
        }
        
        return context
