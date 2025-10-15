"""
Optimized Bird Detection Service for Egret Species Identification
Enhanced YOLO model integration with performance optimizations
"""

import io
import logging
import os
import gc
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import cv2
import numpy as np
import torch
from django.conf import settings
from PIL import Image, ImageOps
from ultralytics import YOLO

logger = logging.getLogger(__name__)


class BirdDetectionService:
    """
    Service class for bird detection using YOLO models
    """

    def __init__(self, model_path: Optional[str] = None, confidence_threshold: float = 0.5):
        """
        Initialize the optimized bird detection service

        Args:
            model_path: Path to the YOLO model file (.pt format)
            confidence_threshold: Minimum confidence score for detections
        """
        self.confidence_threshold = confidence_threshold
        self.device = self._get_optimal_device()
        self.model = None
        self.model_path = self._get_model_path(model_path)
        self.model_cache = {}  # Cache for loaded models

        # Enhanced species mapping with confidence weighting
        self.species_display_names = {
            "Chinese_Egret": "Chinese Egret",
            "Great_Egret": "Great Egret",
            "Intermediate_Egret": "Intermediate Egret",
            "Little_Egret": "Little Egret",
            "Pacific_Reef_Heron": "Pacific Reef Heron",
            "Western_Cattle_Egret": "Western Cattle Egret"
        }

        # Performance optimization settings
        self.enable_half_precision = True  # Use FP16 for faster inference
        self.enable_model_warmup = True    # Warm up model for better performance
        self.max_batch_size = 4            # Process multiple images together
        self.image_size = (640, 640)       # Optimal input size

        self._load_model()

    def _get_optimal_device(self) -> str:
        """
        Get the optimal device for model inference

        Returns:
            Optimal device string ('cuda', 'cpu', 'mps')
        """
        # Check for CUDA (NVIDIA GPU)
        if torch.cuda.is_available():
            gpu_count = torch.cuda.device_count()
            if gpu_count > 0:
                # Use GPU with most available memory
                max_memory = 0
                best_device = 0
                for i in range(gpu_count):
                    memory = torch.cuda.get_device_properties(i).total_memory
                    if memory > max_memory:
                        max_memory = memory
                        best_device = i
                logger.info(f"Using CUDA device {best_device} with {max_memory // 1024**3}GB memory")
                return f"cuda:{best_device}"

        # Check for MPS (Apple Silicon)
        if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            logger.info("Using MPS device (Apple Silicon)")
            return "mps"

        # Fallback to CPU
        logger.info("Using CPU device")
        return "cpu"

    def _get_model_path(self, model_path: Optional[str] = None) -> str:
        """
        Determine the model path to use

        Args:
            model_path: Optional custom model path

        Returns:
            Path to the model file
        """
        if model_path and Path(model_path).exists():
            return model_path

        # Default to the custom egret model
        default_model = Path(settings.BASE_DIR) / "egret_500_model" / "weights" / "best.pt"
        if default_model.exists():
            return str(default_model)

        # Fallback to any available model
        models_dir = Path(settings.BASE_DIR) / "models"
        if models_dir.exists():
            for model_file in models_dir.rglob("*.pt"):
                return str(model_file)

        raise FileNotFoundError("No YOLO model found. Please ensure a model file (.pt) is available.")

    def _load_model(self):
        """Load and optimize the YOLO model"""
        try:
            logger.info(f"Loading optimized YOLO model from: {self.model_path}")

            # Check cache first
            cache_key = f"{self.model_path}_{self.device}"
            if cache_key in self.model_cache:
                self.model = self.model_cache[cache_key]
                logger.info("Using cached model")
                return

            # Load model with optimizations
            self.model = YOLO(self.model_path)

            # Move to optimal device
            if self.device.startswith('cuda'):
                # Enable CUDA optimizations
                torch.cuda.empty_cache()

            # Enable half precision for faster inference (if supported)
            if self.enable_half_precision and self.device.startswith('cuda'):
                try:
                    # Check if model supports half precision
                    if hasattr(self.model.model, 'half'):
                        self.model = self.model.half()  # Convert to FP16
                        logger.info("Enabled half precision (FP16) for faster inference")
                    else:
                        logger.warning("Model does not support half precision")
                except Exception as e:
                    logger.warning(f"Half precision not available: {e}")

            # Warm up model for better performance
            if self.enable_model_warmup:
                try:
                    # Create a dummy image for warmup
                    dummy_image = np.zeros((640, 640, 3), dtype=np.uint8)
                    _ = self.model(dummy_image, verbose=False)
                    logger.info("Model warmup completed")
                except Exception as e:
                    logger.warning(f"Model warmup failed: {e}")

            # Cache the loaded model
            self.model_cache[cache_key] = self.model

            logger.info(f"Model loaded and optimized on device: {self.device}")

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise RuntimeError(f"Model loading failed: {e}")

    def is_available(self) -> bool:
        """Check if the service is ready for use"""
        return self.model is not None

    def _preprocess_image(self, image: Image.Image) -> np.ndarray:
        """
        Enhanced image preprocessing for better detection accuracy

        Args:
            image: PIL Image object

        Returns:
            Preprocessed numpy array
        """
        # Resize to optimal input size while maintaining aspect ratio
        image = ImageOps.fit(image, self.image_size, Image.Resampling.LANCZOS)

        # Convert to numpy array
        image_array = np.array(image)

        # Enhanced preprocessing pipeline
        if image_array.shape[-1] == 4:  # RGBA
            # Better RGBA to RGB conversion
            image_array = cv2.cvtColor(image_array, cv2.COLOR_RGBA2RGB)
        elif len(image_array.shape) == 2:  # Grayscale
            image_array = cv2.cvtColor(image_array, cv2.COLOR_GRAY2RGB)

        # Normalize pixel values for better model performance
        image_array = image_array.astype(np.float32) / 255.0

        # Apply slight contrast enhancement for better feature detection
        image_array = np.clip(image_array * 1.1, 0, 1)  # Increase contrast by 10%

        # Convert back to uint8 for YOLO model
        image_array = (image_array * 255).astype(np.uint8)

        return image_array

    def _postprocess_detections(self, detections: List[Dict], image_width: int, image_height: int) -> List[Dict]:
        """
        Enhanced post-processing for better detection accuracy

        Args:
            detections: Raw detection results
            image_width: Original image width
            image_height: Original image height

        Returns:
            Filtered and improved detections
        """
        # Filter by confidence threshold
        filtered_detections = [
            d for d in detections
            if d["confidence"] >= self.confidence_threshold
        ]

        # Apply Non-Maximum Suppression (NMS) for overlapping boxes
        if len(filtered_detections) > 1:
            filtered_detections = self._apply_nms(filtered_detections)

        # Scale bounding boxes back to original image size
        for detection in filtered_detections:
            # Bounding boxes are already in original image coordinates
            # Ensure they don't exceed image boundaries
            bbox = detection["bounding_box"]
            bbox["x"] = max(0, min(bbox["x"], image_width - 1))
            bbox["y"] = max(0, min(bbox["y"], image_height - 1))
            bbox["width"] = min(bbox["width"], image_width - bbox["x"])
            bbox["height"] = min(bbox["height"], image_height - bbox["y"])

        return filtered_detections

    def _apply_nms(self, detections: List[Dict], iou_threshold: float = 0.45) -> List[Dict]:
        """
        Apply Non-Maximum Suppression to remove overlapping bounding boxes

        Args:
            detections: List of detection dictionaries
            iou_threshold: IoU threshold for suppression

        Returns:
            Filtered detections after NMS
        """
        if len(detections) <= 1:
            return detections

        # Sort by confidence (highest first)
        detections_sorted = sorted(detections, key=lambda x: x["confidence"], reverse=True)

        # Calculate IoU for each pair of boxes
        keep = []
        while detections_sorted:
            # Keep the box with highest confidence
            current = detections_sorted.pop(0)
            keep.append(current)

            # Remove boxes with high IoU
            remaining = []
            for other in detections_sorted:
                iou = self._calculate_iou(current["bounding_box"], other["bounding_box"])
                if iou <= iou_threshold:
                    remaining.append(other)

            detections_sorted = remaining

        return keep

    def _calculate_iou(self, box1: Dict, box2: Dict) -> float:
        """
        Calculate Intersection over Union (IoU) between two bounding boxes

        Args:
            box1: First bounding box dictionary
            box2: Second bounding box dictionary

        Returns:
            IoU score between 0 and 1
        """
        # Convert to coordinates
        x1_1, y1_1 = box1["x"], box1["y"]
        x2_1, y2_1 = x1_1 + box1["width"], y1_1 + box1["height"]

        x1_2, y1_2 = box2["x"], box2["y"]
        x2_2, y2_2 = x1_2 + box2["width"], y1_2 + box2["height"]

        # Calculate intersection area
        x1_i = max(x1_1, x1_2)
        y1_i = max(y1_1, y1_2)
        x2_i = min(x2_1, x2_2)
        y2_i = min(y2_1, y2_2)

        if x2_i <= x1_i or y2_i <= y1_i:
            return 0.0

        intersection_area = (x2_i - x1_i) * (y2_i - y1_i)

        # Calculate union area
        area1 = box1["width"] * box1["height"]
        area2 = box2["width"] * box2["height"]
        union_area = area1 + area2 - intersection_area

        if union_area <= 0:
            return 0.0

        return intersection_area / union_area

    def detect_birds(self, image_data: bytes, filename: str = "unknown") -> Dict:
        """
        Detect birds in the given image

        Args:
            image_data: Raw image bytes (JPEG/PNG format)
            filename: Original filename for logging

        Returns:
            Detection results dictionary
        """
        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_data))

            # Enhanced preprocessing
            image_array = self._preprocess_image(image)

            # Clear GPU cache before inference
            if self.device.startswith('cuda'):
                torch.cuda.empty_cache()

            # Run optimized inference
            results = self.model(
                image_array,
                conf=self.confidence_threshold,
                device=self.device,
                half=self.enable_half_precision and self.device.startswith('cuda'),
                verbose=False  # Reduce logging noise
            )

            # Process results
            detections = []
            total_detections = 0
            egret_detections = 0

            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for i, box in enumerate(boxes):
                        # Get bounding box coordinates
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        confidence = float(box.conf[0].cpu().numpy())
                        class_id = int(box.cls[0].cpu().numpy())

                        # Get class name
                        class_name = self.model.names[class_id]

                        # Map to display name if available
                        display_name = self.species_display_names.get(class_name, class_name)

                        # Only count egret species for total_detections
                        if display_name in self.species_display_names.values():
                            egret_detections += 1

                        detection = {
                            "id": i,
                            "species": display_name,
                            "confidence": confidence,
                            "bounding_box": {
                                "x": int(x1),
                                "y": int(y1),
                                "width": int(x2 - x1),
                                "height": int(y2 - y1)
                            }
                        }
                        detections.append(detection)

            # Apply enhanced post-processing
            detections = self._postprocess_detections(detections, image.width, image.height)

            # Recount egret detections after filtering
            egret_detections = sum(1 for d in detections if d["species"] in self.species_display_names.values())

            # Determine primary species (highest confidence egret detection)
            primary_species = None
            primary_confidence = 0.0

            egret_detections_list = [d for d in detections if d["species"] in self.species_display_names.values()]
            for detection in egret_detections_list:
                if detection["confidence"] > primary_confidence:
                    primary_species = detection["species"]
                    primary_confidence = detection["confidence"]

            # Memory cleanup
            if self.device.startswith('cuda'):
                torch.cuda.empty_cache()
            gc.collect()

            logger.info(f"Detection completed for {filename}: {len(detections)} total, {egret_detections} egrets")

            return {
                "success": True,
                "detections": detections,
                "total_detections": egret_detections,
                "primary_species": primary_species,
                "primary_confidence": primary_confidence,
                "model_used": Path(self.model_path).name,
                "device_used": self.device,
                "processing_time": 0,  # Could measure if needed
            }

        except Exception as e:
            logger.error(f"Detection failed for {filename}: {e}")
            # Memory cleanup on error
            if self.device.startswith('cuda'):
                torch.cuda.empty_cache()
            gc.collect()

            return {
                "success": False,
                "error": str(e),
                "detections": [],
                "total_detections": 0,
                "primary_species": None,
                "primary_confidence": 0.0,
                "model_used": "ERROR",
                "device_used": self.device,
            }

    def get_model_info(self) -> Dict:
        """Get information about the loaded model"""
        if not self.model:
            return {"error": "No model loaded"}

        return {
            "model_path": self.model_path,
            "device": self.device,
            "confidence_threshold": self.confidence_threshold,
            "class_names": self.species_display_names,
            "num_classes": len(self.model.names)
        }


# Singleton instance
_bird_detection_service = None


def get_bird_detection_service(model_path: Optional[str] = None) -> BirdDetectionService:
    """
    Get or create the bird detection service instance

    Args:
        model_path: Optional custom model path

    Returns:
        BirdDetectionService instance
    """
    global _bird_detection_service

    if _bird_detection_service is None or (model_path and model_path != _bird_detection_service.model_path):
        _bird_detection_service = BirdDetectionService(model_path)

    return _bird_detection_service


def reset_bird_detection_service():
    """Reset the singleton instance (useful for testing)"""
    global _bird_detection_service
    _bird_detection_service = None
