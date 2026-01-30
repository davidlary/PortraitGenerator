"""Image transformation utilities for portrait generation."""

import logging
from typing import Optional, Tuple

from PIL import Image, ImageEnhance, ImageFilter

logger = logging.getLogger(__name__)


def convert_to_bw(image: Image.Image, enhance_contrast: float = 1.2) -> Image.Image:
    """
    Convert image to black and white with enhanced contrast.

    Args:
        image: PIL Image to convert
        enhance_contrast: Contrast enhancement factor (1.0 = no change)

    Returns:
        Black and white PIL Image

    Raises:
        ValueError: If image is None or enhance_contrast is invalid
    """
    if image is None:
        raise ValueError("Image cannot be None")

    if enhance_contrast < 0:
        raise ValueError("Contrast enhancement must be >= 0")

    logger.debug(f"Converting to BW with contrast={enhance_contrast}")

    # Convert to grayscale
    bw_image = image.convert("L")

    # Convert back to RGB mode for consistency
    bw_image = bw_image.convert("RGB")

    # Enhance contrast if requested
    if enhance_contrast != 1.0:
        enhancer = ImageEnhance.Contrast(bw_image)
        bw_image = enhancer.enhance(enhance_contrast)

    logger.info(f"Converted to BW: {bw_image.size} {bw_image.mode}")

    return bw_image


def convert_to_sepia(
    image: Image.Image, intensity: float = 1.0
) -> Image.Image:
    """
    Convert image to sepia tone.

    Args:
        image: PIL Image to convert
        intensity: Sepia intensity (0.0 = grayscale, 1.0 = full sepia)

    Returns:
        Sepia-toned PIL Image

    Raises:
        ValueError: If image is None or intensity is out of range
    """
    if image is None:
        raise ValueError("Image cannot be None")

    if not 0.0 <= intensity <= 1.0:
        raise ValueError("Intensity must be between 0.0 and 1.0")

    logger.debug(f"Converting to sepia with intensity={intensity}")

    # Ensure RGB mode
    if image.mode != "RGB":
        image = image.convert("RGB")

    # Get pixel data
    pixels = image.load()
    width, height = image.size

    # Sepia matrix coefficients
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]

            # Convert to grayscale first (intensity 0.0 = grayscale)
            gray = int(0.299 * r + 0.587 * g + 0.114 * b)

            # Calculate sepia values
            tr = int(0.393 * gray + 0.769 * gray + 0.189 * gray)
            tg = int(0.349 * gray + 0.686 * gray + 0.168 * gray)
            tb = int(0.272 * gray + 0.534 * gray + 0.131 * gray)

            # Clamp to 0-255
            tr = min(255, tr)
            tg = min(255, tg)
            tb = min(255, tb)

            # Blend between grayscale (0.0) and sepia (1.0) based on intensity
            if intensity < 1.0:
                # Blend from grayscale to sepia
                tr = int(gray + (tr - gray) * intensity)
                tg = int(gray + (tg - gray) * intensity)
                tb = int(gray + (tb - gray) * intensity)

            pixels[x, y] = (tr, tg, tb)

    logger.info(f"Converted to sepia: {image.size} {image.mode}")

    return image


def enhance_image(
    image: Image.Image,
    brightness: float = 1.0,
    contrast: float = 1.0,
    color: float = 1.0,
    sharpness: float = 1.0,
) -> Image.Image:
    """
    Enhance image with multiple adjustments.

    Args:
        image: PIL Image to enhance
        brightness: Brightness factor (1.0 = no change)
        contrast: Contrast factor (1.0 = no change)
        color: Color saturation factor (1.0 = no change)
        sharpness: Sharpness factor (1.0 = no change)

    Returns:
        Enhanced PIL Image

    Raises:
        ValueError: If image is None or any factor is invalid
    """
    if image is None:
        raise ValueError("Image cannot be None")

    for factor_name, factor_value in [
        ("brightness", brightness),
        ("contrast", contrast),
        ("color", color),
        ("sharpness", sharpness),
    ]:
        if factor_value < 0:
            raise ValueError(f"{factor_name} must be >= 0")

    logger.debug(
        f"Enhancing image: brightness={brightness}, contrast={contrast}, "
        f"color={color}, sharpness={sharpness}"
    )

    result = image.copy()

    # Apply brightness
    if brightness != 1.0:
        enhancer = ImageEnhance.Brightness(result)
        result = enhancer.enhance(brightness)

    # Apply contrast
    if contrast != 1.0:
        enhancer = ImageEnhance.Contrast(result)
        result = enhancer.enhance(contrast)

    # Apply color saturation
    if color != 1.0:
        enhancer = ImageEnhance.Color(result)
        result = enhancer.enhance(color)

    # Apply sharpness
    if sharpness != 1.0:
        enhancer = ImageEnhance.Sharpness(result)
        result = enhancer.enhance(sharpness)

    logger.info("Image enhancement complete")

    return result


def resize_image(
    image: Image.Image,
    target_size: Tuple[int, int],
    maintain_aspect_ratio: bool = False,
    resample: int = Image.Resampling.LANCZOS,
) -> Image.Image:
    """
    Resize image to target size.

    Args:
        image: PIL Image to resize
        target_size: Target (width, height) in pixels
        maintain_aspect_ratio: If True, resize maintaining aspect ratio with padding
        resample: Resampling filter (default: LANCZOS for high quality)

    Returns:
        Resized PIL Image

    Raises:
        ValueError: If image is None or target_size is invalid
    """
    if image is None:
        raise ValueError("Image cannot be None")

    if not target_size or len(target_size) != 2:
        raise ValueError("Target size must be a tuple of (width, height)")

    if target_size[0] <= 0 or target_size[1] <= 0:
        raise ValueError("Target dimensions must be positive")

    logger.debug(
        f"Resizing from {image.size} to {target_size}, "
        f"maintain_aspect_ratio={maintain_aspect_ratio}"
    )

    if maintain_aspect_ratio:
        # Calculate aspect-preserving size
        image.thumbnail(target_size, resample)

        # Create new image with target size and paste centered
        result = Image.new("RGB", target_size, (0, 0, 0))
        offset = (
            (target_size[0] - image.size[0]) // 2,
            (target_size[1] - image.size[1]) // 2,
        )
        result.paste(image, offset)

        logger.info(f"Resized with aspect ratio to {result.size}")
        return result
    else:
        # Direct resize
        result = image.resize(target_size, resample)
        logger.info(f"Resized to {result.size}")
        return result


def crop_to_aspect_ratio(
    image: Image.Image, aspect_ratio: str = "3:4"
) -> Image.Image:
    """
    Crop image to specified aspect ratio, centered.

    Args:
        image: PIL Image to crop
        aspect_ratio: Target aspect ratio as string (e.g., "3:4", "16:9")

    Returns:
        Cropped PIL Image

    Raises:
        ValueError: If image is None or aspect_ratio is invalid
    """
    if image is None:
        raise ValueError("Image cannot be None")

    # Parse aspect ratio
    try:
        width_ratio, height_ratio = map(int, aspect_ratio.split(":"))
    except ValueError:
        raise ValueError(
            f"Invalid aspect ratio '{aspect_ratio}'. Expected format: 'width:height'"
        )

    if width_ratio <= 0 or height_ratio <= 0:
        raise ValueError("Aspect ratio values must be positive")

    logger.debug(f"Cropping to aspect ratio {aspect_ratio}")

    # Calculate target dimensions
    current_width, current_height = image.size
    target_aspect = width_ratio / height_ratio
    current_aspect = current_width / current_height

    if current_aspect > target_aspect:
        # Image is too wide, crop width
        new_width = int(current_height * target_aspect)
        new_height = current_height
    else:
        # Image is too tall, crop height
        new_width = current_width
        new_height = int(current_width / target_aspect)

    # Calculate crop box (centered)
    left = (current_width - new_width) // 2
    top = (current_height - new_height) // 2
    right = left + new_width
    bottom = top + new_height

    # Crop
    result = image.crop((left, top, right, bottom))

    logger.info(f"Cropped to {result.size} (aspect ratio {aspect_ratio})")

    return result


def apply_vignette(
    image: Image.Image, intensity: float = 0.5, radius: float = 0.7
) -> Image.Image:
    """
    Apply vignette effect to image.

    Args:
        image: PIL Image to process
        intensity: Vignette darkness (0.0 = none, 1.0 = maximum)
        radius: Vignette radius (0.0 = center only, 1.0 = full image)

    Returns:
        Image with vignette effect

    Raises:
        ValueError: If parameters are out of range
    """
    if image is None:
        raise ValueError("Image cannot be None")

    if not 0.0 <= intensity <= 1.0:
        raise ValueError("Intensity must be between 0.0 and 1.0")

    if not 0.0 <= radius <= 1.0:
        raise ValueError("Radius must be between 0.0 and 1.0")

    logger.debug(f"Applying vignette: intensity={intensity}, radius={radius}")

    # Ensure RGB mode
    if image.mode != "RGB":
        image = image.convert("RGB")

    # Create a copy
    result = image.copy()
    pixels = result.load()
    width, height = result.size

    # Calculate center
    cx, cy = width / 2, height / 2
    max_distance = ((width / 2) ** 2 + (height / 2) ** 2) ** 0.5

    # Apply vignette
    for y in range(height):
        for x in range(width):
            # Calculate distance from center
            distance = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            normalized_distance = distance / max_distance

            # Calculate vignette factor
            if normalized_distance < radius:
                factor = 1.0
            else:
                factor = 1.0 - ((normalized_distance - radius) / (1.0 - radius)) * intensity

            # Apply to pixel
            r, g, b = pixels[x, y]
            pixels[x, y] = (
                int(r * factor),
                int(g * factor),
                int(b * factor),
            )

    logger.info("Vignette effect applied")

    return result


def validate_image(
    image: Image.Image,
    min_size: Optional[Tuple[int, int]] = None,
    max_size: Optional[Tuple[int, int]] = None,
    required_mode: Optional[str] = None,
) -> bool:
    """
    Validate image meets requirements.

    Args:
        image: PIL Image to validate
        min_size: Minimum (width, height) or None
        max_size: Maximum (width, height) or None
        required_mode: Required color mode (e.g., "RGB") or None

    Returns:
        True if valid, False otherwise
    """
    if image is None:
        logger.warning("Validation failed: Image is None")
        return False

    width, height = image.size

    # Check minimum size
    if min_size:
        if width < min_size[0] or height < min_size[1]:
            logger.warning(
                f"Validation failed: Image {width}x{height} smaller than "
                f"minimum {min_size[0]}x{min_size[1]}"
            )
            return False

    # Check maximum size
    if max_size:
        if width > max_size[0] or height > max_size[1]:
            logger.warning(
                f"Validation failed: Image {width}x{height} larger than "
                f"maximum {max_size[0]}x{max_size[1]}"
            )
            return False

    # Check mode
    if required_mode and image.mode != required_mode:
        logger.warning(
            f"Validation failed: Image mode {image.mode} != required {required_mode}"
        )
        return False

    logger.debug("Image validation passed")
    return True
