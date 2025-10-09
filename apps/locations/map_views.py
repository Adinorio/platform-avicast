"""
Interactive map views for locations app.
Displays sites on a map with detailed popups and filtering.
"""

import json
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from django.shortcuts import render
from django.http import JsonResponse

from .models import Site, SiteSpeciesCount, CensusObservation
from .utils.coordinates import parse_coordinates
from apps.fauna.models import Species


@login_required
def sites_map_view(request):
    """Display all sites on an interactive Leaflet.js map"""
    # Get all sites with their coordinates
    sites = Site.objects.filter(
        status='active'
    ).prefetch_related('species_counts')

    # Prepare site data for map
    site_data = []
    for site in sites:
        # Parse coordinates (supports both decimal and DMS formats)
        coords = parse_coordinates(site.coordinates)
        if not coords:
            continue
        
        lat, lon = coords

        # Get site statistics
        species_counts = SiteSpeciesCount.objects.filter(
            site=site,
            is_verified=True
        )
        
        total_birds = species_counts.aggregate(
            total=Sum('total_count')
        )['total'] or 0
        
        species_diversity = species_counts.count()
        
        # Get recent census count
        recent_census = CensusObservation.objects.filter(
            site=site
        ).count()

        # Get top species
        top_species = species_counts.order_by('-total_count')[:3]
        top_species_list = [
            {
                'name': sc.species.name if sc.species else 'Unknown',
                'count': sc.total_count
            }
            for sc in top_species
        ]

        site_data.append({
            'id': str(site.id),
            'name': site.name,
            'lat': lat,
            'lon': lon,
            'site_type': site.get_site_type_display(),
            'status': site.get_status_display(),
            'description': site.description[:200] if site.description else '',
            'total_birds': total_birds,
            'species_diversity': species_diversity,
            'recent_census': recent_census,
            'top_species': top_species_list,
            'area_hectares': float(site.area_hectares) if site.area_hectares else None,
        })

    # Get filter options
    site_types = Site.SITE_TYPES
    
    # Get species for species filter
    species_list = Species.objects.all().order_by('name')

    context = {
        'sites_json': json.dumps(site_data),
        'site_count': len(site_data),
        'site_types': site_types,
        'species_list': species_list,
    }

    return render(request, 'locations/sites_map.html', context)


@login_required
def species_heatmap_view(request):
    """Display species distribution heat map"""
    species_id = request.GET.get('species_id', None)
    
    if not species_id:
        # Show all species aggregated
        sites = Site.objects.filter(
            status='active',
            coordinates__isnull=False
        ).exclude(coordinates='')
        
        heat_data = []
        for site in sites:
            coords = parse_coordinates(site.coordinates)
            if not coords:
                continue
            
            lat, lon = coords
            
            # Get total bird count at this site
            total_count = SiteSpeciesCount.objects.filter(
                site=site,
                is_verified=True
            ).aggregate(total=Sum('total_count'))['total'] or 0
            
            if total_count > 0:
                heat_data.append({
                    'lat': lat,
                    'lon': lon,
                    'intensity': total_count
                })
    else:
        # Show specific species distribution
        species = Species.objects.get(id=species_id)
        species_counts = SiteSpeciesCount.objects.filter(
            species=species,
            is_verified=True
        ).select_related('site')
        
        heat_data = []
        for sc in species_counts:
            site = sc.site
            coords = parse_coordinates(site.coordinates)
            if not coords:
                continue
            
            lat, lon = coords
            
            heat_data.append({
                'lat': lat,
                'lon': lon,
                'intensity': sc.total_count,
                'site_name': site.name
            })

    # Get all species for filter
    species_list = Species.objects.all().order_by('name')

    context = {
        'heat_data_json': json.dumps(heat_data),
        'species_list': species_list,
        'selected_species_id': species_id,
    }

    return render(request, 'locations/species_heatmap.html', context)


@login_required
def site_map_data_api(request):
    """API endpoint to get site data for map (AJAX)"""
    # Filters
    site_type = request.GET.get('type', '')
    min_species = request.GET.get('min_species', 0)
    species_filter = request.GET.get('species', '')

    # Build query
    sites = Site.objects.filter(
        status='active',
        coordinates__isnull=False
    ).exclude(coordinates='')

    if site_type:
        sites = sites.filter(site_type=site_type)

    # Prepare response data
    site_data = []
    for site in sites:
        coords = parse_coordinates(site.coordinates)
        if not coords:
            continue
        
        lat, lon = coords

        # Get site statistics
        species_counts = SiteSpeciesCount.objects.filter(
            site=site,
            is_verified=True
        )

        # Apply species filter if specified
        if species_filter:
            species_counts = species_counts.filter(species_id=species_filter)
            if not species_counts.exists():
                continue

        species_diversity = species_counts.count()

        # Apply min species filter
        if int(min_species) > 0 and species_diversity < int(min_species):
            continue

        total_birds = species_counts.aggregate(
            total=Sum('total_count')
        )['total'] or 0

        # Get top species
        top_species = species_counts.order_by('-total_count')[:3]
        top_species_list = [
            {
                'name': sc.species.name if sc.species else 'Unknown',
                'count': sc.total_count
            }
            for sc in top_species
        ]

        site_data.append({
            'id': str(site.id),
            'name': site.name,
            'lat': lat,
            'lon': lon,
            'site_type': site.get_site_type_display(),
            'total_birds': total_birds,
            'species_diversity': species_diversity,
            'top_species': top_species_list,
        })

    return JsonResponse({
        'success': True,
        'sites': site_data,
        'count': len(site_data)
    })

