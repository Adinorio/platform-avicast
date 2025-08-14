from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.contrib import messages
from .models import Site

class SiteListView(LoginRequiredMixin, ListView):
    """Display list of all observation sites"""
    model = Site
    template_name = 'locations/site_list.html'
    context_object_name = 'sites'
    paginate_by = 10
    
    def get_queryset(self):
        """Filter sites based on user role"""
        if self.request.user.role == 'SUPERADMIN':
            # Superadmin should not see sites - redirect to admin
            return Site.objects.none()
        elif self.request.user.role == 'ADMIN':
            # Admin sees all sites
            return Site.objects.filter(is_archived=False).order_by('name')
        else:
            # Field Worker sees all sites (view only)
            return Site.objects.filter(is_archived=False).order_by('name')

class SiteDetailView(LoginRequiredMixin, DetailView):
    """Display detailed information about a specific site"""
    model = Site
    template_name = 'locations/site_detail.html'
    context_object_name = 'site'
    
    def get_queryset(self):
        """Filter sites based on user role"""
        if self.request.user.role == 'SUPERADMIN':
            return Site.objects.none()
        return Site.objects.filter(is_archived=False)

class SiteCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Create a new observation site - Admin only"""
    model = Site
    template_name = 'locations/site_form.html'
    fields = ['name', 'location_desc', 'image']
    permission_required = 'locations.add_site'
    
    def form_valid(self, form):
        """Set success message and redirect"""
        messages.success(self.request, f'Site "{form.instance.name}" created successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('locations:site_list')

class SiteUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Edit an existing observation site - Admin only"""
    model = Site
    template_name = 'locations/site_form.html'
    fields = ['name', 'location_desc', 'image']
    permission_required = 'locations.change_site'
    
    def form_valid(self, form):
        """Set success message and redirect"""
        messages.success(self.request, f'Site "{form.instance.name}" updated successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('locations:site_list')

class SiteDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """Delete an observation site - Admin only"""
    model = Site
    template_name = 'locations/site_confirm_delete.html'
    permission_required = 'locations.delete_site'
    success_url = reverse_lazy('locations:site_list')
    
    def delete(self, request, *args, **kwargs):
        """Soft delete by setting is_archived=True"""
        site = self.get_object()
        site.is_archived = True
        site.save()
        messages.success(request, f'Site "{site.name}" archived successfully!')
        return redirect(self.success_url)

class SiteArchiveView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Archive/Unarchive a site - Admin only"""
    model = Site
    fields = ['is_archived']
    permission_required = 'locations.change_site'
    http_method_names = ['post']  # Only allow POST requests
    
    def post(self, request, *args, **kwargs):
        site = self.get_object()
        site.is_archived = not site.is_archived
        site.save()
        
        action = "archived" if site.is_archived else "unarchived"
        messages.success(request, f'Site "{site.name}" {action} successfully!')
        
        return redirect('locations:site_list')
