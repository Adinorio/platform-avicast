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

# Import configuration at module level
try:
    from .config import IMAGE_CONFIG
except ImportError:
    # Fallback for when config is not available
    IMAGE_CONFIG = {
        'MIN_IMAGE_DIMENSIONS': (50, 50),
        'MAX_IMAGE_DIMENSIONS': (4000, 4000),
        'DEFAULT_CONFIDENCE_THRESHOLD': 0.5,
        'VARIANCE_THRESHOLDS': {'VERY_LOW': 100, 'LOW': 500},
    }

class DetectionError:
    """Structured error information for user feedback"""

    def __init__(self, error_type: str, message: str, details: str = "", suggestions: List[str] = None):
        self.error_type = error_type
        self.message = message
        self.details = details
        self.suggestions = suggestions or []

    def to_dict(self) -> Dict:
        return {
            'error_type': self.error_type,
            'message': self.message,
            'details': self.details,
            'suggestions': self.suggestions
        }

class BirdDetectionService:
    """Enhanced service for detecting birds using multiple YOLO versions"""
    
    def __init__(self, preferred_version: str = 'YOLO_V8'):
        self.models = {}  # Cache for different YOLO versions
        self.current_model = None
        self.current_version = preferred_version
        self.device = 'cuda' if torch and torch.cuda.is_available() else 'cpu'
        # Use module-level configuration
        self.confidence_threshold = IMAGE_CONFIG['DEFAULT_CONFIDENCE_THRESHOLD']
        
        # YOLO version configurations
        self.version_configs = {
            'YOLO_V5': {
                'base_model': 'yolov5s.pt',
                'custom_model': 'chinese_egret_model_v5.pt',
                'description': 'YOLOv5 - Fast and lightweight',
                'performance': {'mAP': 0.65, 'fps': 90}
            },
            'YOLO_V8': {
                'base_model': 'yolov8s.pt',
                'custom_model': 'chinese_egret_model_v8.pt',
                'description': 'YOLOv8 - Balanced performance and accuracy',
                'performance': {'mAP': 0.70, 'fps': 75}
            },
            'YOLO_V9': {
                'base_model': 'yolov9c.pt',
                'custom_model': 'chinese_egret_model_v9.pt',
                'description': 'YOLOv9 - Latest and most advanced',
                'performance': {'mAP': 0.75, 'fps': 65}
            },
            'CHINESE_EGRET_V1': {
                'base_model': 'chinese_egret_best.pt',
                'custom_model': 'chinese_egret_best.pt',
                'description': '🏆 Chinese Egret Specialist - Ultra High Performance (99.46% mAP)',
                'performance': {'mAP': 0.9946, 'fps': 75},
                'model_path': 'models/chinese_egret_v1/chinese_egret_best.pt',
                'onnx_path': 'models/chinese_egret_v1/chinese_egret_best.onnx',
                'trained_classes': ['chinese_egret'],
                'training_images': 1198,
                'validation_accuracy': {'precision': 0.9735, 'recall': 0.9912},
                'specialty': 'Chinese Egret Detection',
                'recommended': True
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
            # Env override: AVICAST_MODEL_WEIGHTS (absolute or relative to project root)
            env_path = os.getenv('AVICAST_MODEL_WEIGHTS')
            if env_path:
                override_path = Path(env_path)
                if not override_path.is_absolute():
                    override_path = project_root / override_path
                if override_path.exists():
                    logger.info(f"Loading {version} model from env override: {override_path}")
                    return YOLO(str(override_path))

            # Special handling for the new Chinese Egret model
            if version == 'CHINESE_EGRET_V1':
                model_path = project_root / config['model_path']
                if model_path.exists():
                    logger.info(f"🏆 Loading Chinese Egret Specialist model from: {model_path}")
                    logger.info(f"🎯 Performance: {config['performance']['mAP']:.1%} mAP, {config['performance']['fps']} FPS")
                    return YOLO(str(model_path))
                else:
                    logger.error(f"❌ Chinese Egret model not found at: {model_path}")
                    return None
            
            # Auto-discover: newest best.pt under training/runs/**/weights/best.pt
            training_runs = project_root / 'training' / 'runs'
            if training_runs.exists():
                best_candidates = list(training_runs.rglob('weights/best.pt'))
                if best_candidates:
                    latest_best = max(best_candidates, key=lambda p: p.stat().st_mtime)
                    logger.info(f"Auto-discovered latest training model: {latest_best}")
                    return YOLO(str(latest_best))
            
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
            error = DetectionError(
                error_type="NO_MODEL_AVAILABLE",
                message="No detection model available",
                details="All YOLO models failed to load or are not available",
                suggestions=[
                    "Check if YOLO model files exist in the models/ directory",
                    "Verify that ultralytics package is installed",
                    "Check system requirements (CUDA, PyTorch)",
                    "Restart the application to retry model loading"
                ]
            )
            return self._create_error_result(error)
        
        try:
            logger.info(f"Processing image: {image_filename or 'unknown'} with {used_version}")

            # Validate image content
            if not image_content or len(image_content) == 0:
                error = DetectionError(
                    error_type="EMPTY_IMAGE",
                    message="Image file is empty or corrupted",
                    details="The uploaded image contains no data",
                    suggestions=[
                        "Re-upload the image file",
                        "Check if the original file is corrupted",
                        "Try a different image format (JPG, PNG)",
                        "Ensure the file size is greater than 0 bytes"
                    ]
                )
                return self._create_error_result(error)

            # Convert bytes to PIL Image
            try:
                image = Image.open(io.BytesIO(image_content))
            except Exception as e:
                error = DetectionError(
                    error_type="INVALID_IMAGE_FORMAT",
                    message="Image format not supported or corrupted",
                    details=f"Failed to open image: {str(e)}",
                    suggestions=[
                        "Use supported formats: JPG, JPEG, PNG, GIF",
                        "Check if the file is actually an image",
                        "Try converting the image to a different format",
                        "Re-upload the original image file"
                    ]
                )
                return self._create_error_result(error)

            # Validate image dimensions
            width, height = image.size
            min_dims = IMAGE_CONFIG['MIN_IMAGE_DIMENSIONS']
            if width < min_dims[0] or height < min_dims[1]:
                error = DetectionError(
                    error_type="IMAGE_TOO_SMALL",
                    message="Image is too small for reliable detection",
                    details=f"Image dimensions: {width}x{height} pixels (minimum: {min_dims[0]}x{min_dims[1]})",
                    suggestions=[
                        f"Use images with dimensions at least {min_dims[0]}x{min_dims[1]} pixels",
                        "Higher resolution images provide better detection accuracy",
                        "Consider resizing small images before upload"
                    ]
                )
                return self._create_error_result(error)

            max_dims = IMAGE_CONFIG['MAX_IMAGE_DIMENSIONS']
            if width > max_dims[0] or height > max_dims[1]:
                error = DetectionError(
                    error_type="IMAGE_TOO_LARGE",
                    message="Image is too large and may cause memory issues",
                    details=f"Image dimensions: {width}x{height} pixels (maximum: {max_dims[0]}x{max_dims[1]})",
                    suggestions=[
                        f"Resize the image to under {max_dims[0]}x{max_dims[1]} pixels",
                        "Use image compression tools to reduce file size",
                        "Consider using a smaller image for faster processing"
                    ]
                )
                return self._create_error_result(error)
            
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

            # Check if no detections were found
            if not detections:
                # Analyze why no detections
                analysis = self._analyze_no_detections(image, used_version)

                result = {
                    'success': True,
                    'detections': [],
                    'best_detection': None,
                    'total_detections': 0,
                    'model_used': f"{used_version}_{Path(detection_model.ckpt_path).name if hasattr(detection_model, 'ckpt_path') else 'unknown'}",
                    'model_version': used_version,
                    'device_used': self.device,
                    'confidence_threshold': self.confidence_threshold,
                    'no_detection_analysis': analysis,
                    'image_analysis': {
                        'dimensions': f"{width}x{height}",
                        'file_size_bytes': len(image_content),
                        'format': image.format,
                        'mode': image.mode
                    }
                }

                logger.info(f"No detections found with {used_version}. Analysis: {analysis['reason']}")
                return result

            # Create result with proper detection count and model info
            result = {
                'success': True,
                'detections': detections,
                'best_detection': best_detection,
                'total_detections': len(detections),
                'model_used': f"{used_version}_{Path(detection_model.ckpt_path).name if hasattr(detection_model, 'ckpt_path') else 'unknown'}",
                'model_version': used_version,
                'device_used': self.device,
                'confidence_threshold': self.confidence_threshold,
                'image_analysis': {
                    'dimensions': f"{width}x{height}",
                    'file_size_bytes': len(image_content),
                    'format': image.format,
                    'mode': image.mode
                }
            }

            logger.info(f"Detection completed with {used_version}: {len(detections)} birds found")
            return result
            
        except Exception as e:
            logger.error(f"Error during detection with {used_version}: {e}")
            error = DetectionError(
                error_type="DETECTION_FAILED",
                message="Bird detection failed unexpectedly",
                details=f"Error during detection with {used_version}: {str(e)}",
                suggestions=[
                    "Check if the image file is corrupted",
                    "Try uploading a different image",
                    "Verify the model is properly loaded",
                    "Check system resources (memory, GPU)",
                    "Contact support if the issue persists"
                ]
            )
            return self._create_error_result(error)
    
    def _create_error_result(self, error: DetectionError) -> Dict:
        """Create an error result dictionary with structured error information"""
        return {
            'success': False,
            'error': error.to_dict(),
            'detections': [],
            'best_detection': None,
            'total_detections': 0,
            'model_used': 'unknown',
            'model_version': self.current_version,
            'device_used': self.device,
            'confidence_threshold': self.confidence_threshold,
            'image_analysis': None
        }

    def _analyze_no_detections(self, image: Image.Image, model_version: str) -> Dict:
        """Analyze why no detections were found and provide user guidance"""
        width, height = image.size

        # Check image characteristics
        analysis = {
            'reason': 'unknown',
            'details': '',
            'user_guidance': [],
            'technical_details': {}
        }

        # Check if image is mostly empty/blank
        try:
            # Convert to grayscale and check variance
            gray = image.convert('L')
            if np is not None:
                gray_array = np.array(gray)
                variance = np.var(gray_array)

                variance_thresholds = IMAGE_CONFIG['VARIANCE_THRESHOLDS']
                if variance < variance_thresholds['VERY_LOW']:  # Very low variance indicates mostly uniform image
                    analysis['reason'] = 'IMAGE_TOO_UNIFORM'
                    analysis['details'] = 'Image appears to be mostly blank or uniform in color'
                    analysis['user_guidance'] = [
                        "The image appears to be mostly blank or uniform in color",
                        "Bird detection requires images with visible objects and contrast",
                        "Try uploading an image that clearly shows birds or wildlife",
                        "Ensure the image has good lighting and contrast"
                    ]
                elif variance < variance_thresholds['LOW']:  # Low variance
                    analysis['reason'] = 'LOW_CONTRAST'
                    analysis['details'] = 'Image has low contrast which may affect detection'
                    analysis['user_guidance'] = [
                        "The image has low contrast which may affect bird detection",
                        "Try using images with better lighting and contrast",
                        "Avoid images that are too dark, too bright, or washed out",
                        "Consider adjusting image brightness and contrast before upload"
                    ]
                else:
                    analysis['reason'] = 'NO_BIRDS_DETECTED'
                    analysis['details'] = 'No birds were detected in the image'
                    analysis['user_guidance'] = [
                        "No birds were detected in this image",
                        "The image may not contain any birds",
                        "Birds may be too small, blurry, or obscured",
                        "Try uploading an image with clear, visible birds",
                        "Ensure birds are the main subject of the image"
                    ]

                analysis['technical_details'] = {
                    'image_variance': float(variance),
                    'image_dimensions': f"{width}x{height}",
                    'model_version': model_version,
                    'confidence_threshold': self.confidence_threshold
                }
            else:
                # NumPy not available, basic analysis
                analysis['reason'] = 'NO_BIRDS_DETECTED'
                analysis['details'] = 'No birds were detected in the image'
                analysis['user_guidance'] = [
                    "No birds were detected in this image",
                    "Try uploading an image with clear, visible birds",
                    "Ensure birds are the main subject of the image"
                ]
                analysis['technical_details'] = {
                    'image_dimensions': f"{width}x{height}",
                    'model_version': model_version,
                    'confidence_threshold': self.confidence_threshold
                }

        except Exception as e:
            analysis['reason'] = 'ANALYSIS_FAILED'
            analysis['details'] = f'Could not analyze image: {str(e)}'
            analysis['user_guidance'] = [
                "Unable to analyze the image automatically",
                "Try uploading a different image",
                "Ensure the image format is supported"
            ]

        return analysis
    
    def get_detection_health_status(self) -> Dict:
        """Get comprehensive health status of the detection system"""
        health_status = {
            'overall_status': 'HEALTHY',
            'models_loaded': len(self.models),
            'current_model': self.current_version,
            'device': self.device,
            'confidence_threshold': self.confidence_threshold,
            'issues': [],
            'recommendations': []
        }
        
        # Check model availability
        if not self.models:
            health_status['overall_status'] = 'CRITICAL'
            health_status['issues'].append({
                'type': 'NO_MODELS',
                'severity': 'CRITICAL',
                'message': 'No YOLO models are loaded',
                'impact': 'Bird detection will not work'
            })
            health_status['recommendations'].append('Check model files in models/ directory')
        
        # Check device availability
        if self.device == 'cpu' and torch and torch.cuda.is_available():
            health_status['issues'].append({
                'type': 'GPU_NOT_USED',
                'severity': 'WARNING',
                'message': 'GPU available but using CPU',
                'impact': 'Slower detection performance'
            })
            health_status['recommendations'].append('Check CUDA installation and PyTorch GPU support')
        
        # Check model versions
        expected_models = ['YOLO_V5', 'YOLO_V8', 'YOLO_V9']
        missing_models = [model for model in expected_models if model not in self.models]
        if missing_models:
            health_status['issues'].append({
                'type': 'MISSING_MODELS',
                'severity': 'WARNING',
                'message': f'Missing models: {", ".join(missing_models)}',
                'impact': 'Limited model selection options'
            })
            health_status['recommendations'].append(f'Download missing models: {", ".join(missing_models)}')
        
        # Determine overall status
        if any(issue['severity'] == 'CRITICAL' for issue in health_status['issues']):
            health_status['overall_status'] = 'CRITICAL'
        elif any(issue['severity'] == 'WARNING' for issue in health_status['issues']):
            health_status['overall_status'] = 'WARNING'
        
        return health_status
    
    def get_user_friendly_error_summary(self, detection_result: Dict) -> Dict:
        """Convert technical detection results into user-friendly error summaries"""
        if detection_result.get('success', True):
            if detection_result.get('total_detections', 0) == 0:
                # No detections case
                analysis = detection_result.get('no_detection_analysis', {})
                return {
                    'type': 'NO_DETECTIONS',
                    'title': 'No Birds Detected',
                    'message': analysis.get('details', 'No birds were detected in this image'),
                    'severity': 'INFO',
                    'user_guidance': analysis.get('user_guidance', []),
                    'technical_details': analysis.get('technical_details', {}),
                    'icon': '🐦❌'
                }
            else:
                # Successful detections
                return {
                    'type': 'SUCCESS',
                    'title': f'{detection_result["total_detections"]} Bird(s) Detected',
                    'message': 'Bird detection completed successfully',
                    'severity': 'SUCCESS',
                    'user_guidance': [],
                    'technical_details': detection_result.get('image_analysis', {}),
                    'icon': '✅🐦'
                }
        else:
            # Error case
            error = detection_result.get('error', {})
            return {
                'type': 'ERROR',
                'title': 'Detection Failed',
                'message': error.get('message', 'An error occurred during detection'),
                'severity': 'ERROR',
                'user_guidance': error.get('suggestions', []),
                'technical_details': {
                    'error_type': error.get('error_type', 'UNKNOWN'),
                    'details': error.get('details', '')
                },
                'icon': '❌'
            }
    
    def get_model_info(self) -> Dict:
        """Get comprehensive information about all models"""
        current_config = self.version_configs.get(self.current_version, {})
        
        # Highlight Chinese Egret model performance
        chinese_egret_available = 'CHINESE_EGRET_V1' in self.models
        chinese_egret_performance = None
        if chinese_egret_available:
            chinese_egret_performance = self.version_configs['CHINESE_EGRET_V1']['performance']
        
        return {
            'current_version': self.current_version,
            'current_description': current_config.get('description', 'Unknown model'),
            'current_performance': current_config.get('performance', {}),
            'device': self.device,
            'confidence_threshold': self.confidence_threshold,
            'available_models': self.get_available_models(),
            'total_models': len(self.models),
            'available': len(self.models) > 0,
            'chinese_egret_specialist': {
                'available': chinese_egret_available,
                'performance': chinese_egret_performance,
                'recommended': chinese_egret_available,
                'status': '🏆 Ultra High Performance' if chinese_egret_available else '❌ Not Available'
            }
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


