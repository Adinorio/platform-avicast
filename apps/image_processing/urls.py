from django.urls import path
from . import views, analytics_views

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
    path('api/batch-process/', views.api_batch_process, name='api_batch_process'),
    path('api/progress/<uuid:image_id>/', views.api_progress, name='api_progress'),
    path('api/get-progress/', views.api_get_progress, name='api_get_progress'),
    path('api/clear-upload-results/', views.clear_upload_results, name='clear_upload_results'),
    
    # Review actions
    path('api/approve-result/<uuid:result_id>/', views.approve_result, name='approve_result'),
    path('api/reject-result/<uuid:result_id>/', views.reject_result, name='reject_result'),
    path('api/override-result/<uuid:result_id>/', views.override_result, name='override_result'),
    
    # AI Model management
    path('models/', views.model_selection_view, name='model_selection'),
    path('models/benchmark/', views.benchmark_models_view, name='benchmark_models'),
    
    # Ground truth annotation
    path('annotate/<uuid:pk>/', views.annotation_view, name='annotate'),
    path('api/save-annotations/<uuid:pk>/', views.save_annotations, name='save_annotations'),
    path('species-management/', views.species_management_view, name='species_management'),
    path('api/species-management/', views.api_species_management, name='api_species_management'),
    
    # Model Performance Analytics (MLOps)
    path('analytics/', analytics_views.analytics_dashboard, name='analytics_dashboard'),
    path('analytics/select-images/', analytics_views.image_selection_view, name='image_selection'),
    path('analytics/runs/', analytics_views.evaluation_runs_list, name='evaluation_runs_list'),
    path('analytics/results/<uuid:run_id>/', analytics_views.evaluation_results, name='evaluation_results'),
    path('analytics/comparison/', analytics_views.model_comparison, name='model_comparison'),
    path('analytics/reviewed/', analytics_views.reviewed_analytics_view, name='reviewed_analytics'),
    
    # Analytics API endpoints
    path('api/evaluation/create/', analytics_views.create_evaluation_run, name='create_evaluation_run'),
    path('api/evaluation/status/<uuid:run_id>/', analytics_views.api_evaluation_status, name='api_evaluation_status'),
    path('api/evaluation/delete/<uuid:run_id>/', analytics_views.delete_evaluation_run, name='delete_evaluation_run'),
    path('api/evaluation/kfold/', analytics_views.api_kfold_evaluation, name='api_kfold_evaluation'),
    path('api/analytics/reviewed-summary/', analytics_views.api_reviewed_summary, name='api_reviewed_summary'),
    
    # Debug
    path('debug-form/', views.debug_form_view, name='debug_form'),

    # Health Monitoring
    path('health/', views.health_status_view, name='health_status'),
]
