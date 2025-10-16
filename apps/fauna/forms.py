"""
Forms for fauna app - Species management
"""

from django import forms
from .models import Species, BirdFamily


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
            'family': forms.Select(attrs={
                'class': 'form-select'
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

        # Check for exact duplicate names (case-insensitive)
        if name:
            existing_name = Species.objects.filter(name__iexact=name).exclude(pk=self.instance.pk)
            if existing_name.exists():
                raise forms.ValidationError(f"A species with the name '{name}' already exists.")

        if scientific_name:
            existing_scientific = Species.objects.filter(scientific_name__iexact=scientific_name).exclude(pk=self.instance.pk)
            if existing_scientific.exists():
                raise forms.ValidationError(f"A species with the scientific name '{scientific_name}' already exists.")

        # Check for potential duplicates using smart matching
        if name and scientific_name:
            from .services import SpeciesMatcher
            matcher = SpeciesMatcher()
            
            # Check if this species is too similar to existing ones
            existing_species = Species.objects.filter(is_archived=False).exclude(pk=self.instance.pk)
            for existing in existing_species:
                if matcher.is_likely_same_species(name, existing.name):
                    raise forms.ValidationError(
                        f"This species name '{name}' is very similar to existing species '{existing.name}' "
                        f"({existing.scientific_name}). Please check if this is a duplicate."
                    )

        return cleaned_data


class BirdFamilyForm(forms.ModelForm):
    """Form for creating and editing bird families"""

    class Meta:
        model = BirdFamily
        fields = ['name', 'display_name', 'category', 'description', 'scientific_name', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter family name (e.g., HERONS AND EGRETS)'
            }),
            'display_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter display name (e.g., Herons and Egrets)'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter description of this family'
            }),
            'scientific_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter scientific name (e.g., Ardeidae)'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        display_name = cleaned_data.get('display_name')

        # Check for duplicate names
        if name:
            existing = BirdFamily.objects.filter(name__iexact=name)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise forms.ValidationError(f"A family with the name '{name}' already exists.")

        if display_name:
            existing = BirdFamily.objects.filter(display_name__iexact=display_name)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise forms.ValidationError(f"A family with the display name '{display_name}' already exists.")

        return cleaned_data
