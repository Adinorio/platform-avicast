"""
GTD-based Image Processing URLs
Following Getting Things Done methodology for workflow management

CAPTURE → CLARIFY → ORGANIZE → REFLECT → ENGAGE
"""

from django.urls import path
from .views import (
    dashboard, upload_images, process_images, start_processing,
    review_results, allocate_results, ImageListView, model_selection, benchmark_models
)

app_name = "image_processing"

urlpatterns = [
    # Dashboard - Workflow overview
    path("", dashboard, name="dashboard"),

    # CAPTURE Stage - Upload images
    path("upload/", upload_images, name="upload"),
    path("list/", ImageListView.as_view(), name="list"),

    # CLARIFY Stage - Process images with AI
    path("process/", process_images, name="process"),
    path("process/<uuid:image_id>/", start_processing, name="start_processing"),

    # REFLECT Stage - Review AI results
    path("review/", review_results, name="review"),

    # ENGAGE Stage - Allocate to census data
    path("allocate/", allocate_results, name="allocate"),
    
    # Model Management
    path("models/", model_selection, name="model_selection"),
    path("benchmark/", benchmark_models, name="benchmark_models"),
]

