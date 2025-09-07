"""
Model Performance Analytics Views
Advanced dashboard for YOLO model comparison and thesis analysis
"""

import json
import logging
from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Avg, Count, Max, Min, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

logger = logging.getLogger(__name__)

from .analytics_config import (
    ANALYTICS_CONFIG,
    UI_TEXT,
    get_admin_roles,
    get_available_models,
    get_confusion_matrix_species,
    get_date_filter_days,
    get_helpful_tips,
    get_model_file_size,
    get_target_species,
    log_debug,
)
from .analytics_models import (
    ModelEvaluationRun,
)
from .analytics_service import ModelAnalyticsService
from .models import ImageProcessingResult, ImageUpload


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


@login_required
@csrf_exempt
def create_evaluation_run(request):
    """
    Create and execute a new model evaluation run with optional image selection
    """
    if request.method != "POST":
        return JsonResponse(
            {
                "error": "Method not allowed. This endpoint only accepts POST requests.",
                "message": "To start an evaluation run, please use the form on the analytics dashboard.",
                "redirect_url": reverse("image_processing:analytics_dashboard"),
            },
            status=405,
        )

    if not request.user.can_access_feature("image_processing"):
        return JsonResponse({"error": "Access denied"}, status=403)

    try:
        log_debug(f"Request body: {request.body}")
        data = json.loads(request.body)
        log_debug(f"Parsed data: {data}")

        # Validate that we have either filters or selected images
        models = data.get("models", [])
        species = data.get("species", [])
        selected_images = data.get("selected_images", [])

        if not models and not species and not selected_images:
            return JsonResponse(
                {
                    "error": "Please specify at least one model, species filter, or select specific images"
                },
                status=400,
            )

        # Create evaluation run with enhanced configuration
        evaluation_run = ModelEvaluationRun.objects.create(
            name=data.get("name", f"Evaluation Run {timezone.now().strftime('%Y-%m-%d %H:%M')}"),
            description=data.get("description", ""),
            created_by=request.user,
            iou_threshold=data.get("iou_threshold", ANALYTICS_CONFIG["DEFAULT_IOU_THRESHOLD"]),
            confidence_threshold=data.get(
                "confidence_threshold", ANALYTICS_CONFIG["DEFAULT_CONFIDENCE_THRESHOLD"]
            ),
            models_evaluated=models,
            species_filter=species,
        )

        # Parse date range if provided
        date_range = None
        if data.get("date_start") and data.get("date_end"):
            date_start = datetime.fromisoformat(data["date_start"].replace("Z", "+00:00"))
            date_end = datetime.fromisoformat(data["date_end"].replace("Z", "+00:00"))
            evaluation_run.date_range_start = date_start
            evaluation_run.date_range_end = date_end
            evaluation_run.save()
            date_range = (date_start, date_end)

        # Store selected images if provided
        if selected_images:
            # Store selected image IDs in the evaluation run for targeted evaluation
            # Add a new field to store selected image IDs
            evaluation_run.description += (
                f"\nSelected {len(selected_images)} specific images for evaluation."
            )
            evaluation_run.save()

        # Preview the images that will be evaluated
        from .real_evaluation_workflow import RealEvaluationWorkflow

        workflow = RealEvaluationWorkflow()
        temp_eval_run = evaluation_run  # Use the created run for preview

        # Get the images that would be evaluated
        preview_images = workflow._get_images_for_evaluation(temp_eval_run)

        # Start the actual evaluation
        workflow.start_evaluation(evaluation_run)

        return JsonResponse(
            {
                "success": True,
                "evaluation_run_id": str(evaluation_run.id),
                "preview_image_count": len(preview_images),
                "redirect_url": f"/image-processing/analytics/results/{evaluation_run.id}/",
                "message": f"Evaluation started with {len(preview_images)} images",
            }
        )

    except Exception as e:
        return JsonResponse({"error": f"Failed to create evaluation run: {str(e)}"}, status=500)


@login_required
def evaluation_results(request, run_id):
    """
    Display detailed results for a specific evaluation run
    """
    if not request.user.can_access_feature("image_processing"):
        messages.error(request, "You don't have permission to access analytics.")
        return redirect("image_processing:list")

    evaluation_run = get_object_or_404(ModelEvaluationRun, id=run_id)

    # Get model performance metrics
    model_metrics = evaluation_run.model_metrics.all().order_by("-f1_score")

    # Get species performance for the best model
    best_model = model_metrics.first()
    species_metrics = []
    if best_model:
        species_metrics = best_model.species_metrics.all().order_by("species_name")

    # Get confusion matrix data
    confusion_data = []
    species_names = get_confusion_matrix_species()

    # Initialize confusion matrix
    confusion_matrix = {}
    for actual in species_names:
        confusion_matrix[actual] = {}
        for predicted in species_names:
            confusion_matrix[actual][predicted] = 0

    # Populate confusion matrix from image results
    for image_result in evaluation_run.image_results.all():
        # Count true positives
        for match in image_result.matches:
            actual_species = match["ground_truth"]["species"]
            predicted_species = match["prediction"]["species"]
            confusion_matrix[actual_species][predicted_species] += 1

        # Count false positives (predictions with no match)
        for fp_pred in image_result.unmatched_predictions:
            predicted_species = fp_pred["species"]
            confusion_matrix["Background"][predicted_species] += 1

        # Count false negatives (ground truth with no match)
        for fn_gt in image_result.unmatched_ground_truth:
            actual_species = fn_gt["species"]
            confusion_matrix[actual_species]["Background"] += 1

    # Prepare chart data for visualization
    precision_recall_data = []
    for metrics in model_metrics:
        precision_recall_data.append(
            {
                "model": metrics.model_name,
                "precision": float(metrics.precision) if metrics.precision else 0,
                "recall": float(metrics.recall) if metrics.recall else 0,
                "f1_score": float(metrics.f1_score) if metrics.f1_score else 0,
                "map_50": float(metrics.map_50) if metrics.map_50 else 0,
            }
        )

    # Get performance over time (if multiple runs exist)
    historical_runs = ModelEvaluationRun.objects.filter(
        status="COMPLETED",
        created_at__gte=timezone.now() - timedelta(days=ANALYTICS_CONFIG["HISTORICAL_DATA_DAYS"]),
    ).order_by("created_at")

    performance_timeline = []
    for run in historical_runs:
        if run.overall_map_50:
            performance_timeline.append(
                {
                    "date": run.created_at.strftime("%Y-%m-%d"),
                    "map_50": float(run.overall_map_50),
                    "run_name": run.name,
                }
            )

    # Get sample failure cases for analysis
    failure_cases = evaluation_run.image_results.filter(
        image_recall__lt=ANALYTICS_CONFIG["FAILURE_RECALL_THRESHOLD"]
    ).order_by("image_recall")[: ANALYTICS_CONFIG["FAILURE_CASES_LIMIT"]]

    # Generate comprehensive performance report for thesis
    thesis_report = None
    statistical_analysis = None
    try:
        service = ModelAnalyticsService()
        thesis_report = service.generate_performance_report(
            evaluation_run, include_statistical_analysis=True
        )

        # Convert Decimal objects to float for JavaScript compatibility
        if thesis_report:
            # Convert model performance metrics
            for model in thesis_report.get("model_performance", []):
                for key, value in model.items():
                    if hasattr(value, "__float__") and hasattr(
                        value, "as_tuple"
                    ):  # Check if it's a Decimal
                        model[key] = float(value)

            # Convert species performance metrics
            for species in thesis_report.get("species_performance", []):
                for key, value in species.items():
                    if hasattr(value, "__float__") and hasattr(
                        value, "as_tuple"
                    ):  # Check if it's a Decimal
                        species[key] = float(value)

            # Convert overall metrics
            for key, value in thesis_report.get("overall_metrics", {}).items():
                if hasattr(value, "__float__") and hasattr(
                    value, "as_tuple"
                ):  # Check if it's a Decimal
                    thesis_report["overall_metrics"][key] = float(value)

        # Extract statistical analysis if available
        if "statistical_analysis" in thesis_report:
            statistical_analysis = thesis_report["statistical_analysis"]

    except Exception as e:
        logger.error(f"Error generating thesis report: {e}")
        thesis_report = None

    # Reviewed-results fallback summary when no ground-truth exists
    reviewed_summary = None
    use_reviewed_fallback = False
    try:
        reviewed_summary = service.summarize_reviewed_results(
            model_filters=list(evaluation_run.models_evaluated)
            if evaluation_run.models_evaluated
            else None,
            species_filter=list(evaluation_run.species_filter)
            if evaluation_run.species_filter
            else None,
        )
        # Use fallback section if the ground-truth-based totals are zero
        use_reviewed_fallback = (getattr(evaluation_run, "total_ground_truth_objects", 0) or 0) == 0
    except Exception:
        reviewed_summary = None
        use_reviewed_fallback = False

    # Check if evaluation has meaningful data or if we need to show guidance
    has_ground_truth = any(
        len(result.ground_truth_boxes) > 0 if result.ground_truth_boxes else False
        for result in evaluation_run.image_results.all()
    )

    # Also check if there are any images with annotations in the system
    annotated_images_available = (
        ImageUpload.objects.filter(metadata__ground_truth_annotations__isnull=False)
        .exclude(metadata__ground_truth_annotations=[])
        .count()
    )

    # Update guidance based on available annotated images
    if not has_ground_truth and annotated_images_available > 0:
        evaluation_guidance = {
            "issue": "Ground Truth Available But Not Used in Evaluation",
            "explanation": f"Found {annotated_images_available} images with ground truth annotations, but they weren't included in this evaluation run.",
            "suggestions": [
                "Run a new evaluation to include your annotated images",
                "Make sure your annotated images match the model and species filters",
                "Check that your annotated images are in the selected date range",
                "Ensure your image files still exist and are accessible",
            ],
            "available_data": [
                f"{annotated_images_available} images with ground truth annotations available",
                f"{evaluation_run.total_images_evaluated} images processed in this run",
                "Ready for real evaluation with proper metrics",
            ],
        }

    has_meaningful_metrics = (
        evaluation_run.overall_precision and evaluation_run.overall_precision > 0
    ) or (evaluation_run.overall_recall and evaluation_run.overall_recall > 0)

    # Provide guidance for no ground truth scenario
    evaluation_guidance = None
    if not has_ground_truth:
        evaluation_guidance = {
            "issue": "No Ground Truth Data Available",
            "explanation": "This evaluation run contains images without ground truth annotations, making traditional metrics (Precision, Recall, mAP) unavailable.",
            "suggestions": [
                "For thesis evaluation, consider using a labeled dataset with ground truth annotations",
                "Use the reviewed results feature to analyze model performance on user-approved detections",
                "Export detection results for manual validation and annotation",
                "Consider confidence score distributions and detection counts as alternative metrics",
            ],
            "available_data": [
                f"{evaluation_run.total_images_evaluated} images processed",
                f"{evaluation_run.model_metrics.first().images_processed if evaluation_run.model_metrics.exists() else 0} successful detections",
                "Detection confidence distributions",
                "Species detection counts",
            ],
        }

    context = {
        "evaluation_run": evaluation_run,
        "model_metrics": model_metrics,
        "species_metrics": species_metrics,
        "confusion_matrix": confusion_matrix,
        "species_names": species_names[:-1],  # Exclude 'Background' from display
        "precision_recall_data": json.dumps(precision_recall_data),
        "performance_timeline": json.dumps(performance_timeline),
        "failure_cases": failure_cases,
        "total_models_compared": model_metrics.count(),
        "best_model_name": best_model.model_name if best_model else "N/A",
        "best_model_f1": float(best_model.f1_score) if best_model and best_model.f1_score else 0,
        "reviewed_summary": reviewed_summary,
        "use_reviewed_fallback": use_reviewed_fallback,
        # Enhanced thesis-relevant data
        "thesis_report": thesis_report,
        "statistical_analysis": statistical_analysis,
        "recommendations": thesis_report["recommendations"] if thesis_report else [],
        "error_analysis": thesis_report["error_analysis"] if thesis_report else {},
        # Ground truth status and guidance
        "has_ground_truth": has_ground_truth,
        "has_meaningful_metrics": has_meaningful_metrics,
        "evaluation_guidance": evaluation_guidance,
    }
    return render(request, "image_processing/evaluation_results.html", context)


@login_required
def evaluation_runs_list(request):
    """
    List all evaluation runs with filtering and pagination
    """
    if not request.user.can_access_feature("image_processing"):
        messages.error(request, "You don't have permission to access analytics.")
        return redirect("image_processing:list")

    # Get all runs with filtering
    runs = ModelEvaluationRun.objects.all().order_by("-created_at")

    # Apply filters
    status_filter = request.GET.get("status")
    if status_filter:
        runs = runs.filter(status=status_filter)

    # Model filtering
    model_filter = request.GET.get("model")
    if model_filter:
        runs = runs.filter(models_evaluated__contains=[model_filter])

    # Date range filtering
    date_start = request.GET.get("date_start")
    date_end = request.GET.get("date_end")
    if date_start:
        runs = runs.filter(created_at__date__gte=date_start)
    if date_end:
        runs = runs.filter(created_at__date__lte=date_end)

    # Created by filtering
    created_by_filter = request.GET.get("created_by")
    if created_by_filter:
        runs = runs.filter(created_by__employee_id__icontains=created_by_filter)

    # Date preset filtering
    date_filter = request.GET.get("date_range")
    if date_filter:
        if date_filter == "today":
            runs = runs.filter(created_at__date=timezone.now().date())
        elif date_filter == "week":
            runs = runs.filter(
                created_at__gte=timezone.now() - timedelta(days=get_date_filter_days("week"))
            )
        elif date_filter == "month":
            runs = runs.filter(
                created_at__gte=timezone.now() - timedelta(days=get_date_filter_days("month"))
            )

    # Pagination
    paginator = Paginator(runs, ANALYTICS_CONFIG["PAGINATION_LIMIT"])
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Summary statistics
    total_runs = runs.count()
    completed_runs = runs.filter(status="COMPLETED").count()
    processing_runs = runs.filter(status="PROCESSING").count()
    failed_runs = runs.filter(status="FAILED").count()
    avg_processing_time = runs.filter(
        status="COMPLETED", processing_duration__isnull=False
    ).aggregate(avg_time=Avg("processing_duration"))["avg_time"]

    # Get unique models that have been evaluated
    all_models = ModelEvaluationRun.objects.values_list("models_evaluated", flat=True)
    available_models = set()
    for model_list in all_models:
        if model_list:
            available_models.update(model_list)

    # Sort models for consistent display
    available_models = sorted(list(available_models))

    context = {
        "evaluation_runs": page_obj,  # Template expects this variable name
        "page_obj": page_obj,
        "total_runs": total_runs,
        "completed_runs": completed_runs,
        "processing_runs": processing_runs,
        "failed_runs": failed_runs,
        "avg_processing_time": avg_processing_time,
        "available_models": available_models,
        "status_filter": status_filter,
        "model_filter": model_filter,
        "created_by_filter": created_by_filter,
        "date_filter": date_filter,
        "date_start": date_start,
        "date_end": date_end,
    }

    return render(request, "image_processing/evaluation_runs_list.html", context)


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
def api_evaluation_status(request, run_id):
    """
    API endpoint to check evaluation run status (for REAL progress monitoring)
    """
    if not request.user.can_access_feature("image_processing"):
        return JsonResponse({"error": "Access denied"}, status=403)

    try:
        from .real_evaluation_workflow import RealEvaluationWorkflow

        evaluation_run = get_object_or_404(ModelEvaluationRun, id=run_id)

        # Get real-time progress from the workflow
        workflow = RealEvaluationWorkflow()
        progress = workflow.get_progress(run_id)

        # Add debug information to help users understand the evaluation state
        try:
            debug_info = {
                "models_evaluated": evaluation_run.models_evaluated,
                "species_filter": evaluation_run.species_filter,
                "iou_threshold": float(evaluation_run.iou_threshold),
                "confidence_threshold": float(evaluation_run.confidence_threshold),
                "total_images_evaluated": evaluation_run.total_images_evaluated,
                "has_image_results": evaluation_run.image_results.exists()
                if hasattr(evaluation_run, "image_results")
                else False,
                "has_model_metrics": evaluation_run.model_metrics.exists()
                if hasattr(evaluation_run, "model_metrics")
                else False,
                "has_species_metrics": evaluation_run.species_metrics.exists()
                if hasattr(evaluation_run, "species_metrics")
                else False,
            }
        except Exception as debug_error:
            debug_info = {
                "models_evaluated": evaluation_run.models_evaluated,
                "species_filter": evaluation_run.species_filter,
                "iou_threshold": float(evaluation_run.iou_threshold),
                "confidence_threshold": float(evaluation_run.confidence_threshold),
                "total_images_evaluated": evaluation_run.total_images_evaluated,
                "debug_error": str(debug_error),
            }

        # Get contextual helpful tips
        helpful_tips = get_helpful_tips(evaluation_run.status, progress)

        response_data = {
            "id": str(evaluation_run.id),
            "status": evaluation_run.status,
            "name": evaluation_run.name,
            "created_at": evaluation_run.created_at.isoformat(),
            "total_images": evaluation_run.total_images_evaluated,
            "overall_precision": float(evaluation_run.overall_precision)
            if evaluation_run.overall_precision
            else None,
            "overall_recall": float(evaluation_run.overall_recall)
            if evaluation_run.overall_recall
            else None,
            "overall_f1_score": float(evaluation_run.overall_f1_score)
            if evaluation_run.overall_f1_score
            else None,
            "overall_map_50": float(evaluation_run.overall_map_50)
            if evaluation_run.overall_map_50
            else None,
            "processing_duration": str(evaluation_run.processing_duration)
            if evaluation_run.processing_duration
            else None,
            "error_message": evaluation_run.error_message
            if evaluation_run.status == "FAILED"
            else None,
            # Real progress information
            "progress_percentage": progress.progress_percentage,
            "current_step": progress.current_step,
            "completed_steps": progress.completed_steps,
            "total_steps": progress.total_steps,
            "processing_status": progress.status,
            # Debug and helpful information
            "debug_info": debug_info,
            "helpful_tips": helpful_tips,
        }

        return JsonResponse(response_data)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
@require_http_methods(["DELETE"])
def delete_evaluation_run(request, run_id):
    """
    Delete an evaluation run and all associated data
    """
    if not request.user.can_access_feature("image_processing"):
        return JsonResponse({"error": "Access denied"}, status=403)

    try:
        evaluation_run = get_object_or_404(ModelEvaluationRun, id=run_id)

        # Check if user can delete (only creator or admin)
        admin_roles = get_admin_roles()
        if evaluation_run.created_by != request.user and request.user.role not in admin_roles:
            return JsonResponse(
                {"error": UI_TEXT["ERROR_MESSAGES"]["DELETE_PERMISSION"]}, status=403
            )

        evaluation_run.delete()

        return JsonResponse(
            {"success": True, "message": UI_TEXT["SUCCESS_MESSAGES"]["RUN_DELETED"]}
        )

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def reviewed_analytics_view(request):
    """Display analytics based on human-reviewed processing results."""
    if not request.user.can_access_feature("image_processing"):
        messages.error(request, "You don't have permission to access analytics.")
        return redirect("image_processing:list")

    service = ModelAnalyticsService()
    performance_summary = service.summarize_model_performance_from_reviews()

    context = {
        "summary": performance_summary,
    }
    return render(request, "image_processing/reviewed_analytics.html", context)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_kfold_evaluation(request):
    """Trigger K-fold evaluation over processed results for thesis reporting."""
    if not request.user.can_access_feature("image_processing"):
        return JsonResponse({"error": "Access denied"}, status=403)

    try:
        data = json.loads(request.body or "{}")
        k = int(data.get("k", 5))
        iou_th = float(data.get("iou_threshold", ANALYTICS_CONFIG["DEFAULT_IOU_THRESHOLD"]))
        conf_th = float(
            data.get("confidence_threshold", ANALYTICS_CONFIG["DEFAULT_CONFIDENCE_THRESHOLD"])
        )
        models = data.get("models", None)
        species = data.get("species", None)

        # Optional date range
        date_range = None
        if data.get("date_start") and data.get("date_end"):
            date_start = datetime.fromisoformat(data["date_start"].replace("Z", "+00:00"))
            date_end = datetime.fromisoformat(data["date_end"].replace("Z", "+00:00"))
            date_range = (date_start, date_end)

        service = ModelAnalyticsService()
        eval_run = service.run_kfold_evaluation(
            k=k,
            created_by=request.user,
            name=data.get("name"),
            model_filters=models,
            date_range=date_range,
            species_filter=species,
            iou_threshold=iou_th,
            confidence_threshold=conf_th,
        )

        # Summarize aggregate rows
        aggregates = []
        for m in eval_run.model_metrics.filter(model_name__icontains="[k-fold aggregate]"):
            aggregates.append(
                {
                    "model": m.model_name.replace(" [k-fold aggregate]", ""),
                    "precision_mean": float(m.precision) if m.precision else 0.0,
                    "recall_mean": float(m.recall) if m.recall else 0.0,
                    "f1_mean": float(m.f1_score) if m.f1_score else 0.0,
                    "map50_mean": float(m.map_50) if m.map_50 else 0.0,
                    "images_processed": m.images_processed,
                }
            )

        return JsonResponse(
            {
                "success": True,
                "evaluation_run_id": str(eval_run.id),
                "status": eval_run.status,
                "overall_map_50": float(eval_run.overall_map_50)
                if eval_run.overall_map_50
                else None,
                "total_images": eval_run.total_images_evaluated,
                "aggregates": aggregates,
                "redirect_url": f"/image-processing/analytics/results/{eval_run.id}/",
            }
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@login_required
@csrf_exempt
@require_http_methods(["GET"])
def api_reviewed_summary(request):
    """Return analytics summary based on reviewed (approved/overridden) results."""
    if not request.user.can_access_feature("image_processing"):
        return JsonResponse({"error": "Access denied"}, status=403)

    try:
        models = request.GET.getlist("model") or None
        species = request.GET.getlist("species") or None

        service = ModelAnalyticsService()
        summary = service.summarize_reviewed_results(species_filter=species, model_filters=models)
        return JsonResponse({"success": True, "summary": summary})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)
