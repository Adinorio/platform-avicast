"""
GTD-based Image Processing Admin Configuration
Following Getting Things Done methodology for workflow management
"""

from django.contrib import admin
from .models import ImageUpload, ProcessingResult, ProcessingBatch


@admin.register(ImageUpload)
class ImageUploadAdmin(admin.ModelAdmin):
    """
    CAPTURE Stage: Admin interface for uploaded images
    """
    list_display = ["title", "uploaded_by", "upload_status", "uploaded_at", "file_size"]
    list_filter = ["upload_status", "uploaded_at", "uploaded_by"]
    search_fields = ["title", "uploaded_by__employee_id", "site_hint"]
    readonly_fields = ["id", "uploaded_at", "file_size", "original_filename"]

    fieldsets = (
        ("Basic Information", {
            "fields": ("title", "image_file", "uploaded_by", "site_hint")
        }),
        ("File Information", {
            "fields": ("file_size", "original_filename", "status"),
            "classes": ("collapse",)
        }),
        ("Processing", {
            "fields": ("processing_started_at", "processing_completed_at"),
            "classes": ("collapse",)
        }),
    )

    def get_queryset(self, request):
        """Filter to show only images uploaded by the current user unless superadmin"""
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(uploaded_by=request.user)
        return qs


@admin.register(ProcessingResult)
class ProcessingResultAdmin(admin.ModelAdmin):
    """
    CLARIFY & REFLECT Stage: Admin interface for processing results
    """
    list_display = [
        "image_upload", "detected_species", "confidence_score",
        "review_decision", "reviewed_by", "is_ready_for_allocation"
    ]
    list_filter = [
        "detected_species", "review_decision", "is_overridden",
        "allocated_to_site", "created_at"
    ]
    search_fields = [
        "image_upload__title", "detected_species",
        "review_notes", "override_reason"
    ]
    readonly_fields = [
        "id", "created_at", "updated_at", "inference_time",
        "ai_model_used", "processing_device"
    ]

    fieldsets = (
        ("AI Results", {
            "fields": (
                "image_upload", "detected_species", "confidence_score",
                "bounding_box", "total_detections"
            )
        }),
        ("Processing Info", {
            "fields": ("ai_model_used", "inference_time", "processing_device"),
            "classes": ("collapse",)
        }),
        ("Human Review", {
            "fields": (
                "review_decision", "reviewed_by", "reviewed_at",
                "review_notes", "is_overridden"
            )
        }),
        ("Overrides", {
            "fields": ("overridden_species", "overridden_count", "override_reason"),
            "classes": ("collapse",)
        }),
        ("Allocation", {
            "fields": ("allocated_to_site", "allocated_to_census", "allocated_at"),
            "classes": ("collapse",)
        }),
    )

    def get_queryset(self, request):
        """Filter based on user permissions"""
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            # Show results for images uploaded by current user
            qs = qs.filter(image_upload__uploaded_by=request.user)
        return qs

    def is_ready_for_allocation(self, obj):
        """Show if result can be allocated"""
        return obj.is_ready_for_allocation
    is_ready_for_allocation.boolean = True
    is_ready_for_allocation.short_description = "Ready for Allocation"


@admin.register(ProcessingBatch)
class ProcessingBatchAdmin(admin.ModelAdmin):
    """
    ORGANIZE Stage: Admin interface for processing batches
    """
    list_display = ["name", "status", "created_by", "total_images", "progress_percentage", "created_at"]
    list_filter = ["status", "created_at", "created_by"]
    search_fields = ["name", "description", "created_by__employee_id"]
    readonly_fields = ["id", "created_at", "progress_percentage"]

    fieldsets = (
        ("Batch Information", {
            "fields": ("name", "description", "created_by")
        }),
        ("Images", {
            "fields": ("images",),
            "classes": ("collapse",)
        }),
        ("Progress", {
            "fields": (
                "total_images", "processed_images", "failed_images",
                "status", "progress_percentage"
            )
        }),
        ("Timing", {
            "fields": ("started_at", "completed_at"),
            "classes": ("collapse",)
        }),
    )

    def get_queryset(self, request):
        """Filter based on user permissions"""
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(created_by=request.user)
        return qs

    def progress_percentage(self, obj):
        """Show progress percentage"""
        return f"{obj.progress_percentage:.1f}%"
    progress_percentage.short_description = "Progress"
