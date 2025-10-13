"""
Forms for locations app
"""

from django import forms
from django.contrib.auth import get_user_model
from .models import Site, CensusYear, CensusMonth, Census, CensusObservation

User = get_user_model()


class CoordinateInputWidget(forms.TextInput):
    """Custom widget for coordinate input with validation"""
    
    def __init__(self, attrs=None):
        default_attrs = {
            'class': 'form-control coordinate-input',
            'placeholder': 'e.g., 14.5995, 120.9842 or 14°35\'58.2"N, 120°59\'3.1"E',
            'pattern': r'^-?\d+(\.\d+)?\s*[,;|]\s*-?\d+(\.\d+)?$|^\d+°\d+\'[\d.]+\"[NS]\s*,\s*\d+°\d+\'[\d.]+\"[EW]$',
            'title': 'Enter coordinates as "latitude, longitude" (decimal) or "degrees°minutes\'seconds\"N/S, degrees°minutes\'seconds\"E/W"'
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)


class SiteForm(forms.ModelForm):
    """Form for creating and editing sites"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make coordinates required
        self.fields['coordinates'].required = True
        self.fields['coordinates'].error_messages = {
            'required': 'Coordinates are required for site location mapping.',
        }

    def clean_coordinates(self):
        """Validate and normalize coordinates"""
        coordinates = self.cleaned_data.get('coordinates')
        if not coordinates:
            raise forms.ValidationError('Coordinates are required.')
        
        try:
            # Use the model's coordinate parsing method
            normalized_coords = Site.parse_coordinate_input(coordinates)
            return normalized_coords
        except ValueError as e:
            raise forms.ValidationError(f'Invalid coordinates: {str(e)}')

    class Meta:
        model = Site
        fields = ['name', 'site_type', 'coordinates', 'description', 'image', 'status']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter site name'}),
            'site_type': forms.Select(attrs={'class': 'form-control'}),
            'coordinates': CoordinateInputWidget(),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe the site location and characteristics'
            }),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }
        help_texts = {
            'coordinates': 'Enter coordinates as "latitude, longitude" (e.g., 14.5995, 120.9842) or DMS format (e.g., 14°35\'58.2"N, 120°59\'3.1"E)',
            'image': 'Upload an image of the site for better identification',
        }


class CensusYearForm(forms.ModelForm):
    """Form for creating and editing census years"""

    class Meta:
        model = CensusYear
        fields = ['site', 'year']
        widgets = {
            'site': forms.Select(attrs={'class': 'form-control'}),
            'year': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 2000,
                'max': 2030
            }),
        }


class CensusMonthForm(forms.ModelForm):
    """Form for creating and editing census months"""

    class Meta:
        model = CensusMonth
        fields = ['month']  # Only month field, year is set programmatically
        widgets = {
            'month': forms.Select(attrs={'class': 'form-control'}),
        }


class CensusForm(forms.ModelForm):
    """Form for creating and editing census records"""

    class Meta:
        model = Census
        fields = [
            'census_date', 'lead_observer', 'field_team',
            'weather_conditions', 'notes'
        ]
        widgets = {
            'census_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'lead_observer': forms.Select(attrs={'class': 'form-control'}),
            'field_team': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'weather_conditions': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Sunny, 25°C, light wind'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes about the census'
            }),
        }


class CensusObservationForm(forms.ModelForm):
    """Form for creating and editing census observations"""

    class Meta:
        model = CensusObservation
        fields = ['species', 'species_name', 'family', 'count']
        widgets = {
            'species': forms.Select(attrs={
                'class': 'form-control',
                'onchange': 'toggleSpeciesName()'
            }),
            'species_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter species name if not in list'
            }),
            'family': forms.Select(attrs={
                'class': 'form-control',
                'placeholder': 'Select family (optional)'
            }),
            'count': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Populate species choices from fauna app
        from apps.fauna.models import Species
        species_choices = [('', 'Select Species')] + [(species.id, species.name) for species in Species.objects.all()]
        self.fields['species'].choices = species_choices
        
        # Populate family choices (optional)
        family_choices = [
            ('', 'Select Family (Optional)'),
            ('HERONS AND EGRETS', 'Herons and Egrets'),
            ('SPOONBILLS', 'Spoonbills'),
            ('STILTS AND AVOCETS', 'Stilts and Avocets'),
            ('SANDPIPERS AND ALLIES', 'Sandpipers and Allies'),
            ('GULLS AND TERNS', 'Gulls and Terns'),
            ('KINGFISHERS', 'Kingfishers'),
            ('RAILS AND ALLIES', 'Rails and Allies'),
            ('DUCKS AND GEESE', 'Ducks and Geese'),
            ('PIGEONS AND DOVES', 'Pigeons and Doves'),
            ('CUCKOOS', 'Cuckoos'),
            ('OWLS', 'Owls'),
            ('SWIFTS', 'Swifts'),
            ('HORNBILLS', 'Hornbills'),
            ('BARBETS', 'Barbets'),
            ('WOODPECKERS', 'Woodpeckers'),
            ('FALCONS', 'Falcons'),
            ('PARROTS', 'Parrots'),
            ('BULBULS', 'Bulbuls'),
            ('CROWS AND ALLIES', 'Crows and Allies'),
            ('STARLINGS', 'Starlings'),
            ('THRUSHES', 'Thrushes'),
            ('FLYCATCHERS', 'Flycatchers'),
            ('WARBLERS', 'Warblers'),
            ('WEAVERS', 'Weavers'),
            ('FINCHES', 'Finches'),
            ('SPARROWS', 'Sparrows'),
            ('OTHER', 'Other'),
        ]
        self.fields['family'].choices = family_choices

        # Set initial visibility and requirement of species_name field
        species_selected = False
        if self.instance and self.instance.species:
            species_selected = True
            self.fields['species_name'].widget.attrs['style'] = 'display: none;'
            self.fields['species_name'].required = False
        elif self.data.get('species'):
            species_selected = True
            self.fields['species_name'].widget.attrs['style'] = 'display: none;'
            self.fields['species_name'].required = False
        else:
            # No species selected initially, show species_name field
            self.fields['species_name'].widget.attrs['style'] = 'display: block;'

    def clean(self):
        cleaned_data = super().clean()
        species = cleaned_data.get('species')
        species_name = cleaned_data.get('species_name')

        if not species and not species_name:
            raise forms.ValidationError("Either select a species or enter a species name.")

        # If species is selected, clear species_name
        if species:
            cleaned_data['species_name'] = ''

        return cleaned_data


class BatchObservationForm(forms.Form):
    """Form for batch adding multiple observations"""

    def __init__(self, *args, **kwargs):
        census = kwargs.pop('census', None)
        super().__init__(*args, **kwargs)

        # Populate species choices from fauna app
        from apps.fauna.models import Species
        species_choices = [('', 'Select Species')] + [(species.id, species.name) for species in Species.objects.all()]

        # Create initial observation forms (start with 1, add more dynamically)
        for i in range(1):
            self.fields[f'species_{i}'] = forms.ChoiceField(
                choices=species_choices,
                required=False,
                widget=forms.Select(attrs={
                    'class': 'form-control',
                    'onchange': f'toggleSpeciesName({i})'
                })
            )
            self.fields[f'species_name_{i}'] = forms.CharField(
                max_length=200,
                required=False,
                widget=forms.TextInput(attrs={
                    'class': 'form-control',
                    'placeholder': 'Enter species name if not in list',
                    'style': 'display: block;'
                })
            )
            self.fields[f'count_{i}'] = forms.IntegerField(
                min_value=1,
                required=False,
                widget=forms.NumberInput(attrs={
                    'class': 'form-control',
                    'min': 1
                })
            )

    def get_field_groups(self):
        """Return field groups for template rendering"""
        groups = []
        # Check how many observation groups we have (dynamically created)
        max_groups = 0
        for field_name in self.fields:
            # Only look for species fields that match pattern species_0, species_1, etc.
            # (not species_name_0)
            if field_name.startswith('species_') and not field_name.startswith('species_name_'):
                parts = field_name.split('_')
                if len(parts) >= 2 and parts[1].isdigit():
                    index = int(parts[1])
                    max_groups = max(max_groups, index + 1)

        for i in range(max_groups):
            if f'species_{i}' in self.fields:
                groups.append({
                    'species': self[f'species_{i}'],
                    'species_name': self[f'species_name_{i}'],
                    'count': self[f'count_{i}'],
                    'index': i
                })
        return groups

    def clean(self):
        cleaned_data = super().clean()
        observations = []

        # Check how many observation groups we have
        max_groups = 0
        for field_name in self.fields:
            # Only look for species fields that match pattern species_0, species_1, etc.
            # (not species_name_0)
            if field_name.startswith('species_') and not field_name.startswith('species_name_'):
                parts = field_name.split('_')
                if len(parts) >= 2 and parts[1].isdigit():
                    index = int(parts[1])
                    max_groups = max(max_groups, index + 1)

        for i in range(max_groups):
            if f'species_{i}' in cleaned_data:
                species = cleaned_data.get(f'species_{i}')
                species_name = cleaned_data.get(f'species_name_{i}')
                count = cleaned_data.get(f'count_{i}')

                if count and count > 0:
                    if not species and not species_name:
                        raise forms.ValidationError(f"Row {i+1}: Either select a species or enter a species name.")
                    observations.append({
                        'species': species,
                        'species_name': species_name,
                        'count': count
                    })

        if not observations:
            raise forms.ValidationError("Please add at least one observation.")

        return cleaned_data
