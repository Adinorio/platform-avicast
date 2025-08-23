"""
Visualization utilities for bird detection results
Provides functions to draw bounding boxes and labels on detected images
"""

import cv2
import numpy as np
import logging
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, List, Optional
import io
import base64

logger = logging.getLogger(__name__)

def draw_detections_on_image(image_content: bytes, detections: List[Dict], 
                           output_format: str = 'pil') -> bytes:
    """
    Draw bounding boxes and labels on an image
    
    Args:
        image_content: Raw image bytes
        detections: List of detection dictionaries with bounding_box info
        output_format: 'pil' for PIL Image, 'cv2' for OpenCV format, 'bytes' for raw bytes
        
    Returns:
        Image with detections drawn (format depends on output_format)
    """
    try:
        # Convert bytes to PIL Image
        image = Image.open(io.BytesIO(image_content))
        
        # Create a copy for drawing
        draw_image = image.copy()
        draw = ImageDraw.Draw(draw_image)
        
        # Try to load a font, fall back to default if not available
        try:
            font = ImageFont.truetype("arial.ttf", 16)
        except (OSError, IOError):
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 16)  # macOS
            except (OSError, IOError):
                font = ImageFont.load_default()
        
        # Draw each detection
        for i, detection in enumerate(detections):
            bbox = detection.get('bounding_box', {})
            species = detection.get('species', 'Bird')
            confidence = detection.get('confidence', 0.0)
            
            if not bbox or 'x' not in bbox:
                continue
                
            # Extract coordinates
            x = bbox.get('x', 0)
            y = bbox.get('y', 0)
            width = bbox.get('width', 0)
            height = bbox.get('height', 0)
            
            # Draw bounding box
            box_color = (255, 0, 0)  # Red
            line_width = 3
            
            # Draw rectangle
            draw.rectangle([x, y, x + width, y + height], 
                         outline=box_color, width=line_width)
            
            # Create label text
            label_text = f"{species} ({confidence:.1%})"
            
            # Get text size for background
            try:
                bbox_text = draw.textbbox((0, 0), label_text, font=font)
                text_width = bbox_text[2] - bbox_text[0]
                text_height = bbox_text[3] - bbox_text[1]
            except (AttributeError, TypeError):
                # Fallback for older PIL versions
                text_width = len(label_text) * 8
                text_height = 16
            
            # Draw label background
            label_x = max(0, x)
            label_y = max(0, y - text_height - 5)
            
            # Ensure label doesn't go off the image
            if label_x + text_width > image.width:
                label_x = image.width - text_width - 5
            if label_y < 0:
                label_y = y + height + 5
            
            # Draw label background rectangle
            draw.rectangle([label_x - 2, label_y - 2, 
                          label_x + text_width + 2, label_y + text_height + 2],
                         fill=box_color)
            
            # Draw label text
            draw.text((label_x, label_y), label_text, fill=(255, 255, 255), font=font)
            
            # Add detection number
            detection_num = f"#{i+1}"
            try:
                num_bbox = draw.textbbox((0, 0), detection_num, font=font)
                num_width = num_bbox[2] - num_bbox[0]
                num_height = num_bbox[3] - num_bbox[1]
            except (AttributeError, TypeError):
                num_width = len(detection_num) * 8
                num_height = 16
            
            # Draw detection number at top-right of bounding box
            num_x = min(x + width - num_width - 5, image.width - num_width - 5)
            num_y = max(y + 5, 5)
            
            # Draw number background
            draw.rectangle([num_x - 2, num_y - 2, 
                          num_x + num_width + 2, num_y + num_height + 2],
                         fill=(0, 0, 0))
            
            # Draw number text
            draw.text((num_x, num_y), detection_num, fill=(255, 255, 255), font=font)
        
        # Convert to requested format
        if output_format == 'pil':
            return draw_image
        elif output_format == 'cv2':
            # Convert PIL to OpenCV format
            cv_image = cv2.cvtColor(np.array(draw_image), cv2.COLOR_RGB2BGR)
            return cv_image
        elif output_format == 'bytes':
            # Convert to bytes
            buffer = io.BytesIO()
            draw_image.save(buffer, format='JPEG', quality=95)
            return buffer.getvalue()
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
            
    except Exception as e:
        logger.error(f"Error drawing detections: {e}")
        # Return original image if drawing fails
        return image_content

def create_detection_summary_image(detections: List[Dict], image_size: tuple = (800, 600)) -> bytes:
    """
    Create a summary image showing all detections
    
    Args:
        detections: List of detection dictionaries
        image_size: Size of output image (width, height)
        
    Returns:
        Summary image as bytes
    """
    try:
        # Create a new image
        image = Image.new('RGB', image_size, (240, 240, 240))
        draw = ImageDraw.Draw(image)
        
        # Try to load a font
        try:
            title_font = ImageFont.truetype("arial.ttf", 24)
            font = ImageFont.truetype("arial.ttf", 16)
        except (OSError, IOError):
            try:
                title_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 24)
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 16)
            except (OSError, IOError):
                title_font = ImageFont.load_default()
                font = ImageFont.load_default()
        
        # Draw title
        title = f"Bird Detection Results - {len(detections)} birds found"
        draw.text((20, 20), title, fill=(0, 0, 0), font=title_font)
        
        # Draw detection information
        y_offset = 80
        for i, detection in enumerate(detections):
            species = detection.get('species', 'Unknown')
            confidence = detection.get('confidence', 0.0)
            bbox = detection.get('bounding_box', {})
            
            # Detection line
            line_text = f"{i+1}. {species} - Confidence: {confidence:.1%}"
            draw.text((20, y_offset), line_text, fill=(0, 0, 0), font=font)
            
            # Bounding box coordinates
            if bbox:
                coords_text = f"   Box: ({bbox.get('x', 'N/A')}, {bbox.get('y', 'N/A')}) - {bbox.get('width', 'N/A')}x{bbox.get('height', 'N/A')}"
                draw.text((20, y_offset + 20), coords_text, fill=(100, 100, 100), font=font)
                y_offset += 45
            else:
                y_offset += 30
        
        # Convert to bytes
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG', quality=95)
        return buffer.getvalue()
        
    except Exception as e:
        logger.error(f"Error creating summary image: {e}")
        # Return a simple error image
        error_image = Image.new('RGB', image_size, (255, 200, 200))
        draw = ImageDraw.Draw(error_image)
        draw.text((20, 20), f"Error creating summary: {e}", fill=(255, 0, 0))
        
        buffer = io.BytesIO()
        error_image.save(buffer, format='JPEG')
        return buffer.getvalue()

def get_detection_statistics(detections: List[Dict]) -> Dict:
    """
    Get statistics about detections
    
    Args:
        detections: List of detection dictionaries
        
    Returns:
        Dictionary with detection statistics
    """
    if not detections:
        return {
            'total_detections': 0,
            'species_count': {},
            'confidence_stats': {
                'min': 0.0,
                'max': 0.0,
                'average': 0.0
            }
        }
    
    # Count species
    species_count = {}
    confidences = []
    
    for detection in detections:
        species = detection.get('species', 'Unknown')
        confidence = detection.get('confidence', 0.0)
        
        species_count[species] = species_count.get(species, 0) + 1
        confidences.append(confidence)
    
    # Calculate confidence statistics
    confidences = [c for c in confidences if c > 0]
    if confidences:
        confidence_stats = {
            'min': min(confidences),
            'max': max(confidences),
            'average': sum(confidences) / len(confidences)
        }
    else:
        confidence_stats = {'min': 0.0, 'max': 0.0, 'average': 0.0}
    
    return {
        'total_detections': len(detections),
        'species_count': species_count,
        'confidence_stats': confidence_stats
    }
