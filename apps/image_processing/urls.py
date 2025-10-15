"""
GTD-based Image Processing URLs
Following Getting Things Done methodology for workflow management

CAPTURE → CLARIFY → ORGANIZE → REFLECT → ENGAGE
"""

from django.urls import path
from .views import (
    dashboard, upload_images, process_images, start_processing,
    review_results, allocate_results, ImageListView, model_selection, benchmark_models, image_with_bbox, cache_reset,
    get_years_for_site, get_months_for_site_year
)

app_name = "image_processing"

urlpatterns = [
    # Dashboard - Workflow overview
    path("", dashboard, name="dashboard"),
    path("dashboard/", dashboard, name="dashboard_explicit"),

    # CAPTURE Stage - Upload images
    path("upload/", upload_images, name="upload"),
    path("list/", ImageListView.as_view(), name="list"),

    # CLARIFY Stage - Process images with AI
    path("process/", process_images, name="process"),
    path("process/<uuid:image_id>/", start_processing, name="start_processing"),

    # REFLECT Stage - Review AI results
    path("review/", review_results, name="review"),
    path("image-with-bbox/<uuid:result_id>/", image_with_bbox, name="image_with_bbox"),

    # ENGAGE Stage - Allocate to census data
    path("allocate/", allocate_results, name="allocate"),
    path("allocate/site/<uuid:site_id>/years/", get_years_for_site, name="get_years_for_site"),
    path("allocate/site/<uuid:site_id>/year/<int:year>/months/", get_months_for_site_year, name="get_months_for_site_year"),

    # Cache Management
    path("cache-reset/", cache_reset, name="cache_reset"),

    # Model Management
    path("models/", model_selection, name="model_selection"),
    path("benchmark/", benchmark_models, name="benchmark_models"),
]

