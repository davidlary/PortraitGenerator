"""API request and response models."""

from typing import Dict, List, Literal, Optional
from pathlib import Path

from pydantic import BaseModel, Field, field_validator

from ..lifespan import format_year


class PortraitRequest(BaseModel):
    """Request model for portrait generation."""

    subject_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Full name of the subject",
        examples=["Albert Einstein", "Marie Curie"],
    )
    force_regenerate: bool = Field(
        default=False,
        description="Regenerate even if files exist",
    )
    styles: Optional[List[str]] = Field(
        default=None,
        description="Specific styles to generate (defaults to all 4)",
        examples=[["BW", "Sepia"], ["Color", "Painting"]],
    )

    @field_validator("styles")
    @classmethod
    def validate_styles(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate style list."""
        if v is not None:
            valid_styles = {"BW", "Sepia", "Color", "Painting"}
            invalid = set(v) - valid_styles
            if invalid:
                raise ValueError(
                    f"Invalid styles: {invalid}. "
                    f"Must be from: {valid_styles}"
                )
        return v


class SubjectData(BaseModel):
    """Biographical data for a subject."""

    name: str = Field(..., description="Subject's full name")
    birth_year: int = Field(..., description="Year of birth")
    death_year: Optional[int] = Field(
        default=None,
        description="Year of death (None if still alive)",
    )
    era: str = Field(..., description="Historical era")
    appearance_notes: List[str] = Field(
        default_factory=list,
        description="Physical appearance details",
    )
    historical_context: str = Field(
        default="",
        description="Historical context",
    )
    reference_sources: List[str] = Field(
        default_factory=list,
        description="Reference sources used",
    )
    gender: str = Field(
        default="unknown",
        description="Subject's gender: 'male', 'female', or 'unknown'",
    )
    caption_years: Optional[str] = Field(
        default=None,
        description=(
            "Years line of the caption when supplied by the caller "
            "(Lifespan.caption_years(); None = no years line). Only used when "
            "lifespan_source == 'caller'. Since 2.10.0."
        ),
    )
    lifespan_source: Literal["research", "caller"] = Field(
        default="research",
        description=(
            "'caller' when a verified Lifespan was passed to generate(); "
            "'research' when the years come from auto-research. Since 2.10.0."
        ),
    )
    birth_year_estimated: bool = Field(
        default=False,
        description=(
            "True when birth_year is a placeholder estimate (research could not "
            "extract a plausible year). An estimated birth year may feed age "
            "arithmetic but never any text or caption. Since 2.10.0."
        ),
    )

    @property
    def formatted_years(self) -> str:
        """Get formatted year range (e.g., '1879-1955', '460 BCE-370 BCE', or '1947-Present')."""
        if self.death_year is not None:
            return f"{format_year(self.birth_year)}-{format_year(self.death_year)}"
        return f"{format_year(self.birth_year)}-Present"

    @property
    def display_years(self) -> Optional[str]:
        """The years text that may be shown anywhere (caption, prompts, logs).

        * ``lifespan_source == "caller"`` -> ``caption_years`` (may be None).
        * research with an estimated birth year -> ``"d. YYYY"`` when a death
          year is known, else None (the placeholder never reaches text).
        * otherwise -> :attr:`formatted_years` (2.9.0 behaviour).

        ``None`` means: draw no years line.
        """
        if self.lifespan_source == "caller":
            return self.caption_years
        if self.birth_year_estimated:
            if self.death_year is not None:
                return f"d. {format_year(self.death_year)}"
            return None
        return self.formatted_years

    @property
    def display_birth_year(self) -> Optional[int]:
        """Birth year that may be printed in text (prompts), or None.

        None when the birth year is a research placeholder, or when a caller
        lifespan did not supply a birth year (its caption then has no birth
        part: ``"d. 2022"`` or no years line); in that case ``birth_year``
        holds the researched value for age arithmetic only.
        """
        if self.birth_year_estimated:
            return None
        if self.lifespan_source == "caller":
            caption = self.caption_years
            if caption is None or caption.startswith("d. "):
                return None
        return self.birth_year


class EvaluationResult(BaseModel):
    """Quality evaluation result for a portrait."""

    passed: bool = Field(..., description="Whether portrait passed evaluation")
    scores: Dict[str, float] = Field(
        default_factory=dict,
        description="Scores per criterion (0.0-1.0)",
    )
    feedback: List[str] = Field(
        default_factory=list,
        description="Positive feedback",
    )
    issues: List[str] = Field(
        default_factory=list,
        description="Issues found",
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="Recommendations for improvement",
    )

    @property
    def overall_score(self) -> float:
        """Calculate overall score as average of all scores."""
        if not self.scores:
            return 0.0
        return sum(self.scores.values()) / len(self.scores)


class PortraitResult(BaseModel):
    """Result of portrait generation."""

    subject: str = Field(..., description="Subject name")
    files: Dict[str, str] = Field(
        default_factory=dict,
        description="Generated files by style",
    )
    prompts: Dict[str, str] = Field(
        default_factory=dict,
        description="Prompt files by style",
    )
    metadata: Optional[SubjectData] = Field(None, description="Subject metadata")
    evaluation: Dict[str, EvaluationResult] = Field(
        default_factory=dict,
        description="Evaluation results by style",
    )
    generation_time_seconds: float = Field(
        default=0.0,
        description="Total generation time",
    )
    success: bool = Field(..., description="Whether generation succeeded")
    errors: List[str] = Field(
        default_factory=list,
        description="Errors encountered",
    )
    reference_images_found: int = Field(
        default=0,
        description=(
            "Number of real reference photos the pipeline located for this "
            "subject before generating (across all 9 lookup tiers -- "
            "GroundTruth, Wikidata, Wikipedia, Commons, DBpedia, etc). "
            "ZERO means the portrait was generated with no photographic "
            "reference at all -- for a real (non-legendary/pre-photography) "
            "person this is a strong signal the result is a plausible-"
            "looking but UNVERIFIED likeness, not evidence of resemblance. "
            "Confirmed live 2026-09-03: a contemporary academic with no "
            "locatable reference photo and an unresolved gender still "
            "produced a confident, fully-detailed photorealistic portrait "
            "-- callers building a fact-verified corpus (not just "
            "generating art) should treat reference_images_found == 0 as "
            "a hard reason to withhold marking the result as a verified "
            "likeness, even when success=True."
        ),
    )

    @property
    def all_passed(self) -> bool:
        """Check if all evaluations passed."""
        if not self.evaluation:
            return False
        return all(eval_result.passed for eval_result in self.evaluation.values())


class HealthCheckResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    gemini_configured: bool = Field(
        ...,
        description="Whether Gemini client is configured",
    )
    output_dir_writable: bool = Field(
        ...,
        description="Whether output directory is writable",
    )
    timestamp: str = Field(..., description="Check timestamp (ISO format)")


class StatusResponse(BaseModel):
    """Status response for a subject."""

    subject: str = Field(..., description="Subject name")
    exists: bool = Field(..., description="Whether portraits exist")
    files: List[str] = Field(
        default_factory=list,
        description="List of existing files",
    )
    generated_at: Optional[str] = Field(
        default=None,
        description="Generation timestamp (ISO format)",
    )
