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
from django.db import models as db_models

from .models import ImageUpload, ImageProcessingResult
from .analytics_models import (
    ModelEvaluationRun, ModelPerformanceMetrics, 
    SpeciesPerformanceMetrics, ConfusionMatrixEntry, ImageEvaluationResult
)

class ModelAnalyticsService:
    """Enhanced service for calculating comprehensive model performance analytics with thesis-level statistical analysis"""
    
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
        label_filename = image_filename.replace('.jpg', '.txt').replace('.png', '.txt').replace('.jpeg', '.txt')
        
        # First, try to find in our annotation directory (user-created annotations)
        from django.conf import settings
        import os
        
        annotation_file = os.path.join(settings.MEDIA_ROOT, 'annotations', label_filename)
        if os.path.exists(annotation_file):
            ground_truth = []
            with open(annotation_file, 'r') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 5:
                        class_id = int(parts[0])
                        x, y, w, h = map(float, parts[1:5])
                        ground_truth.append({
                            'class_id': class_id,
                            'species': self.species_mapping.get(class_id, f'Bird_Class_{class_id}'),
                            'bbox': [x, y, w, h],
                            'confidence': 1.0  # Ground truth has perfect confidence
                        })
            return ground_truth
        
        # Fallback: Search in dataset directories (for external datasets)
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
        ai_dimensions_raw = processing_result.bounding_box.get('ai_dimensions', [640, 640])

        # Ensure ai_dimensions is a tuple for consistency
        ai_dimensions = tuple(ai_dimensions_raw) if isinstance(ai_dimensions_raw, list) else ai_dimensions_raw

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

    def run_kfold_evaluation(
        self,
        k: int,
        created_by,
        name: str = None,
        model_filters: List[str] = None,
        date_range: Tuple[datetime, datetime] = None,
        species_filter: List[str] = None,
        iou_threshold: float = 0.5,
        confidence_threshold: float = 0.25,
    ) -> ModelEvaluationRun:
        """
        Run K-fold cross-validation style evaluation over existing processed results.
        This does not retrain models; it partitions evaluated images into K folds and
        computes per-fold metrics for robustness reporting (means/std).
        """
        import hashlib
        from decimal import Decimal as D

        # Create an evaluation run record
        eval_run = ModelEvaluationRun.objects.create(
            name=name or f"K-Fold Evaluation (K={k})",
            description=f"K-fold cross-validation over processed results (K={k})",
            created_by=created_by,
            iou_threshold=D(str(iou_threshold)),
            confidence_threshold=D(str(confidence_threshold)),
            models_evaluated=model_filters or [],
            species_filter=species_filter or [],
            status='PROCESSING'
        )

        try:
            # Base queryset of usable results
            results_qs = ImageProcessingResult.objects.filter(
                processing_status=ImageProcessingResult.ProcessingStatus.COMPLETED,
                review_status__in=[
                    ImageProcessingResult.ReviewStatus.APPROVED,
                    ImageProcessingResult.ReviewStatus.OVERRIDDEN
                ]
            )

            if model_filters:
                results_qs = results_qs.filter(ai_model__in=model_filters)

            if date_range:
                start_date, end_date = date_range
                results_qs = results_qs.filter(
                    created_at__gte=start_date,
                    created_at__lte=end_date
                )

            results = list(results_qs.select_related('image_upload'))

            # Precompute ground truth and predictions per result; filter those without GT
            prepared = []
            for res in results:
                image_filename = res.image_upload.original_filename if res.image_upload else 'unknown'
                gt = self.load_ground_truth_annotations(image_filename)
                if species_filter:
                    gt = [g for g in gt if g['species'] in species_filter]
                # Skip if no ground truth available
                if not gt:
                    continue
                preds = self.extract_predictions_from_result(res)
                if species_filter:
                    preds = [p for p in preds if p['species'] in species_filter]
                prepared.append({
                    'result': res,
                    'filename': image_filename,
                    'model': res.ai_model,
                    'ground_truth': gt,
                    'predictions': preds,
                })

            if not prepared:
                eval_run.status = 'FAILED'
                eval_run.error_message = 'No evaluable results with ground truth found.'
                eval_run.save()
                return eval_run

            # Assign folds deterministically by filename hash
            def fold_index(filename: str) -> int:
                h = hashlib.md5(filename.encode('utf-8')).hexdigest()
                return int(h, 16) % max(1, k)

            # Group by model
            from collections import defaultdict
            by_model: Dict[str, List[dict]] = defaultdict(list)
            for item in prepared:
                by_model[item['model']].append(item)

            # Ensure we only evaluate requested models if provided
            model_names = list(by_model.keys()) if not model_filters else [m for m in by_model.keys() if m in model_filters]

            # Accumulators for overall stats
            total_images = 0
            all_model_maps: Dict[str, List[float]] = defaultdict(list)
            all_model_precisions: Dict[str, List[float]] = defaultdict(list)
            all_model_recalls: Dict[str, List[float]] = defaultdict(list)
            all_model_f1s: Dict[str, List[float]] = defaultdict(list)

            # Evaluate per model per fold
            for model_name in model_names:
                model_items = by_model[model_name]
                if not model_items:
                    continue

                for fi in range(max(1, k)):
                    # Select fold items
                    fold_items = [it for it in model_items if fold_index(it['filename']) == fi]
                    if not fold_items:
                        continue

                    # Aggregate predictions and ground truth for this fold
                    all_preds = []
                    all_gt = []
                    model_tp = model_fp = model_fn = 0

                    for it in fold_items:
                        preds = it['predictions']
                        gt = it['ground_truth']
                        all_preds.extend(preds)
                        all_gt.extend(gt)
                        matches, unmatched_preds, unmatched_gt = self.match_predictions_to_ground_truth(
                            preds, gt, float(iou_threshold)
                        )
                        model_tp += len(matches)
                        model_fp += len(unmatched_preds)
                        model_fn += len(unmatched_gt)

                    # Create a metrics row for this model and fold
                    metrics = ModelPerformanceMetrics.objects.create(
                        evaluation_run=eval_run,
                        model_name=f"{model_name} [fold {fi+1}/{k}]",
                        images_processed=len(fold_items),
                        ground_truth_objects=len(all_gt),
                        predicted_objects=len(all_preds),
                        true_positives=model_tp,
                        false_positives=model_fp,
                        false_negatives=model_fn,
                    )

                    # Calculate AP per class, then mAP@0.5
                    aps = []
                    for class_id, species_name in self.species_mapping.items():
                        if species_filter and species_name not in species_filter:
                            continue
                        ap = self.calculate_average_precision(all_preds, all_gt, class_id, float(iou_threshold))
                        aps.append(ap)
                    if aps:
                        metrics.map_50 = D(str(np.mean(aps)))

                    # Precision/Recall/F1
                    metrics.calculate_metrics()
                    metrics.save()

                    # Collect for aggregates
                    all_model_maps[model_name].append(float(metrics.map_50) if metrics.map_50 else 0.0)
                    all_model_precisions[model_name].append(float(metrics.precision) if metrics.precision else 0.0)
                    all_model_recalls[model_name].append(float(metrics.recall) if metrics.recall else 0.0)
                    all_model_f1s[model_name].append(float(metrics.f1_score) if metrics.f1_score else 0.0)

                    total_images += len(fold_items)

                # After folds, add an aggregate row per model (mean±std)
                def mean_std(values: List[float]) -> Tuple[float, float]:
                    if not values:
                        return 0.0, 0.0
                    return float(np.mean(values)), float(np.std(values))

                map_mean, map_std = mean_std(all_model_maps[model_name])
                p_mean, p_std = mean_std(all_model_precisions[model_name])
                r_mean, r_std = mean_std(all_model_recalls[model_name])
                f1_mean, f1_std = mean_std(all_model_f1s[model_name])

                agg = ModelPerformanceMetrics.objects.create(
                    evaluation_run=eval_run,
                    model_name=f"{model_name} [k-fold aggregate]",
                    images_processed=sum(1 for it in model_items),
                )
                # Store means; std can be placed into size fields as a convenient place if desired,
                # but we keep fields clean and only store means to avoid schema changes.
                agg.precision = D(str(p_mean))
                agg.recall = D(str(r_mean))
                agg.f1_score = D(str(f1_mean))
                agg.map_50 = D(str(map_mean))
                agg.save()

            # Set overall aggregates across models
            # Overall mAP as mean of model aggregates if available
            model_agg_maps = []
            for model_name in model_names:
                means = all_model_maps.get(model_name)
                if means:
                    model_agg_maps.append(float(np.mean(means)))
            if model_agg_maps:
                eval_run.overall_map_50 = D(str(np.mean(model_agg_maps)))

            eval_run.total_images_evaluated = total_images
            eval_run.status = 'COMPLETED'
            eval_run.save()

            return eval_run

        except Exception as e:
            eval_run.status = 'FAILED'
            eval_run.error_message = str(e)
            eval_run.save()
            raise

    def summarize_reviewed_results(self, species_filter: List[str] = None, model_filters: List[str] = None) -> Dict:
        """
        Build analytics directly from reviewed results (Approved/Overridden),
        using final species/count as ground truth for reporting.
        """
        # Query reviewed results
        qs = ImageProcessingResult.objects.filter(
            processing_status=ImageProcessingResult.ProcessingStatus.COMPLETED,
            review_status__in=[
                ImageProcessingResult.ReviewStatus.APPROVED,
                ImageProcessingResult.ReviewStatus.OVERRIDDEN
            ]
        )

        if species_filter:
            qs = qs.filter(
                Q(overridden_species__in=species_filter) |
                Q(detected_species__in=species_filter)
            )
        if model_filters:
            qs = qs.filter(ai_model__in=model_filters)

        total_images = qs.count()
        by_model: Dict[str, Dict] = {}
        by_species: Dict[str, Dict] = {}

        def inc(d: Dict, key: str, field: str, val: float = 1):
            if key not in d:
                d[key] = {'images': 0, 'detections': 0, 'avg_conf': 0.0, 'sum_conf': 0.0}
            d[key][field] = d[key].get(field, 0) + val

        for r in qs.select_related('image_upload'):
            model_name = r.ai_model or 'UNKNOWN'
            final_species = r.final_species or 'UNKNOWN'
            total_detections = r.final_count or 0
            conf = float(r.confidence_score) if r.confidence_score is not None else 0.0

            # Per-model aggregates
            inc(by_model, model_name, 'images', 1)
            inc(by_model, model_name, 'detections', total_detections)
            by_model[model_name]['sum_conf'] += conf

            # Per-species aggregates
            inc(by_species, final_species, 'images', 1)
            inc(by_species, final_species, 'detections', total_detections)
            by_species[final_species]['sum_conf'] += conf

        # Compute averages
        for d in (by_model, by_species):
            for key, entry in d.items():
                imgs = max(1, entry['images'])
                entry['avg_conf'] = entry['sum_conf'] / imgs
                entry.pop('sum_conf', None)

        # Build output
        return {
            'total_images': total_images,
            'models': by_model,
            'species': by_species,
        }

    def summarize_model_performance_from_reviews(self, model_filters: List[str] = None) -> Dict:
        """
        Analyzes model performance by comparing the AI's initial predictions
        against the final human-reviewed (Approved/Overridden) results.
        This provides a practical measure of model accuracy based on curated data.
        """
        qs = ImageProcessingResult.objects.filter(
            processing_status=ImageProcessingResult.ProcessingStatus.COMPLETED
        ).select_related('image_upload')

        if model_filters:
            qs = qs.filter(ai_model__in=model_filters)

        by_model = {}

        for r in qs:
            model_name = r.ai_model or 'UNKNOWN'
            if model_name not in by_model:
                by_model[model_name] = {
                    'total_images': 0,
                    'images_reviewed': 0,
                    'ai_total_detections': 0,
                    'final_human_total_detections': 0,
                    'correctly_identified_species': 0, # AI species matched final approved/overridden species
                    'detections_approved_by_human': 0, # AI count was accepted
                    'detections_overridden_by_human': 0, # AI count/species was changed
                }

            stats = by_model[model_name]
            stats['total_images'] += 1
            stats['ai_total_detections'] += r.total_detections or 0
            stats['final_human_total_detections'] += r.final_count or 0

            if r.review_status != ImageProcessingResult.ReviewStatus.PENDING:
                stats['images_reviewed'] += 1
                
                # Check if the AI's top species prediction was correct
                if r.detected_species and r.detected_species == r.final_species:
                    stats['correctly_identified_species'] += 1

                if r.review_status == ImageProcessingResult.ReviewStatus.APPROVED:
                    # Human agreed with the AI's count and species
                    stats['detections_approved_by_human'] += r.total_detections or 0
                elif r.review_status == ImageProcessingResult.ReviewStatus.OVERRIDDEN:
                    # Human changed the species or count
                    stats['detections_overridden_by_human'] += 1


        # Calculate final summary metrics
        for model, stats in by_model.items():
            reviewed_count = stats['images_reviewed']
            ai_detections = stats['ai_total_detections']
            
            # How often was the AI's top species choice correct in reviewed images?
            stats['species_accuracy'] = (stats['correctly_identified_species'] / reviewed_count) if reviewed_count > 0 else 0
            
            # Of all AI detections, what portion was accepted as-is by humans?
            stats['practical_precision'] = (stats['detections_approved_by_human'] / ai_detections) if ai_detections > 0 else 0

        return {
            'total_results': qs.count(),
            'performance_by_model': by_model,
        }
    
    def calculate_statistical_significance(self, model_metrics_list, metric_name='f1_score', confidence_level=0.95):
        """
        Calculate statistical significance between model performances
        Returns confidence intervals and p-values for hypothesis testing
        """
        import numpy as np
        from scipy import stats
        
        results = {}
        
        # Extract metric values for each model
        model_data = {}
        for metrics in model_metrics_list:
            model_name = metrics.model_name
            metric_value = float(getattr(metrics, metric_name, 0))
            
            if model_name not in model_data:
                model_data[model_name] = []
            model_data[model_name].append(metric_value)
        
        # Calculate confidence intervals for each model
        for model_name, values in model_data.items():
            if len(values) > 1:
                # Calculate mean and standard error
                mean_val = np.mean(values)
                std_err = stats.sem(values)
                
                # Calculate confidence interval
                alpha = 1 - confidence_level
                t_critical = stats.t.ppf(1 - alpha/2, len(values) - 1)
                margin_of_error = t_critical * std_err
                
                results[model_name] = {
                    'mean': mean_val,
                    'std_error': std_err,
                    'confidence_interval': (mean_val - margin_of_error, mean_val + margin_of_error),
                    'sample_size': len(values)
                }
            else:
                results[model_name] = {
                    'mean': values[0] if values else 0,
                    'std_error': 0,
                    'confidence_interval': None,
                    'sample_size': len(values)
                }
        
        # Perform pairwise t-tests between models
        pairwise_tests = {}
        model_names = list(model_data.keys())
        
        for i in range(len(model_names)):
            for j in range(i + 1, len(model_names)):
                model1, model2 = model_names[i], model_names[j]
                data1, data2 = model_data[model1], model_data[model2]
                
                if len(data1) > 1 and len(data2) > 1:
                    # Perform independent t-test
                    t_stat, p_value = stats.ttest_ind(data1, data2)
                    
                    pairwise_tests[f"{model1} vs {model2}"] = {
                        't_statistic': t_stat,
                        'p_value': p_value,
                        'significant': p_value < (1 - confidence_level),
                        'effect_size': abs(np.mean(data1) - np.mean(data2)) / np.sqrt((np.var(data1) + np.var(data2)) / 2)
                    }
        
        return {
            'model_confidence_intervals': results,
            'pairwise_comparisons': pairwise_tests,
            'confidence_level': confidence_level
        }
    
    def generate_performance_report(self, evaluation_run, include_statistical_analysis=True):
        """
        Generate a comprehensive performance report suitable for thesis documentation
        """
        import numpy as np
        
        report = {
            'run_metadata': {
                'name': evaluation_run.name,
                'created_at': evaluation_run.created_at,
                'total_images': evaluation_run.total_images_evaluated,
                'models_evaluated': evaluation_run.models_evaluated,
                'species_filter': evaluation_run.species_filter,
                'iou_threshold': float(evaluation_run.iou_threshold),
                'confidence_threshold': float(evaluation_run.confidence_threshold)
            },
            'overall_metrics': {
                'precision': float(evaluation_run.overall_precision or 0),
                'recall': float(evaluation_run.overall_recall or 0),
                'f1_score': float(evaluation_run.overall_f1_score or 0),
                'map_50': float(evaluation_run.overall_map_50 or 0),
                'map_50_95': float(evaluation_run.overall_map_50_95 or 0)
            },
            'model_performance': [],
            'species_performance': [],
            'error_analysis': {},
            'recommendations': []
        }
        
        # Model-level performance
        model_metrics = evaluation_run.model_metrics.all()
        for metrics in model_metrics:
            model_data = {
                'model_name': metrics.model_name,
                'precision': float(metrics.precision or 0),
                'recall': float(metrics.recall or 0),
                'f1_score': float(metrics.f1_score or 0),
                'map_50': float(metrics.map_50 or 0),
                'map_50_95': float(metrics.map_50_95 or 0),
                'avg_inference_time_ms': float(metrics.avg_inference_time_ms or 0),
                'model_size_mb': float(metrics.model_size_mb or 0),
                'true_positives': metrics.true_positives,
                'false_positives': metrics.false_positives,
                'false_negatives': metrics.false_negatives,
                'images_processed': metrics.images_processed
            }
            
            # Calculate derived metrics
            total_predictions = metrics.true_positives + metrics.false_positives
            total_ground_truth = metrics.true_positives + metrics.false_negatives
            
            model_data.update({
                'accuracy': (metrics.true_positives / (metrics.true_positives + metrics.false_positives + metrics.false_negatives)) if (metrics.true_positives + metrics.false_positives + metrics.false_negatives) > 0 else 0,
                'specificity': self._calculate_specificity(metrics),
                'matthews_correlation': self._calculate_mcc(metrics),
                'efficiency_score': self._calculate_efficiency_score(metrics)
            })
            
            report['model_performance'].append(model_data)
        
        # Species-level performance
        for model_metrics in model_metrics:
            species_metrics = model_metrics.species_metrics.all()
            for species in species_metrics:
                species_data = {
                    'model_name': model_metrics.model_name,
                    'species_name': species.species_name,
                    'precision': float(species.precision or 0),
                    'recall': float(species.recall or 0),
                    'f1_score': float(species.f1_score or 0),
                    'average_precision': float(species.average_precision or 0),
                    'true_positives': species.true_positives,
                    'false_positives': species.false_positives,
                    'false_negatives': species.false_negatives,
                    'ground_truth_count': species.ground_truth_count,
                    'detected_count': species.detected_count
                }
                report['species_performance'].append(species_data)
        
        # Statistical analysis
        if include_statistical_analysis and len(model_metrics) > 1:
            report['statistical_analysis'] = self.calculate_statistical_significance(
                model_metrics, 'f1_score', 0.95
            )
        
        # Error analysis
        report['error_analysis'] = self._analyze_errors(evaluation_run)
        
        # Generate recommendations
        report['recommendations'] = self._generate_recommendations(report)
        
        return report
    
    def _calculate_specificity(self, metrics):
        """Calculate specificity (True Negative Rate)"""
        if metrics.false_positives == 0:
            return 1.0
        
        # Approximate specificity based on false positive rate
        total_possible_detections = metrics.images_processed * 10  # Assume avg 10 possible detection areas per image
        true_negatives = total_possible_detections - metrics.true_positives - metrics.false_positives - metrics.false_negatives
        
        if true_negatives + metrics.false_positives > 0:
            return true_negatives / (true_negatives + metrics.false_positives)
        return 0.0
    
    def _calculate_mcc(self, metrics):
        """Calculate Matthews Correlation Coefficient"""
        import numpy as np
        
        tp = metrics.true_positives
        fp = metrics.false_positives
        fn = metrics.false_negatives
        
        # Approximate true negatives for object detection
        total_possible = metrics.images_processed * 10
        tn = total_possible - tp - fp - fn
        
        denominator = np.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
        if denominator == 0:
            return 0.0
        
        return (tp * tn - fp * fn) / denominator
    
    def _calculate_efficiency_score(self, metrics):
        """Calculate efficiency score combining accuracy and speed"""
        f1 = float(metrics.f1_score or 0)
        inference_time = float(metrics.avg_inference_time_ms or 1000)  # Default to 1 second
        
        # Normalize inference time (lower is better)
        speed_score = 1000 / inference_time if inference_time > 0 else 0
        speed_normalized = min(speed_score / 10, 1.0)  # Normalize to 0-1 scale
        
        # Combine F1 score with speed (weighted 70% accuracy, 30% speed)
        return 0.7 * f1 + 0.3 * speed_normalized
    
    def _analyze_errors(self, evaluation_run):
        """Analyze common error patterns in evaluation results"""
        error_analysis = {
            'common_false_positives': {},
            'common_false_negatives': {},
            'confidence_patterns': {},
            'temporal_patterns': {}
        }
        
        # Analyze image-level results for error patterns
        image_results = evaluation_run.image_results.all()
        
        for result in image_results:
            # Analyze false positives
            for fp in result.unmatched_predictions:
                error_type = f"False Positive: {fp.get('species', 'unknown')}"
                error_analysis['common_false_positives'][error_type] = error_analysis['common_false_positives'].get(error_type, 0) + 1
            
            # Analyze false negatives
            for fn in result.unmatched_ground_truth:
                error_type = f"False Negative: {fn.get('species', 'unknown')}"
                error_analysis['common_false_negatives'][error_type] = error_analysis['common_false_negatives'].get(error_type, 0) + 1
        
        return error_analysis
    
    def _generate_recommendations(self, report):
        """Generate actionable recommendations based on performance analysis"""
        recommendations = []
        
        # Analyze overall performance
        overall_f1 = report['overall_metrics']['f1_score']
        overall_precision = report['overall_metrics']['precision']
        overall_recall = report['overall_metrics']['recall']
        
        if overall_f1 < 0.7:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'Performance',
                'issue': 'Low overall F1-score',
                'recommendation': 'Consider collecting more training data or adjusting model hyperparameters',
                'target_metric': 'F1-Score',
                'current_value': overall_f1,
                'target_value': 0.8
            })
        
        if overall_precision < 0.8 and overall_recall > 0.8:
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'Precision',
                'issue': 'High false positive rate',
                'recommendation': 'Increase confidence threshold or improve background/noise filtering',
                'target_metric': 'Precision',
                'current_value': overall_precision,
                'target_value': 0.85
            })
        
        if overall_recall < 0.8 and overall_precision > 0.8:
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'Recall',
                'issue': 'High false negative rate',
                'recommendation': 'Lower confidence threshold or augment training data with challenging examples',
                'target_metric': 'Recall',
                'current_value': overall_recall,
                'target_value': 0.85
            })
        
        # Model-specific recommendations
        models = report['model_performance']
        if len(models) > 1:
            best_model = max(models, key=lambda x: x['f1_score'])
            worst_model = min(models, key=lambda x: x['f1_score'])
            
            if best_model['f1_score'] - worst_model['f1_score'] > 0.1:
                recommendations.append({
                    'priority': 'LOW',
                    'category': 'Model Selection',
                    'issue': 'Significant performance gap between models',
                    'recommendation': f"Focus development on {best_model['model_name']} architecture",
                    'details': f"Best: {best_model['model_name']} (F1: {best_model['f1_score']:.3f}), "
                              f"Worst: {worst_model['model_name']} (F1: {worst_model['f1_score']:.3f})"
                })
        
        # Speed vs accuracy trade-offs
        for model in models:
            if model['avg_inference_time_ms'] > 1000 and model['f1_score'] < 0.9:
                recommendations.append({
                    'priority': 'MEDIUM',
                    'category': 'Efficiency',
                    'issue': 'Poor speed-accuracy trade-off',
                    'recommendation': f"Consider optimizing {model['model_name']} for faster inference",
                    'details': f"Current: {model['avg_inference_time_ms']:.1f}ms, F1: {model['f1_score']:.3f}"
                })
        
        return recommendations
