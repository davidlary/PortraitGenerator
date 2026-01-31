"""Pre-generation validation for proactive error prevention.

This module performs validation before generation starts to:
- Fact-check biographical data
- Validate reference image compatibility
- Predict potential issues
- Provide recommendations for success
"""

import logging
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

from .api.models import SubjectData
from .reference_finder import ReferenceImage
from .utils.gemini_client import PreGenerationCheck

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result from pre-generation validation."""

    is_valid: bool
    """Whether generation should proceed"""

    confidence: float
    """Confidence in successful generation (0.0-1.0)"""

    issues: List[str]
    """List of issues found"""

    warnings: List[str]
    """Non-blocking warnings"""

    recommendations: List[str]
    """Suggestions for improvement"""

    fact_check_results: Dict[str, bool]
    """Results from fact-checking"""

    reference_validation: Dict[str, Any]
    """Reference image validation results"""


class PreGenerationValidator:
    """Validates generation inputs before starting.

    Performs proactive checks to prevent common errors:
    - Biographical data accuracy
    - Reference image quality and compatibility
    - Prompt clarity and completeness
    - Historical consistency
    """

    def __init__(
        self,
        gemini_client,
        enable_fact_checking: bool = True,
    ):
        """Initialize pre-generation validator.

        Args:
            gemini_client: GeminiImageClient for fact-checking
            enable_fact_checking: Whether to use Google Search grounding
        """
        self.gemini_client = gemini_client
        self.enable_fact_checking = enable_fact_checking
        logger.debug("Initialized PreGenerationValidator")

    def validate(
        self,
        subject_data: SubjectData,
        style: str,
        prompt: str,
        reference_images: Optional[List[ReferenceImage]] = None,
    ) -> ValidationResult:
        """Perform comprehensive pre-generation validation.

        Args:
            subject_data: Subject biographical data
            style: Portrait style
            prompt: Generation prompt
            reference_images: Optional reference images

        Returns:
            ValidationResult with all findings
        """
        logger.info(f"Validating generation request for {subject_data.name}...")

        issues = []
        warnings = []
        recommendations = []
        fact_check_results = {}
        reference_validation = {}

        # 1. Validate subject data
        data_issues = self._validate_subject_data(subject_data)
        issues.extend(data_issues)

        # 2. Fact-check biographical information
        if self.enable_fact_checking:
            fact_check_results = self._fact_check_subject(subject_data)
            for key, is_valid in fact_check_results.items():
                if not is_valid:
                    issues.append(f"Fact-check failed: {key}")

        # 3. Validate style
        style_issues = self._validate_style(style)
        issues.extend(style_issues)

        # 4. Validate prompt quality
        prompt_issues, prompt_warnings = self._validate_prompt(prompt, subject_data)
        issues.extend(prompt_issues)
        warnings.extend(prompt_warnings)

        # 5. Validate reference images
        if reference_images:
            reference_validation = self._validate_reference_images(
                reference_images, subject_data
            )
            if reference_validation.get("issues"):
                issues.extend(reference_validation["issues"])
            if reference_validation.get("warnings"):
                warnings.extend(reference_validation["warnings"])

        # 6. Check for common pitfalls
        pitfall_warnings = self._check_common_pitfalls(subject_data, style)
        warnings.extend(pitfall_warnings)

        # 7. Generate recommendations
        recommendations = self._generate_recommendations(
            subject_data, style, issues, warnings
        )

        # Calculate confidence
        confidence = self._calculate_confidence(issues, warnings, fact_check_results)

        # Determine if valid (no blocking issues)
        is_valid = len(issues) == 0 and confidence > 0.5

        result = ValidationResult(
            is_valid=is_valid,
            confidence=confidence,
            issues=issues,
            warnings=warnings,
            recommendations=recommendations,
            fact_check_results=fact_check_results,
            reference_validation=reference_validation,
        )

        logger.info(
            f"Validation complete: valid={is_valid}, "
            f"confidence={confidence:.2f}, "
            f"issues={len(issues)}, warnings={len(warnings)}"
        )

        return result

    def _validate_subject_data(self, subject_data: SubjectData) -> List[str]:
        """Validate subject data completeness.

        Args:
            subject_data: Subject data to validate

        Returns:
            List of issues found
        """
        issues = []

        if not subject_data.name or len(subject_data.name.strip()) < 3:
            issues.append("Subject name is too short or empty")

        if not subject_data.era:
            issues.append("Historical era not specified")

        if not subject_data.birth_year or subject_data.birth_year < 1000:
            issues.append("Invalid or missing birth year")

        if subject_data.death_year:
            if subject_data.death_year < subject_data.birth_year:
                issues.append("Death year precedes birth year")
            if subject_data.death_year - subject_data.birth_year > 150:
                issues.append("Lifespan exceeds 150 years (likely data error)")

        return issues

    def _fact_check_subject(self, subject_data: SubjectData) -> Dict[str, bool]:
        """Fact-check subject information using Google Search.

        Args:
            subject_data: Subject data to fact-check

        Returns:
            Dictionary of fact-check results
        """
        results = {}

        if not hasattr(self.gemini_client, "query_with_grounding"):
            logger.debug("Fact-checking not available (model doesn't support grounding)")
            return {"grounding_not_available": True}

        try:
            # Check birth year
            birth_query = f"Verify birth year for {subject_data.name}: {subject_data.birth_year}"
            birth_response = self.gemini_client.query_with_grounding(birth_query)
            results["birth_year"] = self._parse_verification_response(birth_response)

            # Check death year if present
            if subject_data.death_year:
                death_query = f"Verify death year for {subject_data.name}: {subject_data.death_year}"
                death_response = self.gemini_client.query_with_grounding(death_query)
                results["death_year"] = self._parse_verification_response(death_response)

            # Check era
            era_query = f"Verify {subject_data.name} lived during {subject_data.era}"
            era_response = self.gemini_client.query_with_grounding(era_query)
            results["era"] = self._parse_verification_response(era_response)

            logger.debug(f"Fact-check results: {results}")

        except Exception as e:
            logger.warning(f"Fact-checking failed: {e}")
            results["error"] = False

        return results

    def _parse_verification_response(self, response: str) -> bool:
        """Parse verification response to boolean.

        Args:
            response: Model response text

        Returns:
            True if verified, False otherwise
        """
        # Handle None or empty response
        if not response:
            logger.warning("Verification response is None or empty, assuming valid")
            return True

        response_lower = response.lower()

        # Look for negative indicators FIRST (to catch "incorrect" before "correct")
        if any(word in response_lower for word in ["incorrect", "inaccurate", "false", "no", "wrong"]):
            return False

        # Look for affirmative indicators
        if any(word in response_lower for word in ["correct", "accurate", "verified", "yes", "confirmed"]):
            return True

        # Uncertain - assume valid to avoid false positives
        return True

    def _validate_style(self, style: str) -> List[str]:
        """Validate portrait style.

        Args:
            style: Portrait style

        Returns:
            List of issues
        """
        issues = []

        valid_styles = ["BW", "Sepia", "Color", "Painting"]
        if style not in valid_styles:
            issues.append(f"Invalid style '{style}'. Must be one of: {valid_styles}")

        return issues

    def _validate_prompt(
        self, prompt: str, subject_data: SubjectData
    ) -> tuple[List[str], List[str]]:
        """Validate prompt quality.

        Args:
            prompt: Generation prompt
            subject_data: Subject data

        Returns:
            Tuple of (issues, warnings)
        """
        issues = []
        warnings = []

        if not prompt or len(prompt.strip()) < 50:
            issues.append("Prompt is too short (minimum 50 characters)")

        if subject_data.name not in prompt:
            warnings.append("Subject name not found in prompt")

        if subject_data.era not in prompt:
            warnings.append("Historical era not mentioned in prompt")

        # Check for potentially problematic words
        problematic = ["cartoon", "anime", "sketch", "drawing"]
        for word in problematic:
            if word in prompt.lower():
                warnings.append(f"Prompt contains '{word}' which may affect photorealism")

        return issues, warnings

    def _validate_reference_images(
        self,
        reference_images: List[ReferenceImage],
        subject_data: SubjectData,
    ) -> Dict[str, Any]:
        """Validate reference images.

        Args:
            reference_images: List of reference images
            subject_data: Subject data

        Returns:
            Validation results dictionary
        """
        validation = {
            "issues": [],
            "warnings": [],
            "total_images": len(reference_images),
            "authentic_count": 0,
            "quality_scores": [],
        }

        for ref in reference_images:
            # Check authenticity score
            if ref.authenticity_score >= 0.75:
                validation["authentic_count"] += 1
            else:
                validation["warnings"].append(
                    f"Low authenticity score for {ref.source}: {ref.authenticity_score:.2f}"
                )

            # Check quality score
            validation["quality_scores"].append(ref.quality_score)
            if ref.quality_score < 0.6:
                validation["warnings"].append(
                    f"Low quality score for {ref.source}: {ref.quality_score:.2f}"
                )

            # Check era match
            if not ref.era_match:
                validation["warnings"].append(
                    f"Reference from {ref.source} may not match era"
                )

        # Calculate average quality
        if validation["quality_scores"]:
            avg_quality = sum(validation["quality_scores"]) / len(validation["quality_scores"])
            validation["average_quality"] = avg_quality

            if avg_quality < 0.7:
                validation["warnings"].append(
                    f"Average reference quality is low: {avg_quality:.2f}"
                )

        # Check if we have enough authentic references
        if validation["authentic_count"] < 2 and len(reference_images) >= 2:
            validation["warnings"].append(
                "Fewer than 2 authentic references available"
            )

        return validation

    def _check_common_pitfalls(
        self, subject_data: SubjectData, style: str
    ) -> List[str]:
        """Check for common generation pitfalls.

        Args:
            subject_data: Subject data
            style: Portrait style

        Returns:
            List of warnings
        """
        warnings = []

        # Check for very old subjects (harder to find references)
        if subject_data.birth_year < 1800:
            warnings.append(
                f"Subject from {subject_data.birth_year} - limited photographic references available"
            )

        # Check for recent subjects (copyright/privacy concerns)
        if subject_data.birth_year > 1950:
            warnings.append(
                "Recent subject - be mindful of copyright and privacy concerns"
            )

        # Check BW for color-era subjects
        if style == "BW" and subject_data.birth_year > 1950:
            warnings.append(
                "Generating BW portrait for color photography era - consider Color style"
            )

        # Check Sepia for modern subjects
        if style == "Sepia" and subject_data.birth_year > 1930:
            warnings.append(
                "Sepia style uncommon for subjects born after 1930"
            )

        return warnings

    def _generate_recommendations(
        self,
        subject_data: SubjectData,
        style: str,
        issues: List[str],
        warnings: List[str],
    ) -> List[str]:
        """Generate recommendations for improvement.

        Args:
            subject_data: Subject data
            style: Style
            issues: Issues found
            warnings: Warnings

        Returns:
            List of recommendations
        """
        recommendations = []

        if issues:
            recommendations.append("Resolve all issues before proceeding with generation")

        if warnings:
            recommendations.append("Review warnings and consider adjustments")

        # Style-specific recommendations
        if subject_data.birth_year < 1850:
            recommendations.append(
                "Consider Painting style for pre-photography era subjects"
            )

        if len(warnings) > 3:
            recommendations.append(
                "Multiple warnings detected - consider revising inputs"
            )

        if not recommendations:
            recommendations.append("All validation checks passed - proceed with generation")

        return recommendations

    def _calculate_confidence(
        self,
        issues: List[str],
        warnings: List[str],
        fact_check_results: Dict[str, bool],
    ) -> float:
        """Calculate confidence score for successful generation.

        Args:
            issues: List of issues
            warnings: List of warnings
            fact_check_results: Fact-check results

        Returns:
            Confidence score (0.0-1.0)
        """
        # Start with full confidence
        confidence = 1.0

        # Deduct for issues (blocking)
        confidence -= len(issues) * 0.25

        # Deduct for warnings (non-blocking)
        confidence -= len(warnings) * 0.05

        # Deduct for failed fact-checks
        failed_checks = sum(1 for v in fact_check_results.values() if not v)
        confidence -= failed_checks * 0.15

        # Clamp to [0.0, 1.0]
        confidence = max(0.0, min(1.0, confidence))

        return confidence

    def quick_check(
        self,
        subject_data: SubjectData,
        style: str,
    ) -> bool:
        """Quick validation check without fact-checking.

        Args:
            subject_data: Subject data
            style: Style

        Returns:
            True if basic validation passes
        """
        issues = []

        issues.extend(self._validate_subject_data(subject_data))
        issues.extend(self._validate_style(style))

        return len(issues) == 0
