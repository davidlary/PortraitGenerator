"""Unit tests for reference_finder module."""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

from portrait_generator.reference_finder import (
    ReferenceImage,
    ReferenceImageFinder,
)
from portrait_generator.api.models import SubjectData


@pytest.fixture
def mock_gemini_client():
    """Create mock Gemini client."""
    client = Mock()
    client.query_with_grounding = Mock(return_value="Mock search response with https://example.com/image.jpg")
    return client


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
def reference_finder(mock_gemini_client, tmp_path):
    """Create reference finder instance."""
    return ReferenceImageFinder(
        gemini_client=mock_gemini_client,
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

    def test_initialization(self, mock_gemini_client, tmp_path):
        """Test finder initialization."""
        finder = ReferenceImageFinder(
            gemini_client=mock_gemini_client,
            enable_grounding=True,
            download_dir=tmp_path / "refs",
        )

        assert finder.gemini_client == mock_gemini_client
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

    def test_validate_reference_authenticity(self, reference_finder, sample_subject_data):
        """Test validating reference authenticity."""
        ref_image = ReferenceImage(
            url="https://example.com/image.jpg",
            source="example.com",
            authenticity_score=0.90,
            quality_score=0.85,
            relevance_score=0.95,
            era_match=True,
        )

        # Mock grounding response
        reference_finder.gemini_client.query_with_grounding.return_value = (
            "This image is AUTHENTIC and shows Alan Turing."
        )

        is_authentic = reference_finder.validate_reference_authenticity(
            ref_image, sample_subject_data
        )

        assert isinstance(is_authentic, bool)

    @patch('portrait_generator.reference_finder.httpx.Client')
    def test_download_and_prepare_references(self, mock_http, reference_finder, tmp_path):
        """Test downloading reference images."""
        # Create mock image data
        from PIL import Image
        from io import BytesIO

        test_image = Image.new('RGB', (512, 512), color='red')
        img_bytes = BytesIO()
        test_image.save(img_bytes, format='PNG')
        img_bytes.seek(0)

        # Mock HTTP response
        mock_response = Mock()
        mock_response.content = img_bytes.read()
        mock_response.raise_for_status = Mock()

        mock_client_instance = Mock()
        mock_client_instance.get.return_value = mock_response
        mock_http.return_value = mock_client_instance

        # Override the http_client
        reference_finder.http_client = mock_client_instance

        images = [
            ReferenceImage(
                url="https://example.com/image1.jpg",
                source="example.com",
                authenticity_score=0.90,
                quality_score=0.85,
                relevance_score=0.95,
                era_match=True,
            ),
        ]

        paths = reference_finder.download_and_prepare_references(images)

        assert len(paths) > 0
        assert all(isinstance(p, Path) for p in paths)

    def test_cleanup_downloads(self, reference_finder):
        """Test cleanup of downloaded images."""
        # Create some test files
        test_file = reference_finder.download_dir / "test.jpg"
        test_file.write_text("test")

        reference_finder.cleanup_downloads()

        # Directory should be empty
        assert reference_finder.download_dir.exists()
        assert not test_file.exists()
