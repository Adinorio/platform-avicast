"""
Views for family-grouped data display and totals
AGENTS.md §3 File Organization - Separate views for family/totals functionality
"""

from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from django.shortcuts import get_object_or_404, render
from django.http import JsonResponse

from .models import Site, CensusYear, CensusMonth, CensusObservation


@login_required
def family_grouped_view(request, site_id, year=None, month=None):
    """
    Display census data organized by families
    Shows family groupings with species counts and totals
    """
    site = get_object_or_404(Site, id=site_id)
    
    # Build query for observations
    observations = CensusObservation.objects.filter(
        census__month__year__site=site
    ).select_related(
        'census__month__year',
        'species'
    ).order_by('census__month__year__year', 'census__month__month', 'species_name')
    
    # Apply filters
    if year:
        year_obj = get_object_or_404(CensusYear, site=site, year=year)
        observations = observations.filter(census__month__year=year_obj)
        if month:
            month_obj = get_object_or_404(CensusMonth, year=year_obj, month=month)
            observations = observations.filter(census__month=month_obj)
    
    # Group observations by family (use the family field from the model)
    family_data = {}
    
    for obs in observations:
        # Use the family field from the model, or extract from species_name if not set
        species_name = obs.species_name  # Always define species_name first
        
        if obs.family:
            family_name = obs.family.strip()
        else:
            # Fallback: extract family from species_name (format: "FAMILY: SPECIES" or just "SPECIES")
            if ':' in species_name:
                family_name, species_name = species_name.split(':', 1)
                family_name = family_name.strip()
                species_name = species_name.strip()
            else:
                family_name = 'UNCATEGORIZED'
        
        if family_name not in family_data:
            family_data[family_name] = {
                'species': {},
                'total_birds': 0,
                'total_observations': 0,
                'months': {}
            }
        
        # Group by species within family
        if species_name not in family_data[family_name]['species']:
            family_data[family_name]['species'][species_name] = {
                'total_count': 0,
                'observations': [],
                'months': {}
            }
        
        # Add observation
        family_data[family_name]['species'][species_name]['observations'].append(obs)
        family_data[family_name]['species'][species_name]['total_count'] += obs.count
        family_data[family_name]['total_birds'] += obs.count
        family_data[family_name]['total_observations'] += 1
        
        # Track by month
        month_key = f"{obs.census.month.year.year}-{obs.census.month.month:02d}"
        if month_key not in family_data[family_name]['months']:
            family_data[family_name]['months'][month_key] = 0
        family_data[family_name]['months'][month_key] += obs.count
        
        if month_key not in family_data[family_name]['species'][species_name]['months']:
            family_data[family_name]['species'][species_name]['months'][month_key] = 0
        family_data[family_name]['species'][species_name]['months'][month_key] += obs.count
    
    # Define family order as shown in species detection summary
    family_order = [
        'HERONS AND EGRETS',
        'SHOREBIRDS-WADERS', 
        'RAILS, GALLINULES & COOTS',
        'GULLS, TERNS & SKIMMERRS',
        'ADDITIONAL SPECIES',
        'UNCATEGORIZED'
    ]
    
    # Sort family_data by the defined order
    sorted_family_data = {}
    for family_name in family_order:
        if family_name in family_data:
            sorted_family_data[family_name] = family_data[family_name]
    
    # Add any remaining families not in the predefined order
    for family_name, family_info in family_data.items():
        if family_name not in sorted_family_data:
            sorted_family_data[family_name] = family_info
    
    # Calculate site totals
    site_totals = {
        'total_families': len(family_data),
        'total_species': sum(len(family['species']) for family in family_data.values()),
        'total_birds': sum(family['total_birds'] for family in family_data.values()),
        'total_observations': sum(family['total_observations'] for family in family_data.values()),
    }
    
    # Get available years and months for filtering
    available_years = CensusYear.objects.filter(site=site).order_by('-year')
    available_months = CensusMonth.objects.filter(year__site=site).order_by('year__year', 'month')
    
    context = {
        'site': site,
        'year': year,
        'month': month,
        'family_data': sorted_family_data,
        'site_totals': site_totals,
        'available_years': available_years,
        'available_months': available_months,
    }
    
    return render(request, 'locations/family_grouped_view.html', context)


@login_required
def site_totals_view(request, site_id):
    """
    Display comprehensive totals for a site across all years/months
    Shows yearly, monthly, and family breakdowns
    """
    site = get_object_or_404(Site, id=site_id)
    
    # Get all observations for this site
    observations = CensusObservation.objects.filter(
        census__month__year__site=site
    ).select_related(
        'census__month__year',
        'species'
    )
    
    # Calculate yearly totals
    yearly_data = {}
    for obs in observations:
        year = obs.census.month.year.year
        if year not in yearly_data:
            yearly_data[year] = {
                'total_birds': 0,
                'total_species': set(),
                'total_observations': 0,
                'months': {}
            }
        
        yearly_data[year]['total_birds'] += obs.count
        yearly_data[year]['total_species'].add(obs.species_name)
        yearly_data[year]['total_observations'] += 1
        
        # Monthly breakdown within year
        month = obs.census.month.month
        if month not in yearly_data[year]['months']:
            yearly_data[year]['months'][month] = {
                'total_birds': 0,
                'species': set(),
                'observations': 0
            }
        
        yearly_data[year]['months'][month]['total_birds'] += obs.count
        yearly_data[year]['months'][month]['species'].add(obs.species_name)
        yearly_data[year]['months'][month]['observations'] += 1
    
    # Convert sets to counts for JSON serialization
    for year_data in yearly_data.values():
        year_data['total_species'] = len(year_data['total_species'])
        for month_data in year_data['months'].values():
            month_data['species'] = len(month_data['species'])
    
    # Calculate overall site totals
    site_totals = {
        'total_years': len(yearly_data),
        'total_birds': sum(year_data['total_birds'] for year_data in yearly_data.values()),
        'total_species': len(set(obs.species_name for obs in observations)),
        'total_observations': observations.count(),
    }
    
    # Get top species
    species_counts = {}
    for obs in observations:
        if obs.species_name not in species_counts:
            species_counts[obs.species_name] = 0
        species_counts[obs.species_name] += obs.count
    
    top_species = sorted(species_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    context = {
        'site': site,
        'yearly_data': yearly_data,
        'site_totals': site_totals,
        'top_species': top_species,
    }
    
    return render(request, 'locations/site_totals_view.html', context)


@login_required
def family_totals_api(request, site_id):
    """
    API endpoint to get family totals as JSON
    Useful for AJAX requests and data visualization
    """
    site = get_object_or_404(Site, id=site_id)
    
    # Get observations
    observations = CensusObservation.objects.filter(
        census__month__year__site=site
    ).values('species_name').annotate(
        total_count=Sum('count'),
        observation_count=Count('id')
    ).order_by('-total_count')
    
    # Extract families and group data
    family_data = {}
    
    for obs in observations:
        species_name = obs['species_name']
        
        # Extract family (simple approach - look for common patterns)
        if any(family in species_name.upper() for family in ['HERON', 'EGRET']):
            family_name = 'HERONS AND EGRETS'
        elif any(family in species_name.upper() for family in ['SPOONBILL', 'IBIS']):
            family_name = 'SPOONBILLS AND IBIS'
        elif any(family in species_name.upper() for family in ['SANDPIPER', 'PLOVER', 'GODWIT']):
            family_name = 'SHOREBIRDS'
        elif any(family in species_name.upper() for family in ['DUCK', 'GOOSE', 'SWAN']):
            family_name = 'WATERFOWL'
        else:
            family_name = 'OTHER BIRDS'
        
        if family_name not in family_data:
            family_data[family_name] = {
                'total_birds': 0,
                'total_species': 0,
                'total_observations': 0,
                'species': []
            }
        
        family_data[family_name]['total_birds'] += obs['total_count']
        family_data[family_name]['total_species'] += 1
        family_data[family_name]['total_observations'] += obs['observation_count']
        family_data[family_name]['species'].append({
            'name': species_name,
            'count': obs['total_count'],
            'observations': obs['observation_count']
        })
    
    return JsonResponse({
        'site_name': site.name,
        'families': family_data,
        'total_families': len(family_data),
        'total_birds': sum(family['total_birds'] for family in family_data.values()),
        'total_species': sum(family['total_species'] for family in family_data.values()),
    })
