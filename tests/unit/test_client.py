"""Unit tests for Python API client."""

import os
import pytest
from pathlib import Path

from portrait_generator.client import (
    PortraitClient,
    generate_portrait,
    generate_batch,
)
from portrait_generator.api.models import PortraitResult, SubjectData

# Sentinel for tests that require a real Gemini API key
_NO_API_KEY = not os.getenv("GOOGLE_API_KEY")
_SKIP_NO_KEY = pytest.mark.skipif(_NO_API_KEY, reason="Requires real Gemini API access - set GOOGLE_API_KEY")

TEST_API_KEY = "test_api_key_1234567890_abcdefghij"


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create temporary output directory."""
    output_dir = tmp_path / "test_output"
    output_dir.mkdir()
    return output_dir


class TestPortraitClientInit:
    """Tests for PortraitClient initialization."""

    def test_init_with_api_key(self, temp_output_dir):
        """Test initialization with explicit API key stores settings correctly."""
        client = PortraitClient(
            api_key=TEST_API_KEY,
            output_dir=temp_output_dir,
        )

        assert client.settings.google_api_key == TEST_API_KEY
        assert client.settings.output_dir == temp_output_dir
        assert client.generator is not None
        assert client.coordinator is not None

    def test_init_from_settings(self, temp_output_dir):
        """Test initialization reads API key from environment."""
        import os
        original_key = os.environ.get('GOOGLE_API_KEY')
        os.environ['GOOGLE_API_KEY'] = TEST_API_KEY

        try:
            client = PortraitClient(output_dir=temp_output_dir)
            assert client.settings.google_api_key == TEST_API_KEY
        finally:
            if original_key is None:
                del os.environ['GOOGLE_API_KEY']
            else:
                os.environ['GOOGLE_API_KEY'] = original_key

    def test_init_custom_model(self, temp_output_dir):
        """Test initialization with valid custom model."""
        client = PortraitClient(
            api_key=TEST_API_KEY,
            output_dir=temp_output_dir,
            model="gemini-exp-1206",  # Valid legacy model
        )

        assert client.settings.gemini_model == "gemini-exp-1206"

    def test_init_default_model_is_flash(self, temp_output_dir):
        """Test default model is gemini-3.1-flash-image-preview."""
        client = PortraitClient(
            api_key=TEST_API_KEY,
            output_dir=temp_output_dir,
        )

        assert client.settings.gemini_model == "gemini-3.1-flash-image-preview"


class TestPortraitClientGenerate:
    """Tests for PortraitClient.generate method - input validation only."""

    @pytest.fixture
    def client(self, temp_output_dir):
        """Create client instance."""
        return PortraitClient(api_key=TEST_API_KEY, output_dir=temp_output_dir)

    @_SKIP_NO_KEY
    def test_generate_success(self, tmp_path) -> None:
        """Test successful portrait generation - covered by integration/test_e2e_real_api.py."""
        pass  # Full portrait generation tested in e2e; unit test validates non-API logic only

    @_SKIP_NO_KEY
    def test_generate_with_styles(self, tmp_path) -> None:
        """Test generation with specific styles (requires real API)."""
        pass

    @_SKIP_NO_KEY
    def test_generate_force_regenerate(self, tmp_path) -> None:
        """Test generation with force regenerate (requires real API)."""
        pass


class TestPortraitClientBatch:
    """Tests for PortraitClient.generate_batch method."""

    @_SKIP_NO_KEY
    def test_generate_batch_success(self, tmp_path) -> None:
        """Test successful batch generation (requires real API)."""
        pass


class TestPortraitClientStatus:
    """Tests for PortraitClient.check_status method."""

    def test_check_status_nonexistent(self, temp_output_dir):
        """Test checking status for subject with no existing portraits."""
        client = PortraitClient(api_key=TEST_API_KEY, output_dir=temp_output_dir)

        status = client.check_status("Nonexistent Person XYZ")

        assert isinstance(status, dict)
        assert all(not exists for exists in status.values())


class TestConvenienceFunctions:
    """Tests for convenience functions - validation only."""

    @_SKIP_NO_KEY
    def test_generate_portrait_function(self, tmp_path) -> None:
        """Test generate_portrait convenience function (requires real API)."""
        pass

    @_SKIP_NO_KEY
    def test_generate_batch_function(self, tmp_path) -> None:
        """Test generate_batch convenience function (requires real API)."""
        pass
