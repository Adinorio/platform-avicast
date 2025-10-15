"""
Forms for fauna app - Species management
"""

from django import forms
from .models import Species


class SpeciesForm(forms.ModelForm):
    """Form for creating and editing species"""

    class Meta:
        model = Species
        fields = ['name', 'scientific_name', 'family', 'iucn_status', 'description', 'image']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter common name (e.g., Chinese Egret)'
            }),
            'scientific_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter scientific name (e.g., Egretta eulophotes)'
            }),
            'family': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter family (e.g., Ardeidae)'
            }),
            'iucn_status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter description or additional notes'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control'
            })
        }

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        scientific_name = cleaned_data.get('scientific_name')

        # Check for duplicate names (case-insensitive)
        if name and Species.objects.filter(name__iexact=name).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(f"A species with the name '{name}' already exists.")

        if scientific_name and Species.objects.filter(scientific_name__iexact=scientific_name).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(f"A species with the scientific name '{scientific_name}' already exists.")

        return cleaned_data
