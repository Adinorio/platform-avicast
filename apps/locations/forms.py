from django import forms
from django.contrib.auth.models import User
from .models import Site, CensusObservation, SpeciesObservation
from django.forms import inlineformset_factory
from django.utils import timezone

class SiteForm(forms.ModelForm):
    class Meta:
        model = Site
        fields = ['name', 'site_type', 'coordinates', 'description', 'status']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'site_type': forms.Select(attrs={'class': 'form-control'}),
            'coordinates': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Latitude, Longitude'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

class CensusObservationForm(forms.ModelForm):
    class Meta:
        model = CensusObservation
        fields = ['observation_date', 'weather_conditions', 'notes']
        widgets = {
            'observation_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'weather_conditions': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Sunny, 25°C, Light breeze'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'General observation notes...'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.site = kwargs.pop('site', None)
        super().__init__(*args, **kwargs)
        if self.site:
            self.fields['observation_date'].widget.attrs['max'] = timezone.now().date().isoformat()

class SpeciesObservationForm(forms.ModelForm):
    class Meta:
        model = SpeciesObservation
        fields = ['species_name', 'count', 'behavior_notes']
        widgets = {
            'species_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Mallard, American Robin'}),
            'count': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'behavior_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Behavior, age, sex, etc.'}),
        }

# Create inline formset for species observations
SpeciesObservationFormSet = inlineformset_factory(
    CensusObservation,
    SpeciesObservation,
    form=SpeciesObservationForm,
    extra=3,  # Start with 3 empty species fields
    can_delete=True,
    min_num=1,  # At least one species must be observed
    validate_min=True,
)

class CensusImportForm(forms.Form):
    file = forms.FileField(
        label='Select File',
        help_text='Upload CSV or Excel file with census data',
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
    observation_date = forms.DateField(
        label='Observation Date',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        help_text='Date for this census observation'
    )
    weather_conditions = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Weather conditions during observation'}),
        help_text='Optional weather information'
    )
    notes = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'General notes about this census'}),
        help_text='Optional general notes'
    )
    
    def clean_file(self):
        file = self.cleaned_data['file']
        if file:
            # Check file extension
            if not file.name.endswith(('.csv', '.xlsx', '.xls')):
                raise forms.ValidationError('Please upload a CSV or Excel file (.csv, .xlsx, .xls)')
            
            # Check file size (max 5MB)
            if file.size > 5 * 1024 * 1024:
                raise forms.ValidationError('File size must be less than 5MB')
        
        return file 