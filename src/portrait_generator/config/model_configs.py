"""Model-specific configuration profiles.

This module defines capabilities and optimal parameters for different Gemini models.
All configurations are data-driven with no hard-coded thresholds in the main code.

Supported Models:
- gemini-3.1-flash-image-preview: Fast, high-efficiency image model (Nano Banana 2) [RECOMMENDED]
- gemini-3-pro-image-preview: Highest quality image model (Nano Banana Pro)
- gemini-2.5-flash-image: Pure image model — no search-as-tool (Nano Banana) [quota fallback]
- gemini-exp-1206: Previous experimental model (legacy)

Model Selection Guide:
- Use gemini-3.1-flash-image-preview (default) for best speed + accuracy balance
- Use gemini-3-pro-image-preview for maximum quality on complex subjects
- Use gemini-2.5-flash-image as quota fallback (pure image model; no tool/search support)
- Use gemini-exp-1206 for legacy compatibility only

Quota Cascade (try in order when rate-limited):
1. gemini-3.1-flash-image-preview  (Nano Banana 2)   — primary   [thinking + search]
2. gemini-3-pro-image-preview      (Nano Banana Pro) — secondary [thinking + search]
3. gemini-2.5-flash-image          (Nano Banana)     — tertiary  [image-only; no search-as-tool]
"""

import dataclasses
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


@dataclass
class ModelCapabilities:
    """Capabilities available in a specific model."""

    # Advanced AI features
    google_search_grounding: bool = False
    """Support for real-time Google Search fact-checking"""

    image_search_grounding: bool = False
    """Support for Image Search grounding (text + image search results)"""

    multi_image_reference: bool = False
    """Support for multiple reference images in generation"""

    max_reference_images: int = 0
    """Maximum number of reference images supported"""

    internal_reasoning: bool = False
    """Model has internal reasoning/thinking capabilities"""

    thinking_mode: bool = False
    """Explicit thinking mode with configurable depth (minimal/low/medium/high)"""

    physics_aware_synthesis: bool = False
    """Built-in physics-aware visual synthesis"""

    native_text_rendering: bool = False
    """LLM-based text rendering (vs pixel drawing)"""

    international_text_rendering: bool = False
    """Enhanced international/multilingual text rendering"""

    iterative_refinement: bool = False
    """Support for internal iteration before final render"""

    # Output capabilities
    supported_resolutions: List[str] = field(
        default_factory=lambda: ["1024x1024"]
    )
    """Supported output resolutions"""

    max_resolution: str = "1024x1024"
    """Maximum resolution available"""

    supported_aspect_ratios: List[str] = field(
        default_factory=lambda: ["1:1", "3:4", "4:3", "9:16", "16:9"]
    )
    """Supported aspect ratios"""

    # Performance characteristics
    typical_generation_time: float = 30.0
    """Typical generation time in seconds"""

    supports_batch: bool = False
    """Support for batch generation via Batch API"""

    # Accuracy characteristics
    accuracy_tier: str = "standard"
    """Accuracy tier: 'standard', 'high', 'maximum'"""


@dataclass
class GenerationConfig:
    """Generation-time configuration parameters."""

    # Pre-generation checks
    enable_pre_generation_checks: bool = True
    """Run validation before generation"""

    enable_iterative_refinement: bool = True
    """Allow model to iterate internally"""

    max_internal_iterations: int = 3
    """Maximum internal iterations for refinement"""

    # Quality thresholds
    quality_threshold: float = 0.90
    """Minimum quality score to accept generation"""

    confidence_threshold: float = 0.85
    """Minimum confidence to proceed without retry"""

    # Feature toggles
    enable_search_grounding: bool = True
    """Enable Google Search fact-checking"""

    enable_reference_images: bool = True
    """Use reference images for guidance"""

    max_reference_images_to_use: int = 5
    """Number of reference images to actually use"""

    # Retry logic
    max_generation_attempts: int = 2
    """Maximum generation attempts before failure"""

    enable_smart_retry: bool = True
    """Use reasoning to refine prompt on retry"""


@dataclass
class EvaluationConfig:
    """Evaluation configuration parameters."""

    use_holistic_reasoning: bool = True
    """Use model's reasoning for holistic evaluation"""

    reasoning_passes: int = 2
    """Number of reasoning passes for consistency"""

    autonomous_error_detection: bool = True
    """Proactively detect errors before they occur"""

    visual_coherence_checking: bool = True
    """Check visual coherence using physics-aware analysis"""

    enable_fact_checking: bool = True
    """Fact-check visual elements against search results"""

    # Quality metrics
    technical_weight: float = 0.25
    """Weight for technical quality metrics"""

    visual_quality_weight: float = 0.25
    """Weight for visual quality assessment"""

    style_adherence_weight: float = 0.25
    """Weight for style adherence"""

    historical_accuracy_weight: float = 0.25
    """Weight for historical accuracy"""


@dataclass
class ModelProfile:
    """Complete profile for a specific model."""

    model_name: str
    """Official model identifier"""

    display_name: str
    """Human-readable name"""

    capabilities: ModelCapabilities
    """Model capabilities"""

    generation: GenerationConfig
    """Default generation configuration"""

    evaluation: EvaluationConfig
    """Default evaluation configuration"""

    description: str = ""
    """Model description"""

    release_date: Optional[str] = None
    """Model release date"""

    is_recommended: bool = False
    """Whether this is the recommended model"""


# Model profile definitions
MODEL_PROFILES: Dict[str, ModelProfile] = {
    "gemini-3.1-flash-image-preview": ModelProfile(
        model_name="gemini-3.1-flash-image-preview",
        display_name="Gemini 3.1 Flash Image (Nano Banana 2)",
        description=(
            "Google's high-efficiency image generation model with best speed/accuracy balance. "
            "Nano Banana 2 delivers 4K studio-quality portraits at ~50% faster generation speed "
            "vs Nano Banana Pro. Features Image Search grounding, thinking mode for enhanced "
            "accuracy, improved international text rendering, and new aspect ratios. "
            "Updated February 2026 with improved image quality and aspect ratio adherence. "
            "Optimized for high-volume, production workloads."
        ),
        release_date="2026-02",
        is_recommended=True,
        capabilities=ModelCapabilities(
            google_search_grounding=True,
            image_search_grounding=True,
            multi_image_reference=True,
            max_reference_images=14,
            internal_reasoning=True,
            thinking_mode=True,
            physics_aware_synthesis=True,
            native_text_rendering=True,
            international_text_rendering=True,
            iterative_refinement=True,
            supported_resolutions=[
                "512x512",    # 0.5K
                "1024x1024",  # 1K (default)
                "2048x2048",  # 2K
                "4096x4096",  # 4K
            ],
            max_resolution="4096x4096",
            supported_aspect_ratios=[
                "1:1", "3:4", "4:3", "9:16", "16:9",
                "2:3", "3:2", "4:5", "5:4", "21:9",
                "1:4", "4:1", "1:8", "8:1",  # New extended ratios
            ],
            typical_generation_time=22.0,  # ~50% faster than Pro
            supports_batch=True,
            accuracy_tier="high",
        ),
        generation=GenerationConfig(
            enable_pre_generation_checks=True,
            enable_iterative_refinement=True,
            max_internal_iterations=3,
            quality_threshold=0.90,
            confidence_threshold=0.85,
            enable_search_grounding=True,
            enable_reference_images=True,
            max_reference_images_to_use=5,
            max_generation_attempts=2,
            enable_smart_retry=True,
        ),
        evaluation=EvaluationConfig(
            use_holistic_reasoning=True,
            reasoning_passes=2,
            autonomous_error_detection=True,
            visual_coherence_checking=True,
            enable_fact_checking=True,
        ),
    ),

    "gemini-3-pro-image-preview": ModelProfile(
        model_name="gemini-3-pro-image-preview",
        display_name="Gemini 3 Pro Image (Nano Banana Pro)",
        description=(
            "Google's highest-quality image generation model with maximum reasoning depth. "
            "Nano Banana Pro delivers best results for complex compositions and subjects "
            "requiring deep historical accuracy. Use for premium portrait generation where "
            "quality trumps speed. Features advanced reasoning, Google Search grounding, "
            "multi-image reference support, and physics-aware synthesis."
        ),
        release_date="2026-01",
        is_recommended=False,
        capabilities=ModelCapabilities(
            google_search_grounding=True,
            image_search_grounding=False,
            multi_image_reference=True,
            max_reference_images=14,
            internal_reasoning=True,
            thinking_mode=True,
            physics_aware_synthesis=True,
            native_text_rendering=True,
            international_text_rendering=True,
            iterative_refinement=True,
            supported_resolutions=["1024x1024", "2048x2048", "4096x4096"],
            max_resolution="4096x4096",
            supported_aspect_ratios=[
                "1:1", "3:4", "4:3", "9:16", "16:9",
                "2:3", "3:2", "4:5", "5:4", "21:9",
            ],
            typical_generation_time=45.0,
            supports_batch=False,
            accuracy_tier="maximum",
        ),
        generation=GenerationConfig(
            enable_pre_generation_checks=True,
            enable_iterative_refinement=True,
            max_internal_iterations=3,
            quality_threshold=0.90,
            confidence_threshold=0.85,
            enable_search_grounding=True,
            enable_reference_images=True,
            max_reference_images_to_use=5,
            max_generation_attempts=2,
            enable_smart_retry=True,
        ),
        evaluation=EvaluationConfig(
            use_holistic_reasoning=True,
            reasoning_passes=2,
            autonomous_error_detection=True,
            visual_coherence_checking=True,
            enable_fact_checking=True,
        ),
    ),

    "gemini-2.5-flash-image": ModelProfile(
        model_name="gemini-2.5-flash-image",
        display_name="Gemini 2.5 Flash Image (Nano Banana)",
        description=(
            "Pure image-generation model. Does NOT support search as a tool "
            "(no google_search or grounding API). No thinking mode. "
            "Use as tertiary quota fallback only when Nano Banana 2 and Pro are "
            "exhausted. Has its own separate daily quota bucket. "
            "Note: any '2.5-flash-*' model ID variant is treated identically."
        ),
        release_date="2025-06",
        is_recommended=False,
        capabilities=ModelCapabilities(
            google_search_grounding=False,  # pure image model; search-as-tool not supported
            image_search_grounding=False,
            multi_image_reference=True,
            max_reference_images=5,
            internal_reasoning=True,
            thinking_mode=False,            # no thinking mode on pure image models
            physics_aware_synthesis=False,
            native_text_rendering=True,
            international_text_rendering=False,
            iterative_refinement=False,
            supported_resolutions=["1024x1024", "2048x2048"],
            max_resolution="2048x2048",
            supported_aspect_ratios=["1:1", "3:4", "4:3", "9:16", "16:9"],
            typical_generation_time=35.0,
            supports_batch=False,
            accuracy_tier="high",
        ),
        generation=GenerationConfig(
            enable_pre_generation_checks=True,
            enable_iterative_refinement=False,
            max_internal_iterations=1,
            quality_threshold=0.82,
            confidence_threshold=0.78,
            enable_search_grounding=False,  # must be False: model does not accept search-as-tool
            enable_reference_images=True,
            max_reference_images_to_use=3,
            max_generation_attempts=2,
            enable_smart_retry=True,
        ),
        evaluation=EvaluationConfig(
            use_holistic_reasoning=True,
            reasoning_passes=1,
            autonomous_error_detection=True,
            visual_coherence_checking=True,
            enable_fact_checking=True,
        ),
    ),

    "gemini-exp-1206": ModelProfile(
        model_name="gemini-exp-1206",
        display_name="Gemini Experimental (December 2025)",
        description=(
            "Legacy experimental Gemini model from December 2025. Good quality image "
            "generation but lacks advanced reasoning, thinking mode, and Google Search "
            "grounding capabilities. Use only for compatibility with existing workflows."
        ),
        release_date="2025-12",
        is_recommended=False,
        capabilities=ModelCapabilities(
            google_search_grounding=False,
            image_search_grounding=False,
            multi_image_reference=False,
            max_reference_images=0,
            internal_reasoning=False,
            thinking_mode=False,
            physics_aware_synthesis=False,
            native_text_rendering=False,
            international_text_rendering=False,
            iterative_refinement=False,
            supported_resolutions=["1024x1024"],
            max_resolution="1024x1024",
            supported_aspect_ratios=["1:1", "3:4", "4:3", "9:16", "16:9"],
            typical_generation_time=30.0,
            supports_batch=False,
            accuracy_tier="standard",
        ),
        generation=GenerationConfig(
            enable_pre_generation_checks=False,
            enable_iterative_refinement=False,
            max_internal_iterations=1,
            quality_threshold=0.80,
            confidence_threshold=0.75,
            enable_search_grounding=False,
            enable_reference_images=False,
            max_reference_images_to_use=0,
            max_generation_attempts=2,
            enable_smart_retry=False,
        ),
        evaluation=EvaluationConfig(
            use_holistic_reasoning=False,
            reasoning_passes=1,
            autonomous_error_detection=False,
            visual_coherence_checking=False,
            enable_fact_checking=False,
        ),
    ),
}


def get_model_profile(model_name: str) -> ModelProfile:
    """Get configuration profile for a model.

    Args:
        model_name: Name of the model

    Returns:
        ModelProfile for the specified model

    Raises:
        ValueError: If model is not supported
    """
    if model_name not in MODEL_PROFILES:
        available = ", ".join(MODEL_PROFILES.keys())
        raise ValueError(
            f"Unsupported model: {model_name}. "
            f"Available models: {available}"
        )

    return MODEL_PROFILES[model_name]


def get_recommended_model() -> str:
    """Get the recommended model name.

    Returns:
        Name of the recommended model
    """
    for model_name, profile in MODEL_PROFILES.items():
        if profile.is_recommended:
            return model_name

    # Fallback to first model if none marked as recommended
    return list(MODEL_PROFILES.keys())[0]


def list_available_models() -> List[str]:
    """List all available model names.

    Returns:
        List of model names
    """
    return list(MODEL_PROFILES.keys())


def model_supports_feature(model_name: str, feature: str) -> bool:
    """Check if a model supports a specific feature.

    Args:
        model_name: Name of the model
        feature: Feature name (e.g., 'google_search_grounding')

    Returns:
        True if feature is supported
    """
    try:
        profile = get_model_profile(model_name)
        return getattr(profile.capabilities, feature, False)
    except (ValueError, AttributeError):
        return False


def get_optimal_config_for_model(
    model_name: str,
    override_generation: Optional[Dict[str, Any]] = None,
    override_evaluation: Optional[Dict[str, Any]] = None,
) -> ModelProfile:
    """Get optimal configuration for a model with optional overrides.

    Args:
        model_name: Name of the model
        override_generation: Override generation config fields
        override_evaluation: Override evaluation config fields

    Returns:
        ModelProfile with applied overrides
    """
    base_profile = get_model_profile(model_name)

    # Create copies to avoid mutating shared MODEL_PROFILES objects
    if override_generation:
        valid_gen = {k: v for k, v in override_generation.items()
                     if hasattr(base_profile.generation, k)}
        generation = dataclasses.replace(base_profile.generation, **valid_gen)
    else:
        generation = base_profile.generation

    if override_evaluation:
        valid_eval = {k: v for k, v in override_evaluation.items()
                      if hasattr(base_profile.evaluation, k)}
        evaluation = dataclasses.replace(base_profile.evaluation, **valid_eval)
    else:
        evaluation = base_profile.evaluation

    return dataclasses.replace(base_profile, generation=generation, evaluation=evaluation)


# Export recommended model as constant
RECOMMENDED_MODEL = get_recommended_model()

# Model constants
FLASH_MODEL = "gemini-3.1-flash-image-preview"              # Nano Banana 2 — fast + accurate (default)
PRO_MODEL = "gemini-3-pro-image-preview"                    # Nano Banana Pro — maximum quality
NANO_BANANA_MODEL = "gemini-2.5-flash-image"                         # Nano Banana — quota fallback
LEGACY_MODEL = "gemini-exp-1206"                            # Legacy compatibility

# Quota cascade: try in order when rate-limited (each has its own daily quota bucket)
QUOTA_CASCADE = [FLASH_MODEL, PRO_MODEL, NANO_BANANA_MODEL]

# Backwards compatibility alias
DEFAULT_MODEL = FLASH_MODEL
