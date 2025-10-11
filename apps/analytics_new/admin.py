"""
Admin configuration for new analytics app
"""

from django.contrib import admin

from .models import (
    # CensusAnalytics,  # Temporarily disabled during locations revamp
    GeneratedReport,
    PopulationTrend,
    ReportConfiguration,
    # SiteAnalytics,  # Temporarily disabled during locations revamp
    SpeciesAnalytics,
)


@admin.register(SpeciesAnalytics)
class SpeciesAnalyticsAdmin(admin.ModelAdmin):
    """Admin for species analytics"""

    list_display = (
        "species",
        "total_count",
        "sites_with_presence",
        "population_trend",
        "last_observation_date",
        "last_updated",
    )
    list_filter = ("population_trend", "is_active")
    search_fields = ("species__name", "species__scientific_name")
    readonly_fields = ("created_at", "last_updated")
    ordering = ("species__name",)

    fieldsets = (
        ("Species Information", {
            "fields": ("species", "total_count", "sites_with_presence", "last_observation_date")
        }),
        ("Geographic Distribution", {
            "fields": ("site_distribution",),
            "classes": ("collapse",),
        }),
        ("Population Trends", {
            "fields": ("population_trend", "trend_confidence"),
            "classes": ("collapse",),
        }),
        ("Metadata", {
            "fields": ("created_at", "is_active"),
            "classes": ("collapse",),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("species")

    def has_add_permission(self, request):
        return request.user.role in ["SUPERADMIN", "ADMIN"]

    def has_change_permission(self, request, obj=None):
        return request.user.role in ["SUPERADMIN", "ADMIN"]

    def has_delete_permission(self, request, obj=None):
        return request.user.role == "SUPERADMIN"


# Temporarily disabled SiteAnalytics admin during locations revamp
# @admin.register(SiteAnalytics)
# class SiteAnalyticsAdmin(admin.ModelAdmin):
#     """Admin for site analytics"""
#
#     list_display = (
#         "get_site_code",
#         "get_site_name",
#         "total_birds_recorded",
#         "species_diversity",
#         "last_survey_date",
#         "is_active",
#     )
#     list_filter = ("is_active",)
#     search_fields = ("site__name", "site__coordinates")
#     readonly_fields = ("created_at",)
#
#     fieldsets = (
#         ("Site Information", {
#             "fields": ("site", "total_birds_recorded", "species_diversity")
#         }),
#         ("Species Composition", {
#             "fields": ("dominant_species", "species_composition"),
#             "classes": ("collapse",),
#         }),
#         ("Monitoring Data", {
#             "fields": ("total_census_observations", "last_survey_date", "survey_frequency_days"),
#             "classes": ("collapse",),
#         }),
#         ("Environmental Data", {
#             "fields": ("avg_temperature", "avg_humidity"),
#             "classes": ("collapse",),
#         }),
#         ("Metadata", {
#             "fields": ("created_at", "is_active"),
#             "classes": ("collapse",),
#         }),
#     )
#
#     def get_queryset(self, request):
#         return super().get_queryset(request).select_related("site")
#
#     def get_site_code(self, obj):
#         return obj.site.name if obj.site else "No Site"
#     get_site_code.short_description = "Site"
#     get_site_code.admin_order_field = "site__name"
#
#     def get_site_name(self, obj):
#         return obj.site.name if obj.site else "No Site"
#     get_site_name.short_description = "Site Name"
#     get_site_name.admin_order_field = "site__name"
#
#     def has_add_permission(self, request):
#         return request.user.role in ["SUPERADMIN", "ADMIN"]
#
#     def has_change_permission(self, request, obj=None):
#         return request.user.role in ["SUPERADMIN", "ADMIN"]
#
#     def has_delete_permission(self, request, obj=None):
#         return request.user.role == "SUPERADMIN"


# Temporarily disabled CensusAnalytics admin during locations revamp
# @admin.register(CensusAnalytics)
# class CensusAnalyticsAdmin(admin.ModelAdmin):
#     """Admin for census analytics"""
#
#     list_display = (
#         "census_observation",
#         "total_birds",
#         "species_richness",
#         "dominant_species",
#         "data_quality_score",
#     )
#     list_filter = ("data_quality_score", "verification_status")
#     search_fields = ("census_observation__site__name", "dominant_species")
#     readonly_fields = ("created_at", "last_updated")
#
#     fieldsets = (
#         ("Census Information", {
#             "fields": ("census_observation", "total_birds", "species_richness")
#         }),
#         ("Species Analysis", {
#             "fields": ("dominant_species", "species_breakdown"),
#             "classes": ("collapse",),
#         }),
#         ("Data Quality", {
#             "fields": ("data_quality_score", "verification_status"),
#             "classes": ("collapse",),
#         }),
#         ("Metadata", {
#             "fields": ("created_at", "last_updated"),
#             "classes": ("collapse",),
#         }),
#     )
#
#     def get_queryset(self, request):
#         return super().get_queryset(request).select_related("census_observation__site", "census_observation__observer")
#
#     def has_add_permission(self, request):
#         return False  # Analytics are computed, not manually created
#
#     def has_change_permission(self, request, obj=None):
#         return request.user.role in ["SUPERADMIN", "ADMIN"]
#
#     def has_delete_permission(self, request, obj=None):
#         return request.user.role == "SUPERADMIN"


@admin.register(PopulationTrend)
class PopulationTrendAdmin(admin.ModelAdmin):
    """Admin for population trends"""

    list_display = (
        "get_species_name",
        "period_start",
        "period_end",
        "trend_direction",
        "trend_strength",
        "average_count",
        "analysis_date",
    )
    list_filter = ("trend_direction", "trend_strength", "analysis_date")
    search_fields = ("species_analytics__species__name", "methodology")
    readonly_fields = ("analysis_date", "period_length_days")

    fieldsets = (
        ("Trend Analysis", {
            "fields": ("species_analytics", "period_start", "period_end", "period_length_days")
        }),
        ("Population Metrics", {
            "fields": ("average_count", "peak_count", "minimum_count")
        }),
        ("Trend Analysis", {
            "fields": ("trend_direction", "trend_strength", "confidence_level")
        }),
        ("Statistical Data", {
            "fields": ("standard_deviation", "coefficient_variation", "sample_size"),
            "classes": ("collapse",),
        }),
        ("Environmental Factors", {
            "fields": ("correlated_factors", "seasonal_pattern"),
            "classes": ("collapse",),
        }),
        ("Data Sources", {
            "fields": ("data_sources",),
            "classes": ("collapse",),
        }),
        ("Methodology", {
            "fields": ("methodology", "analyzed_by", "analysis_date"),
            "classes": ("collapse",),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("species_analytics__species", "analyzed_by")

    def get_species_name(self, obj):
        return obj.species_analytics.species.name
    get_species_name.short_description = "Species"
    get_species_name.admin_order_field = "species_analytics__species__name"

    def has_add_permission(self, request):
        return request.user.role in ["SUPERADMIN", "ADMIN"]

    def has_change_permission(self, request, obj=None):
        return request.user.role in ["SUPERADMIN", "ADMIN"]

    def has_delete_permission(self, request, obj=None):
        return request.user.role == "SUPERADMIN"


@admin.register(ReportConfiguration)
class ReportConfigurationAdmin(admin.ModelAdmin):
    """Admin for report configurations"""

    list_display = (
        "name",
        "report_type",
        "output_format",
        "is_scheduled",
        "is_active",
        "created_at",
    )
    list_filter = ("report_type", "output_format", "is_scheduled", "is_active")
    search_fields = ("name", "description")
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("Basic Information", {
            "fields": ("name", "report_type", "description")
        }),
        ("Report Parameters", {
            "fields": ("include_species", "include_sites", "date_range_start", "date_range_end"),
            "classes": ("collapse",),
        }),
        ("Output Options", {
            "fields": ("output_format", "include_charts", "include_maps", "include_raw_data")
        }),
        ("Scheduling", {
            "fields": ("is_scheduled", "schedule_frequency", "next_generation"),
            "classes": ("collapse",),
        }),
        ("Metadata", {
            "fields": ("created_by", "created_at", "updated_at", "is_active"),
            "classes": ("collapse",),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("created_by")

    def has_add_permission(self, request):
        return request.user.role in ["SUPERADMIN", "ADMIN"]

    def has_change_permission(self, request, obj=None):
        return request.user.role in ["SUPERADMIN", "ADMIN"]

    def has_delete_permission(self, request, obj=None):
        return request.user.role == "SUPERADMIN"


@admin.register(GeneratedReport)
class GeneratedReportAdmin(admin.ModelAdmin):
    """Admin for generated reports"""

    list_display = (
        "title",
        "configuration",
        "generation_date",
        "generated_by",
        "status",
        "file_size_bytes",
    )
    list_filter = ("status", "generation_date", "output_format")
    search_fields = ("title", "configuration__name")
    readonly_fields = ("generation_date", "file_path", "file_size_bytes")

    fieldsets = (
        ("Report Information", {
            "fields": ("configuration", "title", "generation_date", "generated_by")
        }),
        ("Content Summary", {
            "fields": ("species_included", "sites_included", "total_records", "date_range"),
            "classes": ("collapse",),
        }),
        ("File Information", {
            "fields": ("file_path", "file_size_bytes", "status", "error_message"),
            "classes": ("collapse",),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("configuration", "generated_by")

    def has_add_permission(self, request):
        return False  # Reports are generated, not manually created

    def has_change_permission(self, request, obj=None):
        return request.user.role in ["SUPERADMIN", "ADMIN"]

    def has_delete_permission(self, request, obj=None):
        return request.user.role in ["SUPERADMIN", "ADMIN"]

