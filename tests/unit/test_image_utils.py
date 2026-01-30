"""Unit tests for image utilities."""

import pytest
from PIL import Image

from portrait_generator.utils.image_utils import (
    convert_to_bw,
    convert_to_sepia,
    enhance_image,
    resize_image,
    crop_to_aspect_ratio,
    apply_vignette,
    validate_image,
)


@pytest.fixture
def sample_image():
    """Create a sample color image for testing."""
    return Image.new("RGB", (100, 100), color=(255, 0, 0))


@pytest.fixture
def sample_landscape_image():
    """Create a sample landscape image."""
    return Image.new("RGB", (200, 100), color=(0, 255, 0))


@pytest.fixture
def sample_portrait_image():
    """Create a sample portrait image."""
    return Image.new("RGB", (100, 200), color=(0, 0, 255))


class TestConvertToBW:
    """Tests for convert_to_bw function."""

    def test_convert_to_bw_basic(self, sample_image):
        """Test basic BW conversion."""
        result = convert_to_bw(sample_image)

        assert isinstance(result, Image.Image)
        assert result.mode == "RGB"
        assert result.size == sample_image.size

    def test_convert_to_bw_grayscale_pixels(self, sample_image):
        """Test that pixels are grayscale (R=G=B)."""
        result = convert_to_bw(sample_image)
        pixels = list(result.getdata())

        # Check first pixel is grayscale
        r, g, b = pixels[0]
        assert r == g == b

    def test_convert_to_bw_with_contrast(self, sample_image):
        """Test BW conversion with contrast enhancement."""
        result = convert_to_bw(sample_image, enhance_contrast=1.5)

        assert isinstance(result, Image.Image)
        assert result.mode == "RGB"

    def test_convert_to_bw_none_image(self):
        """Test error handling for None image."""
        with pytest.raises(ValueError, match="cannot be None"):
            convert_to_bw(None)

    def test_convert_to_bw_negative_contrast(self, sample_image):
        """Test error handling for negative contrast."""
        with pytest.raises(ValueError, match="must be >= 0"):
            convert_to_bw(sample_image, enhance_contrast=-0.5)

    def test_convert_to_bw_zero_contrast(self, sample_image):
        """Test BW conversion with zero contrast."""
        result = convert_to_bw(sample_image, enhance_contrast=0.0)
        assert isinstance(result, Image.Image)

    def test_convert_to_bw_preserves_size(self, sample_landscape_image):
        """Test that size is preserved."""
        result = convert_to_bw(sample_landscape_image)
        assert result.size == sample_landscape_image.size


class TestConvertToSepia:
    """Tests for convert_to_sepia function."""

    def test_convert_to_sepia_basic(self, sample_image):
        """Test basic sepia conversion."""
        result = convert_to_sepia(sample_image)

        assert isinstance(result, Image.Image)
        assert result.mode == "RGB"
        assert result.size == sample_image.size

    def test_convert_to_sepia_full_intensity(self, sample_image):
        """Test sepia with full intensity."""
        result = convert_to_sepia(sample_image, intensity=1.0)

        # Check that red channel is highest (sepia characteristic)
        pixels = list(result.getdata())
        r, g, b = pixels[0]
        assert r >= g >= b

    def test_convert_to_sepia_zero_intensity(self, sample_image):
        """Test sepia with zero intensity (should be grayscale)."""
        result = convert_to_sepia(sample_image, intensity=0.0)

        pixels = list(result.getdata())
        r, g, b = pixels[0]
        # With zero intensity, should be close to grayscale
        assert abs(r - g) < 10  # Allow small variation

    def test_convert_to_sepia_partial_intensity(self, sample_image):
        """Test sepia with partial intensity."""
        result = convert_to_sepia(sample_image, intensity=0.5)

        assert isinstance(result, Image.Image)
        assert result.mode == "RGB"

    def test_convert_to_sepia_none_image(self):
        """Test error handling for None image."""
        with pytest.raises(ValueError, match="cannot be None"):
            convert_to_sepia(None)

    def test_convert_to_sepia_invalid_intensity_negative(self, sample_image):
        """Test error handling for negative intensity."""
        with pytest.raises(ValueError, match="must be between"):
            convert_to_sepia(sample_image, intensity=-0.1)

    def test_convert_to_sepia_invalid_intensity_too_high(self, sample_image):
        """Test error handling for intensity > 1.0."""
        with pytest.raises(ValueError, match="must be between"):
            convert_to_sepia(sample_image, intensity=1.5)

    def test_convert_to_sepia_grayscale_input(self):
        """Test sepia conversion on grayscale image."""
        gray_img = Image.new("L", (50, 50), color=128)
        result = convert_to_sepia(gray_img, intensity=1.0)

        assert result.mode == "RGB"


class TestEnhanceImage:
    """Tests for enhance_image function."""

    def test_enhance_image_no_changes(self, sample_image):
        """Test enhancement with default values (no changes)."""
        result = enhance_image(sample_image)

        assert isinstance(result, Image.Image)
        assert result.size == sample_image.size

    def test_enhance_image_brightness(self, sample_image):
        """Test brightness enhancement."""
        result = enhance_image(sample_image, brightness=1.5)

        assert isinstance(result, Image.Image)

    def test_enhance_image_contrast(self, sample_image):
        """Test contrast enhancement."""
        result = enhance_image(sample_image, contrast=1.3)

        assert isinstance(result, Image.Image)

    def test_enhance_image_color(self, sample_image):
        """Test color saturation enhancement."""
        result = enhance_image(sample_image, color=1.2)

        assert isinstance(result, Image.Image)

    def test_enhance_image_sharpness(self, sample_image):
        """Test sharpness enhancement."""
        result = enhance_image(sample_image, sharpness=1.5)

        assert isinstance(result, Image.Image)

    def test_enhance_image_all_factors(self, sample_image):
        """Test enhancement with all factors."""
        result = enhance_image(
            sample_image,
            brightness=1.1,
            contrast=1.2,
            color=0.9,
            sharpness=1.3,
        )

        assert isinstance(result, Image.Image)
        assert result.size == sample_image.size

    def test_enhance_image_none_image(self):
        """Test error handling for None image."""
        with pytest.raises(ValueError, match="cannot be None"):
            enhance_image(None)

    def test_enhance_image_negative_brightness(self, sample_image):
        """Test error handling for negative brightness."""
        with pytest.raises(ValueError, match="brightness must be >= 0"):
            enhance_image(sample_image, brightness=-0.5)

    def test_enhance_image_negative_contrast(self, sample_image):
        """Test error handling for negative contrast."""
        with pytest.raises(ValueError, match="contrast must be >= 0"):
            enhance_image(sample_image, contrast=-0.5)

    def test_enhance_image_zero_values(self, sample_image):
        """Test enhancement with zero values."""
        result = enhance_image(
            sample_image, brightness=0.0, contrast=0.0, color=0.0, sharpness=0.0
        )

        assert isinstance(result, Image.Image)


class TestResizeImage:
    """Tests for resize_image function."""

    def test_resize_image_basic(self, sample_image):
        """Test basic resize."""
        result = resize_image(sample_image, (200, 200))

        assert isinstance(result, Image.Image)
        assert result.size == (200, 200)

    def test_resize_image_upscale(self, sample_image):
        """Test upscaling."""
        result = resize_image(sample_image, (300, 300))

        assert result.size == (300, 300)

    def test_resize_image_downscale(self, sample_image):
        """Test downscaling."""
        result = resize_image(sample_image, (50, 50))

        assert result.size == (50, 50)

    def test_resize_image_aspect_ratio_change(self, sample_image):
        """Test resize with aspect ratio change."""
        result = resize_image(sample_image, (200, 100))

        assert result.size == (200, 100)

    def test_resize_image_maintain_aspect_ratio(self, sample_landscape_image):
        """Test resize while maintaining aspect ratio."""
        result = resize_image(
            sample_landscape_image, (100, 100), maintain_aspect_ratio=True
        )

        assert result.size == (100, 100)

    def test_resize_image_none_image(self):
        """Test error handling for None image."""
        with pytest.raises(ValueError, match="cannot be None"):
            resize_image(None, (100, 100))

    def test_resize_image_invalid_target_size_none(self, sample_image):
        """Test error handling for None target size."""
        with pytest.raises(ValueError, match="must be a tuple"):
            resize_image(sample_image, None)

    def test_resize_image_invalid_target_size_single_value(self, sample_image):
        """Test error handling for single value target size."""
        with pytest.raises(ValueError, match="must be a tuple"):
            resize_image(sample_image, (100,))

    def test_resize_image_zero_dimension(self, sample_image):
        """Test error handling for zero dimensions."""
        with pytest.raises(ValueError, match="must be positive"):
            resize_image(sample_image, (0, 100))

    def test_resize_image_negative_dimension(self, sample_image):
        """Test error handling for negative dimensions."""
        with pytest.raises(ValueError, match="must be positive"):
            resize_image(sample_image, (100, -50))


class TestCropToAspectRatio:
    """Tests for crop_to_aspect_ratio function."""

    def test_crop_to_aspect_ratio_square_to_portrait(self, sample_image):
        """Test cropping square to portrait."""
        result = crop_to_aspect_ratio(sample_image, "3:4")

        assert isinstance(result, Image.Image)
        assert result.size[0] < result.size[1]  # Width < Height

    def test_crop_to_aspect_ratio_square_to_landscape(self, sample_image):
        """Test cropping square to landscape."""
        result = crop_to_aspect_ratio(sample_image, "16:9")

        assert isinstance(result, Image.Image)
        assert result.size[0] > result.size[1]  # Width > Height

    def test_crop_to_aspect_ratio_landscape(self, sample_landscape_image):
        """Test cropping landscape image."""
        result = crop_to_aspect_ratio(sample_landscape_image, "3:4")

        assert isinstance(result, Image.Image)
        # Should crop width
        assert result.size[0] < sample_landscape_image.size[0]

    def test_crop_to_aspect_ratio_portrait(self, sample_portrait_image):
        """Test cropping portrait image."""
        result = crop_to_aspect_ratio(sample_portrait_image, "16:9")

        assert isinstance(result, Image.Image)
        # Should crop height
        assert result.size[1] < sample_portrait_image.size[1]

    def test_crop_to_aspect_ratio_none_image(self):
        """Test error handling for None image."""
        with pytest.raises(ValueError, match="cannot be None"):
            crop_to_aspect_ratio(None, "3:4")

    def test_crop_to_aspect_ratio_invalid_format(self, sample_image):
        """Test error handling for invalid aspect ratio format."""
        with pytest.raises(ValueError, match="Invalid aspect ratio"):
            crop_to_aspect_ratio(sample_image, "invalid")

    def test_crop_to_aspect_ratio_zero_value(self, sample_image):
        """Test error handling for zero values."""
        with pytest.raises(ValueError, match="must be positive"):
            crop_to_aspect_ratio(sample_image, "0:4")

    def test_crop_to_aspect_ratio_negative_value(self, sample_image):
        """Test error handling for negative values."""
        with pytest.raises(ValueError, match="must be positive"):
            crop_to_aspect_ratio(sample_image, "3:-4")

    def test_crop_to_aspect_ratio_1_1(self, sample_landscape_image):
        """Test cropping to 1:1 (square)."""
        result = crop_to_aspect_ratio(sample_landscape_image, "1:1")

        assert result.size[0] == result.size[1]


class TestApplyVignette:
    """Tests for apply_vignette function."""

    def test_apply_vignette_basic(self, sample_image):
        """Test basic vignette application."""
        result = apply_vignette(sample_image)

        assert isinstance(result, Image.Image)
        assert result.size == sample_image.size

    def test_apply_vignette_full_intensity(self, sample_image):
        """Test vignette with full intensity."""
        result = apply_vignette(sample_image, intensity=1.0)

        assert isinstance(result, Image.Image)

    def test_apply_vignette_no_intensity(self, sample_image):
        """Test vignette with no intensity."""
        result = apply_vignette(sample_image, intensity=0.0)

        assert isinstance(result, Image.Image)

    def test_apply_vignette_custom_radius(self, sample_image):
        """Test vignette with custom radius."""
        result = apply_vignette(sample_image, intensity=0.5, radius=0.5)

        assert isinstance(result, Image.Image)

    def test_apply_vignette_none_image(self):
        """Test error handling for None image."""
        with pytest.raises(ValueError, match="cannot be None"):
            apply_vignette(None)

    def test_apply_vignette_invalid_intensity_negative(self, sample_image):
        """Test error handling for negative intensity."""
        with pytest.raises(ValueError, match="Intensity must be between"):
            apply_vignette(sample_image, intensity=-0.1)

    def test_apply_vignette_invalid_intensity_too_high(self, sample_image):
        """Test error handling for intensity > 1.0."""
        with pytest.raises(ValueError, match="Intensity must be between"):
            apply_vignette(sample_image, intensity=1.5)

    def test_apply_vignette_invalid_radius_negative(self, sample_image):
        """Test error handling for negative radius."""
        with pytest.raises(ValueError, match="Radius must be between"):
            apply_vignette(sample_image, radius=-0.1)

    def test_apply_vignette_invalid_radius_too_high(self, sample_image):
        """Test error handling for radius > 1.0."""
        with pytest.raises(ValueError, match="Radius must be between"):
            apply_vignette(sample_image, radius=1.5)

    def test_apply_vignette_grayscale_input(self):
        """Test vignette on grayscale image."""
        gray_img = Image.new("L", (50, 50), color=128)
        result = apply_vignette(gray_img)

        assert result.mode == "RGB"


class TestValidateImage:
    """Tests for validate_image function."""

    def test_validate_image_basic(self, sample_image):
        """Test basic image validation."""
        result = validate_image(sample_image)

        assert result is True

    def test_validate_image_none(self):
        """Test validation of None image."""
        result = validate_image(None)

        assert result is False

    def test_validate_image_min_size_pass(self, sample_image):
        """Test validation with minimum size (pass)."""
        result = validate_image(sample_image, min_size=(50, 50))

        assert result is True

    def test_validate_image_min_size_fail(self, sample_image):
        """Test validation with minimum size (fail)."""
        result = validate_image(sample_image, min_size=(200, 200))

        assert result is False

    def test_validate_image_max_size_pass(self, sample_image):
        """Test validation with maximum size (pass)."""
        result = validate_image(sample_image, max_size=(200, 200))

        assert result is True

    def test_validate_image_max_size_fail(self, sample_image):
        """Test validation with maximum size (fail)."""
        result = validate_image(sample_image, max_size=(50, 50))

        assert result is False

    def test_validate_image_mode_pass(self, sample_image):
        """Test validation with required mode (pass)."""
        result = validate_image(sample_image, required_mode="RGB")

        assert result is True

    def test_validate_image_mode_fail(self, sample_image):
        """Test validation with required mode (fail)."""
        result = validate_image(sample_image, required_mode="L")

        assert result is False

    def test_validate_image_all_checks_pass(self, sample_image):
        """Test validation with all checks passing."""
        result = validate_image(
            sample_image,
            min_size=(50, 50),
            max_size=(200, 200),
            required_mode="RGB",
        )

        assert result is True

    def test_validate_image_all_checks_fail_size(self, sample_image):
        """Test validation with size check failing."""
        result = validate_image(
            sample_image,
            min_size=(200, 200),
            max_size=(300, 300),
            required_mode="RGB",
        )

        assert result is False

    def test_validate_image_landscape(self, sample_landscape_image):
        """Test validation of landscape image."""
        result = validate_image(sample_landscape_image, min_size=(100, 50))

        assert result is True

    def test_validate_image_portrait(self, sample_portrait_image):
        """Test validation of portrait image."""
        result = validate_image(sample_portrait_image, min_size=(50, 100))

        assert result is True
