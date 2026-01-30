"""Unit tests for API models."""

import pytest
from pydantic import ValidationError

from portrait_generator.api.models import (
    PortraitRequest,
    SubjectData,
    EvaluationResult,
    PortraitResult,
    HealthCheckResponse,
    StatusResponse,
)


class TestPortraitRequest:
    """Tests for PortraitRequest model."""

    def test_valid_request(self) -> None:
        """Test valid request."""
        request = PortraitRequest(subject_name="Albert Einstein")
        assert request.subject_name == "Albert Einstein"
        assert request.force_regenerate is False
        assert request.styles is None

    def test_with_styles(self) -> None:
        """Test request with specific styles."""
        request = PortraitRequest(
            subject_name="Marie Curie",
            styles=["BW", "Sepia"],
        )
        assert request.styles == ["BW", "Sepia"]

    def test_invalid_style(self) -> None:
        """Test validation fails for invalid style."""
        with pytest.raises(ValidationError, match="Invalid styles"):
            PortraitRequest(
                subject_name="Test",
                styles=["BW", "Invalid"],
            )

    def test_name_too_short(self) -> None:
        """Test validation fails for too short name."""
        with pytest.raises(ValidationError):
            PortraitRequest(subject_name="A")

    def test_name_too_long(self) -> None:
        """Test validation fails for too long name."""
        with pytest.raises(ValidationError):
            PortraitRequest(subject_name="A" * 101)

    def test_force_regenerate(self) -> None:
        """Test force_regenerate flag."""
        request = PortraitRequest(
            subject_name="Test",
            force_regenerate=True,
        )
        assert request.force_regenerate is True


class TestSubjectData:
    """Tests for SubjectData model."""

    def test_valid_subject_deceased(self) -> None:
        """Test valid subject data for deceased person."""
        data = SubjectData(
            name="Albert Einstein",
            birth_year=1879,
            death_year=1955,
            era="20th Century",
        )
        assert data.name == "Albert Einstein"
        assert data.birth_year == 1879
        assert data.death_year == 1955

    def test_valid_subject_living(self) -> None:
        """Test valid subject data for living person."""
        data = SubjectData(
            name="Geoffrey Hinton",
            birth_year=1947,
            death_year=None,
            era="20th-21st Century",
        )
        assert data.death_year is None

    def test_formatted_years_deceased(self) -> None:
        """Test formatted years for deceased person."""
        data = SubjectData(
            name="Test",
            birth_year=1900,
            death_year=2000,
            era="Test",
        )
        assert data.formatted_years == "1900-2000"

    def test_formatted_years_living(self) -> None:
        """Test formatted years for living person."""
        data = SubjectData(
            name="Test",
            birth_year=1950,
            era="Test",
        )
        assert data.formatted_years == "1950-Present"

    def test_with_appearance_notes(self) -> None:
        """Test subject data with appearance notes."""
        data = SubjectData(
            name="Test",
            birth_year=1900,
            era="Test",
            appearance_notes=["Gray hair", "Mustache"],
        )
        assert len(data.appearance_notes) == 2


class TestEvaluationResult:
    """Tests for EvaluationResult model."""

    def test_passed_evaluation(self) -> None:
        """Test passed evaluation."""
        result = EvaluationResult(
            passed=True,
            scores={"visual_quality": 0.9, "accuracy": 0.85},
            feedback=["Excellent quality"],
        )
        assert result.passed is True
        assert len(result.scores) == 2

    def test_failed_evaluation(self) -> None:
        """Test failed evaluation."""
        result = EvaluationResult(
            passed=False,
            scores={"visual_quality": 0.6},
            issues=["Low quality"],
        )
        assert result.passed is False
        assert len(result.issues) == 1

    def test_overall_score(self) -> None:
        """Test overall score calculation."""
        result = EvaluationResult(
            passed=True,
            scores={"a": 0.8, "b": 0.9, "c": 0.7},
        )
        expected = (0.8 + 0.9 + 0.7) / 3
        assert abs(result.overall_score - expected) < 0.01

    def test_overall_score_empty(self) -> None:
        """Test overall score with no scores."""
        result = EvaluationResult(passed=False)
        assert result.overall_score == 0.0


class TestPortraitResult:
    """Tests for PortraitResult model."""

    def test_successful_result(self) -> None:
        """Test successful portrait result."""
        metadata = SubjectData(
            name="Test",
            birth_year=1900,
            era="Test",
        )
        result = PortraitResult(
            subject="Test",
            metadata=metadata,
            success=True,
        )
        assert result.success is True
        assert result.subject == "Test"

    def test_with_files(self) -> None:
        """Test result with generated files."""
        metadata = SubjectData(
            name="Test",
            birth_year=1900,
            era="Test",
        )
        result = PortraitResult(
            subject="Test",
            files={"BW": "/path/to/bw.png", "Color": "/path/to/color.png"},
            metadata=metadata,
            success=True,
        )
        assert len(result.files) == 2

    def test_all_passed_true(self) -> None:
        """Test all_passed when all evaluations pass."""
        metadata = SubjectData(
            name="Test",
            birth_year=1900,
            era="Test",
        )
        result = PortraitResult(
            subject="Test",
            metadata=metadata,
            evaluation={
                "BW": EvaluationResult(passed=True),
                "Color": EvaluationResult(passed=True),
            },
            success=True,
        )
        assert result.all_passed is True

    def test_all_passed_false(self) -> None:
        """Test all_passed when any evaluation fails."""
        metadata = SubjectData(
            name="Test",
            birth_year=1900,
            era="Test",
        )
        result = PortraitResult(
            subject="Test",
            metadata=metadata,
            evaluation={
                "BW": EvaluationResult(passed=True),
                "Color": EvaluationResult(passed=False),
            },
            success=True,
        )
        assert result.all_passed is False

    def test_all_passed_empty(self) -> None:
        """Test all_passed with no evaluations."""
        metadata = SubjectData(
            name="Test",
            birth_year=1900,
            era="Test",
        )
        result = PortraitResult(
            subject="Test",
            metadata=metadata,
            success=True,
        )
        assert result.all_passed is False


class TestHealthCheckResponse:
    """Tests for HealthCheckResponse model."""

    def test_health_check(self) -> None:
        """Test health check response."""
        response = HealthCheckResponse(
            status="healthy",
            version="1.0.0",
            gemini_configured=True,
            output_dir_writable=True,
            timestamp="2026-01-30T00:00:00Z",
        )
        assert response.status == "healthy"
        assert response.gemini_configured is True


class TestStatusResponse:
    """Tests for StatusResponse model."""

    def test_exists_true(self) -> None:
        """Test status when files exist."""
        response = StatusResponse(
            subject="Test Person",
            exists=True,
            files=["/path/to/file1.png", "/path/to/file2.png"],
            generated_at="2026-01-30T00:00:00Z",
        )
        assert response.subject == "Test Person"
        assert response.exists is True
        assert len(response.files) == 2

    def test_exists_false(self) -> None:
        """Test status when files don't exist."""
        response = StatusResponse(subject="Test Person", exists=False)
        assert response.subject == "Test Person"
        assert response.exists is False
        assert len(response.files) == 0
        assert response.generated_at is None
