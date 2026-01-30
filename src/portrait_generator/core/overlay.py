"""Title overlay engine for adding text overlays to portrait images."""

import logging
from pathlib import Path
from typing import Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)


class TitleOverlayEngine:
    """
    Engine for adding title overlays to portrait images.

    Adds a semi-transparent bar at the bottom with subject name and years.
    """

    DEFAULT_BAR_HEIGHT_RATIO = 0.15
    DEFAULT_BAR_OPACITY = 0.65
    DEFAULT_NAME_COLOR = (255, 255, 255)  # White
    DEFAULT_YEARS_COLOR = (200, 200, 200)  # Light gray
    DEFAULT_BAR_COLOR = (0, 0, 0)  # Black

    def __init__(self, font_path: Optional[str] = None):
        """
        Initialize TitleOverlayEngine.

        Args:
            font_path: Optional path to TrueType font file
        """
        self.font_path = font_path
        logger.info(f"Initialized TitleOverlayEngine with font_path={font_path}")

    def add_overlay(
        self,
        image: Image.Image,
        name: str,
        years: str,
        bar_opacity: float = DEFAULT_BAR_OPACITY,
        bar_height_ratio: float = DEFAULT_BAR_HEIGHT_RATIO,
    ) -> Image.Image:
        """
        Add title overlay to image.

        Args:
            image: PIL Image to add overlay to
            name: Subject name to display
            years: Years to display (e.g., "1912-1954")
            bar_opacity: Opacity of bar (0.0-1.0)
            bar_height_ratio: Bar height as ratio of image height

        Returns:
            New PIL Image with overlay

        Raises:
            ValueError: If parameters are invalid
        """
        if image is None:
            raise ValueError("Image cannot be None")

        if not name or not name.strip():
            raise ValueError("Name cannot be empty")

        if not years or not years.strip():
            raise ValueError("Years cannot be empty")

        if not 0.0 <= bar_opacity <= 1.0:
            raise ValueError("Bar opacity must be between 0.0 and 1.0")

        if not 0.0 < bar_height_ratio < 1.0:
            raise ValueError("Bar height ratio must be between 0.0 and 1.0")

        logger.info(f"Adding overlay: name='{name}', years='{years}'")

        # Ensure RGBA mode for transparency
        if image.mode != "RGBA":
            image = image.convert("RGBA")

        # Create overlay layer
        overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # Calculate bar dimensions
        width, height = image.size
        bar_height = int(height * bar_height_ratio)
        bar_top = height - bar_height

        # Draw semi-transparent bar
        bar_alpha = int(255 * bar_opacity)
        bar_color = (*self.DEFAULT_BAR_COLOR, bar_alpha)
        draw.rectangle(
            [(0, bar_top), (width, height)],
            fill=bar_color,
        )

        # Calculate font sizes
        name_font_size, years_font_size = self.calculate_font_size(
            height, bar_height_ratio
        )

        # Load fonts
        try:
            name_font = self._load_font(name_font_size)
            years_font = self._load_font(years_font_size)
        except Exception as e:
            logger.warning(f"Failed to load custom font: {e}. Using default.")
            name_font = ImageFont.load_default()
            years_font = ImageFont.load_default()

        # Calculate text positions (centered)
        name_bbox = draw.textbbox((0, 0), name, font=name_font)
        name_width = name_bbox[2] - name_bbox[0]
        name_x = (width - name_width) // 2

        years_bbox = draw.textbbox((0, 0), years, font=years_font)
        years_width = years_bbox[2] - years_bbox[0]
        years_x = (width - years_width) // 2

        # Calculate vertical positions
        # Name at 25% from top of bar
        name_y = bar_top + int(bar_height * 0.25)
        # Years below name with small gap
        years_y = name_y + (name_bbox[3] - name_bbox[1]) + 5

        # Draw text
        draw.text(
            (name_x, name_y),
            name,
            font=name_font,
            fill=(*self.DEFAULT_NAME_COLOR, 255),
        )

        draw.text(
            (years_x, years_y),
            years,
            font=years_font,
            fill=(*self.DEFAULT_YEARS_COLOR, 255),
        )

        # Composite overlay onto image
        result = Image.alpha_composite(image, overlay)

        # Convert back to RGB
        result = result.convert("RGB")

        logger.info(f"Overlay added successfully: {result.size} {result.mode}")

        return result

    def calculate_font_size(
        self, image_height: int, bar_height_ratio: float = DEFAULT_BAR_HEIGHT_RATIO
    ) -> Tuple[int, int]:
        """
        Calculate appropriate font sizes for name and years.

        Args:
            image_height: Height of image in pixels
            bar_height_ratio: Bar height as ratio of image height

        Returns:
            Tuple of (name_font_size, years_font_size)

        Raises:
            ValueError: If parameters are invalid
        """
        if image_height <= 0:
            raise ValueError("Image height must be positive")

        if not 0.0 < bar_height_ratio < 1.0:
            raise ValueError("Bar height ratio must be between 0.0 and 1.0")

        bar_height = int(image_height * bar_height_ratio)

        # Name font is 40% of bar height
        name_font_size = max(12, int(bar_height * 0.4))

        # Years font is 70% of name font size
        years_font_size = max(10, int(name_font_size * 0.7))

        logger.debug(
            f"Calculated font sizes: name={name_font_size}, years={years_font_size}"
        )

        return name_font_size, years_font_size

    def validate_overlay(self, image: Image.Image, expected_name: str = None) -> bool:
        """
        Validate that overlay is present and appears correct.

        This is a basic visual validation - checks if bottom portion
        of image is darker than average (indicating bar presence).

        Args:
            image: PIL Image to validate
            expected_name: Optional name to check for (requires OCR)

        Returns:
            True if overlay appears valid, False otherwise
        """
        if image is None:
            logger.warning("Validation failed: Image is None")
            return False

        try:
            # Ensure RGB mode
            if image.mode != "RGB":
                image = image.convert("RGB")

            width, height = image.size

            # Check bottom 15% of image for dark bar
            bar_region = image.crop((0, int(height * 0.85), width, height))

            # Get average brightness of bar region
            pixels = list(bar_region.getdata())
            avg_brightness = sum(sum(p[:3]) / 3 for p in pixels) / len(pixels)

            # Bar should be relatively dark (< 100 on 0-255 scale)
            if avg_brightness >= 100:
                logger.warning(
                    f"Validation failed: Bar region too bright ({avg_brightness:.1f})"
                )
                return False

            # Get average brightness of top region for comparison
            top_region = image.crop((0, 0, width, int(height * 0.15)))
            pixels = list(top_region.getdata())
            top_brightness = sum(sum(p[:3]) / 3 for p in pixels) / len(pixels)

            # Bottom should be significantly darker than top (unless whole image is dark)
            # If both are dark (< 100), that's acceptable (uniformly dark image)
            if avg_brightness < 100 and top_brightness < 100:
                # Both dark - acceptable for uniformly dark images
                pass
            elif avg_brightness >= top_brightness * 0.8:
                logger.warning(
                    "Validation failed: Bar not significantly darker than image"
                )
                return False

            logger.debug("Overlay validation passed")
            return True

        except Exception as e:
            logger.error(f"Validation failed with error: {e}", exc_info=True)
            return False

    def _load_font(self, size: int) -> ImageFont.FreeTypeFont:
        """
        Load TrueType font at specified size.

        Args:
            size: Font size in points

        Returns:
            PIL ImageFont object

        Raises:
            IOError: If font file cannot be loaded
        """
        if self.font_path:
            # Try custom font path
            try:
                font = ImageFont.truetype(self.font_path, size)
                logger.debug(f"Loaded custom font: {self.font_path} at size {size}")
                return font
            except IOError as e:
                logger.warning(
                    f"Failed to load custom font {self.font_path}: {e}. "
                    "Trying system fonts."
                )

        # Try common system font locations
        system_fonts = [
            "/System/Library/Fonts/Helvetica.ttc",  # macOS
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
            "C:\\Windows\\Fonts\\arial.ttf",  # Windows
            "/Library/Fonts/Arial.ttf",  # macOS alternative
        ]

        for font_path in system_fonts:
            try:
                font = ImageFont.truetype(font_path, size)
                logger.debug(f"Loaded system font: {font_path} at size {size}")
                return font
            except (IOError, OSError):
                continue

        # Fall back to default font
        logger.warning("No TrueType font found, using default PIL font")
        return ImageFont.load_default()

    def create_overlay_preview(
        self,
        name: str,
        years: str,
        image_size: Tuple[int, int] = (800, 1000),
        background_color: Tuple[int, int, int] = (100, 100, 100),
    ) -> Image.Image:
        """
        Create a preview image showing just the overlay.

        Useful for testing overlay appearance without a full portrait.

        Args:
            name: Subject name
            years: Years string
            image_size: Size of preview image (width, height)
            background_color: RGB background color

        Returns:
            PIL Image with overlay preview
        """
        if not name or not name.strip():
            raise ValueError("Name cannot be empty")

        if not years or not years.strip():
            raise ValueError("Years cannot be empty")

        logger.info(f"Creating overlay preview for '{name}'")

        # Create placeholder image
        placeholder = Image.new("RGB", image_size, background_color)

        # Add overlay
        result = self.add_overlay(placeholder, name, years)

        logger.info("Overlay preview created")

        return result
