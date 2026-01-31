"""Intelligence coordinator for autonomous portrait generation pipeline.

This module orchestrates the full autonomous pipeline:
- Automatic model selection and feature detection
- Intelligent component initialization
- Coordinated workflow execution
- Adaptive error handling and recovery
"""

import logging
from pathlib import Path
from typing import Optional

from .config.settings import Settings
from .config.model_configs import get_model_profile
from .compatibility import CompatibilityManager
from .utils.gemini_client import GeminiImageClient
from .core.researcher import BiographicalResearcher
from .core.overlay import TitleOverlayEngine
from .core.generator import PortraitGenerator
from .core.evaluator import QualityEvaluator

logger = logging.getLogger(__name__)


class IntelligenceCoordinator:
    """Coordinates intelligent portrait generation pipeline.

    Automatically detects model capabilities and orchestrates:
    - Component initialization based on available features
    - Enhanced vs basic workflow selection
    - Adaptive quality thresholds
    - Seamless fallback for unsupported features
    """

    def __init__(
        self,
        settings: Optional[Settings] = None,
    ):
        """Initialize intelligence coordinator.

        Args:
            settings: Settings object (uses defaults if None)
        """
        self.settings = settings or Settings()

        # Validate configuration
        if not self.settings.validate_api_key():
            raise ValueError(
                "Invalid or missing Google API key. "
                "Set GOOGLE_API_KEY environment variable."
            )

        # Get model profile and compatibility
        self.model_profile = self.settings.get_model_profile()
        self.compatibility = CompatibilityManager(self.settings.gemini_model)

        logger.info(
            f"Initialized IntelligenceCoordinator with model: {self.settings.gemini_model}"
        )

        # Log capabilities
        self.compatibility.log_capabilities()

        # Initialize components
        self._initialize_components()

    def _initialize_components(self):
        """Initialize all components based on model capabilities."""
        logger.info("Initializing components...")

        # 1. Initialize Gemini client
        self.gemini_client = GeminiImageClient(
            api_key=self.settings.google_api_key,
            model=self.settings.gemini_model,
            enable_grounding=self.compatibility.supports_google_search_grounding(),
            enable_reasoning=self.compatibility.supports_internal_reasoning(),
        )
        logger.info("✓ Gemini client initialized")

        # 2. Initialize researcher
        self.researcher = BiographicalResearcher(
            gemini_client=self.gemini_client,
        )
        logger.info("✓ Researcher initialized")

        # 3. Initialize overlay engine
        self.overlay_engine = TitleOverlayEngine()
        logger.info("✓ Overlay engine initialized")

        # 4. Initialize evaluator (enhanced or basic)
        if self._should_use_enhanced_evaluator():
            from .core.evaluator_enhanced import EnhancedQualityEvaluator
            self.evaluator = EnhancedQualityEvaluator(
                gemini_client=self.gemini_client,
                model_profile=self.model_profile,
            )
            logger.info("✓ Enhanced evaluator initialized")
        else:
            self.evaluator = QualityEvaluator(
                gemini_client=self.gemini_client,
            )
            logger.info("✓ Basic evaluator initialized")

        # 5. Initialize generator (enhanced or basic)
        if self._should_use_enhanced_generator():
            from .core.generator_enhanced import EnhancedPortraitGenerator
            self.generator = EnhancedPortraitGenerator(
                gemini_client=self.gemini_client,
                researcher=self.researcher,
                overlay_engine=self.overlay_engine,
                evaluator=self.evaluator,
                output_dir=self.settings.output_dir,
                settings=self.settings,
            )
            logger.info("✓ Enhanced generator initialized")
        else:
            self.generator = PortraitGenerator(
                gemini_client=self.gemini_client,
                researcher=self.researcher,
                overlay_engine=self.overlay_engine,
                evaluator=self.evaluator,
                output_dir=self.settings.output_dir,
            )
            logger.info("✓ Basic generator initialized")

        logger.info("All components initialized successfully")

    def _should_use_enhanced_evaluator(self) -> bool:
        """Determine if enhanced evaluator should be used.

        Returns:
            True if enhanced evaluator is supported
        """
        return (
            self.settings.enable_advanced_features
            and (
                self.compatibility.supports_internal_reasoning()
                or self.compatibility.supports_google_search_grounding()
            )
        )

    def _should_use_enhanced_generator(self) -> bool:
        """Determine if enhanced generator should be used.

        Returns:
            True if enhanced generator is supported
        """
        return (
            self.settings.enable_advanced_features
            and (
                self.compatibility.should_use_reference_images()
                or self.compatibility.should_use_pre_generation_checks()
                or self.compatibility.supports_internal_reasoning()
            )
        )

    def generate_portrait(
        self,
        subject_name: str,
        force_regenerate: bool = False,
        styles: Optional[list] = None,
    ):
        """Generate portrait using coordinated pipeline.

        Args:
            subject_name: Name of subject
            force_regenerate: Force regeneration even if exists
            styles: List of styles to generate

        Returns:
            PortraitResult
        """
        logger.info(
            f"Generating portrait for '{subject_name}' "
            f"(enhanced={'Yes' if self._should_use_enhanced_generator() else 'No'})"
        )

        return self.generator.generate_portrait(
            subject_name=subject_name,
            force_regenerate=force_regenerate,
            styles=styles,
        )

    def generate_batch(
        self,
        subject_names: list,
        force_regenerate: bool = False,
        styles: Optional[list] = None,
    ):
        """Generate portraits for multiple subjects.

        Args:
            subject_names: List of subject names
            force_regenerate: Force regeneration
            styles: List of styles

        Returns:
            List of PortraitResult objects
        """
        logger.info(
            f"Starting batch generation for {len(subject_names)} subjects "
            f"(enhanced={'Yes' if self._should_use_enhanced_generator() else 'No'})"
        )

        return self.generator.generate_batch(
            subject_names=subject_names,
            force_regenerate=force_regenerate,
            styles=styles,
        )

    def get_system_info(self) -> dict:
        """Get system information and capabilities.

        Returns:
            Dictionary with system info
        """
        return {
            "model": self.settings.gemini_model,
            "model_profile": {
                "display_name": self.model_profile.display_name,
                "is_recommended": self.model_profile.is_recommended,
                "release_date": self.model_profile.release_date,
            },
            "capabilities": {
                "google_search_grounding": self.compatibility.supports_google_search_grounding(),
                "multi_image_reference": self.compatibility.supports_multi_image_reference(),
                "max_reference_images": self.compatibility.get_max_reference_images(),
                "internal_reasoning": self.compatibility.supports_internal_reasoning(),
                "physics_aware_synthesis": self.compatibility.supports_physics_aware_synthesis(),
                "native_text_rendering": self.compatibility.supports_native_text_rendering(),
                "iterative_refinement": self.compatibility.supports_iterative_refinement(),
            },
            "generation_config": self.compatibility.get_generation_config(),
            "evaluation_config": self.compatibility.get_evaluation_config(),
            "quality_thresholds": self.compatibility.get_quality_thresholds(),
            "components": {
                "generator": "Enhanced" if self._should_use_enhanced_generator() else "Basic",
                "evaluator": "Enhanced" if self._should_use_enhanced_evaluator() else "Basic",
            },
            "settings": {
                "output_dir": str(self.settings.output_dir),
                "resolution": self.settings.resolution_tuple,
                "advanced_features_enabled": self.settings.enable_advanced_features,
            },
        }

    def validate_setup(self) -> tuple[bool, list]:
        """Validate system setup and configuration.

        Returns:
            Tuple of (is_valid, issues)
        """
        issues = []

        # Check API key
        if not self.settings.validate_api_key():
            issues.append("Invalid or missing Google API key")

        # Check output directory
        if not self.settings.output_dir.exists():
            try:
                self.settings.output_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                issues.append(f"Cannot create output directory: {e}")

        # Check if output directory is writable
        test_file = self.settings.output_dir / ".test_write"
        try:
            test_file.write_text("test")
            test_file.unlink()
        except Exception as e:
            issues.append(f"Output directory not writable: {e}")

        # Warn if using legacy model
        if self.compatibility.is_legacy_model():
            logger.warning(
                f"Using legacy model: {self.settings.gemini_model}. "
                "Consider upgrading to gemini-3-pro-image-preview for advanced features."
            )

        is_valid = len(issues) == 0

        return is_valid, issues

    def get_migration_recommendations(self) -> list:
        """Get recommendations for upgrading to better models.

        Returns:
            List of recommendations
        """
        return self.compatibility.get_migration_recommendations()

    def compare_with_model(self, other_model: str) -> dict:
        """Compare current model with another model.

        Args:
            other_model: Name of model to compare

        Returns:
            Comparison dictionary
        """
        return self.compatibility.get_feature_comparison(other_model)


def create_coordinator(
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    output_dir: Optional[Path] = None,
    **kwargs,
) -> IntelligenceCoordinator:
    """Factory function to create intelligence coordinator.

    Args:
        api_key: Google API key (uses env var if None)
        model: Model name (uses default if None)
        output_dir: Output directory (uses default if None)
        **kwargs: Additional settings

    Returns:
        IntelligenceCoordinator instance
    """
    settings_dict = {}

    if api_key:
        settings_dict['google_api_key'] = api_key

    if model:
        settings_dict['gemini_model'] = model

    if output_dir:
        settings_dict['output_dir'] = output_dir

    settings_dict.update(kwargs)

    settings = Settings(**settings_dict)

    return IntelligenceCoordinator(settings=settings)
