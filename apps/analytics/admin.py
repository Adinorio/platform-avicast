from django.contrib import admin
from .models import ChartConfiguration, ReportTemplate, GeneratedReport

@admin.register(ChartConfiguration)
class ChartConfigurationAdmin(admin.ModelAdmin):
    list_display = ['name', 'chart_type', 'title', 'is_active', 'created_by', 'created_at']
    list_filter = ['chart_type', 'is_active', 'created_at']
    search_fields = ['name', 'title', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'chart_type', 'title', 'description')
        }),
        ('Configuration', {
            'fields': ('config_data',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'report_type', 'is_active', 'created_by', 'created_at']
    list_filter = ['report_type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'report_type', 'description')
        }),
        ('Template Configuration', {
            'fields': ('template_data',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(GeneratedReport)
class GeneratedReportAdmin(admin.ModelAdmin):
    list_display = ['title', 'template', 'format', 'generated_by', 'generated_at', 'file_size']
    list_filter = ['template', 'format', 'generated_at']
    search_fields = ['title', 'template__name']
    readonly_fields = ['id', 'generated_at', 'file_size']
    fieldsets = (
        ('Report Information', {
            'fields': ('title', 'template', 'format')
        }),
        ('File Details', {
            'fields': ('file_path', 'file_size')
        }),
        ('Generation Details', {
            'fields': ('parameters', 'generated_by', 'generated_at')
        }),
    )
    
    def file_size_display(self, obj):
        if obj.file_size:
            return f"{obj.file_size / 1024:.1f} KB"
        return "N/A"
    file_size_display.short_description = 'File Size'
