from django.urls import path

from .views import (
    SpeciesListView, SpeciesDetailView, SpeciesCreateView,
    SpeciesUpdateView, SpeciesDeleteView, SpeciesArchivedListView,
    SpeciesRestoreView, SpeciesSuggestionsView
)

app_name = "fauna"

urlpatterns = [
    path("species/", SpeciesListView.as_view(), name="species_list"),
    path("species/archived/", SpeciesArchivedListView.as_view(), name="species_archived_list"),
    path("species/create/", SpeciesCreateView.as_view(), name="species_create"),
    path("species/<uuid:pk>/", SpeciesDetailView.as_view(), name="species_detail"),
    path("species/<uuid:pk>/edit/", SpeciesUpdateView.as_view(), name="species_edit"),
    path("species/<uuid:pk>/delete/", SpeciesDeleteView.as_view(), name="species_delete"),
    path("species/<uuid:pk>/restore/", SpeciesRestoreView.as_view(), name="species_restore"),
    
    # Smart Matching API
    path("api/species/suggestions/", SpeciesSuggestionsView.as_view(), name="species_suggestions"),
]