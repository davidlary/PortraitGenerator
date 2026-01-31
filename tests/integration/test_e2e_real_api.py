"""End-to-end integration tests with real Google Gemini API.

These tests require a valid GOOGLE_API_KEY environment variable.
They are marked with @pytest.mark.e2e and can be run separately:

    pytest tests/integration/test_e2e_real_api.py -m e2e

WARNING: These tests make real API calls and may incur costs.
"""

import os
from pathlib import Path

import pytest

from portrait_generator import (
    PortraitClient,
    generate_portrait,
    generate_batch,
)
from portrait_generator.api.models import PortraitResult


# Skip all tests if no API key
pytestmark = pytest.mark.skipif(
    not os.getenv("GOOGLE_API_KEY"),
    reason="GOOGLE_API_KEY not set - skipping real API tests",
)


@pytest.fixture
def api_key():
    """Get API key from environment."""
    return os.getenv("GOOGLE_API_KEY")


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create temporary output directory."""
    output_dir = tmp_path / "e2e_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


class TestE2ERealAPI:
    """End-to-end tests with real Gemini API."""

    @pytest.mark.e2e
    @pytest.mark.slow
    def test_generate_single_portrait_all_styles(self, api_key, temp_output_dir):
        """Test generating all 4 styles for one subject using real API."""
        client = PortraitClient(
            api_key=api_key,
            output_dir=temp_output_dir,
        )

        # Generate portrait
        result = client.generate("William of Ockham")

        # Verify result
        assert isinstance(result, PortraitResult)
        assert result.success, f"Generation failed: {result.errors}"
        assert len(result.files) == 4, f"Expected 4 files, got {len(result.files)}"
        assert set(result.files.keys()) == {"BW", "Sepia", "Color", "Painting"}

        # Verify files exist
        for style, filepath in result.files.items():
            file_path = Path(filepath)
            assert file_path.exists(), f"{style} file not found: {filepath}"
            assert file_path.suffix == ".png"
            assert file_path.stat().st_size > 0, f"{style} file is empty"

        # Verify metadata
        assert result.metadata is not None
        assert result.metadata.name == "William of Ockham"
        assert result.metadata.birth_year > 0
        assert result.metadata.era != ""

        # Verify evaluations
        assert len(result.evaluation) == 4
        for style, evaluation in result.evaluation.items():
            assert evaluation is not None
            assert "technical" in evaluation.scores
            assert "visual_quality" in evaluation.scores

        # Verify generation time
        assert result.generation_time_seconds > 0

    @pytest.mark.e2e
    @pytest.mark.slow
    def test_generate_specific_styles(self, api_key, temp_output_dir):
        """Test generating specific styles only."""
        client = PortraitClient(
            api_key=api_key,
            output_dir=temp_output_dir,
        )

        # Generate only BW and Sepia
        result = client.generate(
            "Claude Shannon",
            styles=["BW", "Sepia"],
        )

        assert result.success
        assert len(result.files) == 2
        assert set(result.files.keys()) == {"BW", "Sepia"}

        # Verify files
        for style, filepath in result.files.items():
            assert Path(filepath).exists()

    @pytest.mark.e2e
    @pytest.mark.slow
    def test_convenience_function(self, api_key, temp_output_dir):
        """Test convenience function with real API."""
        result = generate_portrait(
            "Alan Turing",
            api_key=api_key,
            output_dir=temp_output_dir,
            styles=["Color"],
        )

        assert result.success
        assert len(result.files) == 1
        assert "Color" in result.files
        assert Path(result.files["Color"]).exists()

    @pytest.mark.e2e
    @pytest.mark.slow
    def test_batch_generation(self, api_key, temp_output_dir):
        """Test batch generation with real API."""
        subjects = [
            "Ada Lovelace",
            "Grace Hopper",
        ]

        results = generate_batch(
            subjects,
            api_key=api_key,
            output_dir=temp_output_dir,
            styles=["BW"],  # Just one style to save time
        )

        assert len(results) == 2

        for result in results:
            assert result.success, f"Failed for {result.subject}: {result.errors}"
            assert len(result.files) == 1
            assert "BW" in result.files

    @pytest.mark.e2e
    def test_skip_existing_files(self, api_key, temp_output_dir):
        """Test that existing files are skipped."""
        client = PortraitClient(
            api_key=api_key,
            output_dir=temp_output_dir,
        )

        # First generation
        result1 = client.generate(
            "Aristotle",
            styles=["BW"],
        )
        assert result1.success

        # Get file modification time
        file1_path = Path(result1.files["BW"])
        mtime1 = file1_path.stat().st_mtime

        # Second generation (should skip)
        result2 = client.generate(
            "Aristotle",
            styles=["BW"],
            force_regenerate=False,
        )
        assert result2.success

        # File should not be regenerated
        file2_path = Path(result2.files["BW"])
        mtime2 = file2_path.stat().st_mtime
        assert mtime1 == mtime2, "File was regenerated when it should have been skipped"

    @pytest.mark.e2e
    def test_force_regenerate(self, api_key, temp_output_dir):
        """Test force regeneration."""
        client = PortraitClient(
            api_key=api_key,
            output_dir=temp_output_dir,
        )

        # First generation
        result1 = client.generate(
            "Thomas Bayes",
            styles=["Color"],
        )
        assert result1.success

        # Force regeneration
        result2 = client.generate(
            "Thomas Bayes",
            styles=["Color"],
            force_regenerate=True,
        )
        assert result2.success

    @pytest.mark.e2e
    def test_check_status(self, api_key, temp_output_dir):
        """Test status checking."""
        client = PortraitClient(
            api_key=api_key,
            output_dir=temp_output_dir,
        )

        # Check status before generation
        status_before = client.check_status("George Boole")
        assert all(not exists for exists in status_before.values())

        # Generate one style
        result = client.generate(
            "George Boole",
            styles=["BW"],
        )
        assert result.success

        # Check status after generation
        status_after = client.check_status("George Boole")
        assert status_after["BW"] is True
        assert status_after["Sepia"] is False
        assert status_after["Color"] is False
        assert status_after["Painting"] is False

    @pytest.mark.e2e
    def test_invalid_subject_name(self, api_key, temp_output_dir):
        """Test error handling for invalid subject names."""
        client = PortraitClient(
            api_key=api_key,
            output_dir=temp_output_dir,
        )

        # Empty name should raise error
        with pytest.raises(ValueError, match="cannot be empty"):
            client.generate("")

        # Whitespace-only name should raise error
        with pytest.raises(ValueError, match="cannot be empty"):
            client.generate("   ")

    @pytest.mark.e2e
    def test_invalid_style(self, api_key, temp_output_dir):
        """Test error handling for invalid styles."""
        client = PortraitClient(
            api_key=api_key,
            output_dir=temp_output_dir,
        )

        # Invalid style should raise error
        with pytest.raises(ValueError, match="Invalid styles"):
            client.generate("Alan Turing", styles=["InvalidStyle"])


class TestE2EAPIClient:
    """Test Python API client initialization."""

    @pytest.mark.e2e
    def test_client_initialization_with_api_key(self, api_key, temp_output_dir):
        """Test client initialization with explicit API key."""
        client = PortraitClient(
            api_key=api_key,
            output_dir=temp_output_dir,
        )

        assert client.api_key == api_key
        assert client.output_dir == temp_output_dir
        assert client.gemini_client is not None
        assert client.generator is not None

    @pytest.mark.e2e
    def test_client_initialization_from_env(self, api_key, temp_output_dir):
        """Test client initialization from environment."""
        # API key should be read from GOOGLE_API_KEY env var
        client = PortraitClient(output_dir=temp_output_dir)

        assert client.api_key is not None
        assert client.output_dir == temp_output_dir

    def test_client_initialization_no_api_key(self, temp_output_dir, monkeypatch):
        """Test client initialization fails without API key."""
        # Remove API key from environment
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

        # Should raise error about missing API key
        with pytest.raises(Exception):  # Pydantic ValidationError
            PortraitClient(output_dir=temp_output_dir)


class TestE2EQualityMetrics:
    """Test quality evaluation with real portraits."""

    @pytest.mark.e2e
    @pytest.mark.slow
    def test_evaluation_scores(self, api_key, temp_output_dir):
        """Test that evaluation produces valid scores."""
        result = generate_portrait(
            "Geoffrey Hinton",
            api_key=api_key,
            output_dir=temp_output_dir,
            styles=["BW"],
        )

        assert result.success
        assert "BW" in result.evaluation

        evaluation = result.evaluation["BW"]

        # Check that all score categories are present
        assert "technical" in evaluation.scores
        assert "visual_quality" in evaluation.scores
        assert "style_adherence" in evaluation.scores
        assert "historical_accuracy" in evaluation.scores

        # Check score ranges
        for category, score in evaluation.scores.items():
            assert 0.0 <= score <= 1.0, f"{category} score out of range: {score}"

        # Check evaluation properties
        assert evaluation.overall_score >= 0.0
        assert evaluation.overall_score <= 1.0

    @pytest.mark.e2e
    @pytest.mark.slow
    def test_bw_style_adherence(self, api_key, temp_output_dir):
        """Test that BW portraits have high BW style adherence."""
        result = generate_portrait(
            "Yann LeCun",
            api_key=api_key,
            output_dir=temp_output_dir,
            styles=["BW"],
        )

        assert result.success
        evaluation = result.evaluation["BW"]

        # BW portraits should have high style adherence
        style_score = evaluation.scores.get("style_adherence", 0)
        assert style_score > 0.7, f"BW style adherence too low: {style_score}"


# Run e2e tests only when explicitly requested
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "e2e"])
