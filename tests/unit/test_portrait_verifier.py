"""Unit tests for core/portrait_verifier.py — post-generation verification."""

import hashlib
import io
import os
from pathlib import Path

import pytest
from PIL import Image, ImageDraw, ImageFont

from portrait_generator.core.portrait_verifier import PortraitVerifier, VerificationResult
from portrait_generator.api.models import SubjectData

# Skip tests that need Vision API (need a valid GOOGLE_API_KEY)
_NO_API_KEY = not os.getenv("GOOGLE_API_KEY")
_SKIP_NO_KEY = pytest.mark.skipif(
    _NO_API_KEY, reason="Requires real Gemini API — set GOOGLE_API_KEY"
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_subject():
    return SubjectData(
        name="Alan Turing",
        birth_year=1912,
        death_year=1954,
        era="20th Century",
        gender="male",
    )


@pytest.fixture
def sample_image():
    """Create a minimal valid RGB image."""
    img = Image.new("RGB", (512, 682), color=(100, 80, 60))
    return img


@pytest.fixture
def portrait_png(tmp_path, sample_image):
    """Save a portrait-sized PNG to a temp file."""
    path = tmp_path / "AlanTuring_Painting.png"
    # Make it large enough to pass the size check (~300 KB)
    # Use an image with enough data
    large_img = Image.new("RGB", (1024, 1365), color=(100, 80, 60))
    # Add random-ish variation to avoid compression being too good
    import random
    pixels = [(random.randint(80, 120), random.randint(60, 100), random.randint(40, 80))
              for _ in range(1024 * 1365)]
    large_img = Image.new("RGB", (1024, 1365))
    large_img.putdata(pixels)
    large_img.save(path, "PNG")
    return path


@pytest.fixture
def tiny_png(tmp_path):
    """Save a tiny PNG that should fail the size check."""
    path = tmp_path / "tiny.png"
    Image.new("RGB", (64, 64), color=(0, 0, 0)).save(path, "PNG")
    return path


@pytest.fixture
def verifier():
    """Create verifier without Gemini client (no Vision checks)."""
    return PortraitVerifier(gemini_client=None, min_size_kb=10)


# ---------------------------------------------------------------------------
# VerificationResult dataclass
# ---------------------------------------------------------------------------

class TestVerificationResult:
    def test_default_construction(self):
        r = VerificationResult(passed=True)
        assert r.passed is True
        assert r.checks == {}
        assert r.scores == {}
        assert r.failures == []
        assert r.warnings == []

    def test_failed_result(self):
        r = VerificationResult(
            passed=False,
            failures=["File too small"],
            warnings=["Gender check skipped"],
        )
        assert r.passed is False
        assert "File too small" in r.failures


# ---------------------------------------------------------------------------
# File size check
# ---------------------------------------------------------------------------

class TestCheckFileSize:
    def test_large_file_passes(self, portrait_png):
        assert PortraitVerifier.check_file_size(portrait_png, min_kb=10) is True

    def test_tiny_file_fails(self, tiny_png):
        assert PortraitVerifier.check_file_size(tiny_png, min_kb=300) is False

    def test_missing_file_returns_false(self, tmp_path):
        missing = tmp_path / "nonexistent.png"
        assert PortraitVerifier.check_file_size(missing) is False


# ---------------------------------------------------------------------------
# MD5 duplicate detection
# ---------------------------------------------------------------------------

class TestCheckMd5Unique:
    def test_no_duplicates_returns_empty_dict(self, tmp_path):
        path_a = tmp_path / "a.png"
        path_b = tmp_path / "b.png"
        Image.new("RGB", (10, 10), color=(255, 0, 0)).save(path_a)
        Image.new("RGB", (10, 10), color=(0, 255, 0)).save(path_b)

        result = PortraitVerifier.check_md5_unique([path_a, path_b])
        assert result == {}

    def test_identical_files_detected(self, tmp_path):
        path_a = tmp_path / "a.png"
        path_b = tmp_path / "b.png"
        img = Image.new("RGB", (10, 10), color=(255, 0, 0))
        img.save(path_a, "PNG")
        # Write exact same bytes to b
        path_b.write_bytes(path_a.read_bytes())

        result = PortraitVerifier.check_md5_unique([path_a, path_b])
        assert len(result) == 1  # one MD5 hash with duplicates

    def test_missing_files_skipped(self, tmp_path):
        missing = tmp_path / "missing.png"
        result = PortraitVerifier.check_md5_unique([missing])
        assert result == {}

    def test_empty_list_returns_empty(self):
        assert PortraitVerifier.check_md5_unique([]) == {}

    def test_single_file_no_duplicate(self, tmp_path):
        path_a = tmp_path / "a.png"
        Image.new("RGB", (10, 10), color=(0, 0, 255)).save(path_a)
        result = PortraitVerifier.check_md5_unique([path_a])
        assert result == {}


# ---------------------------------------------------------------------------
# Gender verification (no Vision API)
# ---------------------------------------------------------------------------

class TestVerifyGender:
    def test_unknown_gender_always_passes(self, verifier, sample_image):
        ok, confidence = verifier.verify_gender(sample_image, "unknown")
        assert ok is True
        assert confidence == 1.0

    def test_no_vision_client_passes_through(self, sample_image):
        """Without a Vision client, verify_gender should always return True."""
        v = PortraitVerifier(gemini_client=None)
        ok, confidence = v.verify_gender(sample_image, "male")
        assert ok is True


# ---------------------------------------------------------------------------
# Full verification run (no Vision client)
# ---------------------------------------------------------------------------

class TestRunFullVerification:
    def test_missing_file_fails(self, verifier, tmp_path, sample_subject):
        missing = tmp_path / "missing.png"
        result = verifier.run_full_verification(missing, sample_subject)
        assert result.passed is False
        assert any("not found" in f.lower() for f in result.failures)

    def test_small_file_fails_size_check(self, verifier, tiny_png, sample_subject):
        v = PortraitVerifier(gemini_client=None, min_size_kb=300)
        result = v.run_full_verification(tiny_png, sample_subject)
        assert result.passed is False
        assert result.checks.get("file_size") is False

    def test_ok_file_passes_without_vision(self, portrait_png, sample_subject):
        v = PortraitVerifier(gemini_client=None, min_size_kb=10)
        result = v.run_full_verification(portrait_png, sample_subject)
        assert result.passed is True
        assert result.checks.get("file_size") is True

    def test_vision_checks_skipped_without_client(self, portrait_png, sample_subject):
        v = PortraitVerifier(gemini_client=None, min_size_kb=10)
        result = v.run_full_verification(portrait_png, sample_subject)
        # Vision checks should be warnings, not failures
        assert "overlay_dates" not in result.checks
        assert "gender" not in result.checks
        assert any("skipped" in w.lower() for w in result.warnings)

    def test_returns_verification_result_type(self, portrait_png, sample_subject):
        v = PortraitVerifier(gemini_client=None, min_size_kb=10)
        result = v.run_full_verification(portrait_png, sample_subject)
        assert isinstance(result, VerificationResult)


# ---------------------------------------------------------------------------
# Sidecar metadata
# ---------------------------------------------------------------------------

class TestSidecar:
    def test_write_and_verify_sidecar_passes(self, portrait_png, sample_subject):
        """write_sidecar then verify_sidecar against same data should pass."""
        PortraitVerifier.write_sidecar(portrait_png, sample_subject)
        sidecar_path = portrait_png.with_suffix(".meta.json")
        assert sidecar_path.exists()
        ok, msg = PortraitVerifier.verify_sidecar(portrait_png, sample_subject)
        assert ok is True
        assert msg == ""

    def test_sidecar_detects_name_mismatch(self, portrait_png, sample_subject):
        """verify_sidecar fails when sidecar records a different name."""
        PortraitVerifier.write_sidecar(portrait_png, sample_subject)

        from portrait_generator.api.models import SubjectData
        different_subject = SubjectData(
            name="Marie Curie",
            birth_year=1867,
            era="19th Century",
        )
        ok, msg = PortraitVerifier.verify_sidecar(portrait_png, different_subject)
        assert ok is False
        assert "name" in msg.lower()

    def test_sidecar_detects_birth_year_mismatch(self, portrait_png, sample_subject):
        """verify_sidecar fails when birth year differs by more than 2."""
        PortraitVerifier.write_sidecar(portrait_png, sample_subject)

        from portrait_generator.api.models import SubjectData
        wrong_year_subject = SubjectData(
            name="Alan Turing",
            birth_year=1900,  # 12 year diff — should fail
            era="20th Century",
        )
        ok, msg = PortraitVerifier.verify_sidecar(portrait_png, wrong_year_subject)
        assert ok is False
        assert "birth" in msg.lower()

    def test_verify_sidecar_passes_when_no_sidecar_exists(self, portrait_png, sample_subject):
        """verify_sidecar returns (True, '') when sidecar file doesn't exist."""
        # Ensure no sidecar
        sidecar = portrait_png.with_suffix(".meta.json")
        if sidecar.exists():
            sidecar.unlink()
        ok, msg = PortraitVerifier.verify_sidecar(portrait_png, sample_subject)
        assert ok is True
        assert msg == ""

    def test_sidecar_written_as_valid_json(self, portrait_png, sample_subject):
        """Sidecar file must be parseable JSON with required keys."""
        import json
        PortraitVerifier.write_sidecar(portrait_png, sample_subject)
        sidecar_path = portrait_png.with_suffix(".meta.json")
        data = json.loads(sidecar_path.read_text())
        assert data["name"] == sample_subject.name
        assert data["birth_year"] == sample_subject.birth_year
        assert "subject_hash" in data
        assert "generation_timestamp" in data

    def test_run_full_verification_checks_sidecar(self, portrait_png, sample_subject):
        """run_full_verification includes sidecar check."""
        PortraitVerifier.write_sidecar(portrait_png, sample_subject)
        v = PortraitVerifier(gemini_client=None, min_size_kb=10)
        result = v.run_full_verification(portrait_png, sample_subject)
        assert "sidecar" in result.checks
        assert result.checks["sidecar"] is True

    def test_run_full_verification_fails_on_sidecar_mismatch(
        self, portrait_png, sample_subject, tmp_path
    ):
        """Sidecar recording wrong person causes verification failure."""
        from portrait_generator.api.models import SubjectData
        # Write sidecar for different person
        wrong_subject = SubjectData(
            name="Ada Lovelace", birth_year=1815, era="19th Century"
        )
        PortraitVerifier.write_sidecar(portrait_png, wrong_subject)
        v = PortraitVerifier(gemini_client=None, min_size_kb=10)
        result = v.run_full_verification(portrait_png, sample_subject)
        assert result.checks.get("sidecar") is False
        assert result.passed is False


# ---------------------------------------------------------------------------
# Vision API tests (require valid GOOGLE_API_KEY)
# ---------------------------------------------------------------------------

@_SKIP_NO_KEY
class TestVerifyOverlayDatesVision:
    """Tests that use real Gemini Vision API."""

    def test_verify_overlay_dates_with_vision(self, tmp_path, sample_subject):
        """Test OCR of dates in portrait overlay using real Vision API."""
        from portrait_generator.utils.gemini_client import GeminiImageClient

        client = GeminiImageClient(api_key=os.getenv("GOOGLE_API_KEY"))
        verifier = PortraitVerifier(gemini_client=client, min_size_kb=10)

        # Create an image with overlay text
        img = Image.new("RGB", (512, 682), color=(100, 80, 60))
        draw = ImageDraw.Draw(img)
        # Draw a simple overlay at bottom
        draw.rectangle([(0, 600), (512, 682)], fill=(0, 0, 0, 200))
        draw.text((10, 620), "Alan Turing", fill="white")
        draw.text((10, 645), "1912-1954", fill="white")

        path = tmp_path / "test_portrait.png"
        img.save(path, "PNG")

        # Just verify it doesn't crash (Vision may or may not parse the text perfectly)
        ok, msg = verifier.verify_overlay_dates(img, expected_birth=1912, expected_death=1954)
        assert isinstance(ok, bool)
        assert isinstance(msg, str)

    def test_verify_gender_with_vision(self, sample_image):
        """Test gender check with real Vision API — minimal image."""
        from portrait_generator.utils.gemini_client import GeminiImageClient

        client = GeminiImageClient(api_key=os.getenv("GOOGLE_API_KEY"))
        verifier = PortraitVerifier(gemini_client=client, min_size_kb=10)

        # With a plain color image, Vision may not identify gender — but shouldn't crash
        ok, confidence = verifier.verify_gender(sample_image, "male")
        assert isinstance(ok, bool)
        assert 0.0 <= confidence <= 1.0
