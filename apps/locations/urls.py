from django.urls import path

from .views import (
    bulk_census_import_cancel,
    bulk_census_import_list,
    bulk_census_import_process,
    bulk_census_import_review,
    bulk_census_import_upload,
    bulk_import_actions,
    census_archive,
    census_create,
    census_dashboard,
    census_delete,
    census_export_csv,
    census_export_excel,
    census_import,
    census_restore,
    census_update,
    get_individual_birds_api,
    mobile_import_list,
    review_mobile_import,
    site_create,
    site_dashboard,
    site_delete,
    site_detail,
    site_list,
    site_update,
    submit_mobile_import,
    verify_species_count,
)
from .request_views import (
    request_list,
    submit_request,
    review_request,
    bulk_request_actions,
)
from .map_views import (
    sites_map_view,
    species_heatmap_view,
    site_map_data_api,
)

app_name = "locations"

urlpatterns = [
    # Site management dashboard (main entry point)
    path("", site_dashboard, name="dashboard"),

    # Site management
    path("sites/", site_list, name="site_list"),
    path("sites/create/", site_create, name="site_create"),
    path("sites/<uuid:site_id>/", site_detail, name="site_detail"),
    path("sites/<uuid:site_id>/update/", site_update, name="site_update"),
    path("sites/<uuid:site_id>/delete/", site_delete, name="site_delete"),
    # Species count verification
    path("species-count/<uuid:count_id>/verify/", verify_species_count, name="verify_species_count"),
    # Census management
    path("census/", census_dashboard, name="census_dashboard"),
    path("sites/<uuid:site_id>/census/create/", census_create, name="census_create"),
    path("census/<uuid:census_id>/update/", census_update, name="census_update"),
    path("census/<uuid:census_id>/delete/", census_delete, name="census_delete"),
    path("census/<uuid:census_id>/archive/", census_archive, name="census_archive"),
    path("census/<uuid:census_id>/restore/", census_restore, name="census_restore"),
    path("api/census/<uuid:census_id>/individual-birds/", get_individual_birds_api, name="get_individual_birds_api"),
    # Census import/export
    path("sites/<uuid:site_id>/census/import/", census_import, name="census_import"),
    path("sites/<uuid:site_id>/census/export/csv/", census_export_csv, name="census_export_csv"),
    path(
        "sites/<uuid:site_id>/census/export/excel/", census_export_excel, name="census_export_excel"
    ),
    # Bulk import
    path("bulk-imports/", bulk_census_import_list, name="bulk_census_import_list"),
    path("bulk-imports/upload/", bulk_census_import_upload, name="bulk_census_import_upload"),
    path("bulk-imports/<uuid:import_id>/review/", bulk_census_import_review, name="bulk_census_import_review"),
    path("bulk-imports/<uuid:import_id>/process/", bulk_census_import_process, name="bulk_census_import_process"),
    path("bulk-imports/<uuid:import_id>/cancel/", bulk_census_import_cancel, name="bulk_census_import_cancel"),
    # Mobile data import
    path("mobile-imports/", mobile_import_list, name="mobile_import_list"),
    path("mobile-imports/submit/", submit_mobile_import, name="submit_mobile_import"),
    path(
        "mobile-imports/<uuid:import_id>/review/", review_mobile_import, name="review_mobile_import"
    ),
    path("mobile-imports/bulk-actions/", bulk_import_actions, name="bulk_import_actions"),
    # Data change requests
    path("requests/", request_list, name="request_list"),
    path("requests/submit/", submit_request, name="submit_request"),
    path("requests/<uuid:request_id>/review/", review_request, name="review_request"),
    path("requests/bulk-actions/", bulk_request_actions, name="bulk_request_actions"),
    # Interactive maps
    path("map/", sites_map_view, name="sites_map"),
    path("map/heatmap/", species_heatmap_view, name="species_heatmap"),
    path("api/map-data/", site_map_data_api, name="site_map_data_api"),
]
