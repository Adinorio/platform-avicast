from django import forms
from django.core.validators import FileExtensionValidator
from .models import ImageUpload, BirdSpecies, ImageProcessingResult

class MultipleFileInput(forms.FileInput):
    """Custom file input widget that supports multiple file selection"""
    def render(self, name, value, attrs=None, renderer=None):
        if attrs is None:
            attrs = {}
        attrs['multiple'] = 'multiple'
        attrs['accept'] = 'image/*'
        attrs['class'] = attrs.get('class', '') + ' form-control'
        return super().render(name, value, attrs, renderer)

class ImageUploadForm(forms.ModelForm):
    """Form for image uploads with enhanced validation"""
    
    image_file = forms.ImageField(
        label='Select Images',
        help_text='Select multiple images for batch processing. Supported formats: JPG, JPEG, PNG, GIF. Maximum size: 50MB per image',
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif'])
        ],
        widget=MultipleFileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*',
            'data-max-size': '52428800'  # 50MB in bytes
        })
    )
    
    title = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Optional title for all images (e.g., "Morning Survey - Site A")'
        })
    )
    
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Optional description for all images (e.g., "Clear weather, low tide conditions")'
        })
    )
    
    class Meta:
        model = ImageUpload
        fields = ['image_file', 'title', 'description']
    
    def clean_image_file(self):
        """Validate image file size and content"""
        image_file = self.cleaned_data.get('image_file')
        
        if image_file:
            print(f"Validating image file: {image_file.name}, size: {image_file.size}")
            
            # Check file size (50MB limit)
            if image_file.size > 52428800:  # 50MB in bytes
                print(f"File too large: {image_file.size} bytes")
                raise forms.ValidationError("Image file size must be less than 50MB.")
            
            # Check if file is actually an image
            try:
                from PIL import Image
                print("PIL imported successfully")
                with Image.open(image_file) as img:
                    print(f"Image opened: {img.format}, size: {img.size}, mode: {img.mode}")
                    # Verify it's a valid image
                    img.verify()
                    print("Image verification passed")
            except Exception as e:
                print(f"Image validation failed: {str(e)}")
                raise forms.ValidationError(f"Invalid image file. Please upload a valid image. Error: {str(e)}")
            
            # Reset file pointer
            image_file.seek(0)
            print("Image file validation completed successfully")
        
        return image_file
    
    def clean_title(self):
        """Validate title"""
        title = self.cleaned_data.get('title')
        print(f"Validating title: '{title}'")
        if not title or not title.strip():
            print("Title is empty, using auto-generated title")
            return ""  # Allow empty titles for batch uploads
        print(f"Title validation passed: '{title.strip()}'")
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
