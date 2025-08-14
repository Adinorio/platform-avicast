from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()

class ChartConfiguration(models.Model):
    """Configuration for different types of charts"""
    CHART_TYPES = [
        ('bar', 'Bar Chart'),
        ('line', 'Line Chart'),
        ('pie', 'Pie Chart'),
        ('scatter', 'Scatter Plot'),
        ('heatmap', 'Heatmap'),
        ('radar', 'Radar Chart'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, help_text="Name of the chart configuration")
    chart_type = models.CharField(max_length=20, choices=CHART_TYPES)
    title = models.CharField(max_length=200, help_text="Chart title")
    description = models.TextField(blank=True, help_text="Description of what the chart shows")
    config_data = models.JSONField(help_text="Chart configuration in JSON format")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, help_text="Whether this chart configuration is active")
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Chart Configuration'
        verbose_name_plural = 'Chart Configurations'
    
    def __str__(self):
        return f"{self.name} ({self.get_chart_type_display()})"

class ReportTemplate(models.Model):
    """Templates for generating reports"""
    REPORT_TYPES = [
        ('census_summary', 'Census Summary Report'),
        ('species_diversity', 'Species Diversity Report'),
        ('population_trends', 'Population Trends Report'),
        ('site_comparison', 'Site Comparison Report'),
        ('seasonal_analysis', 'Seasonal Analysis Report'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, help_text="Name of the report template")
    report_type = models.CharField(max_length=30, choices=REPORT_TYPES)
    description = models.TextField(blank=True, help_text="Description of the report")
    template_data = models.JSONField(help_text="Report template configuration")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Report Template'
        verbose_name_plural = 'Report Templates'
    
    def __str__(self):
        return f"{self.name} ({self.get_report_type_display()})"

class GeneratedReport(models.Model):
    """Records of generated reports"""
    FORMAT_CHOICES = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('html', 'HTML'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(ReportTemplate, on_delete=models.CASCADE)
    title = models.CharField(max_length=200, help_text="Title of the generated report")
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES)
    file_path = models.CharField(max_length=500, blank=True, help_text="Path to the generated file")
    parameters = models.JSONField(help_text="Parameters used to generate the report")
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    file_size = models.PositiveIntegerField(blank=True, null=True, help_text="File size in bytes")
    
    class Meta:
        ordering = ['-generated_at']
        verbose_name = 'Generated Report'
        verbose_name_plural = 'Generated Reports'
    
    def __str__(self):
        return f"{self.title} ({self.get_format_display()}) - {self.generated_at.strftime('%Y-%m-%d')}"
