from django.urls import path
from . import views

app_name = 'weather'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('fetch/', views.fetch_weather, name='fetch_weather'),
    path('optimize/', views.optimize_field_work, name='optimize_field_work'),
    path('forecast/', views.forecast_view, name='forecast'),
    path('forecast/<int:site_id>/', views.forecast_view, name='site_forecast'),
    path('schedule/', views.schedule_view, name='schedule'),
    path('schedule/create/', views.create_schedule, name='create_schedule'),
    path('alerts/', views.alerts_view, name='alerts'),
]
