"""
Admin configuration for locations app
"""

from django.contrib import admin
from .models import Site, CensusYear, CensusMonth, Census, CensusObservation


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    """Admin for sites"""

    list_display = (
        "name",
        "site_type",
        "status",
        "get_coordinates_display",
        "created_at",
    )
    list_filter = ("site_type", "status", "created_at")
    search_fields = ("name", "description")
    readonly_fields = ("id", "created_at", "updated_at")

    fieldsets = (
        ("Basic Information", {
            "fields": ("name", "site_type", "description", "status")
        }),
        ("Location", {
            "fields": ("coordinates", "image"),
        }),
        ("Metadata", {
            "fields": ("id", "created_at", "updated_at", "created_by"),
            "classes": ("collapse",),
        }),
    )

    def get_coordinates_display(self, obj):
        return obj.get_coordinates_display()
    get_coordinates_display.short_description = "Coordinates"
    get_coordinates_display.admin_order_field = "coordinates"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("created_by")


@admin.register(CensusYear)
class CensusYearAdmin(admin.ModelAdmin):
    """Admin for census years"""

    list_display = (
        "site",
        "year",
        "total_census_count",
        "total_birds_recorded",
        "total_species_recorded",
    )
    list_filter = ("year", "site")
    search_fields = ("site__name",)
    readonly_fields = ("id", "created_at", "updated_at")

    fieldsets = (
        ("Census Year", {
            "fields": ("site", "year")
        }),
        ("Summary Data", {
            "fields": ("total_census_count", "total_birds_recorded", "total_species_recorded"),
        }),
        ("Metadata", {
            "fields": ("id", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("site")


@admin.register(CensusMonth)
class CensusMonthAdmin(admin.ModelAdmin):
    """Admin for census months"""

    list_display = (
        "get_site_name",
        "get_year",
        "get_month_display",
        "total_census_count",
        "total_birds_recorded",
        "total_species_recorded",
    )
    list_filter = ("month", "year__year")
    search_fields = ("year__site__name",)
    readonly_fields = ("id", "created_at", "updated_at")

    fieldsets = (
        ("Census Month", {
            "fields": ("year", "month")
        }),
        ("Summary Data", {
            "fields": ("total_census_count", "total_birds_recorded", "total_species_recorded"),
        }),
        ("Metadata", {
            "fields": ("id", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("year__site")

    def get_site_name(self, obj):
        return obj.year.site.name
    get_site_name.short_description = "Site"
    get_site_name.admin_order_field = "year__site__name"

    def get_year(self, obj):
        return obj.year.year
    get_year.short_description = "Year"
    get_year.admin_order_field = "year__year"


@admin.register(Census)
class CensusAdmin(admin.ModelAdmin):
    """Admin for census records"""

    list_display = (
        "get_site_name",
        "get_year_month",
        "census_date",
        "lead_observer",
        "get_field_team_count",
        "total_birds",
        "total_species",
        "weather_conditions",
    )
    list_filter = ("census_date", "lead_observer", "month__year__year")
    search_fields = ("month__year__site__name", "lead_observer__employee_id", "notes")
    readonly_fields = ("id", "created_at", "updated_at", "total_birds", "total_species")

    fieldsets = (
        ("Census Information", {
            "fields": ("month", "census_date", "lead_observer", "field_team")
        }),
        ("Observations", {
            "fields": ("total_birds", "total_species"),
        }),
        ("Conditions", {
            "fields": ("weather_conditions", "notes"),
        }),
        ("Metadata", {
            "fields": ("id", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "month__year__site", "lead_observer"
        ).prefetch_related("field_team")

    def get_site_name(self, obj):
        return obj.month.year.site.name
    get_site_name.short_description = "Site"
    get_site_name.admin_order_field = "month__year__site__name"

    def get_year_month(self, obj):
        return f"{obj.month.get_month_display()} {obj.month.year.year}"
    get_year_month.short_description = "Month/Year"
    get_year_month.admin_order_field = "month__month"

    def get_field_team_count(self, obj):
        return obj.field_team.count()
    get_field_team_count.short_description = "Team Size"


@admin.register(CensusObservation)
class CensusObservationAdmin(admin.ModelAdmin):
    """Admin for census observations"""

    list_display = (
        "get_census_info",
        "species_name",
        "count",
        "census",
    )
    list_filter = ("census__census_date",)
    search_fields = ("species_name", "census__month__year__site__name")
    readonly_fields = ("id", "created_at", "updated_at")

    fieldsets = (
        ("Observation", {
            "fields": ("census", "species", "species_name", "count")
        }),
        ("Metadata", {
            "fields": ("id", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("census__month__year__site", "species")

    def get_census_info(self, obj):
        return f"{obj.census.month.year.site.name} - {obj.census.census_date}"
    get_census_info.short_description = "Census"
    get_census_info.admin_order_field = "census__census_date"




