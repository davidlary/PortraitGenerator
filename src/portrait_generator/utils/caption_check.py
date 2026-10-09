"""Deterministic OCR check of a portrait's caption bar (since 2.10.0).

The caption (dark bar at the bottom: name line + optional years line) is drawn
by :class:`portrait_generator.core.overlay.TitleOverlayEngine`. This module
reads it back with Tesseract and compares it with what was intended, so a
wrong or placeholder year can never ship silently. Before 2.10.0 the only
overlay check was a fail-open Gemini Vision read compared against the same
research data that produced the caption (self-consistency, not truth).

OCR method (validated on all 3,385 Portraits-repo paintings, 2026-10-09)
------------------------------------------------------------------------
1. Crop the bottom :data:`CROP_FRACTIONS` [0] (17 %) of the image (the bar is
   15 % of the height by default); only when no year token is found, retry
   at 26 % and then 36 % (the bar grows for two-line names).
2. Grayscale, autocontrast, INVERT (black text on white), upscale x2 LANCZOS.
3. Tesseract ``--psm 6`` with per-word confidences (``image_to_data`` / TSV).
   If the minimum word confidence is below :data:`MIN_WORD_CONFIDENCE`, retry
   at x3 and keep the better read.
4. Years: :data:`YEAR_RANGE_RE` (``1939-2022``, ``460 BCE-370 BCE``,
   ``1947-Present``) or :data:`SINGLE_YEAR_RE` (``b. 1939`` / ``d. 2022``).
5. Name: NFKD accent strip, casefold, punctuation/space collapse, then
   ``difflib.SequenceMatcher`` ratio against the last text line before the
   years line (or the whole text when there are no years). Because long names
   wrap onto two lines, the best ratio over {last line, all lines before the
   years line} is used.

Verdict ``ok`` iff the years match exactly after normalisation (or, when no
years are expected, no year token is present) AND name similarity >=
:data:`NAME_SIMILARITY_THRESHOLD`.

Engine: ``pytesseract`` when importable and its binary runs, else the
``tesseract`` CLI via subprocess; neither -> :class:`CaptionCheckUnavailable`.
The binary is located via ``$TESSERACT_CMD``, then ``PATH``, then
:data:`TESSERACT_FALLBACK_PATHS`.
"""
from __future__ import annotations

import csv
import difflib
import io
import logging
import os
import re
import shutil
import subprocess
import unicodedata
from dataclasses import asdict, dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple, Union

from PIL import Image, ImageOps

logger = logging.getLogger(__name__)

CROP_FRACTIONS: Tuple[float, ...] = (0.17, 0.26, 0.36)
UPSCALE_FIRST = 2
UPSCALE_RETRY = 3
MIN_WORD_CONFIDENCE = 70.0
NAME_SIMILARITY_THRESHOLD = 0.75
TESSERACT_CONFIG = "--psm 6"
TESSERACT_TIMEOUT_S = 60
TESSERACT_FALLBACK_PATHS: Tuple[str, ...] = ("/opt/homebrew/bin/tesseract", "/usr/local/bin/tesseract")

YEAR_RANGE_RE = re.compile(r"\d{1,4}(?:\s*BCE)?\s*[-–—]\s*(?:Present|\d{1,4}(?:\s*BCE)?)", re.IGNORECASE)
SINGLE_YEAR_RE = re.compile(r"\b[bd]\.\s*\d{1,4}(?:\s*BCE)?", re.IGNORECASE)

ImageLike = Union[Image.Image, str, Path]


class CaptionCheckUnavailable(RuntimeError):
    """Neither pytesseract nor a working ``tesseract`` CLI is available."""


class CaptionMismatchError(RuntimeError):
    """The OCR'd caption does not match the intended name/years.

    ``str(exc)`` always starts with ``"CAPTION-MISMATCH:"``.
    """

    PREFIX = "CAPTION-MISMATCH:"

    def __init__(self, detail: str, verdict: Optional["CaptionVerdict"] = None):
        super().__init__(f"{self.PREFIX} {detail}")
        self.verdict = verdict


@dataclass(frozen=True)
class CaptionRead:
    """Raw OCR read of the caption bar."""

    text: str                      # all recognised lines, "\n"-joined
    lines: Tuple[str, ...]
    years: Optional[str]           # the year token as read (None if none found)
    years_line_index: Optional[int]
    min_confidence: float          # lowest per-word confidence (0 when no words)
    mean_confidence: float
    engine: str                    # "pytesseract" | "tesseract-cli"
    crop_fraction: float
    scale: int


@dataclass(frozen=True)
class CaptionVerdict:
    """Comparison of a :class:`CaptionRead` with the intended caption."""

    ok: bool
    expected_name: str
    expected_years: Optional[str]
    observed_text: str
    observed_years: Optional[str]
    name_similarity: float
    reason: str
    engine: str
    crop_fraction: float

    @property
    def status(self) -> str:
        return "ok" if self.ok else "mismatch"

    def as_sidecar(self) -> Dict[str, Optional[str]]:
        """The ``caption_check`` dict recorded in the portrait sidecar."""
        return {
            "status": self.status,
            "observed_text": self.observed_text,
            "observed_years": self.observed_years,
            "reason": self.reason,
        }

    def as_dict(self) -> Dict[str, object]:
        return asdict(self)


# --------------------------------------------------------------------------
# engine discovery
# --------------------------------------------------------------------------

def _tesseract_binary() -> Optional[str]:
    env = os.environ.get("TESSERACT_CMD")
    if env and Path(env).is_file() and os.access(env, os.X_OK):
        return env
    found = shutil.which("tesseract")
    if found:
        return found
    for cand in TESSERACT_FALLBACK_PATHS:
        if Path(cand).is_file() and os.access(cand, os.X_OK):
            return cand
    return None


@lru_cache(maxsize=1)
def _engine() -> Tuple[str, Optional[str]]:
    """(engine name, binary path). Cached per process; raises when unusable."""
    binary = _tesseract_binary()
    try:
        import pytesseract  # type: ignore

        if binary:
            pytesseract.pytesseract.tesseract_cmd = binary
        pytesseract.get_tesseract_version()
        return "pytesseract", binary
    except ImportError:
        logger.debug("pytesseract not importable; trying the tesseract CLI")
    except Exception as exc:  # binary missing / broken
        logger.debug(f"pytesseract unusable ({exc}); trying the tesseract CLI")
    if binary:
        try:
            subprocess.run([binary, "--version"], capture_output=True, check=True,
                           timeout=TESSERACT_TIMEOUT_S)
            return "tesseract-cli", binary
        except Exception as exc:
            raise CaptionCheckUnavailable(f"tesseract CLI at {binary} is not runnable: {exc}") from exc
    raise CaptionCheckUnavailable(
        "caption check unavailable: neither pytesseract (with a tesseract binary) nor the "
        "tesseract CLI was found (install tesseract, e.g. `brew install tesseract`, or set TESSERACT_CMD)"
    )


def caption_check_available() -> bool:
    """True iff an OCR engine is usable in this process."""
    try:
        _engine()
        return True
    except CaptionCheckUnavailable:
        return False


# --------------------------------------------------------------------------
# OCR
# --------------------------------------------------------------------------

@dataclass
class _Word:
    text: str
    conf: float
    key: Tuple[int, int, int]  # (block, paragraph, line)


@dataclass
class _Read:
    lines: List[str] = field(default_factory=list)
    confs: List[float] = field(default_factory=list)

    @property
    def min_conf(self) -> float:
        return min(self.confs) if self.confs else 0.0

    @property
    def mean_conf(self) -> float:
        return sum(self.confs) / len(self.confs) if self.confs else 0.0


def _rows_to_words(rows: Sequence[Dict[str, str]]) -> List[_Word]:
    words = []
    for row in rows:
        text = (row.get("text") or "").strip()
        try:
            conf = float(row.get("conf", -1))
        except (TypeError, ValueError):
            conf = -1.0
        if not text or conf < 0:
            continue
        key = (int(row.get("block_num", 0)), int(row.get("par_num", 0)), int(row.get("line_num", 0)))
        words.append(_Word(text, conf, key))
    return words


def _ocr_words(image: Image.Image) -> List[_Word]:
    engine, binary = _engine()
    if engine == "pytesseract":
        import pytesseract  # type: ignore

        data = pytesseract.image_to_data(
            image, config=TESSERACT_CONFIG, output_type=pytesseract.Output.DICT,
            timeout=TESSERACT_TIMEOUT_S,
        )
        n = len(data.get("text", []))
        rows = [{k: str(data[k][i]) for k in ("text", "conf", "block_num", "par_num", "line_num")}
                for i in range(n)]
        return _rows_to_words(rows)
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    proc = subprocess.run(
        [binary, "stdin", "stdout", *TESSERACT_CONFIG.split(), "tsv"],
        input=buf.getvalue(), capture_output=True, check=True, timeout=TESSERACT_TIMEOUT_S,
    )
    reader = csv.DictReader(io.StringIO(proc.stdout.decode("utf-8", "replace")), delimiter="\t",
                            quoting=csv.QUOTE_NONE)
    return _rows_to_words(list(reader))


def _prepare(crop: Image.Image, scale: int) -> Image.Image:
    g = ImageOps.autocontrast(crop.convert("L"))
    g = ImageOps.invert(g)
    return g.resize((g.width * scale, g.height * scale), Image.Resampling.LANCZOS)


def _ocr(crop: Image.Image, scale: int) -> _Read:
    words = _ocr_words(_prepare(crop, scale))
    lines: Dict[Tuple[int, int, int], List[str]] = {}
    for w in words:
        lines.setdefault(w.key, []).append(w.text)
    return _Read(lines=[" ".join(v) for v in lines.values()], confs=[w.conf for w in words])


def _find_years(lines: Sequence[str]) -> Tuple[Optional[str], Optional[int]]:
    for i, line in enumerate(lines):
        m = YEAR_RANGE_RE.search(line) or SINGLE_YEAR_RE.search(line)
        if m:
            return m.group(0).strip(), i
    return None, None


def _better(a: _Read, b: _Read) -> _Read:
    """Prefer a read that found a year token, then the higher mean confidence."""
    ya = _find_years(a.lines)[0] is not None
    yb = _find_years(b.lines)[0] is not None
    if ya != yb:
        return a if ya else b
    return a if a.mean_conf >= b.mean_conf else b


def _load(image_or_path: ImageLike) -> Image.Image:
    if isinstance(image_or_path, Image.Image):
        return image_or_path
    with Image.open(image_or_path) as im:
        im.load()
        return im.copy()


def read_caption(image_or_path: ImageLike) -> CaptionRead:
    """OCR the caption bar of a portrait (see module docstring for the method).

    Raises :class:`CaptionCheckUnavailable` when no OCR engine is usable.
    """
    engine, _ = _engine()
    image = _load(image_or_path)
    w, h = image.size
    result: Optional[CaptionRead] = None
    for frac in CROP_FRACTIONS:
        crop = image.crop((0, h - max(1, int(round(h * frac))), w, h))
        read, scale = _ocr(crop, UPSCALE_FIRST), UPSCALE_FIRST
        if read.min_conf < MIN_WORD_CONFIDENCE:
            retry = _ocr(crop, UPSCALE_RETRY)
            if _better(retry, read) is retry:
                read, scale = retry, UPSCALE_RETRY
        years, idx = _find_years(read.lines)
        result = CaptionRead(
            text="\n".join(read.lines), lines=tuple(read.lines), years=years,
            years_line_index=idx, min_confidence=read.min_conf, mean_confidence=read.mean_conf,
            engine=engine, crop_fraction=frac, scale=scale,
        )
        if years is not None:
            break
    assert result is not None  # CROP_FRACTIONS is non-empty
    return result


# --------------------------------------------------------------------------
# comparison
# --------------------------------------------------------------------------

def normalize_name(text: str) -> str:
    """NFKD accent strip, casefold, punctuation -> space, collapse spaces."""
    decomposed = unicodedata.normalize("NFKD", text or "")
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    folded = stripped.casefold()
    return " ".join(re.sub(r"[^\w]+|_", " ", folded).split())


def normalize_years(text: Optional[str]) -> Optional[str]:
    """Whitespace removed, any dash -> '-', casefolded (``"1939 – 2022"`` -> ``"1939-2022"``)."""
    if text is None:
        return None
    t = re.sub(r"[–—‒−]", "-", text)
    return re.sub(r"\s+", "", t).casefold()


def name_similarity(expected: str, candidate: str) -> float:
    a, b = normalize_name(expected), normalize_name(candidate)
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a, b).ratio()


def _name_candidates(read: CaptionRead) -> List[str]:
    lines = list(read.lines)
    if read.years_line_index is not None:
        before = lines[: read.years_line_index]
        # The years token may share a line with the name when tesseract merges them.
        same_line = lines[read.years_line_index].replace(read.years or "", " ").strip()
        cands = []
        if before:
            cands += [before[-1], " ".join(before)]
        if same_line:
            cands.append(same_line)
        return cands or [""]
    return [" ".join(lines)] + lines[-1:]


def compare(read: CaptionRead, expected_name: str, expected_years: Optional[str]) -> CaptionVerdict:
    """Pure comparison of a read with the intended caption (no OCR)."""
    sim = max((name_similarity(expected_name, c) for c in _name_candidates(read)), default=0.0)
    reasons = []
    exp_y, obs_y = normalize_years(expected_years), normalize_years(read.years)
    if expected_years is None:
        years_ok = read.years is None
        if not years_ok:
            reasons.append(f"no years line expected but OCR found {read.years!r}")
    else:
        years_ok = exp_y == obs_y
        if read.years is None:
            reasons.append(f"expected years {expected_years!r} but no year token was read")
        elif not years_ok:
            reasons.append(f"years read {read.years!r} != expected {expected_years!r}")
    name_ok = sim >= NAME_SIMILARITY_THRESHOLD
    if not name_ok:
        reasons.append(
            f"name similarity {sim:.2f} < {NAME_SIMILARITY_THRESHOLD} for expected {expected_name!r}"
        )
    ok = years_ok and name_ok
    reason = "; ".join(reasons) if reasons else (
        f"name similarity {sim:.2f}, years {'absent as expected' if expected_years is None else 'match'}"
    )
    return CaptionVerdict(
        ok=ok, expected_name=expected_name, expected_years=expected_years,
        observed_text=read.text, observed_years=read.years, name_similarity=round(sim, 4),
        reason=reason, engine=read.engine, crop_fraction=read.crop_fraction,
    )


def verify_caption(image_or_path: ImageLike, expected_name: str,
                   expected_years: Optional[str]) -> CaptionVerdict:
    """OCR the caption and compare it with ``expected_name`` / ``expected_years``.

    ``expected_years=None`` means the caption must have NO years token.
    Raises :class:`CaptionCheckUnavailable` when no OCR engine is usable.
    """
    if not expected_name or not expected_name.strip():
        raise ValueError("expected_name cannot be empty")
    return compare(read_caption(image_or_path), expected_name, expected_years)


def caption_gate(image: ImageLike, expected_name: str, expected_years: Optional[str], *,
                 enforce: bool, label: str = "") -> Dict[str, Optional[str]]:
    """Run :func:`verify_caption` for a generator and return the sidecar dict.

    * ok -> ``{"status": "ok", ...}``
    * mismatch -> raise :class:`CaptionMismatchError` when ``enforce`` (caller
      supplied a verified Lifespan), else log a WARNING and record ``"mismatch"``.
    * no OCR engine -> WARNING, ``{"status": "unavailable", ...}``.
    """
    where = f" [{label}]" if label else ""
    try:
        verdict = verify_caption(image, expected_name, expected_years)
    except CaptionCheckUnavailable as exc:
        logger.warning(f"Caption check unavailable{where}: {exc}")
        return {"status": "unavailable", "observed_text": None, "observed_years": None,
                "reason": str(exc)}
    if verdict.ok:
        logger.info(f"Caption check OK{where}: {verdict.reason}")
        return verdict.as_sidecar()
    detail = (f"{label + ': ' if label else ''}expected name={expected_name!r} "
              f"years={expected_years!r}; observed text={verdict.observed_text!r} "
              f"years={verdict.observed_years!r}; {verdict.reason}")
    if enforce:
        logger.error(f"{CaptionMismatchError.PREFIX} {detail}")
        raise CaptionMismatchError(detail, verdict)
    logger.warning(f"Caption check mismatch (not enforced: no caller lifespan){where}: {detail}")
    return verdict.as_sidecar()
