from functools import wraps

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.views.generic import ListView

from .models import Species

# Create your views here.


def role_required(allowed_roles):
    """
    Mixin to check if user has required role
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return HttpResponse("Please log in", status=401)

            if not hasattr(request.user, "role"):
                return HttpResponse("User role not defined", status=403)

            if request.user.role not in allowed_roles:
                return HttpResponse("Access denied. Insufficient permissions.", status=403)

            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator


class SpeciesListView(LoginRequiredMixin, ListView):
    model = Species
    template_name = "fauna/species_list.html"

    def dispatch(self, request, *args, **kwargs):
        # Check role-based permissions
        if not hasattr(request.user, "role"):
            return HttpResponse("User role not defined", status=403)

        if request.user.role not in ["ADMIN", "FIELD_WORKER"]:
            return HttpResponse("Access denied. Insufficient permissions.", status=403)

        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        # Only show non-archived species
        return Species.objects.filter(is_archived=False).order_by("name")
