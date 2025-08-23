from django.urls import path
from . import views

app_name = 'image_processing'

urlpatterns = [
    # Main views
    path('', views.dashboard_view, name='dashboard'),  # Add dashboard as root
    path('upload/', views.image_upload_view, name='upload'),
    path('list/', views.image_list_view, name='list'),
    path('detail/<uuid:pk>/', views.image_detail_view, name='detail'),
    
    # Processing and review
    path('review/', views.review_view, name='review'),
    path('process-batch/<uuid:pk>/', views.process_batch_view, name='process_batch'),
    path('allocate/', views.allocate_view, name='allocate'),
    
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
    path('api/clear-upload-results/', views.clear_upload_results, name='clear_upload_results'),
    
    # Review actions
    path('api/approve-result/<uuid:result_id>/', views.approve_result, name='approve_result'),
    path('api/reject-result/<uuid:result_id>/', views.reject_result, name='reject_result'),
    path('api/override-result/<uuid:result_id>/', views.override_result, name='override_result'),
]
