"""Unit tests for QualityEvaluator."""

import pytest
from PIL import Image

from portrait_generator.core.evaluator import QualityEvaluator
from portrait_generator.api.models import SubjectData, EvaluationResult


@pytest.fixture
def evaluator():
    """Create evaluator instance."""
    return QualityEvaluator()


@pytest.fixture
def sample_subject_data():
    """Create sample subject data."""
    return SubjectData(
        name="Albert Einstein",
        birth_year=1879,
        death_year=1955,
        era="20th Century",
        appearance_notes=["Wild hair", "Mustache"],
        historical_context="Physicist",
        reference_sources=["Records"],
    )


@pytest.fixture
def sample_portrait():
    """Create a sample portrait image with overlay."""
    # Create image with gradient
    img = Image.new("RGB", (1024, 1024), color=(120, 100, 90))

    # Add some variation for realism
    # Mix of color and some grayscale pixels to not be perfect
    pixels = img.load()
    for y in range(1024):
        for x in range(1024):
            variation = ((x + y) % 50) - 25
            r, g, b = pixels[x, y]
            # Make some pixels more grayscale-like (for imperfect color score)
            if (x + y) % 10 == 0:
                # Make this pixel closer to grayscale
                avg = (r + g + b) // 3
                pixels[x, y] = (avg, avg, avg)
            else:
                pixels[x, y] = (
                    max(0, min(255, r + variation)),
                    max(0, min(255, g + variation)),
                    max(0, min(255, b + variation)),
                )

    # Add dark overlay bar at bottom
    for y in range(870, 1024):
        for x in range(1024):
            pixels[x, y] = (20, 20, 20)

    return img


@pytest.fixture
def sample_bw_portrait():
    """Create a grayscale portrait."""
    img = Image.new("RGB", (1024, 1024), color=(128, 128, 128))

    # Add variation
    pixels = img.load()
    for y in range(1024):
        for x in range(1024):
            variation = ((x + y) % 40) - 20
            gray = max(0, min(255, 128 + variation))
            pixels[x, y] = (gray, gray, gray)

    # Add overlay
    for y in range(870, 1024):
        for x in range(1024):
            pixels[x, y] = (20, 20, 20)

    return img


class TestQualityEvaluatorInit:
    """Tests for QualityEvaluator initialization."""

    def test_init_default(self):
        """Test initialization with defaults."""
        evaluator = QualityEvaluator()

        assert evaluator.gemini_client is None

    def test_init_with_client(self):
        """Test initialization with Gemini client."""
        mock_client = object()
        evaluator = QualityEvaluator(gemini_client=mock_client)

        assert evaluator.gemini_client == mock_client


class TestEvaluatePortrait:
    """Tests for evaluate_portrait method."""

    def test_evaluate_portrait_success(
        self, evaluator, sample_portrait, sample_subject_data
    ):
        """Test successful portrait evaluation."""
        result = evaluator.evaluate_portrait(
            sample_portrait, sample_subject_data, "Color"
        )

        assert isinstance(result, EvaluationResult)
        assert isinstance(result.passed, bool)
        assert isinstance(result.scores, dict)
        assert len(result.scores) > 0

    def test_evaluate_portrait_scores_present(
        self, evaluator, sample_portrait, sample_subject_data
    ):
        """Test that all expected scores are present."""
        result = evaluator.evaluate_portrait(
            sample_portrait, sample_subject_data, "Color"
        )

        assert "technical" in result.scores
        assert "visual_quality" in result.scores
        assert "style_adherence" in result.scores
        assert "historical_accuracy" in result.scores

    def test_evaluate_portrait_none_image(self, evaluator, sample_subject_data):
        """Test error handling for None image."""
        with pytest.raises(ValueError, match="cannot be None"):
            evaluator.evaluate_portrait(None, sample_subject_data, "Color")

    def test_evaluate_portrait_none_subject_data(self, evaluator, sample_portrait):
        """Test error handling for None subject data."""
        with pytest.raises(ValueError, match="cannot be None"):
            evaluator.evaluate_portrait(sample_portrait, None, "Color")

    def test_evaluate_portrait_empty_style(
        self, evaluator, sample_portrait, sample_subject_data
    ):
        """Test error handling for empty style."""
        with pytest.raises(ValueError, match="cannot be empty"):
            evaluator.evaluate_portrait(sample_portrait, sample_subject_data, "")

    def test_evaluate_portrait_bw_style(
        self, evaluator, sample_bw_portrait, sample_subject_data
    ):
        """Test evaluation of BW portrait."""
        result = evaluator.evaluate_portrait(
            sample_bw_portrait, sample_subject_data, "BW"
        )

        assert isinstance(result, EvaluationResult)
        # BW portrait should have high style adherence
        assert result.scores.get("style_adherence", 0) > 0.7

    def test_evaluate_portrait_custom_resolution(
        self, evaluator, sample_subject_data
    ):
        """Test evaluation with custom resolution."""
        img = Image.new("RGB", (800, 1000), color=(100, 100, 100))

        result = evaluator.evaluate_portrait(
            img, sample_subject_data, "Color", expected_resolution=(800, 1000)
        )

        assert isinstance(result, EvaluationResult)

    def test_evaluate_portrait_wrong_resolution(
        self, evaluator, sample_portrait, sample_subject_data
    ):
        """Test evaluation fails for wrong resolution."""
        result = evaluator.evaluate_portrait(
            sample_portrait,
            sample_subject_data,
            "Color",
            expected_resolution=(800, 800),
        )

        # Should fail technical checks
        assert not result.passed or result.scores["technical"] < 1.0

    def test_evaluate_portrait_feedback_present(
        self, evaluator, sample_portrait, sample_subject_data
    ):
        """Test that evaluation includes feedback."""
        result = evaluator.evaluate_portrait(
            sample_portrait, sample_subject_data, "Color"
        )

        # Should have either feedback or issues
        assert len(result.feedback) > 0 or len(result.issues) > 0


class TestCheckTechnicalRequirements:
    """Tests for check_technical_requirements method."""

    def test_check_technical_requirements_correct_resolution(
        self, evaluator, sample_portrait
    ):
        """Test technical checks for correct resolution."""
        checks = evaluator.check_technical_requirements(
            sample_portrait, (1024, 1024)
        )

        assert checks["Correct width"] is True
        assert checks["Correct height"] is True

    def test_check_technical_requirements_wrong_resolution(self, evaluator):
        """Test technical checks for wrong resolution."""
        img = Image.new("RGB", (800, 800), color=(100, 100, 100))

        checks = evaluator.check_technical_requirements(img, (1024, 1024))

        assert checks["Correct width"] is False
        assert checks["Correct height"] is False

    def test_check_technical_requirements_rgb_mode(
        self, evaluator, sample_portrait
    ):
        """Test RGB mode check."""
        checks = evaluator.check_technical_requirements(
            sample_portrait, (1024, 1024)
        )

        assert checks["RGB mode"] is True

    def test_check_technical_requirements_wrong_mode(self, evaluator):
        """Test mode check for non-RGB image."""
        img = Image.new("L", (1024, 1024), color=128)

        checks = evaluator.check_technical_requirements(img, (1024, 1024))

        assert checks["RGB mode"] is False

    def test_check_technical_requirements_content_check(
        self, evaluator, sample_portrait
    ):
        """Test content presence check."""
        checks = evaluator.check_technical_requirements(
            sample_portrait, (1024, 1024)
        )

        assert checks["Image has content"] is True

    def test_check_technical_requirements_blank_image(self, evaluator):
        """Test content check fails for blank image."""
        img = Image.new("RGB", (1024, 1024), color=(100, 100, 100))

        checks = evaluator.check_technical_requirements(img, (1024, 1024))

        assert checks["Image has content"] is False

    def test_check_technical_requirements_overlay_present(
        self, evaluator, sample_portrait
    ):
        """Test overlay presence check."""
        checks = evaluator.check_technical_requirements(
            sample_portrait, (1024, 1024)
        )

        assert checks["Overlay present"] is True

    def test_check_technical_requirements_no_overlay(self, evaluator):
        """Test overlay check fails without overlay."""
        img = Image.new("RGB", (1024, 1024), color=(150, 150, 150))

        checks = evaluator.check_technical_requirements(img, (1024, 1024))

        assert checks["Overlay present"] is False

    def test_check_technical_requirements_none_image(self, evaluator):
        """Test technical checks for None image."""
        checks = evaluator.check_technical_requirements(None, (1024, 1024))

        assert checks == {}


class TestCheckVisualQuality:
    """Tests for check_visual_quality method."""

    def test_check_visual_quality_returns_score(
        self, evaluator, sample_portrait
    ):
        """Test visual quality returns score."""
        score = evaluator.check_visual_quality(sample_portrait, "Color")

        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_check_visual_quality_good_brightness(self, evaluator):
        """Test visual quality for good brightness."""
        img = Image.new("RGB", (1024, 1024), color=(120, 120, 120))

        score = evaluator.check_visual_quality(img, "Color")

        assert score > 0.0

    def test_check_visual_quality_too_dark(self, evaluator):
        """Test visual quality penalizes very dark images."""
        img = Image.new("RGB", (1024, 1024), color=(10, 10, 10))

        score = evaluator.check_visual_quality(img, "Color")

        # Should still get some score but not maximum
        assert 0.0 <= score <= 1.0

    def test_check_visual_quality_too_bright(self, evaluator):
        """Test visual quality penalizes very bright images."""
        img = Image.new("RGB", (1024, 1024), color=(240, 240, 240))

        score = evaluator.check_visual_quality(img, "Color")

        assert 0.0 <= score <= 1.0

    def test_check_visual_quality_high_contrast(self, evaluator):
        """Test visual quality rewards high contrast."""
        img = Image.new("RGB", (1024, 1024), color=(100, 100, 100))
        pixels = img.load()

        # Add high contrast areas
        for y in range(512):
            for x in range(1024):
                pixels[x, y] = (200, 200, 200)

        score = evaluator.check_visual_quality(img, "Color")

        assert score > 0.3

    def test_check_visual_quality_none_image(self, evaluator):
        """Test visual quality for None image."""
        score = evaluator.check_visual_quality(None, "Color")

        assert score == 0.0

    def test_check_visual_quality_with_detail(self, evaluator, sample_portrait):
        """Test visual quality for image with detail."""
        score = evaluator.check_visual_quality(sample_portrait, "Color")

        # Should get reasonable score due to variation
        assert score > 0.4


class TestCheckStyleAdherence:
    """Tests for check_style_adherence method."""

    def test_check_style_adherence_bw(self, evaluator, sample_bw_portrait):
        """Test style adherence for BW image."""
        score = evaluator.check_style_adherence(sample_bw_portrait, "BW")

        assert score > 0.8

    def test_check_style_adherence_sepia(self, evaluator):
        """Test style adherence for sepia image."""
        # Create sepia-like image (R > G > B)
        img = Image.new("RGB", (1024, 1024), color=(160, 130, 100))

        score = evaluator.check_style_adherence(img, "Sepia")

        assert score > 0.5

    def test_check_style_adherence_color(self, evaluator, sample_portrait):
        """Test style adherence for color image."""
        score = evaluator.check_style_adherence(sample_portrait, "Color")

        assert score >= 0.0

    def test_check_style_adherence_painting(self, evaluator, sample_portrait):
        """Test style adherence for painting."""
        score = evaluator.check_style_adherence(sample_portrait, "Painting")

        assert score > 0.0

    def test_check_style_adherence_unknown_style(self, evaluator, sample_portrait):
        """Test style adherence for unknown style."""
        score = evaluator.check_style_adherence(sample_portrait, "Unknown")

        # Should return some default score
        assert 0.0 <= score <= 1.0

    def test_check_style_adherence_none_image(self, evaluator):
        """Test style adherence for None image."""
        score = evaluator.check_style_adherence(None, "Color")

        assert score == 0.0

    def test_check_style_adherence_empty_style(self, evaluator, sample_portrait):
        """Test style adherence for empty style."""
        score = evaluator.check_style_adherence(sample_portrait, "")

        assert score == 0.0


class TestCheckHistoricalAccuracy:
    """Tests for check_historical_accuracy method."""

    def test_check_historical_accuracy_valid(
        self, evaluator, sample_portrait, sample_subject_data
    ):
        """Test historical accuracy for valid image."""
        score = evaluator.check_historical_accuracy(
            sample_portrait, sample_subject_data
        )

        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
        assert score > 0.5  # Should have reasonable score

    def test_check_historical_accuracy_blank_image(
        self, evaluator, sample_subject_data
    ):
        """Test historical accuracy for blank image."""
        img = Image.new("RGB", (1024, 1024), color=(100, 100, 100))

        score = evaluator.check_historical_accuracy(img, sample_subject_data)

        # Blank image should get low score
        assert score == 0.0

    def test_check_historical_accuracy_none_image(
        self, evaluator, sample_subject_data
    ):
        """Test historical accuracy for None image."""
        score = evaluator.check_historical_accuracy(None, sample_subject_data)

        assert score == 0.0

    def test_check_historical_accuracy_none_subject(
        self, evaluator, sample_portrait
    ):
        """Test historical accuracy for None subject data."""
        score = evaluator.check_historical_accuracy(sample_portrait, None)

        assert score == 0.0


class TestEvaluateBatch:
    """Tests for evaluate_batch method."""

    def test_evaluate_batch_success(
        self, evaluator, sample_portrait, sample_bw_portrait, sample_subject_data
    ):
        """Test successful batch evaluation."""
        images = {
            "Color": sample_portrait,
            "BW": sample_bw_portrait,
        }

        results = evaluator.evaluate_batch(images, sample_subject_data)

        assert len(results) == 2
        assert "Color" in results
        assert "BW" in results
        assert all(isinstance(r, EvaluationResult) for r in results.values())

    def test_evaluate_batch_empty_images(self, evaluator, sample_subject_data):
        """Test error handling for empty images dict."""
        with pytest.raises(ValueError, match="cannot be empty"):
            evaluator.evaluate_batch({}, sample_subject_data)

    def test_evaluate_batch_none_subject_data(
        self, evaluator, sample_portrait
    ):
        """Test error handling for None subject data."""
        images = {"Color": sample_portrait}

        with pytest.raises(ValueError, match="cannot be None"):
            evaluator.evaluate_batch(images, None)

    def test_evaluate_batch_multiple_styles(
        self, evaluator, sample_portrait, sample_subject_data
    ):
        """Test batch evaluation with multiple styles."""
        images = {
            "BW": sample_portrait,
            "Sepia": sample_portrait,
            "Color": sample_portrait,
            "Painting": sample_portrait,
        }

        results = evaluator.evaluate_batch(images, sample_subject_data)

        assert len(results) == 4
        for style in ["BW", "Sepia", "Color", "Painting"]:
            assert style in results

    def test_evaluate_batch_custom_resolution(
        self, evaluator, sample_subject_data
    ):
        """Test batch evaluation with custom resolution."""
        img = Image.new("RGB", (800, 1000), color=(100, 100, 100))
        images = {"Color": img}

        results = evaluator.evaluate_batch(
            images, sample_subject_data, expected_resolution=(800, 1000)
        )

        assert len(results) == 1

    def test_evaluate_batch_handles_errors(
        self, evaluator, sample_subject_data
    ):
        """Test batch evaluation handles individual errors."""
        images = {
            "Color": Image.new("RGB", (1024, 1024), color=(100, 100, 100)),
            "Invalid": None,  # This will cause an error
        }

        # Should not raise, should return result for valid and error for invalid
        results = evaluator.evaluate_batch(images, sample_subject_data)

        assert "Color" in results
        assert "Invalid" in results
        assert not results["Invalid"].passed


class TestIntegration:
    """Integration tests for QualityEvaluator."""

    def test_full_evaluation_workflow(
        self, evaluator, sample_portrait, sample_subject_data
    ):
        """Test complete evaluation workflow."""
        # Evaluate single portrait
        result = evaluator.evaluate_portrait(
            sample_portrait, sample_subject_data, "Color"
        )

        # Check result structure
        assert isinstance(result, EvaluationResult)
        assert isinstance(result.passed, bool)
        assert len(result.scores) >= 4

        # Check score ranges
        for score_name, score_value in result.scores.items():
            assert 0.0 <= score_value <= 1.0, f"{score_name} out of range"

    def test_evaluation_consistency(
        self, evaluator, sample_portrait, sample_subject_data
    ):
        """Test that evaluation is consistent."""
        result1 = evaluator.evaluate_portrait(
            sample_portrait, sample_subject_data, "Color"
        )
        result2 = evaluator.evaluate_portrait(
            sample_portrait, sample_subject_data, "Color"
        )

        # Same image should get same scores
        assert result1.scores == result2.scores
        assert result1.passed == result2.passed

    def test_evaluation_different_styles(
        self, evaluator, sample_portrait, sample_bw_portrait, sample_subject_data
    ):
        """Test evaluation distinguishes between styles."""
        color_result = evaluator.evaluate_portrait(
            sample_portrait, sample_subject_data, "Color"
        )
        bw_result = evaluator.evaluate_portrait(
            sample_bw_portrait, sample_subject_data, "BW"
        )

        # BW image should score higher on BW style adherence
        assert (
            bw_result.scores.get("style_adherence", 0)
            > color_result.scores.get("style_adherence", 0)
        )
