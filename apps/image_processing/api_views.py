"""
API views for image processing
"""

import json
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .permissions import admin_required

logger = logging.getLogger(__name__)


@login_required
def debug_form_view(request):
    """Debug form view for testing evaluation run creation"""
    if not request.user.can_access_feature("image_processing"):
        messages.error(request, "You don't have permission to access image processing.")
        return redirect("home")


@login_required
def health_status_view(request):
    """Real-time health status monitoring for the detection service"""
    if not request.user.can_access_feature("image_processing"):
        messages.error(request, "You don't have permission to access health monitoring.")
        return redirect("home")

    from .bird_detection_service import get_bird_detection_service

    detection_service = get_bird_detection_service()

    # Get comprehensive health status
    health_status = detection_service.get_detection_health_status()
    model_info = detection_service.get_model_info()
    available_models = detection_service.get_available_models()

    # Add timestamp for monitoring
    import datetime
    health_status["timestamp"] = datetime.datetime.now().isoformat()

    context = {
        "health_status": health_status,
        "model_info": model_info,
        "available_models": available_models,
        "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
    }

    from django.shortcuts import render
    return render(request, "image_processing/health_status.html", context)


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def clear_upload_results(request):
    """Clear upload results from session after modal is shown"""
    if "upload_results" in request.session:
        del request.session["upload_results"]
    return JsonResponse({"status": "success"})


@login_required
def model_selection_view(request):
    """View for selecting and managing AI models"""
    # Only allow ADMIN and SUPERADMIN roles to access model management
    if not hasattr(request.user, "role") or request.user.role not in ["ADMIN", "SUPERADMIN"]:
        messages.error(request, "Access denied. Only administrators can manage AI models.")
        return redirect("image_processing:list")

    from .forms import ModelSelectionForm
    from .bird_detection_service import get_bird_detection_service

    detection_service = get_bird_detection_service()

    if request.method == "POST":
        form = ModelSelectionForm(request.POST)
        if form.is_valid():
            ai_model = form.cleaned_data["ai_model"]
            confidence_threshold = form.cleaned_data["confidence_threshold"]

            # Switch to selected model
            if detection_service.switch_model(ai_model):
                messages.success(request, f"Successfully switched to {ai_model}")
            else:
                messages.error(request, f"Failed to switch to {ai_model}")

            # Update confidence threshold
            detection_service.confidence_threshold = confidence_threshold

            from django.shortcuts import redirect
            return redirect("image_processing:model_selection")
    else:
        # Pre-populate form with current settings
        initial_data = {
            "ai_model": detection_service.current_version,
            "confidence_threshold": detection_service.confidence_threshold,
        }
        form = ModelSelectionForm(initial=initial_data)

    # Get model information
    model_info = detection_service.get_model_info()
    available_models = detection_service.get_available_models()

    context = {
        "form": form,
        "model_info": model_info,
        "available_models": available_models,
        "current_model": detection_service.current_version,
    }

    from django.shortcuts import render
    return render(request, "image_processing/model_selection.html", context)


@login_required
def benchmark_models_view(request):
    """View for benchmarking different YOLO models"""
    # Only allow ADMIN and SUPERADMIN roles to access model benchmarking
    if not hasattr(request.user, "role") or request.user.role not in ["ADMIN", "SUPERADMIN"]:
        messages.error(request, "Access denied. Only administrators can benchmark AI models.")
        return redirect("image_processing:list")

    from .bird_detection_service import get_bird_detection_service

    detection_service = get_bird_detection_service()

    if request.method == "POST":
        # Get test image from request
        test_image = request.FILES.get("test_image")
        if test_image:
            try:
                # Read image content
                image_content = test_image.read()

                # Run benchmark
                benchmark_results = detection_service.benchmark_models(image_content)

                messages.success(request, "Benchmark completed successfully!")

                context = {
                    "benchmark_results": benchmark_results,
                    "test_image_name": test_image.name,
                    "test_image_size": len(image_content),
                }

                from django.shortcuts import render
                return render(request, "image_processing/benchmark_results.html", context)

            except Exception as e:
                messages.error(request, f"Benchmark failed: {str(e)}")
        else:
            messages.error(request, "Please select a test image for benchmarking.")

    context = {
        "available_models": detection_service.get_available_models(),
        "total_models": len(detection_service.models),
    }

    from django.shortcuts import render
    return render(request, "image_processing/benchmark_models.html", context)
