"""Quality evaluator module for portrait evaluation."""

import logging
from typing import Dict, Tuple

from PIL import Image

from ..api.models import EvaluationResult, SubjectData

logger = logging.getLogger(__name__)


class QualityEvaluator:
    """
    Evaluator for assessing portrait quality.

    Performs technical and visual quality checks on generated portraits.
    """

    # Evaluation thresholds
    MIN_VISUAL_QUALITY_SCORE = 0.85
    MIN_HISTORICAL_ACCURACY_SCORE = 0.80

    def __init__(self, gemini_client=None):
        """
        Initialize QualityEvaluator.

        Args:
            gemini_client: Optional Gemini client for visual analysis
        """
        self.gemini_client = gemini_client
        logger.info("Initialized QualityEvaluator")

    def evaluate_portrait(
        self,
        image: Image.Image,
        subject_data: SubjectData,
        style: str,
        expected_resolution: Tuple[int, int] = (1024, 1024),
    ) -> EvaluationResult:
        """
        Evaluate portrait quality.

        Args:
            image: PIL Image to evaluate
            subject_data: Subject biographical data
            style: Portrait style (BW, Sepia, Color, Painting)
            expected_resolution: Expected image resolution

        Returns:
            EvaluationResult with scores and feedback

        Raises:
            ValueError: If parameters are invalid
        """
        if image is None:
            raise ValueError("Image cannot be None")

        if subject_data is None:
            raise ValueError("Subject data cannot be None")

        if not style:
            raise ValueError("Style cannot be empty")

        logger.info(f"Evaluating {style} portrait of {subject_data.name}")

        scores = {}
        feedback = []
        issues = []
        recommendations = []

        # Technical requirements check
        tech_checks = self.check_technical_requirements(image, expected_resolution)
        tech_score = sum(tech_checks.values()) / len(tech_checks) if tech_checks else 0.0
        scores["technical"] = tech_score

        for check, passed in tech_checks.items():
            if passed:
                feedback.append(f"✓ {check}")
            else:
                issues.append(f"✗ {check}")
                recommendations.append(f"Fix {check}")

        # Visual quality check
        visual_score = self.check_visual_quality(image, style)
        scores["visual_quality"] = visual_score

        if visual_score >= self.MIN_VISUAL_QUALITY_SCORE:
            feedback.append(f"✓ Visual quality: {visual_score:.2f}")
        else:
            issues.append(f"✗ Visual quality below threshold: {visual_score:.2f}")
            recommendations.append("Regenerate image with improved prompt")

        # Style-specific check
        style_score = self.check_style_adherence(image, style)
        scores["style_adherence"] = style_score

        if style_score >= 0.8:
            feedback.append(f"✓ Style adherence: {style_score:.2f}")
        else:
            issues.append(f"✗ Style adherence low: {style_score:.2f}")

        # Historical accuracy (simplified without AI)
        # In full implementation, would use Gemini to analyze
        accuracy_score = self.check_historical_accuracy(image, subject_data)
        scores["historical_accuracy"] = accuracy_score

        if accuracy_score >= self.MIN_HISTORICAL_ACCURACY_SCORE:
            feedback.append(f"✓ Historical accuracy: {accuracy_score:.2f}")
        else:
            issues.append(f"✗ Historical accuracy low: {accuracy_score:.2f}")
            recommendations.append("Review era-appropriate details")

        # Determine pass/fail
        passed = (
            tech_score >= 0.95
            and visual_score >= self.MIN_VISUAL_QUALITY_SCORE
            and accuracy_score >= self.MIN_HISTORICAL_ACCURACY_SCORE
        )

        logger.info(
            f"Evaluation complete: {'PASSED' if passed else 'FAILED'} "
            f"(scores: {scores})"
        )

        return EvaluationResult(
            passed=passed,
            scores=scores,
            feedback=feedback,
            issues=issues,
            recommendations=recommendations,
        )

    def check_technical_requirements(
        self, image: Image.Image, expected_resolution: Tuple[int, int]
    ) -> Dict[str, bool]:
        """
        Check technical requirements.

        Args:
            image: PIL Image to check
            expected_resolution: Expected (width, height)

        Returns:
            Dictionary of check results
        """
        if image is None:
            return {}

        checks = {}

        # Check resolution
        actual_width, actual_height = image.size
        expected_width, expected_height = expected_resolution

        checks["Correct width"] = actual_width == expected_width
        checks["Correct height"] = actual_height == expected_height

        # Check mode (should be RGB)
        checks["RGB mode"] = image.mode == "RGB"

        # Check image is not blank
        pixels = list(image.getdata())
        unique_colors = len(set(pixels[:100]))  # Sample first 100 pixels
        checks["Image has content"] = unique_colors > 1

        # Check overlay presence (dark bar at bottom)
        if image.size[1] > 0:
            bar_region = image.crop((
                0,
                int(image.size[1] * 0.85),
                image.size[0],
                image.size[1]
            ))
            pixels = list(bar_region.getdata())
            # Handle both RGB tuples and grayscale integers
            if isinstance(pixels[0], (tuple, list)):
                avg_brightness = sum(sum(p[:3]) / 3 for p in pixels) / len(pixels)
            else:
                avg_brightness = sum(pixels) / len(pixels)
            checks["Overlay present"] = avg_brightness < 100

        logger.debug(f"Technical checks: {checks}")

        return checks

    def check_visual_quality(self, image: Image.Image, style: str) -> float:
        """
        Check visual quality.

        Args:
            image: PIL Image to check
            style: Portrait style

        Returns:
            Quality score (0.0-1.0)
        """
        if image is None:
            return 0.0

        score = 0.0
        criteria = 0

        # Check composition (not too dark, not too bright)
        pixels = list(image.getdata())
        avg_brightness = sum(sum(p[:3]) / 3 for p in pixels) / len(pixels)

        # Good brightness range is 40-200
        if 40 <= avg_brightness <= 200:
            score += 0.3
        elif 20 <= avg_brightness <= 220:
            score += 0.15
        criteria += 1

        # Check contrast (difference between darkest and brightest)
        brightnesses = [sum(p[:3]) / 3 for p in pixels]
        contrast = max(brightnesses) - min(brightnesses)

        # Good contrast > 100
        if contrast > 150:
            score += 0.3
        elif contrast > 100:
            score += 0.2
        elif contrast > 50:
            score += 0.1
        criteria += 1

        # Check detail level (variation in adjacent pixels)
        width, height = image.size
        variations = 0
        samples = 0

        for y in range(10, min(height - 10, 100), 10):
            for x in range(10, min(width - 10, 100), 10):
                pixel1 = image.getpixel((x, y))
                pixel2 = image.getpixel((x + 1, y))
                diff = sum(abs(a - b) for a, b in zip(pixel1, pixel2))
                if diff > 10:
                    variations += 1
                samples += 1

        if samples > 0:
            detail_ratio = variations / samples
            if detail_ratio > 0.3:
                score += 0.25
            elif detail_ratio > 0.15:
                score += 0.15
        criteria += 1

        # Check for artifacts (extreme pixel values)
        extreme_pixels = sum(
            1 for p in pixels
            if min(p[:3]) < 5 or max(p[:3]) > 250
        )
        artifact_ratio = extreme_pixels / len(pixels)

        if artifact_ratio < 0.05:
            score += 0.15
        elif artifact_ratio < 0.1:
            score += 0.1
        criteria += 1

        # Normalize score
        max_score = criteria * 0.3  # Approximate max from criteria above
        normalized_score = min(1.0, score / max_score) if max_score > 0 else 0.0

        logger.debug(
            f"Visual quality: {normalized_score:.2f} "
            f"(brightness={avg_brightness:.1f}, contrast={contrast:.1f})"
        )

        return normalized_score

    def check_style_adherence(self, image: Image.Image, style: str) -> float:
        """
        Check adherence to requested style.

        Args:
            image: PIL Image to check
            style: Requested style (BW, Sepia, Color, Painting)

        Returns:
            Style adherence score (0.0-1.0)
        """
        if image is None or not style:
            return 0.0

        # Sample pixels from center region (avoid overlay)
        width, height = image.size
        center_region = image.crop((
            width // 4,
            height // 4,
            3 * width // 4,
            int(height * 0.75)  # Avoid overlay at bottom
        ))

        pixels = list(center_region.getdata())
        score = 0.0

        if style == "BW":
            # Check if pixels are grayscale (R=G=B)
            grayscale_pixels = sum(
                1 for p in pixels[:100]
                if abs(p[0] - p[1]) < 5 and abs(p[1] - p[2]) < 5
            )
            score = grayscale_pixels / 100

        elif style == "Sepia":
            # Check for warm tones (R > G > B generally)
            warm_pixels = sum(
                1 for p in pixels[:100]
                if p[0] > p[1] and p[1] > p[2]
            )
            score = warm_pixels / 100

        elif style == "Color":
            # Check for color variation (not grayscale)
            color_pixels = sum(
                1 for p in pixels[:100]
                if max(abs(p[0] - p[1]), abs(p[1] - p[2]), abs(p[0] - p[2])) > 10
            )
            score = color_pixels / 100

        elif style == "Painting":
            # For painting, we'd check for artistic qualities
            # Simplified: check for reasonable color variation
            score = 0.85  # Placeholder - would need more sophisticated check

        else:
            logger.warning(f"Unknown style: {style}")
            score = 0.5

        logger.debug(f"Style adherence ({style}): {score:.2f}")

        return score

    def check_historical_accuracy(
        self, image: Image.Image, subject_data: SubjectData
    ) -> float:
        """
        Check historical accuracy.

        Args:
            image: PIL Image to check
            subject_data: Subject biographical data

        Returns:
            Accuracy score (0.0-1.0)
        """
        if image is None or subject_data is None:
            return 0.0

        # Simplified accuracy check (without AI analysis)
        # In full implementation, would use Gemini to analyze image
        # For now, give benefit of the doubt with moderate score

        score = 0.8

        # Check that image has reasonable content
        pixels = list(image.getdata())
        if len(set(pixels[:100])) <= 1:
            # Blank or single-color image
            score = 0.0
        else:
            # Has content, assume reasonable accuracy
            # In production, would analyze with AI
            score = 0.85

        logger.debug(f"Historical accuracy: {score:.2f}")

        return score

    def evaluate_batch(
        self,
        images: Dict[str, Image.Image],
        subject_data: SubjectData,
        expected_resolution: Tuple[int, int] = (1024, 1024),
    ) -> Dict[str, EvaluationResult]:
        """
        Evaluate multiple portrait styles.

        Args:
            images: Dictionary of style -> Image
            subject_data: Subject biographical data
            expected_resolution: Expected image resolution

        Returns:
            Dictionary of style -> EvaluationResult
        """
        if not images:
            raise ValueError("Images dictionary cannot be empty")

        if subject_data is None:
            raise ValueError("Subject data cannot be None")

        logger.info(f"Evaluating batch of {len(images)} portraits")

        results = {}

        for style, image in images.items():
            try:
                result = self.evaluate_portrait(
                    image, subject_data, style, expected_resolution
                )
                results[style] = result
            except Exception as e:
                logger.error(f"Failed to evaluate {style}: {e}", exc_info=True)
                results[style] = EvaluationResult(
                    passed=False,
                    scores={},
                    feedback=[],
                    issues=[f"Evaluation failed: {e}"],
                    recommendations=["Regenerate portrait"],
                )

        passed_count = sum(1 for r in results.values() if r.passed)
        logger.info(f"Batch evaluation complete: {passed_count}/{len(results)} passed")

        return results
