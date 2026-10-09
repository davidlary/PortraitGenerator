"""Image transformation utilities for portrait generation."""

import logging
from typing import Optional, Tuple

from PIL import Image, ImageEnhance, ImageFilter

from .tonal_variants import BWParams
from .tonal_variants import to_bw as _tv_to_bw
from .tonal_variants import to_sepia as _tv_to_sepia

logger = logging.getLogger(__name__)


# convert_to_bw's ``enhance_contrast`` (a 2.9.0-era ImageEnhance factor where
# 1.0 = no change and the generators pass 1.2) is mapped onto the tonal
# S-curve weight of tonal_variants.BWParams so that the generators' default
# (1.2) reproduces the tuned house look exactly: weight = (factor - 1) * k with
# k derived from the house default, never hard-coded separately.
_BW_DEFAULT_ENHANCE_CONTRAST = 1.2
_BW_CONTRAST_PER_UNIT = BWParams().contrast / (_BW_DEFAULT_ENHANCE_CONTRAST - 1.0)


def convert_to_bw(image: Image.Image, enhance_contrast: float = 1.2) -> Image.Image:
    """
    Convert image to black and white with balanced tone.

    Since 2.10.0 this delegates to :func:`portrait_generator.utils.tonal_variants.to_bw`
    (linear-light luminance mix + conservative levels stretch + mild S-curve)
    instead of the gamma-space ``convert("L")`` + global contrast multiplier.

    Args:
        image: PIL Image to convert
        enhance_contrast: Contrast factor (1.0 = no S-curve, 1.2 = the tuned
            house look used by the generators, larger = stronger S-curve,
            capped at a full smoothstep; values below 1.0 additionally
            flatten contrast with ``ImageEnhance.Contrast`` as before)

    Returns:
        Black and white PIL Image in RGB mode (R == G == B), as before

    Raises:
        ValueError: If image is None or enhance_contrast is invalid
    """
    if image is None:
        raise ValueError("Image cannot be None")

    if enhance_contrast < 0:
        raise ValueError("Contrast enhancement must be >= 0")

    logger.debug(f"Converting to BW with contrast={enhance_contrast}")

    weight = min(1.0, max(0.0, (enhance_contrast - 1.0) * _BW_CONTRAST_PER_UNIT))
    bw_image = _tv_to_bw(image, BWParams(contrast=weight)).convert("RGB")

    if enhance_contrast < 1.0:
        bw_image = ImageEnhance.Contrast(bw_image).enhance(enhance_contrast)

    logger.info(f"Converted to BW: {bw_image.size} {bw_image.mode}")

    return bw_image


def convert_to_sepia(
    image: Image.Image, intensity: float = 1.0
) -> Image.Image:
    """
    Convert image to sepia tone.

    Since 2.10.0 this delegates to :func:`portrait_generator.utils.tonal_variants.to_sepia`
    (split-toned OKLCH sepia built on the balanced B&W plane) instead of the
    clipping per-pixel "sepia matrix". The input image is no longer modified
    in place.

    Args:
        image: PIL Image to convert
        intensity: Sepia intensity (0.0 = the balanced B&W rendition,
            1.0 = full sepia; linear blend in between)

    Returns:
        Sepia-toned PIL Image (RGB)

    Raises:
        ValueError: If image is None or intensity is out of range
    """
    if image is None:
        raise ValueError("Image cannot be None")

    if not 0.0 <= intensity <= 1.0:
        raise ValueError("Intensity must be between 0.0 and 1.0")

    logger.debug(f"Converting to sepia with intensity={intensity}")

    sepia = _tv_to_sepia(image)
    if intensity < 1.0:
        gray = _tv_to_bw(image).convert("RGB")
        sepia = Image.blend(gray, sepia, intensity)

    logger.info(f"Converted to sepia: {sepia.size} {sepia.mode}")

    return sepia


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
