# Census Data Import/Export Guide

## Overview

The AVICAST platform now includes comprehensive import/export functionality for historical census data. This guide explains how to use these features to manage large datasets efficiently.

**References:** AGENTS.md §3 File Organization, §6.1 Testing, §9.1 Common Issues

---

## Features

### 1. **Bulk Import from Excel**
- Import historical census data with 96+ species
- Automatic validation and error reporting
- Duplicate detection and merging
- Supports multiple sites and time periods

### 2. **Flexible Export**
- Export to Excel with custom filters
- Filter by site, year, month, or date range
- Formatted Excel output ready for analysis

### 3. **Aggregated Totals View**
- View total bird counts by site/year/month
- Species breakdown with IUCN status
- Filterable dashboard for trend analysis

---

## Quick Start

### Importing Historical Data

**Step 1:** Download the Excel template
```
Navigate to: Locations → Data Management → Download Template
```

**Step 2:** Fill in your census data

| Column | Description | Required | Format |
|--------|-------------|----------|--------|
| Site Name | Must match existing site (case-sensitive) | Yes | Text |
| Year | 4-digit year | Yes | Number (e.g., 2024) |
| Month | Month number | Yes | 1-12 |
| Census Date | Date of observation | Yes | YYYY-MM-DD |
| Species Name | Common or scientific name | Yes | Text |
| Count | Number of birds observed | Yes | Positive integer |
| Weather Conditions | Weather during census | No | Text |
| Notes | Additional notes | No | Text |

**Step 3:** Upload and validate
```
Navigate to: Locations → Data Management → Import Census Data
Upload your filled Excel file
Review validation results
```

**Example Excel Data:**
```
Site Name       | Year | Month | Census Date  | Species Name           | Count | Weather    | Notes
Main Site       | 2024 | 1     | 2024-01-15  | Chinese Egret          | 45    | Sunny      | Morning obs
Main Site       | 2024 | 1     | 2024-01-15  | Black-faced Spoonbill  | 23    | Sunny      | Same census
Coastal Wetland | 2024 | 2     | 2024-02-10  | Chinese Egret          | 67    | Overcast   | High tide
```

---

## Import Process Details

### Data Validation

The system validates:
1. **Required Fields** - All mandatory columns must have values
2. **Site Names** - Must match existing sites exactly (case-sensitive)
3. **Species Names** - Must match common or scientific names in database
4. **Date Formats** - Must be YYYY-MM-DD format
5. **Numerical Values** - Year, month, and count must be valid numbers
6. **Date Ranges** - Years between 1900-2100, months 1-12

### Automatic Grouping

Multiple rows with the same site and census date are automatically grouped into a single census record with multiple observations:

```
Input (2 rows):
- Test Site, 2024-01-15, Chinese Egret, 45
- Test Site, 2024-01-15, Black-faced Spoonbill, 23

Result (1 census, 2 observations):
Census: Test Site - 2024-01-15
  → Observation 1: Chinese Egret (45)
  → Observation 2: Black-faced Spoonbill (23)
```

### Duplicate Handling

If you import data for a species that already exists in a census:
- Counts are **added together**
- You receive a warning message
- Original notes and weather are preserved

**Example:**
```
Existing: Chinese Egret - 45 birds
Import:   Chinese Egret - 30 birds
Result:   Chinese Egret - 75 birds (merged)
```

---

## Export Process

### Basic Export

**Step 1:** Navigate to export page
```
Locations → Data Management → Export Census Data
```

**Step 2:** Select filters (all optional)
- Site: Export data from specific site
- Year: Filter by year
- Month: Filter by month
- Date Range: Custom start/end dates

**Step 3:** Download Excel file
- File includes all matching observations
- Formatted with headers and proper column widths
- Ready for analysis in Excel/Google Sheets

### Export Use Cases

**Scenario 1: Annual Report**
```
Filter: Year = 2024
Result: All census data from 2024 across all sites
```

**Scenario 2: Site-Specific Analysis**
```
Filter: Site = "Main Site", Year = 2024
Result: All 2024 data for Main Site only
```

**Scenario 3: Seasonal Study**
```
Filter: Month = 1 (January)
Result: All January observations across all years
```

---

## Viewing Census Totals

### Aggregated Totals Dashboard

**Access:** Locations → Data Management → View Census Totals

**Features:**
- Grand totals across all data
- Filterable by site/year/month
- Total birds, species diversity, census events
- Paginated for large datasets

**Dashboard Statistics:**
```
┌─────────────────────────────┐
│ Total Birds:      12,456    │
│ Species Recorded:      96    │
│ Census Events:        234    │
└─────────────────────────────┘
```

### Species Breakdown

Click "View Breakdown →" on any row to see detailed species-by-species counts:

**Information Shown:**
- Species common and scientific names
- IUCN conservation status (color-coded)
- Total count for selected period
- Number of separate observations
- Percentage of total birds

**Conservation Status Colors:**
- 🔴 Red: Critically Endangered (CR)
- 🟠 Orange: Endangered (EN)
- 🟡 Yellow: Vulnerable (VU)
- 🔵 Blue: Near Threatened (NT)
- 🟢 Green: Least Concern (LC)

---

## Running Tests

### Test Suite

Run all import/export tests:
```bash
python manage.py test apps.locations.tests.test_import_export
```

### Specific Test Categories

**Validation Tests:**
```bash
python manage.py test apps.locations.tests.test_import_export.ExcelImportValidationTestCase
```

**Integration Tests:**
```bash
python manage.py test apps.locations.tests.test_import_export.ExcelImportIntegrationTestCase
```

**Export Tests:**
```bash
python manage.py test apps.locations.tests.test_import_export.ExcelExportTestCase
```

**View Tests:**
```bash
python manage.py test apps.locations.tests.test_import_export.ImportExportViewsTestCase
```

---

## Common Issues & Solutions

### Issue 1: "Species not found in database"

**Problem:** Species name doesn't match database exactly

**Solution:**
1. Check species list in admin panel
2. Use exact common or scientific name
3. Case-insensitive matching is supported

**Example:**
```
❌ "chinese egret" or "egret"
✅ "Chinese Egret" or "Egretta eulophotes"
```

### Issue 2: "Site not found"

**Problem:** Site name doesn't match exactly

**Solution:**
1. Site names are case-sensitive
2. Check spelling and spacing
3. View active sites in dashboard

**Example:**
```
❌ "main site" or "Main  Site" (extra space)
✅ "Main Site"
```

### Issue 3: "Invalid date format"

**Problem:** Date not in YYYY-MM-DD format

**Solution:**
- Use format: 2024-01-15 (not 01/15/2024 or 15-Jan-2024)
- Excel may auto-format dates - check cell format
- Set cell type to "Text" before entering dates

### Issue 4: Import seems slow

**Problem:** Large file takes time to process

**Expected Performance:**
- 100 rows: ~5 seconds
- 1,000 rows: ~30 seconds
- 10,000 rows: ~3 minutes

**Tips:**
- Break large imports into smaller batches
- Import site-by-site for better error isolation
- Avoid importing during peak usage

---

## Security & Permissions

### Role-Based Access

**SUPERADMIN:**
- Full import/export access
- Can overwrite existing data
- Can delete census records

**ADMIN:**
- Import/export access
- Cannot delete historical data
- Audit trail logged

**USER (Field Worker):**
- View-only access to totals
- Can request imports via Data Request system
- Cannot directly import/export

**Reference:** AGENTS.md §6.1 Security - Role-based access control

---

## Best Practices

### Data Entry

1. **Use Consistent Naming**
   - Standardize site names across all data
   - Use official species names from database

2. **Date Consistency**
   - Group observations from same fieldwork session
   - Use same census date for all species observed together

3. **Validation Before Import**
   - Review data in Excel first
   - Check for typos and formatting
   - Use template format

### Large Datasets

1. **Batch Processing**
   ```
   Year 2020: 1,500 rows → Import separately
   Year 2021: 1,200 rows → Import separately
   Year 2022: 1,800 rows → Import separately
   ```

2. **Error Handling**
   - Import smaller batches first
   - Fix errors before importing rest
   - Keep backup of original data

3. **Performance**
   - Import during off-peak hours
   - Close other browser tabs
   - Wait for confirmation message

---

## API Endpoints (Advanced)

For programmatic access:

### Import
```
POST /locations/data/import/
Content-Type: multipart/form-data
Body: excel_file=<file>
```

### Export
```
POST /locations/data/export/
Body: site_id=<uuid>&year=<int>&month=<int>
Returns: Excel file download
```

### Totals
```
GET /locations/data/totals/?site=<uuid>&year=<int>&month=<int>
Returns: HTML page with aggregated data
```

---

## Troubleshooting

### Step-by-Step Debugging

1. **Download fresh template**
2. **Test with single row** (one observation)
3. **Verify in database** (check census was created)
4. **Add more rows** gradually
5. **Check error messages** for specific row numbers

### Getting Help

**Error Messages:**
- Always include row number (e.g., "Row 5: Invalid year")
- Error messages are specific and actionable
- Review import results page for full error list

**Log Files:**
- Check Django logs: `python manage.py check`
- User activity logged automatically
- Import actions tracked in audit log

---

## Future Enhancements

Planned features:
- [ ] CSV import support
- [ ] Batch edit imported data
- [ ] Import preview before committing
- [ ] Scheduled exports
- [ ] API token authentication for automated imports
- [ ] Species auto-matching suggestions
- [ ] Import from mobile field apps

---

## Summary

| Feature | Description | User Roles |
|---------|-------------|------------|
| **Import** | Bulk import from Excel | ADMIN, SUPERADMIN |
| **Export** | Download filtered data | ALL |
| **Totals** | View aggregated counts | ALL |
| **Breakdown** | Species-level details | ALL |
| **Template** | Formatted Excel template | ALL |

**Key Benefits:**
- ✅ Import 96+ species in minutes
- ✅ Automatic validation prevents errors
- ✅ Duplicate detection protects data integrity
- ✅ Flexible filtering for analysis
- ✅ Comprehensive audit trail

---

**Questions or Issues?**
Contact your system administrator or refer to:
- `AGENTS.md` - Development guidelines
- `docs/TROUBLESHOOTING.md` - General troubleshooting
- `docs/USER_MANUAL.md` - End-user documentation

