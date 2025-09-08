"""
Analytics Comparison Views
Views for comparing models side by side
"""

import json
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

logger = logging.getLogger(__name__)

try:
    from .analytics_config import (
        ANALYTICS_CONFIG,
        UI_TEXT,
        get_admin_roles,
        get_available_models,
        get_model_file_size,
    )
    from .analytics_models import ModelEvaluationRun
    from .analytics_service import ModelAnalyticsService
except ImportError as e:
    logger.warning(f"Analytics components not available: {e}")


@login_required
def model_comparison(request):
    """
    Compare multiple models side by side
    """
    if not request.user.can_access_feature("image_processing"):
        messages.error(request, "You don't have permission to access analytics.")
        return redirect("image_processing:list")

    # Get model comparison data from recent completed runs
    recent_run = (
        ModelEvaluationRun.objects.filter(status="COMPLETED").order_by("-created_at").first()
    )

    comparison_data = []
    model_metrics = []

    if recent_run:
        model_metrics = recent_run.model_metrics.all().order_by("-f1_score")

        for metrics in model_metrics:
            # Get model file size if available
            model_size = None
            model_params = None

            # Try to get model file size from filesystem
            model_size = get_model_file_size(metrics.model_name)

            comparison_data.append(
                {
                    "model_name": metrics.model_name,
                    "precision": float(metrics.precision) if metrics.precision else 0,
                    "recall": float(metrics.recall) if metrics.recall else 0,
                    "f1_score": float(metrics.f1_score) if metrics.f1_score else 0,
                    "map_50": float(metrics.map_50) if metrics.map_50 else 0,
                    "avg_inference_time_ms": float(metrics.avg_inference_time_ms)
                    if metrics.avg_inference_time_ms
                    else 0,
                    "images_processed": metrics.images_processed,
                    "true_positives": metrics.true_positives,
                    "false_positives": metrics.false_positives,
                    "false_negatives": metrics.false_negatives,
                    "model_size_mb": round(model_size, 1) if model_size else None,
                    "model_parameters_millions": float(metrics.model_parameters_millions)
                    if metrics.model_parameters_millions
                    else None,
                }
            )

    # Create performance radar chart data
    radar_data = {
        "labels": ["Precision", "Recall", "F1-Score", "mAP@0.5", "Speed (1/ms)"],
        "datasets": [],
    }

    for i, data in enumerate(comparison_data[: ANALYTICS_CONFIG["RADAR_CHART_LIMIT"]]):
        speed_score = (
            1000 / data["avg_inference_time_ms"] if data["avg_inference_time_ms"] > 0 else 0
        )
        speed_normalized = min(speed_score / ANALYTICS_CONFIG["SPEED_NORMALIZATION_FACTOR"], 1.0)

        radar_data["datasets"].append(
            {
                "label": data["model_name"],
                "data": [
                    data["precision"],
                    data["recall"],
                    data["f1_score"],
                    data["map_50"],
                    speed_normalized,
                ],
                "backgroundColor": ANALYTICS_CONFIG["CHART_COLORS"][
                    i % len(ANALYTICS_CONFIG["CHART_COLORS"])
                ]
                + "40",
                "borderColor": ANALYTICS_CONFIG["CHART_COLORS"][
                    i % len(ANALYTICS_CONFIG["CHART_COLORS"])
                ],
                "borderWidth": 2,
            }
        )

    context = {
        "comparison_data": comparison_data,
        "radar_chart_data": json.dumps(radar_data),
        "recent_run": recent_run,
        "total_models": len(comparison_data),
        "best_overall_model": comparison_data[0] if comparison_data else None,
        "fastest_model": min(comparison_data, key=lambda x: x["avg_inference_time_ms"])
        if comparison_data
        else None,
        "most_accurate_model": max(comparison_data, key=lambda x: x["map_50"])
        if comparison_data
        else None,
    }

    return render(request, "image_processing/model_comparison.html", context)


@login_required
def reviewed_analytics_view(request):
    """Display analytics based on human-reviewed processing results."""
    if not request.user.can_access_feature("image_processing"):
        messages.error(request, "You don't have permission to access analytics.")
        return redirect("image_processing:list")

    try:
        service = ModelAnalyticsService()
        performance_summary = service.summarize_model_performance_from_reviews()

        context = {
            "summary": performance_summary,
        }
        return render(request, "image_processing/reviewed_analytics.html", context)
    except Exception as e:
        logger.error(f"Error in reviewed analytics: {e}")
        context = {
            "summary": None,
            "error": "Unable to generate reviewed analytics at this time.",
        }
        return render(request, "image_processing/reviewed_analytics.html", context)
