from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
import plotly.utils
import json
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from io import BytesIO
import os
from functools import wraps

from apps.locations.models import Site, CensusObservation, SpeciesObservation

def role_required(allowed_roles):
    """
    Decorator to check if user has required role
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            if not hasattr(request.user, 'role'):
                return HttpResponse("User role not defined", status=403)
            
            if request.user.role not in allowed_roles:
                return HttpResponse("Access denied. Insufficient permissions.", status=403)
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

@login_required
@role_required(['ADMIN', 'FIELD_WORKER'])
def analytics_dashboard(request):
    """Main analytics dashboard with overview charts"""
    
    # Get basic statistics
    total_sites = Site.objects.count()
    total_census = CensusObservation.objects.count()
    total_species = SpeciesObservation.objects.values('species_name').distinct().count()
    total_birds = SpeciesObservation.objects.aggregate(total=Sum('count'))['total'] or 0
    
    # Get recent activity
    recent_census = CensusObservation.objects.order_by('-observation_date')[:5]
    
    # Get top sites by species diversity
    top_sites = Site.objects.annotate(
        species_count=Count('census_observations__species_observations__species_name', distinct=True)
    ).order_by('-species_count')[:5]
    
    context = {
        'total_sites': total_sites,
        'total_census': total_census,
        'total_species': total_species,
        'total_birds': total_birds,
        'recent_census': recent_census,
        'top_sites': top_sites,
    }
    
    return render(request, 'analytics/dashboard.html', context)

@login_required
@role_required(['ADMIN', 'FIELD_WORKER'])
def species_diversity_chart(request):
    """Generate species diversity chart for all sites"""
    
    # Get species diversity data
    sites_data = Site.objects.annotate(
        species_count=Count('census_observations__species_observations__species_name', distinct=True),
        total_birds=Sum('census_observations__species_observations__count')
    ).filter(species_count__gt=0).order_by('-species_count')
    
    # Create bar chart
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=[site.name for site in sites_data],
        y=[site.species_count for site in sites_data],
        name='Species Count',
        marker_color='rgb(55, 83, 109)'
    ))
    
    fig.update_layout(
        title='Species Diversity by Site',
        xaxis_title='Sites',
        yaxis_title='Number of Species',
        template='plotly_white',
        height=500
    )
    
    # Convert to JSON for JavaScript
    chart_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    
    return JsonResponse({'chart': chart_json})

@login_required
@role_required(['ADMIN', 'FIELD_WORKER'])
def population_trends_chart(request):
    """Generate population trends chart over time"""
    
    # Get population data over time
    census_data = CensusObservation.objects.annotate(
        total_birds=Sum('species_observations__count')
    ).values('observation_date', 'total_birds').order_by('observation_date')
    
    # Group by month for better visualization
    df = pd.DataFrame(list(census_data))
    if not df.empty:
        df['month'] = pd.to_datetime(df['observation_date']).dt.to_period('M')
        monthly_data = df.groupby('month')['total_birds'].sum().reset_index()
        monthly_data['month'] = monthly_data['month'].astype(str)
        
        # Create line chart
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=monthly_data['month'],
            y=monthly_data['total_birds'],
            mode='lines+markers',
            name='Total Birds',
            line=dict(color='rgb(49, 130, 189)', width=3),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            title='Bird Population Trends Over Time',
            xaxis_title='Month',
            yaxis_title='Total Birds Observed',
            template='plotly_white',
            height=500
        )
        
        chart_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    else:
        chart_json = None
    
    return JsonResponse({'chart': chart_json})

@login_required
@role_required(['ADMIN', 'FIELD_WORKER'])
def seasonal_analysis_chart(request):
    """Generate seasonal analysis heatmap"""
    
    # Get seasonal data
    census_data = CensusObservation.objects.annotate(
        total_birds=Sum('species_observations__count'),
        month=Count('observation_date', filter=Q(observation_date__month=1))  # This needs fixing
    ).values('observation_date', 'total_birds')
    
    # Create monthly heatmap data
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    # This is a simplified version - in practice, you'd aggregate by month properly
    monthly_totals = [0] * 12
    
    for census in census_data:
        month = census['observation_date'].month - 1  # 0-indexed
        monthly_totals[month] += census['total_birds'] or 0
    
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=[monthly_totals],
        x=months,
        y=['Bird Count'],
        colorscale='Viridis',
        showscale=True
    ))
    
    fig.update_layout(
        title='Seasonal Bird Activity Pattern',
        xaxis_title='Month',
        yaxis_title='',
        template='plotly_white',
        height=400
    )
    
    chart_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return JsonResponse({'chart': chart_json})

@login_required
@role_required(['ADMIN', 'FIELD_WORKER'])
def site_comparison_chart(request):
    """Generate site comparison radar chart"""
    
    # Get comparison data for sites
    sites_data = Site.objects.annotate(
        species_count=Count('census_observations__species_observations__species_name', distinct=True),
        total_birds=Sum('census_observations__species_observations__count'),
        census_count=Count('census_observations')
    ).filter(species_count__gt=0)[:6]  # Limit to 6 sites for readability
    
    if sites_data:
        # Create radar chart
        fig = go.Figure()
        
        for site in sites_data:
            fig.add_trace(go.Scatterpolar(
                r=[site.species_count, site.total_birds or 0, site.census_count],
                theta=['Species Diversity', 'Total Birds', 'Census Sessions'],
                fill='toself',
                name=site.name
            ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, max([
                        max([s.species_count for s in sites_data]),
                        max([s.total_birds or 0 for s in sites_data]),
                        max([s.census_count for s in sites_data])
                    ])]
                )),
            showlegend=True,
            title='Site Comparison - Multiple Metrics',
            height=600
        )
        
        chart_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    else:
        chart_json = None
    
    return JsonResponse({'chart': chart_json})

@login_required
@role_required(['ADMIN', 'FIELD_WORKER'])
def generate_census_report(request, site_id=None):
    """Generate comprehensive census report"""
    
    if site_id:
        site = get_object_or_404(Site, id=site_id)
        sites = [site]
        report_title = f"Census Report - {site.name}"
    else:
        sites = Site.objects.all()
        report_title = "Comprehensive Census Report - All Sites"
    
    # Create PDF report
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    story = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=1  # Center alignment
    )
    
    # Title
    story.append(Paragraph(report_title, title_style))
    story.append(Spacer(1, 20))
    
    # Summary table
    summary_data = [['Site', 'Species Count', 'Total Birds', 'Census Sessions']]
    
    for site in sites:
        species_count = SpeciesObservation.objects.filter(
            census__site=site
        ).values('species_name').distinct().count()
        
        total_birds = SpeciesObservation.objects.filter(
            census__site=site
        ).aggregate(total=Sum('count'))['total'] or 0
        
        census_count = CensusObservation.objects.filter(site=site).count()
        
        summary_data.append([
            site.name,
            str(species_count),
            str(total_birds),
            str(census_count)
        ])
    
    # Create table
    table = Table(summary_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(table)
    story.append(Spacer(1, 20))
    
    # Build PDF
    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    
    # Create response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{report_title.replace(" ", "_")}.pdf"'
    response.write(pdf)
    
    return response

@login_required
@role_required(['ADMIN', 'FIELD_WORKER'])
def chart_gallery(request):
    """Display gallery of available charts"""
    
    # Get available chart types
    chart_types = [
        {
            'name': 'Species Diversity',
            'type': 'bar',
            'description': 'Compare species diversity across different sites',
            'endpoint': 'analytics:species_diversity_chart'
        },
        {
            'name': 'Population Trends',
            'type': 'line',
            'description': 'Track bird population changes over time',
            'endpoint': 'analytics:population_trends_chart'
        },
        {
            'name': 'Seasonal Analysis',
            'type': 'heatmap',
            'description': 'Analyze seasonal patterns in bird activity',
            'endpoint': 'analytics:seasonal_analysis_chart'
        },
        {
            'name': 'Site Comparison',
            'type': 'radar',
            'description': 'Compare multiple sites across different metrics',
            'endpoint': 'analytics:site_comparison_chart'
        }
    ]
    
    context = {
        'chart_types': chart_types
    }
    
    return render(request, 'analytics/chart_gallery.html', context)
