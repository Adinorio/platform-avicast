# Annual Trends Report Guide

## Overview

The **Annual Trends & Report Charts** feature provides comprehensive visualizations for Asian Waterbird Census (AWC) reporting, including year-over-year population trends, species composition, and diversity metrics.

**Reference**: AGENTS.md §Development Guidelines, §Testing Instructions

## Features

### A. Charts - Species Composition and Abundance

#### 1. Top 5 Species Composition (Pie Chart)
- **What it shows**: The 5 most abundant species observed across all surveys
- **Use for**: Understanding dominant species in your monitoring area
- **Includes**: 
  - Species common name
  - Scientific name
  - IUCN conservation status (CR, EN, VU, NT, LC)
  - Total count across all years

#### 2. Endangered & Threatened Species Highlight
- **What it shows**: All species with conservation concerns (CR, EN, VU status)
- **Use for**: Highlighting species of conservation importance
- **Color-coded**: Red (CR), Orange (EN), Blue (VU)

### B. Graphs - Annual Population Trends

#### 1. Total Waterbird Population Trends (Line Graph)
- **What it shows**: Year-over-year comparison of total waterbird counts
- **Years covered**: Automatically detects years from your census data
- **Use for**: Demonstrating population trends for AWC reports
- **Features**: Interactive tooltips showing exact counts per year

#### 2. Top 3 Most Abundant Species - Abundance Comparison (Multi-line Graph)
- **What it shows**: The 3 most abundant species compared across years
- **Use for**: Comparing individual species trends over time
- **Features**: 
  - Each species shown as separate colored line
  - Easy identification of increasing/decreasing trends
  - Interactive legend

#### 3. Species Diversity Over Time (Bar Chart)
- **What it shows**: Number of unique species observed per year
- **Use for**: Demonstrating biodiversity trends
- **Metric**: Total unique species count

#### 4. Additional Species Recorded
- **What it shows**: New species observed each year (e.g., Eurasian Coot, Slaty-Breasted Rail)
- **Use for**: Tracking biodiversity expansion
- **Format**: Organized by year with species badges

### C. Annual Statistics Summary Table

Provides comprehensive yearly breakdown:
- Total birds counted
- Number of unique species
- Number of census records
- Average birds per census

## Access

### Via Analytics Dashboard
1. Navigate to **Analytics Dashboard** (`/analytics/`)
2. Click **"Annual Trends"** button (yellow/warning color)
3. Or use direct URL: `/analytics/annual-trends/`

### Via Main Navigation
- Home → Analytics → Annual Trends & Report Charts

## Report Generation

### Print Report
- Click **"Print Report"** button to generate print-friendly version
- All charts are preserved in print output
- Navigation elements hidden for clean printing

### Generate Formal Report
- Click **"Generate Formal Report"** to create exportable document
- Includes all visualizations and data tables
- Available formats: HTML, PDF (configured in Report Generator)

## Data Requirements

### Minimum Data Needed
- Census observations with dates
- Species information linked to observations
- At least 1 year of data (multiple years recommended)

### Optimal Data
- **3+ years of data** for meaningful trend analysis
- Regular census intervals (monthly/quarterly recommended)
- Consistent species identification
- IUCN status assigned to species

## Technical Details

### Data Processing
- **Year extraction**: Automatically extracts year from `census_date`
- **Aggregation**: Uses Django ORM for efficient data grouping
- **Real-time**: Pulls data directly from operational database (no caching)

### Chart Technology
- **Library**: Chart.js 4.x
- **Chart types**: Pie, Line (multi-line), Bar
- **Responsive**: Auto-adjusts to screen size
- **Interactive**: Hover tooltips with detailed information

### Performance
- **Optimization**: Indexed database queries
- **Pagination**: Not needed (summary data only)
- **Load time**: < 2 seconds for typical datasets (1000+ records)

## Use Cases

### 1. Asian Waterbird Census (AWC) Annual Reports
**Required Charts**:
- ✅ Top 5 species composition
- ✅ Annual population trends graph
- ✅ Top 3 species abundance comparison

**Usage**:
1. Navigate to Annual Trends Report
2. Click "Print Report"
3. Save as PDF or copy charts to Word document
4. Include in AWC submission

### 2. Conservation Status Monitoring
**Focus**:
- Endangered & Threatened Species section
- Year-over-year trends for at-risk species

**Usage**:
1. Check highlighted conservation concern species
2. Review Top 3 abundance to see if threatened species are declining
3. Document in conservation reports

### 3. Biodiversity Assessment
**Focus**:
- Species diversity over time chart
- Additional species recorded section

**Usage**:
1. Track increasing/decreasing species diversity
2. Document new species discoveries
3. Support biodiversity grant applications

### 4. Site Management Planning
**Focus**:
- Annual statistics summary table
- Population trend graphs

**Usage**:
1. Identify peak years for planning surveys
2. Allocate resources based on trends
3. Justify budget requests with data

## Troubleshooting

### No Data Displayed
**Issue**: "No species data available" message  
**Solution**:
- Verify census observations exist in database
- Check that species are properly linked to observations
- Ensure `census_date` field is populated

### Missing Years in Graphs
**Issue**: Expected years not showing in charts  
**Solution**:
- Verify census dates are correct (not NULL)
- Check that observations exist for those years
- Ensure year extraction is working (check admin panel)

### Charts Not Loading
**Issue**: Blank spaces where charts should be  
**Solution**:
- Check browser console for JavaScript errors
- Verify Chart.js is loading (CDN connection)
- Try hard refresh (Ctrl+F5 / Cmd+Shift+R)
- Check if ad blockers are interfering

### Incorrect Species Counts
**Issue**: Numbers don't match expectations  
**Solution**:
- Verify CensusObservation count field values
- Check for duplicate observations
- Run data integrity check: `python manage.py check_data`
- Verify species linkage is correct

## Future Enhancements

### Planned Features
1. **Migratory Species Tracking**
   - Add `is_migratory` field to Species model
   - Separate charts for resident vs. migratory species
   - Seasonal pattern analysis

2. **Export to Excel**
   - Download raw data behind charts
   - Pre-formatted for AWC submissions
   - Include metadata and timestamps

3. **Custom Date Ranges**
   - Filter by specific year ranges
   - Compare any two periods
   - Custom reporting periods

4. **Site-Specific Trends**
   - Filter charts by individual sites
   - Multi-site comparison
   - Geographic distribution maps

5. **Statistical Analysis**
   - Trend significance testing
   - Confidence intervals
   - Population growth rates

## Related Documentation

- [Analytics Dashboard Guide](ANALYTICS_DASHBOARD_SOLUTION.md)
- [Report Generator Guide](docs/USER_MANUAL.md)
- [Census Data Import](CENSUS_IMPORT_EXPORT_GUIDE.md)
- [Species Management](USER_MANUAL.md)

## Support

For technical issues or questions:
1. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. Review [AGENTS.md](../AGENTS.md) §Analytics
3. Contact system administrator

---

**Version**: 1.0  
**Last Updated**: 2025-01-13  
**Compatible with**: AVICAST v4.2+

