"""High-level Python API for Portrait Generator.

This module provides a simple Python API for generating portraits programmatically.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Union

from .core.generator import PortraitGenerator
from .core.researcher import BiographicalResearcher
from .core.overlay import TitleOverlayEngine
from .core.evaluator import QualityEvaluator
from .utils.gemini_client import GeminiImageClient
from .api.models import PortraitResult
from .config.settings import get_settings

logger = logging.getLogger(__name__)


class PortraitClient:
    """
    High-level client for portrait generation.

    This is the main entry point for using Portrait Generator from Python code.

    Examples:
        >>> from portrait_generator import PortraitClient
        >>> client = PortraitClient(api_key="your_api_key")
        >>> result = client.generate("Albert Einstein")
        >>> print(f"Generated {len(result.files)} portraits")

        >>> # Generate multiple subjects
        >>> results = client.generate_batch(["Alan Turing", "Ada Lovelace"])

        >>> # Generate specific styles only
        >>> result = client.generate("Marie Curie", styles=["BW", "Sepia"])
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        output_dir: Optional[Union[str, Path]] = None,
        model: str = "gemini-exp-1206",
    ):
        """
        Initialize Portrait Generator client.

        Args:
            api_key: Google Gemini API key. If not provided, reads from environment.
            output_dir: Directory for output files. Defaults to './output'.
            model: Gemini model for image generation.

        Raises:
            ValueError: If API key is invalid or missing.
        """
        # Get settings
        if api_key:
            # Override settings with provided API key
            self.api_key = api_key
        else:
            settings = get_settings()
            self.api_key = settings.google_api_key

        # Set output directory
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            settings = get_settings()
            self.output_dir = Path(settings.output_dir)

        self.model = model

        # Initialize components
        self._initialize_components()

        logger.info("PortraitClient initialized")

    def _initialize_components(self):
        """Initialize internal components."""
        # Initialize Gemini client
        self.gemini_client = GeminiImageClient(
            api_key=self.api_key,
            model=self.model,
        )

        # Initialize components
        self.researcher = BiographicalResearcher(self.gemini_client)
        self.overlay_engine = TitleOverlayEngine()
        self.evaluator = QualityEvaluator(self.gemini_client)

        # Initialize generator
        self.generator = PortraitGenerator(
            gemini_client=self.gemini_client,
            researcher=self.researcher,
            overlay_engine=self.overlay_engine,
            evaluator=self.evaluator,
            output_dir=self.output_dir,
        )

    def generate(
        self,
        subject_name: str,
        force_regenerate: bool = False,
        styles: Optional[List[str]] = None,
    ) -> PortraitResult:
        """
        Generate portraits for a subject.

        Args:
            subject_name: Full name of the subject
            force_regenerate: Force regeneration even if files exist
            styles: List of styles to generate (defaults to all 4)

        Returns:
            PortraitResult with generated files and metadata

        Raises:
            ValueError: If subject_name is invalid
            RuntimeError: If generation fails

        Examples:
            >>> client = PortraitClient(api_key="...")
            >>> result = client.generate("Claude Shannon")
            >>> print(result.files)
            {'BW': 'ClaudeShannon_BW.png', 'Sepia': '...', ...}
        """
        return self.generator.generate_portrait(
            subject_name=subject_name,
            force_regenerate=force_regenerate,
            styles=styles,
        )

    def generate_batch(
        self,
        subject_names: List[str],
        force_regenerate: bool = False,
        styles: Optional[List[str]] = None,
    ) -> List[PortraitResult]:
        """
        Generate portraits for multiple subjects.

        Args:
            subject_names: List of subject names
            force_regenerate: Force regeneration even if files exist
            styles: List of styles to generate

        Returns:
            List of PortraitResult objects

        Examples:
            >>> client = PortraitClient(api_key="...")
            >>> results = client.generate_batch([
            ...     "Alan Turing",
            ...     "Ada Lovelace",
            ...     "Grace Hopper"
            ... ])
            >>> success_count = sum(1 for r in results if r.success)
            >>> print(f"{success_count}/{len(results)} successful")
        """
        return self.generator.generate_batch(
            subject_names=subject_names,
            force_regenerate=force_regenerate,
            styles=styles,
        )

    def check_status(self, subject_name: str) -> Dict[str, bool]:
        """
        Check which portraits already exist for a subject.

        Args:
            subject_name: Name of subject to check

        Returns:
            Dictionary of style -> exists (bool)

        Examples:
            >>> client = PortraitClient(api_key="...")
            >>> status = client.check_status("Albert Einstein")
            >>> print(status)
            {'BW': True, 'Sepia': True, 'Color': False, 'Painting': False}
        """
        return self.generator.check_existing_portraits(subject_name)


# Convenience functions for simple usage
def generate_portrait(
    subject_name: str,
    api_key: Optional[str] = None,
    output_dir: Optional[Union[str, Path]] = None,
    force_regenerate: bool = False,
    styles: Optional[List[str]] = None,
) -> PortraitResult:
    """
    Generate portraits for a subject (convenience function).

    This is a simple one-line function for quick portrait generation.

    Args:
        subject_name: Full name of the subject
        api_key: Google Gemini API key (reads from env if not provided)
        output_dir: Directory for output files
        force_regenerate: Force regeneration even if files exist
        styles: List of styles to generate

    Returns:
        PortraitResult with generated files and metadata

    Examples:
        >>> from portrait_generator import generate_portrait
        >>> result = generate_portrait("Alan Turing", api_key="...")
        >>> print(f"Success: {result.success}")
    """
    client = PortraitClient(api_key=api_key, output_dir=output_dir)
    return client.generate(
        subject_name=subject_name,
        force_regenerate=force_regenerate,
        styles=styles,
    )


def generate_batch(
    subject_names: List[str],
    api_key: Optional[str] = None,
    output_dir: Optional[Union[str, Path]] = None,
    force_regenerate: bool = False,
    styles: Optional[List[str]] = None,
) -> List[PortraitResult]:
    """
    Generate portraits for multiple subjects (convenience function).

    Args:
        subject_names: List of subject names
        api_key: Google Gemini API key (reads from env if not provided)
        output_dir: Directory for output files
        force_regenerate: Force regeneration even if files exist
        styles: List of styles to generate

    Returns:
        List of PortraitResult objects

    Examples:
        >>> from portrait_generator import generate_batch
        >>> results = generate_batch(["Turing", "Lovelace"], api_key="...")
    """
    client = PortraitClient(api_key=api_key, output_dir=output_dir)
    return client.generate_batch(
        subject_names=subject_names,
        force_regenerate=force_regenerate,
        styles=styles,
    )
