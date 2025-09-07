"""
Analytics Configuration - Centralized settings for the analytics system
This replaces all hardcoded values with configurable/dynamic data
"""

from django.conf import settings
from django.utils.translation import gettext_lazy as _

# =============================================================================
# ANALYTICS SYSTEM CONFIGURATION
# =============================================================================

ANALYTICS_CONFIG = {
    # Model Configuration
    "DEFAULT_MODELS": ["yolov5s", "yolov8l", "yolov9c"],
    "MODEL_PATH_PATTERNS": {
        "yolov5": "models/yolov5/{model_name}.pt",
        "yolov8": "models/yolov8/{model_name}.pt",
        "yolov9": "models/yolov9/{model_name}.pt",
    },
    # Species Configuration
    "DEFAULT_SPECIES": ["Chinese Egret", "Whiskered Tern", "Great Knot"],
    "CONFUSION_MATRIX_CLASSES": ["Chinese Egret", "Whiskered Tern", "Great Knot", "Background"],
    # Threshold Defaults
    "DEFAULT_IOU_THRESHOLD": 0.5,
    "DEFAULT_CONFIDENCE_THRESHOLD": 0.25,
    "FAILURE_RECALL_THRESHOLD": 0.8,
    # Display Limits
    "RECENT_RUNS_LIMIT": 5,
    "PAGINATION_LIMIT": 20,
    "RADAR_CHART_LIMIT": 5,
    "FAILURE_CASES_LIMIT": 10,
    "HISTORICAL_DATA_DAYS": 30,
    # Date Filter Presets
    "DATE_FILTERS": {
        "today": 1,
        "week": 7,
        "month": 30,
        "quarter": 90,
        "year": 365,
    },
    # Visual Configuration
    "CHART_COLORS": [
        "#667eea",
        "#764ba2",
        "#f093fb",
        "#f5576c",
        "#4facfe",
        "#43e97b",
        "#38f9d7",
        "#e0c3fc",
        "#fa709a",
        "#a8edea",
    ],
    "SPEED_NORMALIZATION_FACTOR": 50,
    "SPEED_MAX_DISPLAY": 100,
    # Debug Configuration
    "ENABLE_DEBUG_LOGGING": getattr(settings, "DEBUG", False),
}

# =============================================================================
# USER INTERFACE TEXT (Internationalization Ready)
# =============================================================================

UI_TEXT = {
    "HELPFUL_TIPS": {
        "PENDING": [
            _("evaluation_queued_message"),
            _("processing_delay_message"),
        ],
        "PROCESSING": [
            _("current_step_template"),
            _("progress_percentage_template"),
        ],
        "FAILED": [
            _("evaluation_failed_message"),
            _("check_model_files_message"),
            _("check_logs_message"),
        ],
    },
    "ERROR_MESSAGES": {
        "ACCESS_DENIED": _("analytics_access_denied"),
        "DELETE_PERMISSION": _("delete_own_runs_only"),
        "EVALUATION_FAILED": _("evaluation_creation_failed"),
    },
    "SUCCESS_MESSAGES": {
        "EVALUATION_CREATED": _("evaluation_run_created"),
        "RUN_DELETED": _("evaluation_run_deleted"),
    },
}

# =============================================================================
# DYNAMIC DATA RETRIEVAL FUNCTIONS
# =============================================================================


def get_available_models():
    """
    Get models that are actually available/used in the system
    Falls back to default models if none found
    """
    from .models import ImageProcessingResult

    try:
        models = list(ImageProcessingResult.objects.values_list("ai_model", flat=True).distinct())

        # Filter out None/empty values
        models = [m for m in models if m]

        if models:
            return sorted(models)
        else:
            return ANALYTICS_CONFIG["DEFAULT_MODELS"]
    except Exception:
        # Fallback in case of database issues
        return ANALYTICS_CONFIG["DEFAULT_MODELS"]


def get_target_species():
    """
    Get species that are actually detected in the system
    Falls back to default species if none found
    """
    from .models import ImageProcessingResult

    try:
        species = list(
            ImageProcessingResult.objects.filter(detected_species__isnull=False)
            .values_list("detected_species", flat=True)
            .distinct()
        )

        # Filter out None/empty values
        species = [s for s in species if s]

        if species:
            return sorted(species)
        else:
            return ANALYTICS_CONFIG["DEFAULT_SPECIES"]
    except Exception:
        # Fallback in case of database issues
        return ANALYTICS_CONFIG["DEFAULT_SPECIES"]


def get_confusion_matrix_species():
    """
    Get species list for confusion matrix including Background class
    """
    species = get_target_species()
    if "Background" not in species:
        species.append("Background")
    return species


def get_model_file_size(model_name):
    """
    Get model file size from filesystem
    Returns size in MB or None if not found
    """
    import os

    # Try different model path patterns
    for pattern in ANALYTICS_CONFIG["MODEL_PATH_PATTERNS"].values():
        model_path = pattern.format(model_name=model_name.lower())
        if os.path.exists(model_path):
            size_bytes = os.path.getsize(model_path)
            return round(size_bytes / (1024 * 1024), 1)  # Convert to MB

    return None


def get_admin_roles():
    """
    Get admin role names from User model
    """
    from .models import User

    try:
        # Get all role choices that contain 'ADMIN'
        admin_roles = [choice[0] for choice in User.ROLE_CHOICES if "ADMIN" in choice[0]]
        return admin_roles if admin_roles else ["ADMIN", "SUPERADMIN"]
    except Exception:
        # Fallback if model not available
        return ["ADMIN", "SUPERADMIN"]


def get_date_filter_days(filter_name):
    """
    Get number of days for date filter
    """
    return ANALYTICS_CONFIG["DATE_FILTERS"].get(filter_name, 30)


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================


def log_debug(message, *args, **kwargs):
    """
    Conditional debug logging
    """
    if ANALYTICS_CONFIG["ENABLE_DEBUG_LOGGING"]:
        import logging

        logger = logging.getLogger(__name__)
        logger.debug(message, *args, **kwargs)


def get_helpful_tips(status, progress=None):
    """
    Get contextual helpful tips based on evaluation status
    """
    tips = []

    if status == "PENDING":
        tips.extend(UI_TEXT["HELPFUL_TIPS"]["PENDING"])
    elif status == "PROCESSING" and progress:
        tips.append(
            UI_TEXT["HELPFUL_TIPS"]["PROCESSING"][0].format(
                step=getattr(progress, "current_step", "Unknown")
            )
        )
        tips.append(
            UI_TEXT["HELPFUL_TIPS"]["PROCESSING"][1].format(
                percentage=getattr(progress, "progress_percentage", 0)
            )
        )
    elif status == "FAILED":
        tips.extend(UI_TEXT["HELPFUL_TIPS"]["FAILED"])

    return tips
