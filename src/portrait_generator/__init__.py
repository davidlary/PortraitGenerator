"""
Portrait Generator - AI-powered historical portrait generation.

A robust, extensible portrait generation system using Google Gemini.
Generates historically accurate portraits - defaults to Painting style (best quality).
Supports multiple styles: BW, Sepia, Color, and Painting (photorealistic).

Simple Python API Examples:
    >>> from portrait_generator import generate_portrait
    >>> result = generate_portrait("Alan Turing", api_key="your_key")
    >>> print(f"Generated {len(result.files)} portraits")  # Defaults to Painting style

    >>> # Or use the client for more control
    >>> from portrait_generator import PortraitClient
    >>> client = PortraitClient(api_key="your_key")
    >>> result = client.generate("Marie Curie")  # Painting style (default)
    >>> result = client.generate("Ada Lovelace", styles=["BW", "Color"])  # Multiple styles
"""

__version__ = "2.0.0"
__author__ = "Dr. David Lary"
__copyright__ = "Copyright 2026, University of Texas at Dallas"
__license__ = "MIT"

# Import core classes
from .core.generator import PortraitGenerator
from .core.researcher import BiographicalResearcher
from .core.evaluator import QualityEvaluator
from .core.overlay import TitleOverlayEngine
from .utils.gemini_client import GeminiImageClient
from .config.settings import Settings

# Import Python API client
from .client import (
    PortraitClient,
    generate_portrait,
    generate_batch,
)

# Import models
from .api.models import (
    PortraitResult,
    PortraitRequest,
    SubjectData,
    EvaluationResult,
)

__all__ = [
    # Core classes
    "PortraitGenerator",
    "BiographicalResearcher",
    "QualityEvaluator",
    "TitleOverlayEngine",
    "GeminiImageClient",
    "Settings",
    # Python API client
    "PortraitClient",
    "generate_portrait",
    "generate_batch",
    # Models
    "PortraitResult",
    "PortraitRequest",
    "SubjectData",
    "EvaluationResult",
    # Metadata
    "__version__",
    "__author__",
    "__copyright__",
    "__license__",
]
