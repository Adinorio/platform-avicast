from django.contrib import admin

from .models import CensusObservation, Site, SpeciesObservation, SiteSpeciesCount, DataChangeRequest


class SpeciesObservationInline(admin.TabularInline):
    model = SpeciesObservation
    extra = 1
    fields = ["species", "count", "behavior_notes"]


class CensusObservationInline(admin.TabularInline):
    model = CensusObservation
    extra = 0
    fields = ["observation_date", "observer", "weather_conditions", "notes"]
    readonly_fields = ["created_at", "updated_at"]
    show_change_link = True


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ["name", "site_type", "status", "coordinates", "created_at"]
    list_filter = ["site_type", "status", "created_at"]
    search_fields = ["name", "description"]
    readonly_fields = ["id", "created_at", "updated_at"]
    fieldsets = (
        ("Basic Information", {"fields": ("name", "site_type", "description", "status")}),
        ("Location", {"fields": ("coordinates",)}),
        (
            "Metadata",
            {"fields": ("created_by", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )
    inlines = [CensusObservationInline]


@admin.register(CensusObservation)
class CensusObservationAdmin(admin.ModelAdmin):
    list_display = [
        "site",
        "observation_date",
        "observer",
        "total_species",
        "total_birds",
        "created_at",
    ]
    list_filter = ["observation_date", "site", "observer", "created_at"]
    search_fields = ["site__name", "notes", "weather_conditions"]
    readonly_fields = ["id", "created_at", "updated_at"]
    fieldsets = (
        (
            "Observation Details",
            {"fields": ("site", "observation_date", "observer", "weather_conditions", "notes")},
        ),
        ("Metadata", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )
    inlines = [SpeciesObservationInline]

    def total_species(self, obj):
        return obj.get_total_species_count()

    total_species.short_description = "Species Count"

    def total_birds(self, obj):
        return obj.get_total_birds_count()

    total_birds.short_description = "Total Birds"


@admin.register(SpeciesObservation)
class SpeciesObservationAdmin(admin.ModelAdmin):
    list_display = ["get_species_name", "census", "count", "behavior_notes", "created_at"]
    list_filter = ["census__site", "census__observation_date", "species", "created_at"]
    search_fields = ["species__name", "species__scientific_name", "species_name", "behavior_notes", "census__site__name"]
    readonly_fields = ["id", "created_at", "updated_at"]
    fieldsets = (
        ("Species Details", {"fields": ("census", "species", "species_name", "count", "behavior_notes")}),
        ("Metadata", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def get_species_name(self, obj):
        """Display species name from the foreign key or fallback to text field"""
        return obj.species.name if obj.species else obj.species_name
    get_species_name.short_description = "Species"
    get_species_name.admin_order_field = "species__name"


@admin.register(SiteSpeciesCount)
class SiteSpeciesCountAdmin(admin.ModelAdmin):
    list_display = [
        "site",
        "get_species_name",
        "total_count",
        "observation_count",
        "last_observation_date",
        "is_verified",
        "verified_by",
    ]
    list_filter = ["is_verified", "site", "species", "last_observation_date"]
    search_fields = ["site__name", "species__name", "species__scientific_name"]
    readonly_fields = ["id", "created_at", "updated_at", "last_updated_from_census"]
    fieldsets = (
        ("Site and Species", {"fields": ("site", "species")}),
        ("Count Data", {"fields": ("total_count", "observation_count", "last_observation_date")}),
        ("Monthly/Yearly Breakdown", {"fields": ("monthly_counts", "yearly_counts")}),
        (
            "Verification Status",
            {"fields": ("is_verified", "verified_by", "verified_at")},
        ),
        (
            "Metadata",
            {"fields": ("created_at", "updated_at", "last_updated_from_census"), "classes": ("collapse",)},
        ),
    )
    
    def get_species_name(self, obj):
        """Display species name"""
        return obj.species.name if obj.species else "Unknown"
    get_species_name.short_description = "Species"
    get_species_name.admin_order_field = "species__name"


@admin.register(DataChangeRequest)
class DataChangeRequestAdmin(admin.ModelAdmin):
    list_display = [
        "get_request_summary",
        "requested_by",
        "site",
        "status",
        "requested_at",
        "reviewed_by",
        "reviewed_at",
    ]
    list_filter = ["status", "request_type", "requested_at", "reviewed_at"]
    search_fields = [
        "requested_by__first_name",
        "requested_by__last_name",
        "requested_by__employee_id",
        "site__name",
        "reason",
    ]
    readonly_fields = ["id", "requested_at", "reviewed_at", "completed_at"]
    fieldsets = (
        ("Request Information", {"fields": ("request_type", "status", "site", "census")}),
        ("Request Details", {"fields": ("request_data", "reason")}),
        ("Requester Information", {"fields": ("requested_by", "requested_at")}),
        ("Review Information", {"fields": ("reviewed_by", "reviewed_at", "review_notes")}),
        ("Completion", {"fields": ("completed_at",)}),
        ("Metadata", {"fields": ("id",), "classes": ("collapse",)}),
    )
    
    def get_request_summary(self, obj):
        """Display request type and summary"""
        return f"{obj.get_request_type_display()}"
    get_request_summary.short_description = "Request Type"
    get_request_summary.admin_order_field = "request_type"
