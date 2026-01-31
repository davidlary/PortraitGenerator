"""Unit tests for prompt_builder module."""

import pytest
from unittest.mock import Mock

from portrait_generator.prompt_builder import (
    PromptBuilder,
    PromptContext,
)
from portrait_generator.api.models import SubjectData
from portrait_generator.reference_finder import ReferenceImage


@pytest.fixture
def sample_subject_data():
    """Create sample subject data."""
    return SubjectData(
        name="Ada Lovelace",
        birth_year=1815,
        death_year=1852,
        era="19th Century",
    )


@pytest.fixture
def sample_reference_images():
    """Create sample reference images."""
    return [
        ReferenceImage(
            url="https://example.com/image1.jpg",
            source="Library of Congress",
            authenticity_score=0.95,
            quality_score=0.90,
            relevance_score=0.85,
            era_match=True,
            description="Portrait of Ada Lovelace",
        ),
        ReferenceImage(
            url="https://example.com/image2.jpg",
            source="National Archives",
            authenticity_score=0.90,
            quality_score=0.85,
            relevance_score=0.90,
            era_match=True,
            description="Ada Lovelace photograph",
        ),
    ]


@pytest.fixture
def prompt_builder():
    """Create prompt builder instance."""
    return PromptBuilder()


class TestPromptContext:
    """Tests for PromptContext dataclass."""

    def test_create_prompt_context(self, sample_subject_data, sample_reference_images):
        """Test creating prompt context."""
        context = PromptContext(
            subject_data=sample_subject_data,
            style="BW",
            reference_images=sample_reference_images,
            use_native_text=True,
            enable_physics_aware=True,
            enable_fact_checking=True,
        )

        assert context.subject_data == sample_subject_data
        assert context.style == "BW"
        assert len(context.reference_images) == 2
        assert context.use_native_text is True
        assert context.enable_physics_aware is True
        assert context.enable_fact_checking is True


class TestPromptBuilder:
    """Tests for PromptBuilder class."""

    def test_initialization(self):
        """Test builder initialization."""
        builder = PromptBuilder()
        assert builder is not None

    def test_build_prompt(self, prompt_builder, sample_subject_data, sample_reference_images):
        """Test building complete prompt."""
        context = PromptContext(
            subject_data=sample_subject_data,
            style="Color",
            reference_images=sample_reference_images,
            use_native_text=True,
            enable_physics_aware=True,
            enable_fact_checking=True,
        )

        prompt = prompt_builder.build_prompt(context)

        # Check prompt contains key elements
        assert "Ada Lovelace" in prompt
        assert "19th Century" in prompt
        assert "Color" in prompt or "color" in prompt
        assert len(prompt) > 100  # Should be substantial

    def test_build_subject_section(self, prompt_builder, sample_subject_data):
        """Test building subject section."""
        context = PromptContext(
            subject_data=sample_subject_data,
            style="BW",
            reference_images=[],
        )

        section = prompt_builder._build_subject_section(context)

        assert "Ada Lovelace" in section
        assert "1815" in section
        assert "19th Century" in section

    def test_build_reference_section(self, prompt_builder, sample_subject_data, sample_reference_images):
        """Test building reference section."""
        context = PromptContext(
            subject_data=sample_subject_data,
            style="BW",
            reference_images=sample_reference_images,
        )

        section = prompt_builder._build_reference_section(context)

        assert "reference" in section.lower() or "Reference" in section
        assert "Library of Congress" in section
        assert "National Archives" in section

    def test_build_reference_section_empty(self, prompt_builder, sample_subject_data):
        """Test building reference section with no references."""
        context = PromptContext(
            subject_data=sample_subject_data,
            style="BW",
            reference_images=[],
        )

        section = prompt_builder._build_reference_section(context)

        assert section == ""

    def test_build_style_section(self, prompt_builder, sample_subject_data):
        """Test building style sections for all styles."""
        styles = ["BW", "Sepia", "Color", "Painting"]

        for style in styles:
            context = PromptContext(
                subject_data=sample_subject_data,
                style=style,
                reference_images=[],
            )

            section = prompt_builder._build_style_section(context)

            assert len(section) > 0
            assert style in section or style.lower() in section.lower()

    def test_build_composition_section(self, prompt_builder, sample_subject_data):
        """Test building composition section."""
        context = PromptContext(
            subject_data=sample_subject_data,
            style="BW",
            reference_images=[],
        )

        section = prompt_builder._build_composition_section(context)

        assert "portrait" in section.lower()
        assert "3:4" in section or "aspect ratio" in section.lower()

    def test_build_text_rendering_section(self, prompt_builder, sample_subject_data):
        """Test building text rendering section."""
        context = PromptContext(
            subject_data=sample_subject_data,
            style="BW",
            reference_images=[],
            use_native_text=True,
        )

        section = prompt_builder._build_text_rendering_section(context)

        assert "text" in section.lower()
        assert "Ada Lovelace" in section

    def test_build_quality_section(self, prompt_builder, sample_subject_data):
        """Test building quality section."""
        context = PromptContext(
            subject_data=sample_subject_data,
            style="BW",
            reference_images=[],
        )

        section = prompt_builder._build_quality_section(context)

        assert "quality" in section.lower() or "QUALITY" in section
        assert "19th Century" in section

    def test_build_physics_section(self, prompt_builder, sample_subject_data):
        """Test building physics-aware section."""
        context = PromptContext(
            subject_data=sample_subject_data,
            style="BW",
            reference_images=[],
            enable_physics_aware=True,
        )

        section = prompt_builder._build_physics_section(context)

        assert "lighting" in section.lower() or "LIGHTING" in section
        assert "shadows" in section.lower() or "SHADOWS" in section

    def test_build_fact_checking_section(self, prompt_builder, sample_subject_data):
        """Test building fact-checking section."""
        context = PromptContext(
            subject_data=sample_subject_data,
            style="BW",
            reference_images=[],
            enable_fact_checking=True,
        )

        section = prompt_builder._build_fact_checking_section(context)

        assert "Ada Lovelace" in section
        assert "19th Century" in section
        assert "fact" in section.lower() or "FACT" in section

    def test_build_simple_prompt(self, prompt_builder, sample_subject_data):
        """Test building simple prompt without advanced features."""
        prompt = prompt_builder.build_simple_prompt(
            subject_data=sample_subject_data,
            style="BW",
        )

        assert "Ada Lovelace" in prompt
        assert len(prompt) > 50
        # Should not have advanced features
        assert "reference" not in prompt.lower() or len(prompt) < 500

    def test_enhance_prompt_with_reasoning(self, prompt_builder):
        """Test enhancing prompt with reasoning instructions."""
        base_prompt = "Generate a portrait of Ada Lovelace."

        enhanced = prompt_builder.enhance_prompt_with_reasoning(
            base_prompt,
            enable_iteration=True,
            max_iterations=3,
        )

        assert len(enhanced) > len(base_prompt)
        assert "reasoning" in enhanced.lower() or "REASONING" in enhanced
        assert "3" in enhanced  # max iterations

    def test_enhance_prompt_no_iteration(self, prompt_builder):
        """Test enhancing prompt without iteration."""
        base_prompt = "Generate a portrait."

        enhanced = prompt_builder.enhance_prompt_with_reasoning(
            base_prompt,
            enable_iteration=False,
            max_iterations=1,
        )

        assert len(enhanced) > len(base_prompt)
        assert "reasoning" in enhanced.lower() or "REASONING" in enhanced
