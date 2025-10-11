"""
URL configuration for the new focused analytics app
"""

from django.urls import path

from . import views

app_name = "analytics_new"

urlpatterns = [
    # Main dashboard
    path("", views.dashboard_view, name="dashboard"),
    path("dashboard/", views.dashboard_view, name="dashboard"),

    # Species analytics
    path("species/", views.species_analytics_view, name="species_analytics"),

    # Site analytics
    path("sites/", views.site_analytics_view, name="site_analytics"),

    # Census records
    path("census/", views.census_records_view, name="census_records"),
    path("census/verify/<uuid:record_id>/", views.verify_census_record, name="verify_census_record"),

    # Population trends
    path("trends/", views.population_trends_view, name="population_trends"),

    # Report generation
    path("reports/", views.report_generator_view, name="report_generator"),
    path("reports/<uuid:report_id>/", views.report_detail_view, name="report_detail"),
]















