from django.contrib import admin

from .models import Species


@admin.register(Species)
class SpeciesAdmin(admin.ModelAdmin):
    list_display = ("name", "scientific_name", "iucn_status", "is_archived")
    list_filter = ("iucn_status", "is_archived")
    search_fields = ("name", "scientific_name")
