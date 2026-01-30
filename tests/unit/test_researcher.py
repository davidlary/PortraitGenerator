"""Unit tests for BiographicalResearcher."""

import sys
import pytest
from unittest.mock import Mock, patch, MagicMock

from portrait_generator.core.researcher import BiographicalResearcher
from portrait_generator.api.models import SubjectData


@pytest.fixture
def mock_genai():
    """Mock google.genai module."""
    # Create mock module
    mock_genai_module = MagicMock()

    # Setup mock client
    mock_client = Mock()
    mock_genai_module.Client.return_value = mock_client

    # Setup mock generate_content method
    mock_genai_module.Client.return_value.models = Mock()

    # Ensure parent google module exists
    if 'google' not in sys.modules:
        sys.modules['google'] = MagicMock()

    # Inject into sys.modules
    sys.modules['google.genai'] = mock_genai_module

    yield mock_genai_module

    # Cleanup
    if 'google.genai' in sys.modules:
        del sys.modules['google.genai']


@pytest.fixture
def mock_gemini_client():
    """Create mock Gemini client."""
    client = Mock()
    client.api_key = "test_key_1234567890"
    return client


@pytest.fixture
def researcher(mock_gemini_client):
    """Create researcher instance."""
    return BiographicalResearcher(mock_gemini_client)


@pytest.fixture
def sample_gemini_response():
    """Sample Gemini research response."""
    return """
FULL NAME: Albert Einstein
BIRTH YEAR: 1879
DEATH YEAR: 1955
ERA: Early 20th Century
APPEARANCE NOTES:
- Distinctive wild gray hair
- Thick mustache
- Casual attire, often sweaters
- Penetrating brown eyes
- Characteristic thoughtful expression
HISTORICAL CONTEXT: Lived during the revolutionary period of modern physics, witnessing two world wars and the atomic age.
REFERENCE SOURCES:
- Historical records
- Contemporary photographs
- Biographical accounts
"""


@pytest.fixture
def sample_living_person_response():
    """Sample response for living person."""
    return """
FULL NAME: Geoffrey Hinton
BIRTH YEAR: 1947
DEATH YEAR: Present
ERA: Contemporary / Digital Age
APPEARANCE NOTES:
- White hair and beard
- Glasses
- Academic style clothing
- Friendly demeanor
HISTORICAL CONTEXT: Pioneer in artificial intelligence and deep learning in the late 20th and early 21st centuries.
REFERENCE SOURCES:
- Current biographical data
- Academic records
"""


class TestBiographicalResearcherInit:
    """Tests for BiographicalResearcher initialization."""

    def test_init(self, mock_gemini_client):
        """Test initialization."""
        researcher = BiographicalResearcher(mock_gemini_client)

        assert researcher.gemini_client == mock_gemini_client


class TestResearchSubject:
    """Tests for research_subject method."""

    # Removed patch decorator - using mock_genai fixture instead
    def test_research_subject_success(
        self, mock_genai, researcher, sample_gemini_response
    ):
        """Test successful subject research."""
        # Setup mock
        mock_response = Mock()
        mock_response.text = sample_gemini_response

        mock_client = Mock()
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client

        # Research
        result = researcher.research_subject("Albert Einstein")

        # Verify
        assert isinstance(result, SubjectData)
        assert result.name == "Albert Einstein"
        assert result.birth_year == 1879
        assert result.death_year == 1955
        assert result.era == "Early 20th Century"
        assert len(result.appearance_notes) > 0
        assert result.historical_context != ""

    # Removed patch decorator - using mock_genai fixture instead
    def test_research_subject_living_person(
        self, mock_genai, researcher, sample_living_person_response
    ):
        """Test research for living person."""
        # Setup mock
        mock_response = Mock()
        mock_response.text = sample_living_person_response

        mock_client = Mock()
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client

        # Research
        result = researcher.research_subject("Geoffrey Hinton")

        # Verify
        assert isinstance(result, SubjectData)
        assert result.name == "Geoffrey Hinton"
        assert result.birth_year == 1947
        assert result.death_year is None
        assert result.formatted_years == "1947-Present"

    def test_research_subject_empty_name(self, researcher):
        """Test error handling for empty name."""
        with pytest.raises(ValueError, match="cannot be empty"):
            researcher.research_subject("")

    def test_research_subject_whitespace_name(self, researcher):
        """Test error handling for whitespace-only name."""
        with pytest.raises(ValueError, match="cannot be empty"):
            researcher.research_subject("   ")

    # Removed patch decorator - using mock_genai fixture instead
    def test_research_subject_gemini_failure(self, mock_genai, researcher):
        """Test error handling when Gemini fails."""
        # Setup mock to fail
        mock_genai.Client.side_effect = Exception("API Error")

        # Test
        with pytest.raises(RuntimeError, match="Failed to research"):
            researcher.research_subject("Test Person")

    # Removed patch decorator - using mock_genai fixture instead
    def test_research_subject_empty_response(self, mock_genai, researcher):
        """Test error handling for empty Gemini response."""
        # Setup mock
        mock_response = Mock()
        mock_response.text = None

        mock_client = Mock()
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client

        # Test
        with pytest.raises(RuntimeError, match="Failed to research"):
            researcher.research_subject("Test Person")

    # Removed patch decorator - using mock_genai fixture instead
    def test_research_subject_invalid_response(self, mock_genai, researcher):
        """Test error handling for unparseable response."""
        # Setup mock with invalid response
        mock_response = Mock()
        mock_response.text = "Invalid response without required fields"

        mock_client = Mock()
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client

        # Test
        with pytest.raises(RuntimeError, match="Failed to research"):
            researcher.research_subject("Test Person")


class TestFormatYears:
    """Tests for format_years method."""

    def test_format_years_deceased(self, researcher):
        """Test formatting for deceased person."""
        result = researcher.format_years(1879, 1955)

        assert result == "1879-1955"

    def test_format_years_living(self, researcher):
        """Test formatting for living person."""
        result = researcher.format_years(1947, None)

        assert result == "1947-Present"

    def test_format_years_recent_death(self, researcher):
        """Test formatting for recently deceased."""
        result = researcher.format_years(1940, 2023)

        assert result == "1940-2023"

    def test_format_years_negative_birth(self, researcher):
        """Test error handling for negative birth year (CE)."""
        with pytest.raises(ValueError, match="cannot be negative"):
            researcher.format_years(-500, -450)

    def test_format_years_death_before_birth(self, researcher):
        """Test error handling for death before birth."""
        with pytest.raises(ValueError, match="cannot be before"):
            researcher.format_years(1900, 1850)

    def test_format_years_same_year(self, researcher):
        """Test formatting when birth and death in same year."""
        result = researcher.format_years(1900, 1900)

        assert result == "1900-1900"

    def test_format_years_ancient_figure(self, researcher):
        """Test formatting for very old dates."""
        # Note: For BC dates, we'd need special handling
        # This tests very early CE dates
        result = researcher.format_years(100, 150)

        assert result == "100-150"


class TestValidateData:
    """Tests for validate_data method."""

    def test_validate_data_valid(self, researcher):
        """Test validation of valid data."""
        data = SubjectData(
            name="Albert Einstein",
            birth_year=1879,
            death_year=1955,
            era="20th Century",
            appearance_notes=["Wild hair", "Mustache"],
            historical_context="Physicist",
            reference_sources=["Historical records"],
        )

        result = researcher.validate_data(data)

        assert result is True

    def test_validate_data_living_person(self, researcher):
        """Test validation of living person data."""
        data = SubjectData(
            name="Test Person",
            birth_year=1970,
            death_year=None,
            era="Contemporary",
            appearance_notes=["Test"],
            historical_context="Test",
            reference_sources=["Test"],
        )

        result = researcher.validate_data(data)

        assert result is True

    def test_validate_data_none(self, researcher):
        """Test validation of None data."""
        result = researcher.validate_data(None)

        assert result is False

    def test_validate_data_empty_name(self, researcher):
        """Test validation fails for empty name."""
        data = SubjectData(
            name="",
            birth_year=1900,
            death_year=1950,
            era="Test",
            appearance_notes=["Test"],
            historical_context="Test",
            reference_sources=["Test"],
        )

        result = researcher.validate_data(data)

        assert result is False

    def test_validate_data_whitespace_name(self, researcher):
        """Test validation fails for whitespace-only name."""
        data = SubjectData(
            name="   ",
            birth_year=1900,
            death_year=1950,
            era="Test",
            appearance_notes=["Test"],
            historical_context="Test",
            reference_sources=["Test"],
        )

        result = researcher.validate_data(data)

        assert result is False

    def test_validate_data_invalid_birth_year_negative(self, researcher):
        """Test validation fails for negative birth year."""
        data = SubjectData(
            name="Test",
            birth_year=-100,
            death_year=50,
            era="Test",
            appearance_notes=["Test"],
            historical_context="Test",
            reference_sources=["Test"],
        )

        result = researcher.validate_data(data)

        assert result is False

    def test_validate_data_invalid_birth_year_future(self, researcher):
        """Test validation fails for future birth year."""
        data = SubjectData(
            name="Test",
            birth_year=2150,
            death_year=None,
            era="Test",
            appearance_notes=["Test"],
            historical_context="Test",
            reference_sources=["Test"],
        )

        result = researcher.validate_data(data)

        assert result is False

    def test_validate_data_death_before_birth(self, researcher):
        """Test validation fails for death before birth."""
        data = SubjectData(
            name="Test",
            birth_year=1900,
            death_year=1850,
            era="Test",
            appearance_notes=["Test"],
            historical_context="Test",
            reference_sources=["Test"],
        )

        result = researcher.validate_data(data)

        assert result is False

    def test_validate_data_invalid_death_year_future(self, researcher):
        """Test validation fails for future death year."""
        data = SubjectData(
            name="Test",
            birth_year=1900,
            death_year=2150,
            era="Test",
            appearance_notes=["Test"],
            historical_context="Test",
            reference_sources=["Test"],
        )

        result = researcher.validate_data(data)

        assert result is False

    def test_validate_data_empty_era(self, researcher):
        """Test validation fails for empty era."""
        data = SubjectData(
            name="Test",
            birth_year=1900,
            death_year=1950,
            era="",
            appearance_notes=["Test"],
            historical_context="Test",
            reference_sources=["Test"],
        )

        result = researcher.validate_data(data)

        assert result is False

    def test_validate_data_whitespace_era(self, researcher):
        """Test validation fails for whitespace-only era."""
        data = SubjectData(
            name="Test",
            birth_year=1900,
            death_year=1950,
            era="   ",
            appearance_notes=["Test"],
            historical_context="Test",
            reference_sources=["Test"],
        )

        result = researcher.validate_data(data)

        assert result is False

    def test_validate_data_minimal_valid(self, researcher):
        """Test validation passes with minimal but valid data."""
        data = SubjectData(
            name="Test",
            birth_year=1900,
            death_year=None,
            era="Modern",
        )

        result = researcher.validate_data(data)

        assert result is True


class TestCreateResearchPrompt:
    """Tests for _create_research_prompt method."""

    def test_create_research_prompt(self, researcher):
        """Test research prompt creation."""
        prompt = researcher._create_research_prompt("Albert Einstein")

        assert "Albert Einstein" in prompt
        assert "BIRTH YEAR" in prompt
        assert "DEATH YEAR" in prompt
        assert "ERA" in prompt
        assert "APPEARANCE NOTES" in prompt
        assert "HISTORICAL CONTEXT" in prompt

    def test_create_research_prompt_different_names(self, researcher):
        """Test prompts for different names."""
        prompt1 = researcher._create_research_prompt("Marie Curie")
        prompt2 = researcher._create_research_prompt("Alan Turing")

        assert "Marie Curie" in prompt1
        assert "Alan Turing" in prompt2
        assert "Marie Curie" not in prompt2


class TestQueryGemini:
    """Tests for _query_gemini method."""

    # Removed patch decorator - using mock_genai fixture instead
    def test_query_gemini_success(self, mock_genai, researcher):
        """Test successful Gemini query."""
        # Setup mock
        mock_response = Mock()
        mock_response.text = "Test response"

        mock_client = Mock()
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client

        # Query
        result = researcher._query_gemini("Test prompt")

        # Verify
        assert result == "Test response"
        mock_client.models.generate_content.assert_called_once()

    # Removed patch decorator - using mock_genai fixture instead
    def test_query_gemini_empty_response(self, mock_genai, researcher):
        """Test error handling for empty response."""
        # Setup mock
        mock_response = Mock()
        mock_response.text = None

        mock_client = Mock()
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client

        # Test
        with pytest.raises(RuntimeError, match="Empty response"):
            researcher._query_gemini("Test prompt")

    # Removed patch decorator - using mock_genai fixture instead
    def test_query_gemini_api_error(self, mock_genai, researcher):
        """Test error handling for API errors."""
        # Setup mock to fail
        mock_genai.Client.side_effect = Exception("API Error")

        # Test
        with pytest.raises(RuntimeError, match="Gemini query failed"):
            researcher._query_gemini("Test prompt")


class TestParseResearchResponse:
    """Tests for _parse_research_response method."""

    def test_parse_research_response_complete(
        self, researcher, sample_gemini_response
    ):
        """Test parsing complete response."""
        result = researcher._parse_research_response(
            "Albert Einstein", sample_gemini_response
        )

        assert result.name == "Albert Einstein"
        assert result.birth_year == 1879
        assert result.death_year == 1955
        assert result.era == "Early 20th Century"
        assert len(result.appearance_notes) > 0
        assert "wild gray hair" in result.appearance_notes[0].lower()

    def test_parse_research_response_living(
        self, researcher, sample_living_person_response
    ):
        """Test parsing response for living person."""
        result = researcher._parse_research_response(
            "Geoffrey Hinton", sample_living_person_response
        )

        assert result.name == "Geoffrey Hinton"
        assert result.death_year is None
        assert result.formatted_years == "1947-Present"

    def test_parse_research_response_missing_birth_year(self, researcher):
        """Test error handling for missing birth year."""
        response = """
        FULL NAME: Test
        ERA: Modern
        """

        with pytest.raises(ValueError, match="Could not extract birth year"):
            researcher._parse_research_response("Test", response)

    def test_parse_research_response_minimal(self, researcher):
        """Test parsing minimal but valid response."""
        response = """
        BIRTH YEAR: 1900
        DEATH YEAR: 1950
        ERA: 20th Century
        """

        result = researcher._parse_research_response("Test Person", response)

        assert result.birth_year == 1900
        assert result.death_year == 1950

    def test_parse_research_response_alternative_formats(self, researcher):
        """Test parsing with different response formats."""
        response = """
        Birth Year: 1900
        death year: 1950
        ERA: Modern
        """

        result = researcher._parse_research_response("Test", response)

        assert result.birth_year == 1900
        assert result.death_year == 1950


class TestGetPromptContext:
    """Tests for get_prompt_context method."""

    def test_get_prompt_context(self, researcher):
        """Test getting prompt context from subject data."""
        data = SubjectData(
            name="Albert Einstein",
            birth_year=1879,
            death_year=1955,
            era="20th Century",
            appearance_notes=["Wild hair", "Mustache"],
            historical_context="Physicist",
            reference_sources=["Records"],
        )

        context = researcher.get_prompt_context(data)

        assert context["name"] == "Albert Einstein"
        assert context["birth_year"] == 1879
        assert context["death_year"] == 1955
        assert context["years"] == "1879-1955"
        assert context["era"] == "20th Century"
        assert "Wild hair" in context["appearance"]
        assert "Mustache" in context["appearance"]

    def test_get_prompt_context_living(self, researcher):
        """Test prompt context for living person."""
        data = SubjectData(
            name="Test Person",
            birth_year=1970,
            death_year=None,
            era="Contemporary",
            appearance_notes=["Test"],
            historical_context="Test",
        )

        context = researcher.get_prompt_context(data)

        assert context["death_year"] == "Present"
        assert context["years"] == "1970-Present"

    def test_get_prompt_context_no_appearance_notes(self, researcher):
        """Test prompt context with no appearance notes."""
        data = SubjectData(
            name="Test",
            birth_year=1900,
            death_year=1950,
            era="Modern",
            appearance_notes=[],
            historical_context="Test",
        )

        context = researcher.get_prompt_context(data)

        assert context["appearance"] == ""


class TestIntegration:
    """Integration tests for BiographicalResearcher."""

    # Removed patch decorator - using mock_genai fixture instead
    def test_full_research_workflow(
        self, mock_genai, researcher, sample_gemini_response
    ):
        """Test complete research workflow."""
        # Setup mock
        mock_response = Mock()
        mock_response.text = sample_gemini_response

        mock_client = Mock()
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client

        # Research
        subject_data = researcher.research_subject("Albert Einstein")

        # Validate
        assert researcher.validate_data(subject_data)

        # Get context
        context = researcher.get_prompt_context(subject_data)

        assert context["name"] == "Albert Einstein"
        assert context["years"] == "1879-1955"

    # Removed patch decorator - using mock_genai fixture instead
    def test_multiple_subjects(self, mock_genai, researcher):
        """Test researching multiple subjects."""
        # Setup mock responses
        responses = {
            "Albert Einstein": """
                BIRTH YEAR: 1879
                DEATH YEAR: 1955
                ERA: 20th Century
                """,
            "Marie Curie": """
                BIRTH YEAR: 1867
                DEATH YEAR: 1934
                ERA: 20th Century
                """,
        }

        def generate_content_side_effect(*args, **kwargs):
            prompt = kwargs.get("contents", "")
            for name, response in responses.items():
                if name in prompt:
                    mock_resp = Mock()
                    mock_resp.text = response
                    return mock_resp
            mock_resp = Mock()
            mock_resp.text = list(responses.values())[0]
            return mock_resp

        mock_client = Mock()
        mock_client.models.generate_content.side_effect = generate_content_side_effect
        mock_genai.Client.return_value = mock_client

        # Research multiple subjects
        einstein = researcher.research_subject("Albert Einstein")
        curie = researcher.research_subject("Marie Curie")

        assert einstein.birth_year == 1879
        assert curie.birth_year == 1867
