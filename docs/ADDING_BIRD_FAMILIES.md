# Adding New Bird Families to AVICAST

This guide explains how to add new bird families to make the system versatile and future-proof.

## Current Family Structure

The system currently has 50+ predefined bird families organized into categories:

### Water Birds
- Herons and Egrets
- Ibises & Spoonbills  
- Geese & Ducks
- Gulls, Terns & Skimmers
- Shorebirds-Waders
- Rails, Gallinules & Coots

### Land Birds
- Pheasants & Fowl
- Pigeons & Doves
- Cuckoos
- Swifts & Swallows
- Rails & Cranes

### Raptors
- Eagles & Hawks
- Owls
- Falcons

### Small Birds
- Kingfishers
- Bee-eaters
- Hoopoes
- Woodpeckers
- Barbets
- Hornbills

### Songbirds
- Passerines (Songbirds)
- Crows & Jays
- Larks
- Swallows & Martins
- Bulbuls
- Babblers
- Warblers
- Flycatchers
- Thrushes
- Chats
- Robins
- Sunbirds
- Sparrows & Finches
- Weavers
- Waxbills

### Scientific Families
- Ardeidae (Herons, Egrets, Bitterns)
- Anatidae (Ducks, Geese, Swans)
- Charadriidae (Plovers, Lapwings)
- Scolopacidae (Sandpipers, Snipes)
- Laridae (Gulls, Terns, Skimmers)
- Rallidae (Rails, Gallinules, Coots)
- Accipitridae (Eagles, Hawks, Kites)
- Falconidae (Falcons, Kestrels)
- Strigidae (Owls)
- Corvidae (Crows, Jays, Magpies)
- Alcedinidae (Kingfishers)
- Meropidae (Bee-eaters)
- Upupidae (Hoopoes)
- Picidae (Woodpeckers)
- Bucerotidae (Hornbills)
- Pycnonotidae (Bulbuls)
- Muscicapidae (Chats, Robins, Flycatchers)
- Turdidae (Thrushes)
- Sylviidae (Warblers)
- Nectariniidae (Sunbirds)
- Passeridae (Sparrows)
- Fringillidae (Finches)
- Ploceidae (Weavers)
- Estrildidae (Waxbills, Munias)

### Additional/Other
- Additional Species
- Uncategorized
- Other

## Methods to Add New Families

### Method 1: Direct Model Edit (Recommended for Developers)

1. **Edit the Model** (`apps/fauna/models.py`):
   ```python
   class BirdFamily(models.TextChoices):
       # Add your new family here
       NEW_FAMILY = "NEW FAMILY NAME", "Display Name"
       
       # Example:
       PENGUINS = "PENGUINS", "Penguins"
       FLAMINGOS = "FLAMINGOS", "Flamingos"
       PARROTS = "PARROTS", "Parrots"
   ```

2. **Create Migration**:
   ```bash
   python manage.py makemigrations fauna --name add_new_families
   python manage.py migrate fauna
   ```

3. **Update Import/Export Logic** (if needed):
   - Edit `apps/locations/utils/excel_handler.py`
   - Add family detection patterns if needed

### Method 2: Management Command (For Non-Developers)

Use the provided management command to add families dynamically.

### Method 3: Admin Interface (Future Enhancement)

A custom admin interface could be built for adding families through the web UI.

## Family Naming Conventions

### Standard Format
- **Value**: UPPERCASE_WITH_UNDERSCORES or "UPPERCASE WITH SPACES"
- **Display**: "Proper Case with Spaces"
- **Examples**:
  - `PENGUINS = "PENGUINS", "Penguins"`
  - `SEA_BIRDS = "SEA BIRDS", "Sea Birds"`
  - `WATERFOWL = "WATERFOWL", "Waterfowl"`

### Best Practices
1. **Use descriptive names** that clearly identify the bird group
2. **Keep names concise** but informative
3. **Use consistent formatting** with existing families
4. **Include scientific names** when appropriate (e.g., "Spheniscidae (Penguins)")
5. **Group related families** together in the code

## Integration Points

When adding new families, ensure compatibility with:

### 1. Import/Export System
- **Excel Handler**: Update family detection logic in `excel_handler.py`
- **Template Generation**: New families appear in export templates
- **Validation**: Import validates against new choices

### 2. Views and Templates
- **Family Grouping**: Views automatically group by new families
- **Filtering**: Family filters work with new choices
- **Analytics**: Family-based reports include new families

### 3. Census Management
- **CensusObservation**: Family field works with new choices
- **Family Totals**: Analytics include new families
- **Data Consistency**: All census data maintains family relationships

## Example: Adding Penguin Family

### Step 1: Edit Model
```python
# In apps/fauna/models.py
class BirdFamily(models.TextChoices):
    # Add to appropriate section
    PENGUINS = "PENGUINS", "Penguins"
    # Or with scientific name:
    SPHENISCIDAE = "Spheniscidae", "Spheniscidae (Penguins)"
```

### Step 2: Create Migration
```bash
python manage.py makemigrations fauna --name add_penguins
python manage.py migrate fauna
```

### Step 3: Update Excel Handler (if needed)
```python
# In apps/locations/utils/excel_handler.py
# Add to family detection logic:
elif any(pattern in species_upper for pattern in ['PENGUIN']):
    family_name = 'PENGUINS'
```

### Step 4: Test
```bash
python manage.py shell
>>> from apps.fauna.models import Species
>>> Species.BirdFamily.choices  # Verify new choice appears
>>> # Test creating species with new family
```

## Verification Checklist

After adding new families:

- [ ] **Model**: New family appears in `Species.BirdFamily.choices`
- [ ] **Form**: Dropdown includes new family option
- [ ] **Database**: Migration applied successfully
- [ ] **Import/Export**: Excel handler recognizes new family (if needed)
- [ ] **Views**: Family grouping works with new family
- [ ] **Analytics**: Family-based reports include new family
- [ ] **Census**: CensusObservation can use new family

## Troubleshooting

### Common Issues

1. **Migration Errors**:
   - Check for typos in family names
   - Ensure proper syntax in TextChoices
   - Run `python manage.py showmigrations fauna` to check status

2. **Form Not Showing New Family**:
   - Restart development server
   - Check browser cache
   - Verify migration was applied

3. **Import/Export Issues**:
   - Update family detection logic in `excel_handler.py`
   - Test with sample data
   - Check validation rules

### Getting Help

- Check Django logs for detailed error messages
- Use `python manage.py shell` to test model changes
- Verify database schema with `python manage.py dbshell`

## Future Enhancements

### Planned Features
1. **Admin Interface**: Web-based family management
2. **Dynamic Families**: Add families without code changes
3. **Family Hierarchy**: Support for sub-families
4. **Import Validation**: Automatic family suggestions
5. **Bulk Operations**: Mass family updates

### Contributing
When adding families:
1. Follow naming conventions
2. Update documentation
3. Test all integration points
4. Consider backward compatibility
5. Update this guide if needed

---

**Note**: Always backup your database before making model changes in production!
