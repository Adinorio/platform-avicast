"""
Chart generation views for analytics app
"""

import json

import pandas as pd
import plotly.graph_objects as go
import plotly.utils

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.db.models.functions import ExtractMonth
from django.http import JsonResponse

from apps.image_processing.permissions import staff_required
from apps.locations.models import CensusObservation, Site


@login_required
@staff_required
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
@staff_required
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
@staff_required
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
@staff_required
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
