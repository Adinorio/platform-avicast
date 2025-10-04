"""
GTD-based Image Processing Views
Following Getting Things Done methodology for workflow management

CAPTURE → CLARIFY → ORGANIZE → REFLECT → ENGAGE
"""

import logging
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView

from .forms import ImageUploadForm, ProcessingResultReviewForm, ProcessingResultOverrideForm, CensusAllocationForm
from .models import ImageUpload, ProcessingResult, ProcessingBatch, ProcessingStatus, ReviewDecision

logger = logging.getLogger(__name__)


@login_required
def dashboard(request):
    """
    CAPTURE Stage: Main dashboard showing workflow overview
    """
    # Get counts for each GTD stage
    capture_count = ImageUpload.objects.filter(
        uploaded_by=request.user,
        upload_status=ProcessingStatus.CAPTURED
    ).count()

    clarify_count = ImageUpload.objects.filter(
        uploaded_by=request.user,
        upload_status=ProcessingStatus.CLARIFIED
    ).count()

    organize_count = ImageUpload.objects.filter(
        uploaded_by=request.user,
        upload_status=ProcessingStatus.ORGANIZED
    ).count()

    reflect_count = ProcessingResult.objects.filter(
        image_upload__uploaded_by=request.user,
        review_decision=ReviewDecision.PENDING
    ).count()

    engage_count = ProcessingResult.objects.filter(
        image_upload__uploaded_by=request.user,
        review_decision__in=[ReviewDecision.APPROVED, ReviewDecision.OVERRIDDEN]
    ).count()

    # Recent activity
    recent_uploads = ImageUpload.objects.filter(
        uploaded_by=request.user
    ).order_by("-uploaded_at")[:5]

    recent_results = ProcessingResult.objects.filter(
        image_upload__uploaded_by=request.user
    ).order_by("-created_at")[:5]

    context = {
        "title": "Image Processing Dashboard",
        "capture_count": capture_count,
        "clarify_count": clarify_count,
        "organize_count": organize_count,
        "reflect_count": reflect_count,
        "engage_count": engage_count,
        "recent_uploads": recent_uploads,
        "recent_results": recent_results,
    }

    return render(request, "image_processing/dashboard.html", context)


@login_required
def upload_images(request):
    """
    CAPTURE Stage: Upload bird images for processing
    """
    if request.method == "POST":
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # Save the upload
            upload = form.save(commit=False)
            upload.uploaded_by = request.user
            upload.file_size = request.FILES["image_file"].size
            upload.original_filename = request.FILES["image_file"].name
            upload.save()

            messages.success(
                request,
                f"✅ Image '{upload.title}' captured successfully! "
                "It will be processed in the Clarify stage."
            )

            return redirect("image_processing:dashboard")
    else:
        form = ImageUploadForm()

    context = {
        "title": "Capture Images",
        "form": form,
        "stage": "capture",
    }

    return render(request, "image_processing/upload.html", context)


@login_required
def process_images(request):
    """
    CLARIFY Stage: Process uploaded images with AI
    """
    # Get images ready for processing (Captured status)
    pending_images = ImageUpload.objects.filter(
        uploaded_by=request.user,
        upload_status=ProcessingStatus.CAPTURED
    ).order_by("uploaded_at")

    if not pending_images.exists():
        messages.info(request, "No images waiting for processing. Upload some images first!")
        return redirect("image_processing:dashboard")

    context = {
        "title": "Clarify Images",
        "pending_images": pending_images,
        "stage": "clarify",
    }

    return render(request, "image_processing/process.html", context)


@login_required
@require_http_methods(["POST"])
def start_processing(request, image_id):
    """
    CLARIFY Stage: Start AI processing for a specific image
    """
    image = get_object_or_404(ImageUpload, id=image_id, uploaded_by=request.user)

    if image.upload_status != ProcessingStatus.CAPTURED:
        return JsonResponse({"success": False, "error": "Image is not ready for processing"})

    try:
        # Start processing (this would call your AI service)
        image.start_processing()

        # Simulate AI processing here
        # In real implementation, this would call your YOLO model
        process_image_with_ai(image)

        messages.success(request, f"🔍 '{image.title}' is being clarified by AI processing.")

    except Exception as e:
        logger.error(f"Processing failed for image {image_id}: {e}")
        messages.error(request, f"❌ Processing failed for '{image.title}'. Please try again.")

    return redirect("image_processing:process")


def process_image_with_ai(image_upload):
    """
    Simulate AI processing (replace with actual YOLO integration)
    """
    # This is where you'd integrate with your YOLO model
    # For now, we'll simulate the processing

    # Simulate processing time
    import time
    time.sleep(2)  # Simulate AI processing

    # Create processing result (this would be done by your AI service)
    result = ProcessingResult.objects.create(
        image_upload=image_upload,
        detected_species="LITTLE_EGRET",  # Simulated result
        confidence_score=0.85,  # Simulated confidence
        bounding_box={"x": 100, "y": 100, "width": 200, "height": 200},  # Simulated bbox
        total_detections=1,
        ai_model_used="YOLOv8_Egret_Specialist",
        review_decision=ReviewDecision.PENDING,
    )

    # Update image status
    image_upload.complete_processing()


@login_required
def review_results(request):
    """
    REFLECT Stage: Review AI processing results and make decisions
    """
    # Get results that need review
    pending_results = ProcessingResult.objects.filter(
        image_upload__uploaded_by=request.user,
        review_decision=ReviewDecision.PENDING
    ).order_by("created_at")

    if request.method == "POST":
        result_id = request.POST.get("result_id")
        action = request.POST.get("action")

        if result_id and action:
            result = get_object_or_404(ProcessingResult, id=result_id)

            if action == "approve":
                result.approve_result(request.user, request.POST.get("notes", ""))
                messages.success(request, f"✅ Approved '{result.image_upload.title}'")

            elif action == "reject":
                result.reject_result(request.user, request.POST.get("notes", ""))
                messages.warning(request, f"❌ Rejected '{result.image_upload.title}'")

            elif action == "override":
                # Handle override form submission
                override_form = ProcessingResultOverrideForm(request.POST)
                if override_form.is_valid():
                    result.override_result(
                        reviewer=request.user,
                        new_species=override_form.cleaned_data["new_species"],
                        new_count=override_form.cleaned_data["new_count"],
                        reason=override_form.cleaned_data["override_reason"]
                    )
                    messages.success(request, f"🔄 Overrode '{result.image_upload.title}'")

            return redirect("image_processing:review")

    context = {
        "title": "Reflect on Results",
        "pending_results": pending_results,
        "stage": "reflect",
    }

    return render(request, "image_processing/review.html", context)


@login_required
def allocate_results(request):
    """
    ENGAGE Stage: Allocate approved results to census data
    """
    # Get results ready for allocation
    ready_results = ProcessingResult.objects.filter(
        image_upload__uploaded_by=request.user,
        review_decision__in=[ReviewDecision.APPROVED, ReviewDecision.OVERRIDDEN]
    ).order_by("created_at")

    if request.method == "POST":
        result_id = request.POST.get("result_id")
        site_id = request.POST.get("site_id")

        if result_id and site_id:
            result = get_object_or_404(ProcessingResult, id=result_id)
            site = get_object_or_404("locations.Site", id=site_id)

            # Create or find census observation
            # This would integrate with your census system
            # For now, we'll simulate the allocation

            result.allocate_to_census(site, None)  # Would create census observation

            messages.success(
                request,
                f"✅ Allocated '{result.image_upload.title}' to {site.name} census data"
            )

            return redirect("image_processing:allocate")

    # Get available sites for allocation
    from apps.locations.models import Site
    available_sites = Site.objects.filter(status="active")

    context = {
        "title": "Engage with Census",
        "ready_results": ready_results,
        "available_sites": available_sites,
        "stage": "engage",
    }

    return render(request, "image_processing/allocate.html", context)


class ImageListView(LoginRequiredMixin, ListView):
    """
    ORGANIZE Stage: List view for organizing images by workflow stage
    """
    model = ImageUpload
    template_name = "image_processing/list.html"
    context_object_name = "images"
    paginate_by = 20

    def get_queryset(self):
        """Filter images based on workflow stage"""
        stage = self.request.GET.get("stage", "all")
        queryset = ImageUpload.objects.filter(uploaded_by=self.request.user)

        if stage == "captured":
            queryset = queryset.filter(upload_status=ProcessingStatus.CAPTURED)
        elif stage == "clarified":
            queryset = queryset.filter(upload_status=ProcessingStatus.CLARIFIED)
        elif stage == "organized":
            queryset = queryset.filter(upload_status=ProcessingStatus.ORGANIZED)
        elif stage == "reflected":
            # Images that have been reviewed
            queryset = queryset.filter(processing_result__review_decision__in=[
                ProcessingStatus.REFLECTED, ProcessingStatus.ENGAGED
            ])
        elif stage == "engaged":
            queryset = queryset.filter(upload_status=ProcessingStatus.ENGAGED)

        return queryset.order_by("-uploaded_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["current_stage"] = self.request.GET.get("stage", "all")
        context["stage_counts"] = {
            "all": ImageUpload.objects.filter(uploaded_by=self.request.user).count(),
            "captured": ImageUpload.objects.filter(
                uploaded_by=self.request.user, upload_status=ProcessingStatus.CAPTURED
            ).count(),
            "clarified": ImageUpload.objects.filter(
                uploaded_by=self.request.user, upload_status=ProcessingStatus.CLARIFIED
            ).count(),
            "organized": ImageUpload.objects.filter(
                uploaded_by=self.request.user, upload_status=ProcessingStatus.ORGANIZED
            ).count(),
            "reflected": ProcessingResult.objects.filter(
                image_upload__uploaded_by=self.request.user,
                review_decision__in=[ReviewDecision.APPROVED, ReviewDecision.REJECTED, ReviewDecision.OVERRIDDEN]
            ).count(),
            "engaged": ProcessingResult.objects.filter(
                image_upload__uploaded_by=self.request.user,
                review_decision__in=[ReviewDecision.APPROVED, ReviewDecision.OVERRIDDEN]
            ).count(),
        }
        return context


@login_required
def model_selection(request):
    """
    Model Management: Select and configure AI models for bird detection
    """
    # Get available models from the models directory
    import os
    from django.conf import settings
    
    models_dir = os.path.join(settings.BASE_DIR, "models")
    available_models = []
    
    if os.path.exists(models_dir):
        for model_name in os.listdir(models_dir):
            model_path = os.path.join(models_dir, model_name)
            if os.path.isdir(model_path):
                # Check for model files
                model_files = [f for f in os.listdir(model_path) if f.endswith(('.pt', '.pth', '.onnx'))]
                if model_files:
                    available_models.append({
                        'name': model_name,
                        'files': model_files,
                        'path': model_path
                    })
    
    # Get current active model (you might store this in settings or database)
    current_model = getattr(settings, 'ACTIVE_BIRD_MODEL', 'chinese_egret_v1')
    
    context = {
        "title": "Model Management",
        "available_models": available_models,
        "current_model": current_model,
    }
    
    return render(request, "image_processing/model_selection.html", context)


@login_required
def benchmark_models(request):
    """
    Model Benchmarking: Test and compare AI model performance
    """
    # Get model performance data (this would come from your benchmarking system)
    model_performance = [
        {
            'name': 'chinese_egret_v1',
            'accuracy': 0.94,
            'precision': 0.92,
            'recall': 0.89,
            'f1_score': 0.90,
            'inference_time': 0.15,
            'status': 'active'
        },
        {
            'name': 'yolov8n_birds',
            'accuracy': 0.87,
            'precision': 0.84,
            'recall': 0.82,
            'f1_score': 0.83,
            'inference_time': 0.08,
            'status': 'available'
        }
    ]
    
    context = {
        "title": "Model Benchmarking",
        "model_performance": model_performance,
    }
    
    return render(request, "image_processing/benchmark.html", context)
