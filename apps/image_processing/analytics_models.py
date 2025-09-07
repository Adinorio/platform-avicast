"""
Model Performance Analytics Models
Advanced MLOps metrics tracking for YOLO model comparison and thesis analysis
"""

import uuid
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class ModelEvaluationRun(models.Model):
    """Represents a single evaluation run with specific filters and parameters"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Run metadata
    name = models.CharField(max_length=200, help_text="Human-readable name for this evaluation run")
    description = models.TextField(
        blank=True, help_text="Description of what this evaluation measures"
    )
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="evaluation_runs")
    created_at = models.DateTimeField(auto_now_add=True)

    # Evaluation parameters
    iou_threshold = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.50,
        help_text="IoU threshold for TP/FP classification",
    )
    confidence_threshold = models.DecimalField(
        max_digits=3, decimal_places=2, default=0.25, help_text="Minimum confidence for detections"
    )

    # Filters applied
    models_evaluated = models.JSONField(
        default=list, help_text="List of model variants included in evaluation"
    )
    date_range_start = models.DateTimeField(
        null=True, blank=True, help_text="Start date for filtered data"
    )
    date_range_end = models.DateTimeField(
        null=True, blank=True, help_text="End date for filtered data"
    )
    species_filter = models.JSONField(default=list, help_text="Species included in evaluation")

    # Overall metrics
    total_images_evaluated = models.IntegerField(default=0)
    total_ground_truth_objects = models.IntegerField(default=0)
    total_predicted_objects = models.IntegerField(default=0)

    # Aggregated performance metrics
    overall_precision = models.DecimalField(max_digits=6, decimal_places=4, null=True, blank=True)
    overall_recall = models.DecimalField(max_digits=6, decimal_places=4, null=True, blank=True)
    overall_f1_score = models.DecimalField(max_digits=6, decimal_places=4, null=True, blank=True)
    overall_map_50 = models.DecimalField(
        max_digits=6, decimal_places=4, null=True, blank=True, help_text="mAP@0.5"
    )
    overall_map_50_95 = models.DecimalField(
        max_digits=6, decimal_places=4, null=True, blank=True, help_text="mAP@0.5:0.95"
    )

    # Processing status
    status = models.CharField(
        max_length=20,
        choices=[
            ("PENDING", "Pending"),
            ("PROCESSING", "Processing"),
            ("COMPLETED", "Completed"),
            ("FAILED", "Failed"),
        ],
        default="PENDING",
    )
    error_message = models.TextField(blank=True, help_text="Error details if evaluation failed")
    processing_duration = models.DurationField(
        null=True, blank=True, help_text="Time taken to complete evaluation"
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Model Evaluation Run"
        verbose_name_plural = "Model Evaluation Runs"

    def __str__(self):
        return f"{self.name} - {self.created_at.strftime('%Y-%m-%d')}"


class ModelPerformanceMetrics(models.Model):
    """Performance metrics for a specific model in an evaluation run"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    evaluation_run = models.ForeignKey(
        ModelEvaluationRun, on_delete=models.CASCADE, related_name="model_metrics"
    )

    # Model identification
    model_name = models.CharField(max_length=50, help_text="Model variant name (e.g., yolov8l)")
    model_version = models.CharField(
        max_length=100, blank=True, help_text="Specific model version or checkpoint"
    )

    # Dataset metrics
    images_processed = models.IntegerField(default=0)
    ground_truth_objects = models.IntegerField(
        default=0, help_text="Total GT objects for this model's images"
    )
    predicted_objects = models.IntegerField(
        default=0, help_text="Total predictions made by this model"
    )

    # Confusion matrix components
    true_positives = models.IntegerField(default=0)
    false_positives = models.IntegerField(default=0)
    false_negatives = models.IntegerField(default=0)

    # Core performance metrics
    precision = models.DecimalField(max_digits=6, decimal_places=4, null=True, blank=True)
    recall = models.DecimalField(max_digits=6, decimal_places=4, null=True, blank=True)
    f1_score = models.DecimalField(max_digits=6, decimal_places=4, null=True, blank=True)

    # mAP metrics
    map_50 = models.DecimalField(
        max_digits=6, decimal_places=4, null=True, blank=True, help_text="mAP@0.5"
    )
    map_50_95 = models.DecimalField(
        max_digits=6, decimal_places=4, null=True, blank=True, help_text="mAP@0.5:0.95"
    )

    # Performance characteristics
    avg_inference_time_ms = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )
    avg_confidence_score = models.DecimalField(
        max_digits=5, decimal_places=4, null=True, blank=True
    )

    # Model parameters and size
    model_parameters_millions = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )
    model_size_mb = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-f1_score", "-map_50"]
        unique_together = ["evaluation_run", "model_name"]
        verbose_name = "Model Performance Metrics"
        verbose_name_plural = "Model Performance Metrics"

    def __str__(self):
        return f"{self.model_name} - F1: {self.f1_score or 'N/A'}"

    def calculate_metrics(self):
        """Calculate precision, recall, and F1 score from confusion matrix"""
        tp, fp, fn = self.true_positives, self.false_positives, self.false_negatives

        # Precision: TP / (TP + FP)
        if tp + fp > 0:
            self.precision = Decimal(tp) / Decimal(tp + fp)
        else:
            self.precision = Decimal("0.0000")

        # Recall: TP / (TP + FN)
        if tp + fn > 0:
            self.recall = Decimal(tp) / Decimal(tp + fn)
        else:
            self.recall = Decimal("0.0000")

        # F1 Score: 2 * (Precision * Recall) / (Precision + Recall)
        if self.precision + self.recall > 0:
            self.f1_score = 2 * (self.precision * self.recall) / (self.precision + self.recall)
        else:
            self.f1_score = Decimal("0.0000")


class SpeciesPerformanceMetrics(models.Model):
    """Per-species performance metrics for detailed analysis"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    model_metrics = models.ForeignKey(
        ModelPerformanceMetrics, on_delete=models.CASCADE, related_name="species_metrics"
    )

    # Species identification
    species_name = models.CharField(max_length=100, help_text="Species name (e.g., Chinese Egret)")
    species_class_id = models.IntegerField(help_text="YOLO class ID for this species")

    # Species-specific confusion matrix
    true_positives = models.IntegerField(default=0)
    false_positives = models.IntegerField(default=0)
    false_negatives = models.IntegerField(default=0)

    # Species-specific metrics
    precision = models.DecimalField(max_digits=6, decimal_places=4, null=True, blank=True)
    recall = models.DecimalField(max_digits=6, decimal_places=4, null=True, blank=True)
    f1_score = models.DecimalField(max_digits=6, decimal_places=4, null=True, blank=True)
    average_precision = models.DecimalField(
        max_digits=6, decimal_places=4, null=True, blank=True, help_text="AP@0.5 for this species"
    )

    # Species-specific characteristics
    avg_confidence = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    ground_truth_count = models.IntegerField(
        default=0, help_text="Total GT instances of this species"
    )
    detected_count = models.IntegerField(default=0, help_text="Total detections for this species")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["species_name"]
        unique_together = ["model_metrics", "species_name"]
        verbose_name = "Species Performance Metrics"
        verbose_name_plural = "Species Performance Metrics"

    def __str__(self):
        return f"{self.species_name} - AP: {self.average_precision or 'N/A'}"


class ConfusionMatrixEntry(models.Model):
    """Individual entries in the confusion matrix for detailed error analysis"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    evaluation_run = models.ForeignKey(
        ModelEvaluationRun, on_delete=models.CASCADE, related_name="confusion_matrix"
    )

    # Matrix coordinates
    actual_species = models.CharField(max_length=100, help_text="Ground truth species")
    predicted_species = models.CharField(
        max_length=100, help_text="Predicted species (or 'background' for FN)"
    )

    # Count and percentage
    count = models.IntegerField(
        default=0, help_text="Number of instances with this actual/predicted combination"
    )
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Percentage of total predictions",
    )

    # Additional context
    avg_confidence = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Average confidence for this combination",
    )
    avg_iou = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Average IoU for this combination",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-count"]
        unique_together = ["evaluation_run", "actual_species", "predicted_species"]
        verbose_name = "Confusion Matrix Entry"
        verbose_name_plural = "Confusion Matrix Entries"

    def __str__(self):
        return f"{self.actual_species} → {self.predicted_species}: {self.count}"


class ImageEvaluationResult(models.Model):
    """Detailed evaluation results for individual images"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    evaluation_run = models.ForeignKey(
        ModelEvaluationRun, on_delete=models.CASCADE, related_name="image_results"
    )

    # Image reference
    image_upload = models.ForeignKey("ImageUpload", on_delete=models.CASCADE, null=True, blank=True)
    image_filename = models.CharField(max_length=255, help_text="Image filename for reference")
    model_used = models.CharField(max_length=50, help_text="Model variant used for this image")

    # Ground truth data
    ground_truth_boxes = models.JSONField(
        default=list, help_text="List of ground truth bounding boxes"
    )
    ground_truth_count = models.IntegerField(default=0)

    # Prediction data
    predicted_boxes = models.JSONField(default=list, help_text="List of predicted bounding boxes")
    predicted_count = models.IntegerField(default=0)

    # Matching results
    matches = models.JSONField(
        default=list, help_text="List of matched prediction-GT pairs with IoU scores"
    )
    unmatched_predictions = models.JSONField(default=list, help_text="FP predictions")
    unmatched_ground_truth = models.JSONField(default=list, help_text="FN ground truth")

    # Image-level metrics
    image_precision = models.DecimalField(max_digits=6, decimal_places=4, null=True, blank=True)
    image_recall = models.DecimalField(max_digits=6, decimal_places=4, null=True, blank=True)
    image_f1 = models.DecimalField(max_digits=6, decimal_places=4, null=True, blank=True)
    avg_iou = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Average IoU of matched boxes",
    )

    # Processing metadata
    inference_time_ms = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Image Evaluation Result"
        verbose_name_plural = "Image Evaluation Results"

    def __str__(self):
        return f"{self.image_filename} - {self.model_used}"
