"""
Report generation views for analytics app
"""

from io import BytesIO

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from apps.image_processing.permissions import staff_required
from apps.locations.models import Site, SpeciesObservation


@login_required
@staff_required
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

        census_count = site.census_observations.count()

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
