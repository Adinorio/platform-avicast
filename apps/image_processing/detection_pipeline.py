"""
Detection Pipeline Components
Separates detection logic into focused, testable components
"""

import logging
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image
from ultralytics import YOLO

from .config import IMAGE_CONFIG
from .image_utils import ImageUtils

logger = logging.getLogger(__name__)


class ImageValidator:
    """Validates image content and dimensions"""
    
    def __init__(self):
        self.image_utils = ImageUtils()
    
    def validate_image_content(self, image_content: bytes) -> Tuple[bool, str]:
        """Validate that image content is valid"""
        if not image_content or len(image_content) == 0:
            return False, "Image file is empty or corrupted"
        
        if not self.image_utils.is_valid_image_format(image_content):
            return False, "Image format not supported or corrupted"
        
        return True, "Valid image content"
    
    def validate_image_dimensions(self, image_content: bytes) -> Tuple[bool, str]:
        """Validate image dimensions against configured limits"""
        width, height = self.image_utils.get_image_dimensions(image_content)
        
        if width == 0 or height == 0:
            return False, "Could not determine image dimensions"
        
        min_dims = IMAGE_CONFIG["MIN_IMAGE_DIMENSIONS"]
        max_dims = IMAGE_CONFIG["MAX_IMAGE_DIMENSIONS"]
        
        return self.image_utils.validate_image_dimensions(width, height, min_dims, max_dims)


class YOLODetector:
    """Handles YOLO model detection operations"""
    
    def __init__(self, model, device: str, confidence_threshold: float):
        self.model = model
        self.device = device
        self.confidence_threshold = confidence_threshold
    
    def detect_objects(self, image: Image.Image) -> List[Dict[str, Any]]:
        """Run YOLO detection on image"""
        try:
            results = self.model(image, conf=self.confidence_threshold, device=self.device)
            return self._extract_detections(results)
        except Exception as e:
            logger.error(f"YOLO detection failed: {str(e)}")
            return []
    
    def _extract_detections(self, results) -> List[Dict[str, Any]]:
        """Extract detection data from YOLO results"""
        detections = []
        
        for result in results:
            boxes = result.boxes
            if boxes is not None and len(boxes) > 0:
                for i, box in enumerate(boxes):
                    try:
                        detection = self._process_single_detection(box, result, i)
                        if detection:
                            detections.append(detection)
                    except Exception as e:
                        logger.warning(f"Error processing detection {i}: {e}")
                        continue
        
        return detections
    
    def _process_single_detection(self, box, result, index: int) -> Optional[Dict[str, Any]]:
        """Process a single detection box"""
        try:
            # Get coordinates
            if not (hasattr(box, "xyxy") and len(box.xyxy) > 0):
                return None
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            
            # Get confidence
            if not (hasattr(box, "conf") and len(box.conf) > 0):
                return None
            confidence = float(box.conf[0].cpu().numpy())
            
            # Get class
            if not (hasattr(box, "cls") and len(box.cls) > 0):
                return None
            class_id = int(box.cls[0].cpu().numpy())
            
            # Get class name
            class_name = (
                result.names[class_id]
                if hasattr(result, "names") and class_id in result.names
                else f"class_{class_id}"
            )
            
            # Calculate dimensions
            crop_w = int(x2 - x1)
            crop_h = int(y2 - y1)
            
            return {
                "species": class_name,
                "confidence": confidence,
                "bounding_box": {
                    "x": int(x1),
                    "y": int(y1),
                    "width": crop_w,
                    "height": crop_h,
                    "x1": int(x1),
                    "y1": int(y1),
                    "x2": int(x2),
                    "y2": int(y2),
                },
                "class_id": class_id,
                "crop_size": (crop_w, crop_h),
                "index": index,
            }
        except Exception as e:
            logger.warning(f"Error processing detection {index}: {e}")
            return None


class SpeciesClassifier:
    """Handles species classification using trained EfficientNet model"""
    
    def __init__(self):
        self.model_path = Path(__file__).parent.parent / "models" / "classifier" / "best_model.pth"
    
    def classify_species(self, crop: np.ndarray) -> Dict[str, float]:
        """Classify species from cropped image"""
        if not self.model_path.exists():
            logger.warning("Trained classifier model not found, using mock classification")
            return self._mock_classify(crop)
        
        try:
            return self._trained_classify(crop)
        except Exception as e:
            logger.error(f"Error in species classification: {e}")
            return self._mock_classify(crop)
    
    def _trained_classify(self, crop: np.ndarray) -> Dict[str, float]:
        """Use trained EfficientNet model for classification"""
        import torch.nn as nn
        from torchvision import models, transforms
        
        # Load checkpoint
        checkpoint = torch.load(self.model_path, map_location="cpu", weights_only=False)
        model_name = checkpoint.get("model_name", "efficientnet_b0")
        class_names = checkpoint.get("class_names", ["Chinese Egret", "Intermediate Egret"])
        
        # Recreate model architecture
        if model_name == "efficientnet_b0":
            model = models.efficientnet_b0(weights=None)
            num_features = model.classifier[1].in_features
            model.classifier[1] = nn.Linear(num_features, len(class_names))
        else:
            logger.warning("Unsupported model architecture, using mock classification")
            return self._mock_classify(crop)
        
        # Load trained weights
        model.load_state_dict(checkpoint["model_state_dict"])
        model.eval()
        
        # Prepare image
        image = Image.fromarray(crop)
        transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        
        with torch.no_grad():
            input_tensor = transform(image).unsqueeze(0)
            outputs = model(input_tensor)
            probabilities = torch.softmax(outputs, dim=1)[0]
        
        # Convert to expected format
        probs_dict = {}
        for i, prob in enumerate(probabilities):
            class_name = class_names[i]
            # Map to expected format
            if "Chinese" in class_name:
                probs_dict["Chinese"] = float(prob)
            elif "Intermediate" in class_name:
                probs_dict["Intermediate"] = float(prob)
            else:
                probs_dict[class_name] = float(prob)
        
        # Fill in missing classes with low probabilities
        all_classes = ["Chinese", "Great", "Intermediate", "Little"]
        for cls in all_classes:
            if cls not in probs_dict:
                probs_dict[cls] = 0.01
        
        # Renormalize
        total = sum(probs_dict.values())
        probs_dict = {k: v / total for k, v in probs_dict.items()}
        
        return probs_dict
    
    def _mock_classify(self, crop: np.ndarray) -> Dict[str, float]:
        """Mock classification for testing"""
        # Simple mock based on crop characteristics
        crop_min_side = min(crop.shape[0], crop.shape[1])
        
        if crop_min_side > 200:
            return {"Chinese": 0.7, "Great": 0.1, "Intermediate": 0.1, "Little": 0.1}
        elif crop_min_side > 100:
            return {"Chinese": 0.4, "Great": 0.3, "Intermediate": 0.2, "Little": 0.1}
        else:
            return {"Chinese": 0.2, "Great": 0.3, "Intermediate": 0.3, "Little": 0.2}


class DecisionGates:
    """Applies decision gates to filter detections"""
    
    def __init__(self):
        self.detection_conf_threshold = 0.80
        self.detection_min_crop_side = 128
        self.classifier_conf_threshold = 0.60
        self.classifier_margin_threshold = 0.20
    
    def apply_detection_gate(self, detection: Dict[str, Any]) -> Tuple[str, str]:
        """Apply detection gate to filter detections"""
        confidence = detection["confidence"]
        crop_w = detection["crop_size"][0]
        crop_h = detection["crop_size"][1]
        
        min_side = min(crop_w, crop_h)
        
        if confidence < self.detection_conf_threshold:
            return "ABSTAIN", "low_confidence_detection"
        
        if min_side < self.detection_min_crop_side:
            return "ABSTAIN", "small_crop_min_side"
        
        return "ACCEPT", "accept_detection"
    
    def apply_classification_gate(self, classifier_probs: Dict[str, float], crop_min_side: int) -> Tuple[str, str]:
        """Apply classification gate to filter classifications"""
        if not classifier_probs:
            return "ABSTAIN", "no_classifier_probs"
        
        # Get top two predictions
        sorted_probs = sorted(classifier_probs.items(), key=lambda x: x[1], reverse=True)
        top1_species, top1_prob = sorted_probs[0]
        
        if len(sorted_probs) < 2:
            margin = top1_prob
        else:
            top2_prob = sorted_probs[1][1]
            margin = top1_prob - top2_prob
        
        # Apply thresholds
        if top1_prob >= self.classifier_conf_threshold and margin >= self.classifier_margin_threshold:
            return "ACCEPT", f"high_confidence_margin_{top1_prob:.2f}_{margin:.2f}"
        else:
            return "ABSTAIN", f"low_confidence_or_ambiguous_margin_{top1_prob:.2f}_{margin:.2f}"
    
    def apply_final_decision(self, detection_status: str, detection_reason: str, 
                           classification_status: str, classification_reason: str) -> Tuple[str, str]:
        """Apply final decision combining both gates"""
        if detection_status == "ACCEPT" and classification_status == "ACCEPT":
            return "ACCEPT", "both_stages_passed"
        else:
            return "ABSTAIN", f"stage1_{detection_reason}_stage2_{classification_reason}"


class DetectionResultFormatter:
    """Formats detection results for output"""
    
    def __init__(self):
        self.image_utils = ImageUtils()
    
    def format_detection_result(self, detections: List[Dict[str, Any]], 
                              image_content: bytes, filename: str,
                              model_used: str, device_used: str,
                              confidence_threshold: float) -> Dict[str, Any]:
        """Format complete detection result"""
        # Get best detection
        best_detection = None
        if detections:
            best_detection = max(detections, key=lambda x: x["confidence"])
        
        # Get image analysis
        image_analysis = self.image_utils.create_image_analysis(image_content, filename)
        
        # Create result
        result = {
            "success": True,
            "detections": detections,
            "best_detection": best_detection,
            "total_detections": len(detections),
            "model_used": model_used,
            "model_version": model_used.split("_")[0] if model_used else "unknown",
            "device_used": device_used,
            "confidence_threshold": confidence_threshold,
            "image_analysis": image_analysis,
        }
        
        # Add no detection analysis if no detections found
        if not detections:
            result["no_detection_analysis"] = self._analyze_no_detections(image_content, model_used)
        
        return result
    
    def _analyze_no_detections(self, image_content: bytes, model_used: str) -> Dict[str, Any]:
        """Analyze why no detections were found"""
        width, height = self.image_utils.get_image_dimensions(image_content)
        
        # Simple analysis based on image characteristics
        if width < 200 or height < 200:
            return {
                "reason": "Image too small for reliable detection",
                "suggestions": [
                    "Use higher resolution images",
                    "Ensure image is at least 200x200 pixels"
                ]
            }
        elif width > 4000 or height > 4000:
            return {
                "reason": "Image too large, may cause memory issues",
                "suggestions": [
                    "Resize image to under 4000x4000 pixels",
                    "Use image compression tools"
                ]
            }
        else:
            return {
                "reason": "No birds detected in image",
                "suggestions": [
                    "Try a different image",
                    "Check if birds are clearly visible",
                    "Ensure good lighting and contrast"
                ]
            }



