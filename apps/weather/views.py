from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from apps.users.decorators import role_required

class WeatherDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'weather/dashboard.html'
    
    @method_decorator(role_required(['ADMIN', 'FIELD_WORKER']))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

class ForecastView(LoginRequiredMixin, TemplateView):
    template_name = 'weather/forecast.html'
    
    @method_decorator(role_required(['ADMIN', 'FIELD_WORKER']))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

class ScheduleView(LoginRequiredMixin, TemplateView):
    template_name = 'weather/schedule.html'
    
    @method_decorator(role_required(['ADMIN']))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

class AlertsView(LoginRequiredMixin, TemplateView):
    template_name = 'weather/alerts.html'
    
    @method_decorator(role_required(['ADMIN']))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
