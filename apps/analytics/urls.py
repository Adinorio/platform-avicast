from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    # Dashboard
    path('', views.analytics_dashboard, name='dashboard'),
    
    # Chart endpoints
    path('charts/species-diversity/', views.species_diversity_chart, name='species_diversity_chart'),
    path('charts/population-trends/', views.population_trends_chart, name='population_trends_chart'),
    path('charts/seasonal-analysis/', views.seasonal_analysis_chart, name='seasonal_analysis_chart'),
    path('charts/site-comparison/', views.site_comparison_chart, name='site_comparison_chart'),
    
    # Reports
    path('reports/census/', views.generate_census_report, name='generate_census_report'),
    path('reports/census/<uuid:site_id>/', views.generate_census_report, name='generate_site_census_report'),
    
    # Gallery
    path('gallery/', views.chart_gallery, name='chart_gallery'),
] 