"""API request and response models."""

from typing import Dict, List, Optional
from pathlib import Path

from pydantic import BaseModel, Field, field_validator


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

    @property
    def formatted_years(self) -> str:
        """Get formatted year range (e.g., '1879-1955' or '1947-Present')."""
        if self.death_year:
            return f"{self.birth_year}-{self.death_year}"
        return f"{self.birth_year}-Present"


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
