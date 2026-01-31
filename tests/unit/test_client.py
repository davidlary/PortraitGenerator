"""Unit tests for Python API client."""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

from portrait_generator.client import (
    PortraitClient,
    generate_portrait,
    generate_batch,
)
from portrait_generator.api.models import PortraitResult, SubjectData


@pytest.fixture
def mock_api_key():
    """Mock API key."""
    return "test_api_key_1234567890_abcdefghij"


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create temporary output directory."""
    output_dir = tmp_path / "test_output"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def mock_gemini_client():
    """Mock Gemini client."""
    return Mock()


@pytest.fixture
def mock_generator():
    """Mock PortraitGenerator."""
    generator = Mock()

    # Mock successful result
    success_result = PortraitResult(
        subject="Test Subject",
        files={"BW": "test_BW.png", "Color": "test_Color.png"},
        prompts={"BW": "test_BW_prompt.md", "Color": "test_Color_prompt.md"},
        metadata=SubjectData(
            name="Test Subject",
            birth_year=1900,
            death_year=2000,
            era="20th Century",
        ),
        evaluation={},
        generation_time_seconds=10.0,
        success=True,
        errors=[],
    )

    generator.generate_portrait.return_value = success_result
    generator.generate_batch.return_value = [success_result]
    generator.check_existing_portraits.return_value = {
        "BW": True,
        "Sepia": False,
        "Color": True,
        "Painting": False,
    }

    return generator


class TestPortraitClientInit:
    """Tests for PortraitClient initialization."""

    @patch("portrait_generator.client.GeminiImageClient")
    @patch("portrait_generator.client.PortraitGenerator")
    def test_init_with_api_key(
        self, mock_pg, mock_gc, mock_api_key, temp_output_dir
    ):
        """Test initialization with explicit API key."""
        client = PortraitClient(
            api_key=mock_api_key,
            output_dir=temp_output_dir,
        )

        assert client.api_key == mock_api_key
        assert client.output_dir == temp_output_dir
        assert client.model == "gemini-exp-1206"

        # Verify Gemini client was created
        mock_gc.assert_called_once()

    @patch("portrait_generator.client.GeminiImageClient")
    @patch("portrait_generator.client.PortraitGenerator")
    @patch("portrait_generator.client.get_settings")
    def test_init_from_settings(
        self, mock_settings, mock_pg, mock_gc, mock_api_key, temp_output_dir
    ):
        """Test initialization reads from settings when no API key provided."""
        # Mock settings
        settings = Mock()
        settings.google_api_key = mock_api_key
        settings.output_dir = str(temp_output_dir)
        mock_settings.return_value = settings

        client = PortraitClient()

        assert client.api_key == mock_api_key

    @patch("portrait_generator.client.GeminiImageClient")
    @patch("portrait_generator.client.PortraitGenerator")
    def test_init_custom_model(
        self, mock_pg, mock_gc, mock_api_key, temp_output_dir
    ):
        """Test initialization with custom model."""
        client = PortraitClient(
            api_key=mock_api_key,
            output_dir=temp_output_dir,
            model="custom-model",
        )

        assert client.model == "custom-model"


class TestPortraitClientGenerate:
    """Tests for PortraitClient.generate method."""

    @patch("portrait_generator.client.PortraitGenerator")
    def test_generate_success(
        self, mock_pg_class, mock_api_key, temp_output_dir, mock_generator
    ):
        """Test successful portrait generation."""
        mock_pg_class.return_value = mock_generator

        client = PortraitClient(
            api_key=mock_api_key,
            output_dir=temp_output_dir,
        )

        result = client.generate("Test Subject")

        assert result.success
        assert result.subject == "Test Subject"
        assert len(result.files) == 2

        # Verify generator was called correctly
        mock_generator.generate_portrait.assert_called_once_with(
            subject_name="Test Subject",
            force_regenerate=False,
            styles=None,
        )

    @patch("portrait_generator.client.PortraitGenerator")
    def test_generate_with_styles(
        self, mock_pg_class, mock_api_key, temp_output_dir, mock_generator
    ):
        """Test generation with specific styles."""
        mock_pg_class.return_value = mock_generator

        client = PortraitClient(
            api_key=mock_api_key,
            output_dir=temp_output_dir,
        )

        result = client.generate("Test Subject", styles=["BW", "Sepia"])

        mock_generator.generate_portrait.assert_called_once_with(
            subject_name="Test Subject",
            force_regenerate=False,
            styles=["BW", "Sepia"],
        )

    @patch("portrait_generator.client.PortraitGenerator")
    def test_generate_force_regenerate(
        self, mock_pg_class, mock_api_key, temp_output_dir, mock_generator
    ):
        """Test generation with force regenerate."""
        mock_pg_class.return_value = mock_generator

        client = PortraitClient(
            api_key=mock_api_key,
            output_dir=temp_output_dir,
        )

        result = client.generate("Test Subject", force_regenerate=True)

        mock_generator.generate_portrait.assert_called_once_with(
            subject_name="Test Subject",
            force_regenerate=True,
            styles=None,
        )


class TestPortraitClientBatch:
    """Tests for PortraitClient.generate_batch method."""

    @patch("portrait_generator.client.PortraitGenerator")
    def test_generate_batch_success(
        self, mock_pg_class, mock_api_key, temp_output_dir, mock_generator
    ):
        """Test successful batch generation."""
        mock_pg_class.return_value = mock_generator

        client = PortraitClient(
            api_key=mock_api_key,
            output_dir=temp_output_dir,
        )

        subjects = ["Subject 1", "Subject 2"]
        results = client.generate_batch(subjects)

        assert len(results) == 1  # Mock returns single result
        mock_generator.generate_batch.assert_called_once_with(
            subject_names=subjects,
            force_regenerate=False,
            styles=None,
        )


class TestPortraitClientStatus:
    """Tests for PortraitClient.check_status method."""

    @patch("portrait_generator.client.PortraitGenerator")
    def test_check_status(
        self, mock_pg_class, mock_api_key, temp_output_dir, mock_generator
    ):
        """Test checking portrait status."""
        mock_pg_class.return_value = mock_generator

        client = PortraitClient(
            api_key=mock_api_key,
            output_dir=temp_output_dir,
        )

        status = client.check_status("Test Subject")

        assert status["BW"] is True
        assert status["Sepia"] is False
        assert status["Color"] is True
        assert status["Painting"] is False

        mock_generator.check_existing_portraits.assert_called_once_with("Test Subject")


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    @patch("portrait_generator.client.PortraitClient")
    def test_generate_portrait_function(self, mock_client_class, mock_api_key):
        """Test generate_portrait convenience function."""
        # Mock client and its generate method
        mock_client = Mock()
        mock_result = PortraitResult(
            subject="Test",
            files={},
            prompts={},
            metadata=SubjectData(
                name="Test",
                birth_year=1900,
                death_year=2000,
                era="Test",
            ),
            evaluation={},
            generation_time_seconds=1.0,
            success=True,
            errors=[],
        )
        mock_client.generate.return_value = mock_result
        mock_client_class.return_value = mock_client

        result = generate_portrait(
            "Test Subject",
            api_key=mock_api_key,
            styles=["BW"],
        )

        # Verify client was created
        mock_client_class.assert_called_once()

        # Verify generate was called
        mock_client.generate.assert_called_once_with(
            subject_name="Test Subject",
            force_regenerate=False,
            styles=["BW"],
        )

        assert result == mock_result

    @patch("portrait_generator.client.PortraitClient")
    def test_generate_batch_function(self, mock_client_class, mock_api_key):
        """Test generate_batch convenience function."""
        # Mock client and its generate_batch method
        mock_client = Mock()
        mock_result = [
            PortraitResult(
                subject="Test",
                files={},
                prompts={},
                metadata=SubjectData(
                    name="Test",
                    birth_year=1900,
                    death_year=2000,
                    era="Test",
                ),
                evaluation={},
                generation_time_seconds=1.0,
                success=True,
                errors=[],
            )
        ]
        mock_client.generate_batch.return_value = mock_result
        mock_client_class.return_value = mock_client

        subjects = ["Subject 1", "Subject 2"]
        results = generate_batch(
            subjects,
            api_key=mock_api_key,
        )

        # Verify client was created
        mock_client_class.assert_called_once()

        # Verify generate_batch was called
        mock_client.generate_batch.assert_called_once_with(
            subject_names=subjects,
            force_regenerate=False,
            styles=None,
        )

        assert results == mock_result
