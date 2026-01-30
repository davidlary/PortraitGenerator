"""Unit tests for validators module."""

import pytest
from portrait_generator.utils.validators import (
    validate_subject_name,
    validate_style,
    validate_styles,
    sanitize_filename,
    VALID_STYLES,
)


class TestValidateSubjectName:
    """Tests for validate_subject_name function."""

    def test_valid_name(self) -> None:
        """Test validation passes for valid name."""
        validate_subject_name("Albert Einstein")
        validate_subject_name("Marie Curie")
        validate_subject_name("Ada Lovelace")

    def test_empty_name(self) -> None:
        """Test validation fails for empty name."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_subject_name("")

    def test_short_name(self) -> None:
        """Test validation fails for name too short."""
        with pytest.raises(ValueError, match="too short"):
            validate_subject_name("A")

    def test_long_name(self) -> None:
        """Test validation fails for name too long."""
        with pytest.raises(ValueError, match="too long"):
            validate_subject_name("A" * 101)

    def test_invalid_characters(self) -> None:
        """Test validation fails for invalid characters."""
        invalid_names = [
            "Test<Name",
            "Test>Name",
            "Test:Name",
            'Test"Name',
            "Test/Name",
            "Test\\Name",
            "Test|Name",
            "Test?Name",
            "Test*Name",
        ]
        for name in invalid_names:
            with pytest.raises(ValueError, match="invalid characters"):
                validate_subject_name(name)

    def test_non_string(self) -> None:
        """Test validation fails for non-string input."""
        with pytest.raises(ValueError, match="must be a string"):
            validate_subject_name(123)  # type: ignore


class TestValidateStyle:
    """Tests for validate_style function."""

    def test_valid_styles(self) -> None:
        """Test validation passes for all valid styles."""
        for style in VALID_STYLES:
            validate_style(style)

    def test_invalid_style(self) -> None:
        """Test validation fails for invalid style."""
        with pytest.raises(ValueError, match="Invalid style"):
            validate_style("Invalid")

    def test_empty_style(self) -> None:
        """Test validation fails for empty style."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_style("")

    def test_case_sensitive(self) -> None:
        """Test style validation is case-sensitive."""
        with pytest.raises(ValueError, match="Invalid style"):
            validate_style("bw")  # lowercase not valid


class TestValidateStyles:
    """Tests for validate_styles function."""

    def test_valid_styles_list(self) -> None:
        """Test validation passes for valid styles list."""
        validate_styles(["BW", "Sepia"])
        validate_styles(list(VALID_STYLES))

    def test_empty_list(self) -> None:
        """Test validation fails for empty list."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_styles([])

    def test_invalid_style_in_list(self) -> None:
        """Test validation fails if any style is invalid."""
        with pytest.raises(ValueError, match="Invalid style"):
            validate_styles(["BW", "Invalid", "Color"])


class TestSanitizeFilename:
    """Tests for sanitize_filename function."""

    def test_simple_name(self) -> None:
        """Test sanitization of simple names."""
        assert sanitize_filename("Albert Einstein") == "AlbertEinstein"
        assert sanitize_filename("Marie Curie") == "MarieCurie"

    def test_special_characters(self) -> None:
        """Test removal of special characters."""
        # Unicode characters that don't have ASCII equivalents are removed
        assert sanitize_filename("Marie Curie-Skłodowska") == "MarieCurie-Skodowska"
        assert sanitize_filename("Name (with) brackets") == "Namewithbrackets"

    def test_capitalization(self) -> None:
        """Test first letter capitalization."""
        assert sanitize_filename("albert einstein")[0].isupper()

    def test_empty_string(self) -> None:
        """Test sanitization of empty string."""
        assert sanitize_filename("") == ""

    def test_preserves_hyphens(self) -> None:
        """Test that hyphens are preserved."""
        assert "-" in sanitize_filename("Marie-Curie")

    def test_removes_spaces(self) -> None:
        """Test that spaces are removed."""
        result = sanitize_filename("Albert Einstein")
        assert " " not in result
