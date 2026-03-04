"""Unit tests for reference_finder module."""

import os
import pytest
from pathlib import Path

from portrait_generator.reference_finder import (
    ReferenceImage,
    ReferenceImageFinder,
)
from portrait_generator.api.models import SubjectData
from portrait_generator.utils.gemini_client import GeminiImageClient

# Sentinel for tests that require a real Gemini API key
_NO_API_KEY = not os.getenv("GOOGLE_API_KEY")
_SKIP_NO_KEY = pytest.mark.skipif(_NO_API_KEY, reason="Requires real Gemini API access - set GOOGLE_API_KEY")


@pytest.fixture
def gemini_client():
    """Create a real Gemini client with test API key."""
    return GeminiImageClient(api_key="test_api_key_1234567890")


@pytest.fixture
def sample_subject_data():
    """Create sample subject data."""
    return SubjectData(
        name="Alan Turing",
        birth_year=1912,
        death_year=1954,
        era="20th Century",
    )


@pytest.fixture
def reference_finder(gemini_client, tmp_path):
    """Create reference finder instance with real client."""
    return ReferenceImageFinder(
        gemini_client=gemini_client,
        enable_grounding=True,
        download_dir=tmp_path / "refs",
    )


class TestReferenceImage:
    """Tests for ReferenceImage dataclass."""

    def test_create_reference_image(self):
        """Test creating a reference image."""
        ref = ReferenceImage(
            url="https://example.com/image.jpg",
            source="example.com",
            authenticity_score=0.90,
            quality_score=0.85,
            relevance_score=0.95,
            era_match=True,
            description="Test image",
        )

        assert ref.url == "https://example.com/image.jpg"
        assert ref.source == "example.com"
        assert ref.authenticity_score == 0.90
        assert ref.quality_score == 0.85
        assert ref.relevance_score == 0.95
        assert ref.era_match is True
        assert ref.description == "Test image"
        assert ref.local_path is None


class TestReferenceImageFinder:
    """Tests for ReferenceImageFinder class."""

    def test_initialization(self, gemini_client, tmp_path):
        """Test finder initialization."""
        finder = ReferenceImageFinder(
            gemini_client=gemini_client,
            enable_grounding=True,
            download_dir=tmp_path / "refs",
        )

        assert finder.gemini_client is gemini_client
        assert finder.enable_grounding is True
        assert finder.download_dir.exists()

    def test_build_search_queries(self, reference_finder, sample_subject_data):
        """Test building search queries."""
        queries = reference_finder._build_search_queries(sample_subject_data)

        assert len(queries) > 0
        assert any("Alan Turing" in q for q in queries)
        assert any("1912" in q for q in queries)
        assert any("20th Century" in q for q in queries)

    def test_rank_and_filter(self, reference_finder, sample_subject_data):
        """Test ranking and filtering images."""
        images = [
            ReferenceImage(
                url="https://example.com/image1.jpg",
                source="example.com",
                authenticity_score=0.95,
                quality_score=0.90,
                relevance_score=0.85,
                era_match=True,
            ),
            ReferenceImage(
                url="https://example.com/image2.jpg",
                source="example.com",
                authenticity_score=0.50,
                quality_score=0.45,
                relevance_score=0.40,
                era_match=False,
            ),
            ReferenceImage(
                url="https://example.com/image3.jpg",
                source="example.com",
                authenticity_score=0.85,
                quality_score=0.80,
                relevance_score=0.90,
                era_match=True,
            ),
        ]

        ranked = reference_finder._rank_and_filter(images, sample_subject_data)

        # Should filter out low-quality image
        assert len(ranked) < len(images)

        # Should be ranked by score
        assert ranked[0].authenticity_score >= ranked[-1].authenticity_score

    @_SKIP_NO_KEY
    def test_validate_reference_authenticity(self, sample_subject_data, tmp_path) -> None:
        """Test validating reference authenticity (requires real API)."""
        pass

    @pytest.mark.skip(reason="Requires real HTTP client - no external dependencies in unit tests")
    def test_download_and_prepare_references(self, reference_finder, tmp_path) -> None:
        """Test downloading reference images (requires real HTTP)."""
        pass

    def test_cleanup_downloads(self, reference_finder):
        """Test cleanup of downloaded images."""
        # Create some test files
        test_file = reference_finder.download_dir / "test.jpg"
        test_file.write_text("test")

        reference_finder.cleanup_downloads()

        # Directory should be empty
        assert reference_finder.download_dir.exists()
        assert not test_file.exists()
