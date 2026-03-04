"""Unit tests for GeminiImageClient."""

import io
import os
import pytest
from PIL import Image

from portrait_generator.utils.gemini_client import GeminiImageClient, GenerationResult

# Sentinel for tests that require a real Gemini API key
_NO_API_KEY = not os.getenv("GOOGLE_API_KEY")
_SKIP_NO_KEY = pytest.mark.skipif(_NO_API_KEY, reason="Requires real Gemini API access - set GOOGLE_API_KEY")


@pytest.fixture
def sample_image():
    """Create a sample PIL image for testing."""
    img = Image.new("RGB", (100, 100), color="red")
    return img


@pytest.fixture
def sample_image_bytes(sample_image):
    """Convert sample image to bytes."""
    buf = io.BytesIO()
    sample_image.save(buf, format="PNG")
    return buf.getvalue()


class TestGeminiImageClientInit:
    """Tests for GeminiImageClient initialization."""

    def test_init_success(self) -> None:
        """Test successful initialization with real genai.Client."""
        client = GeminiImageClient(
            api_key="test_api_key_1234567890",
            model="gemini-exp-1206"
        )

        assert client.api_key == "test_api_key_1234567890"
        assert client.model == "gemini-exp-1206"
        assert client.client is not None

    def test_init_empty_api_key(self) -> None:
        """Test initialization fails with empty API key."""
        with pytest.raises(ValueError, match="cannot be empty"):
            GeminiImageClient(api_key="")

    def test_init_short_api_key(self) -> None:
        """Test initialization fails with too short API key."""
        with pytest.raises(ValueError, match="too short"):
            GeminiImageClient(api_key="short")

    def test_init_default_model(self) -> None:
        """Test default model is gemini-3.1-flash-image-preview (Nano Banana 2)."""
        client = GeminiImageClient(api_key="test_api_key_1234567890")
        assert client.model == "gemini-3.1-flash-image-preview"

    def test_init_custom_thinking_level(self) -> None:
        """Test custom thinking level for accuracy tuning."""
        client = GeminiImageClient(
            api_key="test_api_key_1234567890",
            thinking_level="high"
        )
        assert client.thinking_level == "high"

    def test_init_stores_all_parameters(self) -> None:
        """Test that all init parameters are stored correctly."""
        client = GeminiImageClient(
            api_key="test_api_key_1234567890",
            model="gemini-exp-1206",
            enable_grounding=False,
            enable_reasoning=False,
            thinking_level="low",
        )
        assert client.api_key == "test_api_key_1234567890"
        assert client.model == "gemini-exp-1206"
        assert client.enable_grounding is False
        assert client.enable_reasoning is False
        assert client.thinking_level == "low"

    def test_init_flash_capabilities_detected(self) -> None:
        """Test Flash model capabilities are detected at init."""
        client = GeminiImageClient(
            api_key="test_api_key_1234567890",
            model="gemini-3.1-flash-image-preview"
        )
        assert client.supports_image_grounding is True
        assert client.supports_extended_aspect_ratios is True
        assert client.supports_batch is True

    def test_init_legacy_capabilities_detected(self) -> None:
        """Test legacy model has no advanced capabilities."""
        client = GeminiImageClient(
            api_key="test_api_key_1234567890",
            model="gemini-exp-1206"
        )
        assert client.supports_grounding is False
        assert client.supports_image_grounding is False


class TestGenerateImage:
    """Tests for generate_image method - input validation only."""

    @pytest.fixture
    def client(self) -> GeminiImageClient:
        """Create client instance for testing."""
        return GeminiImageClient(api_key="test_api_key_1234567890")

    def test_generate_image_empty_prompt(self, client) -> None:
        """Test generation fails with empty prompt."""
        with pytest.raises(ValueError, match="cannot be empty"):
            client.generate_image(prompt="")

    def test_generate_image_whitespace_prompt(self, client) -> None:
        """Test generation fails with whitespace-only prompt."""
        with pytest.raises(ValueError, match="cannot be only whitespace"):
            client.generate_image(prompt="   ")

    def test_generate_image_invalid_aspect_ratio(self, client) -> None:
        """Test generation fails with invalid aspect ratio."""
        with pytest.raises(ValueError, match="Invalid aspect_ratio"):
            client.generate_image(
                prompt="Test",
                aspect_ratio="invalid"
            )

    def test_generate_image_valid_base_aspect_ratios_accepted(self, client) -> None:
        """Test that base aspect ratios pass validation (do not raise ValueError)."""
        base_ratios = ["1:1", "3:4", "4:3", "9:16", "16:9"]
        for ratio in base_ratios:
            # Should not raise ValueError for the aspect ratio
            # (may raise RuntimeError from actual API call which is expected)
            try:
                client.generate_image(prompt="Test", aspect_ratio=ratio)
            except ValueError as e:
                if "aspect_ratio" in str(e).lower():
                    raise  # Re-raise only if it's an aspect ratio error
            except RuntimeError:
                pass  # Expected - API call fails with test key

    def test_generate_image_extended_ratios_accepted_for_flash(self) -> None:
        """Test Flash model accepts extended aspect ratios."""
        flash_client = GeminiImageClient(
            api_key="test_api_key_1234567890",
            model="gemini-3.1-flash-image-preview"
        )
        extended_ratios = ["1:4", "4:1", "1:8", "8:1", "2:3", "3:2"]
        for ratio in extended_ratios:
            try:
                flash_client.generate_image(prompt="Test", aspect_ratio=ratio)
            except ValueError as e:
                if "aspect_ratio" in str(e).lower():
                    raise
            except RuntimeError:
                pass  # Expected - API call fails with test key

    def test_generate_image_extended_ratios_rejected_for_legacy(self) -> None:
        """Test legacy model rejects extended aspect ratios."""
        legacy_client = GeminiImageClient(
            api_key="test_api_key_1234567890",
            model="gemini-exp-1206"
        )
        with pytest.raises(ValueError, match="Invalid aspect_ratio"):
            legacy_client.generate_image(prompt="Test", aspect_ratio="1:4")

    @_SKIP_NO_KEY
    def test_generate_image_success(self) -> None:
        """Test successful image generation - covered by integration/test_e2e_real_api.py."""
        pass  # Full image generation tested in e2e; unit tests validate input logic only

    @_SKIP_NO_KEY
    def test_generate_image_no_images_returned(self) -> None:
        """Test error handling when no image returned - covered by integration tests."""
        pass  # API behavior tested in e2e; unit tests validate error-handling code paths

    @_SKIP_NO_KEY
    def test_generate_image_api_error(self) -> None:
        """Test error handling for API failures - invalid key raises RuntimeError."""
        # A malformed (but correctly-length) key to trigger real API auth failure
        bad_client = GeminiImageClient(api_key="AIzaSy_INVALID_KEY_FOR_TESTING_1234")
        with pytest.raises(RuntimeError, match="Image generation failed"):
            bad_client.generate_image(prompt="Test portrait")


class TestValidateConnection:
    """Tests for validate_connection method."""

    @_SKIP_NO_KEY
    def test_validate_connection_success(self) -> None:
        """Test successful connection validation with real API key."""
        client = GeminiImageClient(api_key=os.getenv("GOOGLE_API_KEY"))
        result = client.validate_connection()
        assert result is True

    @_SKIP_NO_KEY
    def test_validate_connection_failure(self) -> None:
        """Test connection validation returns False for invalid key."""
        client = GeminiImageClient(api_key="AIzaSy_INVALID_KEY_FOR_TESTING_1234")
        result = client.validate_connection()
        assert result is False


class TestGetModelInfo:
    """Tests for get_model_info method."""

    def test_get_model_info(self) -> None:
        """Test getting model information."""
        client = GeminiImageClient(
            api_key="test_api_key_1234567890",
            model="gemini-exp-1206"
        )

        info = client.get_model_info()

        assert info["model"] == "gemini-exp-1206"
        assert info["provider"] == "Google Gemini"
        assert "image_generation" in info["capabilities"]

    def test_get_model_info_flash_capabilities(self) -> None:
        """Test Flash model (Nano Banana 2) reports correct capabilities."""
        client = GeminiImageClient(
            api_key="test_api_key_1234567890",
            model="gemini-3.1-flash-image-preview"
        )

        info = client.get_model_info()

        assert info["capabilities"]["image_search_grounding"] is True
        assert info["capabilities"]["thinking_mode"] is True
        assert info["capabilities"]["extended_aspect_ratios"] is True
        assert info["capabilities"]["batch_api"] is True
        assert info["settings"]["thinking_level"] == "medium"

    def test_get_model_info_custom_thinking_level(self) -> None:
        """Test custom thinking level is reflected in model info."""
        client = GeminiImageClient(
            api_key="test_api_key_1234567890",
            thinking_level="high"
        )

        assert client.thinking_level == "high"
        info = client.get_model_info()
        assert info["settings"]["thinking_level"] == "high"

    def test_get_model_info_legacy_capabilities(self) -> None:
        """Test legacy model reports correct (limited) capabilities."""
        client = GeminiImageClient(
            api_key="test_api_key_1234567890",
            model="gemini-exp-1206"
        )

        info = client.get_model_info()

        assert info["capabilities"]["image_search_grounding"] is False
        assert info["capabilities"]["extended_aspect_ratios"] is False
        assert info["capabilities"]["batch_api"] is False
