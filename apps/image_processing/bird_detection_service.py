"""
Enhanced Bird Detection Service using multiple YOLO versions
Supports YOLOv5, YOLOv8, and YOLOv9 with automatic fallback
"""

import json
import logging
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

# Add the bird_detection directory to Python path
project_root = Path(__file__).parent.parent.parent
bird_detection_path = project_root / "bird_detection"
sys.path.insert(0, str(bird_detection_path))

try:
    import io

    import cv2
    import numpy as np
    import torch
    from PIL import Image
    from ultralytics import YOLO
except ImportError as e:
    logging.error(f"Required packages not installed: {e}")
    YOLO = None
    torch = None
    cv2 = None
    np = None
    Image = None

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Decision policy for acceptance/abstain of detections
# -----------------------------------------------------------------------------

# Minimum detector confidence to accept a detection (tuned for unified model)
DETECTION_CONF_THRESHOLD: float = 0.50

# Minimum crop side (in pixels) to accept a detection (guards small/ambiguous crops)
DETECTION_MIN_CROP_SIDE: int = 96


def decide_detection_gate(
    detector_confidence: float, crop_width_px: int, crop_height_px: int
) -> tuple[str, str]:
    """Decide whether to accept a detection based on detector confidence and crop size.

    Returns a tuple of (status, reason), where status is one of {"ACCEPT", "ABSTAIN"}.
    """
    try:
        min_side = min(int(crop_width_px), int(crop_height_px))
    except Exception:
        # Fallback if values are unexpected
        min_side = 0

    if detector_confidence < DETECTION_CONF_THRESHOLD:
        return "ABSTAIN", "low_confidence_detection"

    if min_side < DETECTION_MIN_CROP_SIDE:
        return "ABSTAIN", "small_crop_min_side"

    return "ACCEPT", "accept_detection"


# -----------------------------------------------------------------------------
# Crop Extraction Helper
# -----------------------------------------------------------------------------


def crop_image(image: Any, bbox: dict) -> Any:
    """
    Crop a region from the image given a YOLO bbox.

    Args:
        image (np.ndarray): Original image (H x W x C).
        bbox (dict): {"x": int, "y": int, "width": int, "height": int}

    Returns:
        np.ndarray: Cropped image.
    """
    x, y, w, h = bbox["x"], bbox["y"], bbox["width"], bbox["height"]
    x2, y2 = x + w, y + h

    # Ensure within image bounds
    h_img, w_img = image.shape[:2]
    x, y = max(0, x), max(0, y)
    x2, y2 = min(w_img, x2), min(h_img, y2)

    return image[y:y2, x:x2]


# -----------------------------------------------------------------------------
# Review Queue for ABSTAIN Cases
# -----------------------------------------------------------------------------

REVIEW_QUEUE_BASE_DIR: str = "review_queue"


def save_abstain_to_review_queue(
    crop: Any, detection: dict, base_dir: str = REVIEW_QUEUE_BASE_DIR
) -> bool:
    """Save ABSTAIN cases with structured folder format: <date>/<uuid>.png + metadata.json"""
    try:
        # If OpenCV is not available, skip saving and return gracefully
        if cv2 is None:
            logger.warning("OpenCV not installed; skipping saving ABSTAIN crop to review queue")
            return False
        # Create date-based folder
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        date_dir = os.path.join(base_dir, date_str)
        os.makedirs(date_dir, exist_ok=True)

        # Generate unique ID for this detection
        detection_id = str(uuid.uuid4())

        # Save cropped image
        image_filename = f"{detection_id}.png"
        image_path = os.path.join(date_dir, image_filename)
        cv2.imwrite(image_path, crop)

        # Prepare metadata entry
        metadata_path = os.path.join(date_dir, "metadata.json")

        # Load existing metadata if file exists
        metadata = []
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path) as f:
                    metadata = json.load(f)
            except Exception:
                metadata = []  # Start fresh if corrupted

        # Create new entry
        entry = {
            "id": detection_id,
            "timestamp": datetime.utcnow().isoformat(),
            "image_file": image_filename,
            "stage1_decision": detection.get("decision", {}),
            "stage2_decision": detection.get("stage2_decision", {}),
            "final_decision": detection.get("final_decision", {}),
            "yolo_conf": detection.get("confidence", None),
            "classifier_probs": detection.get("classifier_probs", {}),
            "crop_size": detection.get("crop_size", ()),
            "source_image": detection.get("source_image", None),
            "site": detection.get("site", None),
            "observer": "auto_pipeline",
        }

        metadata.append(entry)

        # Save updated metadata
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Saved ABSTAIN case to review queue: {image_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to save ABSTAIN case to review queue: {e}")
        return False


# -----------------------------------------------------------------------------
# Stage-2 Classifier Decision Module
# -----------------------------------------------------------------------------

CLASSIFIER_CONF_THRESHOLD: float = 0.80  # Minimum classifier confidence to accept
CLASSIFIER_MARGIN_THRESHOLD: float = 0.25  # Minimum margin between top-2 classes


def decide_classification_gate(
    classifier_probs: dict[str, float], crop_min_side: int
) -> tuple[str, str]:
    """Decide whether to accept a classification based on probabilities and crop size.

    Args:
        classifier_probs: Dict of class_name -> probability (e.g., {"Chinese": 0.85, "Great": 0.10})
        crop_min_side: Minimum side of the crop in pixels

    Returns:
        Tuple[str, str]: (status, reason) where status is "ACCEPT" or "ABSTAIN"
    """
    if not classifier_probs or not isinstance(classifier_probs, dict):
        return "ABSTAIN", "invalid_classifier_output"

    # Check if crop is too small for reliable classification
    if crop_min_side < DETECTION_MIN_CROP_SIDE:
        return "ABSTAIN", "crop_too_small_for_classification"

    # Sort probabilities to find top-2
    sorted_probs = sorted(classifier_probs.items(), key=lambda x: x[1], reverse=True)

    if len(sorted_probs) < 1:
        return "ABSTAIN", "no_classifier_predictions"

    top1_prob = sorted_probs[0][1]
    top2_prob = sorted_probs[1][1] if len(sorted_probs) > 1 else 0.0
    margin = top1_prob - top2_prob

    # Acceptance criteria
    if top1_prob >= CLASSIFIER_CONF_THRESHOLD and margin >= CLASSIFIER_MARGIN_THRESHOLD:
        return "ACCEPT", "high_confidence_classification"
    else:
        return "ABSTAIN", f"low_confidence_or_ambiguous_margin_{top1_prob:.2f}_{margin:.2f}"


# -----------------------------------------------------------------------------
# Mock Classifier for Testing (replace with real classifier)
# -----------------------------------------------------------------------------


def trained_classifier_predict(crop: Any) -> dict[str, float]:
    """Trained classifier using the Stage-2 EfficientNet model."""
    import torch
    import torch.nn as nn
    from PIL import Image
    from torchvision import models, transforms
    import numpy as np

    # Validate crop parameter
    if crop is None or not isinstance(crop, np.ndarray) or crop.size == 0:
        print("⚠️ Invalid crop parameter, falling back to mock")
        return mock_classifier_predict(crop)
    
    # Check crop dimensions
    if len(crop.shape) != 3 or crop.shape[2] != 3:
        print(f"⚠️ Invalid crop shape {crop.shape}, falling back to mock")
        return mock_classifier_predict(crop)
    
    # Check if crop is too small
    if crop.shape[0] < 10 or crop.shape[1] < 10:
        print(f"⚠️ Crop too small {crop.shape}, falling back to mock")
        return mock_classifier_predict(crop)

    # Load the trained model
    model_path = Path(__file__).parent.parent / "models" / "classifier" / "best_model.pth"

    if not model_path.exists():
        print("⚠️ Trained classifier model not found, falling back to mock")
        return mock_classifier_predict(crop)

    try:
        # Load checkpoint
        checkpoint = torch.load(model_path, map_location="cpu", weights_only=False)
        model_name = checkpoint.get("model_name", "efficientnet_b0")
        class_names = checkpoint.get("class_names", ["Chinese Egret", "Intermediate Egret"])

        # Recreate model architecture
        if model_name == "efficientnet_b0":
            model = models.efficientnet_b0(weights=None)
            num_features = model.classifier[1].in_features
            model.classifier[1] = nn.Linear(num_features, len(class_names))
        else:
            print("⚠️ Unsupported model architecture, falling back to mock")
            return mock_classifier_predict(crop)

        # Load trained weights
        model.load_state_dict(checkpoint["model_state_dict"])
        model.eval()

        # Prepare image
        image = Image.fromarray(crop)
        transform = transforms.Compose(
            [
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ]
        )

        with torch.no_grad():
            input_tensor = transform(image).unsqueeze(0)
            outputs = model(input_tensor)
            probabilities = torch.softmax(outputs, dim=1)[0]

        # Convert to expected format (full egret names)
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
                probs_dict[cls] = 0.01  # Very low probability for missing classes

        # Renormalize
        total = sum(probs_dict.values())
        probs_dict = {k: v / total for k, v in probs_dict.items()}

        return probs_dict

    except Exception as e:
        print(f"⚠️ Error loading trained classifier: {e}, falling back to mock")
        return mock_classifier_predict(crop)


def mock_classifier_predict(crop: Any) -> dict[str, float]:
    """Mock classifier that returns random probabilities for testing the pipeline."""
    import random

    classes = ["Chinese", "Great", "Intermediate", "Little"]
    # Simulate realistic probabilities (Chinese egret should be highest in our dataset)
    base_probs = [0.6, 0.25, 0.10, 0.05]  # Chinese dominant
    noise = [random.uniform(-0.1, 0.1) for _ in range(4)]

    probs = [max(0.01, min(0.99, base_probs[i] + noise[i])) for i in range(4)]
    total = sum(probs)
    probs = [p / total for p in probs]  # Normalize

    return dict(zip(classes, probs, strict=False))


# Import configuration at module level
try:
    from .config import IMAGE_CONFIG
except ImportError:
    # Fallback for when config is not available
    IMAGE_CONFIG = {
        "MIN_IMAGE_DIMENSIONS": (50, 50),
        "MAX_IMAGE_DIMENSIONS": (4000, 4000),
        "DEFAULT_CONFIDENCE_THRESHOLD": 0.5,
        "VARIANCE_THRESHOLDS": {"VERY_LOW": 100, "LOW": 500},
    }

# Import model configurations
try:
    from .config import YOLO_VERSION_CONFIGS
except ImportError:
    # Fallback for when config is not available
    YOLO_VERSION_CONFIGS = {
        "YOLO_V8": {
            "base_model": "yolov8s.pt",
            "custom_model": "chinese_egret_model_v8.pt",
            "description": "YOLOv8 - Default fallback model",
            "performance": {"mAP": 0.70, "fps": 75},
        }
    }


class DetectionError:
    """Structured error information for user feedback"""

    def __init__(
        self, error_type: str, message: str, details: str = "", suggestions: list[str] = None
    ):
        self.error_type = error_type
        self.message = message
        self.details = details
        self.suggestions = suggestions or []

    def to_dict(self) -> dict:
        return {
            "error_type": self.error_type,
            "message": self.message,
            "details": self.details,
            "suggestions": self.suggestions,
        }


class BirdDetectionService:
    """Enhanced service for detecting birds using multiple YOLO versions"""

    def __init__(self, preferred_version: str = "YOLO11M_EGRET_MAX_ACCURACY"):
        self.models = {}  # Cache for different YOLO versions
        self.current_model = None
        self.current_version = preferred_version
        self.device = "cuda" if torch and torch.cuda.is_available() else "cpu"
        # Use module-level configuration
        self.confidence_threshold = IMAGE_CONFIG["DEFAULT_CONFIDENCE_THRESHOLD"]

        # YOLO version configurations are now loaded from config.py
        # Restrict to unified egret model only (local-only requirement; AGENTS.md: Model storage)
        base_configs = YOLO_VERSION_CONFIGS
        if "YOLO11M_EGRET_MAX_ACCURACY" in base_configs:
            self.version_configs = {
                "YOLO11M_EGRET_MAX_ACCURACY": base_configs["YOLO11M_EGRET_MAX_ACCURACY"]
            }
            # Adopt model-recommended inference conf if provided
            model_conf = self.version_configs["YOLO11M_EGRET_MAX_ACCURACY"].get(
                "inference_conf"
            )
            if isinstance(model_conf, (int, float)):
                self.confidence_threshold = float(model_conf)
        else:
            self.version_configs = base_configs

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

    def _load_model(self, version: str, config: dict) -> YOLO | None:
        """Load a specific YOLO model version"""
        try:
            # Env override: AVICAST_MODEL_WEIGHTS (absolute or relative to project root)
            env_path = os.getenv("AVICAST_MODEL_WEIGHTS")
            if env_path:
                override_path = Path(env_path)
                if not override_path.is_absolute():
                    override_path = project_root / override_path
                if override_path.exists():
                    if override_path.is_file():
                        logger.info(
                            f"Loading {version} model from env override file: {override_path}"
                        )
                        return YOLO(str(override_path))
                    # If a directory is provided, search recursively for best.pt or any .pt
                    if override_path.is_dir():
                        candidates = list(override_path.rglob("best.pt"))
                        if not candidates:
                            candidates = list(override_path.rglob("*.pt"))
                        if candidates:
                            chosen = max(candidates, key=lambda p: p.stat().st_mtime)
                            logger.info(
                                f"Loading {version} model from env override directory: {chosen}"
                            )
                            return YOLO(str(chosen))

            # Special handling for the new Chinese Egret model
            if version == "CHINESE_EGRET_V1":
                model_path = project_root / config["model_path"]
                if model_path.exists():
                    logger.info(f"🏆 Loading Chinese Egret Specialist model from: {model_path}")
                    logger.info(
                        f"🎯 Performance: {config['performance']['mAP']:.1%} mAP, {config['performance']['fps']} FPS"
                    )
                    return YOLO(str(model_path))
                else:
                    logger.error(f"❌ Chinese Egret model not found at: {model_path}")
                    return None

            # Special handling for YOLO11m Egret Max Accuracy model
            if version == "YOLO11M_EGRET_MAX_ACCURACY":
                model_path = Path(config["model_path"])
                if not model_path.is_absolute():
                    model_path = project_root / model_path
                if model_path.exists():
                    if model_path.is_file():
                        logger.info(
                            f"🚀 Loading YOLO11m Egret Max Accuracy model from: {model_path}"
                        )
                        logger.info(
                            f"🎯 Performance: {config['performance']['mAP']:.1%} mAP, {config['performance']['fps']} FPS"
                        )
                        logger.info(
                            f"📊 Trained on {config['training_images']} images, validated on {config['validation_images']} images"
                        )
                        logger.info(f"🦅 Species: {', '.join(config['trained_classes'])}")
                        return YOLO(str(model_path))
                    # Directory: search inside
                    if model_path.is_dir():
                        candidates = list(model_path.rglob("best.pt"))
                        if not candidates:
                            candidates = list(model_path.rglob("*.pt"))
                        if candidates:
                            chosen = max(candidates, key=lambda p: p.stat().st_mtime)
                            logger.info(
                                f"🚀 Loading YOLO11m Egret Max Accuracy model from directory: {chosen}"
                            )
                            return YOLO(str(chosen))
                logger.error(f"❌ YOLO11m Egret model not found at: {model_path}")
                return None

            # Skip auto-discovery for YOLO11M_EGRET_MAX_ACCURACY - use specific path
            if version != "YOLO11M_EGRET_MAX_ACCURACY":
                # Auto-discover: newest best.pt under training/runs/**/weights/best.pt
                training_runs = project_root / "training" / "runs"
                if training_runs.exists():
                    best_candidates = list(training_runs.rglob("weights/best.pt"))
                    if best_candidates:
                        latest_best = max(best_candidates, key=lambda p: p.stat().st_mtime)
                        logger.info(f"Auto-discovered latest training model: {latest_best}")
                        return YOLO(str(latest_best))

            # Priority 1: Custom trained model for bird detection
            custom_model_paths = [
                project_root / "bird_detection" / config["custom_model"],
                project_root / "runs" / "detect" / "train" / "weights" / "best.pt",
                project_root / "runs" / "detect" / "train2" / "weights" / "best.pt",
                project_root / "runs" / "detect" / "train3" / "weights" / "best.pt",
                project_root / "runs" / "detect" / "train4" / "weights" / "best.pt",
            ]

            for model_path in custom_model_paths:
                if model_path.exists():
                    logger.info(f"Loading custom {version} model from: {model_path}")
                    return YOLO(str(model_path))

            # Priority 2: Base model from ultralytics
            try:
                logger.info(f"Loading base {version} model: {config['base_model']}")
                return YOLO(config["base_model"])
            except Exception as e:
                logger.warning(f"Base {version} model not available: {e}")

            # Priority 3: Local base model file
            local_model_path = project_root / "models" / config["base_model"]
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

    def get_available_models(self) -> dict:
        """Get information about available models"""
        available = {}
        for version, config in self.version_configs.items():
            available[version] = {
                "available": version in self.models,
                "description": config["description"],
                "is_current": version == self.current_version,
            }
        return available

    def detect_birds(
        self, image_content: bytes, image_filename: str = None, model_version: str = None
    ) -> dict:
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
                    "Restart the application to retry model loading",
                ],
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
                        "Ensure the file size is greater than 0 bytes",
                    ],
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
                        "Re-upload the original image file",
                    ],
                )
                return self._create_error_result(error)

            # Validate image dimensions
            width, height = image.size
            min_dims = IMAGE_CONFIG["MIN_IMAGE_DIMENSIONS"]
            if width < min_dims[0] or height < min_dims[1]:
                error = DetectionError(
                    error_type="IMAGE_TOO_SMALL",
                    message="Image is too small for reliable detection",
                    details=f"Image dimensions: {width}x{height} pixels (minimum: {min_dims[0]}x{min_dims[1]})",
                    suggestions=[
                        f"Use images with dimensions at least {min_dims[0]}x{min_dims[1]} pixels",
                        "Higher resolution images provide better detection accuracy",
                        "Consider resizing small images before upload",
                    ],
                )
                return self._create_error_result(error)

            max_dims = IMAGE_CONFIG["MAX_IMAGE_DIMENSIONS"]
            if width > max_dims[0] or height > max_dims[1]:
                error = DetectionError(
                    error_type="IMAGE_TOO_LARGE",
                    message="Image is too large and may cause memory issues",
                    details=f"Image dimensions: {width}x{height} pixels (maximum: {max_dims[0]}x{max_dims[1]})",
                    suggestions=[
                        f"Resize the image to under {max_dims[0]}x{max_dims[1]} pixels",
                        "Use image compression tools to reduce file size",
                        "Consider using a smaller image for faster processing",
                    ],
                )
                return self._create_error_result(error)

            # Convert PIL image to numpy array for cropping
            image_np = np.array(image)

            # Run detection
            results = detection_model(image, conf=self.confidence_threshold, device=self.device)

            # Process results
            detections = []
            for result in results:
                boxes = result.boxes
                if boxes is not None and len(boxes) > 0:
                    for i, box in enumerate(boxes):
                        try:
                            # Get coordinates
                            if hasattr(box, "xyxy") and len(box.xyxy) > 0:
                                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                            else:
                                continue  # Skip if no coordinates

                            if hasattr(box, "conf") and len(box.conf) > 0:
                                confidence = float(box.conf[0].cpu().numpy())
                            else:
                                continue  # Skip if no confidence

                            if hasattr(box, "cls") and len(box.cls) > 0:
                                class_id = int(box.cls[0].cpu().numpy())
                            else:
                                continue  # Skip if no class

                            # Map to unified egret/heron classes when using our unified model
                            class_name = (
                                result.names[class_id]
                                if hasattr(result, "names") and class_id in result.names
                                else f"class_{class_id}"
                            )
                            # Normalize class names for the five target species
                            normalized_map = {
                                "chinese egret": "Chinese Egret",
                                "great egret": "Great Egret",
                                "intermediate egret": "Intermediate Egret",
                                "little egret": "Little Egret",
                                "pacific reef heron": "Pacific Reef Heron",
                                "pacific reef egret": "Pacific Reef Heron",
                                "reef heron": "Pacific Reef Heron",
                            }
                            key_lc = str(class_name).strip().lower().replace("_", " ")
                            class_name = normalized_map.get(key_lc, class_name)

                            # If using the unified egret model, keep only the five target species
                            if used_version == "YOLO11M_EGRET_MAX_ACCURACY":
                                allowed = {
                                    "Chinese Egret",
                                    "Great Egret",
                                    "Intermediate Egret",
                                    "Little Egret",
                                    "Pacific Reef Heron",
                                }
                                if class_name not in allowed:
                                    continue  # Skip non-target classes

                            crop_w = int(x2 - x1)
                            crop_h = int(y2 - y1)

                            # Stage-1: Detection gate
                            decision_status, decision_reason = decide_detection_gate(
                                detector_confidence=confidence,
                                crop_width_px=crop_w,
                                crop_height_px=crop_h,
                            )

                            # Extract crop for Stage-2 classifier
                            bbox = {"x": int(x1), "y": int(y1), "width": crop_w, "height": crop_h}
                            crop = crop_image(image_np, bbox)
                            crop_min_side = min(crop.shape[0], crop.shape[1])

                            # Stage-2: Classifier (bypass when using unified egret model)
                            if used_version == "YOLO11M_EGRET_MAX_ACCURACY":
                                # Build a pseudo-prob vector biased toward the detector class
                                target_classes = [
                                    "Chinese Egret",
                                    "Great Egret",
                                    "Intermediate Egret",
                                    "Little Egret",
                                    "Pacific Reef Heron",
                                ]
                                base = 0.01
                                class_probs = {c: base for c in target_classes}
                                if class_name in class_probs:
                                    class_probs[class_name] = max(confidence, 0.8)
                                # renormalize
                                s = sum(class_probs.values())
                                class_probs = {k: v / s for k, v in class_probs.items()}
                            else:
                                class_probs = trained_classifier_predict(crop)

                            # Stage-2 decision
                            stage2_status, stage2_reason = decide_classification_gate(
                                classifier_probs=class_probs, crop_min_side=crop_min_side
                            )

                            # Final decision: ACCEPT only if both stages pass
                            if decision_status == "ACCEPT" and stage2_status == "ACCEPT":
                                final_status = "ACCEPT"
                                final_reason = "both_stages_passed"
                            else:
                                final_status = "ABSTAIN"
                                final_reason = f"stage1_{decision_reason}_stage2_{stage2_reason}"

                            detection = {
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
                                "decision": {
                                    "status": decision_status,
                                    "reason": decision_reason,
                                    "detector_threshold": DETECTION_CONF_THRESHOLD,
                                    "min_crop_side_px": DETECTION_MIN_CROP_SIDE,
                                },
                                "stage2_decision": {
                                    "status": stage2_status,
                                    "reason": stage2_reason,
                                    "classifier_threshold": CLASSIFIER_CONF_THRESHOLD,
                                    "margin_threshold": CLASSIFIER_MARGIN_THRESHOLD,
                                },
                                "final_decision": {"status": final_status, "reason": final_reason},
                                "classifier_probs": class_probs,
                                "crop_size": (crop.shape[1], crop.shape[0]),  # width, height
                                "source_image": image_filename or "unknown",
                            }

                            # Save ABSTAIN cases to review queue
                            if final_status == "ABSTAIN":
                                save_abstain_to_review_queue(crop, detection)

                            detections.append(detection)

                        except Exception as e:
                            logger.warning(f"Error processing detection {i}: {e}")
                            continue  # Skip this detection and continue with others

            # Get the best detection (highest confidence)
            best_detection = None
            if detections:
                best_detection = max(detections, key=lambda x: x["confidence"])

            # Check if no detections were found
            if not detections:
                # Analyze why no detections
                analysis = self._analyze_no_detections(image, used_version)

                result = {
                    "success": True,
                    "detections": [],
                    "best_detection": None,
                    "total_detections": 0,
                    "model_used": f"{used_version}_{Path(detection_model.ckpt_path).name if hasattr(detection_model, 'ckpt_path') else 'unknown'}",
                    "model_version": used_version,
                    "device_used": self.device,
                    "confidence_threshold": self.confidence_threshold,
                    "no_detection_analysis": analysis,
                    "image_analysis": {
                        "dimensions": f"{width}x{height}",
                        "file_size_bytes": len(image_content),
                        "format": image.format,
                        "mode": image.mode,
                    },
                }

                logger.info(
                    f"No detections found with {used_version}. Analysis: {analysis['reason']}"
                )
                return result

            # Create result with proper detection count and model info
            result = {
                "success": True,
                "detections": detections,
                "best_detection": best_detection,
                "total_detections": len(detections),
                "model_used": f"{used_version}_{Path(detection_model.ckpt_path).name if hasattr(detection_model, 'ckpt_path') else 'unknown'}",
                "model_version": used_version,
                "device_used": self.device,
                "confidence_threshold": self.confidence_threshold,
                "trained_classes": self.version_configs.get(used_version, {}).get("trained_classes", []),
                "image_analysis": {
                    "dimensions": f"{width}x{height}",
                    "file_size_bytes": len(image_content),
                    "format": image.format,
                    "mode": image.mode,
                },
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
                    "Contact support if the issue persists",
                ],
            )
            return self._create_error_result(error)

    def _create_error_result(self, error: DetectionError) -> dict:
        """Create an error result dictionary with structured error information"""
        return {
            "success": False,
            "error": error.to_dict(),
            "detections": [],
            "best_detection": None,
            "total_detections": 0,
            "model_used": "unknown",
            "model_version": self.current_version,
            "device_used": self.device,
            "confidence_threshold": self.confidence_threshold,
            "image_analysis": None,
        }

    def _analyze_no_detections(self, image: Image.Image, model_version: str) -> dict:
        """Analyze why no detections were found and provide user guidance"""
        width, height = image.size

        # Check image characteristics
        analysis = {
            "reason": "unknown",
            "details": "",
            "user_guidance": [],
            "technical_details": {},
        }

        # 1. Check for specialist model mismatch first, as it's a very specific reason.
        model_config = self.version_configs.get(model_version, {})
        trained_classes = model_config.get("trained_classes")
        is_specialist = "specialty" in model_config

        if is_specialist and trained_classes:
            analysis["reason"] = "SPECIALIST_MODEL_MISMATCH"
            analysis["details"] = (
                f'The current model ("{model_config.get("description")}") is a specialist trained ONLY for: {", ".join(trained_classes)}.'
            )
            analysis["user_guidance"] = [
                f"This model will not detect other species. Please use an image containing a '{', '.join(trained_classes)}'.",
                "To detect a wider range of species, please switch to a general-purpose model (like YOLOv8) from the 'Model Selection' page.",
            ]
            analysis["technical_details"] = {
                "image_dimensions": f"{width}x{height}",
                "model_version": model_version,
                "confidence_threshold": self.confidence_threshold,
            }
            return analysis  # Return early as this is the most likely cause.

        # 2. Check image characteristics if not a specialist mismatch
        try:
            # Convert to grayscale and check variance
            gray = image.convert("L")
            if np is not None:
                gray_array = np.array(gray)
                variance = np.var(gray_array)

                variance_thresholds = IMAGE_CONFIG["VARIANCE_THRESHOLDS"]
                if (
                    variance < variance_thresholds["VERY_LOW"]
                ):  # Very low variance indicates mostly uniform image
                    analysis["reason"] = "IMAGE_TOO_UNIFORM"
                    analysis["details"] = "Image appears to be mostly blank or uniform in color"
                    analysis["user_guidance"] = [
                        "The image appears to be mostly blank or uniform in color",
                        "Bird detection requires images with visible objects and contrast",
                        "Try uploading an image that clearly shows birds or wildlife",
                        "Ensure the image has good lighting and contrast",
                    ]
                elif variance < variance_thresholds["LOW"]:  # Low variance
                    analysis["reason"] = "LOW_CONTRAST"
                    analysis["details"] = "Image has low contrast which may affect detection"
                    analysis["user_guidance"] = [
                        "The image has low contrast which may affect bird detection",
                        "Try using images with better lighting and contrast",
                        "Avoid images that are too dark, too bright, or washed out",
                        "Consider adjusting image brightness and contrast before upload",
                    ]
                else:
                    analysis["reason"] = "NO_BIRDS_DETECTED"
                    analysis["details"] = "No birds were detected in the image"
                    analysis["user_guidance"] = [
                        "No birds were detected in this image",
                        "The image may not contain any birds",
                        "Birds may be too small, blurry, or obscured",
                        "Try uploading an image with clear, visible birds",
                        "Ensure birds are the main subject of the image",
                    ]

                analysis["technical_details"] = {
                    "image_variance": float(variance),
                    "image_dimensions": f"{width}x{height}",
                    "model_version": model_version,
                    "confidence_threshold": self.confidence_threshold,
                }
            else:
                # NumPy not available, basic analysis
                analysis["reason"] = "NO_BIRDS_DETECTED"
                analysis["details"] = "No birds were detected in the image"
                analysis["user_guidance"] = [
                    "No birds were detected in this image",
                    "Try uploading an image with clear, visible birds",
                    "Ensure birds are the main subject of the image",
                ]
                analysis["technical_details"] = {
                    "image_dimensions": f"{width}x{height}",
                    "model_version": model_version,
                    "confidence_threshold": self.confidence_threshold,
                }

        except Exception as e:
            analysis["reason"] = "ANALYSIS_FAILED"
            analysis["details"] = f"Could not analyze image: {str(e)}"
            analysis["user_guidance"] = [
                "Unable to analyze the image automatically",
                "Try uploading a different image",
                "Ensure the image format is supported",
            ]

        return analysis

    def get_detection_health_status(self) -> dict:
        """Get comprehensive health status of the detection system"""
        health_status = {
            "overall_status": "HEALTHY",
            "models_loaded": len(self.models),
            "current_model": self.current_version,
            "device": self.device,
            "confidence_threshold": self.confidence_threshold,
            "issues": [],
            "recommendations": [],
        }

        # Check model availability
        if not self.models:
            health_status["overall_status"] = "CRITICAL"
            health_status["issues"].append(
                {
                    "type": "NO_MODELS",
                    "severity": "CRITICAL",
                    "message": "No YOLO models are loaded",
                    "impact": "Bird detection will not work",
                }
            )
            health_status["recommendations"].append("Check model files in models/ directory")

        # Check device availability
        if self.device == "cpu" and torch and torch.cuda.is_available():
            health_status["issues"].append(
                {
                    "type": "GPU_NOT_USED",
                    "severity": "WARNING",
                    "message": "GPU available but using CPU",
                    "impact": "Slower detection performance",
                }
            )
            health_status["recommendations"].append(
                "Check CUDA installation and PyTorch GPU support"
            )

        # Check model versions
        expected_models = ["YOLO_V5", "YOLO_V8", "YOLO_V9"]
        missing_models = [model for model in expected_models if model not in self.models]
        if missing_models:
            health_status["issues"].append(
                {
                    "type": "MISSING_MODELS",
                    "severity": "WARNING",
                    "message": f'Missing models: {", ".join(missing_models)}',
                    "impact": "Limited model selection options",
                }
            )
            health_status["recommendations"].append(
                f'Download missing models: {", ".join(missing_models)}'
            )

        # Determine overall status
        if any(issue["severity"] == "CRITICAL" for issue in health_status["issues"]):
            health_status["overall_status"] = "CRITICAL"
        elif any(issue["severity"] == "WARNING" for issue in health_status["issues"]):
            health_status["overall_status"] = "WARNING"

        return health_status

    def get_user_friendly_error_summary(self, detection_result: dict) -> dict:
        """Convert technical detection results into user-friendly error summaries"""
        if detection_result.get("success", True):
            if detection_result.get("total_detections", 0) == 0:
                # No detections case
                analysis = detection_result.get("no_detection_analysis", {})
                return {
                    "type": "NO_DETECTIONS",
                    "title": "No Birds Detected",
                    "message": analysis.get("details", "No birds were detected in this image"),
                    "severity": "INFO",
                    "user_guidance": analysis.get("user_guidance", []),
                    "technical_details": analysis.get("technical_details", {}),
                    "icon": "🐦❌",
                }
            else:
                # Successful detections
                return {
                    "type": "SUCCESS",
                    "title": f'{detection_result["total_detections"]} Bird(s) Detected',
                    "message": "Bird detection completed successfully",
                    "severity": "SUCCESS",
                    "user_guidance": [],
                    "technical_details": detection_result.get("image_analysis", {}),
                    "icon": "✅🐦",
                }
        else:
            # Error case
            error = detection_result.get("error", {})
            return {
                "type": "ERROR",
                "title": "Detection Failed",
                "message": error.get("message", "An error occurred during detection"),
                "severity": "ERROR",
                "user_guidance": error.get("suggestions", []),
                "technical_details": {
                    "error_type": error.get("error_type", "UNKNOWN"),
                    "details": error.get("details", ""),
                },
                "icon": "❌",
            }

    def get_model_info(self) -> dict:
        """Get comprehensive information about all models"""
        current_config = self.version_configs.get(self.current_version, {})

        # Highlight Chinese Egret model performance
        chinese_egret_available = "CHINESE_EGRET_V1" in self.models
        chinese_egret_performance = None
        if chinese_egret_available:
            chinese_egret_performance = self.version_configs["CHINESE_EGRET_V1"]["performance"]

        return {
            "current_version": self.current_version,
            "current_description": current_config.get("description", "Unknown model"),
            "current_performance": current_config.get("performance", {}),
            "device": self.device,
            "confidence_threshold": self.confidence_threshold,
            "available_models": self.get_available_models(),
            "total_models": len(self.models),
            "available": len(self.models) > 0,
            "chinese_egret_specialist": {
                "available": chinese_egret_available,
                "performance": chinese_egret_performance,
                "recommended": chinese_egret_available,
                "status": "🏆 Ultra High Performance"
                if chinese_egret_available
                else "❌ Not Available",
            },
        }

    def is_available(self) -> bool:
        """Check if the detection service is available"""
        return len(self.models) > 0

    def benchmark_models(self, image_content: bytes) -> dict:
        """Benchmark all available models on the same image"""
        if not self.models:
            return {"error": "No models available for benchmarking"}

        results = {}
        for version, _model in self.models.items():
            try:
                start_time = (
                    torch.cuda.Event(enable_timing=True) if torch.cuda.is_available() else None
                )
                end_time = (
                    torch.cuda.Event(enable_timing=True) if torch.cuda.is_available() else None
                )

                if start_time and end_time:
                    start_time.record()

                # Run detection
                detection_result = self.detect_birds(image_content, f"benchmark_{version}", version)

                if start_time and end_time:
                    end_time.record()
                    torch.cuda.synchronize()
                    inference_time = (
                        start_time.elapsed_time(end_time) / 1000.0
                    )  # Convert to seconds
                else:
                    inference_time = None

                results[version] = {
                    "detections": detection_result.get("total_detections", 0),
                    "inference_time": inference_time,
                    "success": detection_result.get("success", False),
                }

            except Exception as e:
                results[version] = {"error": str(e), "success": False}

        return results


# Global instance
bird_detection_service = BirdDetectionService()


def get_bird_detection_service(version: str = None) -> BirdDetectionService:
    """Get the global bird detection service instance, optionally switching to specific version"""
    if version and version in bird_detection_service.models:
        bird_detection_service.switch_model(version)
    return bird_detection_service
