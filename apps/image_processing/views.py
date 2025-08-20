from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from apps.users.decorators import role_required

class ImageProcessingDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'image_processing/dashboard.html'
    
    @method_decorator(role_required(['ADMIN', 'FIELD_WORKER']))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

class ImageUploadView(LoginRequiredMixin, TemplateView):
    template_name = 'image_processing/upload.html'
    
    @method_decorator(role_required(['ADMIN', 'FIELD_WORKER']))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

class ProcessDataView(LoginRequiredMixin, TemplateView):
    template_name = 'image_processing/process.html'
    
    @method_decorator(role_required(['ADMIN', 'FIELD_WORKER']))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

class ReviewView(LoginRequiredMixin, TemplateView):
    template_name = 'image_processing/review.html'
    
    @method_decorator(role_required(['ADMIN']))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

class AllocateView(LoginRequiredMixin, TemplateView):
    template_name = 'image_processing/allocate.html'
    
    @method_decorator(role_required(['ADMIN']))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
