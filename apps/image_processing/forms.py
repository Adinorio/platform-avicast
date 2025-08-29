from django import forms
from django.core.validators import FileExtensionValidator
from .models import ImageUpload, BirdSpecies, ImageProcessingResult, ProcessingBatch, AIModel
from .config import IMAGE_CONFIG
from .utils import validate_file_extension

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
        help_text=f'Select multiple images for batch processing. Supported formats: {", ".join(IMAGE_CONFIG["ALLOWED_EXTENSIONS"]).upper()}. Maximum size: {IMAGE_CONFIG["MAX_FILE_SIZE_MB"]}MB per image',
        validators=[
            FileExtensionValidator(allowed_extensions=IMAGE_CONFIG['ALLOWED_EXTENSIONS'])
        ],
        widget=MultipleFileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*',
            'data-max-size': str(IMAGE_CONFIG['MAX_FILE_SIZE_BYTES'])
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
            
            # Check file size
            if image_file.size > IMAGE_CONFIG['MAX_FILE_SIZE_BYTES']:
                print(f"File too large: {image_file.size} bytes")
                raise forms.ValidationError(f"Image file size must be less than {IMAGE_CONFIG['MAX_FILE_SIZE_MB']}MB.")
            
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

class BatchProcessingForm(forms.ModelForm):
    """Form for batch processing images"""
    
    class Meta:
        model = ProcessingBatch
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter batch name...'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe the batch (optional)...'
            })
        }

class ModelSelectionForm(forms.Form):
    """Form for selecting AI model version"""
    
    ai_model = forms.ChoiceField(
        choices=AIModel.choices,
        initial=AIModel.CHINESE_EGRET_V1,  # Default to the best performing model
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'ai-model-select'
        }),
        help_text="🏆 Chinese Egret Specialist recommended for optimal performance (99.46% accuracy)"
    )
    
    confidence_threshold = forms.FloatField(
        min_value=0.1,
        max_value=1.0,
        initial=0.5,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': 0.05,
            'min': 0.1,
            'max': 1.0
        }),
        help_text="Detection confidence threshold (0.1 - 1.0)"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add descriptions for each model
        model_descriptions = {
            AIModel.YOLO_V5: 'Fast and lightweight, good for real-time processing',
            AIModel.YOLO_V8: 'Balanced performance and accuracy',
            AIModel.YOLO_V9: 'Latest and most advanced',
            AIModel.CHINESE_EGRET_V1: '🏆 ULTRA HIGH PERFORMANCE - 99.46% accuracy, specially trained for Chinese Egrets (RECOMMENDED)'
        }
        
        # Update choices with descriptions
        self.fields['ai_model'].choices = [
            (choice[0], f"{choice[1]} - {model_descriptions.get(choice[0], '')}")
            for choice in AIModel.choices
        ]

class ImageProcessingForm(forms.Form):
    """Form for processing individual images"""
    
    ai_model = forms.ChoiceField(
        choices=AIModel.choices,
        initial=AIModel.YOLO_V8,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        help_text="Select YOLO version for detection"
    )
    
    confidence_threshold = forms.FloatField(
        min_value=0.1,
        max_value=1.0,
        initial=0.5,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': 0.05
        }),
        help_text="Detection confidence threshold"
    )
    
    force_reprocess = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        help_text="Force reprocessing even if already processed"
    )

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
