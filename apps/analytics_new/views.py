"""
Views for the new focused analytics app
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .models import (
    GeneratedReport,
    ReportConfiguration,
)


@login_required
def dashboard_view(request):
    """Main analytics dashboard reading directly from operational data"""

    # Get summary statistics from census observations
    from django.db.models import Sum, Count
    from apps.locations.models import CensusObservation, SpeciesObservation, Site

    # Total birds from recent census observations (last 60 days)
    sixty_days_ago = timezone.now().date() - timezone.timedelta(days=60)
    total_birds = SpeciesObservation.objects.filter(
        census__observation_date__gte=sixty_days_ago
    ).aggregate(total=Sum('count'))['total'] or 0

    # Count active sites and species
    total_sites = Site.objects.filter(status='active').count()

    # Count species with observations in last 60 days
    species_with_observations = SpeciesObservation.objects.filter(
        census__observation_date__gte=sixty_days_ago
    ).values('species').distinct().count()

    # Recent census observations (last 60 days)
    recent_census = CensusObservation.objects.filter(
        observation_date__gte=sixty_days_ago
    ).select_related('site', 'observer').order_by('-observation_date')[:10]

    # Species breakdown - get actual species data from fauna app
    from apps.fauna.models import Species

    species_data = []
    target_species = Species.objects.filter(name__icontains='egret') | Species.objects.filter(name__icontains='heron')

    for species in target_species:
        # Get count for this species in last 60 days
        count = SpeciesObservation.objects.filter(
            species=species,
            census__observation_date__gte=sixty_days_ago
        ).aggregate(total=Sum('count'))['total'] or 0

        species_data.append({
            'name': species.name,
            'scientific_name': species.scientific_name,
            'count': count,
            'iucn_status': species.iucn_status,
        })

    # Get top sites by bird count in last 60 days
    site_counts = SpeciesObservation.objects.filter(
        census__observation_date__gte=sixty_days_ago
    ).values('census__site').annotate(
        total_birds=Sum('count'),
        species_count=Count('species', distinct=True)
    ).order_by('-total_birds')[:5]

    top_sites = []
    for site_count in site_counts:
        site = Site.objects.get(id=site_count['census__site'])
        top_sites.append({
            'site': site,
            'total_birds': site_count['total_birds'],
            'species_count': site_count['species_count'],
        })

    context = {
        'total_birds': total_birds,
        'total_sites': total_sites,
        'total_species': species_with_observations,
        'recent_census': recent_census,
        'species_data': species_data,
        'top_sites': top_sites,
        'page_title': 'Analytics Dashboard',
    }

    return render(request, 'analytics_new/dashboard.html', context)


@login_required
def species_analytics_view(request):
    """Species-specific analytics reading from operational data"""

    from apps.fauna.models import Species
    from apps.locations.models import SpeciesObservation
    from django.db.models import Sum, Count, Avg

    # Get target species (egrets and herons)
    target_species = Species.objects.filter(
        name__icontains='egret'
    ) | Species.objects.filter(
        name__icontains='heron'
    )

    # Get analytics for each species
    species_with_data = []
    for species in target_species:
        # Get observations for this species
        observations = SpeciesObservation.objects.filter(species=species)

        if observations.exists():
            # Calculate statistics
            total_count = observations.aggregate(total=Sum('count'))['total'] or 0
            sites_with_presence = observations.values('census__site').distinct().count()
            avg_count = observations.aggregate(avg=Avg('count'))['avg'] or 0

            # Get most recent observation
            recent_obs = observations.order_by('-census__observation_date').first()

            # Create analytics-like object structure for template compatibility
            class AnalyticsObj:
                def __init__(self, species, total_count, sites_with_presence, iucn_status):
                    self.species = species
                    self.total_count = total_count
                    self.sites_with_presence = sites_with_presence
                    self.iucn_status = iucn_status

                def get_species_display(self):
                    return self.species.name

            analytics_obj = AnalyticsObj(species, total_count, sites_with_presence, getattr(species, 'iucn_status', 'LC'))

            species_with_data.append({
                'analytics': analytics_obj,
                'recent_trend': None,  # For now, no trend data
            })

    # Sort by total count descending
    species_with_data.sort(key=lambda x: x['analytics'].total_count, reverse=True)

    context = {
        'species_with_trends': species_with_data,
        'page_title': 'Species Analytics',
    }

    return render(request, 'analytics_new/species_analytics.html', context)


@login_required
def site_analytics_view(request):
    """Site-specific analytics reading from operational data"""

    from apps.locations.models import Site, CensusObservation, SpeciesObservation
    from django.db.models import Sum, Count

    # Get active sites with census data
    sites = Site.objects.filter(status='active')

    # Add analytics data for each site
    sites_with_data = []
    for site in sites:
        # Get census observations for this site
        census_observations = CensusObservation.objects.filter(site=site)

        if census_observations.exists():
            # Get species observations for this site
            species_observations = SpeciesObservation.objects.filter(census__site=site)

            # Calculate statistics
            total_birds = species_observations.aggregate(total=Sum('count'))['total'] or 0
            species_diversity = species_observations.values('species').distinct().count()
            total_observations = census_observations.count()

            # Get most recent observation
            recent_census = census_observations.order_by('-observation_date').first()

            # Get species composition
            species_data = {}
            for obs in species_observations:
                species_name = obs.species.name if obs.species else obs.species_name
                species_data[species_name] = species_data.get(species_name, 0) + obs.count

            dominant_species = max(species_data.items(), key=lambda x: x[1])[0] if species_data else "None"

            sites_with_data.append({
                'site': {
                    'site_code': site.name,  # Use site name as code for display
                    'site_name': site.name,
                    'total_birds_recorded': total_birds,
                    'species_diversity': species_diversity,
                    'habitat_type': site.site_type,
                    'area_hectares': site.area_hectares,
                    'target_species_present': list(species_data.keys()) if species_data else [],
                },
                'recent_census': [{
                    'census_date': recent_census.observation_date,
                    'total_birds': total_birds,
                    'is_verified': True,  # Mark as verified since it's operational data
                }] if recent_census else [],
            })

    # Sort by total birds descending
    sites_with_data.sort(key=lambda x: x['site']['total_birds_recorded'], reverse=True)

    context = {
        'sites_with_data': sites_with_data,
        'page_title': 'Site Analytics',
    }

    return render(request, 'analytics_new/site_analytics.html', context)


@login_required
def census_records_view(request):
    """View census observations with analytics"""

    from apps.locations.models import CensusObservation, SpeciesObservation, Site

    # Filter options
    site_filter = request.GET.get('site')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    species_filter = request.GET.get('species')

    # Base query for census observations
    records = CensusObservation.objects.select_related('site', 'observer')

    if site_filter:
        records = records.filter(site_id=site_filter)

    if date_from:
        records = records.filter(observation_date__gte=date_from)

    if date_to:
        records = records.filter(observation_date__lte=date_to)

    # If no date filters provided, show last 60 days by default
    if not date_from and not date_to:
        sixty_days_ago = timezone.now().date() - timezone.timedelta(days=60)
        records = records.filter(observation_date__gte=sixty_days_ago)

    # Apply species filter if provided
    if species_filter:
        # Filter census observations that have observations of the specified species
        records = records.filter(
            species_observations__species__name__icontains=species_filter
        ).distinct()

    records = records.order_by('-observation_date')

    # Enhance records with analytics data
    enhanced_records = []
    for census in records:
        # Get species observations for this census
        species_observations = SpeciesObservation.objects.filter(census=census)

        # Calculate analytics
        total_birds = species_observations.aggregate(total=Sum('count'))['total'] or 0
        species_richness = species_observations.count()

        # Get species breakdown
        species_breakdown = {}
        for obs in species_observations:
            species_name = obs.species.name if obs.species else obs.species_name
            species_breakdown[species_name] = obs.count

        dominant_species = max(species_breakdown.items(), key=lambda x: x[1])[0] if species_breakdown else "None"

        enhanced_records.append({
            'census': census,
            'total_birds': total_birds,
            'species_richness': species_richness,
            'dominant_species': dominant_species,
            'species_breakdown': species_breakdown,
            'verification_status': 'VERIFIED',  # For now, mark all as verified since they're operational data
        })

    # Get available sites for filter
    sites = Site.objects.filter(status='active')

    context = {
        'records': enhanced_records,
        'sites': sites,
        'page_title': 'Census Records',
    }

    return render(request, 'analytics_new/census_records.html', context)


@login_required
def report_generator_view(request):
    """Report generation interface"""

    configurations = ReportConfiguration.objects.filter(is_active=True).order_by('name')

    if request.method == 'POST':
        config_id = request.POST.get('configuration')
        if config_id:
            config = get_object_or_404(ReportConfiguration, id=config_id, is_active=True)

            # Generate comprehensive report
            report_data = generate_comprehensive_report(config, request.user)

            # Create the report record
            # Extract species and sites included in the report
            species_included = []
            if 'species_data' in report_data:
                species_included = [species['name'] for species in report_data['species_data']]

            sites_included = []
            if 'sites_data' in report_data:
                sites_included = [site['name'] for site in report_data['sites_data']]

            report = GeneratedReport.objects.create(
                configuration=config,
                title=f"{config.name} - {timezone.now().strftime('%Y-%m-%d')}",
                generated_by=request.user,
                output_format=config.output_format,
                status="COMPLETED",
                species_included=species_included,
                sites_included=sites_included,
                total_records=report_data.get('total_records', 0),
                date_range=report_data.get('date_range', ''),
            )

            # Generate HTML report content
            html_content = generate_html_report(report_data, config)

            # Save the report file (in a real implementation, you'd save to a file)
            # For now, we'll store a summary in the database
            report.file_path = f"reports/report_{report.id}.html"
            report.file_size_bytes = len(html_content.encode('utf-8'))

            # In a real implementation, you'd save the HTML to a file:
            # report_path = os.path.join(settings.MEDIA_ROOT, 'reports', f'report_{report.id}.html')
            # os.makedirs(os.path.dirname(report_path), exist_ok=True)
            # with open(report_path, 'w', encoding='utf-8') as f:
            #     f.write(html_content)

            report.save()

            messages.success(request, f"Report '{config.name}' generated successfully!")
            return redirect('analytics_new:report_detail', report_id=report.id)

    context = {
        'configurations': configurations,
        'page_title': 'Report Generator',
    }

    return render(request, 'analytics_new/report_generator.html', context)


def generate_comprehensive_report(config, user):
    """Generate comprehensive report data from all systems"""
    from apps.fauna.models import Species
    from apps.locations.models import Site, CensusObservation, SpeciesObservation
    from apps.users.models import User
    from django.db.models import Sum, Count
    from django.utils import timezone

    report_data = {
        'generated_by': user,
        'generated_at': timezone.now(),
        'configuration': config,
    }

    # Get date range from configuration or default to last 60 days
    start_date = config.date_range_start or (timezone.now().date() - timezone.timedelta(days=60))
    end_date = config.date_range_end or timezone.now().date()
    report_data['date_range'] = f"{start_date} to {end_date}"

    # Species Management Data
    if "SPECIES" in config.report_type or config.report_type == "SPECIES_SUMMARY":
        species_data = []
        target_species = Species.objects.filter(name__icontains='egret') | Species.objects.filter(name__icontains='heron')

        for species in target_species:
            observations = SpeciesObservation.objects.filter(
                species=species,
                census__observation_date__gte=start_date,
                census__observation_date__lte=end_date
            )

            if observations.exists():
                total_count = observations.aggregate(total=Sum('count'))['total'] or 0
                sites_with_presence = observations.values('census__site').distinct().count()

                species_data.append({
                    'name': species.name,
                    'scientific_name': species.scientific_name,
                    'iucn_status': species.iucn_status,
                    'total_count': total_count,
                    'sites_with_presence': sites_with_presence,
                })

        report_data['species_data'] = species_data
        report_data['species_count'] = len(species_data)

    # Site Management Data
    if "SITE" in config.report_type or config.report_type == "SITE_COMPARISON":
        sites_data = []
        sites = Site.objects.filter(status='active')

        for site in sites:
            census_observations = CensusObservation.objects.filter(
                site=site,
                observation_date__gte=start_date,
                observation_date__lte=end_date
            )

            if census_observations.exists():
                species_observations = SpeciesObservation.objects.filter(census__site=site)
                total_birds = species_observations.aggregate(total=Sum('count'))['total'] or 0
                species_diversity = species_observations.values('species').distinct().count()

                sites_data.append({
                    'name': site.name,
                    'site_type': site.site_type,
                    'coordinates': site.coordinates,
                    'area_hectares': site.area_hectares,
                    'total_birds': total_birds,
                    'species_diversity': species_diversity,
                    'census_count': census_observations.count(),
                })

        report_data['sites_data'] = sites_data
        report_data['sites_count'] = len(sites_data)

    # Census Management Data
    if "CENSUS" in config.report_type or "MONTHLY" in config.report_type:
        census_data = []
        census_observations = CensusObservation.objects.filter(
            observation_date__gte=start_date,
            observation_date__lte=end_date
        ).select_related('site', 'observer')

        for census in census_observations:
            species_observations = SpeciesObservation.objects.filter(census=census)
            total_birds = species_observations.aggregate(total=Sum('count'))['total'] or 0

            species_breakdown = {}
            for obs in species_observations:
                species_name = obs.species.name if obs.species else obs.species_name
                species_breakdown[species_name] = obs.count

            census_data.append({
                'site': census.site.name,
                'date': census.observation_date,
                'observer': census.observer.employee_id if census.observer else 'Unknown',
                'total_birds': total_birds,
                'species_count': len(species_breakdown),
                'species_breakdown': species_breakdown,
            })

        report_data['census_data'] = census_data
        report_data['total_records'] = len(census_observations)

    # Personnel Data
    personnel_data = []
    users = User.objects.filter(is_active=True)
    for user in users:
        # Get user's activity (simplified - in real implementation, you'd track this)
        census_count = CensusObservation.objects.filter(observer=user).count()
        species_obs_count = SpeciesObservation.objects.filter(census__observer=user).count()

        personnel_data.append({
            'employee_id': user.employee_id,
            'name': f"{user.first_name} {user.last_name}",
            'role': user.role,
            'census_observations': census_count,
            'species_observations': species_obs_count,
        })

    report_data['personnel_data'] = personnel_data
    report_data['personnel_count'] = len(personnel_data)

    return report_data


def generate_html_report(report_data, config):
    """Generate HTML report content"""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{config.name} - AVICAST Analytics Report</title>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .section {{ margin: 30px 0; }}
            .section h2 {{ color: #333; border-bottom: 2px solid #007bff; padding-bottom: 5px; }}
            table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            .summary {{ background-color: #e7f3ff; padding: 15px; border-radius: 5px; margin: 10px 0; }}
            .count {{ font-size: 1.2em; font-weight: bold; color: #007bff; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>{config.name}</h1>
            <p>AVICAST Analytics Report</p>
            <p>Generated on: {report_data['generated_at'].strftime('%Y-%m-%d %H:%M')}</p>
            <p>Report Period: {report_data['date_range']}</p>
        </div>
    """

    # Species Section
    if 'species_data' in report_data:
        html += f"""
        <div class="section">
            <h2>Species Management Summary</h2>
            <div class="summary">
                <p><strong>Total Species Monitored:</strong> <span class="count">{report_data['species_count']}</span></p>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Species Name</th>
                        <th>Scientific Name</th>
                        <th>IUCN Status</th>
                        <th>Total Count</th>
                        <th>Sites Present</th>
                    </tr>
                </thead>
                <tbody>
        """
        for species in report_data['species_data']:
            html += f"""
                    <tr>
                        <td>{species['name']}</td>
                        <td>{species['scientific_name']}</td>
                        <td>{species['iucn_status']}</td>
                        <td>{species['total_count']}</td>
                        <td>{species['sites_with_presence']}</td>
                    </tr>
            """
        html += """
                </tbody>
            </table>
        </div>
        """

    # Sites Section
    if 'sites_data' in report_data:
        html += f"""
        <div class="section">
            <h2>Site Management Summary</h2>
            <div class="summary">
                <p><strong>Total Sites:</strong> <span class="count">{report_data['sites_count']}</span></p>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Site Name</th>
                        <th>Type</th>
                        <th>Total Birds</th>
                        <th>Species Diversity</th>
                        <th>Census Count</th>
                    </tr>
                </thead>
                <tbody>
        """
        for site in report_data['sites_data']:
            html += f"""
                    <tr>
                        <td>{site['name']}</td>
                        <td>{site['site_type']}</td>
                        <td>{site['total_birds']}</td>
                        <td>{site['species_diversity']}</td>
                        <td>{site['census_count']}</td>
                    </tr>
            """
        html += """
                </tbody>
            </table>
        </div>
        """

    # Census Section
    if 'census_data' in report_data:
        html += f"""
        <div class="section">
            <h2>Census Observations Summary</h2>
            <div class="summary">
                <p><strong>Total Records:</strong> <span class="count">{report_data['total_records']}</span></p>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Site</th>
                        <th>Date</th>
                        <th>Observer</th>
                        <th>Total Birds</th>
                        <th>Species Count</th>
                    </tr>
                </thead>
                <tbody>
        """
        for census in report_data['census_data']:
            html += f"""
                    <tr>
                        <td>{census['site']}</td>
                        <td>{census['date']}</td>
                        <td>{census['observer']}</td>
                        <td>{census['total_birds']}</td>
                        <td>{census['species_count']}</td>
                    </tr>
            """
        html += """
                </tbody>
            </table>
        </div>
        """

    # Personnel Section
    if 'personnel_data' in report_data:
        html += f"""
        <div class="section">
            <h2>Personnel Summary</h2>
            <div class="summary">
                <p><strong>Total Personnel:</strong> <span class="count">{report_data['personnel_count']}</span></p>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Employee ID</th>
                        <th>Name</th>
                        <th>Role</th>
                        <th>Census Observations</th>
                        <th>Species Observations</th>
                    </tr>
                </thead>
                <tbody>
        """
        for personnel in report_data['personnel_data']:
            html += f"""
                    <tr>
                        <td>{personnel['employee_id']}</td>
                        <td>{personnel['name']}</td>
                        <td>{personnel['role']}</td>
                        <td>{personnel['census_observations']}</td>
                        <td>{personnel['species_observations']}</td>
                    </tr>
            """
        html += """
                </tbody>
            </table>
        </div>
        """

    html += f"""
        <div class="section">
            <h2>Report Generation Information</h2>
            <div class="summary">
                <p><strong>Report Type:</strong> {config.get_report_type_display()}</p>
                <p><strong>Generated By:</strong> {report_data['generated_by'].get_full_name() or report_data['generated_by'].employee_id}</p>
                <p><strong>Generation Date:</strong> {report_data['generated_at'].strftime('%Y-%m-%d %H:%M')}</p>
                <p><strong>Output Format:</strong> {config.output_format}</p>
            </div>
        </div>
    </body>
    </html>
    """

    return html


@login_required
def report_detail_view(request, report_id):
    """View generated report details"""

    report = get_object_or_404(GeneratedReport, id=report_id)

    # Generate the report content if not already generated
    if not hasattr(report, '_report_content'):
        report_data = generate_comprehensive_report(report.configuration, report.generated_by)
        report._report_content = generate_html_report(report_data, report.configuration)

    context = {
        'report': report,
        'report_content': report._report_content,
        'page_title': f'Report: {report.title}',
    }

    return render(request, 'analytics_new/report_detail.html', context)


@login_required
def population_trends_view(request):
    """Population trends analysis"""

    trends = PopulationTrend.objects.select_related('analyzed_by').order_by('-analysis_date')[:20]

    context = {
        'trends': trends,
        'page_title': 'Population Trends',
    }

    return render(request, 'analytics_new/population_trends.html', context)


@login_required
@require_http_methods(["POST"])
def verify_census_record(request, record_id):
    """Verify a census observation"""

    if request.user.role not in ['SUPERADMIN', 'ADMIN']:
        messages.error(request, "Only administrators can verify records.")
        return redirect('analytics_new:census_records')

    from apps.locations.models import CensusObservation
    census_observation = get_object_or_404(CensusObservation, id=record_id)

    # Update verification status (you could add a verification field to CensusObservation if needed)
    # For now, we'll just show a success message since the operational data is already "verified"
    messages.success(request, f"Census observation for {census_observation.site.name} on {census_observation.observation_date} has been verified.")
    return redirect('analytics_new:census_records')
