from django.urls import path
from .views import (
    site_list, site_detail, site_create, site_update, site_delete,
    census_create, census_update, census_delete,
    census_import, census_export_csv, census_export_excel
)

app_name = 'locations'

urlpatterns = [
    # Site management
    path('sites/', site_list, name='site_list'),
    path('sites/create/', site_create, name='site_create'),
    path('sites/<uuid:site_id>/', site_detail, name='site_detail'),
    path('sites/<uuid:site_id>/update/', site_update, name='site_update'),
    path('sites/<uuid:site_id>/delete/', site_delete, name='site_delete'),
    
    # Census management
    path('sites/<uuid:site_id>/census/create/', census_create, name='census_create'),
    path('census/<uuid:census_id>/update/', census_update, name='census_update'),
    path('census/<uuid:census_id>/delete/', census_delete, name='census_delete'),
    
    # Census import/export
    path('sites/<uuid:site_id>/census/import/', census_import, name='census_import'),
    path('sites/<uuid:site_id>/census/export/csv/', census_export_csv, name='census_export_csv'),
    path('sites/<uuid:site_id>/census/export/excel/', census_export_excel, name='census_export_excel'),
] 