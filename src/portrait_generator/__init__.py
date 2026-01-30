"""
Portrait Generator API

A robust, extensible portrait generation system using Google Gemini.
Generates historically accurate portraits in multiple styles (BW, Sepia, Color, Painting).
"""

__version__ = "1.0.0"
__author__ = "Dr. David Lary"
__copyright__ = "Copyright 2026, University of Texas at Dallas"
__license__ = "MIT"

from .core.generator import PortraitGenerator
from .core.researcher import BiographicalResearcher
from .core.evaluator import QualityEvaluator
from .core.overlay import TitleOverlayEngine
from .utils.gemini_client import GeminiImageClient
from .config.settings import Settings

__all__ = [
    "PortraitGenerator",
    "BiographicalResearcher",
    "QualityEvaluator",
    "TitleOverlayEngine",
    "GeminiImageClient",
    "Settings",
]
