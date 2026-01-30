"""Portrait generator module - main orchestrator."""

import logging
import time
from pathlib import Path
from typing import Dict, List, Optional

from PIL import Image

from ..api.models import PortraitResult, SubjectData, EvaluationResult
from ..utils.image_utils import convert_to_bw, convert_to_sepia
from .researcher import BiographicalResearcher
from .overlay import TitleOverlayEngine
from .evaluator import QualityEvaluator

logger = logging.getLogger(__name__)


class PortraitGenerator:
    """
    Main portrait generation orchestrator.

    Coordinates research, image generation, overlay application,
    and quality evaluation to produce complete portrait sets.
    """

    STYLES = ["BW", "Sepia", "Color", "Painting"]

    def __init__(
        self,
        gemini_client,
        researcher: BiographicalResearcher,
        overlay_engine: TitleOverlayEngine,
        evaluator: QualityEvaluator,
        output_dir: Path,
    ):
        """
        Initialize PortraitGenerator.

        Args:
            gemini_client: GeminiImageClient for image generation
            researcher: BiographicalResearcher instance
            overlay_engine: TitleOverlayEngine instance
            evaluator: QualityEvaluator instance
            output_dir: Directory for output files
        """
        self.gemini_client = gemini_client
        self.researcher = researcher
        self.overlay_engine = overlay_engine
        self.evaluator = evaluator
        self.output_dir = Path(output_dir)

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initialized PortraitGenerator with output_dir={output_dir}")

    def generate_portrait(
        self,
        subject_name: str,
        force_regenerate: bool = False,
        styles: Optional[List[str]] = None,
    ) -> PortraitResult:
        """
        Generate portrait(s) for a subject.

        Args:
            subject_name: Full name of subject
            force_regenerate: If True, regenerate even if files exist
            styles: List of styles to generate (defaults to all 4)

        Returns:
            PortraitResult with all generated files and evaluations

        Raises:
            ValueError: If subject_name is invalid
            RuntimeError: If generation fails
        """
        if not subject_name or not subject_name.strip():
            raise ValueError("Subject name cannot be empty")

        if styles is None:
            styles = self.STYLES.copy()
        else:
            # Validate styles
            invalid = set(styles) - set(self.STYLES)
            if invalid:
                raise ValueError(f"Invalid styles: {invalid}")

        logger.info(f"=== Generating portraits for: {subject_name} ===")
        logger.info(f"Styles: {styles}")

        start_time = time.time()
        errors = []

        try:
            # Step 1: Research subject
            logger.info("Step 1: Researching subject...")
            subject_data = self.researcher.research_subject(subject_name)
            logger.info(
                f"Research complete: {subject_data.name} ({subject_data.formatted_years})"
            )

            # Step 2: Generate portraits for each style
            files = {}
            prompts = {}
            evaluations = {}

            for style in styles:
                try:
                    logger.info(f"Step 2.{styles.index(style) + 1}: Generating {style} portrait...")

                    # Generate portrait
                    file_path, prompt_path = self._generate_version(
                        subject_data, style, force_regenerate
                    )

                    files[style] = str(file_path)
                    prompts[style] = str(prompt_path)

                    # Step 3: Evaluate
                    logger.info(f"Step 3.{styles.index(style) + 1}: Evaluating {style} portrait...")

                    image = Image.open(file_path)
                    evaluation = self.evaluator.evaluate_portrait(
                        image, subject_data, style
                    )
                    evaluations[style] = evaluation

                    status = "PASSED" if evaluation.passed else "FAILED"
                    logger.info(
                        f"{style} evaluation: {status} "
                        f"(score: {evaluation.overall_score:.2f})"
                    )

                except Exception as e:
                    error_msg = f"Failed to generate {style} portrait: {e}"
                    logger.error(error_msg, exc_info=True)
                    errors.append(error_msg)

                    # Add failed evaluation
                    evaluations[style] = EvaluationResult(
                        passed=False,
                        scores={},
                        feedback=[],
                        issues=[error_msg],
                        recommendations=["Retry generation"],
                    )

            # Calculate total time
            generation_time = time.time() - start_time

            # Determine overall success
            success = len(files) > 0 and len(errors) == 0

            logger.info(f"=== Generation complete in {generation_time:.1f}s ===")
            logger.info(f"Success: {success}, Files: {len(files)}, Errors: {len(errors)}")

            return PortraitResult(
                subject=subject_name,
                files=files,
                prompts=prompts,
                metadata=subject_data,
                evaluation=evaluations,
                generation_time_seconds=generation_time,
                success=success,
                errors=errors,
            )

        except Exception as e:
            error_msg = f"Portrait generation failed: {e}"
            logger.error(error_msg, exc_info=True)

            return PortraitResult(
                subject=subject_name,
                files={},
                prompts={},
                metadata=SubjectData(
                    name=subject_name,
                    birth_year=0,
                    death_year=None,
                    era="Unknown",
                ),
                evaluation={},
                generation_time_seconds=time.time() - start_time,
                success=False,
                errors=[error_msg],
            )

    def _generate_version(
        self,
        subject_data: SubjectData,
        style: str,
        force_regenerate: bool = False,
    ) -> tuple[Path, Path]:
        """
        Generate a single portrait version.

        Args:
            subject_data: Subject biographical data
            style: Portrait style
            force_regenerate: Force regeneration even if exists

        Returns:
            Tuple of (image_path, prompt_path)

        Raises:
            RuntimeError: If generation fails
        """
        # Create filename
        filename_base = self._create_filename(subject_data.name, style)
        image_path = self.output_dir / f"{filename_base}.png"
        prompt_path = self.output_dir / f"{filename_base}_prompt.md"

        # Check if already exists
        if not force_regenerate and image_path.exists():
            logger.info(f"File exists: {image_path}")
            return image_path, prompt_path

        try:
            # Create prompt
            prompt = self._create_prompt(subject_data, style)

            # Save prompt
            prompt_path.write_text(prompt, encoding="utf-8")
            logger.debug(f"Saved prompt: {prompt_path}")

            # Generate base image
            logger.info(f"Generating {style} image...")
            base_image = self.gemini_client.generate_image(
                prompt=prompt, aspect_ratio="3:4"
            )

            # Apply style transformations if needed
            if style in ["BW", "Sepia"]:
                styled_image = self._apply_style_transformation(base_image, style)
            else:
                styled_image = base_image

            # Add overlay
            logger.debug("Adding title overlay...")
            final_image = self.overlay_engine.add_overlay(
                styled_image,
                name=subject_data.name,
                years=subject_data.formatted_years,
            )

            # Save image
            final_image.save(image_path, "PNG", quality=95)
            logger.info(f"Saved image: {image_path}")

            return image_path, prompt_path

        except Exception as e:
            logger.error(f"Failed to generate {style} version: {e}", exc_info=True)
            raise RuntimeError(f"Failed to generate {style} version: {e}") from e

    def _create_prompt(self, subject_data: SubjectData, style: str) -> str:
        """
        Create image generation prompt for style.

        Args:
            subject_data: Subject biographical data
            style: Portrait style

        Returns:
            Image generation prompt
        """
        # Get prompt context
        context = self.researcher.get_prompt_context(subject_data)

        # Style-specific instructions
        style_instructions = self._get_style_instructions(style)

        # Build prompt
        prompt = f"""Generate a {style} portrait of {context['name']}.

SUBJECT DETAILS:
- Era: {context['era']}
- Years: {context['years']}
- Historical Context: {context['context']}
"""

        if context['appearance']:
            prompt += f"- Physical Appearance: {context['appearance']}\n"

        prompt += f"""
COMPOSITION:
- Extreme close-up portrait, head and shoulders only
- Face fills 80-90% of frame
- Vertical aspect ratio (3:4)
- Subject looking directly at viewer or slight three-quarter view
- Minimal background, period-appropriate setting

STYLE: {style_instructions}

QUALITY REQUIREMENTS:
- Publication-grade quality
- Historically accurate clothing and hairstyle for {context['era']}
- Professional lighting showing facial features clearly
- No text, watermarks, or borders in the image
- High detail in facial features and textures
- Photorealistic rendering (or painterly for Painting style)

Create a dignified, historically accurate portrait suitable for academic use.
"""

        logger.debug(f"Created prompt for {style}: {len(prompt)} chars")

        return prompt

    def _get_style_instructions(self, style: str) -> str:
        """
        Get style-specific instructions for prompt.

        Args:
            style: Portrait style

        Returns:
            Style instructions string
        """
        instructions = {
            "BW": """Classic black and white portrait photography. Deep contrast with
dramatic lighting. Rich tonal range from deep blacks to bright highlights.
Sharp focus. Reminiscent of classic portrait masters like Yousuf Karsh.""",
            "Sepia": """Warm sepia tone photograph with vintage aesthetic. Rich brown
tones throughout. Soft focus on edges with sharp central detail. Classic
early photography style from late 1800s/early 1900s.""",
            "Color": """Full color photorealistic portrait. Natural, accurate skin
tones and hair color appropriate for the era. Contemporary professional
photography style with natural lighting. Rich, lifelike colors.""",
            "Painting": """Hyper-detailed oil painting on canvas. Visible brushstrokes
adding texture and depth. Classical portrait painting technique similar to
John Singer Sargent or modern hyperrealist portraiture. Rich, layered colors
with painterly quality while maintaining photographic detail.""",
        }

        return instructions.get(style, "Photorealistic portrait")

    def _apply_style_transformation(
        self, image: Image.Image, style: str
    ) -> Image.Image:
        """
        Apply style-specific transformations to image.

        Args:
            image: Base PIL Image
            style: Style to apply

        Returns:
            Transformed PIL Image
        """
        if style == "BW":
            logger.debug("Applying BW transformation...")
            return convert_to_bw(image, enhance_contrast=1.2)

        elif style == "Sepia":
            logger.debug("Applying Sepia transformation...")
            return convert_to_sepia(image, intensity=1.0)

        else:
            # No transformation needed for Color or Painting
            return image

    def _create_filename(self, name: str, style: str) -> str:
        """
        Create filename from subject name and style.

        Args:
            name: Subject name
            style: Portrait style

        Returns:
            Filename (without extension)
        """
        # Remove spaces and special characters
        clean_name = "".join(c for c in name if c.isalnum() or c.isspace())

        # Convert to PascalCase
        parts = clean_name.split()
        filename = "".join(word.capitalize() for word in parts)

        # Add style suffix
        filename = f"{filename}_{style}"

        logger.debug(f"Created filename: {filename}")

        return filename

    def check_existing_portraits(self, subject_name: str) -> Dict[str, bool]:
        """
        Check which portraits already exist for a subject.

        Args:
            subject_name: Subject name

        Returns:
            Dictionary of style -> exists (bool)
        """
        results = {}

        for style in self.STYLES:
            filename = self._create_filename(subject_name, style)
            image_path = self.output_dir / f"{filename}.png"
            results[style] = image_path.exists()

        logger.debug(f"Existing portraits for {subject_name}: {results}")

        return results

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
            force_regenerate: Force regeneration even if exists
            styles: List of styles to generate

        Returns:
            List of PortraitResult objects
        """
        if not subject_names:
            raise ValueError("Subject names list cannot be empty")

        logger.info(f"=== Starting batch generation: {len(subject_names)} subjects ===")

        results = []

        for i, name in enumerate(subject_names, 1):
            logger.info(f"[{i}/{len(subject_names)}] Processing: {name}")

            try:
                result = self.generate_portrait(
                    name, force_regenerate=force_regenerate, styles=styles
                )
                results.append(result)

                status = "SUCCESS" if result.success else "FAILED"
                logger.info(f"[{i}/{len(subject_names)}] {name}: {status}")

            except Exception as e:
                logger.error(f"[{i}/{len(subject_names)}] {name}: ERROR - {e}")
                results.append(
                    PortraitResult(
                        subject=name,
                        files={},
                        prompts={},
                        metadata=SubjectData(
                            name=name, birth_year=0, death_year=None, era="Unknown"
                        ),
                        evaluation={},
                        generation_time_seconds=0.0,
                        success=False,
                        errors=[str(e)],
                    )
                )

        success_count = sum(1 for r in results if r.success)
        logger.info(
            f"=== Batch complete: {success_count}/{len(results)} successful ==="
        )

        return results
