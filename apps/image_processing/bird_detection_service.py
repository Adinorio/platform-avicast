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

    def __init__(self, model_path: Optional[str] = None, confidence_threshold: float = 0.3):
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

    def _preprocess_image(self, image: Image.Image) -> Tuple[np.ndarray, Dict]:
        """
        Enhanced image preprocessing for better detection accuracy

        Args:
            image: PIL Image object

        Returns:
            Tuple of (preprocessed numpy array, scaling information)
        """
        # Store original dimensions for coordinate scaling
        original_width, original_height = image.size
        
        # Resize to optimal input size while maintaining aspect ratio
        processed_image = ImageOps.fit(image, self.image_size, Image.Resampling.LANCZOS)
        
        # Calculate scaling factors for coordinate transformation
        # These factors convert from processed space (640x640) back to original space
        scale_x = original_width / self.image_size[0]  # original_width / 640
        scale_y = original_height / self.image_size[1]  # original_height / 640
        
        # Calculate padding offsets (ImageOps.fit centers the image)
        # When aspect ratio doesn't match, ImageOps.fit adds padding
        if original_width / original_height > self.image_size[0] / self.image_size[1]:
            # Image is wider than target ratio - padding added top/bottom
            padding_x = 0
            padding_y = (self.image_size[1] - (original_height * self.image_size[0] / original_width)) / 2
        else:
            # Image is taller than target ratio - padding added left/right
            padding_x = (self.image_size[0] - (original_width * self.image_size[1] / original_height)) / 2
            padding_y = 0
        
        # Store scaling information for coordinate transformation
        scaling_info = {
            'original_width': original_width,
            'original_height': original_height,
            'processed_width': self.image_size[0],
            'processed_height': self.image_size[1],
            'scale_x': scale_x,
            'scale_y': scale_y,
            'padding_x': padding_x,
            'padding_y': padding_y
        }

        # Convert to numpy array
        image_array = np.array(processed_image)

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

        return image_array, scaling_info

    def _transform_coordinates_to_original(self, detections: List[Dict], scaling_info: Dict) -> List[Dict]:
        """
        Transform bounding box coordinates from model space back to original image space
        
        Args:
            detections: List of detection dictionaries with coordinates in model space
            scaling_info: Dictionary containing scaling and padding information
            
        Returns:
            List of detections with coordinates transformed to original image space
        """
        transformed_detections = []
        
        # Log transformation parameters for debugging
        logger.debug(f"Coordinate transformation: original={scaling_info['original_width']}x{scaling_info['original_height']}, "
                    f"processed={scaling_info['processed_width']}x{scaling_info['processed_height']}, "
                    f"scale=({scaling_info['scale_x']:.3f}, {scaling_info['scale_y']:.3f}), "
                    f"padding=({scaling_info['padding_x']:.1f}, {scaling_info['padding_y']:.1f})")
        
        for detection in detections:
            bbox = detection["bounding_box"].copy()
            
            # Log original coordinates
            logger.debug(f"Original bbox: x={bbox['x']}, y={bbox['y']}, w={bbox['width']}, h={bbox['height']}")
            
            # CORRECTED TRANSFORMATION LOGIC:
            # ImageOps.fit() scales the image to fit the target size while maintaining aspect ratio,
            # then centers it. The key insight is that we need to account for the actual scaling
            # that was applied, not just the target size.
            
            # Calculate the actual scale factors that were applied during ImageOps.fit()
            # These are different from the target scale factors
            if scaling_info['original_width'] / scaling_info['original_height'] > scaling_info['processed_width'] / scaling_info['processed_height']:
                # Wide image - scaled by height, centered horizontally
                actual_scale = scaling_info['original_height'] / scaling_info['processed_height']
                # The image was scaled to fit the height, so width was scaled by the same factor
                scaled_width = scaling_info['original_width'] / actual_scale
                # Calculate horizontal padding (how much of the target width is padding)
                horizontal_padding = (scaling_info['processed_width'] - scaled_width) / 2
                # Transform coordinates
                x_original = (bbox["x"] - horizontal_padding) * actual_scale
                y_original = bbox["y"] * actual_scale
                width_scaled = bbox["width"] * actual_scale
                height_scaled = bbox["height"] * actual_scale
            else:
                # Tall image - scaled by width, centered vertically
                actual_scale = scaling_info['original_width'] / scaling_info['processed_width']
                # The image was scaled to fit the width, so height was scaled by the same factor
                scaled_height = scaling_info['original_height'] / actual_scale
                # Calculate vertical padding (how much of the target height is padding)
                vertical_padding = (scaling_info['processed_height'] - scaled_height) / 2
                # Transform coordinates
                x_original = bbox["x"] * actual_scale
                y_original = (bbox["y"] - vertical_padding) * actual_scale
                width_scaled = bbox["width"] * actual_scale
                height_scaled = bbox["height"] * actual_scale
            
            # Ensure coordinates are within original image bounds
            x_final = max(0, min(int(x_original), scaling_info["original_width"] - 1))
            y_final = max(0, min(int(y_original), scaling_info["original_height"] - 1))
            width_final = max(1, min(int(width_scaled), scaling_info["original_width"] - x_final))
            height_final = max(1, min(int(height_scaled), scaling_info["original_height"] - y_final))
            
            # Log transformed coordinates
            logger.debug(f"Transformed bbox: x={x_final}, y={y_final}, w={width_final}, h={height_final}")
            
            # Create transformed detection
            transformed_detection = detection.copy()
            transformed_detection["bounding_box"] = {
                "x": x_final,
                "y": y_final,
                "width": width_final,
                "height": height_final
            }
            
            transformed_detections.append(transformed_detection)
            
        return transformed_detections

    def _postprocess_detections(self, detections: List[Dict], scaling_info: Dict) -> List[Dict]:
        """
        Enhanced post-processing for better detection accuracy

        Args:
            detections: Raw detection results
            scaling_info: Dictionary containing scaling and padding information

        Returns:
            Filtered and improved detections with coordinates in original image space
        """
        # Filter by confidence threshold
        logger.info(f"Filtering {len(detections)} detections by confidence threshold {self.confidence_threshold}")
        for i, det in enumerate(detections):
            logger.info(f"  Detection {i}: {det['species']} confidence {det['confidence']:.3f} {'PASS' if det['confidence'] >= self.confidence_threshold else 'FILTERED'}")
        
        filtered_detections = [
            d for d in detections
            if d["confidence"] >= self.confidence_threshold
        ]
        
        logger.info(f"After confidence filtering: {len(filtered_detections)} detections remain")

        # Apply Non-Maximum Suppression (NMS) for overlapping boxes
        if len(filtered_detections) > 1:
            filtered_detections = self._apply_nms(filtered_detections)

        # Transform coordinates from model space to original image space
        transformed_detections = self._transform_coordinates_to_original(filtered_detections, scaling_info)

        return transformed_detections

    def _apply_nms(self, detections: List[Dict], iou_threshold: float = 0.3) -> List[Dict]:
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

        logger.info(f"Applying NMS to {len(detections)} detections with IoU threshold {iou_threshold}")

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
                logger.debug(f"IoU between {current['species']} and {other['species']}: {iou:.3f}")
                if iou <= iou_threshold:
                    remaining.append(other)
                else:
                    logger.info(f"Suppressing {other['species']} due to high IoU ({iou:.3f} > {iou_threshold})")

            detections_sorted = remaining

        logger.info(f"NMS result: {len(keep)} detections kept from {len(detections)} original")
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

            # Enhanced preprocessing with scaling information
            image_array, scaling_info = self._preprocess_image(image)

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

            # Apply enhanced post-processing with coordinate transformation
            logger.info(f"BEFORE post-processing: {len(detections)} detections found")
            for i, det in enumerate(detections):
                logger.info(f"  Detection {i}: {det['species']} (conf: {det['confidence']:.3f}) at {det['bounding_box']}")
            
            detections = self._postprocess_detections(detections, scaling_info)

            logger.info(f"AFTER post-processing: {len(detections)} detections remaining")
            for i, det in enumerate(detections):
                logger.info(f"  Detection {i}: {det['species']} (conf: {det['confidence']:.3f}) at {det['bounding_box']}")

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
