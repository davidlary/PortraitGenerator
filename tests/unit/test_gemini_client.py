"""Unit tests for GeminiImageClient."""

import io
import sys
from unittest.mock import Mock, MagicMock, patch

import pytest
from PIL import Image

from portrait_generator.utils.gemini_client import GeminiImageClient


@pytest.fixture
def mock_genai():
    """Mock google.genai module."""
    # Create mock module
    mock_genai_module = MagicMock()

    # Setup mock client
    mock_client = Mock()
    mock_genai_module.Client.return_value = mock_client

    # Setup mock types with a simple config object
    mock_types = Mock()

    # Create a mock GenerateImagesConfig that returns itself
    mock_config = Mock()
    mock_config.number_of_images = 1
    mock_config.aspect_ratio = "3:4"
    mock_types.GenerateImagesConfig.return_value = mock_config

    mock_genai_module.types = mock_types

    # Ensure parent google module exists
    if 'google' not in sys.modules:
        sys.modules['google'] = MagicMock()

    # Inject into sys.modules
    sys.modules['google.genai'] = mock_genai_module

    yield mock_genai_module, mock_client, mock_types

    # Cleanup
    if 'google.genai' in sys.modules:
        del sys.modules['google.genai']


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

    def test_init_success(self, mock_genai) -> None:
        """Test successful initialization."""
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

    def test_init_default_model(self, mock_genai) -> None:
        """Test default model is used."""
        client = GeminiImageClient(api_key="test_api_key_1234567890")
        assert client.model == "gemini-3-pro-image-preview"

    def test_init_missing_package(self) -> None:
        """Test initialization fails if google-genai not installed."""
        # Save current sys.modules state
        saved_modules = sys.modules.copy()

        # Remove google.genai from sys.modules
        if 'google.genai' in sys.modules:
            del sys.modules['google.genai']

        # Create a module that raises ImportError on genai access
        import types
        mock_google = types.ModuleType('google')

        def _getattr(name):
            if name == 'genai':
                raise ImportError("No module named 'google.genai'")
            raise AttributeError(f"module 'google' has no attribute '{name}'")

        mock_google.__getattr__ = _getattr
        sys.modules['google'] = mock_google

        try:
            with pytest.raises(ImportError, match="google-genai package not installed"):
                GeminiImageClient(api_key="test_api_key_1234567890")
        finally:
            # Restore sys.modules
            sys.modules.clear()
            sys.modules.update(saved_modules)


class TestGenerateImage:
    """Tests for generate_image method."""

    @pytest.fixture
    def client(self, mock_genai) -> GeminiImageClient:
        """Create client instance for testing."""
        return GeminiImageClient(api_key="test_api_key_1234567890")

    def test_generate_image_success(
        self, client, mock_genai, sample_image_bytes
    ) -> None:
        """Test successful image generation."""
        _, mock_client, _ = mock_genai

        # Setup mock response
        mock_response = Mock()
        mock_image_data = Mock()
        mock_image_data.image.image_bytes = sample_image_bytes
        mock_response.generated_images = [mock_image_data]

        # Mock generate_images to avoid config validation
        def mock_generate_images(**kwargs):
            # Just return the response without validating config
            return mock_response

        mock_client.models.generate_images = mock_generate_images

        # Generate image
        result = client.generate_image(
            prompt="Test portrait",
            aspect_ratio="3:4"
        )

        # Verify result - returns GenerationResult, not Image
        from portrait_generator.utils.gemini_client import GenerationResult
        assert isinstance(result, GenerationResult)
        assert isinstance(result.image, Image.Image)
        assert result.image.size == (100, 100)

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

    def test_generate_image_valid_aspect_ratios(
        self, client, mock_genai, sample_image_bytes
    ) -> None:
        """Test all valid aspect ratios are accepted."""
        _, mock_client, _ = mock_genai

        # Setup mock response
        mock_response = Mock()
        mock_image_data = Mock()
        mock_image_data.image.image_bytes = sample_image_bytes
        mock_response.generated_images = [mock_image_data]

        # Mock generate_images to avoid config validation
        def mock_generate_images(**kwargs):
            return mock_response

        mock_client.models.generate_images = mock_generate_images

        valid_ratios = ["1:1", "3:4", "4:3", "9:16", "16:9"]

        for ratio in valid_ratios:
            result = client.generate_image(
                prompt="Test",
                aspect_ratio=ratio
            )
            from portrait_generator.utils.gemini_client import GenerationResult
            assert isinstance(result, GenerationResult)
            assert isinstance(result.image, Image.Image)

    def test_generate_image_no_images_returned(
        self, client, mock_genai
    ) -> None:
        """Test error handling when no images returned."""
        _, mock_client, _ = mock_genai

        # Setup mock response with no images
        mock_response = Mock()
        mock_response.generated_images = []

        # Mock generate_images to avoid config validation
        def mock_generate_images(**kwargs):
            return mock_response

        mock_client.models.generate_images = mock_generate_images

        with pytest.raises(RuntimeError, match="No images returned"):
            client.generate_image(prompt="Test")

    def test_generate_image_api_error(self, client, mock_genai) -> None:
        """Test error handling for API failures."""
        _, mock_client, _ = mock_genai

        # Setup mock to raise exception
        mock_client.models.generate_images.side_effect = Exception(
            "API Error"
        )

        with pytest.raises(RuntimeError, match="Image generation failed"):
            client.generate_image(prompt="Test")


class TestValidateConnection:
    """Tests for validate_connection method."""

    @pytest.fixture
    def client(self, mock_genai) -> GeminiImageClient:
        """Create client instance for testing."""
        return GeminiImageClient(api_key="test_api_key_1234567890")

    def test_validate_connection_success(
        self, client, mock_genai, sample_image_bytes
    ) -> None:
        """Test successful connection validation."""
        _, mock_client, _ = mock_genai

        # Setup mock response
        mock_response = Mock()
        mock_image_data = Mock()
        mock_image_data.image.image_bytes = sample_image_bytes
        mock_response.generated_images = [mock_image_data]

        # Mock generate_images to avoid config validation
        def mock_generate_images(**kwargs):
            return mock_response

        mock_client.models.generate_images = mock_generate_images

        result = client.validate_connection()
        assert result is True

    def test_validate_connection_failure(self, client, mock_genai) -> None:
        """Test connection validation failure."""
        _, mock_client, _ = mock_genai

        # Setup mock to raise exception
        mock_client.models.generate_images.side_effect = Exception(
            "Connection failed"
        )

        result = client.validate_connection()
        assert result is False


class TestGetModelInfo:
    """Tests for get_model_info method."""

    def test_get_model_info(self, mock_genai) -> None:
        """Test getting model information."""
        client = GeminiImageClient(
            api_key="test_api_key_1234567890",
            model="test-model"
        )

        info = client.get_model_info()

        assert info["model"] == "test-model"
        assert info["provider"] == "Google Gemini"
        assert "image_generation" in info["capabilities"]
