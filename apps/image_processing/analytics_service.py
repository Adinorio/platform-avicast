"""
Model Performance Analytics Service
Advanced MLOps metrics calculation for YOLO model comparison
"""
import os
import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from decimal import Decimal
from datetime import datetime, timedelta
from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from .models import ImageUpload, ImageProcessingResult
from .analytics_models import (
    ModelEvaluationRun, ModelPerformanceMetrics, 
    SpeciesPerformanceMetrics, ConfusionMatrixEntry, ImageEvaluationResult
)

class ModelAnalyticsService:
    """Service for calculating comprehensive model performance analytics"""
    
    def __init__(self):
        self.dataset_path = Path(settings.BASE_DIR) / 'dataset'
        self.species_mapping = {
            0: 'Chinese Egret',
            1: 'Whiskered Tern', 
            2: 'Great Knot'
        }
    
    def calculate_iou(self, box1: List[float], box2: List[float]) -> float:
        """
        Calculate Intersection over Union (IoU) between two bounding boxes
        
        Args:
            box1, box2: [x, y, width, height] in normalized coordinates (0-1)
        
        Returns:
            IoU score between 0 and 1
        """
        # Convert from [x, y, w, h] to [x1, y1, x2, y2]
        x1_1, y1_1 = box1[0] - box1[2]/2, box1[1] - box1[3]/2
        x2_1, y2_1 = box1[0] + box1[2]/2, box1[1] + box1[3]/2
        
        x1_2, y1_2 = box2[0] - box2[2]/2, box2[1] - box2[3]/2
        x2_2, y2_2 = box2[0] + box2[2]/2, box2[1] + box2[3]/2
        
        # Calculate intersection
        xi1 = max(x1_1, x1_2)
        yi1 = max(y1_1, y1_2)
        xi2 = min(x2_1, x2_2)
        yi2 = min(y2_1, y2_2)
        
        if xi2 <= xi1 or yi2 <= yi1:
            return 0.0
        
        intersection = (xi2 - xi1) * (yi2 - yi1)
        
        # Calculate union
        area1 = box1[2] * box1[3]
        area2 = box2[2] * box2[3]
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0.0
    
    def load_ground_truth_annotations(self, image_filename: str) -> List[Dict]:
        """
        Load ground truth annotations from YOLO format files
        
        Args:
            image_filename: Name of the image file
            
        Returns:
            List of ground truth boxes with species information
        """
        # Find corresponding label file
        label_filename = image_filename.replace('.jpg', '.txt').replace('.png', '.txt')
        
        # Search in dataset directories
        for split in ['train', 'val', 'test']:
            label_path = self.dataset_path / split / 'labels' / label_filename
            if label_path.exists():
                ground_truth = []
                with open(label_path, 'r') as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) >= 5:
                            class_id = int(parts[0])
                            x, y, w, h = map(float, parts[1:5])
                            ground_truth.append({
                                'class_id': class_id,
                                'species': self.species_mapping.get(class_id, f'Unknown_{class_id}'),
                                'bbox': [x, y, w, h],
                                'confidence': 1.0  # Ground truth has perfect confidence
                            })
                return ground_truth
        
        return []  # No ground truth found
    
    def extract_predictions_from_result(self, processing_result: ImageProcessingResult) -> List[Dict]:
        """
        Extract predictions from ImageProcessingResult in standardized format
        
        Args:
            processing_result: The AI processing result from database
            
        Returns:
            List of predictions with normalized bounding boxes
        """
        predictions = []
        
        if not processing_result.bounding_box:
            return predictions
        
        # Get all detections from the result
        all_detections = processing_result.bounding_box.get('all_detections', [])
        ai_dimensions = processing_result.bounding_box.get('ai_dimensions', [640, 640])
        
        for detection in all_detections:
            bbox_data = detection.get('bounding_box', {})
            if bbox_data:
                # Convert from pixel coordinates to normalized coordinates
                x1 = bbox_data.get('x1', bbox_data.get('x', 0))
                y1 = bbox_data.get('y1', bbox_data.get('y', 0))
                x2 = bbox_data.get('x2', x1 + bbox_data.get('width', 0))
                y2 = bbox_data.get('y2', y1 + bbox_data.get('height', 0))
                
                # Normalize coordinates
                img_width, img_height = ai_dimensions
                x_center = ((x1 + x2) / 2) / img_width
                y_center = ((y1 + y2) / 2) / img_height
                width = (x2 - x1) / img_width
                height = (y2 - y1) / img_height
                
                # Map species name to class ID
                species_name = detection.get('species', 'Unknown')
                class_id = self._get_class_id_from_species(species_name)
                
                predictions.append({
                    'class_id': class_id,
                    'species': species_name,
                    'bbox': [x_center, y_center, width, height],
                    'confidence': float(detection.get('confidence', 0.0))
                })
        
        return predictions
    
    def _get_class_id_from_species(self, species_name: str) -> int:
        """Map species name to class ID"""
        name_to_id = {v: k for k, v in self.species_mapping.items()}
        return name_to_id.get(species_name, -1)
    
    def match_predictions_to_ground_truth(
        self, 
        predictions: List[Dict], 
        ground_truth: List[Dict], 
        iou_threshold: float = 0.5
    ) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """
        Match predictions to ground truth boxes using IoU threshold
        
        Args:
            predictions: List of predicted boxes
            ground_truth: List of ground truth boxes
            iou_threshold: Minimum IoU for a match
            
        Returns:
            Tuple of (matches, unmatched_predictions, unmatched_ground_truth)
        """
        matches = []
        unmatched_predictions = predictions.copy()
        unmatched_ground_truth = ground_truth.copy()
        
        # Calculate IoU matrix
        for i, pred in enumerate(predictions):
            best_iou = 0.0
            best_gt_idx = -1
            
            for j, gt in enumerate(ground_truth):
                iou = self.calculate_iou(pred['bbox'], gt['bbox'])
                
                if iou > best_iou and iou >= iou_threshold:
                    # Check if species match for True Positive
                    if pred['class_id'] == gt['class_id']:
                        best_iou = iou
                        best_gt_idx = j
            
            # If we found a match
            if best_gt_idx >= 0:
                match = {
                    'prediction': pred,
                    'ground_truth': ground_truth[best_gt_idx],
                    'iou': best_iou,
                    'is_true_positive': True
                }
                matches.append(match)
                
                # Remove from unmatched lists
                if pred in unmatched_predictions:
                    unmatched_predictions.remove(pred)
                if ground_truth[best_gt_idx] in unmatched_ground_truth:
                    unmatched_ground_truth.remove(ground_truth[best_gt_idx])
        
        return matches, unmatched_predictions, unmatched_ground_truth
    
    def calculate_average_precision(self, 
                                  predictions: List[Dict], 
                                  ground_truth: List[Dict], 
                                  class_id: int,
                                  iou_threshold: float = 0.5) -> float:
        """
        Calculate Average Precision (AP) for a specific class
        
        Args:
            predictions: All predictions for images
            ground_truth: All ground truth for images  
            class_id: Class to calculate AP for
            iou_threshold: IoU threshold for positive detection
            
        Returns:
            Average Precision score
        """
        # Filter predictions and GT for this class
        class_predictions = [p for p in predictions if p['class_id'] == class_id]
        class_ground_truth = [gt for gt in ground_truth if gt['class_id'] == class_id]
        
        if not class_ground_truth:
            return 0.0
        
        # Sort predictions by confidence (descending)
        class_predictions.sort(key=lambda x: x['confidence'], reverse=True)
        
        # Calculate precision and recall at each threshold
        tp = 0
        fp = 0
        precisions = []
        recalls = []
        
        gt_matched = [False] * len(class_ground_truth)
        
        for pred in class_predictions:
            # Find best matching ground truth
            best_iou = 0.0
            best_gt_idx = -1
            
            for i, gt in enumerate(class_ground_truth):
                if gt_matched[i]:
                    continue
                    
                iou = self.calculate_iou(pred['bbox'], gt['bbox'])
                if iou > best_iou:
                    best_iou = iou
                    best_gt_idx = i
            
            # Determine if this is TP or FP
            if best_iou >= iou_threshold and best_gt_idx >= 0:
                tp += 1
                gt_matched[best_gt_idx] = True
            else:
                fp += 1
            
            # Calculate precision and recall
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / len(class_ground_truth)
            
            precisions.append(precision)
            recalls.append(recall)
        
        # Calculate AP using interpolated precision
        if not precisions:
            return 0.0
        
        # Add points at recall 0 and 1
        precisions = [precisions[0]] + precisions + [0]
        recalls = [0] + recalls + [1]
        
        # Interpolate precision
        for i in range(len(precisions) - 2, -1, -1):
            precisions[i] = max(precisions[i], precisions[i + 1])
        
        # Calculate area under curve
        ap = 0.0
        for i in range(1, len(recalls)):
            ap += (recalls[i] - recalls[i - 1]) * precisions[i]
        
        return ap
    
    def run_evaluation(self, 
                      evaluation_run: ModelEvaluationRun,
                      model_filters: List[str] = None,
                      date_range: Tuple[datetime, datetime] = None,
                      species_filter: List[str] = None) -> ModelEvaluationRun:
        """
        Run comprehensive model evaluation
        
        Args:
            evaluation_run: The evaluation run object to populate
            model_filters: List of model names to include
            date_range: (start_date, end_date) tuple
            species_filter: List of species to include
            
        Returns:
            Updated evaluation run with results
        """
        try:
            evaluation_run.status = 'PROCESSING'
            evaluation_run.save()
            
            start_time = timezone.now()
            
            # Get filtered processing results
            results_query = ImageProcessingResult.objects.filter(
                processing_status=ImageProcessingResult.ProcessingStatus.COMPLETED,
                review_status__in=[
                    ImageProcessingResult.ReviewStatus.APPROVED,
                    ImageProcessingResult.ReviewStatus.OVERRIDDEN
                ]
            )
            
            # Apply filters
            if model_filters:
                results_query = results_query.filter(ai_model__in=model_filters)
            
            if date_range:
                start_date, end_date = date_range
                results_query = results_query.filter(
                    created_at__gte=start_date,
                    created_at__lte=end_date
                )
            
            processing_results = results_query.select_related('image_upload').all()
            
            # Group results by model
            results_by_model = {}
            for result in processing_results:
                model_name = result.ai_model
                if model_name not in results_by_model:
                    results_by_model[model_name] = []
                results_by_model[model_name].append(result)
            
            total_images = 0
            total_gt_objects = 0
            total_pred_objects = 0
            overall_tp = 0
            overall_fp = 0
            overall_fn = 0
            
            # Process each model
            for model_name, model_results in results_by_model.items():
                metrics = ModelPerformanceMetrics.objects.create(
                    evaluation_run=evaluation_run,
                    model_name=model_name,
                    images_processed=len(model_results)
                )
                
                model_tp = model_fp = model_fn = 0
                model_inference_times = []
                model_confidences = []
                all_predictions = []
                all_ground_truth = []
                
                # Process each image for this model
                for result in model_results:
                    image_filename = result.image_upload.original_filename if result.image_upload else 'unknown'
                    
                    # Load ground truth
                    ground_truth = self.load_ground_truth_annotations(image_filename)
                    
                    # Extract predictions
                    predictions = self.extract_predictions_from_result(result)
                    
                    if species_filter:
                        ground_truth = [gt for gt in ground_truth if gt['species'] in species_filter]
                        predictions = [pred for pred in predictions if pred['species'] in species_filter]
                    
                    all_predictions.extend(predictions)
                    all_ground_truth.extend(ground_truth)
                    
                    # Match predictions to ground truth
                    matches, unmatched_preds, unmatched_gt = self.match_predictions_to_ground_truth(
                        predictions, ground_truth, float(evaluation_run.iou_threshold)
                    )
                    
                    # Update confusion matrix
                    image_tp = len(matches)
                    image_fp = len(unmatched_preds)
                    image_fn = len(unmatched_gt)
                    
                    model_tp += image_tp
                    model_fp += image_fp
                    model_fn += image_fn
                    
                    # Store image-level results
                    if result.inference_time:
                        model_inference_times.append(float(result.inference_time))
                    
                    # Store detailed image evaluation
                    ImageEvaluationResult.objects.create(
                        evaluation_run=evaluation_run,
                        image_upload=result.image_upload,
                        image_filename=image_filename,
                        model_used=model_name,
                        ground_truth_boxes=ground_truth,
                        ground_truth_count=len(ground_truth),
                        predicted_boxes=predictions,
                        predicted_count=len(predictions),
                        matches=[{
                            'prediction': m['prediction'],
                            'ground_truth': m['ground_truth'],
                            'iou': m['iou']
                        } for m in matches],
                        unmatched_predictions=unmatched_preds,
                        unmatched_ground_truth=unmatched_gt,
                        image_precision=image_tp / (image_tp + image_fp) if (image_tp + image_fp) > 0 else 0,
                        image_recall=image_tp / (image_tp + image_fn) if (image_tp + image_fn) > 0 else 0,
                        inference_time_ms=float(result.inference_time) * 1000 if result.inference_time else None
                    )
                
                # Calculate model-level metrics
                metrics.true_positives = model_tp
                metrics.false_positives = model_fp
                metrics.false_negatives = model_fn
                metrics.ground_truth_objects = len(all_ground_truth)
                metrics.predicted_objects = len(all_predictions)
                
                # Calculate performance metrics
                metrics.calculate_metrics()
                
                # Calculate mAP
                if all_predictions and all_ground_truth:
                    aps = []
                    for class_id, species_name in self.species_mapping.items():
                        if not species_filter or species_name in species_filter:
                            ap = self.calculate_average_precision(
                                all_predictions, all_ground_truth, class_id, 
                                float(evaluation_run.iou_threshold)
                            )
                            aps.append(ap)
                            
                            # Create species-specific metrics
                            species_preds = [p for p in all_predictions if p['class_id'] == class_id]
                            species_gt = [gt for gt in all_ground_truth if gt['class_id'] == class_id]
                            
                            species_matches, species_fp, species_fn = self.match_predictions_to_ground_truth(
                                species_preds, species_gt, float(evaluation_run.iou_threshold)
                            )
                            
                            species_tp = len(species_matches)
                            species_fp_count = len(species_fp)
                            species_fn_count = len(species_fn)
                            
                            species_metrics = SpeciesPerformanceMetrics.objects.create(
                                model_metrics=metrics,
                                species_name=species_name,
                                species_class_id=class_id,
                                true_positives=species_tp,
                                false_positives=species_fp_count,
                                false_negatives=species_fn_count,
                                average_precision=Decimal(str(ap)),
                                ground_truth_count=len(species_gt),
                                detected_count=len(species_preds)
                            )
                            
                            # Calculate species precision/recall
                            if species_tp + species_fp_count > 0:
                                species_metrics.precision = Decimal(species_tp) / Decimal(species_tp + species_fp_count)
                            if species_tp + species_fn_count > 0:
                                species_metrics.recall = Decimal(species_tp) / Decimal(species_tp + species_fn_count)
                            if species_metrics.precision and species_metrics.recall and (species_metrics.precision + species_metrics.recall) > 0:
                                species_metrics.f1_score = 2 * (species_metrics.precision * species_metrics.recall) / (species_metrics.precision + species_metrics.recall)
                            
                            species_metrics.save()
                    
                    metrics.map_50 = Decimal(str(np.mean(aps))) if aps else Decimal('0.0000')
                
                # Calculate average inference time
                if model_inference_times:
                    metrics.avg_inference_time_ms = Decimal(str(np.mean(model_inference_times) * 1000))
                
                metrics.save()
                
                # Update overall counters
                total_images += len(model_results)
                total_gt_objects += len(all_ground_truth)
                total_pred_objects += len(all_predictions)
                overall_tp += model_tp
                overall_fp += model_fp
                overall_fn += model_fn
            
            # Calculate overall metrics
            evaluation_run.total_images_evaluated = total_images
            evaluation_run.total_ground_truth_objects = total_gt_objects
            evaluation_run.total_predicted_objects = total_pred_objects
            
            if overall_tp + overall_fp > 0:
                evaluation_run.overall_precision = Decimal(overall_tp) / Decimal(overall_tp + overall_fp)
            if overall_tp + overall_fn > 0:
                evaluation_run.overall_recall = Decimal(overall_tp) / Decimal(overall_tp + overall_fn)
            if evaluation_run.overall_precision and evaluation_run.overall_recall and (evaluation_run.overall_precision + evaluation_run.overall_recall) > 0:
                evaluation_run.overall_f1_score = 2 * (evaluation_run.overall_precision * evaluation_run.overall_recall) / (evaluation_run.overall_precision + evaluation_run.overall_recall)
            
            # Calculate overall mAP
            model_maps = [float(m.map_50) for m in evaluation_run.model_metrics.all() if m.map_50]
            if model_maps:
                evaluation_run.overall_map_50 = Decimal(str(np.mean(model_maps)))
            
            # Complete evaluation
            end_time = timezone.now()
            evaluation_run.processing_duration = end_time - start_time
            evaluation_run.status = 'COMPLETED'
            evaluation_run.save()
            
            return evaluation_run
            
        except Exception as e:
            evaluation_run.status = 'FAILED'
            evaluation_run.error_message = str(e)
            evaluation_run.save()
            raise e
