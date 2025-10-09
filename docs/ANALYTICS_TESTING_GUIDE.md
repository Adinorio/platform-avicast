# Analytics Dashboard Testing Guide

**Purpose**: Verify that the analytics dashboard renders correctly and all features work as expected.

---

## ✅ Pre-Testing Checklist

Before testing, ensure:
- [ ] Django development server is running
- [ ] You have valid login credentials
- [ ] You're using a web browser (not viewing files directly)

---

## 🚀 Step-by-Step Testing Procedure

### Step 1: Start the Server

```bash
cd C:\Users\LAPIS\Documents\Github\platform-avicast
python manage.py runserver 127.0.0.1:8000
```

**Expected Output**:
```
Watching for file changes with StatReloader
Performing system checks...
System check identified no issues (0 silenced).
Django version 4.2.23, using settings 'avicast_project.settings.development'
Starting development server at http://127.0.0.1:8000/
```

---

### Step 2: Login to the System

1. **Open your web browser** (Chrome, Firefox, Edge)
2. **Navigate to**: `http://127.0.0.1:8000/login/`
3. **Enter credentials**:
   - **Employee ID**: `010101`
   - **Password**: `avicast123`
4. **Click** the "Login" button

**Expected**: You should be redirected to the home dashboard

---

### Step 3: Access Analytics Dashboard

**Navigate to**: `http://127.0.0.1:8000/analytics/`

---

## 🎯 Expected Visual Output

### What You SHOULD See:

#### **1. Success Banner** (Green Alert)
```
✓ Success! Analytics dashboard rendered correctly for user: 010101
```

#### **2. Page Header**
- Blue chart icon
- Title: "Analytics Dashboard"
- Subtitle: "Wildlife monitoring insights for [Current Month]"

#### **3. Tier 1: Hero Section**

**Large Primary Metric Card**:
- Label: "Total Birds Observed This Month"
- Large number (e.g., "1,247 birds")
- Trend indicator (e.g., "↑ 23% vs last month")
- Green "Generate Report" button

**4 Secondary Metric Cards** (in a row):
1. Active Sites (with count + "sites" suffix)
2. Census Sessions (with count + "sessions" suffix)
3. Species Observed (with count + "species" suffix)
4. Active This Week (with count + "records" suffix)

#### **4. Tier 2: Key Insights**

**Left Panel (8 columns)**:
- "Population Trends Over Time" chart
- Interactive Plotly line chart
- Expand and download buttons

**Right Panel (4 columns)**:
- "🏆 Top Sites by Diversity" list
- Site names with species count badges
- "View All Sites" button

#### **5. Tier 3: More Analytics** (Collapsed)
- Collapsible section with down arrow
- When expanded, shows 3 additional charts

#### **6. Quick Actions** (Bottom)
4 colorful action buttons:
- Green: "Generate Report"
- Blue: "New Census"
- Cyan: "Manage Sites"
- Yellow: "View Species"

---

## ❌ What You Should NOT See

If you see any of these, something is wrong:

1. **Raw Django Template Code**:
   ```
   {% include 'analytics/components/metric_card.html' %}
   ```
   **Problem**: You're viewing the source file, not the rendered page

2. **Syntax Highlighting**:
   - Colored text with `{%`, `{{`, `%}` visible
   **Problem**: You're in an editor or viewing page source

3. **Login Page**:
   - If you see a login form instead of analytics
   **Problem**: You're not logged in - go to Step 2

4. **404 Error**:
   - "Page not found"
   **Problem**: Server not running or wrong URL

5. **500 Error**:
   - "Server Error"
   **Problem**: Check server logs for Python errors

---

## 🔍 Troubleshooting

### Issue: "I see raw template code"

**Diagnosis**: You're viewing the `.html` file itself, not the rendered output

**Solutions**:
1. Make sure you're accessing via `http://127.0.0.1:8000/analytics/`
2. NOT via `file:///C:/Users/...`
3. NOT via "View Page Source" (right-click)
4. NOT via opening the file in VS Code preview

---

### Issue: "I see a login page"

**Diagnosis**: Not authenticated

**Solutions**:
1. Go to `http://127.0.0.1:8000/login/`
2. Login with credentials:
   - Employee ID: `010101`
   - Password: `avicast123`
3. Then navigate to analytics

---

### Issue: "Charts don't load"

**Diagnosis**: JavaScript not loading or network issue

**Solutions**:
1. Open browser Developer Console (F12)
2. Check for JavaScript errors
3. Verify Plotly CDN is accessible
4. Check network tab for failed requests

---

### Issue: "No data showing (0 birds, 0 sites)"

**Diagnosis**: Empty database

**Solutions**:
1. This is normal for a fresh install
2. Add test data via:
   - Create sites in Site Management
   - Conduct census observations
   - Process images for bird counts
3. Alternatively, import sample data

---

## 📊 Feature Testing Checklist

Once dashboard loads successfully, test each feature:

### Metrics
- [ ] Hero metric shows bird count
- [ ] Trend indicator shows percentage
- [ ] Secondary metrics show correct counts
- [ ] Hover tooltips appear (if any)

### Charts
- [ ] Population Trends chart loads
- [ ] Chart is interactive (hover, zoom)
- [ ] Expand button works
- [ ] Download button works
- [ ] Top Sites list populates

### Navigation
- [ ] "More Analytics" expands/collapses
- [ ] Quick action buttons link correctly
- [ ] "Generate Report" opens report builder
- [ ] "New Census" goes to site list
- [ ] "Manage Sites" opens site management
- [ ] "View Species" opens species catalog

### Mobile Responsiveness
- [ ] Resize browser to mobile width
- [ ] Metrics stack vertically
- [ ] Charts resize properly
- [ ] Quick actions become sticky at bottom
- [ ] All buttons remain accessible

---

## 🎥 Visual Comparison

### ✅ CORRECT Rendering Example:
```
┌─────────────────────────────────────────────┐
│ ✓ Success! Analytics dashboard rendered... │
├─────────────────────────────────────────────┤
│ 📊 Analytics Dashboard                      │
│ Wildlife monitoring insights for October... │
├─────────────────────────────────────────────┤
│                                             │
│  ┌────────────────────────────────────┐    │
│  │ Total Birds Observed This Month    │    │
│  │           1,247 birds              │    │
│  │      ↑ 23% vs last month          │    │
│  │   [Generate Report]               │    │
│  └────────────────────────────────────┘    │
│                                             │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐      │
│  │  12  │ │  45  │ │   6  │ │  10  │      │
│  │sites │ │census│ │species│ │records│    │
│  └──────┘ └──────┘ └──────┘ └──────┘      │
│                                             │
│  [Chart: Population Trends]  [Top Sites]   │
│                                             │
└─────────────────────────────────────────────┘
```

### ❌ INCORRECT (Raw Template):
```
{% extends 'base.html' %}
{% load static %}

{% block title %}Analytics Dashboard{% endblock %}

{% include 'analytics/components/metric_card.html' with
  label='Total Birds Observed This Month'
  value=total_birds
```

---

## 📝 Testing Report Template

After testing, document your results:

```markdown
## Analytics Dashboard Test Report

**Date**: [Date]
**Tester**: [Your Name]
**Browser**: [Chrome/Firefox/Edge]
**Version**: [Browser Version]

### Results:

| Feature | Status | Notes |
|---------|--------|-------|
| Page loads | ✓/✗ | |
| Login works | ✓/✗ | |
| Metrics display | ✓/✗ | |
| Charts render | ✓/✗ | |
| Navigation works | ✓/✗ | |
| Mobile responsive | ✓/✗ | |

### Issues Found:
1. [Describe any issues]

### Screenshots:
[Attach screenshots if needed]

### Conclusion:
[Pass / Fail with explanation]
```

---

## 🚀 Success Criteria

The analytics dashboard is considered **WORKING** when:

1. ✅ Page loads without errors
2. ✅ Success banner appears
3. ✅ All metrics display with real or zero counts
4. ✅ Charts load (even if showing "No data")
5. ✅ All buttons are clickable and navigate correctly
6. ✅ Responsive design works on mobile
7. ✅ No console errors in browser dev tools
8. ✅ CSS styles are applied (Bootstrap + custom)

---

## 📞 Support

If you encounter issues not covered here:

1. Check Django server logs
2. Check browser console (F12)
3. Review `docs/ANALYTICS_PHASE1_COMPLETE.md`
4. Review `docs/ANALYTICS_PHASE2_COMPLETE.md`
5. Check system health: `python manage.py check`

---

**Last Updated**: October 4, 2025  
**Version**: Phase 2 Complete  
**Status**: Production Ready

