from django import forms
from django.core.validators import FileExtensionValidator
from .models import ImageUpload, BirdSpecies, ImageProcessingResult

class ImageUploadForm(forms.ModelForm):
    """Form for image uploads with enhanced validation"""
    
    image_file = forms.ImageField(
        label='Select Image',
        help_text='Supported formats: JPG, JPEG, PNG, GIF. Maximum size: 50MB',
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif'])
        ],
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*',
            'data-max-size': '52428800'  # 50MB in bytes
        })
    )
    
    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter image title'
        })
    )
    
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Optional description of the image'
        })
    )
    
    class Meta:
        model = ImageUpload
        fields = ['image_file', 'title', 'description']
    
    def clean_image_file(self):
        """Validate image file size and content"""
        image_file = self.cleaned_data.get('image_file')
        
        if image_file:
            # Check file size (50MB limit)
            if image_file.size > 52428800:  # 50MB in bytes
                raise forms.ValidationError("Image file size must be less than 50MB.")
            
            # Check if file is actually an image
            try:
                from PIL import Image
                with Image.open(image_file) as img:
                    # Verify it's a valid image
                    img.verify()
            except Exception:
                raise forms.ValidationError("Invalid image file. Please upload a valid image.")
            
            # Reset file pointer
            image_file.seek(0)
        
        return image_file
    
    def clean_title(self):
        """Validate title"""
        title = self.cleaned_data.get('title')
        if not title.strip():
            raise forms.ValidationError("Title is required.")
        return title.strip()

class ImageProcessingForm(forms.ModelForm):
    """Form for image processing configuration"""
    
    class Meta:
        model = ImageProcessingResult
        fields = ['ai_model', 'model_confidence_threshold']
        widgets = {
            'ai_model': forms.Select(attrs={'class': 'form-control'}),
            'model_confidence_threshold': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0.1',
                'max': '1.0',
                'step': '0.05'
            })
        }

class ImageSearchForm(forms.Form):
    """Form for searching images"""
    
    search_query = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by title, description, or filename...'
        })
    )
    
    storage_tier = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All Storage Tiers'),
            ('HOT', 'Hot Storage'),
            ('WARM', 'Warm Storage'),
            ('COLD', 'Cold Storage'),
            ('ARCHIVE', 'Archive')
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    compression_status = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All Images'),
            ('compressed', 'Compressed Only'),
            ('uncompressed', 'Uncompressed Only')
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

class StorageCleanupForm(forms.Form):
    """Form for storage cleanup operations"""
    
    action = forms.ChoiceField(
        choices=[
            ('cleanup', 'Cleanup Old Files'),
            ('optimize', 'Optimize Uncompressed Images'),
            ('archive', 'Archive Old Files')
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    
    days = forms.IntegerField(
        min_value=1,
        max_value=3650,  # 10 years
        initial=30,
        help_text='Files older than this many days will be processed',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1',
            'max': '3650'
        })
    )
    
    dry_run = forms.BooleanField(
        required=False,
        initial=True,
        help_text='Show what would be done without actually doing it',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    force = forms.BooleanField(
        required=False,
        initial=False,
        help_text='Force operation even if not near storage limits',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
