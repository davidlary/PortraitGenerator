"""Configuration settings for Portrait Generator."""

import os
from pathlib import Path
from typing import Tuple, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # API Keys (REQUIRED from environment)
    google_api_key: str = Field(..., description="Google Gemini API key")

    # Gemini Model Configuration
    gemini_model: str = Field(
        default="gemini-3-pro-image-preview",
        description="Gemini model for image generation (default: gemini-3-pro-image-preview)",
    )

    # Image Settings
    image_resolution: str = Field(
        default="1024,1024",
        description="Image resolution as 'width,height'",
    )
    portrait_quality: int = Field(
        default=95,
        ge=1,
        le=100,
        description="JPEG quality (1-100)",
    )

    # Advanced Features (Gemini 3 Pro Image)
    enable_advanced_features: bool = Field(
        default=True,
        description="Enable advanced features for capable models",
    )
    enable_reference_images: bool = Field(
        default=False,  # Changed to False in v2.1.0 - Google API returns empty results
        description="Enable reference image finding and usage",
    )
    max_reference_images: int = Field(
        default=5,
        ge=0,
        le=14,
        description="Maximum reference images to use (0-14)",
    )
    enable_search_grounding: bool = Field(
        default=False,  # Changed to False in v2.1.0 - Google API returns empty results
        description="Enable Google Search fact-checking and grounding",
    )
    enable_internal_reasoning: bool = Field(
        default=True,
        description="Enable model's internal reasoning and iteration",
    )
    max_internal_iterations: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Maximum internal reasoning iterations",
    )

    # Quality and Validation
    quality_threshold: float = Field(
        default=0.90,
        ge=0.0,
        le=1.0,
        description="Minimum quality score for acceptance (0.0-1.0)",
    )
    confidence_threshold: float = Field(
        default=0.85,
        ge=0.0,
        le=1.0,
        description="Minimum confidence to proceed without retry (0.0-1.0)",
    )
    enable_pre_generation_checks: bool = Field(
        default=True,
        description="Run validation before generation starts",
    )
    enable_autonomous_error_detection: bool = Field(
        default=True,
        description="Proactively detect and prevent errors",
    )

    # Evaluation Settings
    use_holistic_reasoning: bool = Field(
        default=True,
        description="Use model's reasoning for holistic evaluation",
    )
    reasoning_passes: int = Field(
        default=2,
        ge=1,
        le=5,
        description="Number of reasoning passes for consistency",
    )
    enable_visual_coherence_checking: bool = Field(
        default=True,
        description="Check visual coherence using physics-aware analysis",
    )

    # Generation Behavior
    max_generation_attempts: int = Field(
        default=2,
        ge=1,
        le=5,
        description="Maximum generation attempts before failure",
    )
    enable_smart_retry: bool = Field(
        default=True,
        description="Use reasoning to refine prompt on retry",
    )

    # Text Rendering
    use_native_text_rendering: bool = Field(
        default=True,
        description="Use model's native LLM-based text rendering (vs post-processing overlay)",
    )

    # Output Settings
    output_dir: Path = Field(
        default=Path("./output"),
        description="Output directory for generated portraits",
    )
    save_prompts: bool = Field(
        default=True,
        description="Save prompt markdown files alongside images",
    )

    # Testing Settings
    visual_inspection_enabled: bool = Field(
        default=True,
        description="Enable visual inspection tests",
    )

    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level",
    )

    # API Settings
    max_concurrent_requests: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum concurrent API requests",
    )

    @field_validator("output_dir", mode="before")
    @classmethod
    def create_output_dir(cls, v: Path | str) -> Path:
        """Ensure output directory exists."""
        path = Path(v) if isinstance(v, str) else v
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def resolution_tuple(self) -> Tuple[int, int]:
        """Parse resolution string to tuple."""
        parts = self.image_resolution.split(",")
        if len(parts) != 2:
            return (1024, 1024)
        try:
            return (int(parts[0].strip()), int(parts[1].strip()))
        except ValueError:
            return (1024, 1024)

    def validate_api_key(self) -> bool:
        """Validate that API key is set and not a placeholder."""
        if not self.google_api_key:
            return False
        if "your_" in self.google_api_key.lower():
            return False
        if len(self.google_api_key) < 20:
            return False
        return True

    def get_model_profile(self):
        """Get the model profile for the configured model.

        Returns:
            ModelProfile with capabilities and optimal configuration

        Note:
            Import model_configs here to avoid circular imports
        """
        from .model_configs import get_optimal_config_for_model

        # Build overrides from settings
        generation_overrides = {}
        evaluation_overrides = {}

        if not self.enable_advanced_features:
            # Disable all advanced features
            generation_overrides.update({
                "enable_pre_generation_checks": False,
                "enable_iterative_refinement": False,
                "enable_search_grounding": False,
                "enable_reference_images": False,
            })

        # Apply specific overrides from settings
        if self.quality_threshold is not None:
            generation_overrides["quality_threshold"] = self.quality_threshold

        if self.confidence_threshold is not None:
            generation_overrides["confidence_threshold"] = self.confidence_threshold

        if self.max_reference_images is not None:
            generation_overrides["max_reference_images_to_use"] = self.max_reference_images

        if self.max_internal_iterations is not None:
            generation_overrides["max_internal_iterations"] = self.max_internal_iterations

        if self.max_generation_attempts is not None:
            generation_overrides["max_generation_attempts"] = self.max_generation_attempts

        if self.reasoning_passes is not None:
            evaluation_overrides["reasoning_passes"] = self.reasoning_passes

        # Get profile with overrides
        return get_optimal_config_for_model(
            self.gemini_model,
            override_generation=generation_overrides,
            override_evaluation=evaluation_overrides,
        )

    def model_supports_feature(self, feature: str) -> bool:
        """Check if the configured model supports a specific feature.

        Args:
            feature: Feature name (e.g., 'google_search_grounding')

        Returns:
            True if feature is supported
        """
        try:
            profile = self.get_model_profile()
            return getattr(profile.capabilities, feature, False)
        except Exception:
            return False


def get_settings() -> Settings:
    """Factory function to get settings instance."""
    return Settings()
