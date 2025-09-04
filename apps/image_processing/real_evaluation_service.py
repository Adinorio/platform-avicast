"""
Real Model Evaluation Service
Implements actual YOLO model loading, inference, and performance calculation
"""

import os
import cv2
import numpy as np
import torch
import time
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from decimal import Decimal
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

@dataclass
class Detection:
    """Single object detection result"""
    bbox: Tuple[float, float, float, float]  # x1, y1, x2, y2
    confidence: float
    class_id: int
    class_name: str

@dataclass
class GroundTruth:
    """Ground truth annotation"""
    bbox: Tuple[float, float, float, float]  # x1, y1, x2, y2
    class_id: int
    class_name: str

@dataclass
class ImageEvaluation:
    """Evaluation results for a single image"""
    image_path: str
    ground_truth: List[GroundTruth]
    predictions: Dict[str, List[Detection]]  # model_name -> detections
    metrics: Dict[str, Dict]  # model_name -> metrics

class RealEvaluationService:
    """Service for running actual YOLO model evaluations"""
    
    def __init__(self):
        self.models = {}
        self.class_names = ['chinese_egret', 'whiskered_tern', 'great_knot']
        # model path resolution is handled dynamically to support multiple aliases

    def _resolve_model_path(self, model_name: str) -> Tuple[Optional[str], Optional[str]]:
        """Resolve a given model name/alias to an on-disk weight file.
        Returns (resolved_model_name, absolute_path) or (None, None) if not found.
        Supports aliases like 'YOLO_V8', 'yolov8l', 'yolov9c', etc.
        """
        if not model_name:
            return None, None

        alias = model_name.strip()
        upper = alias.upper()
        base_models_dir = Path(settings.BASE_DIR) / 'models'

        alias_map = {
            'YOLO_V5': 'yolov5s.pt',
            'YOLO_V8': 'yolov8l.pt',
            'YOLO_V9': 'yolov9c.pt',
            'YOLOV5S': 'yolov5s.pt',
            'YOLOV8L': 'yolov8l.pt',
            'YOLOV9C': 'yolov9c.pt',
            'YOLOV5': 'yolov5s.pt',
            'YOLOV8': 'yolov8l.pt',
            'YOLOV9': 'yolov9c.pt',
            'CHINESE_EGRET_V1': 'chinese_egret_v1/chinese_egret_best.pt',
        }

        # If user passed a direct filename
        if alias.lower().endswith('.pt'):
            abs_path = Path(alias)
            if not abs_path.is_absolute():
                abs_path = base_models_dir / alias
            return alias, str(abs_path)

        filename = None
        if upper in alias_map:
            filename = alias_map[upper]
        elif alias.lower() in ['yolov5s', 'yolov8l', 'yolov9c']:
            filename = f"{alias.lower()}.pt"

        if not filename:
            return None, None

        abs_path = base_models_dir / filename
        return alias, str(abs_path)
 
    def load_model(self, model_name: str) -> bool:
        """Load a YOLO model"""
        try:
            resolved_name, model_path = self._resolve_model_path(model_name)
            if not model_path or not os.path.exists(model_path):
                logger.error(f"Model file not found for '{model_name}': {model_path}")
                return False
                
            # Try to load real YOLO model
            if 'yolov5' in model_path or 'yolov5' in (resolved_name or '').lower():
                # Load YOLOv5 model
                model = torch.hub.load('ultralytics/yolov5', 'custom', path=model_path)
            else:
                # Load YOLOv8/v9 with ultralytics
                from ultralytics import YOLO
                model = YOLO(model_path)
            self.models[model_name] = model
            logger.info(f"Successfully loaded model: {model_name} from {model_path}")
            return True
             
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            return False
    
    def run_inference(self, model_name: str, image_path: str, conf_threshold: float = 0.25) -> List[Detection]:
        """Run inference on a single image"""
        if model_name not in self.models:
            if not self.load_model(model_name):
                return []
        
        model = self.models[model_name]
        
        try:
            # Run prediction
            if hasattr(model, 'predict'):
                # Ultralytics YOLO models
                from ultralytics import YOLO  # ensure available
                results = model.predict(image_path, conf=conf_threshold, verbose=False)
                detections: List[Detection] = []
                for r in results:
                    if getattr(r, 'boxes', None) is None:
                        continue
                    for b in r.boxes:
                        # xyxy tensor
                        xyxy = b.xyxy[0].cpu().numpy()
                        x1, y1, x2, y2 = float(xyxy[0]), float(xyxy[1]), float(xyxy[2]), float(xyxy[3])
                        conf = float(b.conf[0].cpu().numpy()) if hasattr(b, 'conf') else 0.0
                        cls_id = int(b.cls[0].cpu().numpy()) if hasattr(b, 'cls') else -1
                        cls_name = self.class_names[cls_id] if 0 <= cls_id < len(self.class_names) else f'class_{cls_id}'
                        detections.append(Detection(bbox=(x1, y1, x2, y2), confidence=conf, class_id=cls_id, class_name=cls_name))
                return detections
            else:
                # Real PyTorch model
                img = cv2.imread(str(image_path))
                if img is None:
                    return []
                
                results = model(img)
                detections = []
                
                # Convert results to Detection objects
                for result in results.pandas().xyxy[0].itertuples():
                    conf = getattr(result, 'confidence', getattr(result, 'conf', 0))
                    cls_val = getattr(result, 'cls', getattr(result, 'class', -1))
                    if conf >= conf_threshold:
                        class_id = int(cls_val)
                        if class_id < len(self.class_names):
                            detection = Detection(
                                bbox=(float(result.xmin), float(result.ymin), float(result.xmax), float(result.ymax)),
                                confidence=float(conf),
                                class_id=class_id,
                                class_name=self.class_names[class_id]
                            )
                            detections.append(detection)
                
                return detections
                
        except Exception as e:
            logger.error(f"Inference failed for {model_name} on {image_path}: {e}")
            return []
    
    def calculate_iou(self, box1: Tuple[float, float, float, float], 
                     box2: Tuple[float, float, float, float]) -> float:
        """Calculate Intersection over Union (IoU) between two bounding boxes"""
        x1_1, y1_1, x2_1, y2_1 = box1
        x1_2, y1_2, x2_2, y2_2 = box2
        
        # Calculate intersection
        x1_int = max(x1_1, x1_2)
        y1_int = max(y1_1, y1_2)
        x2_int = min(x2_1, x2_2)
        y2_int = min(y2_1, y2_2)
        
        if x2_int <= x1_int or y2_int <= y1_int:
            return 0.0
        
        intersection = (x2_int - x1_int) * (y2_int - y1_int)
        
        # Calculate union
        area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
        area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
        union = area1 + area2 - intersection
        
        if union <= 0:
            return 0.0
        
        return intersection / union
    
    def match_detections(self, predictions: List[Detection], 
                        ground_truth: List[GroundTruth], 
                        iou_threshold: float = 0.5) -> Tuple[List, List, List]:
        """Match predictions to ground truth using IoU threshold"""
        matches = []  # (pred_idx, gt_idx, iou)
        unmatched_preds = list(range(len(predictions)))
        unmatched_gts = list(range(len(ground_truth)))
        
        # Sort predictions by confidence (highest first)
        pred_indices = sorted(range(len(predictions)), 
                            key=lambda i: predictions[i].confidence, reverse=True)
        
        for pred_idx in pred_indices:
            pred = predictions[pred_idx]
            best_iou = 0
            best_gt_idx = -1
            
            for gt_idx in unmatched_gts:
                gt = ground_truth[gt_idx]
                
                # Only match same class
                if pred.class_id != gt.class_id:
                    continue
                
                iou = self.calculate_iou(pred.bbox, gt.bbox)
                
                if iou > best_iou and iou >= iou_threshold:
                    best_iou = iou
                    best_gt_idx = gt_idx
            
            if best_gt_idx != -1:
                matches.append((pred_idx, best_gt_idx, best_iou))
                unmatched_preds.remove(pred_idx)
                unmatched_gts.remove(best_gt_idx)
        
        return matches, unmatched_preds, unmatched_gts
    
    def calculate_metrics(self, matches: List, unmatched_preds: List, 
                         unmatched_gts: List) -> Dict:
        """Calculate precision, recall, and F1 score"""
        tp = len(matches)
        fp = len(unmatched_preds)
        fn = len(unmatched_gts)
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        return {
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score,
            'true_positives': tp,
            'false_positives': fp,
            'false_negatives': fn
        }
    
    def load_ground_truth(self, image_path: str) -> List[GroundTruth]:
        """Load ground truth annotations for an image"""
        # Look for annotation file (YOLO format)
        image_path = Path(image_path)
        annotation_path = image_path.parent / 'labels' / f"{image_path.stem}.txt"
        
        if not annotation_path.exists():
            # No ground truth available
            return []
        
        ground_truth = []
        
        try:
            # Load image to get dimensions
            img = cv2.imread(str(image_path))
            if img is None:
                return []
            height, width = img.shape[:2]
            
            with open(annotation_path, 'r') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 5:
                        class_id = int(parts[0])
                        center_x, center_y, box_width, box_height = map(float, parts[1:5])
                        
                        # Convert from YOLO format to absolute coordinates
                        x1 = (center_x - box_width/2) * width
                        y1 = (center_y - box_height/2) * height
                        x2 = (center_x + box_width/2) * width
                        y2 = (center_y + box_height/2) * height
                        
                        if class_id < len(self.class_names):
                            gt = GroundTruth(
                                bbox=(x1, y1, x2, y2),
                                class_id=class_id,
                                class_name=self.class_names[class_id]
                            )
                            ground_truth.append(gt)
                            
        except Exception as e:
            logger.error(f"Failed to load ground truth for {image_path}: {e}")
            return []
        
        return ground_truth
    
    # Removed mock ground truth generation to ensure only real data is used
    
    def evaluate_image(self, image_path: str, models: List[str],
                      conf_threshold: float = 0.25, iou_threshold: float = 0.5) -> ImageEvaluation:
        """Evaluate multiple models on a single image"""
        logger.info(f"Starting evaluation of {os.path.basename(image_path)} with {len(models)} models")

        ground_truth = self.load_ground_truth(image_path)
        logger.info(f"Loaded ground truth: {len(ground_truth)} objects")

        predictions = {}
        metrics = {}

        for i, model_name in enumerate(models):
            logger.info(f"Evaluating with model {i+1}/{len(models)}: {model_name}")

            start_time = time.time()
            preds = self.run_inference(model_name, image_path, conf_threshold)
            inference_time = time.time() - start_time

            logger.info(f"Model {model_name} found {len(preds)} predictions in {inference_time:.3f}s")

            predictions[model_name] = preds

            # Calculate metrics
            matches, unmatched_preds, unmatched_gts = self.match_detections(
                preds, ground_truth, iou_threshold
            )
            model_metrics = self.calculate_metrics(matches, unmatched_preds, unmatched_gts)
            model_metrics['inference_time'] = inference_time

            logger.info(f"Model {model_name} metrics: Precision={model_metrics['precision']:.3f}, Recall={model_metrics['recall']:.3f}, F1={model_metrics['f1_score']:.3f}")

            metrics[model_name] = model_metrics

        logger.info(f"Completed evaluation of {os.path.basename(image_path)}")

        return ImageEvaluation(
            image_path=image_path,
            ground_truth=ground_truth,
            predictions=predictions,
            metrics=metrics
        )
