"""
GTD-based Image Processing Models
Following Getting Things Done methodology for workflow management
"""

import uuid
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils import timezone

User = get_user_model()


class EgretSpecies(models.TextChoices):
    """6 Focus egret species for identification"""
    CHINESE_EGRET = "CHINESE_EGRET", "Chinese Egret"
    GREAT_EGRET = "GREAT_EGRET", "Great Egret"
    INTERMEDIATE_EGRET = "INTERMEDIATE_EGRET", "Intermediate Egret"
    LITTLE_EGRET = "LITTLE_EGRET", "Little Egret"
    CATTLE_EGRET = "CATTLE_EGRET", "Cattle Egret"
    PACIFIC_REEF_HERON = "PACIFIC_REEF_HERON", "Pacific Reef Heron"


class ProcessingStatus(models.TextChoices):
    """GTD Workflow Status - Following Capture → Clarify → Organize → Reflect → Engage"""
    CAPTURED = "CAPTURED", "Captured"  # Image uploaded and waiting
    CLARIFIED = "CLARIFIED", "Clarified"  # AI processing completed, results ready
    ORGANIZED = "ORGANIZED", "Organized"  # Results categorized and ready for review
    REFLECTED = "REFLECTED", "Reflected"  # Human review completed, decision made
    ENGAGED = "ENGAGED", "Engaged"  # Results allocated to census data


class ReviewDecision(models.TextChoices):
    """Human decision during Reflect stage"""
    PENDING = "PENDING", "Pending Review"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"
    OVERRIDDEN = "OVERRIDDEN", "Overridden"


class ImageUpload(models.Model):
    """
    CAPTURE Stage: Collect all bird images for processing
    Following GTD inbox concept - capture everything first
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Basic capture information
    title = models.CharField(max_length=200, help_text="Brief description of the image")
    image_file = models.ImageField(
        upload_to="egret_images/%Y/%m/%d/",
        validators=[FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png"])],
        help_text="Upload bird image for egret species identification"
    )
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="uploaded_images")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    # Capture metadata
    file_size = models.PositiveIntegerField(help_text="File size in bytes")
    original_filename = models.CharField(max_length=255)

    # GTD Workflow status (maps to upload_status in database)
    upload_status = models.CharField(
        max_length=20,
        choices=ProcessingStatus.choices,
        default=ProcessingStatus.CAPTURED
    )

    # Processing information
    processing_started_at = models.DateTimeField(null=True, blank=True)
    processing_completed_at = models.DateTimeField(null=True, blank=True)

    # Location context (for later allocation)
    site_hint = models.CharField(
        max_length=200,
        blank=True,
        help_text="Optional site location hint for easier allocation"
    )

    class Meta:
        ordering = ["-uploaded_at"]
        verbose_name = "Image Upload"
        verbose_name_plural = "Image Uploads"

    def __str__(self):
        return f"{self.title} - {self.uploaded_by.employee_id}"

    def start_processing(self):
        """Mark as Clarify stage started"""
        self.upload_status = ProcessingStatus.CLARIFIED
        self.processing_started_at = timezone.now()
        self.save(update_fields=["upload_status", "processing_started_at"])

    def complete_processing(self):
        """Mark as Clarify stage completed"""
        self.upload_status = ProcessingStatus.ORGANIZED
        self.processing_completed_at = timezone.now()
        self.save(update_fields=["upload_status", "processing_completed_at"])

    def mark_reviewed(self, decision, reviewer, notes=""):
        """Mark as Reflect stage completed"""
        self.upload_status = ProcessingStatus.REFLECTED
        self.review_decision = decision
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.review_notes = notes
        self.save()

    def mark_allocated(self):
        """Mark as Engage stage completed"""
        self.upload_status = ProcessingStatus.ENGAGED
        self.save(update_fields=["upload_status"])

    @property
    def processing_duration(self):
        """Calculate processing duration in seconds"""
        if self.processing_started_at and self.processing_completed_at:
            return (self.processing_completed_at - self.processing_started_at).total_seconds()
        return None

    def get_upload_status_display(self):
        """Get the display value for upload_status field"""
        return dict(self._meta.get_field('upload_status').choices)[self.upload_status]


class ProcessingResult(models.Model):
    """
    CLARIFY & ORGANIZE Stage: AI processing results and human organization
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    image_upload = models.OneToOneField(ImageUpload, on_delete=models.CASCADE, related_name="processing_result")

    # AI detection results (Clarify stage)
    detected_species = models.CharField(
        max_length=50,
        choices=EgretSpecies.choices,
        help_text="AI-identified egret species"
    )
    confidence_score = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        help_text="AI confidence score (0.0 to 1.0)"
    )
    bounding_box = models.JSONField(
        help_text="Bounding box coordinates for detected bird"
    )
    total_detections = models.PositiveIntegerField(
        default=1,
        help_text="Number of birds detected in image"
    )

    # Processing metadata
    ai_model_used = models.CharField(
        max_length=100,
        default="YOLOv8_Egret_Specialist"
    )
    processing_device = models.CharField(max_length=20, default="cpu")
    inference_time = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        null=True,
        blank=True,
        help_text="AI inference time in seconds"
    )

    # Human review (Reflect stage)
    review_decision = models.CharField(
        max_length=20,
        choices=ReviewDecision.choices,
        default=ReviewDecision.PENDING
    )
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_images"
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)

    # Override capability (for manual corrections)
    is_overridden = models.BooleanField(default=False)
    overridden_species = models.CharField(
        max_length=50,
        choices=EgretSpecies.choices,
        null=True,
        blank=True
    )
    overridden_count = models.PositiveIntegerField(null=True, blank=True)
    override_reason = models.TextField(blank=True)

    # Allocation (Engage stage)
    allocated_to_site = models.ForeignKey(
        "locations.Site",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="allocated_images"
    )
    allocated_to_census = models.ForeignKey(
        "locations.CensusObservation",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="allocated_images"
    )
    allocated_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Processing Result"
        verbose_name_plural = "Processing Results"

    def __str__(self):
        return f"{self.image_upload.title} - {self.get_detected_species_display()}"

    def approve_result(self, reviewer, notes=""):
        """Approve AI result during Reflect stage"""
        self.review_decision = ReviewDecision.APPROVED
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.review_notes = notes
        self.save(update_fields=["review_decision", "reviewed_by", "reviewed_at", "review_notes"])

    def reject_result(self, reviewer, notes=""):
        """Reject AI result during Reflect stage"""
        self.review_decision = ReviewDecision.REJECTED
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.review_notes = notes
        self.save(update_fields=["review_decision", "reviewed_by", "reviewed_at", "review_notes"])

    def override_result(self, reviewer, new_species, new_count=None, reason=""):
        """Override AI result with manual classification"""
        self.is_overridden = True
        self.overridden_species = new_species
        self.overridden_count = new_count
        self.override_reason = reason
        self.review_decision = ReviewDecision.OVERRIDDEN
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.save()

    def allocate_to_census(self, site, census_observation):
        """Allocate approved result to census data (Engage stage)"""
        self.allocated_to_site = site
        self.allocated_to_census = census_observation
        self.allocated_at = timezone.now()
        self.save(update_fields=["allocated_to_site", "allocated_to_census", "allocated_at"])

    @property
    def final_species(self):
        """Get final species classification (AI or overridden)"""
        if self.is_overridden and self.overridden_species:
            return self.overridden_species
        return self.detected_species

    @property
    def final_count(self):
        """Get final count (AI or overridden)"""
        if self.is_overridden and self.overridden_count is not None:
            return self.overridden_count
        return self.total_detections

    @property
    def is_ready_for_allocation(self):
        """Check if result can be allocated to census"""
        return (
            self.review_decision in [ReviewDecision.APPROVED, ReviewDecision.OVERRIDDEN]
            and self.final_species is not None
        )

    @property
    def needs_review(self):
        """Check if result needs human review"""
        return self.review_decision == ReviewDecision.PENDING


class ProcessingBatch(models.Model):
    """
    ORGANIZE Stage: Batch processing for multiple images
    Following GTD project concept - group related work
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Batch information
    name = models.CharField(max_length=200, help_text="Batch name/description")
    description = models.TextField(blank=True)

    # Batch contents
    images = models.ManyToManyField(ImageUpload, related_name="processing_batches")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_batches")
    created_at = models.DateTimeField(auto_now_add=True)

    # Processing status
    total_images = models.PositiveIntegerField(default=0)
    processed_images = models.PositiveIntegerField(default=0)
    failed_images = models.PositiveIntegerField(default=0)

    # Batch status
    status = models.CharField(
        max_length=20,
        choices=[
            ("QUEUED", "Queued"),
            ("PROCESSING", "Processing"),
            ("COMPLETED", "Completed"),
            ("FAILED", "Failed"),
            ("CANCELLED", "Cancelled"),
        ],
        default="QUEUED"
    )

    # Timing
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Processing Batch"
        verbose_name_plural = "Processing Batches"

    def __str__(self):
        return f"{self.name} ({self.status})"

    def start_processing(self):
        """Mark batch as processing"""
        self.status = "PROCESSING"
        self.started_at = timezone.now()
        self.save(update_fields=["status", "started_at"])

    def complete_processing(self):
        """Mark batch as completed"""
        self.status = "COMPLETED"
        self.completed_at = timezone.now()
        self.save(update_fields=["status", "completed_at"])

    def mark_failed(self):
        """Mark batch as failed"""
        self.status = "FAILED"
        self.save(update_fields=["status"])

    def update_progress(self, processed, failed):
        """Update batch progress"""
        self.processed_images = processed
        self.failed_images = failed
        self.save(update_fields=["processed_images", "failed_images"])

    @property
    def progress_percentage(self):
        """Calculate processing progress"""
        if self.total_images == 0:
            return 0
        return ((self.processed_images + self.failed_images) / self.total_images) * 100
