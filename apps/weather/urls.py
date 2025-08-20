from django.urls import path
from . import views

app_name = 'weather'

urlpatterns = [
    path('', views.WeatherDashboardView.as_view(), name='dashboard'),
    path('forecast/', views.ForecastView.as_view(), name='forecast'),
    path('schedule/', views.ScheduleView.as_view(), name='schedule'),
    path('alerts/', views.AlertsView.as_view(), name='alerts'),
]
