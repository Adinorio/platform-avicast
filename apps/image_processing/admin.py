from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import ImageUpload, ImageProcessingResult, ProcessingBatch
from apps.users.models import User


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
