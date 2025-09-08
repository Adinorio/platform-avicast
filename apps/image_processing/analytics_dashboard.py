"""
Analytics Dashboard Views
Main dashboard and statistics views for model performance analytics
"""

import json
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Max, Min, Q
from django.http import JsonResponse
from django.shortcuts import redirect, render

logger = logging.getLogger(__name__)

try:
    from .analytics_config import (
        ANALYTICS_CONFIG,
        get_available_models,
        get_target_species,
    )
    from .analytics_models import ModelEvaluationRun
    from .analytics_service import ModelAnalyticsService
    from .models import ImageProcessingResult
except ImportError as e:
    logger.warning(f"Analytics components not available: {e}")


@login_required
def analytics_dashboard(request):
    """
    Enhanced Model Performance Analytics Dashboard
    Advanced MLOps metrics for thesis analysis with improved filtering
    """
    if not request.user.can_access_feature("image_processing"):
        messages.error(request, "You don't have permission to access analytics.")
        return redirect("image_processing:list")

    # Get filtering parameters
    model_filter = request.GET.getlist("model")
    species_filter = request.GET.getlist("species")
    date_start = request.GET.get("date_start")
    date_end = request.GET.get("date_end")
    review_status_filter = request.GET.getlist("review_status")
    confidence_min = request.GET.get("confidence_min")
    confidence_max = request.GET.get("confidence_max")

    # Get available models for filtering (dynamic)
    available_models = get_available_models()

    # Get recent evaluation runs
    recent_runs = ModelEvaluationRun.objects.filter(status="COMPLETED").order_by("-created_at")[
        : ANALYTICS_CONFIG["RECENT_RUNS_LIMIT"]
    ]

    # Base query for processed images
    processed_query = ImageProcessingResult.objects.filter(
        processing_status=ImageProcessingResult.ProcessingStatus.COMPLETED
    )

    # Apply filters
    if model_filter:
        processed_query = processed_query.filter(ai_model__in=model_filter)
    if species_filter:
        processed_query = processed_query.filter(detected_species__in=species_filter)
    if date_start:
        processed_query = processed_query.filter(created_at__date__gte=date_start)
    if date_end:
        processed_query = processed_query.filter(created_at__date__lte=date_end)
    if review_status_filter:
        processed_query = processed_query.filter(review_status__in=review_status_filter)
    if confidence_min:
        processed_query = processed_query.filter(confidence_score__gte=float(confidence_min))
    if confidence_max:
        processed_query = processed_query.filter(confidence_score__lte=float(confidence_max))

    # Get enhanced statistics
    total_processed_images = processed_query.count()

    total_approved_results = processed_query.filter(
        review_status__in=[
            ImageProcessingResult.ReviewStatus.APPROVED,
            ImageProcessingResult.ReviewStatus.OVERRIDDEN,
        ]
    ).count()

    total_rejected_results = processed_query.filter(
        review_status=ImageProcessingResult.ReviewStatus.REJECTED
    ).count()

    # Enhanced model usage statistics with performance metrics
    model_usage = (
        processed_query.values("ai_model")
        .annotate(
            count=Count("id"),
            avg_confidence=Avg("confidence_score"),
            avg_inference_time=Avg("inference_time"),
            approved_count=Count(
                "id",
                filter=Q(
                    review_status__in=[
                        ImageProcessingResult.ReviewStatus.APPROVED,
                        ImageProcessingResult.ReviewStatus.OVERRIDDEN,
                    ]
                ),
            ),
            rejected_count=Count(
                "id", filter=Q(review_status=ImageProcessingResult.ReviewStatus.REJECTED)
            ),
        )
        .order_by("-count")
    )

    # Calculate approval rates for each model and convert Decimals to float
    for model in model_usage:
        total = model["count"]
        approved = model["approved_count"]
        model["approval_rate"] = (approved / total * 100) if total > 0 else 0
        model["rejection_rate"] = (model["rejected_count"] / total * 100) if total > 0 else 0

        # Convert Decimal fields to float for JavaScript compatibility
        if model.get("avg_confidence") is not None:
            model["avg_confidence"] = float(model["avg_confidence"])
        if model.get("avg_inference_time") is not None:
            model["avg_inference_time"] = float(model["avg_inference_time"])

    # Enhanced species detection statistics
    species_stats = []
    target_species = get_target_species()
    for species in target_species:
        species_results = processed_query.filter(detected_species=species)
        total_count = species_results.count()
        approved_count = species_results.filter(
            review_status__in=[
                ImageProcessingResult.ReviewStatus.APPROVED,
                ImageProcessingResult.ReviewStatus.OVERRIDDEN,
            ]
        ).count()
        avg_confidence = (
            species_results.aggregate(avg_conf=Avg("confidence_score"))["avg_conf"] or 0
        )

        species_stats.append(
            {
                "name": species,
                "total_count": total_count,
                "approved_count": approved_count,
                "approval_rate": (approved_count / total_count * 100) if total_count > 0 else 0,
                "avg_confidence": avg_confidence,
            }
        )

    # Available filter options
    available_species = ImageProcessingResult.objects.values_list(
        "detected_species", flat=True
    ).distinct()
    available_review_statuses = ImageProcessingResult.ReviewStatus.choices

    # Confidence statistics for threshold optimization
    confidence_stats = processed_query.aggregate(
        min_confidence=Min("confidence_score"),
        max_confidence=Max("confidence_score"),
        avg_confidence=Avg("confidence_score"),
    )

    # Processing performance metrics
    performance_stats = processed_query.aggregate(
        avg_inference_time=Avg("inference_time"),
        min_inference_time=Min("inference_time"),
        max_inference_time=Max("inference_time"),
        total_processed_results=Count("id"),
    )

    # Calculate average detections per image separately to avoid aggregate conflict
    detections_data = processed_query.values_list("total_detections", flat=True)
    avg_detections = (
        sum(d for d in detections_data if d is not None) / len(detections_data)
        if detections_data
        else 0
    )
    performance_stats["avg_detections_per_image"] = avg_detections

    # Convert Decimal objects to float for JavaScript compatibility
    for stat in species_stats:
        if "avg_confidence" in stat and stat["avg_confidence"]:
            stat["avg_confidence"] = float(stat["avg_confidence"])

    # Convert confidence stats to float
    for key, value in confidence_stats.items():
        if value is not None:
            confidence_stats[key] = float(value)

    # Convert performance stats to float
    for key, value in performance_stats.items():
        if value is not None and hasattr(value, "__float__"):
            performance_stats[key] = float(value)

    context = {
        "available_models": available_models,
        "available_species": [s for s in available_species if s],
        "available_review_statuses": available_review_statuses,
        "recent_runs": recent_runs,
        "total_processed_images": total_processed_images,
        "total_approved_results": total_approved_results,
        "total_rejected_results": total_rejected_results,
        "model_usage": model_usage,
        "species_stats": species_stats,
        "target_species": target_species,
        "confidence_stats": confidence_stats,
        "performance_stats": performance_stats,
        # Current filter values
        "current_filters": {
            "model": model_filter,
            "species": species_filter,
            "date_start": date_start,
            "date_end": date_end,
            "review_status": review_status_filter,
            "confidence_min": confidence_min,
            "confidence_max": confidence_max,
        },
    }

    return render(request, "image_processing/analytics_dashboard.html", context)


@login_required
def image_selection_view(request):
    """
    View for selecting specific images for evaluation runs
    """
    if not request.user.can_access_feature("image_processing"):
        messages.error(request, "You don't have permission to access analytics.")
        return redirect("image_processing:list")

    # Get filtering parameters
    model_filter = request.GET.getlist("model")
    species_filter = request.GET.getlist("species")
    review_status_filter = request.GET.getlist("review_status")
    date_start = request.GET.get("date_start")
    date_end = request.GET.get("date_end")

    # Base query for processed images
    results_query = ImageProcessingResult.objects.filter(
        processing_status=ImageProcessingResult.ProcessingStatus.COMPLETED
    ).select_related("image_upload")

    # Apply filters
    if model_filter:
        results_query = results_query.filter(ai_model__in=model_filter)
    if species_filter:
        results_query = results_query.filter(detected_species__in=species_filter)
    if review_status_filter:
        results_query = results_query.filter(review_status__in=review_status_filter)
    if date_start:
        results_query = results_query.filter(created_at__date__gte=date_start)
    if date_end:
        results_query = results_query.filter(created_at__date__lte=date_end)

    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(results_query, 24)  # 24 images per page for grid display
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Available filter options
    available_models = get_available_models()
    available_species = ImageProcessingResult.objects.values_list(
        "detected_species", flat=True
    ).distinct()
    available_review_statuses = ImageProcessingResult.ReviewStatus.choices

    context = {
        "page_obj": page_obj,
        "available_models": available_models,
        "available_species": [s for s in available_species if s],
        "available_review_statuses": available_review_statuses,
        "current_filters": {
            "model": model_filter,
            "species": species_filter,
            "review_status": review_status_filter,
            "date_start": date_start,
            "date_end": date_end,
        },
        "total_images": results_query.count(),
    }

    return render(request, "image_processing/image_selection.html", context)
