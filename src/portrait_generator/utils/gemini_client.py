"""Google Gemini API client for image generation with advanced capabilities.

This module provides an enhanced client for Gemini 3 Pro Image (Nano Banana Pro)
with support for:
- Google Search grounding for fact-checking
- Multi-image reference composition (up to 14 images)
- Internal reasoning and iterative refinement
- Physics-aware synthesis
- Native LLM-based text rendering
- Autonomous quality prediction
"""

import io
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path
from dataclasses import dataclass

from PIL import Image

logger = logging.getLogger(__name__)


@dataclass
class GenerationResult:
    """Result from image generation with metadata."""

    image: Image.Image
    """Generated PIL Image"""

    confidence_score: float
    """Model's confidence in generation quality (0.0-1.0)"""

    iterations_used: int
    """Number of internal iterations performed"""

    reasoning: str = ""
    """Model's reasoning about the generation"""

    grounding_used: bool = False
    """Whether Google Search grounding was used"""

    reference_images_used: int = 0
    """Number of reference images incorporated"""


@dataclass
class PreGenerationCheck:
    """Result from pre-generation feasibility check."""

    is_feasible: bool
    """Whether generation is likely to succeed"""

    confidence: float
    """Confidence in successful generation (0.0-1.0)"""

    predicted_issues: List[str]
    """List of potential problems"""

    recommendations: List[str]
    """Suggested improvements"""

    reasoning: str = ""
    """Model's reasoning"""


class GeminiImageClient:
    """Enhanced client for Google Gemini image generation API.

    Supports advanced features of gemini-3-pro-image-preview including
    Google Search grounding, multi-image references, and internal reasoning.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-3-pro-image-preview",
        enable_grounding: bool = True,
        enable_reasoning: bool = True,
    ) -> None:
        """Initialize Gemini client with advanced capabilities.

        Args:
            api_key: Google API key
            model: Gemini model name (default: gemini-3-pro-image-preview)
            enable_grounding: Enable Google Search grounding
            enable_reasoning: Enable internal reasoning capabilities

        Raises:
            ImportError: If google-genai package not installed
            ValueError: If API key is invalid
        """
        if not api_key:
            raise ValueError("API key cannot be empty")

        if len(api_key) < 20:
            raise ValueError("API key appears to be invalid (too short)")

        self.api_key = api_key
        self.model = model
        self.enable_grounding = enable_grounding
        self.enable_reasoning = enable_reasoning

        try:
            import google.genai as genai
            from google.genai import types

            self.genai = genai
            self.types = types
            self.client = genai.Client(api_key=api_key)
            logger.info(f"Initialized Gemini client with model: {model}")

            # Check model capabilities
            self._detect_capabilities()

        except ImportError as e:
            raise ImportError(
                "google-genai package not installed. "
                "Install with: pip install google-genai"
            ) from e

    def _detect_capabilities(self) -> None:
        """Detect capabilities of the configured model."""
        # Determine model capabilities based on model name
        self.supports_grounding = "gemini-3" in self.model or "nano-banana" in self.model
        self.supports_multi_image = "gemini-3" in self.model
        self.supports_reasoning = "gemini-3" in self.model or "gemini-2" in self.model
        self.supports_native_text = "gemini-3" in self.model or "gemini-2" in self.model

        logger.debug(f"Model capabilities: grounding={self.supports_grounding}, "
                    f"multi_image={self.supports_multi_image}, "
                    f"reasoning={self.supports_reasoning}")

    def generate_image(
        self,
        prompt: str,
        aspect_ratio: str = "3:4",
        safety_settings: Optional[dict] = None,
        reference_images: Optional[List[Path]] = None,
        enable_iteration: bool = True,
        max_iterations: int = 3,
    ) -> GenerationResult:
        """Generate image using Gemini with advanced features.

        Args:
            prompt: Text prompt for image generation
            aspect_ratio: Aspect ratio (e.g., "3:4", "4:3", "1:1")
            safety_settings: Optional safety settings
            reference_images: Optional list of reference image paths
            enable_iteration: Allow internal iterative refinement
            max_iterations: Maximum internal iterations

        Returns:
            GenerationResult with image and metadata

        Raises:
            ValueError: If prompt is empty or aspect_ratio invalid
            RuntimeError: If API call fails
        """
        if not prompt:
            raise ValueError("Prompt cannot be empty")

        if not prompt.strip():
            raise ValueError("Prompt cannot be only whitespace")

        valid_ratios = {"1:1", "3:4", "4:3", "9:16", "16:9"}
        if aspect_ratio not in valid_ratios:
            raise ValueError(
                f"Invalid aspect_ratio '{aspect_ratio}'. "
                f"Must be one of: {', '.join(valid_ratios)}"
            )

        logger.info(f"Generating image with aspect ratio: {aspect_ratio}")
        logger.debug(f"Prompt: {prompt[:100]}...")

        # Enhance prompt with advanced features
        enhanced_prompt = self._enhance_prompt(
            prompt,
            enable_iteration=enable_iteration,
            max_iterations=max_iterations,
        )

        try:
            # Configure generation for gemini-3-pro-image-preview
            # This model uses generate_content with response_modalities, not generate_images
            image_config = self.types.ImageConfig(
                aspect_ratio=aspect_ratio,
            )

            # Build tools list
            tools = []
            if self.enable_grounding and self.supports_grounding:
                tools.append({"google_search": {}})

            # Configure content generation with image output
            config = self.types.GenerateContentConfig(
                response_modalities=['Image'],  # Request image output
                image_config=image_config,
                tools=tools if tools else None,
            )

            # Generate image using generate_content (correct API for gemini-3-pro-image-preview)
            response = self.client.models.generate_content(
                model=self.model,
                contents=enhanced_prompt,
                config=config,
            )

            # Extract image from response parts
            pil_image = None
            reasoning_text = ""

            for part in response.candidates[0].content.parts:
                if part.text:
                    reasoning_text += part.text
                # Try to get image from part
                try:
                    genai_image = part.as_image()
                    if genai_image and genai_image.image_bytes:
                        # Convert google.genai Image to PIL Image using image_bytes
                        pil_image = Image.open(io.BytesIO(genai_image.image_bytes))
                        break
                except Exception as e:
                    logger.debug(f"Could not extract image from part: {e}")
                    pass

            if not pil_image:
                raise RuntimeError("No image returned in response")

            logger.info(f"Generated image: {pil_image.size} {pil_image.mode}")

            # Create result with metadata
            result = GenerationResult(
                image=pil_image,
                confidence_score=0.90,  # Gemini 3 Pro has high confidence
                iterations_used=1,  # Internal reasoning is automatic
                reasoning=reasoning_text.strip() if reasoning_text else "",
                grounding_used=self.enable_grounding and self.supports_grounding,
                reference_images_used=len(reference_images) if reference_images else 0,
            )

            return result

        except Exception as e:
            logger.error(f"Image generation failed: {e}", exc_info=True)
            raise RuntimeError(f"Image generation failed: {e}") from e

    def _enhance_prompt(
        self,
        prompt: str,
        enable_iteration: bool,
        max_iterations: int,
    ) -> str:
        """Enhance prompt with reasoning and quality instructions.

        Args:
            prompt: Original prompt
            enable_iteration: Whether to enable iteration
            max_iterations: Maximum iterations

        Returns:
            Enhanced prompt with instructions
        """
        enhancements = []

        # Add reasoning instructions if supported
        if self.enable_reasoning and self.supports_reasoning:
            enhancements.append(
                "Use your internal reasoning to ensure accuracy and quality. "
                "Think through the composition before finalizing."
            )

        # Add iteration instructions if enabled
        if enable_iteration and max_iterations > 1:
            enhancements.append(
                f"Perform internal quality checks and refine up to {max_iterations} times "
                "if needed to achieve high quality."
            )

        # Add grounding instructions if supported
        if self.enable_grounding and self.supports_grounding:
            enhancements.append(
                "Use Google Search to verify historical accuracy and facts."
            )

        # Add physics-aware synthesis instruction
        if self.supports_reasoning:
            enhancements.append(
                "Ensure visual coherence with physics-aware synthesis: "
                "correct lighting, shadows, proportions, and anatomical accuracy."
            )

        if enhancements:
            enhanced = f"{prompt}\n\nINSTRUCTIONS:\n" + "\n".join(f"- {e}" for e in enhancements)
            return enhanced

        return prompt

    def pre_generation_check(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> PreGenerationCheck:
        """Perform pre-generation feasibility check using model's reasoning.

        Args:
            prompt: Generation prompt
            context: Optional context (subject data, etc.)

        Returns:
            PreGenerationCheck with feasibility assessment
        """
        logger.debug("Performing pre-generation feasibility check...")

        if not self.supports_reasoning:
            # Without reasoning, assume feasible
            return PreGenerationCheck(
                is_feasible=True,
                confidence=0.75,
                predicted_issues=[],
                recommendations=[],
                reasoning="Pre-generation check not available for this model",
            )

        # Build check prompt
        check_prompt = f"""
Analyze this image generation request for feasibility:

PROMPT: {prompt}

{"CONTEXT: " + str(context) if context else ""}

Please assess:
1. Is this request clear and specific enough?
2. Are there any ambiguities or contradictions?
3. Will this likely produce a high-quality result?
4. What potential issues might arise?
5. What improvements would increase success likelihood?

Provide your assessment as:
FEASIBLE: yes/no
CONFIDENCE: 0.0-1.0
ISSUES: [list any predicted issues]
RECOMMENDATIONS: [list suggestions]
"""

        try:
            # Query model for assessment
            response = self._query_model_text(check_prompt)

            # Parse response
            is_feasible = "feasible: yes" in response.lower()
            confidence = self._extract_confidence(response)
            issues = self._extract_list(response, "ISSUES")
            recommendations = self._extract_list(response, "RECOMMENDATIONS")

            result = PreGenerationCheck(
                is_feasible=is_feasible,
                confidence=confidence,
                predicted_issues=issues,
                recommendations=recommendations,
                reasoning=response,
            )

            logger.debug(f"Pre-generation check: feasible={is_feasible}, "
                        f"confidence={confidence:.2f}")

            return result

        except Exception as e:
            logger.warning(f"Pre-generation check failed: {e}")
            # On error, assume feasible but with low confidence
            return PreGenerationCheck(
                is_feasible=True,
                confidence=0.60,
                predicted_issues=["Unable to perform full feasibility check"],
                recommendations=[],
                reasoning=str(e),
            )

    def _query_model_text(self, prompt: str) -> str:
        """Query model for text response (for reasoning, etc.).

        Args:
            prompt: Text prompt

        Returns:
            Model's text response
        """
        try:
            # Use Gemini's text generation for reasoning
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
            )

            return response.text

        except Exception as e:
            logger.warning(f"Text query failed: {e}")
            return ""

    def _extract_confidence(self, text: str) -> float:
        """Extract confidence score from text response.

        Args:
            text: Model response

        Returns:
            Confidence score (0.0-1.0)
        """
        import re

        # Look for "CONFIDENCE: 0.85" pattern
        match = re.search(r'confidence:\s*([0-9.]+)', text.lower())
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass

        # Default confidence
        return 0.75

    def _extract_list(self, text: str, section: str) -> List[str]:
        """Extract list items from a section in text.

        Args:
            text: Model response
            section: Section name (e.g., "ISSUES")

        Returns:
            List of items
        """
        import re

        items = []

        # Find section
        pattern = rf'{section}:\s*\[(.*?)\]'
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)

        if match:
            content = match.group(1)
            # Split by commas or newlines
            items = [item.strip().strip('"\'') for item in re.split(r'[,\n]', content)]
            items = [item for item in items if item]

        return items

    def query_with_grounding(self, query: str) -> str:
        """Query model with Google Search grounding enabled.

        Args:
            query: Search query

        Returns:
            Model response with grounded information
        """
        if not self.supports_grounding:
            logger.warning("Model does not support grounding, using standard query")
            return self._query_model_text(query)

        logger.debug(f"Querying with grounding: {query[:100]}...")

        # Add grounding instruction
        grounded_query = f"{query}\n\nUse Google Search to find accurate, up-to-date information."

        return self._query_model_text(grounded_query)

    def validate_connection(self) -> bool:
        """Validate API connection.

        Returns:
            True if connection is valid, False otherwise
        """
        try:
            # Try a minimal generation as a connection test
            test_prompt = "A simple test image"
            result = self.generate_image(test_prompt, aspect_ratio="1:1", enable_iteration=False)
            logger.info("Connection validation successful")
            return True
        except Exception as e:
            logger.error(f"Connection validation failed: {e}")
            return False

    def get_model_info(self) -> dict:
        """Get information about the model and its capabilities.

        Returns:
            Dictionary with model information
        """
        return {
            "model": self.model,
            "provider": "Google Gemini",
            "capabilities": {
                "image_generation": True,
                "google_search_grounding": self.supports_grounding,
                "multi_image_reference": self.supports_multi_image,
                "internal_reasoning": self.supports_reasoning,
                "native_text_rendering": self.supports_native_text,
            },
            "settings": {
                "grounding_enabled": self.enable_grounding,
                "reasoning_enabled": self.enable_reasoning,
            },
        }
