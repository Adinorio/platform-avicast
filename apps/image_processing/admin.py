from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import ImageUpload, ImageProcessingResult, ProcessingBatch
from apps.users.models import User
from .analytics_models import ModelEvaluationRun, ModelPerformanceMetrics, SpeciesPerformanceMetrics, ImageEvaluationResult


@admin.register(ImageUpload)
class ImageUploadAdmin(admin.ModelAdmin):
    list_display = ('title', 'uploaded_by', 'upload_status', 'file_size_display', 'uploaded_at', 'processing_status')
    list_filter = ('upload_status', 'uploaded_at', 'uploaded_by__role')
    search_fields = ('title', 'description', 'uploaded_by__employee_id', 'original_filename')
    readonly_fields = ('uploaded_by', 'uploaded_at', 'file_size', 'file_type', 'image_width', 'image_height')
    ordering = ('-uploaded_at',)
    
    fieldsets = (
        ('Upload Information', {
            'fields': ('title', 'description', 'image_file', 'upload_status')
        }),
        ('File Details', {
            'fields': ('file_size', 'file_type', 'original_filename', 'image_width', 'image_height'),
            'classes': ('collapse',)
        }),
        ('Processing Information', {
            'fields': ('processing_started_at', 'processing_completed_at', 'processing_duration'),
            'classes': ('collapse',)
        }),
        ('User Information', {
            'fields': ('uploaded_by', 'uploaded_at'),
            'classes': ('collapse',)
        }),
    )
    
    def file_size_display(self, obj):
        if obj.file_size:
            size_kb = obj.file_size / 1024
            if size_kb > 1024:
                return f"{size_kb/1024:.1f} MB"
            return f"{size_kb:.1f} KB"
        return "N/A"
    file_size_display.short_description = 'File Size'
    
    def processing_status(self, obj):
        if hasattr(obj, 'processing_result'):
            result = obj.processing_result
            if result.processing_status == 'COMPLETED':
                if result.review_status == 'APPROVED':
                    return format_html('<span style="color: green;">✅ Approved</span>')
                elif result.review_status == 'REJECTED':
                    return format_html('<span style="color: red;">❌ Rejected</span>')
                elif result.review_status == 'OVERRIDDEN':
                    return format_html('<span style="color: orange;">🔄 Overridden</span>')
                else:
                    return format_html('<span style="color: blue;">⏳ Pending Review</span>')
            elif result.processing_status == 'FAILED':
                return format_html('<span style="color: red;">❌ Failed</span>')
            else:
                return format_html('<span style="color: orange;">⏳ {}</span>', result.processing_status)
        return format_html('<span style="color: gray;">⏳ Not Processed</span>')
    processing_status.short_description = 'Processing Status'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.role == User.Role.SUPERADMIN:
            return qs
        elif request.user.role == User.Role.ADMIN:
            return qs
        else:
            return qs.filter(uploaded_by=request.user)
    
    def has_add_permission(self, request):
        return request.user.role in [User.Role.ADMIN, User.Role.FIELD_WORKER]
    
    def has_change_permission(self, request, obj=None):
        if obj is None:
            return request.user.role in [User.Role.SUPERADMIN, User.Role.ADMIN, User.Role.FIELD_WORKER]
        if obj.uploaded_by == request.user:
            return True
        return request.user.role in [User.Role.SUPERADMIN, User.Role.ADMIN]
    
    def has_delete_permission(self, request, obj=None):
        return request.user.role in [User.Role.SUPERADMIN, User.Role.ADMIN]


@admin.register(ImageProcessingResult)
class ImageProcessingResultAdmin(admin.ModelAdmin):
    list_display = ('image_title', 'detected_species', 'confidence_score', 'processing_status', 'review_status', 'reviewed_by', 'created_at')
    list_filter = ('processing_status', 'review_status', 'detected_species', 'created_at', 'reviewed_by__role')
    search_fields = ('image_upload__title', 'detected_species', 'review_notes', 'override_reason')
    readonly_fields = ('image_upload', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Processing Results', {
            'fields': ('image_upload', 'detected_species', 'confidence_score', 'bounding_box', 'processing_status')
        }),
        ('Review & Approval', {
            'fields': ('review_status', 'reviewed_by', 'reviewed_at', 'review_notes')
        }),
        ('Override Information', {
            'fields': ('is_overridden', 'overridden_species', 'overridden_by', 'overridden_at', 'override_reason'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def image_title(self, obj):
        return obj.image_upload.title if obj.image_upload else 'N/A'
    image_title.short_description = 'Image Title'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.role == User.Role.SUPERADMIN:
            return qs
        elif request.user.role == User.Role.ADMIN:
            return qs
        else:
            return qs.filter(image_upload__uploaded_by=request.user)
    
    def has_add_permission(self, request):
        return False  # Results are created automatically during processing
    
    def has_change_permission(self, request, obj=None):
        if obj is None:
            return request.user.role in [User.Role.SUPERADMIN, User.Role.ADMIN]
        if obj.image_upload.uploaded_by == request.user:
            return True
        return request.user.role in [User.Role.SUPERADMIN, User.Role.ADMIN]
    
    def has_delete_permission(self, request, obj=None):
        return request.user.role in [User.Role.SUPERADMIN, User.Role.ADMIN]


@admin.register(ProcessingBatch)
class ProcessingBatchAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'total_images', 'processed_images', 'failed_images', 'status', 'progress_bar', 'created_at')
    list_filter = ('status', 'created_at', 'created_by__role')
    search_fields = ('name', 'description', 'created_by__employee_id')
    readonly_fields = ('created_by', 'created_at', 'started_at', 'completed_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Batch Information', {
            'fields': ('name', 'description', 'status')
        }),
        ('Progress Tracking', {
            'fields': ('total_images', 'processed_images', 'failed_images')
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at'),
            'classes': ('collapse',)
        }),
        ('Images', {
            'fields': ('images',),
            'classes': ('collapse',)
        }),
        ('User Information', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def progress_bar(self, obj):
        percentage = obj.progress_percentage
        if percentage >= 80:
            color = 'green'
        elif percentage >= 60:
            color = 'orange'
        elif percentage >= 40:
            color = 'yellow'
        else:
            color = 'red'
        
        return format_html(
            '<div style="width: 100px; background-color: #f0f0f0; border-radius: 3px;">'
            '<div style="width: {}%; height: 20px; background-color: {}; border-radius: 3px; text-align: center; line-height: 20px; color: white; font-size: 12px;">'
            '{}%</div></div>',
            percentage, color, percentage
        )
    progress_bar.short_description = 'Progress'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.role == User.Role.SUPERADMIN:
            return qs
        elif request.user.role == User.Role.ADMIN:
            return qs
        else:
            return qs.filter(created_by=request.user)
    
    def has_add_permission(self, request):
        return request.user.role in [User.Role.SUPERADMIN, User.Role.ADMIN]
    
    def has_change_permission(self, request, obj=None):
        if obj is None:
            return request.user.role in [User.Role.SUPERADMIN, User.Role.ADMIN]
        if obj.created_by == request.user:
            return True
        return request.user.role in [User.Role.SUPERADMIN, User.Role.ADMIN]
    
    def has_delete_permission(self, request, obj=None):
        return request.user.role in [User.Role.SUPERADMIN, User.Role.ADMIN]

# Analytics Models Admin

@admin.register(ModelEvaluationRun)
class ModelEvaluationRunAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'created_by', 'created_at', 'total_images_evaluated', 'overall_precision')
    list_filter = ('status', 'created_at', 'created_by__role')
    search_fields = ('name', 'description', 'created_by__employee_id')
    readonly_fields = ('created_by', 'created_at', 'total_images_evaluated', 'overall_precision', 'overall_recall', 'overall_f1_score')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Run Information', {
            'fields': ('name', 'description', 'status')
        }),
        ('Evaluation Parameters', {
            'fields': ('iou_threshold', 'confidence_threshold', 'models_evaluated', 'species_filter'),
            'classes': ('collapse',)
        }),
        ('Date Filters', {
            'fields': ('date_range_start', 'date_range_end'),
            'classes': ('collapse',)
        }),
        ('Results', {
            'fields': ('total_images_evaluated', 'total_ground_truth_objects', 'total_predicted_objects', 'overall_precision', 'overall_recall', 'overall_f1_score', 'overall_map_50', 'overall_map_50_95'),
            'classes': ('collapse',)
        }),
        ('User Information', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.role == User.Role.SUPERADMIN:
            return qs
        elif request.user.role == User.Role.ADMIN:
            return qs
        else:
            return qs.filter(created_by=request.user)
    
    def has_add_permission(self, request):
        return request.user.role in [User.Role.SUPERADMIN, User.Role.ADMIN]
    
    def has_change_permission(self, request, obj=None):
        if obj is None:
            return request.user.role in [User.Role.SUPERADMIN, User.Role.ADMIN]
        if obj.created_by == request.user:
            return True
        return request.user.role in [User.Role.SUPERADMIN, User.Role.ADMIN]
    
    def has_delete_permission(self, request, obj=None):
        return request.user.role in [User.Role.SUPERADMIN, User.Role.ADMIN]


@admin.register(ModelPerformanceMetrics)
class ModelPerformanceMetricsAdmin(admin.ModelAdmin):
    list_display = ('evaluation_run', 'model_name', 'model_version', 'precision', 'recall', 'f1_score', 'map_50', 'map_50_95')
    list_filter = ('model_name', 'model_version', 'created_at')
    search_fields = ('evaluation_run__name', 'model_name', 'model_version')
    readonly_fields = ('evaluation_run', 'created_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Model Information', {
            'fields': ('evaluation_run', 'model_name', 'model_version')
        }),
        ('Performance Metrics', {
            'fields': ('precision', 'recall', 'f1_score', 'map_50', 'map_50_95')
        }),
        ('Dataset Metrics', {
            'fields': ('images_processed', 'ground_truth_objects', 'predicted_objects'),
            'classes': ('collapse',)
        }),
        ('Confusion Matrix', {
            'fields': ('true_positives', 'false_positives', 'false_negatives'),
            'classes': ('collapse',)
        }),
        ('Model Characteristics', {
            'fields': ('avg_inference_time_ms', 'avg_confidence_score', 'model_parameters_millions', 'model_size_mb'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.role == User.Role.SUPERADMIN:
            return qs
        elif request.user.role == User.Role.ADMIN:
            return qs
        else:
            return qs.filter(evaluation_run__created_by=request.user)
    
    def has_add_permission(self, request):
        return request.user.role in [User.Role.SUPERADMIN, User.Role.ADMIN]
    
    def has_change_permission(self, request, obj=None):
        return request.user.role in [User.Role.SUPERADMIN, User.Role.ADMIN]
    
    def has_delete_permission(self, request, obj=None):
        return request.user.role in [User.Role.SUPERADMIN, User.Role.ADMIN]


@admin.register(SpeciesPerformanceMetrics)
class SpeciesPerformanceMetricsAdmin(admin.ModelAdmin):
    list_display = ('model_metrics', 'species_name', 'precision', 'recall', 'f1_score', 'average_precision')
    list_filter = ('species_name', 'model_metrics__model_name', 'created_at')
    search_fields = ('species_name', 'model_metrics__evaluation_run__name')
    readonly_fields = ('model_metrics', 'created_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Species Information', {
            'fields': ('model_metrics', 'species_name', 'species_class_id')
        }),
        ('Performance Metrics', {
            'fields': ('precision', 'recall', 'f1_score', 'average_precision')
        }),
        ('Counts', {
            'fields': ('ground_truth_count', 'detected_count'),
            'classes': ('collapse',)
        }),
        ('Confusion Matrix', {
            'fields': ('true_positives', 'false_positives', 'false_negatives'),
            'classes': ('collapse',)
        }),
        ('Characteristics', {
            'fields': ('avg_confidence',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.role == User.Role.SUPERADMIN:
            return qs
        elif request.user.role == User.Role.ADMIN:
            return qs
        else:
            return qs.filter(model_metrics__evaluation_run__created_by=request.user)
    
    def has_add_permission(self, request):
        return request.user.role in [User.Role.SUPERADMIN, User.Role.ADMIN]
    
    def has_change_permission(self, request, obj=None):
        return request.user.role in [User.Role.SUPERADMIN, User.Role.ADMIN]
    
    def has_delete_permission(self, request, obj=None):
        return request.user.role in [User.Role.SUPERADMIN, User.Role.ADMIN]


@admin.register(ImageEvaluationResult)
class ImageEvaluationResultAdmin(admin.ModelAdmin):
    list_display = ('evaluation_run', 'image_filename', 'model_used', 'ground_truth_count', 'predicted_count', 'avg_iou')
    list_filter = ('model_used', 'evaluation_run__status', 'created_at')
    search_fields = ('image_filename', 'model_used', 'evaluation_run__name')
    readonly_fields = ('evaluation_run', 'created_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Image Information', {
            'fields': ('evaluation_run', 'image_upload', 'image_filename', 'model_used')
        }),
        ('Ground Truth', {
            'fields': ('ground_truth_boxes', 'ground_truth_count'),
            'classes': ('collapse',)
        }),
        ('Predictions', {
            'fields': ('predicted_boxes', 'predicted_count'),
            'classes': ('collapse',)
        }),
        ('Matching Results', {
            'fields': ('matches', 'unmatched_predictions', 'unmatched_ground_truth'),
            'classes': ('collapse',)
        }),
        ('Image Metrics', {
            'fields': ('image_precision', 'image_recall', 'image_f1', 'avg_iou', 'inference_time_ms'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.role == User.Role.SUPERADMIN:
            return qs
        elif request.user.role == User.Role.ADMIN:
            return qs
        else:
            return qs.filter(evaluation_run__created_by=request.user)
    
    def has_add_permission(self, request):
        return request.user.role in [User.Role.SUPERADMIN, User.Role.ADMIN]
    
    def has_change_permission(self, request, obj=None):
        return request.user.role in [User.Role.SUPERADMIN, User.Role.ADMIN]
    
    def has_delete_permission(self, request, obj=None):
        return request.user.role in [User.Role.SUPERADMIN, User.Role.ADMIN]
