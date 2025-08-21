from django.urls import path
from . import views

app_name = 'image_processing'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('upload/', views.upload_view, name='upload'),
    path('process/', views.process_view, name='process'),
    path('process/<uuid:batch_id>/', views.process_view, name='process_batch'),
    path('process/start/', views.start_processing, name='start_processing'),
    path('review/', views.review_view, name='review'),
    path('review/approve/<int:result_id>/', views.approve_result, name='approve_result'),
    path('review/reject/<int:result_id>/', views.reject_result, name='reject_result'),
    path('allocate/', views.allocate_view, name='allocate'),
    path('allocate/census/', views.allocate_to_census, name='allocate_to_census'),
]
