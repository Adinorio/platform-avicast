"""
Dashboard views for analytics app
"""

import os

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.shortcuts import render

from apps.image_processing.permissions import staff_required
from apps.locations.models import CensusObservation, Site, SpeciesObservation


@login_required
@staff_required
def analytics_dashboard(request):
    """
    Main analytics dashboard displaying overview charts and statistics.

    Shows total sites, census observations, species count, bird population,
    recent activity, top sites by diversity, and available AI models.
    """

    # Get basic statistics
    total_sites = Site.objects.count()
    total_census = CensusObservation.objects.count()
    total_species = SpeciesObservation.objects.values("species_name").distinct().count()
    total_birds = SpeciesObservation.objects.aggregate(total=Sum("count"))["total"] or 0

    # Get recent activity
    recent_census = CensusObservation.objects.order_by("-observation_date")[:5]

    # Get top sites by species diversity
    top_sites = Site.objects.annotate(
        species_count=Count(
            "census_observations__species_observations__species_name", distinct=True
        )
    ).order_by("-species_count")[:5]

    # Get AI model information
    models_dir = "models"
    yolov5_models = []
    yolov8_models = []
    yolov9_models = []

    if os.path.exists(models_dir):
        for filename in os.listdir(models_dir):
            if filename.endswith(".pt"):
                file_path = os.path.join(models_dir, filename)
                file_size = os.path.getsize(file_path)
                size_mb = f"{file_size / (1024 * 1024):.1f}MB"

                if filename.startswith("yolov5"):
                    yolov5_models.append(
                        {"name": filename.replace(".pt", ""), "size": size_mb, "filename": filename}
                    )
                elif filename.startswith("yolov8"):
                    yolov8_models.append(
                        {"name": filename.replace(".pt", ""), "size": size_mb, "filename": filename}
                    )
                elif filename.startswith("yolov9"):
                    yolov9_models.append(
                        {"name": filename.replace(".pt", ""), "size": size_mb, "filename": filename}
                    )

    # Sort models by name
    yolov5_models.sort(key=lambda x: x["name"])
    yolov8_models.sort(key=lambda x: x["name"])
    yolov9_models.sort(key=lambda x: x["name"])

    context = {
        "total_sites": total_sites,
        "total_census": total_census,
        "total_species": total_species,
        "total_birds": total_birds,
        "recent_census": recent_census,
        "top_sites": top_sites,
        "yolov5_models": yolov5_models,
        "yolov8_models": yolov8_models,
        "yolov9_models": yolov9_models,
    }

    return render(request, "analytics/dashboard.html", context)


@login_required
@staff_required
def chart_gallery(request):
    """Display gallery of available charts"""

    # Get available chart types
    chart_types = [
        {
            "name": "Species Diversity",
            "type": "bar",
            "description": "Compare species diversity across different sites",
            "endpoint": "analytics:species_diversity_chart",
        },
        {
            "name": "Population Trends",
            "type": "line",
            "description": "Track bird population changes over time",
            "endpoint": "analytics:population_trends_chart",
        },
        {
            "name": "Seasonal Analysis",
            "type": "heatmap",
            "description": "Analyze seasonal patterns in bird activity",
            "endpoint": "analytics:seasonal_analysis_chart",
        },
        {
            "name": "Site Comparison",
            "type": "radar",
            "description": "Compare multiple sites across different metrics",
            "endpoint": "analytics:site_comparison_chart",
        },
    ]

    context = {"chart_types": chart_types}

    return render(request, "analytics/chart_gallery.html", context)
