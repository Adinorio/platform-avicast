from django.urls import path
from .views import SpeciesListView

app_name = 'fauna'

urlpatterns = [
    path('species/', SpeciesListView.as_view(), name='species_list'),
] 