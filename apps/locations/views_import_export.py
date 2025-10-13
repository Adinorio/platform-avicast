"""
Import/Export Views for Census Data
AGENTS.md §3 File Organization - Separate views file to keep under 500 lines
AGENTS.md §6.1 Security - Role-based access control for data import
"""

from datetime import datetime
from io import BytesIO

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.db.models import Sum, Count, Q
from django.core.paginator import Paginator

from .models import Site, CensusYear, CensusMonth, Census, CensusObservation
from .utils.excel_handler import CensusExcelHandler, ExcelImportError
from apps.fauna.models import Species


@login_required
def census_import_export_hub(request):
    """
    Main hub for import/export operations
    Shows current data statistics and access to import/export functions
    """
    # Get statistics
    total_sites = Site.objects.filter(status='active').count()
    total_census = Census.objects.count()
    total_observations = CensusObservation.objects.count()
    total_species = CensusObservation.objects.values('species').distinct().count()
    
    # Get recent imports (from user activity logs if available)
    recent_activity = []
    
    context = {
        'total_sites': total_sites,
        'total_census': total_census,
        'total_observations': total_observations,
        'total_species': total_species,
        'recent_activity': recent_activity,
    }
    
    return render(request, 'locations/import_export_hub.html', context)


@login_required
def download_import_template(request):
    """
    Download Excel template for census data import
    Generates a formatted Excel file with instructions
    """
    try:
        wb = CensusExcelHandler.generate_template()
        
        # Save to BytesIO
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        
        # Create response
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="census_import_template.xlsx"'
        
        return response
        
    except Exception as e:
        messages.error(request, f"Error generating template: {str(e)}")
        return redirect('locations:import_export_hub')


@login_required
@require_http_methods(["GET", "POST"])
def import_census_data(request):
    """
    Import census data from Excel file
    Validates and bulk imports historical census records
    """
    if request.method == 'POST':
        # Check if file was uploaded
        if 'excel_file' not in request.FILES:
            messages.error(request, "Please select an Excel file to upload")
            return redirect('locations:import_census_data')
        
        excel_file = request.FILES['excel_file']
        
        # Validate file extension
        if not excel_file.name.endswith(('.xlsx', '.xls')):
            messages.error(request, "Please upload a valid Excel file (.xlsx or .xls)")
            return redirect('locations:import_census_data')
        
        try:
            # Detect Excel structure first
            structure = CensusExcelHandler.detect_excel_structure(excel_file)
            
            # Preview data first (don't import yet)
            preview_results = CensusExcelHandler.preview_import(excel_file, request.user)
            
            # Store file content as base64 string for session storage
            import base64
            excel_file.seek(0)  # Reset file pointer
            file_content = excel_file.read()
            file_content_b64 = base64.b64encode(file_content).decode('utf-8')
            
            # Store preview results in session (without file object)
            preview_results['file_content_b64'] = file_content_b64
            preview_results['detected_structure'] = structure  # Store detected structure
            preview_results.pop('file_data', None)  # Remove the file object
            
            request.session['import_preview'] = preview_results
            request.session['import_filename'] = excel_file.name
            
            return redirect('locations:import_preview')
            
        except ExcelImportError as e:
            messages.error(request, f"Import failed: {str(e)}")
            return redirect('locations:import_census_data')
        except Exception as e:
            messages.error(request, f"Unexpected error during import: {str(e)}")
            return redirect('locations:import_census_data')
    
    # GET request - show upload form
    from .utils.ai_census_helper import get_ai_helper

    ai = get_ai_helper()
    ai_available = ai.is_available()

    context = {
        'sites_count': Site.objects.filter(status='active').count(),
        'ai_available': ai_available,
        'species_count': Species.objects.count(),
    }
    return render(request, 'locations/import_census_data.html', context)


@login_required
def import_preview(request):
    """
    Step 2: Show preview of what will be imported
    Allow user to confirm before actually importing
    """
    preview_data = request.session.get('import_preview')
    filename = request.session.get('import_filename', 'Unknown file')
    
    if not preview_data:
        messages.error(request, "No import preview found. Please upload a file first.")
        return redirect('locations:import_census_data')
    
    # Check which sites already exist
    from apps.locations.models import Site
    existing_sites = Site.objects.filter(name__in=preview_data.get('sites', [])).values_list('name', flat=True)
    
    context = {
        'preview_data': preview_data,
        'filename': filename,
        'has_errors': len(preview_data.get('errors', [])) > 0,
        'has_warnings': len(preview_data.get('warnings', [])) > 0,
        'existing_sites': existing_sites,
    }
    
    return render(request, 'locations/import_preview.html', context)


@login_required
def confirm_import(request):
    """
    Step 3: Actually import the data after user confirmation
    """
    if request.method != 'POST':
        return redirect('locations:import_census_data')
    
    preview_data = request.session.get('import_preview')
    filename = request.session.get('import_filename', 'Unknown file')
    
    if not preview_data:
        messages.error(request, "No import preview found. Please upload a file first.")
        return redirect('locations:import_census_data')
    
    # Get form data
    import_year = request.POST.get('import_year')
    if not import_year:
        messages.error(request, "Please select a year for the data.")
        return redirect('locations:import_preview')
    
    # Collect site coordinates
    site_coordinates = {}
    for key, value in request.POST.items():
        if key.startswith('site_') and key.endswith('_latitude'):
            site_name = key.replace('site_', '').replace('_latitude', '')
            lat = request.POST.get(f'site_{site_name}_latitude')
            lng = request.POST.get(f'site_{site_name}_longitude')
            if lat and lng:
                site_coordinates[site_name] = f"{lat}, {lng}"
    
    try:
        # Recreate file object from stored base64 content
        import base64
        from django.core.files.uploadedfile import InMemoryUploadedFile
        from io import BytesIO
        
        file_content_b64 = preview_data['file_content_b64']
        file_content = base64.b64decode(file_content_b64.encode('utf-8'))
        file_buffer = BytesIO(file_content)
        
        # Create a new InMemoryUploadedFile object
        recreated_file = InMemoryUploadedFile(
            file_buffer,
            None,
            filename,
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            len(file_content),
            None
        )
        
        # Re-import with actual data creation (pass year and coordinates)
        results = CensusExcelHandler.import_from_excel(recreated_file, request.user, import_year, site_coordinates)
        
        # Show results
        if results['successful'] > 0:
            messages.success(
                request,
                f"Successfully imported {results['successful']} observations! "
                f"Created {results['created_census']} census records and "
                f"{results['created_observations']} observations."
            )
        
        if results['skipped'] > 0:
            messages.warning(
                request,
                f"{results['skipped']} rows were skipped due to errors. "
                f"See details below."
            )
        
        # Store results in session for display
        if results['errors']:
            request.session['import_errors'] = results['errors']
        if results.get('info_messages'):
            request.session['import_info_messages'] = results['info_messages']
        request.session['import_ai_matches'] = results.get('ai_matches', 0)
        request.session['import_created_species'] = results.get('created_species', 0)
        
        # Clear preview data
        request.session.pop('import_preview', None)
        request.session.pop('import_filename', None)

        return redirect('locations:import_results')
        
    except ExcelImportError as e:
        messages.error(request, f"Import failed: {str(e)}")
        return redirect('locations:import_preview')
    except Exception as e:
        messages.error(request, f"Unexpected error during import: {str(e)}")
        return redirect('locations:import_preview')


@login_required
def import_results(request):
    """Display import results with errors if any"""
    errors = request.session.pop('import_errors', [])
    info_messages = request.session.pop('import_info_messages', [])
    ai_matches = request.session.pop('import_ai_matches', 0)
    created_species = request.session.pop('import_created_species', 0)

    context = {
        'errors': errors,
        'info_messages': info_messages,
        'has_errors': len(errors) > 0,
        'ai_matches': ai_matches,
        'created_species': created_species,
    }

    return render(request, 'locations/import_results.html', context)


@login_required
def export_census_data(request):
    """
    Export census data to Excel with filters
    Allows filtering by site, year, month, date range
    """
    if request.method == 'POST':
        # Get filter parameters
        filters = {}
        
        if request.POST.get('site_id'):
            filters['site_id'] = request.POST.get('site_id')
        
        if request.POST.get('year'):
            filters['year'] = int(request.POST.get('year'))
        
        if request.POST.get('month'):
            filters['month'] = int(request.POST.get('month'))
        
        if request.POST.get('start_date'):
            filters['start_date'] = datetime.strptime(
                request.POST.get('start_date'), '%Y-%m-%d'
            ).date()
        
        if request.POST.get('end_date'):
            filters['end_date'] = datetime.strptime(
                request.POST.get('end_date'), '%Y-%m-%d'
            ).date()
        
        try:
            # Generate export
            wb = CensusExcelHandler.export_to_excel(filters)
            
            # Save to BytesIO
            output = BytesIO()
            wb.save(output)
            output.seek(0)
            
            # Generate filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"census_data_export_{timestamp}.xlsx"
            
            # Create response
            response = HttpResponse(
                output.read(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            return response
            
        except Exception as e:
            messages.error(request, f"Error generating export: {str(e)}")
            return redirect('locations:export_census_data')
    
    # GET request - show filter form
    sites = Site.objects.filter(status='active').order_by('name')
    years = CensusYear.objects.values_list('year', flat=True).distinct().order_by('-year')
    
    context = {
        'sites': sites,
        'years': years,
        'months': range(1, 13),
    }
    
    return render(request, 'locations/export_census_data.html', context)


@login_required
def census_totals_view(request):
    """
    Aggregated view showing total birds by site, year, and month
    This is the main view for seeing "total number of birds within the site
    that are picked within their respective year and month"
    """
    # Get filter parameters
    selected_site = request.GET.get('site')
    selected_year = request.GET.get('year')
    selected_month = request.GET.get('month')
    
    # Build base query
    observations = CensusObservation.objects.select_related(
        'census__month__year__site',
        'species'
    )
    
    # Apply filters
    filters_applied = {}
    if selected_site:
        observations = observations.filter(census__month__year__site_id=selected_site)
        filters_applied['site'] = Site.objects.get(id=selected_site)
    
    if selected_year:
        observations = observations.filter(census__month__year__year=int(selected_year))
        filters_applied['year'] = int(selected_year)
    
    if selected_month:
        observations = observations.filter(census__month__month=int(selected_month))
        filters_applied['month'] = int(selected_month)
    
    # Aggregate totals by site, year, month
    totals = observations.values(
        'census__month__year__site__name',
        'census__month__year__site__id',
        'census__month__year__year',
        'census__month__month'
    ).annotate(
        total_birds=Sum('count'),
        total_species=Count('species', distinct=True),
        census_count=Count('census', distinct=True)
    ).order_by(
        'census__month__year__site__name',
        '-census__month__year__year',
        'census__month__month'
    )
    
    # Pagination
    paginator = Paginator(totals, 25)  # Show 25 records per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculate grand totals
    grand_total_birds = observations.aggregate(total=Sum('count'))['total'] or 0
    grand_total_species = observations.values('species').distinct().count()
    grand_total_census = observations.values('census').distinct().count()
    
    # Get available filters
    sites = Site.objects.filter(status='active').order_by('name')
    years = CensusYear.objects.values_list('year', flat=True).distinct().order_by('-year')
    
    context = {
        'page_obj': page_obj,
        'totals': page_obj,
        'filters_applied': filters_applied,
        'grand_total_birds': grand_total_birds,
        'grand_total_species': grand_total_species,
        'grand_total_census': grand_total_census,
        'sites': sites,
        'years': years,
        'months': [
            {'num': 1, 'name': 'January'},
            {'num': 2, 'name': 'February'},
            {'num': 3, 'name': 'March'},
            {'num': 4, 'name': 'April'},
            {'num': 5, 'name': 'May'},
            {'num': 6, 'name': 'June'},
            {'num': 7, 'name': 'July'},
            {'num': 8, 'name': 'August'},
            {'num': 9, 'name': 'September'},
            {'num': 10, 'name': 'October'},
            {'num': 11, 'name': 'November'},
            {'num': 12, 'name': 'December'},
        ],
        'selected_site': selected_site,
        'selected_year': selected_year,
        'selected_month': selected_month,
    }
    
    return render(request, 'locations/census_totals.html', context)


@login_required
def census_species_breakdown(request):
    """
    Detailed breakdown showing counts per species for selected site/year/month
    """
    # Get filter parameters (required)
    site_id = request.GET.get('site')
    year = request.GET.get('year')
    month = request.GET.get('month')
    
    if not all([site_id, year, month]):
        messages.warning(request, "Please select site, year, and month to view breakdown")
        return redirect('locations:census_totals')
    
    # Get observations
    observations = CensusObservation.objects.filter(
        census__month__year__site_id=site_id,
        census__month__year__year=int(year),
        census__month__month=int(month)
    ).select_related('species', 'census')
    
    # Aggregate by species
    species_totals = observations.values(
        'species__name',
        'species__scientific_name',
        'species__iucn_status'
    ).annotate(
        total_count=Sum('count'),
        observation_count=Count('id')
    ).order_by('-total_count')
    
    # Get context info
    site = Site.objects.get(id=site_id)
    month_name = [
        '', 'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ][int(month)]
    
    context = {
        'species_totals': species_totals,
        'site': site,
        'year': year,
        'month': month,
        'month_name': month_name,
        'total_birds': observations.aggregate(total=Sum('count'))['total'] or 0,
        'total_species': species_totals.count(),
    }
    
    return render(request, 'locations/census_species_breakdown.html', context)

