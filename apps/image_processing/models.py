import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator
from django.utils import timezone

User = get_user_model()

class BirdSpecies(models.TextChoices):
    """Limited to 3 bird species as per requirements"""
    CHINESE_EGRET = 'CHINESE_EGRET', 'Chinese Egret'
    WHISKERED_TERN = 'WHISKERED_TERN', 'Whiskered Tern'
    GREAT_KNOT = 'GREAT_KNOT', 'Great Knot'

class AIModel(models.TextChoices):
    """Available AI models for bird detection"""
    YOLO_V5 = 'YOLO_V5', 'YOLOv5'
    YOLO_V8 = 'YOLO_V8', 'YOLOv8'
    YOLO_V9 = 'YOLO_V9', 'YOLOv9'

class ImageUpload(models.Model):
    """Model for handling image uploads"""
    
    class UploadStatus(models.TextChoices):
        UPLOADING = 'UPLOADING', 'Uploading'
        UPLOADED = 'UPLOADED', 'Uploaded'
        PROCESSING = 'PROCESSING', 'Processing'
        PROCESSED = 'PROCESSED', 'Processed'
        FAILED = 'FAILED', 'Failed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # File handling with improved storage
    image_file = models.ImageField(
        upload_to='bird_images/%Y/%m/%d/',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif'])]
    )
    file_size = models.BigIntegerField(help_text="File size in bytes")
    file_type = models.CharField(max_length=20)

    # Enhanced deduplication and optimization fields
    file_hash = models.CharField(max_length=64, blank=True, help_text="SHA256 hash of file content")
    original_filename = models.CharField(max_length=255)
    is_compressed = models.BooleanField(default=False, help_text="Whether image has been optimized")
    compressed_size = models.BigIntegerField(null=True, blank=True, help_text="Size after compression")
    
    # Archive storage field
    archive_path = models.CharField(max_length=500, null=True, blank=True, help_text="Path to archived file")

    # Storage tier management
    storage_tier = models.CharField(
        max_length=20,
        choices=[
            ('HOT', 'Hot Storage'),
            ('WARM', 'Warm Storage'),
            ('COLD', 'Cold Storage'),
            ('ARCHIVE', 'Archive')
        ],
        default='HOT',
        help_text="Storage tier for lifecycle management"
    )
    last_accessed = models.DateTimeField(auto_now=True, help_text="Last time file was accessed")
    retention_days = models.IntegerField(default=365, help_text="Days to retain file")
    
    # Upload information
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='image_uploads')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    upload_status = models.CharField(max_length=20, choices=UploadStatus.choices, default=UploadStatus.UPLOADING)
    
    # Processing information
    processing_started_at = models.DateTimeField(null=True, blank=True)
    processing_completed_at = models.DateTimeField(null=True, blank=True)
    processing_duration = models.DurationField(null=True, blank=True)
    
    # Metadata
    image_width = models.IntegerField(null=True, blank=True)
    image_height = models.IntegerField(null=True, blank=True)
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Image Upload'
        verbose_name_plural = 'Image Uploads'

    def __str__(self):
        return f"{self.title} - {self.uploaded_by.employee_id}"

    def start_processing(self):
        """Mark image as processing"""
        self.upload_status = self.UploadStatus.PROCESSING
        self.processing_started_at = timezone.now()
        self.save(update_fields=['upload_status', 'processing_started_at'])

    def complete_processing(self):
        """Mark image as processed"""
        self.upload_status = self.UploadStatus.PROCESSED
        self.processing_completed_at = timezone.now()
        if self.processing_started_at:
            self.processing_duration = self.processing_completed_at - self.processing_started_at
        self.save(update_fields=['upload_status', 'processing_completed_at', 'processing_duration'])

    def mark_failed(self):
        """Mark image processing as failed"""
        self.upload_status = self.UploadStatus.FAILED
        self.save(update_fields=['upload_status'])

    def calculate_file_hash(self):
        """Calculate SHA256 hash of the image file"""
        import hashlib
        if self.image_file:
            with self.image_file.open('rb') as f:
                file_content = f.read()
                return hashlib.sha256(file_content).hexdigest()
        return None

    def get_storage_info(self):
        """Get storage information for this image"""
        return {
            'id': str(self.id),
            'title': self.title,
            'file_size': self.file_size,
            'compressed_size': self.compressed_size,
            'storage_tier': self.storage_tier,
            'is_compressed': self.is_compressed,
            'uploaded_at': self.uploaded_at,
            'last_accessed': self.last_accessed
        }

class ImageProcessingResult(models.Model):
    """Model for storing image processing results"""
    
    class ProcessingStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PROCESSING = 'PROCESSING', 'Processing'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'

    class ReviewStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending Review'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        OVERRIDDEN = 'OVERRIDDEN', 'Overridden'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    image_upload = models.OneToOneField(ImageUpload, on_delete=models.CASCADE, related_name='processing_result')
    
    # Processing results
    detected_species = models.CharField(max_length=50, choices=BirdSpecies.choices, null=True, blank=True)
    confidence_score = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    bounding_box = models.JSONField(default=dict, blank=True)  # Store coordinates
    total_detections = models.IntegerField(default=0)  # Number of birds detected
    processing_status = models.CharField(max_length=20, choices=ProcessingStatus.choices, default=ProcessingStatus.PENDING)

    # AI Model Configuration
    ai_model = models.CharField(max_length=20, choices=AIModel.choices, default=AIModel.YOLO_V8)
    model_version = models.CharField(max_length=50, blank=True)  # Specific model version
    processing_device = models.CharField(max_length=20, default='cpu')  # cpu or cuda

    # Processing metrics
    inference_time = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)  # in seconds
    model_confidence_threshold = models.DecimalField(max_digits=3, decimal_places=2, default=0.25)
    
    # Review and approval
    review_status = models.CharField(max_length=20, choices=ReviewStatus.choices, default=ReviewStatus.PENDING)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='results_reviewed')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)
    
    # Override information (when admin overrides AI result)
    is_overridden = models.BooleanField(default=False)
    overridden_species = models.CharField(max_length=50, choices=BirdSpecies.choices, null=True, blank=True)
    overridden_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='results_overridden')
    overridden_at = models.DateTimeField(null=True, blank=True)
    override_reason = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Image Processing Result'
        verbose_name_plural = 'Image Processing Results'

    def __str__(self):
        return f"{self.image_upload.title} - {self.detected_species or 'Unknown'}"

    def approve_result(self, reviewed_by_user, notes=""):
        """Approve the processing result"""
        self.review_status = self.ReviewStatus.APPROVED
        self.reviewed_by = reviewed_by_user
        self.reviewed_at = timezone.now()
        self.review_notes = notes
        self.save(update_fields=['review_status', 'reviewed_by', 'reviewed_at', 'review_notes'])

    def reject_result(self, reviewed_by_user, notes=""):
        """Reject the processing result"""
        self.review_status = self.ReviewStatus.REJECTED
        self.reviewed_by = reviewed_by_user
        self.reviewed_at = timezone.now()
        self.review_notes = notes
        self.save(update_fields=['review_status', 'reviewed_by', 'reviewed_at', 'review_notes'])

    def override_result(self, overridden_by_user, new_species, reason=""):
        """Override the AI result with manual classification"""
        self.is_overridden = True
        self.overridden_species = new_species
        self.overridden_by = overridden_by_user
        self.overridden_at = timezone.now()
        self.override_reason = reason
        self.review_status = self.ReviewStatus.OVERRIDDEN
        self.save(update_fields=['is_overridden', 'overridden_species', 'overridden_by', 
                                'overridden_at', 'override_reason', 'review_status'])

    @property
    def final_species(self):
        """Get the final species classification (AI or overridden)"""
        if self.is_overridden and self.overridden_species:
            return self.overridden_species
        return self.detected_species

    @property
    def is_reviewed(self):
        """Check if result has been reviewed"""
        return self.review_status != self.ReviewStatus.PENDING

    @property
    def can_be_allocated(self):
        """Check if result can be allocated to census data"""
        return (self.review_status in [self.ReviewStatus.APPROVED, self.ReviewStatus.OVERRIDDEN] 
                and self.final_species is not None)

class ProcessingBatch(models.Model):
    """Model for handling batch processing of multiple images"""
    
    class BatchStatus(models.TextChoices):
        QUEUED = 'QUEUED', 'Queued'
        PROCESSING = 'PROCESSING', 'Processing'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Batch information
    total_images = models.IntegerField(default=0)
    processed_images = models.IntegerField(default=0)
    failed_images = models.IntegerField(default=0)
    
    # Status and timing
    status = models.CharField(max_length=20, choices=BatchStatus.choices, default=BatchStatus.QUEUED)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='processing_batches')
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Images in this batch
    images = models.ManyToManyField(ImageUpload, related_name='processing_batches')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Processing Batch'
        verbose_name_plural = 'Processing Batches'

    def __str__(self):
        return f"{self.name} - {self.status}"

    def start_processing(self):
        """Start the batch processing"""
        self.status = self.BatchStatus.PROCESSING
        self.started_at = timezone.now()
        self.save(update_fields=['status', 'started_at'])

    def complete_processing(self):
        """Mark batch as completed"""
        self.status = self.BatchStatus.COMPLETED
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at'])

    def update_progress(self, processed_count, failed_count):
        """Update processing progress"""
        self.processed_images = processed_count
        self.failed_images = failed_count
        self.save(update_fields=['processed_images', 'failed_images'])

    @property
    def progress_percentage(self):
        """Calculate processing progress percentage"""
        if self.total_images == 0:
            return 0
        return (self.processed_images + self.failed_images) / self.total_images * 100
