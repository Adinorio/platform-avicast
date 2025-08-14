from django.urls import path
from .views import (
    SiteListView, SiteDetailView, SiteCreateView, 
    SiteUpdateView, SiteDeleteView, SiteArchiveView
)

app_name = 'locations'

urlpatterns = [
    # Site management URLs
    path('sites/', SiteListView.as_view(), name='site_list'),
    path('sites/create/', SiteCreateView.as_view(), name='site_create'),
    path('sites/<uuid:pk>/', SiteDetailView.as_view(), name='site_detail'),
    path('sites/<uuid:pk>/edit/', SiteUpdateView.as_view(), name='site_update'),
    path('sites/<uuid:pk>/delete/', SiteDeleteView.as_view(), name='site_delete'),
    path('sites/<uuid:pk>/archive/', SiteArchiveView.as_view(), name='site_archive'),
] 