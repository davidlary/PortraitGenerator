"""Unit tests for pre_generation_validator module."""

import pytest
from unittest.mock import Mock

from portrait_generator.pre_generation_validator import (
    ValidationResult,
    PreGenerationValidator,
)
from portrait_generator.api.models import SubjectData
from portrait_generator.reference_finder import ReferenceImage


@pytest.fixture
def mock_gemini_client():
    """Create mock Gemini client."""
    client = Mock()
    client.query_with_grounding = Mock(return_value="Verified: This is correct and accurate.")
    return client


@pytest.fixture
def sample_subject_data():
    """Create valid sample subject data."""
    return SubjectData(
        name="Alan Turing",
        birth_year=1912,
        death_year=1954,
        era="20th Century",
    )


@pytest.fixture
def validator(mock_gemini_client):
    """Create validator instance."""
    return PreGenerationValidator(
        gemini_client=mock_gemini_client,
        enable_fact_checking=True,
    )


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_create_validation_result(self):
        """Test creating validation result."""
        result = ValidationResult(
            is_valid=True,
            confidence=0.95,
            issues=[],
            warnings=["Warning 1"],
            recommendations=["Recommendation 1"],
            fact_check_results={"birth_year": True},
            reference_validation={},
        )

        assert result.is_valid is True
        assert result.confidence == 0.95
        assert len(result.issues) == 0
        assert len(result.warnings) == 1
        assert len(result.recommendations) == 1


class TestPreGenerationValidator:
    """Tests for PreGenerationValidator class."""

    def test_initialization(self, mock_gemini_client):
        """Test validator initialization."""
        validator = PreGenerationValidator(
            gemini_client=mock_gemini_client,
            enable_fact_checking=True,
        )

        assert validator.gemini_client == mock_gemini_client
        assert validator.enable_fact_checking is True

    def test_validate_valid_inputs(self, validator, sample_subject_data):
        """Test validation with valid inputs."""
        result = validator.validate(
            subject_data=sample_subject_data,
            style="BW",
            prompt="Generate a BW portrait of Alan Turing from the 20th Century.",
            reference_images=None,
        )

        assert isinstance(result, ValidationResult)
        # Should pass basic validation
        assert result.confidence > 0.5

    def test_validate_invalid_subject_data(self, validator):
        """Test validation with invalid subject data."""
        invalid_data = SubjectData(
            name="",  # Empty name
            birth_year=0,  # Invalid year
            death_year=None,
            era="",
        )

        result = validator.validate(
            subject_data=invalid_data,
            style="BW",
            prompt="Test prompt",
        )

        assert result.is_valid is False
        assert len(result.issues) > 0

    def test_validate_invalid_style(self, validator, sample_subject_data):
        """Test validation with invalid style."""
        result = validator.validate(
            subject_data=sample_subject_data,
            style="INVALID_STYLE",
            prompt="Test prompt",
        )

        assert result.is_valid is False
        assert any("style" in issue.lower() for issue in result.issues)

    def test_validate_short_prompt(self, validator, sample_subject_data):
        """Test validation with too short prompt."""
        result = validator.validate(
            subject_data=sample_subject_data,
            style="BW",
            prompt="Short",  # Too short
        )

        assert result.is_valid is False
        assert any("prompt" in issue.lower() for issue in result.issues)

    def test_validate_subject_data(self, validator, sample_subject_data):
        """Test subject data validation."""
        issues = validator._validate_subject_data(sample_subject_data)

        # Valid data should have no issues
        assert len(issues) == 0

    def test_validate_subject_data_invalid_years(self, validator):
        """Test validation with invalid years."""
        invalid_data = SubjectData(
            name="Test Subject",
            birth_year=2000,
            death_year=1900,  # Death before birth
            era="Test Era",
        )

        issues = validator._validate_subject_data(invalid_data)

        assert len(issues) > 0
        assert any("death year" in issue.lower() for issue in issues)

    def test_validate_style(self, validator):
        """Test style validation."""
        # Valid styles
        assert len(validator._validate_style("BW")) == 0
        assert len(validator._validate_style("Sepia")) == 0
        assert len(validator._validate_style("Color")) == 0
        assert len(validator._validate_style("Painting")) == 0

        # Invalid style
        assert len(validator._validate_style("Invalid")) > 0

    def test_validate_prompt(self, validator, sample_subject_data):
        """Test prompt validation."""
        # Valid prompt
        issues, warnings = validator._validate_prompt(
            "Generate a portrait of Alan Turing from the 20th Century.",
            sample_subject_data,
        )

        assert len(issues) == 0

    def test_validate_prompt_missing_subject(self, validator, sample_subject_data):
        """Test prompt validation with missing subject name."""
        issues, warnings = validator._validate_prompt(
            "Generate a portrait of someone from the 20th Century.",
            sample_subject_data,
        )

        # Should have warning about missing subject name
        assert len(warnings) > 0

    def test_validate_reference_images(self, validator, sample_subject_data):
        """Test reference image validation."""
        references = [
            ReferenceImage(
                url="https://example.com/image1.jpg",
                source="Library of Congress",
                authenticity_score=0.95,
                quality_score=0.90,
                relevance_score=0.85,
                era_match=True,
            ),
            ReferenceImage(
                url="https://example.com/image2.jpg",
                source="Example",
                authenticity_score=0.60,  # Low authenticity
                quality_score=0.55,  # Low quality
                relevance_score=0.50,
                era_match=False,
            ),
        ]

        validation = validator._validate_reference_images(
            references, sample_subject_data
        )

        assert validation["total_images"] == 2
        assert validation["authentic_count"] >= 1
        assert len(validation["warnings"]) > 0  # Should warn about low quality

    def test_check_common_pitfalls_old_subject(self, validator):
        """Test pitfall checking for old subjects."""
        old_subject = SubjectData(
            name="Historical Figure",
            birth_year=1750,  # Very old
            death_year=1820,
            era="18th Century",
        )

        warnings = validator._check_common_pitfalls(old_subject, "BW")

        # Should warn about limited photographic references
        assert len(warnings) > 0
        assert any("1750" in w or "photograph" in w.lower() for w in warnings)

    def test_check_common_pitfalls_recent_subject(self, validator):
        """Test pitfall checking for recent subjects."""
        recent_subject = SubjectData(
            name="Recent Person",
            birth_year=1980,
            death_year=None,
            era="20th-21st Century",
        )

        warnings = validator._check_common_pitfalls(recent_subject, "BW")

        # Should warn about copyright concerns
        assert len(warnings) > 0

    def test_calculate_confidence(self, validator):
        """Test confidence calculation."""
        # No issues - high confidence
        confidence1 = validator._calculate_confidence(
            issues=[],
            warnings=[],
            fact_check_results={},
        )
        assert confidence1 >= 0.9

        # Some issues - lower confidence
        confidence2 = validator._calculate_confidence(
            issues=["Issue 1", "Issue 2"],
            warnings=["Warning 1"],
            fact_check_results={"check1": False},
        )
        assert confidence2 < confidence1

    def test_quick_check_valid(self, validator, sample_subject_data):
        """Test quick check with valid inputs."""
        result = validator.quick_check(
            subject_data=sample_subject_data,
            style="BW",
        )

        assert result is True

    def test_quick_check_invalid(self, validator):
        """Test quick check with invalid inputs."""
        invalid_data = SubjectData(
            name="",
            birth_year=0,
            death_year=None,
            era="",
        )

        result = validator.quick_check(
            subject_data=invalid_data,
            style="INVALID",
        )

        assert result is False

    def test_parse_verification_response(self, validator):
        """Test parsing verification responses."""
        # Positive response
        assert validator._parse_verification_response("This is correct and verified") is True
        assert validator._parse_verification_response("Yes, this is accurate") is True

        # Negative response
        assert validator._parse_verification_response("This is incorrect") is False
        assert validator._parse_verification_response("No, this is wrong") is False
