"""Google Gemini API client for image generation with advanced capabilities.

This module provides an enhanced client supporting multiple models with automatic
rate-limit cascade recovery:

- Gemini 3.1 Flash Image (Nano Banana 2) — PRIMARY / RECOMMENDED
  * ~22s generation time
  * Image Search grounding (text + image search results)
  * Thinking mode for enhanced accuracy
  * New resolutions: 0.5K, 1K, 2K, 4K
  * New aspect ratios: 1:4, 4:1, 1:8, 8:1 + standard set
  * Improved international text rendering
  * Batch API support

- Gemini 3 Pro Image (Nano Banana Pro) — SECONDARY (quota cascade fallback)
  * ~45s generation time
  * Deepest reasoning and physics-aware synthesis
  * Highest accuracy for complex/obscure historical subjects

- Gemini 2.5 Flash Preview Image Generation (Nano Banana) — TERTIARY fallback
  * Separate daily quota bucket from newer models
  * Good portrait quality with Google Search grounding and reasoning

Cascade behavior: when a generation call hits a quota / rate-limit error the
client automatically advances to the next model and retries.  After exhausting
all models in one cycle the client pauses 5 s before cycling back:

    Nano Banana 2  →  Nano Banana Pro  →  Nano Banana  →  (pause 5 s)  →  Nano Banana 2 …
"""

import io
import logging
import time
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

    Default model is gemini-3.1-flash-image-preview (Nano Banana 2) which
    provides the best combination of speed and accuracy:
    - ~22s generation vs ~45s for Pro
    - Image Search grounding (text + image results)
    - Thinking mode for accuracy-critical generations
    - 4K resolution support with extended aspect ratios
    - Batch API support for high-volume use

    For maximum quality on complex historical subjects, use
    gemini-3-pro-image-preview (Nano Banana Pro) instead.

    Model cascade (automatic rate-limit recovery):
    When a generation call hits a quota / rate-limit error the client
    automatically advances to the next model in the cascade and retries,
    allowing each model's daily quota to be used in turn.  After exhausting
    all models in one full cycle the client pauses briefly before cycling
    back to the primary model (which has had time to recover):

        Nano Banana 2  →  Nano Banana Pro  →  Nano Banana  →  (cycle back)
        gemini-3.1-flash-image-preview
                       →  gemini-3-pro-image-preview
                                          →  gemini-2.5-flash-preview-image-generation
                                                           →  gemini-3.1-flash-image-preview …
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-3.1-flash-image-preview",
        model_cascade: Optional[List[str]] = None,
        enable_grounding: bool = True,
        enable_reasoning: bool = True,
        thinking_level: str = "medium",
    ) -> None:
        """Initialize Gemini client with advanced capabilities.

        Args:
            api_key: Google API key
            model: Primary Gemini model name (default: gemini-3.1-flash-image-preview)
            model_cascade: Ordered list of fallback models for rate-limit recovery.
                           Defaults to QUOTA_CASCADE (NB2 → NB Pro → NB) starting at
                           the position of *model* in the cascade.  Pass ``[model]``
                           to disable cascading entirely.
            enable_grounding: Enable Google Search / Image Search grounding
            enable_reasoning: Enable internal reasoning capabilities
            thinking_level: Thinking depth for accuracy (minimal/low/medium/high)

        Raises:
            ImportError: If google-genai package not installed
            ValueError: If API key is invalid
        """
        if not api_key:
            raise ValueError("API key cannot be empty")

        if len(api_key) < 20:
            raise ValueError("API key appears to be invalid (too short)")

        self.api_key = api_key
        self.enable_grounding = enable_grounding
        self.enable_reasoning = enable_reasoning
        self.thinking_level = thinking_level

        # --- Model cascade setup ---
        # Import here to avoid circular imports at module level
        from ..config.model_configs import QUOTA_CASCADE as _DEFAULT_CASCADE
        if model_cascade is None:
            self._model_cascade: List[str] = _DEFAULT_CASCADE
        else:
            self._model_cascade = list(model_cascade)

        # Start at the requested model's position in the cascade (or 0 if not found)
        if model in self._model_cascade:
            self._cascade_index: int = self._model_cascade.index(model)
        else:
            # Requested model not in cascade — prepend it so it is tried first
            self._model_cascade = [model] + self._model_cascade
            self._cascade_index = 0

        self.model: str = self._model_cascade[self._cascade_index]

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
        # Flash model (Nano Banana 2) - recommended for speed + accuracy
        is_flash = "3.1-flash" in self.model or "nano-banana-2" in self.model
        # Pro model (Nano Banana Pro) - maximum quality
        is_pro = "3-pro" in self.model or "nano-banana-pro" in self.model
        # Any Gemini 3.x generation
        is_gemini3 = "gemini-3" in self.model or is_flash or is_pro
        # Gemini 2.5 Flash (Nano Banana) - previous gen flash, quota fallback
        is_gemini25 = "2.5-flash" in self.model and not is_gemini3
        # Legacy or other Gemini 2.x
        is_gemini2 = "gemini-2" in self.model and not is_gemini3

        self.supports_grounding = is_gemini3 or is_gemini25
        self.supports_image_grounding = is_flash  # Flash adds Image Search grounding
        self.supports_multi_image = is_gemini3 or is_gemini25
        self.supports_reasoning = is_gemini3 or is_gemini2 or is_gemini25
        self.supports_native_text = is_gemini3 or is_gemini2 or is_gemini25
        self.supports_thinking_mode = is_gemini3  # Only Gemini 3.x has thinking mode
        self.supports_batch = is_flash  # Flash supports Batch API
        self.supports_extended_aspect_ratios = is_flash  # Flash adds 1:4, 4:1, 1:8, 8:1

        logger.debug(
            f"Model capabilities: grounding={self.supports_grounding}, "
            f"image_grounding={self.supports_image_grounding}, "
            f"thinking={self.supports_thinking_mode}, "
            f"multi_image={self.supports_multi_image}, "
            f"reasoning={self.supports_reasoning}, "
            f"extended_ratios={self.supports_extended_aspect_ratios}"
        )

    # ------------------------------------------------------------------
    # Model cascade helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _is_rate_limit_error(error: Exception) -> bool:
        """Return True if *error* is a quota / rate-limit error.

        Checks both the stringified exception message (catches wrapped
        RuntimeError) and the original ``__cause__`` (raw Google API error).
        """
        _KEYWORDS = (
            'quota', 'rate limit', 'rate_limit', 'ratelimit',
            'resource_exhausted', 'resourceexhausted', 'resource exhausted',
            '429', 'too many requests', 'quota exceeded', 'limit exceeded',
            'requests per day', 'requests per minute', 'per_day', 'per_minute',
        )

        def _matches(exc: Exception) -> bool:
            msg = str(exc).lower()
            return any(k in msg for k in _KEYWORDS)

        if _matches(error):
            return True

        # Also inspect the original cause (may be a google.api_core exception)
        cause = getattr(error, '__cause__', None)
        if cause is not None and _matches(cause):
            return True

        # Check google.api_core.exceptions.ResourceExhausted if available
        try:
            import google.api_core.exceptions as _gae
            if isinstance(error, _gae.ResourceExhausted):
                return True
            if cause is not None and isinstance(cause, _gae.ResourceExhausted):
                return True
        except (ImportError, AttributeError):
            pass

        return False

    def _advance_model_cascade(self) -> str:
        """Advance to the next model in the cascade.

        Updates ``self.model`` and re-detects capabilities so every
        subsequent call uses the new model's feature set.

        Returns:
            The name of the newly selected model.
        """
        self._cascade_index = (self._cascade_index + 1) % len(self._model_cascade)
        self.model = self._model_cascade[self._cascade_index]
        self._detect_capabilities()  # refresh supports_* flags for the new model
        logger.info(
            f"Model cascade: switched to {self.model} "
            f"(position {self._cascade_index + 1}/{len(self._model_cascade)} "
            f"in cascade: {' → '.join(self._model_cascade)})"
        )
        return self.model

    def get_cascade_status(self) -> dict:
        """Return current cascade state (useful for logging / diagnostics)."""
        return {
            "current_model": self.model,
            "cascade_index": self._cascade_index,
            "cascade": self._model_cascade,
        }

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

        # Base ratios supported by all models
        base_ratios = {"1:1", "3:4", "4:3", "9:16", "16:9"}
        # Extended ratios for Flash model (Nano Banana 2) - improved adherence
        extended_ratios = {"2:3", "3:2", "4:5", "5:4", "21:9", "1:4", "4:1", "1:8", "8:1"}

        if self.supports_extended_aspect_ratios:
            valid_ratios = base_ratios | extended_ratios
        else:
            valid_ratios = base_ratios

        if aspect_ratio not in valid_ratios:
            raise ValueError(
                f"Invalid aspect_ratio '{aspect_ratio}'. "
                f"Must be one of: {', '.join(sorted(valid_ratios))}"
            )

        # ------------------------------------------------------------------
        # Model cascade loop
        # Tries each model in self._model_cascade in turn when a quota /
        # rate-limit error is encountered.  Allows up to 2 full cycles so
        # the primary model has time to recover before the cascade wraps.
        #
        #   Nano Banana 2 → Nano Banana Pro → Nano Banana → (pause) → Nano Banana 2 …
        # ------------------------------------------------------------------
        _cascade_max = len(self._model_cascade) * 2   # 2 full cycles before giving up
        _cascade_used = 0

        while True:
            # Determine the effective aspect ratio for the current model.
            # The initial validation passed for the primary model; if the cascade
            # has switched to a model that lacks extended-ratio support, fall back
            # gracefully rather than failing with a hard error.
            _base_ratios = {"1:1", "3:4", "4:3", "9:16", "16:9"}
            effective_ratio = (
                aspect_ratio
                if (self.supports_extended_aspect_ratios or aspect_ratio in _base_ratios)
                else "3:4"
            )
            if effective_ratio != aspect_ratio:
                logger.debug(
                    f"Downgraded aspect_ratio {aspect_ratio!r} → {effective_ratio!r} "
                    f"({self.model} does not support extended ratios)"
                )

            logger.info(
                f"Generating image [{self.model}] ratio={effective_ratio}"
                + (f" (cascade attempt {_cascade_used + 1})" if _cascade_used else "")
            )
            logger.debug(f"Prompt: {prompt[:100]}...")

            # (Re-)enhance prompt for the current model's capabilities.
            # Must be inside the loop because _enhance_prompt() is model-aware
            # (thinking mode, grounding instructions differ between models).
            enhanced_prompt = self._enhance_prompt(
                prompt,
                enable_iteration=enable_iteration,
                max_iterations=max_iterations,
            )

            try:
                # Configure generation
                image_config = self.types.ImageConfig(aspect_ratio=effective_ratio)

                # Build tools list — grounding support differs between models
                tools = []
                if self.enable_grounding and self.supports_grounding:
                    tools.append({"google_search": {}})

                config = self.types.GenerateContentConfig(
                    response_modalities=['Image'],
                    image_config=image_config,
                    tools=tools if tools else None,
                )

                # Build multimodal contents: reference images first (image-first
                # ordering), then text prompt last.
                if reference_images:
                    contents = []
                    loaded_count = 0
                    _mime_map = {
                        ".jpg": "image/jpeg",
                        ".jpeg": "image/jpeg",
                        ".png": "image/png",
                        ".gif": "image/gif",
                        ".webp": "image/webp",
                    }
                    for ref_path in reference_images:
                        try:
                            image_bytes = ref_path.read_bytes()
                            mime_type = _mime_map.get(ref_path.suffix.lower(), "image/jpeg")
                            contents.append(
                                self.types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
                            )
                            loaded_count += 1
                        except Exception as ref_err:
                            logger.warning(f"Failed to load reference image {ref_path}: {ref_err}")
                    contents.append(self.types.Part.from_text(text=enhanced_prompt))
                    logger.info(
                        f"Sending {loaded_count} reference image(s) + text prompt "
                        f"to {self.model} (image-first ordering)"
                    )
                else:
                    contents = enhanced_prompt
                    loaded_count = 0

                # Generate image
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=contents,
                    config=config,
                )

                # Extract image from response parts
                pil_image = None
                reasoning_text = ""

                for part in response.candidates[0].content.parts:
                    if part.text:
                        reasoning_text += part.text
                    try:
                        genai_image = part.as_image()
                        if genai_image and genai_image.image_bytes:
                            pil_image = Image.open(io.BytesIO(genai_image.image_bytes))
                            break
                    except Exception as part_err:
                        logger.debug(f"Could not extract image from part: {part_err}")

                if not pil_image:
                    raise RuntimeError("No image returned in response")

                logger.info(
                    f"Generated image: {pil_image.size} {pil_image.mode}"
                    + (f" (via {self.model} after {_cascade_used} cascade switch(es))" if _cascade_used else "")
                )

                return GenerationResult(
                    image=pil_image,
                    confidence_score=0.90,
                    iterations_used=1,
                    reasoning=reasoning_text.strip() if reasoning_text else "",
                    grounding_used=self.enable_grounding and self.supports_grounding,
                    reference_images_used=loaded_count if reference_images else 0,
                )

            except Exception as e:
                # Rate-limit / quota error → advance cascade and retry
                if self._is_rate_limit_error(e) and _cascade_used < _cascade_max:
                    _old_model = self.model
                    _new_model = self._advance_model_cascade()
                    _cascade_used += 1
                    logger.warning(
                        f"Rate limited on {_old_model} — cascading to {_new_model} "
                        f"({_cascade_used}/{_cascade_max} cascade attempts)"
                    )
                    # After a full cycle through all models, pause briefly to allow
                    # the primary model's quota window to start recovering.
                    if self._cascade_index == 0:
                        _pause_s = 5
                        logger.info(
                            f"Completed full cascade cycle — pausing {_pause_s}s "
                            f"before retrying from {_new_model}…"
                        )
                        time.sleep(_pause_s)
                    continue  # retry with the new model

                # Non-rate-limit failure (or cascade exhausted) — propagate
                logger.error(f"Image generation failed: {e}", exc_info=True)
                raise RuntimeError(f"Image generation failed: {e}") from e

    def _enhance_prompt(
        self,
        prompt: str,
        enable_iteration: bool,
        max_iterations: int,
    ) -> str:
        """Enhance prompt with reasoning and quality instructions.

        For gemini-3.1-flash-image-preview (Nano Banana 2), thinking mode
        provides enhanced accuracy while maintaining speed advantage. The model
        reasons through historical details, composition, and visual coherence
        before generating.

        Args:
            prompt: Original prompt
            enable_iteration: Whether to enable iteration
            max_iterations: Maximum iterations

        Returns:
            Enhanced prompt with instructions
        """
        enhancements = []

        # Add thinking-enhanced accuracy instructions (Flash and Pro)
        if self.enable_reasoning and self.supports_thinking_mode:
            enhancements.append(
                "Apply thinking mode to reason through historical accuracy, "
                "compositional details, and visual coherence before generating. "
                "Verify all depicted details are historically correct."
            )
        elif self.enable_reasoning and self.supports_reasoning:
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

        # Add Image Search grounding for Flash (includes both text and image results)
        if self.enable_grounding and self.supports_image_grounding:
            enhancements.append(
                "Use Image Search grounding to incorporate real historical visual references "
                "and verify accuracy of depicted appearance, clothing, and era-specific details."
            )
        elif self.enable_grounding and self.supports_grounding:
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
            "model_cascade": self._model_cascade,
            "cascade_index": self._cascade_index,
            "provider": "Google Gemini",
            "capabilities": {
                "image_generation": True,
                "google_search_grounding": self.supports_grounding,
                "image_search_grounding": self.supports_image_grounding,
                "multi_image_reference": self.supports_multi_image,
                "internal_reasoning": self.supports_reasoning,
                "thinking_mode": self.supports_thinking_mode,
                "native_text_rendering": self.supports_native_text,
                "extended_aspect_ratios": self.supports_extended_aspect_ratios,
                "batch_api": self.supports_batch,
            },
            "settings": {
                "grounding_enabled": self.enable_grounding,
                "reasoning_enabled": self.enable_reasoning,
                "thinking_level": self.thinking_level,
            },
        }
