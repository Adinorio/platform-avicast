"""
Excel Import/Export Utilities for Census Data
AGENTS.md §3 File Organization - Utility module for Excel operations
AGENTS.md §6.1 Security - Input validation for bulk imports
"""

from datetime import datetime
from decimal import Decimal
from io import BytesIO
from typing import Dict, List, Tuple

from django.db import transaction
from django.db.models import Q
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment

from apps.fauna.models import Species
from apps.locations.models import Site, CensusYear, CensusMonth, Census, CensusObservation


class ExcelImportError(Exception):
    """Custom exception for Excel import errors"""
    pass


class CensusExcelHandler:
    """Handles Excel import/export for census data"""
    
    # Excel column mapping
    COLUMNS = {
        'A': 'site_name',
        'B': 'year',
        'C': 'month',
        'D': 'census_date',
        'E': 'species_name',
        'F': 'count',
        'G': 'weather_conditions',
        'H': 'notes',
    }
    
    HEADER_ROW = [
        'Site Name',
        'Year',
        'Month',
        'Census Date (YYYY-MM-DD)',
        'Species Name',
        'Count',
        'Weather Conditions',
        'Notes'
    ]
    
    @staticmethod
    def generate_template() -> Workbook:
        """
        Generate Excel template for data import
        Returns: Workbook object with headers and example data
        """
        wb = Workbook()
        ws = wb.active
        ws.title = "Census Data"
        
        # Header styling
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF")
        header_alignment = Alignment(horizontal="center", vertical="center")
        
        # Write headers
        for idx, header in enumerate(CensusExcelHandler.HEADER_ROW, start=1):
            cell = ws.cell(row=1, column=idx, value=header)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = header_alignment
        
        # Add example data
        ws.append([
            "Main Site",
            2024,
            1,
            "2024-01-15",
            "Chinese Egret",
            45,
            "Sunny, light breeze",
            "Morning observation"
        ])
        ws.append([
            "Main Site",
            2024,
            1,
            "2024-01-15",
            "Black-faced Spoonbill",
            23,
            "Sunny, light breeze",
            "Same census event"
        ])
        
        # Adjust column widths
        ws.column_dimensions['A'].width = 20
        ws.column_dimensions['B'].width = 10
        ws.column_dimensions['C'].width = 10
        ws.column_dimensions['D'].width = 22
        ws.column_dimensions['E'].width = 30
        ws.column_dimensions['F'].width = 10
        ws.column_dimensions['G'].width = 25
        ws.column_dimensions['H'].width = 30
        
        # Add instructions sheet
        ws_instructions = wb.create_sheet("Instructions")
        instructions = [
            ["Census Data Import Instructions"],
            [""],
            ["Column Requirements:"],
            ["Site Name", "Must match existing site name exactly (case-sensitive)"],
            ["Year", "4-digit year (e.g., 2024)"],
            ["Month", "Month number 1-12"],
            ["Census Date", "Format: YYYY-MM-DD (e.g., 2024-01-15)"],
            ["Species Name", "Common or scientific name (will be matched to species database)"],
            ["Count", "Positive integer (number of birds observed)"],
            ["Weather Conditions", "Optional - weather during census"],
            ["Notes", "Optional - any additional notes"],
            [""],
            ["Important Notes:"],
            ["- Multiple species can be recorded for the same census date/site"],
            ["- All species from the same date/site will be grouped into one census record"],
            ["- Species names will be validated against the database"],
            ["- If a species is not found, the row will be skipped with an error"],
            ["- Duplicate entries (same site/date/species) will be rejected"],
        ]
        
        for row_idx, row_data in enumerate(instructions, start=1):
            for col_idx, value in enumerate(row_data, start=1):
                cell = ws_instructions.cell(row=row_idx, column=col_idx, value=value)
                if row_idx == 1:
                    cell.font = Font(bold=True, size=14)
                elif row_idx in [3, 13]:
                    cell.font = Font(bold=True)
        
        ws_instructions.column_dimensions['A'].width = 25
        ws_instructions.column_dimensions['B'].width = 60
        
        return wb
    
    @staticmethod
    def validate_row(row_data: Dict, row_num: int) -> Tuple[bool, str]:
        """
        Validate a single row of data
        Returns: (is_valid, error_message)
        """
        # Required fields
        required = ['site_name', 'year', 'month', 'census_date', 'species_name', 'count']
        for field in required:
            if not row_data.get(field):
                return False, f"Row {row_num}: Missing required field '{field}'"
        
        # Validate year
        try:
            year = int(row_data['year'])
            if year < 1900 or year > 2100:
                return False, f"Row {row_num}: Invalid year {year}"
        except (ValueError, TypeError):
            return False, f"Row {row_num}: Year must be a number"
        
        # Validate month
        try:
            month = int(row_data['month'])
            if month < 1 or month > 12:
                return False, f"Row {row_num}: Month must be between 1-12"
        except (ValueError, TypeError):
            return False, f"Row {row_num}: Month must be a number"
        
        # Validate date format
        try:
            date_str = str(row_data['census_date'])
            if isinstance(row_data['census_date'], datetime):
                pass  # Already a datetime object from Excel
            else:
                datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            return False, f"Row {row_num}: Invalid date format. Use YYYY-MM-DD"
        
        # Validate count
        try:
            count = int(row_data['count'])
            if count < 1:
                return False, f"Row {row_num}: Count must be a positive number"
        except (ValueError, TypeError):
            return False, f"Row {row_num}: Count must be a number"
        
        # Validate site exists
        if not Site.objects.filter(name__iexact=row_data['site_name']).exists():
            return False, f"Row {row_num}: Site '{row_data['site_name']}' not found"
        
        return True, ""
    
    @staticmethod
    def import_from_excel(file, user) -> Dict:
        """
        Import census data from Excel file
        Args:
            file: UploadedFile object
            user: User object (for lead_observer)
        Returns: Dict with success/error statistics
        """
        try:
            wb = load_workbook(file, data_only=True)
            ws = wb.active
            
            results = {
                'total_rows': 0,
                'successful': 0,
                'skipped': 0,
                'errors': [],
                'created_census': 0,
                'created_observations': 0,
            }
            
            # Group observations by (site, date) to create census records
            census_groups = {}
            
            # Read data rows (skip header)
            for row_num, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
                if not any(row):  # Skip empty rows
                    continue
                
                results['total_rows'] += 1
                
                # Map row to dictionary
                row_data = {}
                for idx, col_letter in enumerate('ABCDEFGH'):
                    field_name = CensusExcelHandler.COLUMNS[col_letter]
                    row_data[field_name] = row[idx] if idx < len(row) else None
                
                # Validate row
                is_valid, error_msg = CensusExcelHandler.validate_row(row_data, row_num)
                if not is_valid:
                    results['errors'].append(error_msg)
                    results['skipped'] += 1
                    continue
                
                # Find or validate species
                species_name = str(row_data['species_name']).strip()
                species = Species.objects.filter(
                    Q(name__iexact=species_name) | 
                    Q(scientific_name__iexact=species_name)
                ).first()
                
                if not species:
                    results['errors'].append(
                        f"Row {row_num}: Species '{species_name}' not found in database"
                    )
                    results['skipped'] += 1
                    continue
                
                # Prepare census key
                site = Site.objects.get(name__iexact=row_data['site_name'])
                
                # Handle date - could be datetime or string
                if isinstance(row_data['census_date'], datetime):
                    census_date = row_data['census_date'].date()
                else:
                    census_date = datetime.strptime(
                        str(row_data['census_date']), '%Y-%m-%d'
                    ).date()
                
                census_key = (site.id, census_date)
                
                # Group observations
                if census_key not in census_groups:
                    census_groups[census_key] = {
                        'site': site,
                        'date': census_date,
                        'year': int(row_data['year']),
                        'month': int(row_data['month']),
                        'weather': row_data.get('weather_conditions', ''),
                        'notes': row_data.get('notes', ''),
                        'observations': []
                    }
                
                # Add observation to group
                census_groups[census_key]['observations'].append({
                    'species': species,
                    'species_name': species.name,
                    'count': int(row_data['count']),
                    'row_num': row_num
                })
                
                results['successful'] += 1
            
            # Create census records with observations
            with transaction.atomic():
                for census_key, census_data in census_groups.items():
                    # Get or create CensusYear
                    year_obj, _ = CensusYear.objects.get_or_create(
                        site=census_data['site'],
                        year=census_data['year']
                    )
                    
                    # Get or create CensusMonth
                    month_obj, _ = CensusMonth.objects.get_or_create(
                        year=year_obj,
                        month=census_data['month']
                    )
                    
                    # Check if census already exists for this date
                    census, created = Census.objects.get_or_create(
                        month=month_obj,
                        census_date=census_data['date'],
                        defaults={
                            'lead_observer': user,
                            'weather_conditions': census_data['weather'],
                            'notes': census_data['notes'],
                        }
                    )
                    
                    if created:
                        results['created_census'] += 1
                    
                    # Add observations
                    for obs_data in census_data['observations']:
                        # Check for duplicates
                        existing = CensusObservation.objects.filter(
                            census=census,
                            species=obs_data['species']
                        ).first()
                        
                        if existing:
                            # Update count instead of creating duplicate
                            existing.count += obs_data['count']
                            existing.save()
                            results['errors'].append(
                                f"Row {obs_data['row_num']}: Duplicate observation for "
                                f"{obs_data['species_name']} on {census_data['date']} - "
                                f"count added to existing record"
                            )
                        else:
                            CensusObservation.objects.create(
                                census=census,
                                species=obs_data['species'],
                                species_name=obs_data['species_name'],
                                count=obs_data['count']
                            )
                            results['created_observations'] += 1
            
            return results
            
        except Exception as e:
            raise ExcelImportError(f"Error processing Excel file: {str(e)}")
    
    @staticmethod
    def export_to_excel(filters: Dict = None) -> Workbook:
        """
        Export census data to Excel
        Args:
            filters: Dict with optional keys: site_id, year, month, start_date, end_date
        Returns: Workbook object
        """
        wb = Workbook()
        ws = wb.active
        ws.title = "Census Data Export"
        
        # Header styling
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF")
        
        # Write headers
        for idx, header in enumerate(CensusExcelHandler.HEADER_ROW, start=1):
            cell = ws.cell(row=1, column=idx, value=header)
            cell.fill = header_fill
            cell.font = header_font
        
        # Build query
        observations = CensusObservation.objects.select_related(
            'census__month__year__site',
            'species'
        ).all()
        
        # Apply filters
        if filters:
            if filters.get('site_id'):
                observations = observations.filter(
                    census__month__year__site_id=filters['site_id']
                )
            if filters.get('year'):
                observations = observations.filter(
                    census__month__year__year=filters['year']
                )
            if filters.get('month'):
                observations = observations.filter(
                    census__month__month=filters['month']
                )
            if filters.get('start_date'):
                observations = observations.filter(
                    census__census_date__gte=filters['start_date']
                )
            if filters.get('end_date'):
                observations = observations.filter(
                    census__census_date__lte=filters['end_date']
                )
        
        # Write data
        for obs in observations.order_by('census__census_date', 'species_name'):
            ws.append([
                obs.census.month.year.site.name,
                obs.census.month.year.year,
                obs.census.month.month,
                obs.census.census_date.strftime('%Y-%m-%d'),
                obs.species_name,
                obs.count,
                obs.census.weather_conditions or '',
                obs.census.notes or ''
            ])
        
        # Adjust column widths
        ws.column_dimensions['A'].width = 20
        ws.column_dimensions['B'].width = 10
        ws.column_dimensions['C'].width = 10
        ws.column_dimensions['D'].width = 22
        ws.column_dimensions['E'].width = 30
        ws.column_dimensions['F'].width = 10
        ws.column_dimensions['G'].width = 25
        ws.column_dimensions['H'].width = 30
        
        return wb

