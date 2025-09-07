from django.contrib import admin

from .models import CensusObservation, Site, SpeciesObservation


class SpeciesObservationInline(admin.TabularInline):
    model = SpeciesObservation
    extra = 1
    fields = ["species_name", "count", "behavior_notes"]


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
    list_display = ["species_name", "census", "count", "behavior_notes", "created_at"]
    list_filter = ["census__site", "census__observation_date", "created_at"]
    search_fields = ["species_name", "behavior_notes", "census__site__name"]
    readonly_fields = ["id", "created_at", "updated_at"]
    fieldsets = (
        ("Species Details", {"fields": ("census", "species_name", "count", "behavior_notes")}),
        ("Metadata", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )
