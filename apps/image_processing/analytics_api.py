"""
Analytics API Views
API endpoints for analytics functionality
"""

import json
import logging
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

logger = logging.getLogger(__name__)

try:
    from .analytics_config import ANALYTICS_CONFIG
    from .analytics_service import ModelAnalyticsService
except ImportError as e:
    logger.warning(f"Analytics components not available: {e}")


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
