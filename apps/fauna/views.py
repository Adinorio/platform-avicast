"""
Views for fauna app - Species management
"""

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.views import View
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404

from .models import Species, BirdFamily
from .forms import SpeciesForm, BirdFamilyForm
from .services import SpeciesMatcher
from apps.users.models import UserActivity


class SpeciesListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    Display list of all non-archived species with search functionality

    Accessible by: ADMIN, FIELD_WORKER
    """
    model = Species
    template_name = "fauna/species_list.html"
    context_object_name = "species_list"
    paginate_by = 50

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

        from django.shortcuts import render
        return render(self.request, '403.html', {'message': 'Access denied. Insufficient permissions.'}, status=403)

    def get_queryset(self):
        """Return filtered and ordered species with smart matching"""
        queryset = Species.objects.filter(is_archived=False)

        # Apply search filter if provided (with smart matching)
        search_query = self.request.GET.get('search', '').strip()
        if search_query:
            # Use smart matching for species search
            matcher = SpeciesMatcher()
            smart_matches = matcher.find_species(search_query, limit=50)
            
            if smart_matches:
                # Get species IDs from smart matches
                species_ids = [match['species'].id for match in smart_matches]
                queryset = queryset.filter(id__in=species_ids)
            else:
                # Fallback to basic search if no smart matches found
                queryset = queryset.filter(
                    Q(name__icontains=search_query) |
                    Q(scientific_name__icontains=search_query) |
                    Q(family__display_name__icontains=search_query) |
                    Q(description__icontains=search_query)
                )

        # Apply family filter if provided
        family_filter = self.request.GET.get('family', '').strip()
        if family_filter:
            queryset = queryset.filter(family__display_name__iexact=family_filter)

        # Apply IUCN status filter if provided
        iucn_filter = self.request.GET.get('iucn_status', '').strip()
        if iucn_filter:
            queryset = queryset.filter(iucn_status=iucn_filter)

        return queryset.order_by("name")

    def get_paginate_by(self, queryset):
        """Allow users to show all species or use pagination"""
        show_all = self.request.GET.get('show_all', '').strip()
        if show_all.lower() == 'true':
            return None  # No pagination
        return self.paginate_by

    def get_context_data(self, **kwargs):
        """Add additional context data with smart matching info"""
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()

        context["total_species"] = Species.objects.filter(is_archived=False).count()
        context["current_search"] = self.request.GET.get('search', '')
        context["current_family"] = self.request.GET.get('family', '')
        context["current_iucn"] = self.request.GET.get('iucn_status', '')

        # Add IUCN status statistics for all species
        all_species = Species.objects.filter(is_archived=False)
        context["iucn_stats"] = {
            'least_concern': all_species.filter(iucn_status='LC').count(),
            'near_threatened': all_species.filter(iucn_status='NT').count(),
            'vulnerable': all_species.filter(iucn_status='VU').count(),
            'endangered': all_species.filter(iucn_status='EN').count(),
            'critically_endangered': all_species.filter(iucn_status='CR').count(),
        }

        # Add family options for filter dropdown
        context["families"] = sorted(
            Species.objects.filter(is_archived=False).exclude(family__isnull=True).values_list('family__display_name', flat=True).distinct()
        )

        # Add smart matching info if there's a search query
        search_query = context["current_search"]
        if search_query:
            matcher = SpeciesMatcher()
            smart_matches = matcher.find_species(search_query, limit=10)
            context['smart_matches'] = smart_matches
            context['has_smart_matches'] = len(smart_matches) > 0

        return context


class SpeciesDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """
    Display detailed information about a specific species

    Accessible by: ADMIN, FIELD_WORKER
    """
    model = Species
    template_name = "fauna/species_detail.html"
    context_object_name = "species"

    def test_func(self):
        """Check if user has required permissions"""
        user = self.request.user
        if not user.is_authenticated:
            return False

        if not hasattr(user, "role"):
            return False

        return user.role in ["ADMIN", "FIELD_WORKER"]

    def handle_no_permission(self):
        """Handle unauthorized access"""
        if not self.request.user.is_authenticated:
            from django.shortcuts import redirect
            from django.contrib import messages
            messages.error(self.request, "Authentication required.")
            return redirect("login")

        from django.shortcuts import render
        return render(self.request, '403.html', {'message': 'Access denied. Insufficient permissions.'}, status=403)

    def get_context_data(self, **kwargs):
        """Add additional context data"""
        context = super().get_context_data(**kwargs)

        # Add census observation statistics for this species
        from apps.locations.models import CensusObservation
        observations = CensusObservation.objects.filter(
            species_name=self.object.name
        ).select_related('census', 'census__month', 'census__month__year', 'census__month__year__site').order_by('-census__census_date')
        
        context["observation_count"] = observations.count()
        context["total_birds_observed"] = observations.aggregate(total=Sum('count'))['total'] or 0
        context["observations"] = observations

        return context


class SpeciesCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    Create a new species

    Accessible by: ADMIN only
    """
    model = Species
    form_class = SpeciesForm
    template_name = "fauna/species_form.html"
    success_url = reverse_lazy("fauna:species_list")

    def test_func(self):
        """Check if user has required permissions"""
        user = self.request.user
        if not user.is_authenticated:
            return False

        if not hasattr(user, "role"):
            return False

        return user.role == "ADMIN"

    def handle_no_permission(self):
        """Handle unauthorized access"""
        if not self.request.user.is_authenticated:
            from django.shortcuts import redirect
            from django.contrib import messages
            messages.error(self.request, "Authentication required.")
            return redirect("login")

        from django.shortcuts import render
        return render(self.request, '403.html', {'message': 'Access denied. Admin privileges required.'}, status=403)

    def form_valid(self, form):
        """Handle successful form submission"""
        species = form.instance
        
        # Log the activity
        UserActivity.log_activity(
            user=self.request.user,
            activity_type=UserActivity.ActivityType.SPECIES_ADDED,
            description=f"Created new species: {species.name} ({species.scientific_name})",
            ip_address=self.request.META.get('REMOTE_ADDR'),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            metadata={
                'species_id': str(species.id),
                'species_name': species.name,
                'scientific_name': species.scientific_name,
                'family': species.family,
                'iucn_status': species.iucn_status,
            }
        )
        
        messages.success(self.request, f"Species '{species.name}' has been created successfully.")
        return super().form_valid(form)


class SpeciesUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Update an existing species

    Accessible by: ADMIN only
    """
    model = Species
    form_class = SpeciesForm
    template_name = "fauna/species_form.html"

    def test_func(self):
        """Check if user has required permissions"""
        user = self.request.user
        if not user.is_authenticated:
            return False

        if not hasattr(user, "role"):
            return False

        return user.role == "ADMIN"

    def handle_no_permission(self):
        """Handle unauthorized access"""
        if not self.request.user.is_authenticated:
            from django.shortcuts import redirect
            from django.contrib import messages
            messages.error(self.request, "Authentication required.")
            return redirect("login")

        from django.shortcuts import render
        return render(self.request, '403.html', {'message': 'Access denied. Admin privileges required.'}, status=403)

    def form_valid(self, form):
        """Handle successful form submission"""
        species = form.instance
        old_values = {}
        
        # Get old values for comparison (if available)
        if hasattr(self, 'get_object'):
            try:
                old_species = self.get_object()
                old_values = {
                    'old_name': old_species.name,
                    'old_scientific_name': old_species.scientific_name,
                    'old_family': old_species.family,
                    'old_iucn_status': old_species.iucn_status,
                    'old_description': old_species.description,
                }
            except:
                pass
        
        # Log the activity
        UserActivity.log_activity(
            user=self.request.user,
            activity_type=UserActivity.ActivityType.SPECIES_UPDATED,
            description=f"Updated species: {species.name} ({species.scientific_name})",
            ip_address=self.request.META.get('REMOTE_ADDR'),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            metadata={
                'species_id': str(species.id),
                'species_name': species.name,
                'scientific_name': species.scientific_name,
                'family': species.family,
                'iucn_status': species.iucn_status,
                'old_values': old_values,
                'new_values': {
                    'name': species.name,
                    'scientific_name': species.scientific_name,
                    'family': species.family,
                    'iucn_status': species.iucn_status,
                    'description': species.description,
                }
            }
        )
        
        messages.success(self.request, f"Species '{species.name}' has been updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        """Return URL to redirect to after successful update"""
        return reverse_lazy("fauna:species_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        """Add additional context data"""
        context = super().get_context_data(**kwargs)
        context["is_edit"] = True
        return context


class SpeciesDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    Archive a species (soft delete)

    Accessible by: ADMIN only
    """
    model = Species
    template_name = "fauna/species_confirm_delete.html"
    success_url = reverse_lazy("fauna:species_list")

    def test_func(self):
        """Check if user has required permissions"""
        user = self.request.user
        if not user.is_authenticated:
            return False

        if not hasattr(user, "role"):
            return False

        return user.role == "ADMIN"

    def handle_no_permission(self):
        """Handle unauthorized access"""
        if not self.request.user.is_authenticated:
            from django.shortcuts import redirect
            from django.contrib import messages
            messages.error(self.request, "Authentication required.")
            return redirect("login")

        from django.shortcuts import render
        return render(self.request, '403.html', {'message': 'Access denied. Admin privileges required.'}, status=403)

    def delete(self, request, *args, **kwargs):
        """Archive the species instead of deleting"""
        species = self.get_object()
        
        # Log the activity
        UserActivity.log_activity(
            user=request.user,
            activity_type=UserActivity.ActivityType.SPECIES_ARCHIVED,
            description=f"Archived species: {species.name} ({species.scientific_name})",
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            metadata={
                'species_id': str(species.id),
                'species_name': species.name,
                'scientific_name': species.scientific_name,
                'family': species.family,
                'iucn_status': species.iucn_status,
                'reason': 'Soft delete - archived instead of permanent deletion'
            }
        )
        
        species.is_archived = True
        species.save()

        messages.success(request, f"Species '{species.name}' has been archived successfully.")
        return super().delete(request, *args, **kwargs)


class SpeciesArchivedListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    Display list of archived species
    
    Accessible by: ADMIN only
    """
    model = Species
    template_name = "fauna/species_archived_list.html"
    context_object_name = "species_list"
    paginate_by = 50

    def test_func(self):
        """Check if user has required permissions"""
        user = self.request.user
        if not user.is_authenticated:
            return False
        if not hasattr(user, "role"):
            return False
        return user.role == "ADMIN"

    def handle_no_permission(self):
        """Handle unauthorized access"""
        if not self.request.user.is_authenticated:
            from django.shortcuts import redirect
            from django.contrib import messages
            messages.error(self.request, "Authentication required.")
            return redirect("login")
        from django.shortcuts import render
        return render(self.request, '403.html', {'message': 'Access denied. Admin privileges required.'}, status=403)

    def get_queryset(self):
        """Return only archived species"""
        return Species.objects.filter(is_archived=True).order_by("name")

    def get_context_data(self, **kwargs):
        """Add additional context data"""
        context = super().get_context_data(**kwargs)
        context["total_archived"] = Species.objects.filter(is_archived=True).count()
        return context


class SpeciesRestoreView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Restore an archived species
    
    Accessible by: ADMIN only
    """
    model = Species
    fields = []  # No fields needed, just restore
    template_name = "fauna/species_confirm_restore.html"

    def test_func(self):
        """Check if user has required permissions"""
        user = self.request.user
        if not user.is_authenticated:
            return False
        if not hasattr(user, "role"):
            return False
        return user.role == "ADMIN"

    def handle_no_permission(self):
        """Handle unauthorized access"""
        if not self.request.user.is_authenticated:
            from django.shortcuts import redirect
            from django.contrib import messages
            messages.error(self.request, "Authentication required.")
            return redirect("login")
        from django.shortcuts import render
        return render(self.request, '403.html', {'message': 'Access denied. Admin privileges required.'}, status=403)

    def post(self, request, *args, **kwargs):
        """Restore the species"""
        species = self.get_object()
        
        # Log the activity
        UserActivity.log_activity(
            user=request.user,
            activity_type=UserActivity.ActivityType.SPECIES_UPDATED,
            description=f"Restored archived species: {species.name} ({species.scientific_name})",
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            metadata={
                'species_id': str(species.id),
                'species_name': species.name,
                'scientific_name': species.scientific_name,
                'action': 'restored_from_archive'
            }
        )
        
        species.is_archived = False
        species.save()

        messages.success(request, f"Species '{species.name}' has been restored successfully.")
        return redirect("fauna:species_archived_list")


class SpeciesSuggestionsView(LoginRequiredMixin, View):
    """
    API endpoint for smart species suggestions
    
    Accessible by: ADMIN, FIELD_WORKER
    """
    
    def get(self, request):
        """Get species suggestions based on query"""
        query = request.GET.get('q', '').strip()
        
        if not query:
            return JsonResponse({'suggestions': []})
        
        # Check user permissions
        if not hasattr(request.user, 'role') or request.user.role not in ['ADMIN', 'FIELD_WORKER']:
            return JsonResponse({'error': 'Access denied'}, status=403)
        
        # Use smart matching to get suggestions
        matcher = SpeciesMatcher()
        suggestions = matcher.get_suggestions(query, limit=10)
        
        # Format suggestions for JSON response
        formatted_suggestions = []
        for suggestion in suggestions:
            formatted_suggestions.append({
                'id': str(suggestion['name'].id),
                'name': suggestion['name'].name,
                'scientific_name': suggestion['name'].scientific_name,
                'family': suggestion['name'].family,
                'iucn_status': suggestion['name'].iucn_status,
                'score': suggestion['score'],
                'match_type': suggestion['match_type']
            })
        
        return JsonResponse({
            'suggestions': formatted_suggestions,
            'query': query,
            'total': len(formatted_suggestions)
        })


# Bird Family Management Views

class BirdFamilyListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """List all bird families"""
    model = BirdFamily
    template_name = 'fauna/family_list.html'
    context_object_name = 'families'
    paginate_by = 20

    def test_func(self):
        return self.request.user.role in ['ADMIN', 'SUPERADMIN']

    def get_queryset(self):
        queryset = BirdFamily.objects.all()
        
        # Filter by category
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        # Filter by active status
        is_active = self.request.GET.get('is_active')
        if is_active == 'true':
            queryset = queryset.filter(is_active=True)
        elif is_active == 'false':
            queryset = queryset.filter(is_active=False)
        
        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(display_name__icontains=search) |
                Q(description__icontains=search) |
                Q(scientific_name__icontains=search)
            )
        
        return queryset.order_by('category', 'display_name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = BirdFamily.FamilyCategory.choices
        context['current_category'] = self.request.GET.get('category', '')
        context['current_search'] = self.request.GET.get('search', '')
        context['current_is_active'] = self.request.GET.get('is_active', '')
        
        # Add usage statistics
        families = context['families']
        for family in families:
            family.species_count = Species.objects.filter(family=family).count()
            family.census_count = Species.objects.filter(family=family).count()
        
        return context


class BirdFamilyDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """View bird family details"""
    model = BirdFamily
    template_name = 'fauna/family_detail.html'
    context_object_name = 'family'

    def test_func(self):
        return self.request.user.role in ['ADMIN', 'SUPERADMIN']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        family = self.get_object()
        
        # Get related species
        context['species'] = Species.objects.filter(family=family).order_by('name')
        context['species_count'] = context['species'].count()
        
        return context


class BirdFamilyCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create new bird family"""
    model = BirdFamily
    form_class = BirdFamilyForm
    template_name = 'fauna/family_form.html'
    success_url = reverse_lazy('fauna:family_list')

    def test_func(self):
        return self.request.user.role in ['ADMIN', 'SUPERADMIN']

    def form_valid(self, form):
        messages.success(self.request, f'Bird family "{form.instance.display_name}" created successfully.')
        
        # Log activity
        UserActivity.objects.create(
            user=self.request.user,
            action='CREATE',
            resource_type='BIRD_FAMILY',
            resource_name=form.instance.display_name,
            details=f'Created bird family: {form.instance.name}'
        )
        
        return super().form_valid(form)


class BirdFamilyUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Update bird family"""
    model = BirdFamily
    form_class = BirdFamilyForm
    template_name = 'fauna/family_form.html'
    success_url = reverse_lazy('fauna:family_list')

    def test_func(self):
        return self.request.user.role in ['ADMIN', 'SUPERADMIN']

    def form_valid(self, form):
        messages.success(self.request, f'Bird family "{form.instance.display_name}" updated successfully.')
        
        # Log activity
        UserActivity.objects.create(
            user=self.request.user,
            action='UPDATE',
            resource_type='BIRD_FAMILY',
            resource_name=form.instance.display_name,
            details=f'Updated bird family: {form.instance.name}'
        )
        
        return super().form_valid(form)


class BirdFamilyDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete bird family"""
    model = BirdFamily
    template_name = 'fauna/family_confirm_delete.html'
    success_url = reverse_lazy('fauna:family_list')

    def test_func(self):
        return self.request.user.role in ['ADMIN', 'SUPERADMIN']

    def delete(self, request, *args, **kwargs):
        family = self.get_object()
        
        # Check if family is being used
        species_count = Species.objects.filter(family=family).count()
        if species_count > 0:
            messages.error(
                request, 
                f'Cannot delete "{family.display_name}" because it is being used by {species_count} species. '
                f'Please reassign or delete those species first.'
            )
            return redirect('fauna:family_detail', pk=family.pk)
        
        messages.success(request, f'Bird family "{family.display_name}" deleted successfully.')
        
        # Log activity
        UserActivity.objects.create(
            user=request.user,
            action='DELETE',
            resource_type='BIRD_FAMILY',
            resource_name=family.display_name,
            details=f'Deleted bird family: {family.name}'
        )
        
        return super().delete(request, *args, **kwargs)
