from django.urls import path
from . import views

app_name = 'image_processing'

urlpatterns = [
    # Main views
    path('upload/', views.image_upload_view, name='upload'),
    path('list/', views.image_list_view, name='list'),
    path('detail/<uuid:pk>/', views.image_detail_view, name='detail'),
    
    # Storage management
    path('storage/status/', views.storage_status_view, name='storage_status'),
    path('storage/cleanup/', views.storage_cleanup_view, name='storage_cleanup'),
    
    # Image management
    path('delete/<uuid:pk>/', views.image_delete_view, name='delete'),
    path('restore/<uuid:pk>/', views.restore_archived_image, name='restore'),
    
    # API endpoints
    path('api/upload-progress/', views.api_upload_progress, name='api_upload_progress'),
    path('api/storage-stats/', views.api_storage_stats, name='api_storage_stats'),
    path('api/search/', views.api_image_search, name='api_search'),
]
