# Census Data Import/Export - Quick Start

## 5-Minute Tutorial

### Step 1: Access the Data Management Hub
1. Login to AVICAST as ADMIN or SUPERADMIN
2. Click **"Data Import/Export"** in the sidebar
3. You'll see three main options: Import, Export, and View Totals

### Step 2: Download and Fill Template
1. Click **"Download Template"**
2. Open the Excel file
3. Fill in your census data (example provided in template)

**Example Data:**
```
Site Name    | Year | Month | Census Date  | Species Name        | Count | Weather | Notes
Main Site    | 2024 | 1     | 2024-01-15  | Chinese Egret       | 45    | Sunny   | Morning
Main Site    | 2024 | 1     | 2024-01-15  | Black-faced Spoonbill | 23  | Sunny   | Same census
Coastal Site | 2024 | 2     | 2024-02-10  | Chinese Egret       | 67    | Cloudy  | High tide
```

### Step 3: Import Your Data
1. Click **"Import Census Data"**
2. Select your filled Excel file
3. Click **"Import Data"**
4. Review the results page

✅ **Success:** You'll see how many observations were imported
⚠️ **Errors:** Any validation errors will show with specific row numbers

### Step 4: View Your Imported Data
1. Click **"View Census Totals"**
2. Filter by site, year, or month
3. Click **"View Breakdown"** to see species details

### Step 5: Export Data (Optional)
1. Click **"Export Census Data"**
2. Select your filters (site, year, month, date range)
3. Click **"Download Excel"**
4. Use the exported file for analysis or reports

---

## Common Use Cases

### Use Case 1: Import 5 Years of Historical Data
**Scenario:** You have bird census data from 2019-2023 in spreadsheets

**Steps:**
1. Download template
2. Copy your data year-by-year into separate sheets
3. Import each year separately (better error handling)
4. Verify totals after each import

**Time Estimate:** 30-60 minutes for 5 years of data

### Use Case 2: Monthly Report Generation
**Scenario:** Generate monthly bird count reports for stakeholders

**Steps:**
1. Go to Export page
2. Filter: Month = Current Month, Year = Current Year
3. Download Excel file
4. Open in Excel/Google Sheets for formatting
5. Share with stakeholders

**Time Estimate:** 2-3 minutes per report

### Use Case 3: Site Comparison Analysis
**Scenario:** Compare bird populations across multiple sites

**Steps:**
1. Go to View Census Totals
2. Apply no filters (see all data)
3. Sort by site name
4. Compare total birds and species diversity
5. Click breakdown for detailed species comparison

**Time Estimate:** 5-10 minutes

---

## Tips & Tricks

### For Large Datasets (1000+ rows)
- Import in batches of 500 rows
- Test with 10 rows first
- Use consistent naming conventions
- Keep a backup of your original data

### For Best Data Quality
- Validate species names before import
- Use YYYY-MM-DD format for dates
- Group observations from same field visit
- Add weather conditions and notes for context

### For Faster Workflows
- Bookmark the Import/Export hub
- Save your export filter preferences in Excel
- Create template copies for different sites
- Review import results page for any warnings

---

## Troubleshooting in 30 Seconds

| Problem | Solution |
|---------|----------|
| Species not found | Check spelling, use exact name from database |
| Site not found | Verify site name is exact match (case-sensitive) |
| Date format error | Use YYYY-MM-DD format (e.g., 2024-01-15) |
| Count must be positive | Ensure count > 0 |
| Import seems slow | Large files take time, be patient |

---

## Next Steps

📖 **Full Documentation:** See `docs/CENSUS_IMPORT_EXPORT_GUIDE.md`

🧪 **Run Tests:** `python manage.py test apps.locations.tests.test_import_export`

🎯 **Best Practices:** Review AGENTS.md §3 File Organization

💡 **Get Help:** Contact system administrator or check logs

---

**That's it! You're ready to manage historical census data efficiently.** 🎉

