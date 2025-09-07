from django.urls import path

from .views import (
    bulk_import_actions,
    census_create,
    census_delete,
    census_export_csv,
    census_export_excel,
    census_import,
    census_update,
    mobile_import_list,
    review_mobile_import,
    site_create,
    site_delete,
    site_detail,
    site_list,
    site_update,
    submit_mobile_import,
)

app_name = "locations"

urlpatterns = [
    # Site management
    path("sites/", site_list, name="site_list"),
    path("sites/create/", site_create, name="site_create"),
    path("sites/<uuid:site_id>/", site_detail, name="site_detail"),
    path("sites/<uuid:site_id>/update/", site_update, name="site_update"),
    path("sites/<uuid:site_id>/delete/", site_delete, name="site_delete"),
    # Census management
    path("sites/<uuid:site_id>/census/create/", census_create, name="census_create"),
    path("census/<uuid:census_id>/update/", census_update, name="census_update"),
    path("census/<uuid:census_id>/delete/", census_delete, name="census_delete"),
    # Census import/export
    path("sites/<uuid:site_id>/census/import/", census_import, name="census_import"),
    path("sites/<uuid:site_id>/census/export/csv/", census_export_csv, name="census_export_csv"),
    path(
        "sites/<uuid:site_id>/census/export/excel/", census_export_excel, name="census_export_excel"
    ),
    # Mobile data import
    path("mobile-imports/", mobile_import_list, name="mobile_import_list"),
    path("mobile-imports/submit/", submit_mobile_import, name="submit_mobile_import"),
    path(
        "mobile-imports/<uuid:import_id>/review/", review_mobile_import, name="review_mobile_import"
    ),
    path("mobile-imports/bulk-actions/", bulk_import_actions, name="bulk_import_actions"),
]
