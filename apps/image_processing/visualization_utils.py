"""
Visualization utilities for bird detection results
Provides functions to draw bounding boxes and labels on detected images
"""

import io
import logging

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)


def scale_bounding_box_coordinates(
    bbox: dict, from_width: int, from_height: int, to_width: int, to_height: int
) -> dict:
    """
    Scale bounding box coordinates from one image size to another

    Args:
        bbox: Bounding box dictionary with x1,y1,x2,y2 or x,y,width,height format
        from_width: Source image width
        from_height: Source image height
        to_width: Target image width
        to_height: Target image height

    Returns:
        Scaled bounding box dictionary in x,y,width,height format
    """
    if not bbox:
        return bbox

    # Calculate scaling factors
    scale_x = to_width / from_width
    scale_y = to_height / from_height

    logger.info(
        f"Scaling factors: {scale_x:.3f} x {scale_y:.3f} (from {from_width}x{from_height} to {to_width}x{to_height})"
    )

    # Handle x1,y1,x2,y2 format (from YOLO)
    if "x1" in bbox and "y1" in bbox and "x2" in bbox and "y2" in bbox:
        x1 = bbox["x1"] * scale_x
        y1 = bbox["y1"] * scale_y
        x2 = bbox["x2"] * scale_x
        y2 = bbox["y2"] * scale_y

        result = {"x": int(x1), "y": int(y1), "width": int(x2 - x1), "height": int(y2 - y1)}
        logger.info(f"Converted x1y1x2y2 {bbox} to xywh {result}")
        return result

    # Handle x,y,width,height format (already scaled or different format)
    elif "x" in bbox and "y" in bbox and "width" in bbox and "height" in bbox:
        result = {
            "x": int(bbox["x"] * scale_x),
            "y": int(bbox["y"] * scale_y),
            "width": int(bbox["width"] * scale_x),
            "height": int(bbox["height"] * scale_y),
        }
        logger.info(f"Scaled xywh {bbox} to {result}")
        return result

    return bbox


def draw_detections_on_image(
    image_content: bytes,
    detections: list[dict],
    output_format: str = "pil",
    ai_processing_size: tuple = (640, 640),
) -> bytes:
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

        # Convert to RGB to prevent issues with RGBA formats (e.g., PNG) when saving as JPEG
        if image.mode == "RGBA":
            image = image.convert("RGB")

        # Get display image dimensions
        display_width, display_height = image.size

        # Create a copy for drawing
        draw_image = image.copy()
        draw = ImageDraw.Draw(draw_image)

        # Try to load a font, fall back to default if not available
        try:
            font = ImageFont.truetype("arial.ttf", 16)
        except OSError:
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 16)  # macOS
            except OSError:
                font = ImageFont.load_default()

        # Draw each detection
        for i, detection in enumerate(detections):
            bbox = detection.get("bounding_box", {})
            species = detection.get("species", "Bird")
            confidence = detection.get("confidence", 0.0)

            if not bbox:
                continue

            # Scale bounding box coordinates from AI processing size to display size
            logger.info(
                f"Original bbox: {bbox}, AI size: {ai_processing_size}, Display size: {display_width}x{display_height}"
            )

            # If AI processed the same dimensions as display, no scaling needed
            if ai_processing_size == (display_width, display_height):
                logger.info("AI processed same dimensions as display - no scaling needed")
                scaled_bbox = bbox
            else:
                logger.info(
                    f"Scaling coordinates from {ai_processing_size} to {display_width}x{display_height}"
                )
                scaled_bbox = scale_bounding_box_coordinates(
                    bbox,
                    ai_processing_size[0],
                    ai_processing_size[1],  # From AI processing size
                    display_width,
                    display_height,  # To display size
                )

            logger.info(f"Scaled bbox: {scaled_bbox}")

            if not scaled_bbox or "x" not in scaled_bbox:
                logger.warning(f"Invalid scaled bbox: {scaled_bbox}")
                continue

            # Sanity check: filter out obviously wrong coordinates
            x = scaled_bbox.get("x", 0)
            y = scaled_bbox.get("y", 0)
            width = scaled_bbox.get("width", 0)
            height = scaled_bbox.get("height", 0)

            # If coordinates are way outside reasonable bounds, skip this detection
            if (
                x < -1000
                or y < -1000
                or x > display_width + 1000
                or y > display_height + 1000
                or width > display_width * 2
                or height > display_height * 2
            ):
                logger.warning(
                    f"Skipping detection with obviously wrong coordinates: ({x}, {y}) {width}x{height}"
                )
                continue

            # Additional safety check: ensure coordinates don't exceed image boundaries by too much
            if x + width > display_width + 50 or y + height > display_height + 50:
                logger.warning(
                    f"Detection extends too far beyond image boundaries: ({x}, {y}) {width}x{height} for {display_width}x{display_height}"
                )
                # Try to adjust the bounding box to fit within the image
                if x + width > display_width:
                    width = max(1, display_width - x)
                    logger.info(f"Adjusted width to {width}")
                if y + height > display_height:
                    height = max(1, display_height - y)
                    logger.info(f"Adjusted height to {height}")

            # Extract scaled coordinates
            x = scaled_bbox.get("x", 0)
            y = scaled_bbox.get("y", 0)
            width = scaled_bbox.get("width", 0)
            height = scaled_bbox.get("height", 0)

            # Validate coordinates are within image bounds and have positive dimensions
            if width <= 0 or height <= 0:
                logger.warning(f"Invalid bounding box dimensions: {width}x{height}")
                continue

            # Calculate actual boundaries
            right_edge = x + width
            bottom_edge = y + height

            # Log detailed coordinate analysis
            logger.info(f"Bbox analysis: x={x}, y={y}, w={width}, h={height}")
            logger.info(f"Bbox boundaries: right={right_edge}, bottom={bottom_edge}")
            logger.info(f"Image boundaries: width={display_width}, height={display_height}")

            # Check if coordinates are out of bounds
            out_of_bounds = False
            if x < 0:
                logger.warning(f"X coordinate {x} < 0")
                out_of_bounds = True
            if y < 0:
                logger.warning(f"Y coordinate {y} < 0")
                out_of_bounds = True
            if right_edge > display_width:
                logger.warning(f"Right edge {right_edge} > image width {display_width}")
                out_of_bounds = True
            if bottom_edge > display_height:
                logger.warning(f"Bottom edge {bottom_edge} > image height {display_height}")
                out_of_bounds = True

            if out_of_bounds:
                logger.warning(
                    f"Bounding box coordinates out of bounds: ({x}, {y}) {width}x{height} for image {display_width}x{display_height}"
                )
                # Clamp coordinates to image bounds
                x = max(0, min(x, display_width - width))
                y = max(0, min(y, display_height - height))
                logger.info(f"Clamped coordinates to: ({x}, {y})")

                # Final safety check: ensure the adjusted coordinates are valid
            if x < 0 or y < 0 or x + width > display_width or y + height > display_height:
                logger.error(
                    f"Coordinates still out of bounds after clamping: ({x}, {y}) {width}x{height}"
                )
                # Last resort: force coordinates to be within bounds
                x = max(0, min(x, display_width - 1))
                y = max(0, min(y, display_height - 1))
                width = max(1, min(width, display_width - x))
                height = max(1, min(height, display_height - y))
                logger.info(f"Force-adjusted coordinates to: ({x}, {y}) {width}x{height}")

            logger.info(f"Drawing bbox at ({x}, {y}) with size {width}x{height}")

            # Draw bounding box
            box_color = (255, 0, 0)  # Red
            line_width = 3

            # Draw rectangle
            draw.rectangle([x, y, x + width, y + height], outline=box_color, width=line_width)

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
            draw.rectangle(
                [label_x - 2, label_y - 2, label_x + text_width + 2, label_y + text_height + 2],
                fill=box_color,
            )

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
            draw.rectangle(
                [num_x - 2, num_y - 2, num_x + num_width + 2, num_y + num_height + 2],
                fill=(0, 0, 0),
            )

            # Draw number text
            draw.text((num_x, num_y), detection_num, fill=(255, 255, 255), font=font)

        # Convert to requested format
        if output_format == "pil":
            return draw_image
        elif output_format == "cv2":
            # Convert PIL to OpenCV format
            cv_image = cv2.cvtColor(np.array(draw_image), cv2.COLOR_RGB2BGR)
            return cv_image
        elif output_format == "bytes":
            # Convert to bytes
            buffer = io.BytesIO()
            draw_image.save(buffer, format="JPEG", quality=95)
            return buffer.getvalue()
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

    except Exception as e:
        logger.error(f"Error drawing detections: {e}")
        # Return original image if drawing fails
        return image_content


def create_detection_summary_image(detections: list[dict], image_size: tuple = (800, 600)) -> bytes:
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
        image = Image.new("RGB", image_size, (240, 240, 240))
        draw = ImageDraw.Draw(image)

        # Try to load a font
        try:
            title_font = ImageFont.truetype("arial.ttf", 24)
            font = ImageFont.truetype("arial.ttf", 16)
        except OSError:
            try:
                title_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 24)
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 16)
            except OSError:
                title_font = ImageFont.load_default()
                font = ImageFont.load_default()

        # Draw title
        title = f"Bird Detection Results - {len(detections)} birds found"
        draw.text((20, 20), title, fill=(0, 0, 0), font=title_font)

        # Draw detection information
        y_offset = 80
        for i, detection in enumerate(detections):
            species = detection.get("species", "Unknown")
            confidence = detection.get("confidence", 0.0)
            bbox = detection.get("bounding_box", {})

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
        image.save(buffer, format="JPEG", quality=95)
        return buffer.getvalue()

    except Exception as e:
        logger.error(f"Error creating summary image: {e}")
        # Return a simple error image
        error_image = Image.new("RGB", image_size, (255, 200, 200))
        draw = ImageDraw.Draw(error_image)
        draw.text((20, 20), f"Error creating summary: {e}", fill=(255, 0, 0))

        buffer = io.BytesIO()
        error_image.save(buffer, format="JPEG")
        return buffer.getvalue()


def get_detection_statistics(detections: list[dict]) -> dict:
    """
    Get statistics about detections

    Args:
        detections: List of detection dictionaries

    Returns:
        Dictionary with detection statistics
    """
    if not detections:
        return {
            "total_detections": 0,
            "species_count": {},
            "confidence_stats": {"min": 0.0, "max": 0.0, "average": 0.0},
        }

    # Count species
    species_count = {}
    confidences = []

    for detection in detections:
        species = detection.get("species", "Unknown")
        confidence = detection.get("confidence", 0.0)

        species_count[species] = species_count.get(species, 0) + 1
        confidences.append(confidence)

    # Calculate confidence statistics
    confidences = [c for c in confidences if c > 0]
    if confidences:
        confidence_stats = {
            "min": min(confidences),
            "max": max(confidences),
            "average": sum(confidences) / len(confidences),
        }
    else:
        confidence_stats = {"min": 0.0, "max": 0.0, "average": 0.0}

    return {
        "total_detections": len(detections),
        "species_count": species_count,
        "confidence_stats": confidence_stats,
    }
