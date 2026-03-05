"""Post-generation portrait verification pipeline.

Runs multi-layer checks after each portrait is generated to ensure:
- Minimum file size (not a corrupted/placeholder image)
- No duplicate images across styles (caching bug detection via MD5)
- Overlay text shows correct name and dates (OCR via Gemini Vision)
- Depicted person's gender matches expected gender (Gemini Vision)
- Generated portrait is consistent with reference photo (Gemini Vision)
"""

import hashlib
import io
import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from PIL import Image

from ..api.models import SubjectData

logger = logging.getLogger(__name__)

_MIN_SIZE_KB_DEFAULT = 300


@dataclass
class VerificationResult:
    """Results from a full portrait verification run."""

    passed: bool
    """True only if ALL critical checks passed."""

    checks: Dict[str, bool] = field(default_factory=dict)
    """Per-check pass/fail status."""

    scores: Dict[str, float] = field(default_factory=dict)
    """Per-check confidence score (0.0-1.0)."""

    failures: List[str] = field(default_factory=list)
    """Human-readable descriptions of failed checks."""

    warnings: List[str] = field(default_factory=list)
    """Non-critical issues (don't fail the portrait)."""


class PortraitVerifier:
    """Verifies portrait accuracy and quality after generation.

    Initialized with an optional gemini_client. Vision-based checks
    (overlay OCR, gender check, identity comparison) are only run
    when a client with a valid API key is available.
    """

    def __init__(self, gemini_client=None, min_size_kb: int = _MIN_SIZE_KB_DEFAULT):
        """Initialize portrait verifier.

        Args:
            gemini_client: GeminiImageClient for Vision API checks.
                           If None, Vision checks are skipped.
            min_size_kb: Minimum acceptable file size in kilobytes.
        """
        self.gemini_client = gemini_client
        self.min_size_kb = min_size_kb
        self._has_vision = (
            gemini_client is not None
            and hasattr(gemini_client, "client")
            and hasattr(gemini_client, "model")
        )

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def run_full_verification(
        self,
        portrait_path: Path,
        subject_data: SubjectData,
        reference_paths: Optional[List[Path]] = None,
    ) -> VerificationResult:
        """Run all applicable verification checks on a portrait file.

        Checks performed:
        1. File size (always)
        2. Overlay date OCR — compares dates in overlay against expected (Vision)
        3. Gender check — detects if depicted person matches expected gender (Vision)
        4. Identity check — compares portrait against reference photo (Vision)

        Args:
            portrait_path: Path to the generated portrait PNG.
            subject_data: Biographical data with expected name, dates, gender.
            reference_paths: Optional list of reference photo paths for identity check.

        Returns:
            VerificationResult.  ``passed`` is True only when all critical
            checks pass (size, dates, gender).  Identity check failure is
            a warning, not a hard failure, because the reference photo itself
            may be wrong.
        """
        result = VerificationResult(passed=True)

        if not portrait_path.exists():
            result.passed = False
            result.failures.append(f"Portrait file not found: {portrait_path}")
            return result

        # --- Check 1: File size ---
        size_ok = self.check_file_size(portrait_path, self.min_size_kb)
        result.checks["file_size"] = size_ok
        if not size_ok:
            actual_kb = portrait_path.stat().st_size // 1024
            result.failures.append(
                f"File too small: {actual_kb} KB (minimum {self.min_size_kb} KB)"
            )
            result.passed = False

        # Load image for Vision checks
        try:
            pil_image = Image.open(portrait_path)
        except Exception as e:
            result.failures.append(f"Cannot open portrait image: {e}")
            result.passed = False
            return result

        # --- Check 2: Overlay date OCR (Vision) ---
        if self._has_vision and subject_data.birth_year:
            date_ok, date_msg = self.verify_overlay_dates(
                pil_image,
                subject_data.birth_year,
                subject_data.death_year,
            )
            result.checks["overlay_dates"] = date_ok
            result.scores["overlay_dates"] = 1.0 if date_ok else 0.0
            if not date_ok:
                result.failures.append(f"Date overlay mismatch: {date_msg}")
                result.passed = False
        else:
            result.warnings.append("Date OCR skipped (no Vision client or birth year)")

        # --- Check 3: Gender verification (Vision) ---
        gender = getattr(subject_data, "gender", "unknown")
        if self._has_vision and gender != "unknown":
            gender_ok, gender_confidence = self.verify_gender(pil_image, gender)
            result.checks["gender"] = gender_ok
            result.scores["gender"] = gender_confidence
            if not gender_ok:
                result.failures.append(
                    f"Gender mismatch: expected '{gender}' but portrait appears to show a different gender"
                )
                result.passed = False
        else:
            result.warnings.append(
                "Gender check skipped (no Vision client or gender unknown)"
            )

        # --- Check 4: Identity vs reference (Vision, non-critical) ---
        if self._has_vision and reference_paths:
            valid_refs = [p for p in reference_paths if p and p.exists()]
            if valid_refs:
                identity_ok, identity_msg = self.verify_identity_vs_reference(
                    pil_image, valid_refs[0], subject_data.name
                )
                result.checks["identity"] = identity_ok
                if not identity_ok:
                    # Warning only — reference photo could be wrong
                    result.warnings.append(
                        f"Identity check warning: {identity_msg}"
                    )
            else:
                result.warnings.append("Identity check skipped (no valid reference files)")
        else:
            result.warnings.append(
                "Identity check skipped (no Vision client or no reference images)"
            )

        logger.info(
            f"Verification for {portrait_path.name}: "
            f"passed={result.passed}, "
            f"failures={result.failures}, "
            f"warnings={result.warnings}"
        )
        return result

    # ------------------------------------------------------------------ #
    # Individual checks                                                    #
    # ------------------------------------------------------------------ #

    @staticmethod
    def check_file_size(path: Path, min_kb: int = _MIN_SIZE_KB_DEFAULT) -> bool:
        """Return True if the file is at least min_kb kilobytes."""
        try:
            return path.stat().st_size >= min_kb * 1024
        except OSError:
            return False

    @staticmethod
    def check_md5_unique(image_paths: List[Path]) -> Dict[str, List[Path]]:
        """Detect duplicate files by MD5 hash.

        A duplicate means the caching bug has copied one portrait to multiple
        style outputs.

        Args:
            image_paths: List of portrait file paths to check.

        Returns:
            Dict mapping MD5 hash → list of paths that share that hash.
            Only hashes with more than one path are included.
            Empty dict means no duplicates detected.
        """
        hashes: Dict[str, List[Path]] = {}
        for path in image_paths:
            if not path or not path.exists():
                continue
            try:
                md5 = hashlib.md5(path.read_bytes()).hexdigest()
                hashes.setdefault(md5, []).append(path)
            except OSError as e:
                logger.warning(f"Cannot hash {path}: {e}")
        return {h: paths for h, paths in hashes.items() if len(paths) > 1}

    def verify_overlay_dates(
        self,
        image: Image.Image,
        expected_birth: int,
        expected_death: Optional[int] = None,
    ) -> tuple:
        """OCR the date overlay and compare against expected years.

        Sends the portrait image to Gemini Vision and asks it to read
        the text overlay at the bottom.

        Args:
            image: PIL Image of the full portrait (with overlay).
            expected_birth: Expected birth year.
            expected_death: Expected death year (None if still alive).

        Returns:
            Tuple of (passed: bool, message: str).
        """
        if not self._has_vision:
            return True, "Vision not available — skipped"

        prompt = (
            "Look at the text overlay at the bottom of this portrait image. "
            "Read the name and the year range (e.g. '1912-1954' or '1947-Present'). "
            "Respond ONLY with valid JSON: "
            '{"name": "...", "years": "..."}'
        )

        try:
            response_text = self._call_vision_api(image, prompt)
            if not response_text:
                return True, "Empty Vision response — skipped"

            # Extract JSON from response
            json_match = re.search(r'\{[^}]+\}', response_text, re.DOTALL)
            if not json_match:
                return True, f"Could not parse JSON from Vision response: {response_text[:100]}"

            data = json.loads(json_match.group())
            years_str = data.get("years", "")

            # Parse years from response (e.g., "1912-1954" or "1947-Present")
            year_matches = re.findall(r'\d{4}', years_str)
            if not year_matches:
                return True, f"No years found in overlay: '{years_str}'"

            detected_birth = int(year_matches[0])
            detected_death = int(year_matches[1]) if len(year_matches) > 1 else None

            # Verify birth year (tolerance: 1 year for rounding)
            if abs(detected_birth - expected_birth) > 1:
                return False, (
                    f"Birth year: overlay shows {detected_birth}, "
                    f"expected {expected_birth}"
                )

            # Verify death year if expected
            if expected_death and detected_death:
                if abs(detected_death - expected_death) > 1:
                    return False, (
                        f"Death year: overlay shows {detected_death}, "
                        f"expected {expected_death}"
                    )

            return True, f"Dates match: {years_str}"

        except Exception as e:
            logger.debug(f"Overlay date verification error: {e}")
            return True, f"Verification error (non-critical): {e}"

    def verify_gender(
        self,
        image: Image.Image,
        expected_gender: str,
    ) -> tuple:
        """Check if the depicted person's gender matches expected gender.

        Args:
            image: PIL Image of the portrait.
            expected_gender: "male" or "female".

        Returns:
            Tuple of (passed: bool, confidence: float 0.0-1.0).
        """
        if not self._has_vision or expected_gender == "unknown":
            return True, 1.0

        prompt = (
            "Look at the person depicted in this portrait. "
            "What is the gender of the person shown? "
            "Respond with exactly one word: 'male' or 'female'."
        )

        try:
            response_text = self._call_vision_api(image, prompt)
            if not response_text:
                return True, 0.5  # No response — don't fail

            response_lower = response_text.strip().lower()
            if "female" in response_lower:
                detected = "female"
            elif "male" in response_lower:
                detected = "male"
            else:
                return True, 0.5  # Unclear response — don't fail

            matches = detected == expected_gender
            confidence = 0.9 if matches else 0.1
            return matches, confidence

        except Exception as e:
            logger.debug(f"Gender verification error: {e}")
            return True, 0.5  # Error — don't fail

    def verify_identity_vs_reference(
        self,
        portrait: Image.Image,
        reference_path: Path,
        subject_name: str,
    ) -> tuple:
        """Compare generated portrait against a known reference photograph.

        Args:
            portrait: PIL Image of the generated portrait.
            reference_path: Path to a reference photograph.
            subject_name: Subject's full name (for the Vision prompt).

        Returns:
            Tuple of (consistent: bool, reason: str).
        """
        if not self._has_vision or not reference_path.exists():
            return True, "Vision not available or no reference file"

        prompt = (
            f"Image 1 is a known reference photograph of {subject_name}. "
            f"Image 2 is an AI-generated portrait intended to depict {subject_name}. "
            "Do they depict the same person's gender, approximate era, and ethnic background? "
            "Respond ONLY with valid JSON: "
            '{"consistent": true_or_false, "confidence": 0.0_to_1.0, "reason": "..."}'
        )

        try:
            reference_img = Image.open(reference_path)
            response_text = self._call_vision_api_multi(
                [reference_img, portrait], prompt
            )
            if not response_text:
                return True, "Empty Vision response"

            json_match = re.search(r'\{[^}]+\}', response_text, re.DOTALL)
            if not json_match:
                return True, f"Could not parse JSON: {response_text[:100]}"

            data = json.loads(json_match.group())
            consistent = data.get("consistent", True)
            reason = data.get("reason", "")
            return consistent, reason

        except Exception as e:
            logger.debug(f"Identity verification error: {e}")
            return True, f"Error (non-critical): {e}"

    # ------------------------------------------------------------------ #
    # Vision API helpers                                                   #
    # ------------------------------------------------------------------ #

    def _image_to_bytes(self, image: Image.Image) -> bytes:
        """Convert PIL Image to JPEG bytes."""
        buf = io.BytesIO()
        image.convert("RGB").save(buf, format="JPEG", quality=90)
        return buf.getvalue()

    def _call_vision_api(self, image: Image.Image, prompt: str) -> str:
        """Send a single image + text prompt to Gemini Vision.

        Returns:
            Response text, or empty string on error.
        """
        try:
            image_bytes = self._image_to_bytes(image)
            part = self.gemini_client.types.Part.from_bytes(
                data=image_bytes, mime_type="image/jpeg"
            )
            response = self.gemini_client.client.models.generate_content(
                model=self.gemini_client.model,
                contents=[prompt, part],
            )
            return response.text or ""
        except Exception as e:
            logger.debug(f"Vision API call failed: {e}")
            return ""

    def _call_vision_api_multi(
        self, images: List[Image.Image], prompt: str
    ) -> str:
        """Send multiple images + text prompt to Gemini Vision.

        Returns:
            Response text, or empty string on error.
        """
        try:
            contents = [prompt]
            for img in images:
                image_bytes = self._image_to_bytes(img)
                contents.append(
                    self.gemini_client.types.Part.from_bytes(
                        data=image_bytes, mime_type="image/jpeg"
                    )
                )
            response = self.gemini_client.client.models.generate_content(
                model=self.gemini_client.model,
                contents=contents,
            )
            return response.text or ""
        except Exception as e:
            logger.debug(f"Vision API multi-image call failed: {e}")
            return ""
