from django.urls import path
from . import views

app_name = 'image_processing'

urlpatterns = [
    path('', views.ImageProcessingDashboardView.as_view(), name='dashboard'),
    path('upload/', views.ImageUploadView.as_view(), name='upload'),
    path('process/', views.ProcessDataView.as_view(), name='process'),
    path('review/', views.ReviewView.as_view(), name='review'),
    path('allocate/', views.AllocateView.as_view(), name='allocate'),
]
