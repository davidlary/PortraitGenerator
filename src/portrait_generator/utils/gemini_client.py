"""Google Gemini API client for image generation."""

import io
import logging
from typing import Optional

from PIL import Image

logger = logging.getLogger(__name__)


class GeminiImageClient:
    """
    Client for Google Gemini image generation API.

    Uses the Gemini experimental image generation model for creating
    portrait images.
    """

    def __init__(self, api_key: str, model: str = "gemini-exp-1206") -> None:
        """
        Initialize Gemini client.

        Args:
            api_key: Google API key
            model: Gemini model name for image generation

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

        try:
            import google.genai as genai
            from google.genai import types

            self.genai = genai
            self.types = types
            self.client = genai.Client(api_key=api_key)
            logger.info(f"Initialized Gemini client with model: {model}")
        except ImportError as e:
            raise ImportError(
                "google-genai package not installed. "
                "Install with: pip install google-genai"
            ) from e

    def generate_image(
        self,
        prompt: str,
        aspect_ratio: str = "3:4",
        safety_settings: Optional[dict] = None,
    ) -> Image.Image:
        """
        Generate image using Gemini.

        Args:
            prompt: Text prompt for image generation
            aspect_ratio: Aspect ratio (e.g., "3:4", "4:3", "1:1")
            safety_settings: Optional safety settings

        Returns:
            PIL Image object

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

        try:
            # Configure generation
            config = self.types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio=aspect_ratio,
            )

            # Add safety settings if provided
            if safety_settings:
                config.safety_filter_level = safety_settings.get(
                    "filter_level", "block_some"
                )

            # Generate image
            response = self.client.models.generate_images(
                model=self.model,
                prompt=prompt,
                config=config,
            )

            if not response.generated_images:
                raise RuntimeError("No images returned in response")

            # Extract image bytes
            image_bytes = response.generated_images[0].image.image_bytes

            # Convert to PIL Image
            image = Image.open(io.BytesIO(image_bytes))

            logger.info(f"Generated image: {image.size} {image.mode}")

            return image

        except Exception as e:
            logger.error(f"Image generation failed: {e}", exc_info=True)
            raise RuntimeError(f"Image generation failed: {e}") from e

    def validate_connection(self) -> bool:
        """
        Validate API connection.

        Returns:
            True if connection is valid, False otherwise
        """
        try:
            # Try a minimal generation as a connection test
            test_prompt = "A simple test image"
            self.generate_image(test_prompt, aspect_ratio="1:1")
            logger.info("Connection validation successful")
            return True
        except Exception as e:
            logger.error(f"Connection validation failed: {e}")
            return False

    def get_model_info(self) -> dict:
        """
        Get information about the model.

        Returns:
            Dictionary with model information
        """
        return {
            "model": self.model,
            "provider": "Google Gemini",
            "capabilities": ["image_generation"],
        }
