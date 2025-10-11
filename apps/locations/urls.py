"""
URLs for locations app
Following the card-based user flow: Site -> Year -> Month -> Census Table
"""

from django.urls import path
from . import views

app_name = "locations"

urlpatterns = [
    # Main dashboard - Site cards
    path("", views.site_dashboard, name="dashboard"),

    # Site management (CRUD)
    path("sites/", views.site_list, name="site_list"),
    path("sites/create/", views.site_create, name="site_create"),
    path("sites/<uuid:site_id>/", views.site_detail, name="site_detail"),
    path("sites/<uuid:site_id>/edit/", views.site_edit, name="site_edit"),
    path("sites/<uuid:site_id>/delete/", views.site_delete, name="site_delete"),

    # Year management (card-based)
    path("sites/<uuid:site_id>/years/", views.year_list, name="year_list"),
    path("sites/<uuid:site_id>/years/create/", views.year_create, name="year_create"),
    path("sites/<uuid:site_id>/years/<int:year>/", views.year_detail, name="year_detail"),
    path("sites/<uuid:site_id>/years/<int:year>/edit/", views.year_edit, name="year_edit"),
    path("sites/<uuid:site_id>/years/<int:year>/delete/", views.year_delete, name="year_delete"),

    # Month management (card-based)
    path("sites/<uuid:site_id>/years/<int:year>/months/", views.month_list, name="month_list"),
    path("sites/<uuid:site_id>/years/<int:year>/months/create/", views.month_create, name="month_create"),
    path("sites/<uuid:site_id>/years/<int:year>/months/<int:month>/", views.month_detail, name="month_detail"),
    path("sites/<uuid:site_id>/years/<int:year>/months/<int:month>/edit/", views.month_edit, name="month_edit"),
    path("sites/<uuid:site_id>/years/<int:year>/months/<int:month>/delete/", views.month_delete, name="month_delete"),

    # Census management (tabular)
    path("sites/<uuid:site_id>/years/<int:year>/months/<int:month>/census/", views.census_list, name="census_list"),
    path("sites/<uuid:site_id>/years/<int:year>/months/<int:month>/census/create/", views.census_create, name="census_create"),
    path("sites/<uuid:site_id>/years/<int:year>/months/<int:month>/census/<uuid:census_id>/", views.census_detail, name="census_detail"),
    path("sites/<uuid:site_id>/years/<int:year>/months/<int:month>/census/<uuid:census_id>/edit/", views.census_edit, name="census_edit"),
    path("sites/<uuid:site_id>/years/<int:year>/months/<int:month>/census/<uuid:census_id>/delete/", views.census_delete, name="census_delete"),

    # Observation management
    path("sites/<uuid:site_id>/years/<int:year>/months/<int:month>/census/<uuid:census_id>/observations/create/", views.observation_create, name="observation_create"),
    path("sites/<uuid:site_id>/years/<int:year>/months/<int:month>/census/<uuid:census_id>/observations/batch/", views.batch_observation_create, name="batch_observation_create"),
    path("sites/<uuid:site_id>/years/<int:year>/months/<int:month>/census/<uuid:census_id>/observations/<uuid:observation_id>/edit/", views.observation_edit, name="observation_edit"),
    path("sites/<uuid:site_id>/years/<int:year>/months/<int:month>/census/<uuid:census_id>/observations/<uuid:observation_id>/delete/", views.observation_delete, name="observation_delete"),

    # API endpoints for AJAX operations
    path("api/sites/<uuid:site_id>/coordinates/", views.update_coordinates, name="update_coordinates"),
    path("api/census/<uuid:census_id>/observations/", views.get_observations, name="get_observations"),
]