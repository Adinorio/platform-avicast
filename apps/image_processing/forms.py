"""
GTD-based Image Processing Forms
Following Getting Things Done methodology for workflow management
"""

from django import forms
from .models import ImageUpload, ProcessingResult, EgretSpecies


class ImageUploadForm(forms.ModelForm):
    """
    CAPTURE Stage: Form for uploading bird images
    """
    class Meta:
        model = ImageUpload
        fields = ["title", "image_file", "site_hint"]
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Brief description of the image"
            }),
            "image_file": forms.FileInput(attrs={
                "class": "form-control",
                "accept": "image/jpeg,image/jpg,image/png"
            }),
            "site_hint": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Optional: Site location for easier allocation"
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add help text for better GTD guidance
        self.fields["title"].help_text = "Use descriptive titles to help with organization later"
        self.fields["site_hint"].help_text = "This helps with the Engage stage when allocating to census data"


class ProcessingResultReviewForm(forms.ModelForm):
    """
    REFLECT Stage: Form for reviewing AI results
    """
    decision_notes = forms.CharField(
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 3,
            "placeholder": "Optional notes about your decision"
        }),
        required=False,
        help_text="Add notes to explain your decision or provide context"
    )

    class Meta:
        model = ProcessingResult
        fields = ["review_decision", "review_notes"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove the review_notes field since we have decision_notes
        if "review_notes" in self.fields:
            del self.fields["review_notes"]

        # Add custom choice labels for better UX
        self.fields["review_decision"].choices = [
            ("PENDING", "⏳ Still Reviewing"),
            ("APPROVED", "✅ Approve AI Result"),
            ("REJECTED", "❌ Reject - Wrong Species"),
            ("OVERRIDDEN", "🔄 Override - Manual Correction"),
        ]


class ProcessingResultOverrideForm(forms.Form):
    """
    REFLECT Stage: Form for overriding AI results
    """
    new_species = forms.ChoiceField(
        choices=EgretSpecies.choices,
        widget=forms.Select(attrs={"class": "form-control"}),
        help_text="Select the correct egret species"
    )

    new_count = forms.IntegerField(
        min_value=1,
        max_value=50,
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "placeholder": "Number of birds"
        }),
        help_text="How many birds do you see in the image?"
    )

    override_reason = forms.CharField(
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 3,
            "placeholder": "Why are you overriding the AI result?"
        }),
        help_text="Explain your reasoning for the override"
    )


class CensusAllocationForm(forms.Form):
    """
    ENGAGE Stage: Form for allocating results to census data
    """
    target_site = forms.ModelChoiceField(
        queryset=None,  # Will be populated in view
        widget=forms.Select(attrs={"class": "form-control"}),
        empty_label="Select a site for allocation",
        help_text="Choose the site where these birds were observed"
    )

    observation_date = forms.DateField(
        widget=forms.DateInput(attrs={
            "class": "form-control",
            "type": "date"
        }),
        help_text="When were these birds observed?"
    )


    def __init__(self, *args, **kwargs):
        sites_queryset = kwargs.pop("sites_queryset", None)
        super().__init__(*args, **kwargs)
        if sites_queryset:
            self.fields["target_site"].queryset = sites_queryset

