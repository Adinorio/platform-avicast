# Standard library imports
import json
import os
from functools import wraps
from io import BytesIO

# Third-party imports
import pandas as pd
import plotly.graph_objects as go
import plotly.utils

# Django imports
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.db.models.functions import ExtractMonth
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

# Third-party Django-related imports
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

# Local imports
from apps.locations.models import CensusObservation, Site, SpeciesObservation


def role_required(allowed_roles):
    """
    Decorator to check if user has required role for accessing views.

    Args:
        allowed_roles: List of role strings that are allowed access

    Returns:
        Decorated function or redirect/error response
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("login")

            if not hasattr(request.user, "role"):
                return HttpResponse("User role not defined", status=403)

            if request.user.role not in allowed_roles:
                return HttpResponse("Access denied. Insufficient permissions.", status=403)

            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator


@login_required
@role_required(["ADMIN", "FIELD_WORKER"])
def analytics_dashboard(request):
    """
    Main analytics dashboard displaying overview charts and statistics.

    Shows total sites, census observations, species count, bird population,
    recent activity, top sites by diversity, and available AI models.
    """

    # Get basic statistics
    total_sites = Site.objects.count()
    total_census = CensusObservation.objects.count()
    total_species = SpeciesObservation.objects.values("species_name").distinct().count()
    total_birds = SpeciesObservation.objects.aggregate(total=Sum("count"))["total"] or 0

    # Get recent activity
    recent_census = CensusObservation.objects.order_by("-observation_date")[:5]

    # Get top sites by species diversity
    top_sites = Site.objects.annotate(
        species_count=Count(
            "census_observations__species_observations__species_name", distinct=True
        )
    ).order_by("-species_count")[:5]

    # Get AI model information
    models_dir = "models"
    yolov5_models = []
    yolov8_models = []
    yolov9_models = []

    if os.path.exists(models_dir):
        for filename in os.listdir(models_dir):
            if filename.endswith(".pt"):
                file_path = os.path.join(models_dir, filename)
                file_size = os.path.getsize(file_path)
                size_mb = f"{file_size / (1024 * 1024):.1f}MB"

                if filename.startswith("yolov5"):
                    yolov5_models.append(
                        {"name": filename.replace(".pt", ""), "size": size_mb, "filename": filename}
                    )
                elif filename.startswith("yolov8"):
                    yolov8_models.append(
                        {"name": filename.replace(".pt", ""), "size": size_mb, "filename": filename}
                    )
                elif filename.startswith("yolov9"):
                    yolov9_models.append(
                        {"name": filename.replace(".pt", ""), "size": size_mb, "filename": filename}
                    )

    # Sort models by name
    yolov5_models.sort(key=lambda x: x["name"])
    yolov8_models.sort(key=lambda x: x["name"])
    yolov9_models.sort(key=lambda x: x["name"])

    context = {
        "total_sites": total_sites,
        "total_census": total_census,
        "total_species": total_species,
        "total_birds": total_birds,
        "recent_census": recent_census,
        "top_sites": top_sites,
        "yolov5_models": yolov5_models,
        "yolov8_models": yolov8_models,
        "yolov9_models": yolov9_models,
    }

    return render(request, "analytics/dashboard.html", context)


@login_required
@role_required(["ADMIN", "FIELD_WORKER"])
def species_diversity_chart(request):
    """Generate species diversity chart for all sites"""

    # Get species diversity data
    sites_data = (
        Site.objects.annotate(
            species_count=Count(
                "census_observations__species_observations__species_name", distinct=True
            ),
            total_birds=Sum("census_observations__species_observations__count"),
        )
        .filter(species_count__gt=0)
        .order_by("-species_count")
    )

    # Create bar chart
    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=[site.name for site in sites_data],
            y=[site.species_count for site in sites_data],
            name="Species Count",
            marker_color="rgb(55, 83, 109)",
        )
    )

    fig.update_layout(
        title="Species Diversity by Site",
        xaxis_title="Sites",
        yaxis_title="Number of Species",
        template="plotly_white",
        height=500,
    )

    # Convert to JSON for JavaScript
    chart_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return JsonResponse({"chart": chart_json})


@login_required
@role_required(["ADMIN", "FIELD_WORKER"])
def population_trends_chart(request):
    """Generate population trends chart over time"""

    # Get population data over time
    census_data = (
        CensusObservation.objects.annotate(total_birds=Sum("species_observations__count"))
        .values("observation_date", "total_birds")
        .order_by("observation_date")
    )

    # Group by month for better visualization
    df = pd.DataFrame(list(census_data))
    if not df.empty:
        df["month"] = pd.to_datetime(df["observation_date"]).dt.to_period("M")
        monthly_data = df.groupby("month")["total_birds"].sum().reset_index()
        monthly_data["month"] = monthly_data["month"].astype(str)

        # Create line chart
        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=monthly_data["month"],
                y=monthly_data["total_birds"],
                mode="lines+markers",
                name="Total Birds",
                line=dict(color="rgb(49, 130, 189)", width=3),
                marker=dict(size=8),
            )
        )

        fig.update_layout(
            title="Bird Population Trends Over Time",
            xaxis_title="Month",
            yaxis_title="Total Birds Observed",
            template="plotly_white",
            height=500,
        )

        chart_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    else:
        chart_json = None

    return JsonResponse({"chart": chart_json})


@login_required
@role_required(["ADMIN", "FIELD_WORKER"])
def seasonal_analysis_chart(request):
    """Generate seasonal analysis heatmap"""

    # Get seasonal data - group by month properly
    census_data = CensusObservation.objects.annotate(
        total_birds=Sum("species_observations__count"),
        observation_month=ExtractMonth("observation_date"),
    ).values("observation_date", "total_birds", "observation_month")

    # Create monthly heatmap data
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    # Aggregate data by month properly
    monthly_totals = [0] * 12

    for census in census_data:
        month = census["observation_month"] - 1  # 0-indexed (1-12 -> 0-11)
        monthly_totals[month] += census["total_birds"] or 0

    # Create heatmap
    fig = go.Figure(
        data=go.Heatmap(
            z=[monthly_totals], x=months, y=["Bird Count"], colorscale="Viridis", showscale=True
        )
    )

    fig.update_layout(
        title="Seasonal Bird Activity Pattern",
        xaxis_title="Month",
        yaxis_title="",
        template="plotly_white",
        height=400,
    )

    chart_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return JsonResponse({"chart": chart_json})


@login_required
@role_required(["ADMIN", "FIELD_WORKER"])
def site_comparison_chart(request):
    """Generate site comparison radar chart"""

    # Get comparison data for sites
    sites_data = Site.objects.annotate(
        species_count=Count(
            "census_observations__species_observations__species_name", distinct=True
        ),
        total_birds=Sum("census_observations__species_observations__count"),
        census_count=Count("census_observations"),
    ).filter(species_count__gt=0)[:6]  # Limit to 6 sites for readability

    if sites_data:
        # Create radar chart
        fig = go.Figure()

        for site in sites_data:
            fig.add_trace(
                go.Scatterpolar(
                    r=[site.species_count, site.total_birds or 0, site.census_count],
                    theta=["Species Diversity", "Total Birds", "Census Sessions"],
                    fill="toself",
                    name=site.name,
                )
            )

        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[
                        0,
                        max(
                            [
                                max([s.species_count for s in sites_data]),
                                max([s.total_birds or 0 for s in sites_data]),
                                max([s.census_count for s in sites_data]),
                            ]
                        ),
                    ],
                )
            ),
            showlegend=True,
            title="Site Comparison - Multiple Metrics",
            height=600,
        )

        chart_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    else:
        chart_json = None

    return JsonResponse({"chart": chart_json})


@login_required
@role_required(["ADMIN", "FIELD_WORKER"])
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
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=24,
        spaceAfter=30,
        alignment=1,  # Center alignment
    )

    # Title
    story.append(Paragraph(report_title, title_style))
    story.append(Spacer(1, 20))

    # Summary table
    summary_data = [["Site", "Species Count", "Total Birds", "Census Sessions"]]

    for site in sites:
        species_count = (
            SpeciesObservation.objects.filter(census__site=site)
            .values("species_name")
            .distinct()
            .count()
        )

        total_birds = (
            SpeciesObservation.objects.filter(census__site=site).aggregate(total=Sum("count"))[
                "total"
            ]
            or 0
        )

        census_count = CensusObservation.objects.filter(site=site).count()

        summary_data.append([site.name, str(species_count), str(total_birds), str(census_count)])

    # Create table
    table = Table(summary_data)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 14),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )

    story.append(table)
    story.append(Spacer(1, 20))

    # Build PDF
    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()

    # Create response
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{report_title.replace(" ", "_")}.pdf"'
    response.write(pdf)

    return response


@login_required
@role_required(["ADMIN", "FIELD_WORKER"])
def chart_gallery(request):
    """Display gallery of available charts"""

    # Get available chart types
    chart_types = [
        {
            "name": "Species Diversity",
            "type": "bar",
            "description": "Compare species diversity across different sites",
            "endpoint": "analytics:species_diversity_chart",
        },
        {
            "name": "Population Trends",
            "type": "line",
            "description": "Track bird population changes over time",
            "endpoint": "analytics:population_trends_chart",
        },
        {
            "name": "Seasonal Analysis",
            "type": "heatmap",
            "description": "Analyze seasonal patterns in bird activity",
            "endpoint": "analytics:seasonal_analysis_chart",
        },
        {
            "name": "Site Comparison",
            "type": "radar",
            "description": "Compare multiple sites across different metrics",
            "endpoint": "analytics:site_comparison_chart",
        },
    ]

    context = {"chart_types": chart_types}

    return render(request, "analytics/chart_gallery.html", context)
