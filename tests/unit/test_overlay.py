"""Unit tests for TitleOverlayEngine."""

import pytest
from PIL import Image

from portrait_generator.core.overlay import TitleOverlayEngine


@pytest.fixture
def engine():
    """Create TitleOverlayEngine instance."""
    return TitleOverlayEngine()


@pytest.fixture
def sample_image():
    """Create a sample image for testing."""
    return Image.new("RGB", (800, 1000), color=(150, 150, 150))


@pytest.fixture
def sample_square_image():
    """Create a sample square image."""
    return Image.new("RGB", (500, 500), color=(100, 100, 100))


class TestTitleOverlayEngineInit:
    """Tests for TitleOverlayEngine initialization."""

    def test_init_default(self):
        """Test initialization with defaults."""
        engine = TitleOverlayEngine()

        assert engine.font_path is None

    def test_init_with_font_path(self):
        """Test initialization with custom font path."""
        engine = TitleOverlayEngine(font_path="/path/to/font.ttf")

        assert engine.font_path == "/path/to/font.ttf"


class TestAddOverlay:
    """Tests for add_overlay method."""

    def test_add_overlay_basic(self, engine, sample_image):
        """Test basic overlay addition."""
        result = engine.add_overlay(
            sample_image, name="Albert Einstein", years="1879-1955"
        )

        assert isinstance(result, Image.Image)
        assert result.size == sample_image.size
        assert result.mode == "RGB"

    def test_add_overlay_result_different(self, engine, sample_image):
        """Test that overlay modifies the image."""
        result = engine.add_overlay(
            sample_image, name="Albert Einstein", years="1879-1955"
        )

        # Check that bottom portion is darker (has overlay)
        width, height = result.size
        bottom_region = result.crop((0, int(height * 0.85), width, height))
        pixels = list(bottom_region.getdata())
        avg_brightness = sum(sum(p[:3]) / 3 for p in pixels) / len(pixels)

        # Should be dark (overlay bar)
        assert avg_brightness < 100

    def test_add_overlay_none_image(self, engine):
        """Test error handling for None image."""
        with pytest.raises(ValueError, match="cannot be None"):
            engine.add_overlay(None, name="Test", years="1900-2000")

    def test_add_overlay_empty_name(self, engine, sample_image):
        """Test error handling for empty name."""
        with pytest.raises(ValueError, match="cannot be empty"):
            engine.add_overlay(sample_image, name="", years="1900-2000")

    def test_add_overlay_whitespace_name(self, engine, sample_image):
        """Test error handling for whitespace-only name."""
        with pytest.raises(ValueError, match="cannot be empty"):
            engine.add_overlay(sample_image, name="   ", years="1900-2000")

    def test_add_overlay_empty_years(self, engine, sample_image):
        """Test error handling for empty years."""
        with pytest.raises(ValueError, match="cannot be empty"):
            engine.add_overlay(sample_image, name="Test", years="")

    def test_add_overlay_whitespace_years(self, engine, sample_image):
        """Test error handling for whitespace-only years."""
        with pytest.raises(ValueError, match="cannot be empty"):
            engine.add_overlay(sample_image, name="Test", years="   ")

    def test_add_overlay_invalid_opacity_negative(self, engine, sample_image):
        """Test error handling for negative opacity."""
        with pytest.raises(ValueError, match="must be between"):
            engine.add_overlay(
                sample_image,
                name="Test",
                years="1900-2000",
                bar_opacity=-0.1,
            )

    def test_add_overlay_invalid_opacity_too_high(self, engine, sample_image):
        """Test error handling for opacity > 1.0."""
        with pytest.raises(ValueError, match="must be between"):
            engine.add_overlay(
                sample_image,
                name="Test",
                years="1900-2000",
                bar_opacity=1.5,
            )

    def test_add_overlay_invalid_bar_height_zero(self, engine, sample_image):
        """Test error handling for zero bar height ratio."""
        with pytest.raises(ValueError, match="must be between"):
            engine.add_overlay(
                sample_image,
                name="Test",
                years="1900-2000",
                bar_height_ratio=0.0,
            )

    def test_add_overlay_invalid_bar_height_one(self, engine, sample_image):
        """Test error handling for bar height ratio = 1.0."""
        with pytest.raises(ValueError, match="must be between"):
            engine.add_overlay(
                sample_image,
                name="Test",
                years="1900-2000",
                bar_height_ratio=1.0,
            )

    def test_add_overlay_custom_opacity(self, engine, sample_image):
        """Test overlay with custom opacity."""
        result = engine.add_overlay(
            sample_image,
            name="Test Name",
            years="1900-2000",
            bar_opacity=0.8,
        )

        assert isinstance(result, Image.Image)

    def test_add_overlay_custom_bar_height(self, engine, sample_image):
        """Test overlay with custom bar height."""
        result = engine.add_overlay(
            sample_image,
            name="Test Name",
            years="1900-2000",
            bar_height_ratio=0.2,
        )

        assert isinstance(result, Image.Image)

    def test_add_overlay_long_name(self, engine, sample_image):
        """Test overlay with very long name."""
        result = engine.add_overlay(
            sample_image,
            name="Christopher von Bülowenstein-Schaumberg",
            years="1850-1920",
        )

        assert isinstance(result, Image.Image)

    def test_add_overlay_square_image(self, engine, sample_square_image):
        """Test overlay on square image."""
        result = engine.add_overlay(
            sample_square_image, name="Test", years="1900-2000"
        )

        assert result.size == sample_square_image.size

    def test_add_overlay_small_image(self, engine):
        """Test overlay on small image."""
        small_img = Image.new("RGB", (100, 100), color=(128, 128, 128))
        result = engine.add_overlay(small_img, name="Test", years="1900-2000")

        assert isinstance(result, Image.Image)
        assert result.size == (100, 100)

    def test_add_overlay_large_image(self, engine):
        """Test overlay on large image."""
        large_img = Image.new("RGB", (2048, 2048), color=(128, 128, 128))
        result = engine.add_overlay(large_img, name="Test", years="1900-2000")

        assert isinstance(result, Image.Image)
        assert result.size == (2048, 2048)

    def test_add_overlay_rgba_input(self, engine):
        """Test overlay on RGBA input image."""
        rgba_img = Image.new("RGBA", (800, 1000), color=(150, 150, 150, 255))
        result = engine.add_overlay(rgba_img, name="Test", years="1900-2000")

        assert result.mode == "RGB"

    def test_add_overlay_grayscale_input(self, engine):
        """Test overlay on grayscale input."""
        gray_img = Image.new("L", (800, 1000), color=128)
        result = engine.add_overlay(gray_img, name="Test", years="1900-2000")

        assert result.mode == "RGB"


class TestCalculateFontSize:
    """Tests for calculate_font_size method."""

    def test_calculate_font_size_default(self, engine):
        """Test font size calculation with defaults."""
        name_size, years_size = engine.calculate_font_size(1000)

        assert isinstance(name_size, int)
        assert isinstance(years_size, int)
        assert name_size > years_size
        assert name_size >= 12
        assert years_size >= 10

    def test_calculate_font_size_custom_ratio(self, engine):
        """Test font size calculation with custom bar height ratio."""
        name_size, years_size = engine.calculate_font_size(1000, bar_height_ratio=0.2)

        assert isinstance(name_size, int)
        assert isinstance(years_size, int)
        assert name_size > years_size

    def test_calculate_font_size_small_image(self, engine):
        """Test font size calculation for small image."""
        name_size, years_size = engine.calculate_font_size(100)

        # Even for small images, fonts should be at minimum size
        assert name_size >= 12
        assert years_size >= 10

    def test_calculate_font_size_large_image(self, engine):
        """Test font size calculation for large image."""
        name_size, years_size = engine.calculate_font_size(3000)

        # For large images, fonts should scale up
        assert name_size > 50

    def test_calculate_font_size_zero_height(self, engine):
        """Test error handling for zero image height."""
        with pytest.raises(ValueError, match="must be positive"):
            engine.calculate_font_size(0)

    def test_calculate_font_size_negative_height(self, engine):
        """Test error handling for negative image height."""
        with pytest.raises(ValueError, match="must be positive"):
            engine.calculate_font_size(-100)

    def test_calculate_font_size_invalid_ratio_zero(self, engine):
        """Test error handling for zero bar height ratio."""
        with pytest.raises(ValueError, match="must be between"):
            engine.calculate_font_size(1000, bar_height_ratio=0.0)

    def test_calculate_font_size_invalid_ratio_one(self, engine):
        """Test error handling for bar height ratio = 1.0."""
        with pytest.raises(ValueError, match="must be between"):
            engine.calculate_font_size(1000, bar_height_ratio=1.0)

    def test_calculate_font_size_years_is_70_percent(self, engine):
        """Test that years font is 70% of name font."""
        name_size, years_size = engine.calculate_font_size(1000)

        # Years should be approximately 70% of name (allowing for min size)
        if name_size > 20:  # Only test when not at minimum
            expected_years = int(name_size * 0.7)
            assert abs(years_size - expected_years) <= 1


class TestValidateOverlay:
    """Tests for validate_overlay method."""

    def test_validate_overlay_with_overlay(self, engine, sample_image):
        """Test validation of image with overlay."""
        image_with_overlay = engine.add_overlay(
            sample_image, name="Test", years="1900-2000"
        )

        result = engine.validate_overlay(image_with_overlay)

        assert result is True

    def test_validate_overlay_without_overlay(self, engine, sample_image):
        """Test validation of image without overlay."""
        result = engine.validate_overlay(sample_image)

        # Should fail because no dark bar at bottom
        assert result is False

    def test_validate_overlay_none_image(self, engine):
        """Test validation of None image."""
        result = engine.validate_overlay(None)

        assert result is False

    def test_validate_overlay_dark_image(self, engine):
        """Test validation of completely dark image."""
        dark_img = Image.new("RGB", (800, 1000), color=(10, 10, 10))
        result = engine.validate_overlay(dark_img)

        # Should pass because bottom is dark
        # (even though it's all dark, not just the bar)
        assert result is True

    def test_validate_overlay_bright_bottom(self, engine):
        """Test validation fails for bright bottom."""
        # Create image with bright bottom
        img = Image.new("RGB", (800, 1000), color=(50, 50, 50))
        pixels = img.load()
        # Make bottom bright
        for y in range(850, 1000):
            for x in range(800):
                pixels[x, y] = (200, 200, 200)

        result = engine.validate_overlay(img)

        assert result is False

    def test_validate_overlay_rgba_image(self, engine, sample_image):
        """Test validation of RGBA image with overlay."""
        image_with_overlay = engine.add_overlay(
            sample_image, name="Test", years="1900-2000"
        )
        rgba_img = image_with_overlay.convert("RGBA")

        result = engine.validate_overlay(rgba_img)

        assert result is True

    def test_validate_overlay_grayscale_image(self, engine):
        """Test validation of grayscale image."""
        gray_img = Image.new("L", (800, 1000), color=50)
        result = engine.validate_overlay(gray_img)

        assert result is True  # Dark enough to pass


class TestCreateOverlayPreview:
    """Tests for create_overlay_preview method."""

    def test_create_overlay_preview_basic(self, engine):
        """Test basic preview creation."""
        result = engine.create_overlay_preview(
            name="Test Name", years="1900-2000"
        )

        assert isinstance(result, Image.Image)
        assert result.size == (800, 1000)
        assert result.mode == "RGB"

    def test_create_overlay_preview_custom_size(self, engine):
        """Test preview with custom size."""
        result = engine.create_overlay_preview(
            name="Test", years="1900-2000", image_size=(1024, 768)
        )

        assert result.size == (1024, 768)

    def test_create_overlay_preview_custom_background(self, engine):
        """Test preview with custom background color."""
        result = engine.create_overlay_preview(
            name="Test",
            years="1900-2000",
            background_color=(50, 100, 150),
        )

        assert isinstance(result, Image.Image)

    def test_create_overlay_preview_empty_name(self, engine):
        """Test error handling for empty name."""
        with pytest.raises(ValueError, match="cannot be empty"):
            engine.create_overlay_preview(name="", years="1900-2000")

    def test_create_overlay_preview_empty_years(self, engine):
        """Test error handling for empty years."""
        with pytest.raises(ValueError, match="cannot be empty"):
            engine.create_overlay_preview(name="Test", years="")

    def test_create_overlay_preview_long_name(self, engine):
        """Test preview with long name."""
        result = engine.create_overlay_preview(
            name="Christopher von Bülowenstein-Schaumberg",
            years="1850-1920",
        )

        assert isinstance(result, Image.Image)

    def test_create_overlay_preview_validates(self, engine):
        """Test that created preview passes validation."""
        preview = engine.create_overlay_preview(
            name="Test", years="1900-2000"
        )

        assert engine.validate_overlay(preview) is True


class TestLoadFont:
    """Tests for _load_font private method."""

    def test_load_font_default(self, engine):
        """Test loading default font."""
        font = engine._load_font(20)

        assert font is not None

    def test_load_font_different_sizes(self, engine):
        """Test loading fonts at different sizes."""
        font_small = engine._load_font(12)
        font_large = engine._load_font(48)

        assert font_small is not None
        assert font_large is not None

    def test_load_font_invalid_path(self):
        """Test loading font with invalid custom path."""
        engine = TitleOverlayEngine(font_path="/nonexistent/font.ttf")
        font = engine._load_font(20)

        # Should fall back to default
        assert font is not None


class TestIntegration:
    """Integration tests for TitleOverlayEngine."""

    def test_multiple_overlays_same_engine(self, engine):
        """Test adding multiple overlays with same engine instance."""
        img1 = Image.new("RGB", (800, 1000), color=(100, 100, 100))
        img2 = Image.new("RGB", (800, 1000), color=(150, 150, 150))

        result1 = engine.add_overlay(img1, name="Person One", years="1900-1950")
        result2 = engine.add_overlay(img2, name="Person Two", years="1950-2000")

        assert engine.validate_overlay(result1)
        assert engine.validate_overlay(result2)

    def test_overlay_preserves_image_quality(self, engine, sample_image):
        """Test that overlay doesn't degrade image quality significantly."""
        result = engine.add_overlay(
            sample_image, name="Test", years="1900-2000"
        )

        # Check that top 80% of image is unchanged
        width, height = sample_image.size
        top_region_orig = sample_image.crop((0, 0, width, int(height * 0.8)))
        top_region_result = result.crop((0, 0, width, int(height * 0.8)))

        # Compare pixel data (should be very similar)
        pixels_orig = list(top_region_orig.getdata())
        pixels_result = list(top_region_result.getdata())

        # Allow small differences due to mode conversion
        differences = sum(
            1 for p1, p2 in zip(pixels_orig, pixels_result) if p1 != p2
        )
        total_pixels = len(pixels_orig)

        # Less than 5% of pixels should differ
        assert differences / total_pixels < 0.05

    def test_overlay_on_real_portrait(self, engine):
        """Test overlay on a more realistic portrait-sized image."""
        # Create a gradient to simulate a portrait
        portrait = Image.new("RGB", (768, 1024), color=(100, 80, 70))

        result = engine.add_overlay(
            portrait, name="William of Ockham", years="1285-1347"
        )

        assert isinstance(result, Image.Image)
        assert result.size == (768, 1024)
        assert engine.validate_overlay(result)
