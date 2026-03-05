"""Wikipedia and Wikidata ground-truth verification for portrait subjects.

Fetches authoritative biographical data (gender, dates, photo) from free
public APIs to cross-validate and enrich Gemini-researched SubjectData.
"""

import logging
import re
import urllib.parse
from dataclasses import dataclass, field
from typing import List, Optional

import requests

logger = logging.getLogger(__name__)

# Wikidata gender entity IDs
_WIKIDATA_FEMALE = "Q6581072"
_WIKIDATA_MALE = "Q6581097"
_WIKIDATA_TRANS_FEMALE = "Q1052281"
_WIKIDATA_TRANS_MALE = "Q2449503"

_FEMALE_IDS = {_WIKIDATA_FEMALE, _WIKIDATA_TRANS_FEMALE}
_MALE_IDS = {_WIKIDATA_MALE, _WIKIDATA_TRANS_MALE}

_HEADERS = {
    "User-Agent": "PortraitGenerator/2.2.0 (https://github.com/davidlary/PortraitGenerator; educational use)"
}
_TIMEOUT = 10  # seconds


@dataclass
class GroundTruthResult:
    """Verified biographical facts from Wikipedia and Wikidata."""

    name: str
    gender: str = "unknown"          # "male" | "female" | "unknown"
    birth_year: Optional[int] = None
    death_year: Optional[int] = None
    wikipedia_url: Optional[str] = None
    photo_url: Optional[str] = None  # Direct image URL from Wikipedia thumbnail
    confidence: float = 0.0          # 0.0-1.0; 0.0 if not found at all
    source: str = "none"             # "wikipedia" | "wikidata" | "both" | "none"
    conflicts: List[str] = field(default_factory=list)


class GroundTruthVerifier:
    """Cross-validates Gemini-researched biographical data against Wikipedia/Wikidata."""

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def fetch(self, name: str) -> GroundTruthResult:
        """Fetch ground-truth biographical facts for a subject.

        Tries Wikipedia REST API first, then enriches with Wikidata SPARQL
        for structured gender and date data.

        Args:
            name: Subject's full name (e.g., "Eugenia Kalnay")

        Returns:
            GroundTruthResult with confidence=0.0 if nothing found.
        """
        result = GroundTruthResult(name=name)

        # Step 1: Wikipedia REST API
        wiki_data = self._fetch_wikipedia(name)
        if wiki_data:
            result.wikipedia_url = wiki_data.get("content_urls", {}).get("desktop", {}).get("page")
            result.photo_url = wiki_data.get("thumbnail", {}).get("source")
            # Parse years from description or extract
            birth, death = self._parse_years_from_wikipedia(wiki_data)
            if birth:
                result.birth_year = birth
                result.death_year = death
                result.confidence = 0.6
                result.source = "wikipedia"

        # Step 2: Wikidata SPARQL for structured gender + dates
        wikidata = self._fetch_wikidata(name)
        if wikidata:
            if wikidata.get("gender"):
                result.gender = wikidata["gender"]
                result.confidence = min(1.0, result.confidence + 0.3)

            if wikidata.get("birth_year") and not result.birth_year:
                result.birth_year = wikidata["birth_year"]
                result.death_year = wikidata.get("death_year")
                result.confidence = min(1.0, result.confidence + 0.2)
            elif wikidata.get("birth_year") and result.birth_year:
                # Both sources have dates — if they agree, boost confidence
                if abs(wikidata["birth_year"] - result.birth_year) <= 2:
                    result.confidence = min(1.0, result.confidence + 0.1)

            result.source = "both" if result.source == "wikipedia" else "wikidata"

        logger.info(
            f"Ground truth for '{name}': gender={result.gender}, "
            f"birth={result.birth_year}, death={result.death_year}, "
            f"confidence={result.confidence:.2f}, photo={'yes' if result.photo_url else 'no'}"
        )
        return result

    def cross_validate(self, subject_data, ground_truth: GroundTruthResult) -> List[str]:
        """Compare Gemini research output against Wikipedia/Wikidata facts.

        Args:
            subject_data: SubjectData from researcher.py
            ground_truth: GroundTruthResult from fetch()

        Returns:
            List of human-readable conflict descriptions (empty = no conflicts).
        """
        conflicts = []

        if ground_truth.confidence < 0.4:
            # Not enough confidence to flag conflicts
            return conflicts

        # Birth year check (tolerance: 2 years)
        if ground_truth.birth_year and subject_data.birth_year:
            diff = abs(ground_truth.birth_year - subject_data.birth_year)
            if diff > 2:
                conflicts.append(
                    f"Birth year mismatch: Gemini says {subject_data.birth_year}, "
                    f"Wikipedia says {ground_truth.birth_year} (diff={diff})"
                )

        # Death year check (tolerance: 2 years)
        if ground_truth.death_year and subject_data.death_year:
            diff = abs(ground_truth.death_year - subject_data.death_year)
            if diff > 2:
                conflicts.append(
                    f"Death year mismatch: Gemini says {subject_data.death_year}, "
                    f"Wikipedia says {ground_truth.death_year} (diff={diff})"
                )

        # Living/deceased status check
        if ground_truth.death_year and subject_data.death_year is None:
            conflicts.append(
                f"Gemini says subject is alive but Wikipedia records death in {ground_truth.death_year}"
            )
        if not ground_truth.death_year and ground_truth.birth_year and subject_data.death_year:
            # Wikipedia has no death year but Gemini says deceased
            conflicts.append(
                f"Gemini says subject died in {subject_data.death_year} but "
                f"Wikipedia shows no death record"
            )

        # Gender check
        gemini_gender = getattr(subject_data, "gender", "unknown")
        if (
            ground_truth.gender != "unknown"
            and gemini_gender != "unknown"
            and ground_truth.gender != gemini_gender
        ):
            conflicts.append(
                f"Gender mismatch: Gemini says '{gemini_gender}', "
                f"Wikidata says '{ground_truth.gender}'"
            )

        return conflicts

    def enrich_subject_data(self, subject_data, ground_truth: GroundTruthResult):
        """Return enriched SubjectData using Wikipedia/Wikidata where more reliable.

        Args:
            subject_data: Original SubjectData from researcher.py
            ground_truth: GroundTruthResult from fetch()

        Returns:
            New SubjectData instance with Wikipedia-verified data where applicable.
        """
        if ground_truth.confidence < 0.5:
            # Not confident enough to override
            return subject_data

        # Build updated fields
        updates = {}

        # Override dates when Wikipedia confidence is high enough
        if ground_truth.birth_year and ground_truth.confidence >= 0.7:
            updates["birth_year"] = ground_truth.birth_year
            if ground_truth.death_year is not None:
                updates["death_year"] = ground_truth.death_year

        # Always set gender from Wikidata if known
        if ground_truth.gender != "unknown":
            updates["gender"] = ground_truth.gender

        # Add Wikipedia photo URL to reference_sources with special prefix
        updated_sources = list(subject_data.reference_sources)
        if ground_truth.photo_url:
            photo_entry = f"WIKIPEDIA_PHOTO:{ground_truth.photo_url}"
            if photo_entry not in updated_sources:
                updated_sources.insert(0, photo_entry)  # front of list = highest priority
                updates["reference_sources"] = updated_sources

        if ground_truth.wikipedia_url:
            wiki_entry = f"WIKIPEDIA:{ground_truth.wikipedia_url}"
            if wiki_entry not in updated_sources and "reference_sources" not in updates:
                updated_sources.insert(0 if not ground_truth.photo_url else 1, wiki_entry)
                updates["reference_sources"] = updated_sources

        if not updates:
            return subject_data

        return subject_data.model_copy(update=updates)

    # ------------------------------------------------------------------ #
    # Private: Wikipedia REST API                                          #
    # ------------------------------------------------------------------ #

    def _fetch_wikipedia(self, name: str) -> Optional[dict]:
        """Fetch page summary from Wikipedia REST API."""
        encoded = urllib.parse.quote(name.replace(" ", "_"))
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded}"
        try:
            resp = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("type") == "disambiguation":
                    logger.debug(f"Wikipedia disambiguation page for '{name}'")
                    return None
                return data
            elif resp.status_code == 404:
                # Try with different name formatting
                return self._fetch_wikipedia_fallback(name)
            else:
                logger.debug(f"Wikipedia returned {resp.status_code} for '{name}'")
                return None
        except Exception as e:
            logger.debug(f"Wikipedia fetch failed for '{name}': {e}")
            return None

    def _fetch_wikipedia_fallback(self, name: str) -> Optional[dict]:
        """Try Wikipedia search API when direct lookup fails."""
        url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + urllib.parse.quote(
            name.replace(" ", "_").replace("-", "_")
        )
        try:
            resp = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT)
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
        return None

    def _parse_years_from_wikipedia(self, data: dict) -> tuple[Optional[int], Optional[int]]:
        """Extract birth and death years from Wikipedia description or extract."""
        # Try description field first (e.g., "French botanist (1767–1845)")
        text = data.get("description", "") + " " + data.get("extract", "")[:500]

        # Pattern: (1767–1845) or (1767-1845) or born 1767
        patterns = [
            r'\((\d{4})\s*[–\-]\s*(\d{4})\)',      # (1767–1845)
            r'\(born\s+(\d{4})\)',                   # (born 1767)
            r'born.*?(\d{4}).*?died.*?(\d{4})',      # born ... died ...
            r'(\d{4})\s*[–\-]\s*(\d{4})',           # 1767–1845 anywhere
        ]

        for pattern in patterns:
            m = re.search(pattern, text)
            if m:
                try:
                    birth = int(m.group(1))
                    death = int(m.group(2)) if m.lastindex >= 2 else None
                    if 1000 <= birth <= 2100:
                        return birth, death
                except (ValueError, IndexError):
                    continue

        return None, None

    # ------------------------------------------------------------------ #
    # Private: Wikidata SPARQL                                             #
    # ------------------------------------------------------------------ #

    def _fetch_wikidata(self, name: str) -> Optional[dict]:
        """Fetch structured data (gender, birth, death) from Wikidata SPARQL."""
        sparql = self._build_sparql(name)
        url = "https://query.wikidata.org/sparql"
        try:
            resp = requests.get(
                url,
                params={"format": "json", "query": sparql},
                headers=_HEADERS,
                timeout=_TIMEOUT,
            )
            if resp.status_code != 200:
                logger.debug(f"Wikidata returned {resp.status_code} for '{name}'")
                return None

            results = resp.json().get("results", {}).get("bindings", [])
            if not results:
                return None

            return self._parse_wikidata_result(results[0])

        except Exception as e:
            logger.debug(f"Wikidata fetch failed for '{name}': {e}")
            return None

    def _build_sparql(self, name: str) -> str:
        """Build SPARQL query to fetch gender and dates for a person by name."""
        # Escape name for SPARQL
        safe_name = name.replace('"', '\\"').replace("\\", "\\\\")
        # Include both ?gender (entity URI) and ?genderLabel (English label from label service)
        return f"""
SELECT ?person ?gender ?genderLabel ?birth ?death WHERE {{
  ?person rdfs:label "{safe_name}"@en .
  ?person wdt:P31 wd:Q5 .
  OPTIONAL {{ ?person wdt:P21 ?gender . }}
  OPTIONAL {{ ?person wdt:P569 ?birth . }}
  OPTIONAL {{ ?person wdt:P570 ?death . }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}}
LIMIT 1
"""

    def _parse_wikidata_result(self, binding: dict) -> dict:
        """Parse a single Wikidata SPARQL result binding into a simple dict."""
        result: dict = {}

        # Gender — try label first, fall back to entity URI comparison
        gender_label = binding.get("genderLabel", {}).get("value", "").lower()
        gender_uri = binding.get("gender", {}).get("value", "")

        if "female" in gender_label or "woman" in gender_label:
            result["gender"] = "female"
        elif "male" in gender_label or "man" in gender_label:
            result["gender"] = "male"
        elif gender_uri:
            # Compare entity IDs directly (e.g., "Q6581072" at end of URI)
            entity_id = gender_uri.rstrip("/").rsplit("/", 1)[-1]
            if entity_id in _FEMALE_IDS:
                result["gender"] = "female"
            elif entity_id in _MALE_IDS:
                result["gender"] = "male"

        # Birth year
        birth_val = binding.get("birth", {}).get("value", "")
        if birth_val:
            m = re.search(r"(\d{4})", birth_val)
            if m:
                result["birth_year"] = int(m.group(1))

        # Death year
        death_val = binding.get("death", {}).get("value", "")
        if death_val:
            m = re.search(r"(\d{4})", death_val)
            if m:
                result["death_year"] = int(m.group(1))

        return result
