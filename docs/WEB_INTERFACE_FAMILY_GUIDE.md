# Where to Find Family Selection in the Web Interface

## 🌐 Web Interface Locations

### 1. **Add New Species** (Primary Location)
**URL**: `http://127.0.0.1:8000/fauna/species/create/`

**Steps**:
1. Open your browser to `http://127.0.0.1:8000`
2. Navigate to **Species Management** (in the main menu)
3. Click **"Add Species"** button
4. Look for the **"Family"** dropdown field

**What You'll See**:
- A dropdown menu with exactly 7 options:
  - Herons and Egrets
  - Geese & Ducks  
  - Ibises & Spoonbills
  - Shorebirds-Waders
  - Rails, Gallinules & Coots
  - Gulls, Terns & Skimmers
  - Additional Species

### 2. **Edit Existing Species**
**URL**: `http://127.0.0.1:8000/fauna/species/<species-id>/edit/`

**Steps**:
1. Go to **Species Management**
2. Click on any existing species name
3. Click **"Edit"** button
4. Find the **"Family"** dropdown field

### 3. **Species List with Family Filter**
**URL**: `http://127.0.0.1:8000/fauna/species/`

**Steps**:
1. Go to **Species Management**
2. Use the **"Filter by Family"** dropdown to filter species
3. Only the 7 active families will be shown

## 📍 Visual Guide

```
Main Navigation Menu
├── Dashboard
├── Species Management  ← CLICK HERE
│   ├── List Species    ← See all species with family filter
│   ├── Add Species     ← ADD NEW SPECIES (Family dropdown here)
│   └── Edit Species    ← Edit existing (Family dropdown here)
├── Sites & Census
└── Analytics
```

## 🎯 Family Dropdown Location

When you're on the **Add Species** or **Edit Species** page:

```
Species Information Form
├── Name: [Text Input]
├── Scientific Name: [Text Input]  
├── Family: [DROPDOWN MENU] ← FAMILY SELECTION HERE
├── IUCN Status: [Dropdown]
├── Description: [Text Area]
└── Image: [File Upload]
```

## 🔍 What You'll See in the Family Dropdown

The dropdown will show exactly these 7 options:

1. **Herons and Egrets**
2. **Geese & Ducks**
3. **Ibises & Spoonbills**
4. **Shorebirds-Waders**
5. **Rails, Gallinules & Coots**
6. **Gulls, Terns & Skimmers**
7. **Additional Species**

## 🚀 Quick Access

**Direct URLs**:
- **Add Species**: `http://127.0.0.1:8000/fauna/species/create/`
- **List Species**: `http://127.0.0.1:8000/fauna/species/`
- **Species Management**: `http://127.0.0.1:8000/fauna/`

## 💡 Pro Tips

1. **Bookmark the Add Species page** for quick access
2. **Use the family filter** on the species list to see species by family
3. **The dropdown is required** - you must select a family when adding species
4. **All 7 families are active** and ready for immediate use

## 🔧 If You Need More Families

The system is designed to easily add more families when needed. Use the management command:

```bash
python manage.py add_bird_family "New Family Name" --dry-run
```

This will show you how to add additional families to the dropdown.
