"""Compatibility manager for backward compatibility with older models.

This module provides automatic feature detection and graceful fallback
for models that don't support advanced Gemini 3 Pro Image features.
"""

import logging
from typing import Optional, Any

from .config.model_configs import get_model_profile, MODEL_PROFILES

logger = logging.getLogger(__name__)


class CompatibilityManager:
    """Manages backward compatibility across different Gemini models.

    Automatically detects model capabilities and provides appropriate
    fallbacks for unsupported features.
    """

    def __init__(self, model_name: str):
        """Initialize compatibility manager.

        Args:
            model_name: Name of the Gemini model
        """
        self.model_name = model_name
        self.profile = self._get_profile_safe(model_name)
        logger.debug(f"Initialized compatibility manager for {model_name}")

    def _get_profile_safe(self, model_name: str):
        """Get model profile with fallback.

        Args:
            model_name: Model name

        Returns:
            Model profile or None if not found
        """
        try:
            return get_model_profile(model_name)
        except ValueError:
            logger.warning(f"Unknown model {model_name}, using fallback compatibility mode")
            return None

    def supports_feature(self, feature: str) -> bool:
        """Check if model supports a specific feature.

        Args:
            feature: Feature name (e.g., 'google_search_grounding')

        Returns:
            True if feature is supported
        """
        if not self.profile:
            return False

        return getattr(self.profile.capabilities, feature, False)

    def supports_google_search_grounding(self) -> bool:
        """Check if model supports Google Search grounding.

        Returns:
            True if supported
        """
        return self.supports_feature('google_search_grounding')

    def supports_multi_image_reference(self) -> bool:
        """Check if model supports multiple reference images.

        Returns:
            True if supported
        """
        return self.supports_feature('multi_image_reference')

    def supports_internal_reasoning(self) -> bool:
        """Check if model supports internal reasoning.

        Returns:
            True if supported
        """
        return self.supports_feature('internal_reasoning')

    def supports_physics_aware_synthesis(self) -> bool:
        """Check if model supports physics-aware synthesis.

        Returns:
            True if supported
        """
        return self.supports_feature('physics_aware_synthesis')

    def supports_native_text_rendering(self) -> bool:
        """Check if model supports native text rendering.

        Returns:
            True if supported
        """
        return self.supports_feature('native_text_rendering')

    def supports_iterative_refinement(self) -> bool:
        """Check if model supports iterative refinement.

        Returns:
            True if supported
        """
        return self.supports_feature('iterative_refinement')

    def get_max_reference_images(self) -> int:
        """Get maximum number of reference images supported.

        Returns:
            Maximum number of reference images
        """
        if not self.profile:
            return 0

        return self.profile.capabilities.max_reference_images

    def should_use_reference_images(self) -> bool:
        """Check if reference images should be used.

        Returns:
            True if reference images are enabled and supported
        """
        if not self.profile:
            return False

        return (
            self.profile.capabilities.multi_image_reference
            and self.profile.generation.enable_reference_images
        )

    def should_use_pre_generation_checks(self) -> bool:
        """Check if pre-generation checks should be used.

        Returns:
            True if checks should be performed
        """
        if not self.profile:
            return False

        return self.profile.generation.enable_pre_generation_checks

    def should_use_fact_checking(self) -> bool:
        """Check if fact-checking should be used.

        Returns:
            True if fact-checking is enabled
        """
        if not self.profile:
            return False

        return (
            self.profile.capabilities.google_search_grounding
            and self.profile.generation.enable_search_grounding
        )

    def get_generation_config(self) -> dict:
        """Get generation configuration for this model.

        Returns:
            Dictionary of generation configuration
        """
        if not self.profile:
            return {
                'enable_pre_generation_checks': False,
                'enable_iterative_refinement': False,
                'max_internal_iterations': 1,
                'enable_search_grounding': False,
                'enable_reference_images': False,
                'max_reference_images_to_use': 0,
                'max_generation_attempts': 2,
                'enable_smart_retry': False,
            }

        return {
            'enable_pre_generation_checks': self.profile.generation.enable_pre_generation_checks,
            'enable_iterative_refinement': self.profile.generation.enable_iterative_refinement,
            'max_internal_iterations': self.profile.generation.max_internal_iterations,
            'enable_search_grounding': self.profile.generation.enable_search_grounding,
            'enable_reference_images': self.profile.generation.enable_reference_images,
            'max_reference_images_to_use': self.profile.generation.max_reference_images_to_use,
            'max_generation_attempts': self.profile.generation.max_generation_attempts,
            'enable_smart_retry': self.profile.generation.enable_smart_retry,
        }

    def get_evaluation_config(self) -> dict:
        """Get evaluation configuration for this model.

        Returns:
            Dictionary of evaluation configuration
        """
        if not self.profile:
            return {
                'use_holistic_reasoning': False,
                'reasoning_passes': 1,
                'autonomous_error_detection': False,
                'visual_coherence_checking': False,
                'enable_fact_checking': False,
            }

        return {
            'use_holistic_reasoning': self.profile.evaluation.use_holistic_reasoning,
            'reasoning_passes': self.profile.evaluation.reasoning_passes,
            'autonomous_error_detection': self.profile.evaluation.autonomous_error_detection,
            'visual_coherence_checking': self.profile.evaluation.visual_coherence_checking,
            'enable_fact_checking': self.profile.evaluation.enable_fact_checking,
        }

    def get_quality_thresholds(self) -> dict:
        """Get quality thresholds for this model.

        Returns:
            Dictionary of quality thresholds
        """
        if not self.profile:
            return {
                'quality_threshold': 0.80,
                'confidence_threshold': 0.75,
            }

        return {
            'quality_threshold': self.profile.generation.quality_threshold,
            'confidence_threshold': self.profile.generation.confidence_threshold,
        }

    def is_legacy_model(self) -> bool:
        """Check if this is a legacy model.

        Returns:
            True if model is considered legacy
        """
        if not self.profile:
            return True

        return not self.profile.is_recommended

    def get_migration_recommendations(self) -> list:
        """Get recommendations for migrating from this model.

        Returns:
            List of migration recommendations
        """
        if not self.profile or self.profile.is_recommended:
            return []

        recommendations = [
            "Consider upgrading to gemini-3-pro-image-preview for advanced features:",
            "  - Google Search grounding for fact-checking",
            "  - Multi-image reference support (up to 14 images)",
            "  - Internal reasoning and iterative refinement",
            "  - Physics-aware synthesis",
            "  - Native LLM-based text rendering",
            "  - Higher quality thresholds (90% vs 80%)",
            "  - Autonomous error detection",
        ]

        return recommendations

    def adapt_settings_for_model(self, settings: dict) -> dict:
        """Adapt settings for model capabilities.

        Args:
            settings: Desired settings

        Returns:
            Adapted settings compatible with model
        """
        adapted = settings.copy()

        if not self.profile:
            # Disable all advanced features for unknown models
            adapted['enable_reference_images'] = False
            adapted['enable_search_grounding'] = False
            adapted['enable_internal_reasoning'] = False
            adapted['enable_pre_generation_checks'] = False
            adapted['use_holistic_reasoning'] = False
            return adapted

        # Disable unsupported features
        if not self.profile.capabilities.multi_image_reference:
            adapted['enable_reference_images'] = False
            adapted['max_reference_images'] = 0

        if not self.profile.capabilities.google_search_grounding:
            adapted['enable_search_grounding'] = False

        if not self.profile.capabilities.internal_reasoning:
            adapted['enable_internal_reasoning'] = False
            adapted['max_internal_iterations'] = 1

        if not self.profile.capabilities.iterative_refinement:
            adapted['enable_iterative_refinement'] = False

        # Adjust thresholds to model capabilities
        if self.profile.generation.quality_threshold < settings.get('quality_threshold', 0.90):
            logger.info(
                f"Lowering quality threshold to {self.profile.generation.quality_threshold} "
                f"for model {self.model_name}"
            )
            adapted['quality_threshold'] = self.profile.generation.quality_threshold

        return adapted

    def get_feature_comparison(self, other_model: str) -> dict:
        """Compare features with another model.

        Args:
            other_model: Name of model to compare with

        Returns:
            Dictionary of feature comparisons
        """
        if not self.profile:
            return {}

        try:
            other_profile = get_model_profile(other_model)
        except ValueError:
            return {}

        comparison = {
            'google_search_grounding': {
                'current': self.profile.capabilities.google_search_grounding,
                'other': other_profile.capabilities.google_search_grounding,
            },
            'multi_image_reference': {
                'current': self.profile.capabilities.multi_image_reference,
                'other': other_profile.capabilities.multi_image_reference,
            },
            'internal_reasoning': {
                'current': self.profile.capabilities.internal_reasoning,
                'other': other_profile.capabilities.internal_reasoning,
            },
            'physics_aware_synthesis': {
                'current': self.profile.capabilities.physics_aware_synthesis,
                'other': other_profile.capabilities.physics_aware_synthesis,
            },
            'max_reference_images': {
                'current': self.profile.capabilities.max_reference_images,
                'other': other_profile.capabilities.max_reference_images,
            },
            'quality_threshold': {
                'current': self.profile.generation.quality_threshold,
                'other': other_profile.generation.quality_threshold,
            },
        }

        return comparison

    def log_capabilities(self):
        """Log model capabilities for debugging."""
        if not self.profile:
            logger.info(f"Model {self.model_name}: Unknown (using fallback mode)")
            return

        logger.info(f"Model {self.model_name} capabilities:")
        logger.info(f"  - Google Search Grounding: {self.profile.capabilities.google_search_grounding}")
        logger.info(f"  - Multi-Image Reference: {self.profile.capabilities.multi_image_reference}")
        logger.info(f"  - Max Reference Images: {self.profile.capabilities.max_reference_images}")
        logger.info(f"  - Internal Reasoning: {self.profile.capabilities.internal_reasoning}")
        logger.info(f"  - Physics-Aware Synthesis: {self.profile.capabilities.physics_aware_synthesis}")
        logger.info(f"  - Native Text Rendering: {self.profile.capabilities.native_text_rendering}")
        logger.info(f"  - Iterative Refinement: {self.profile.capabilities.iterative_refinement}")
        logger.info(f"  - Quality Threshold: {self.profile.generation.quality_threshold}")
        logger.info(f"  - Recommended: {self.profile.is_recommended}")


def get_compatibility_manager(model_name: str) -> CompatibilityManager:
    """Factory function to get compatibility manager for a model.

    Args:
        model_name: Name of the model

    Returns:
        CompatibilityManager instance
    """
    return CompatibilityManager(model_name)


def list_compatible_models() -> list:
    """List all compatible models.

    Returns:
        List of model names
    """
    return list(MODEL_PROFILES.keys())


def get_recommended_model() -> str:
    """Get the recommended model name.

    Returns:
        Name of recommended model
    """
    from .config.model_configs import get_recommended_model as get_rec
    return get_rec()
