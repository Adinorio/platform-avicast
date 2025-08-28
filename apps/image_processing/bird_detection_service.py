"""
Enhanced Bird Detection Service using multiple YOLO versions
Supports YOLOv5, YOLOv8, and YOLOv9 with automatic fallback
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
    """Enhanced service for detecting birds using multiple YOLO versions"""
    
    def __init__(self, preferred_version: str = 'YOLO_V8'):
        self.models = {}  # Cache for different YOLO versions
        self.current_model = None
        self.current_version = preferred_version
        self.device = 'cuda' if torch and torch.cuda.is_available() else 'cpu'
        self.confidence_threshold = 0.5
        
        # YOLO version configurations
        self.version_configs = {
            'YOLO_V5': {
                'base_model': 'yolov5s.pt',
                'custom_model': 'chinese_egret_model_v5.pt',
                'description': 'YOLOv5 - Fast and lightweight'
            },
            'YOLO_V8': {
                'base_model': 'yolov8s.pt',
                'custom_model': 'chinese_egret_model_v8.pt',
                'description': 'YOLOv8 - Balanced performance and accuracy'
            },
            'YOLO_V9': {
                'base_model': 'yolov9c.pt',
                'custom_model': 'chinese_egret_model_v9.pt',
                'description': 'YOLOv9 - Latest and most advanced'
            }
        }
        
        self.initialize_models()
    
    def initialize_models(self):
        """Initialize all available YOLO models"""
        try:
            logger.info(f"Initializing YOLO models on device: {self.device}")
            
            for version, config in self.version_configs.items():
                try:
                    model = self._load_model(version, config)
                    if model:
                        self.models[version] = model
                        logger.info(f"✅ {version} model loaded successfully")
                    else:
                        logger.warning(f"⚠️ {version} model failed to load")
                except Exception as e:
                    logger.error(f"❌ Error loading {version}: {e}")
            
            # Set current model to preferred version or first available
            if self.current_version in self.models:
                self.current_model = self.models[self.current_version]
                logger.info(f"Current model set to: {self.current_version}")
            elif self.models:
                self.current_version = list(self.models.keys())[0]
                self.current_model = self.models[self.current_version]
                logger.info(f"Fallback to available model: {self.current_version}")
            else:
                logger.error("No YOLO models could be loaded!")
                
        except Exception as e:
            logger.error(f"Error during model initialization: {e}")
    
    def _load_model(self, version: str, config: Dict) -> Optional[YOLO]:
        """Load a specific YOLO model version"""
        try:
            # Priority 1: Custom trained model for bird detection
            custom_model_paths = [
                project_root / 'bird_detection' / config['custom_model'],
                project_root / 'runs' / 'detect' / 'train' / 'weights' / 'best.pt',
                project_root / 'runs' / 'detect' / 'train2' / 'weights' / 'best.pt',
                project_root / 'runs' / 'detect' / 'train3' / 'weights' / 'best.pt',
                project_root / 'runs' / 'detect' / 'train4' / 'weights' / 'best.pt',
            ]
            
            for model_path in custom_model_paths:
                if model_path.exists():
                    logger.info(f"Loading custom {version} model from: {model_path}")
                    return YOLO(str(model_path))
            
            # Priority 2: Base model from ultralytics
            try:
                logger.info(f"Loading base {version} model: {config['base_model']}")
                return YOLO(config['base_model'])
            except Exception as e:
                logger.warning(f"Base {version} model not available: {e}")
            
            # Priority 3: Local base model file
            local_model_path = project_root / 'models' / config['base_model']
            if local_model_path.exists():
                logger.info(f"Loading local {version} model from: {local_model_path}")
                return YOLO(str(local_model_path))
            
            return None
            
        except Exception as e:
            logger.error(f"Error loading {version} model: {e}")
            return None
    
    def switch_model(self, version: str) -> bool:
        """Switch to a different YOLO version"""
        if version not in self.models:
            logger.error(f"Model version {version} not available")
            return False
        
        self.current_version = version
        self.current_model = self.models[version]
        logger.info(f"Switched to {version} model")
        return True
    
    def get_available_models(self) -> Dict:
        """Get information about available models"""
        available = {}
        for version, config in self.version_configs.items():
            available[version] = {
                'available': version in self.models,
                'description': config['description'],
                'is_current': version == self.current_version
            }
        return available
    
    def detect_birds(self, image_content: bytes, image_filename: str = None, model_version: str = None) -> Dict:
        """
        Detect birds in an image using specified or current model
        
        Args:
            image_content: Raw image bytes
            image_filename: Optional filename for logging
            model_version: Optional specific YOLO version to use
            
        Returns:
            Dictionary containing detection results
        """
        # Use specified version or current model
        if model_version and model_version in self.models:
            detection_model = self.models[model_version]
            used_version = model_version
        elif self.current_model:
            detection_model = self.current_model
            used_version = self.current_version
        else:
            logger.error("No detection model available")
            return self._create_error_result("No detection model available")
        
        try:
            logger.info(f"Processing image: {image_filename or 'unknown'} with {used_version}")
            
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_content))
            
            # Run detection
            results = detection_model(image, conf=self.confidence_threshold, device=self.device)
            
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
            
            # Create result with proper detection count and model info
            result = {
                'success': True,
                'detections': detections,
                'best_detection': best_detection,
                'total_detections': len(detections),
                'model_used': f"{used_version}_{Path(detection_model.ckpt_path).name if hasattr(detection_model, 'ckpt_path') else 'unknown'}",
                'model_version': used_version,
                'device_used': self.device,
                'confidence_threshold': self.confidence_threshold
            }
            
            logger.info(f"Detection completed with {used_version}: {len(detections)} birds found")
            return result
            
        except Exception as e:
            logger.error(f"Error during detection with {used_version}: {e}")
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
            'model_version': self.current_version,
            'device_used': self.device,
            'confidence_threshold': self.confidence_threshold
        }
    
    def get_model_info(self) -> Dict:
        """Get comprehensive information about all models"""
        return {
            'current_version': self.current_version,
            'device': self.device,
            'confidence_threshold': self.confidence_threshold,
            'available_models': self.get_available_models(),
            'total_models': len(self.models),
            'available': len(self.models) > 0
        }
    
    def is_available(self) -> bool:
        """Check if the detection service is available"""
        return len(self.models) > 0
    
    def benchmark_models(self, image_content: bytes) -> Dict:
        """Benchmark all available models on the same image"""
        if not self.models:
            return {'error': 'No models available for benchmarking'}
        
        results = {}
        for version, model in self.models.items():
            try:
                start_time = torch.cuda.Event(enable_timing=True) if torch.cuda.is_available() else None
                end_time = torch.cuda.Event(enable_timing=True) if torch.cuda.is_available() else None
                
                if start_time and end_time:
                    start_time.record()
                
                # Run detection
                detection_result = self.detect_birds(image_content, f"benchmark_{version}", version)
                
                if start_time and end_time:
                    end_time.record()
                    torch.cuda.synchronize()
                    inference_time = start_time.elapsed_time(end_time) / 1000.0  # Convert to seconds
                else:
                    inference_time = None
                
                results[version] = {
                    'detections': detection_result.get('total_detections', 0),
                    'inference_time': inference_time,
                    'success': detection_result.get('success', False)
                }
                
            except Exception as e:
                results[version] = {
                    'error': str(e),
                    'success': False
                }
        
        return results

# Global instance
bird_detection_service = BirdDetectionService()

def get_bird_detection_service(version: str = None) -> BirdDetectionService:
    """Get the global bird detection service instance, optionally switching to specific version"""
    if version and version in bird_detection_service.models:
        bird_detection_service.switch_model(version)
    return bird_detection_service


