"""Caller-supplied, independently verified lifespan (since 2.10.0).

Why this exists
---------------
Before 2.10.0 the caption drawn on every portrait (the years line under the
name) came from PortraitGenerator's OWN auto-research (Gemini text research +
bare-name ground-truth cascade + ``data/verified_biographies.yaml``). Callers
that verify birth/death years themselves (the Portraits pipeline's
``VerifiedFacts``) had no way to pass them in, so the image caption and the
verified record were two unrelated sources of truth. An OCR audit of 3,385
paintings on 2026-10-09 found ~166 birth-year and ~48 death-year mismatches
and ~1,000 captions asserting a year the verified record says is unknown
(e.g. Arthur A. Few, verified 1939-2022, captioned "1975-Present").

A :class:`Lifespan` passed as ``generate(..., lifespan=...)`` is now the sole
source of the caption's years line; research still runs for identity, era,
appearance and the age-at-portrait estimate.

Caption forms (:meth:`Lifespan.caption_years`)
----------------------------------------------
=====================  ==========================  ==================
birth / death known    still_alive                 caption
=====================  ==========================  ==================
both                   (must not be True)          ``"1939-2022"``
birth only             True                        ``"1939-Present"``
birth only             False / None                ``"b. 1939"``
death only             (must not be True)          ``"d. 2022"``
neither                any                         ``None`` (no years line)
=====================  ==========================  ==================

Negative years are BCE and render exactly like
``SubjectData.formatted_years`` (``-460`` -> ``"460 BCE"``).
"""
from __future__ import annotations

import datetime as _dt
import re
from dataclasses import dataclass
from typing import Any, Mapping, Optional

# Plausibility bounds shared by the researcher (rejecting regex artefacts such
# as "20" from "20th century") and Lifespan.validate().
EARLIEST_PLAUSIBLE_YEAR = -5000
MAX_PLAUSIBLE_LIFESPAN_YEARS = 125

# Strings that mean "no verifiable value" in a record.
_UNKNOWN_TOKENS = frozenset({"", "unknown", "none", "null", "n/a", "na", "?", "-"})
# death_year strings that mean "still alive".
_LIVING_TOKENS = frozenset({"living", "alive", "present", "still alive"})
_TRUE_TOKENS = frozenset({"true", "yes", "y", "1"})
_FALSE_TOKENS = frozenset({"false", "no", "n", "0"})
_YEAR_STR_RE = re.compile(r"^(?P<num>[+-]?\d{1,4})(?:\.0+)?\s*(?P<era>BCE|BC|CE|AD)?$", re.IGNORECASE)


def current_year() -> int:
    """The current calendar year (UTC)."""
    return _dt.datetime.now(_dt.timezone.utc).year


def plausible_year(year: Optional[int]) -> bool:
    """True iff ``year`` is an int in ``[EARLIEST_PLAUSIBLE_YEAR, current year]``.

    ``bool`` is rejected even though it subclasses ``int``.
    """
    if year is None or isinstance(year, bool) or not isinstance(year, int):
        return False
    return EARLIEST_PLAUSIBLE_YEAR <= year <= current_year()


def format_year(year: int) -> str:
    """``1939`` -> ``"1939"``; ``-460`` -> ``"460 BCE"`` (same as SubjectData.formatted_years)."""
    return f"{abs(year)} BCE" if year < 0 else str(year)


def _coerce_year(value: Any, field: str) -> Optional[int]:
    """Tolerant year coercion for :meth:`Lifespan.from_record`."""
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError(f"{field}: boolean {value!r} is not a year")
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if value.is_integer():
            return int(value)
        raise ValueError(f"{field}: non-integral year {value!r}")
    if isinstance(value, str):
        text = value.strip()
        if text.casefold() in _UNKNOWN_TOKENS:
            return None
        m = _YEAR_STR_RE.match(text)
        if not m:
            raise ValueError(f"{field}: cannot parse year from {value!r}")
        year = int(m.group("num"))
        era = (m.group("era") or "").upper()
        if era in ("BCE", "BC"):
            if year <= 0:
                raise ValueError(f"{field}: {value!r} mixes a sign with a BCE marker")
            year = -year
        return year
    raise ValueError(f"{field}: unsupported type {type(value).__name__} ({value!r})")


def _coerce_bool(value: Any) -> Optional[bool]:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        text = value.strip().casefold()
        if text in _UNKNOWN_TOKENS:
            return None
        if text in _TRUE_TOKENS:
            return True
        if text in _FALSE_TOKENS:
            return False
    raise ValueError(f"still_alive: cannot interpret {value!r} as a boolean")


@dataclass(frozen=True)
class Lifespan:
    """Verified birth/death years supplied by the caller.

    ``None`` means "not verifiable" and is never replaced by an estimate in
    any text the generator produces. ``still_alive`` is ``True`` only when the
    caller has verified the person is living (renders ``"-Present"``).
    """

    birth_year: Optional[int]
    death_year: Optional[int]
    still_alive: Optional[bool] = None

    def caption_years(self) -> Optional[str]:
        """The years line of the caption, or ``None`` when nothing is verifiable."""
        b, d = self.birth_year, self.death_year
        if b is not None and d is not None:
            return f"{format_year(b)}-{format_year(d)}"
        if b is not None:
            if self.still_alive:
                return f"{format_year(b)}-Present"
            return f"b. {format_year(b)}"
        if d is not None:
            return f"d. {format_year(d)}"
        return None

    def validate(self) -> "Lifespan":
        """Raise ``ValueError`` on an impossible lifespan; returns ``self``.

        Checks: each year is an int (not bool) within
        ``[EARLIEST_PLAUSIBLE_YEAR, current year]``; death >= birth; lifespan
        (or current age when ``still_alive``) <= ``MAX_PLAUSIBLE_LIFESPAN_YEARS``;
        ``still_alive`` True together with a death year is contradictory.
        """
        for field in ("birth_year", "death_year"):
            value = getattr(self, field)
            if value is not None and not plausible_year(value):
                raise ValueError(
                    f"{field}={value!r} is not a plausible year "
                    f"(expected an int in [{EARLIEST_PLAUSIBLE_YEAR}, {current_year()}])"
                )
        if self.still_alive is not None and not isinstance(self.still_alive, bool):
            raise ValueError(f"still_alive must be a bool or None, got {self.still_alive!r}")
        if self.still_alive and self.death_year is not None:
            raise ValueError(
                f"still_alive=True contradicts death_year={self.death_year}"
            )
        b, d = self.birth_year, self.death_year
        if b is not None and d is not None:
            if d < b:
                raise ValueError(f"death_year {d} precedes birth_year {b}")
            if d - b > MAX_PLAUSIBLE_LIFESPAN_YEARS:
                raise ValueError(
                    f"lifespan {b}..{d} = {d - b} years exceeds {MAX_PLAUSIBLE_LIFESPAN_YEARS}"
                )
        if b is not None and self.still_alive and current_year() - b > MAX_PLAUSIBLE_LIFESPAN_YEARS:
            raise ValueError(
                f"still_alive with birth_year {b} implies age {current_year() - b} "
                f"> {MAX_PLAUSIBLE_LIFESPAN_YEARS}"
            )
        return self

    @classmethod
    def from_record(cls, record: Mapping[str, Any]) -> "Lifespan":
        """Build (and validate) a Lifespan from a loosely typed mapping.

        Keys ``birth_year`` / ``death_year`` / ``still_alive`` (all optional).
        Years may be ints, integral floats, numeric strings (``"1930"``,
        ``"-460"``, ``"460 BCE"``); ``"Unknown"`` / ``""`` / ``None`` mean not
        verifiable. ``death_year`` of ``"living"`` / ``"alive"`` /
        ``"present"`` sets ``still_alive=True``. Anything else unparseable
        raises ``ValueError`` (never silently dropped).
        """
        if record is None:
            raise ValueError("lifespan record is None")
        birth = _coerce_year(record.get("birth_year"), "birth_year")
        raw_death = record.get("death_year")
        still_alive = _coerce_bool(record.get("still_alive"))
        if isinstance(raw_death, str) and raw_death.strip().casefold() in _LIVING_TOKENS:
            death = None
            if still_alive is False:
                raise ValueError(f"death_year={raw_death!r} contradicts still_alive=False")
            still_alive = True
        else:
            death = _coerce_year(raw_death, "death_year")
        return cls(birth_year=birth, death_year=death, still_alive=still_alive).validate()

    def apply_to(self, subject_data: Any) -> Any:
        """Return a copy of ``subject_data`` (``api.models.SubjectData``) whose
        caption comes solely from this lifespan.

        * ``caption_years`` = :meth:`caption_years`; ``lifespan_source`` = ``"caller"``.
        * ``death_year`` = the caller's value (``None`` allowed).
        * ``birth_year``: ``SubjectData.birth_year`` is a required int, so when
          the caller's birth is ``None`` the researched value is KEPT, used only
          for age-at-portrait arithmetic and never printed (every text path
          uses ``display_years``); otherwise the caller's value replaces it and
          ``birth_year_estimated`` is cleared.
        """
        self.validate()
        updates = {
            "death_year": self.death_year,
            "caption_years": self.caption_years(),
            "lifespan_source": "caller",
        }
        if self.birth_year is not None:
            updates["birth_year"] = self.birth_year
            updates["birth_year_estimated"] = False
        elif self.death_year is not None:
            researched = subject_data.birth_year
            if researched > self.death_year or self.death_year - researched > MAX_PLAUSIBLE_LIFESPAN_YEARS:
                # The researched birth cannot belong to the verified death year:
                # not even usable for age arithmetic.
                updates["birth_year_estimated"] = True
        return subject_data.model_copy(update=updates)


def coerce_lifespan(lifespan: Any) -> Optional[Lifespan]:
    """Accept a :class:`Lifespan`, a mapping for :meth:`Lifespan.from_record`,
    or None; return a validated Lifespan (or None).

    Used by the generators before any research/generation, so an invalid
    lifespan fails fast with ValueError (TypeError for an unsupported type).
    """
    if lifespan is None:
        return None
    if isinstance(lifespan, Lifespan):
        return lifespan.validate()
    if isinstance(lifespan, Mapping):
        return Lifespan.from_record(lifespan)
    raise TypeError(
        f"lifespan must be a Lifespan, a mapping or None, got {type(lifespan).__name__}"
    )


_TRAILING_PAREN_RE = re.compile(r"\s*\([^()]*\)\s*$")


def caption_display_name(name: str) -> str:
    """Return the name as it must be drawn on the caption bar.

    Strips every trailing parenthetical group: lifespan disambiguation
    suffixes ("Mike Fisher (1962-Present)"), alias/birth-name notes
    ('Robert Charles Geary ("Roy" Geary)', "bell hooks (born Gloria Jean
    Watkins)") and expansions ("Richard C. Thompson (Richard Charles
    Thompson)").  The full name is still used for research and filenames;
    only the caption shows the bare display name.  Never returns an empty
    string: a name that is nothing but parentheses is returned unchanged.
    """
    cleaned = name
    while True:
        new = _TRAILING_PAREN_RE.sub("", cleaned)
        if new == cleaned:
            break
        cleaned = new
    cleaned = cleaned.strip()
    return cleaned or name.strip()
