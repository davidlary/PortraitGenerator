"""Intelligent prompt builder for Gemini 3 Pro Image.

This module builds advanced prompts that leverage reference images,
native text rendering, and physics-aware synthesis instructions.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Any

from .api.models import SubjectData
from .reference_finder import ReferenceImage

logger = logging.getLogger(__name__)


@dataclass
class PromptContext:
    """Context for prompt building."""

    subject_data: SubjectData
    """Subject biographical information"""

    style: str
    """Portrait style (BW, Sepia, Color, Painting)"""

    reference_images: List[ReferenceImage]
    """Reference images to guide generation"""

    use_native_text: bool = True
    """Use model's native text rendering"""

    enable_physics_aware: bool = True
    """Enable physics-aware synthesis instructions"""

    enable_fact_checking: bool = True
    """Include fact-checking instructions"""


class PromptBuilder:
    """Builds intelligent prompts for Gemini 3 Pro Image generation.

    Creates prompts that:
    - Leverage reference images for authenticity
    - Use native LLM-based text rendering
    - Include physics-aware synthesis instructions
    - Incorporate fact-checking guidance
    """

    def __init__(
        self,
        model_profile=None,
    ):
        """Initialize prompt builder.

        Args:
            model_profile: Model profile from model_configs (optional)
        """
        self.model_profile = model_profile
        logger.debug("Initialized PromptBuilder")

    def build_prompt(
        self,
        context: PromptContext,
    ) -> str:
        """Build complete generation prompt.

        Args:
            context: Prompt context with all information

        Returns:
            Complete prompt for image generation
        """
        logger.info(
            f"Building prompt for {context.subject_data.name} "
            f"({context.style}, {len(context.reference_images)} refs)"
        )

        sections = []

        # 1. Core subject description
        sections.append(self._build_subject_section(context))

        # 2. Reference image guidance
        if context.reference_images:
            sections.append(self._build_reference_section(context))

        # 3. Composition instructions
        sections.append(self._build_composition_section(context))

        # 4. Style instructions
        sections.append(self._build_style_section(context))

        # 5. Text rendering instructions (if native text enabled)
        if context.use_native_text:
            sections.append(self._build_text_rendering_section(context))

        # 6. Quality and technical requirements
        sections.append(self._build_quality_section(context))

        # 7. Physics-aware synthesis instructions
        if context.enable_physics_aware:
            sections.append(self._build_physics_section(context))

        # 8. Fact-checking instructions
        if context.enable_fact_checking:
            sections.append(self._build_fact_checking_section(context))

        # 9. Final directives
        sections.append(self._build_final_directives(context))

        # Assemble prompt
        prompt = "\n\n".join(sections)

        logger.debug(f"Built prompt: {len(prompt)} chars")

        return prompt

    def _build_subject_section(self, context: PromptContext) -> str:
        """Build subject description section.

        Args:
            context: Prompt context

        Returns:
            Subject section text
        """
        data = context.subject_data

        section = f"""Generate a historically accurate {context.style} portrait of {data.name}.

SUBJECT INFORMATION:
- Full Name: {data.name}
- Historical Era: {data.era}
- Lifespan: {data.formatted_years}
- Birth Year: {data.birth_year}"""

        if data.death_year:
            section += f"\n- Death Year: {data.death_year}"

        # Add appearance details if available
        if hasattr(data, 'appearance_details') and data.appearance_details:
            section += f"\n- Physical Appearance: {data.appearance_details}"

        # Add historical context if available
        if hasattr(data, 'historical_context') and data.historical_context:
            section += f"\n- Historical Context: {data.historical_context}"

        return section

    def _build_reference_section(self, context: PromptContext) -> str:
        """Build reference images section.

        Args:
            context: Prompt context

        Returns:
            Reference section text
        """
        if not context.reference_images:
            return ""

        section = f"""REFERENCE IMAGES:
You have access to {len(context.reference_images)} authenticated historical reference images of {context.subject_data.name}.

Use these references to ensure:
1. Facial features and proportions match historical photographs
2. Hairstyle and grooming are era-appropriate
3. Clothing and accessories reflect the time period
4. Overall appearance is authentic and verifiable

Reference image sources:"""

        for i, ref in enumerate(context.reference_images[:5], 1):
            section += f"\n  {i}. {ref.source} (authenticity: {ref.authenticity_score:.0%})"

        section += "\n\nSynthesize details from these references to create an accurate composite."

        return section

    def _build_composition_section(self, context: PromptContext) -> str:
        """Build composition instructions.

        Args:
            context: Prompt context

        Returns:
            Composition section text
        """
        return """COMPOSITION REQUIREMENTS:
- Vertical portrait format (3:4 aspect ratio)
- Extreme close-up: head and upper shoulders fill frame
- Face occupies 80-90% of total image area
- Subject looking directly at viewer OR slight three-quarter turn
- Eyes at approximately upper third of frame
- Minimal background: simple, period-appropriate setting
- Professional studio lighting with clear facial detail
- Sharp focus on eyes and facial features"""

    def _build_style_section(self, context: PromptContext) -> str:
        """Build style-specific instructions.

        Args:
            context: Prompt context

        Returns:
            Style section text
        """
        style_instructions = {
            "BW": """STYLE: Black & White Portrait
- Classic monochrome photography aesthetic
- Rich tonal range from deep blacks to bright highlights
- Enhanced contrast with dramatic lighting
- Sharp focus with crisp detail
- Reminiscent of Yousuf Karsh's portrait mastery
- No color information whatsoever
- Deep shadows balanced with illuminated highlights""",

            "Sepia": """STYLE: Sepia Tone Vintage Portrait
- Warm brown sepia tones throughout
- Vintage early photography aesthetic (1890s-1920s)
- Soft focus on edges, sharp central detail
- Warm, nostalgic color palette
- Classic archival photograph appearance
- Subtle grain matching period photography
- Gentle vignetting at edges""",

            "Color": """STYLE: Full Color Photorealistic Portrait
- Contemporary professional color photography
- Natural, accurate skin tones for the era
- Realistic hair color and eye color
- Balanced color temperature
- Natural lighting with rich, lifelike colors
- Sharp, modern photographic clarity
- No color grading or filters
- True-to-life color reproduction""",

            "Painting": """STYLE: Hyperrealistic Oil Painting Portrait
- Classical oil painting technique on canvas
- Visible brushstrokes adding texture and depth
- Similar to John Singer Sargent or modern hyperrealist artists
- Rich, layered colors with painterly quality
- Maintains photographic detail level
- Subtle impasto texture visible
- Traditional portrait painting composition
- Artistic interpretation while maintaining accuracy""",
        }

        return style_instructions.get(
            context.style,
            f"STYLE: {context.style} portrait with photorealistic quality"
        )

    def _build_text_rendering_section(self, context: PromptContext) -> str:
        """Build native text rendering instructions.

        Args:
            context: Prompt context

        Returns:
            Text rendering section
        """
        data = context.subject_data

        return f"""TEXT RENDERING (NATIVE LLM-BASED):
DO NOT include any text, labels, watermarks, or borders in the portrait image itself.
The image should be pure portrait with no overlaid text.

The following text will be added programmatically after generation:
- Name: {data.name}
- Years: {data.formatted_years}

Your task is ONLY to generate the portrait image without any text elements."""

    def _build_quality_section(self, context: PromptContext) -> str:
        """Build quality requirements section.

        Args:
            context: Prompt context

        Returns:
            Quality section text
        """
        return f"""QUALITY REQUIREMENTS:
- Publication-grade professional quality
- High resolution and detail clarity
- Historically accurate clothing and hairstyle for {context.subject_data.era}
- Period-appropriate grooming and accessories
- Professional lighting showing facial features clearly
- No anachronistic elements (modern clothing, styles, etc.)
- No text, watermarks, signatures, or borders
- No digital artifacts or distortions
- Photorealistic rendering (or painterly for Painting style)
- Suitable for academic and educational use"""

    def _build_physics_section(self, context: PromptContext) -> str:
        """Build physics-aware synthesis instructions.

        Args:
            context: Prompt context

        Returns:
            Physics section text
        """
        return """PHYSICS-AWARE SYNTHESIS:
Ensure visual coherence with physically accurate rendering:

LIGHTING & SHADOWS:
- Light sources must be consistent and physically plausible
- Shadows must match light direction and intensity
- Subsurface scattering for realistic skin rendering
- Specular highlights appropriate for materials (skin, hair, fabric)

PROPORTIONS & ANATOMY:
- Anatomically correct facial proportions
- Realistic bone structure and musculature
- Age-appropriate skin texture and features
- Proper eye placement and symmetry
- Natural hair growth patterns and physics

MATERIALS & TEXTURES:
- Fabric drape and fold following gravity
- Hair with natural volume and flow
- Skin with appropriate pore detail and texture
- Proper material reflectance (matte vs glossy)

DEPTH & PERSPECTIVE:
- Correct depth of field for portrait distance
- Proper perspective with no distortions
- Realistic bokeh if background is out of focus
- Natural atmospheric depth"""

    def _build_fact_checking_section(self, context: PromptContext) -> str:
        """Build fact-checking instructions.

        Args:
            context: Prompt context

        Returns:
            Fact-checking section text
        """
        data = context.subject_data

        return f"""FACT-CHECKING REQUIREMENTS:
Use Google Search grounding to verify:

1. Historical accuracy of {data.name}'s appearance
2. Appropriate clothing styles for {data.era}
3. Hairstyles and grooming conventions of the period
4. Cultural and regional context for {data.birth_year}
5. Any known photographic references

Cross-reference multiple sources to ensure:
- No anachronisms in clothing, hairstyle, or accessories
- Era-appropriate technology and materials in visible items
- Historically accurate representation
- Culturally sensitive depiction

If uncertain about specific details, favor historically documented conventions
of the {data.era} rather than modern interpretations."""

    def _build_final_directives(self, context: PromptContext) -> str:
        """Build final generation directives.

        Args:
            context: Prompt context

        Returns:
            Final directives text
        """
        return f"""FINAL DIRECTIVES:
Create a dignified, respectful portrait of {context.subject_data.name} that:
- Honors their historical significance
- Maintains academic and educational standards
- Provides clear visual reference suitable for biography or textbook
- Balances artistic merit with documentary accuracy
- Captures the character and gravitas appropriate to their achievements

Generate a portrait that would be proudly displayed in a museum, university,
or historical archive."""

    def build_simple_prompt(
        self,
        subject_data: SubjectData,
        style: str,
    ) -> str:
        """Build a simple prompt without advanced features.

        For backward compatibility with older models.

        Args:
            subject_data: Subject information
            style: Portrait style

        Returns:
            Simple prompt string
        """
        context = PromptContext(
            subject_data=subject_data,
            style=style,
            reference_images=[],
            use_native_text=False,
            enable_physics_aware=False,
            enable_fact_checking=False,
        )

        # Build minimal prompt
        sections = [
            f"Generate a {style} portrait of {subject_data.name}.",
            f"Era: {subject_data.era}",
            f"Years: {subject_data.formatted_years}",
            self._build_composition_section(context),
            self._build_style_section(context),
            self._build_quality_section(context),
        ]

        return "\n\n".join(sections)

    def enhance_prompt_with_reasoning(
        self,
        base_prompt: str,
        enable_iteration: bool = True,
        max_iterations: int = 3,
    ) -> str:
        """Enhance prompt with reasoning instructions.

        Args:
            base_prompt: Base prompt to enhance
            enable_iteration: Enable iterative refinement
            max_iterations: Maximum iterations

        Returns:
            Enhanced prompt with reasoning instructions
        """
        enhancements = []

        enhancements.append("""
INTERNAL REASONING:
Before generating the final image, use your internal reasoning to:
1. Analyze the subject's historical context
2. Verify accuracy of all visual elements
3. Plan the composition and lighting
4. Consider era-appropriate details
5. Ensure no anachronisms are present""")

        if enable_iteration and max_iterations > 1:
            enhancements.append(f"""
ITERATIVE REFINEMENT:
Perform up to {max_iterations} internal iterations:
1. Generate initial composition
2. Self-evaluate for accuracy and quality
3. Refine details that don't meet standards
4. Verify historical authenticity
5. Finalize only when quality is optimal""")

        enhancements.append("""
QUALITY CHECKS:
Self-assess the generated image for:
- Historical accuracy (no anachronisms)
- Visual coherence (physics-aware rendering)
- Technical quality (resolution, clarity, lighting)
- Compositional balance
- Style adherence

Only output the final image when all quality criteria are met.""")

        enhanced = base_prompt + "\n\n" + "\n".join(enhancements)

        return enhanced
