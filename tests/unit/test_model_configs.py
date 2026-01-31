"""Unit tests for model_configs module."""

import pytest

from portrait_generator.config.model_configs import (
    ModelCapabilities,
    GenerationConfig,
    EvaluationConfig,
    ModelProfile,
    get_model_profile,
    get_recommended_model,
    list_available_models,
    model_supports_feature,
    get_optimal_config_for_model,
)


class TestModelCapabilities:
    """Tests for ModelCapabilities dataclass."""

    def test_default_capabilities(self):
        """Test default capabilities."""
        caps = ModelCapabilities()

        assert caps.google_search_grounding is False
        assert caps.multi_image_reference is False
        assert caps.max_reference_images == 0
        assert caps.internal_reasoning is False
        assert caps.physics_aware_synthesis is False
        assert caps.native_text_rendering is False
        assert caps.iterative_refinement is False

    def test_advanced_capabilities(self):
        """Test advanced model capabilities."""
        caps = ModelCapabilities(
            google_search_grounding=True,
            multi_image_reference=True,
            max_reference_images=14,
            internal_reasoning=True,
            physics_aware_synthesis=True,
            native_text_rendering=True,
            iterative_refinement=True,
        )

        assert caps.google_search_grounding is True
        assert caps.multi_image_reference is True
        assert caps.max_reference_images == 14
        assert caps.internal_reasoning is True
        assert caps.physics_aware_synthesis is True
        assert caps.native_text_rendering is True
        assert caps.iterative_refinement is True


class TestGenerationConfig:
    """Tests for GenerationConfig dataclass."""

    def test_default_generation_config(self):
        """Test default generation config."""
        config = GenerationConfig()

        assert config.enable_pre_generation_checks is True
        assert config.enable_iterative_refinement is True
        assert config.max_internal_iterations == 3
        assert config.quality_threshold == 0.90
        assert config.confidence_threshold == 0.85

    def test_custom_generation_config(self):
        """Test custom generation config."""
        config = GenerationConfig(
            quality_threshold=0.95,
            max_generation_attempts=3,
            max_reference_images_to_use=10,
        )

        assert config.quality_threshold == 0.95
        assert config.max_generation_attempts == 3
        assert config.max_reference_images_to_use == 10


class TestEvaluationConfig:
    """Tests for EvaluationConfig dataclass."""

    def test_default_evaluation_config(self):
        """Test default evaluation config."""
        config = EvaluationConfig()

        assert config.use_holistic_reasoning is True
        assert config.reasoning_passes == 2
        assert config.autonomous_error_detection is True
        assert config.visual_coherence_checking is True

    def test_custom_evaluation_config(self):
        """Test custom evaluation config."""
        config = EvaluationConfig(
            reasoning_passes=3,
            technical_weight=0.30,
            visual_quality_weight=0.30,
        )

        assert config.reasoning_passes == 3
        assert config.technical_weight == 0.30
        assert config.visual_quality_weight == 0.30


class TestModelProfile:
    """Tests for ModelProfile operations."""

    def test_get_model_profile_gemini_3(self):
        """Test getting gemini-3-pro-image-preview profile."""
        profile = get_model_profile("gemini-3-pro-image-preview")

        assert profile.model_name == "gemini-3-pro-image-preview"
        assert profile.is_recommended is True
        assert profile.capabilities.google_search_grounding is True
        assert profile.capabilities.multi_image_reference is True
        assert profile.capabilities.max_reference_images == 14
        assert profile.generation.quality_threshold == 0.90

    def test_get_model_profile_legacy(self):
        """Test getting legacy model profile."""
        profile = get_model_profile("gemini-exp-1206")

        assert profile.model_name == "gemini-exp-1206"
        assert profile.is_recommended is False
        assert profile.capabilities.google_search_grounding is False
        assert profile.capabilities.multi_image_reference is False
        assert profile.generation.quality_threshold == 0.80

    def test_get_model_profile_invalid(self):
        """Test getting profile for invalid model."""
        with pytest.raises(ValueError, match="Unsupported model"):
            get_model_profile("invalid-model-name")

    def test_get_recommended_model(self):
        """Test getting recommended model."""
        model = get_recommended_model()

        assert model == "gemini-3-pro-image-preview"

    def test_list_available_models(self):
        """Test listing available models."""
        models = list_available_models()

        assert len(models) >= 3
        assert "gemini-3-pro-image-preview" in models
        assert "gemini-exp-1206" in models
        assert "gemini-2.0-flash-exp" in models

    def test_model_supports_feature(self):
        """Test checking if model supports feature."""
        # Advanced model supports grounding
        assert model_supports_feature("gemini-3-pro-image-preview", "google_search_grounding") is True

        # Legacy model doesn't support grounding
        assert model_supports_feature("gemini-exp-1206", "google_search_grounding") is False

        # Unknown feature
        assert model_supports_feature("gemini-3-pro-image-preview", "unknown_feature") is False

    def test_get_optimal_config_no_overrides(self):
        """Test getting optimal config without overrides."""
        profile = get_optimal_config_for_model("gemini-3-pro-image-preview")

        assert profile.generation.quality_threshold == 0.90
        assert profile.evaluation.reasoning_passes == 2

    def test_get_optimal_config_with_generation_overrides(self):
        """Test getting optimal config with generation overrides."""
        profile = get_optimal_config_for_model(
            "gemini-3-pro-image-preview",
            override_generation={"quality_threshold": 0.95, "max_generation_attempts": 3},
        )

        assert profile.generation.quality_threshold == 0.95
        assert profile.generation.max_generation_attempts == 3

    def test_get_optimal_config_with_evaluation_overrides(self):
        """Test getting optimal config with evaluation overrides."""
        profile = get_optimal_config_for_model(
            "gemini-3-pro-image-preview",
            override_evaluation={"reasoning_passes": 3},
        )

        assert profile.evaluation.reasoning_passes == 3

    def test_profile_has_all_required_fields(self):
        """Test that all profiles have required fields."""
        for model_name in list_available_models():
            profile = get_model_profile(model_name)

            # Check required fields
            assert profile.model_name
            assert profile.display_name
            assert profile.capabilities is not None
            assert profile.generation is not None
            assert profile.evaluation is not None
            assert isinstance(profile.is_recommended, bool)
