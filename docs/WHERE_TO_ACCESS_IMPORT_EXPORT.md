# Where to Access Import/Export & Census Totals

## 📍 Access Points Overview

You can access the Census Data Import/Export system from **3 convenient locations**:

---

## **1. Main Navigation Sidebar** ⭐ (Always Available)

The **primary access point** - available from anywhere in the application.

**Location:** Left sidebar menu (visible when logged in as ADMIN or SUPERADMIN)

```
┌─────────────────────────────┐
│ AVICAST Menu                │
├─────────────────────────────┤
│ 🏠 Home                     │
│ 🦅 Species Management       │
│ 📍 Site Management          │
│ 📈 Analytics Dashboard      │
│ 📊 Species Analytics        │
│                             │
│ --- ADMIN FEATURES ---      │
│ 📷 Image Processing         │
│ 🌤️  Weather Forecasting     │
│                             │
│ 📥 Data Import/Export       │  ⬅️ CLICK HERE
│ 📱 Mobile Data Import       │
│ ✓  Data Requests            │
└─────────────────────────────┘
```

**How to Access:**
1. Login to AVICAST
2. Look at the left sidebar
3. Find **"📥 Data Import/Export"** (under Admin Features)
4. Click to access the data management hub

**URL:** `http://127.0.0.1:8000/locations/data/`

---

## **2. Site Management Dashboard** (Quick Access Buttons)

**Location:** Top-right corner of the Site Management Dashboard

**Visual Layout:**
```
┌────────────────────────────────────────────────────────────────┐
│ 📍 Site Management Dashboard                                    │
│ Manage wildlife monitoring sites and their census data          │
│                                                                  │
│                          [ Import/Export Data ] [ View Totals ] [ New Site ] ⬅️ HERE
└────────────────────────────────────────────────────────────────┘

┌─────────────┬─────────────┬─────────────┬─────────────┐
│ 🗺️ Total    │ 📍 Sites    │ 📅 Active   │ 🦅 Total    │
│   Sites     │   Coordinated│   Years     │  Observations│
└─────────────┴─────────────┴─────────────┴─────────────┘
```

**How to Access:**
1. Navigate to: **Site Management** (from sidebar or home)
2. Look at the **top-right corner** of the page
3. You'll see three buttons:
   - **📥 Import/Export Data** - Opens data management hub
   - **📊 View Totals** - Jump directly to census totals
   - **➕ New Site** - Create new site

**These buttons only appear for ADMIN and SUPERADMIN users**

---

## **3. Census Management Page** (Contextual Access)

**Location:** When viewing census records for a specific month

**Visual Layout:**
```
Breadcrumb: Sites → Main Site → 2024 → January → Census Records

┌────────────────────────────────────────────────────────────────┐
│ January 2024                                                     │
│ Main Site - Census Records                                      │
│                                                                  │
│                    [ Import Data ] [ View Totals ] [ Add Census ] ⬅️ HERE
└────────────────────────────────────────────────────────────────┘

┌─────────────┬─────────────┬─────────────┬─────────────┐
│ 📋 Census   │ 🦅 Total    │ 🐾 Species  │ 👥 Field    │
│   Records   │   Birds     │   Recorded  │  Personnel  │
└─────────────┴─────────────┴─────────────┴─────────────┘
```

**How to Access:**
1. Navigate: **Site Management** → Select a site → Select a year → Select a month
2. You're now in the **Census Records** page
3. Look at the **top-right** under the month title
4. You'll see:
   - **📥 Import Data** - Opens import hub
   - **📊 View Totals** - Shows totals **filtered for this specific site/year/month**
   - **➕ Add Census Record** - Manual entry

**Smart Filtering:** The "View Totals" button automatically filters by the current site, year, and month!

---

## **Quick Navigation Paths**

### **Path 1: Import Historical Data**
```
Login → Sidebar: Data Import/Export → Import Census Data → Upload Excel → Done
Time: 2 minutes
```

### **Path 2: View Census Totals**
```
Login → Sidebar: Data Import/Export → View Census Totals → Apply Filters
OR
Login → Site Management → View Totals button (top-right)
Time: 30 seconds
```

### **Path 3: Export Data**
```
Login → Sidebar: Data Import/Export → Export Census Data → Select Filters → Download
Time: 1 minute
```

### **Path 4: View Totals for Specific Month**
```
Login → Site Management → Select Site → Select Year → Select Month
→ Click "View Totals" button (automatically filtered!)
Time: 1 minute
```

---

## **What Each Section Contains**

### **Import/Export Hub** (`/locations/data/`)
- **Three Main Cards:**
  1. **Import Data** - Upload Excel files
  2. **Export Data** - Download filtered data
  3. **View Totals** - Aggregated counts

- **Statistics:**
  - Active Sites
  - Census Records
  - Total Observations
  - Species Recorded

- **Quick Start Guide** - Instructions for each feature

### **Census Totals View** (`/locations/data/totals/`)
- **Grand Totals:** Overall statistics
- **Filters:** Site, Year, Month (any combination)
- **Table Columns:**
  - Site Name
  - Year
  - Month
  - Total Birds (⭐ The count you asked for!)
  - Species Count
  - Census Events
  - Actions (View Breakdown link)

- **Pagination:** 25 records per page

### **Species Breakdown** (`/locations/data/breakdown/`)
- Accessed by clicking "View Breakdown →" on any total
- Shows **species-by-species** counts
- Displays:
  - Common Name
  - Scientific Name
  - IUCN Conservation Status (color-coded)
  - Total Count
  - Number of Observations
  - Percentage of Total

---

## **Role-Based Visibility**

| Feature | SUPERADMIN | ADMIN | USER (Field Worker) |
|---------|------------|-------|---------------------|
| Sidebar Link | ✅ | ✅ | ❌ |
| Site Dashboard Buttons | ✅ | ✅ | ❌ |
| Census Page Buttons | ✅ | ✅ | ❌ |
| Import Data | ✅ | ✅ | ❌ |
| Export Data | ✅ | ✅ | ✅ (read-only) |
| View Totals | ✅ | ✅ | ✅ |

**Note:** Field Workers (USER role) can view totals and export data, but cannot import.

---

## **URL Reference**

For direct access or bookmarking:

| Feature | URL | Description |
|---------|-----|-------------|
| **Hub** | `/locations/data/` | Main data management hub |
| **Template** | `/locations/data/template/` | Download Excel template |
| **Import** | `/locations/data/import/` | Import form |
| **Export** | `/locations/data/export/` | Export with filters |
| **Totals** | `/locations/data/totals/` | Aggregated totals dashboard |
| **Breakdown** | `/locations/data/breakdown/?site=X&year=Y&month=Z` | Species details |

**Example Full URLs:**
```
http://127.0.0.1:8000/locations/data/
http://127.0.0.1:8000/locations/data/totals/
http://127.0.0.1:8000/locations/data/totals/?site=abc-123&year=2024&month=1
```

---

## **Visual Flow Diagram**

```
                    ┌─────────────────────┐
                    │   Login to AVICAST  │
                    └──────────┬──────────┘
                               │
            ┌──────────────────┼──────────────────┐
            │                  │                  │
            ▼                  ▼                  ▼
    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
    │   Sidebar    │  │     Site      │  │   Census     │
    │   Menu       │  │  Management   │  │   Records    │
    │              │  │   Dashboard   │  │     Page     │
    └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
           │                 │                  │
           │    [Buttons at top-right]         │
           │                 │                  │
           └────────┬────────┴─────────┬────────┘
                    │                  │
                    ▼                  ▼
           ┌──────────────────┐  ┌──────────────────┐
           │  Data Import/    │  │  Census Totals   │
           │  Export Hub      │  │  (Filtered)      │
           └────────┬─────────┘  └──────────────────┘
                    │
        ┌───────────┼───────────┐
        │           │           │
        ▼           ▼           ▼
   ┌────────┐  ┌────────┐  ┌────────┐
   │ Import │  │ Export │  │ Totals │
   └────────┘  └────────┘  └────────┘
```

---

## **Tips for Quick Access**

### **Bookmark These URLs:**
```
Data Hub:    http://127.0.0.1:8000/locations/data/
Totals View: http://127.0.0.1:8000/locations/data/totals/
```

### **Keyboard Shortcuts:**
1. Press `Ctrl+K` or `Cmd+K` (if implemented) to open quick navigation
2. Type "import" or "data" to find the import/export hub

### **Most Common Workflow:**
```
1. Sidebar → Data Import/Export
2. Download Template (first time only)
3. Import Census Data → Upload Excel
4. View Census Totals → Check imported data
5. Export Data (for reports/analysis)
```

---

## **Troubleshooting Access**

### **"I don't see the Data Import/Export link"**
- **Check your role:** Only ADMIN and SUPERADMIN can see this
- **Check sidebar:** Should be under "Admin Features" section
- **Try refreshing:** Log out and log back in

### **"I don't see the quick action buttons"**
- **Check your role:** Only ADMIN and SUPERADMIN see these buttons
- **Check page:** Buttons only appear on Site Dashboard and Census pages
- **Clear cache:** Hard refresh your browser (Ctrl+F5)

### **"The buttons don't work"**
- **Check URL routes:** Run `python manage.py check`
- **Check browser console:** Look for JavaScript errors
- **Try direct URL:** Navigate to `/locations/data/` directly

---

## **Summary**

**3 Ways to Access:**
1. **Sidebar Menu** - Always visible (Admin/Superadmin)
2. **Site Dashboard** - Quick access buttons (top-right)
3. **Census Page** - Contextual buttons with auto-filtering (top-right)

**Key Features:**
- 📥 **Import:** Bulk upload from Excel
- 📤 **Export:** Download filtered data
- 📊 **Totals:** View aggregated counts by site/year/month ⭐
- 🔍 **Breakdown:** Species-level details

**All accessible within 1-2 clicks from any location in the app!**


