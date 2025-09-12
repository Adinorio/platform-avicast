"""
Custom template tags for enhanced egret identification frontend
"""
from django import template
from django.template.defaultfilters import register

register = template.Library()

@register.filter
def get_uncertainty_color(level):
    """Get CSS class for uncertainty level color"""
    colors = {
        0: 'success',    # Green - High confidence
        1: 'warning',    # Yellow - Some uncertainty
        2: 'warning',    # Orange - Moderate uncertainty
        3: 'danger',     # Red - High uncertainty
        4: 'secondary'   # Gray - Very uncertain
    }
    return colors.get(level, 'secondary')

@register.filter
def get_uncertainty_bootstrap_color(level):
    """Get Bootstrap color class for uncertainty level"""
    colors = {
        0: 'success',
        1: 'warning',
        2: 'warning',
        3: 'danger',
        4: 'secondary'
    }
    return colors.get(level, 'secondary')

@register.filter
def get_confidence_level(confidence):
    """Get confidence level category from confidence percentage"""
    if confidence >= 80:
        return 'high'
    elif confidence >= 60:
        return 'medium'
    else:
        return 'low'

@register.filter
def get_expected_size_range(species):
    """Get expected size range for egret species"""
    from apps.image_processing.config import EGRET_SIZE_RANGES

    if species in EGRET_SIZE_RANGES:
        min_size, max_size = EGRET_SIZE_RANGES[species]
        return [min_size, max_size]
    else:
        # Default range for unknown species
        return [0.05, 0.50]

@register.filter
def get_uncertainty_description(level):
    """Get human-readable description of uncertainty level"""
    descriptions = {
        0: "High confidence - This identification is very reliable.",
        1: "Some uncertainty - Generally reliable but consider alternatives.",
        2: "Moderate uncertainty - Review carefully, multiple species possible.",
        3: "High uncertainty - Low confidence, manual review recommended.",
        4: "Very uncertain - Identification may be incorrect."
    }
    return descriptions.get(level, "Uncertainty level unknown")

@register.filter
def format_uncertainty_factors(factors):
    """Format uncertainty factors for display"""
    if not factors:
        return []

    if isinstance(factors, str):
        return [factor.strip() for factor in factors.split(',') if factor.strip()]
    elif isinstance(factors, list):
        return factors
    else:
        return []

@register.simple_tag
def get_alternative_species(species):
    """Get alternative species that could be confused with the given species"""
    confusion_map = {
        "Chinese Egret": ["Intermediate Egret"],
        "Great Egret": ["Intermediate Egret", "Little Egret"],
        "Intermediate Egret": ["Chinese Egret", "Great Egret"],
        "Little Egret": ["Great Egret"]
    }

    return confusion_map.get(species, [])

@register.simple_tag
def get_species_training_info(species):
    """Get training data information for a species"""
    training_info = {
        "Chinese Egret": {"samples": 990, "percentage": 37.7},
        "Great Egret": {"samples": 613, "percentage": 23.6},
        "Intermediate Egret": {"samples": 159, "percentage": 6.0},
        "Little Egret": {"samples": 30, "percentage": 3.0}
    }

    return training_info.get(species, {"samples": 0, "percentage": 0})

@register.filter
def get_detection_quality_score(detection):
    """Calculate an overall quality score for a detection"""
    if not hasattr(detection, 'confidence'):
        return 0

    confidence = detection.confidence
    has_bbox = hasattr(detection, 'bounding_box') and detection.bounding_box
    has_alternatives = hasattr(detection, 'alternative_species') and detection.alternative_species

    # Base score from confidence
    score = confidence / 100

    # Bonus for having bounding box
    if has_bbox:
        score += 0.1

    # Bonus for having alternatives (shows system awareness)
    if has_alternatives:
        score += 0.05

    # Penalty for high uncertainty
    uncertainty_level = getattr(detection, 'uncertainty_level', 0)
    uncertainty_penalty = uncertainty_level * 0.05
    score -= uncertainty_penalty

    # Ensure score is between 0 and 1
    return max(0, min(1, score))

@register.filter
def get_detection_reliability_text(detection):
    """Get human-readable reliability text for a detection"""
    if not hasattr(detection, 'confidence'):
        return "Unable to assess reliability"

    confidence = detection.confidence
    uncertainty_level = getattr(detection, 'uncertainty_level', 0)

    if confidence >= 85 and uncertainty_level <= 1:
        return "Highly reliable identification"
    elif confidence >= 75 and uncertainty_level <= 2:
        return "Generally reliable, consider alternatives"
    elif confidence >= 60:
        return "Moderate confidence, review recommended"
    else:
        return "Low confidence, manual review strongly recommended"

