"""
Bird Detection Service using YOLO model
Integrates with the existing bird_detection system
"""
import os
import sys
import uuid
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging

# Add the bird_detection directory to Python path
project_root = Path(__file__).parent.parent.parent
bird_detection_path = project_root / 'bird_detection'
sys.path.insert(0, str(bird_detection_path))

try:
    from ultralytics import YOLO
    import torch
    import cv2
    import numpy as np
    from PIL import Image
    import io
except ImportError as e:
    logging.error(f"Required packages not installed: {e}")
    YOLO = None
    torch = None
    cv2 = None
    np = None
    Image = None

logger = logging.getLogger(__name__)

class BirdDetectionService:
    """Service for detecting birds in images using YOLO model"""
    
    def __init__(self):
        self.model = None
        self.model_path = None
        self.device = 'cuda' if torch and torch.cuda.is_available() else 'cpu'
        self.confidence_threshold = 0.25
        self.initialize_model()
    
    def initialize_model(self):
        """Initialize the YOLO model"""
        try:
            # Look for trained model in multiple locations
            possible_model_paths = [
                project_root / 'bird_detection' / 'chinese_egret_model.pt',
                project_root / 'runs' / 'detect' / 'train' / 'weights' / 'best.pt',
                project_root / 'runs' / 'detect' / 'train2' / 'weights' / 'best.pt',
                project_root / 'runs' / 'detect' / 'train3' / 'weights' / 'best.pt',
                project_root / 'runs' / 'detect' / 'train4' / 'weights' / 'best.pt',
                project_root / 'models' / 'yolov8x.pt',  # Fallback to base model
            ]
            
            for model_path in possible_model_paths:
                if model_path.exists():
                    logger.info(f"Loading model from: {model_path}")
                    self.model = YOLO(str(model_path))
                    self.model_path = str(model_path)
                    break
            
            if not self.model:
                logger.warning("No trained model found, using base YOLOv8x model")
                base_model_path = project_root / 'models' / 'yolov8x.pt'
                if base_model_path.exists():
                    self.model = YOLO(str(base_model_path))
                    self.model_path = str(base_model_path)
                else:
                    logger.error("No YOLO model found!")
                    return
            
            logger.info(f"Model loaded successfully on device: {self.device}")
            
        except Exception as e:
            logger.error(f"Error initializing model: {e}")
            self.model = None
    
    def detect_birds(self, image_content: bytes, image_filename: str = None) -> Dict:
        """
        Detect birds in an image
        
        Args:
            image_content: Raw image bytes
            image_filename: Optional filename for logging
            
        Returns:
            Dictionary containing detection results
        """
        if not self.model:
            logger.error("Model not initialized")
            return self._create_error_result("Model not initialized")
        
        try:
            logger.info(f"Processing image: {image_filename or 'unknown'}")
            
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_content))
            
            # Run detection
            results = self.model(image, conf=self.confidence_threshold, device=self.device)
            
            # Process results
            detections = []
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # Get coordinates
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        confidence = float(box.conf[0].cpu().numpy())
                        class_id = int(box.cls[0].cpu().numpy())
                        class_name = result.names[class_id] if class_id in result.names else f"class_{class_id}"
                        
                        detection = {
                            'species': class_name,
                            'confidence': confidence,
                            'bounding_box': {
                                'x': int(x1),
                                'y': int(y1),
                                'width': int(x2 - x1),
                                'height': int(y2 - y1),
                                'x1': int(x1),
                                'y1': int(y1),
                                'x2': int(x2),
                                'y2': int(y2)
                            },
                            'class_id': class_id
                        }
                        detections.append(detection)
            
            # Get the best detection (highest confidence)
            best_detection = None
            if detections:
                best_detection = max(detections, key=lambda x: x['confidence'])
            
            # Create result with proper detection count
            result = {
                'success': True,
                'detections': detections,
                'best_detection': best_detection,
                'total_detections': len(detections),
                'model_used': Path(self.model_path).name if self.model_path else 'unknown',
                'device_used': self.device,
                'confidence_threshold': self.confidence_threshold
            }
            
            logger.info(f"Detection completed: {len(detections)} birds found")
            return result
            
        except Exception as e:
            logger.error(f"Error during detection: {e}")
            return self._create_error_result(str(e))
    
    def _create_error_result(self, error_message: str) -> Dict:
        """Create an error result dictionary"""
        return {
            'success': False,
            'error': error_message,
            'detections': [],
            'best_detection': None,
            'total_detections': 0,
            'model_used': 'unknown',
            'device_used': self.device,
            'confidence_threshold': self.confidence_threshold
        }
    
    def get_model_info(self) -> Dict:
        """Get information about the loaded model"""
        if not self.model:
            return {'error': 'Model not initialized'}
        
        return {
            'model_path': self.model_path,
            'device': self.device,
            'confidence_threshold': self.confidence_threshold,
            'model_type': 'YOLOv8',
            'available': True
        }
    
    def is_available(self) -> bool:
        """Check if the detection service is available"""
        return self.model is not None

# Global instance
bird_detection_service = BirdDetectionService()

def get_bird_detection_service() -> BirdDetectionService:
    """Get the global bird detection service instance"""
    return bird_detection_service
