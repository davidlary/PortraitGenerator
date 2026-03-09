"""Multi-source ground-truth cascade for portrait subject biographical verification.

Fetches authoritative biographical data (gender, dates, photo) from a progressive
cascade of free public APIs to cross-validate and enrich Gemini-researched SubjectData.

Cascade tiers (stops as soon as birth_year + gender are both found with confidence >= 0.7):
  Tier 1: Wikipedia REST API (direct page summary — fast, free)
  Tier 2: Wikipedia Search API (when direct lookup returns 404 or disambiguation)
  Tier 3: Wikidata entity search + structured P21/P569/P570 claims (free SPARQL)
  Tier 4: DBpedia SPARQL (Wikipedia mirror with structured triples)
  Tier 5: Gemini web search (AI-powered, understands context; optional — requires client)
"""

import logging
import re
import urllib.parse
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import requests

from .http_cache import HTTP_CACHE

logger = logging.getLogger(__name__)

# Wikidata gender entity IDs
_WIKIDATA_FEMALE = "Q6581072"
_WIKIDATA_MALE = "Q6581097"
_WIKIDATA_TRANS_FEMALE = "Q1052281"
_WIKIDATA_TRANS_MALE = "Q2449503"

_FEMALE_IDS = {_WIKIDATA_FEMALE, _WIKIDATA_TRANS_FEMALE}
_MALE_IDS = {_WIKIDATA_MALE, _WIKIDATA_TRANS_MALE}

_HEADERS = {
    "User-Agent": "PortraitGenerator/2.8.0 (https://github.com/davidlary/PortraitGenerator; educational use)"
}
_TIMEOUT = 12  # seconds


@dataclass
class GroundTruthResult:
    """Verified biographical facts from multi-source cascade."""

    name: str
    gender: str = "unknown"          # "male" | "female" | "unknown"
    birth_year: Optional[int] = None
    death_year: Optional[int] = None
    wikipedia_url: Optional[str] = None
    photo_url: Optional[str] = None  # Direct image URL from Wikipedia thumbnail
    confidence: float = 0.0          # 0.0-1.0; 0.0 if not found at all
    source: str = "none"             # sources that contributed, comma-separated
    conflicts: List[str] = field(default_factory=list)


class GroundTruthVerifier:
    """Cross-validates Gemini-researched biographical data using a multi-source cascade.

    Cascade: Wikipedia REST → Wikipedia Search → Wikidata entity search → DBpedia → Gemini
    Stops as soon as birth_year + gender are confidently established.
    """

    def __init__(self, gemini_client: Optional[Any] = None):
        """Initialize the verifier.

        Args:
            gemini_client: Optional GeminiImageClient for Tier 5 (AI web search).
                           When provided, enables the Gemini biographical search tier.
        """
        self._gemini_client = gemini_client

    # ------------------------------------------------------------------ #
    # Private: cached HTTP helper                                          #
    # ------------------------------------------------------------------ #

    def _cached_get_json(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Optional[Any]:
        """GET a URL and return its JSON, using the local HTTP response cache.

        Checks the on-disk cache first (TTL 30 days).  On a cache miss, makes
        the real request and stores the successful response for future runs.
        Returns None on HTTP error or parse failure.
        """
        data = HTTP_CACHE.get_json(url, params)
        if data is not None:
            return data
        try:
            resp = requests.get(url, params=params, headers=_HEADERS, timeout=_TIMEOUT)
            if resp.status_code != 200:
                return None
            data = resp.json()
            HTTP_CACHE.put_json(url, params, data)
            return data
        except Exception as e:
            logger.debug(f"HTTP request failed for {url!r}: {e}")
            return None

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def fetch(self, name: str) -> GroundTruthResult:
        """Fetch ground-truth biographical facts using a progressive cascade.

        Tiers tried in order, stopping when birth_year + gender both found:
          1. Wikipedia REST API (direct summary lookup)
          2. Wikipedia Search API (fallback for disambiguation / missing pages)
          3. Wikidata entity search (wbsearchentities + structured claims)
          4. DBpedia SPARQL
          5. Gemini web search (if client provided)

        Args:
            name: Subject's full name (e.g., "Brian Tinsley")

        Returns:
            GroundTruthResult with confidence=0.0 if nothing found.
        """
        result = GroundTruthResult(name=name)
        sources: list[str] = []

        # ── Tier 1: Wikipedia REST API ────────────────────────────────────
        wiki_data = self._fetch_wikipedia_direct(name)
        if wiki_data and wiki_data.get("type") != "disambiguation":
            self._apply_wikipedia(result, wiki_data, sources)

        # ── Tier 2: Wikipedia Search API (when direct lookup insufficient) ─
        if not result.birth_year or result.confidence < 0.5:
            wiki_data2 = self._fetch_wikipedia_search(name)
            if wiki_data2 and wiki_data2.get("type") != "disambiguation":
                self._apply_wikipedia(result, wiki_data2, sources)

        # ── Tier 3: Wikidata entity search ───────────────────────────────
        if result.gender == "unknown" or not result.birth_year or result.confidence < 0.6:
            wikidata = self._fetch_wikidata_entity(name)
            if wikidata:
                self._apply_wikidata(result, wikidata, sources)

        # ── Tier 4: DBpedia ──────────────────────────────────────────────
        if result.gender == "unknown" or not result.birth_year or result.confidence < 0.65:
            dbpedia = self._fetch_dbpedia(name)
            if dbpedia:
                self._apply_dbpedia(result, dbpedia, sources)

        # ── Tier 5: Gemini web search (optional) ─────────────────────────
        if self._gemini_client and (not result.birth_year or result.confidence < 0.7):
            gemini_result = self._fetch_via_gemini(name)
            if gemini_result:
                self._apply_gemini_result(result, gemini_result, sources)

        result.source = ", ".join(sources) if sources else "none"
        logger.info(
            f"Ground truth for '{name}': gender={result.gender}, "
            f"birth={result.birth_year}, death={result.death_year}, "
            f"confidence={result.confidence:.2f}, sources=[{result.source}], "
            f"photo={'yes' if result.photo_url else 'no'}"
        )
        return result

    def cross_validate(self, subject_data, ground_truth: GroundTruthResult) -> List[str]:
        """Compare Gemini research output against ground-truth facts.

        Returns:
            List of human-readable conflict descriptions (empty = no conflicts).
        """
        conflicts = []

        if ground_truth.confidence < 0.4:
            return conflicts

        # Birth year check (tolerance: 2 years)
        if ground_truth.birth_year and subject_data.birth_year:
            diff = abs(ground_truth.birth_year - subject_data.birth_year)
            if diff > 2:
                conflicts.append(
                    f"Birth year mismatch: Gemini says {subject_data.birth_year}, "
                    f"ground truth says {ground_truth.birth_year} (diff={diff}, "
                    f"source={ground_truth.source})"
                )

        # Death year check (tolerance: 2 years)
        if ground_truth.death_year and subject_data.death_year:
            diff = abs(ground_truth.death_year - subject_data.death_year)
            if diff > 2:
                conflicts.append(
                    f"Death year mismatch: Gemini says {subject_data.death_year}, "
                    f"ground truth says {ground_truth.death_year}"
                )

        # Living/deceased status check
        if ground_truth.death_year and subject_data.death_year is None:
            conflicts.append(
                f"Gemini says subject is alive but ground truth records death in {ground_truth.death_year}"
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
                f"ground truth says '{ground_truth.gender}'"
            )

        return conflicts

    def enrich_subject_data(self, subject_data, ground_truth: GroundTruthResult):
        """Return enriched SubjectData using ground-truth where more reliable.

        Override logic:
          - Dates overridden if confidence >= 0.7 (standard)
          - Dates overridden if confidence >= 0.5 AND discrepancy > 10 years (obviously wrong)
          - Gender always overridden when ground truth is confident
          - Wikipedia photo URL always injected into reference_sources (for cascade Tier 3)
        """
        if ground_truth.confidence < 0.5:
            return subject_data

        updates = {}

        # Override dates — two conditions: standard confidence or large discrepancy
        if ground_truth.birth_year:
            should_override = ground_truth.confidence >= 0.7
            if not should_override and ground_truth.confidence >= 0.5 and subject_data.birth_year:
                year_diff = abs(ground_truth.birth_year - subject_data.birth_year)
                if year_diff > 10:
                    # Researcher was >10 years wrong — override even at moderate confidence
                    should_override = True
                    logger.warning(
                        f"Overriding birth year for '{subject_data.name}': "
                        f"Gemini={subject_data.birth_year}, ground_truth={ground_truth.birth_year} "
                        f"(diff={year_diff} years, confidence={ground_truth.confidence:.2f})"
                    )
            if should_override:
                updates["birth_year"] = ground_truth.birth_year
                if ground_truth.death_year is not None:
                    updates["death_year"] = ground_truth.death_year
                elif subject_data.death_year is not None and not ground_truth.death_year:
                    # Ground truth says alive, don't remove death year from researcher
                    pass

        # Always set gender from ground truth when known
        if ground_truth.gender != "unknown":
            updates["gender"] = ground_truth.gender

        # Add photo URL to reference_sources (used by reference finder Tier 3)
        updated_sources = list(subject_data.reference_sources)
        if ground_truth.photo_url:
            photo_entry = f"WIKIPEDIA_PHOTO:{ground_truth.photo_url}"
            if photo_entry not in updated_sources:
                updated_sources.insert(0, photo_entry)
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
    # Private: apply helpers                                               #
    # ------------------------------------------------------------------ #

    def _apply_wikipedia(self, result: GroundTruthResult, data: dict, sources: list) -> None:
        """Apply Wikipedia REST API data to result."""
        if "wikipedia" not in sources:
            sources.append("wikipedia")

        if not result.wikipedia_url:
            result.wikipedia_url = (
                data.get("content_urls", {}).get("desktop", {}).get("page")
            )
        if not result.photo_url:
            result.photo_url = (
                data.get("originalimage", {}).get("source")
                or data.get("thumbnail", {}).get("source")
            )

        birth, death = self._parse_years_from_wikipedia(data)
        if birth and (not result.birth_year or result.confidence < 0.5):
            result.birth_year = birth
            result.death_year = death
            result.confidence = max(result.confidence, 0.6)

    def _apply_wikidata(self, result: GroundTruthResult, data: dict, sources: list) -> None:
        """Apply Wikidata entity data to result."""
        if "wikidata" not in sources:
            sources.append("wikidata")

        if data.get("gender"):
            result.gender = data["gender"]
            result.confidence = min(1.0, result.confidence + 0.25)

        if data.get("birth_year"):
            if not result.birth_year:
                result.birth_year = data["birth_year"]
                result.death_year = data.get("death_year")
                result.confidence = min(1.0, result.confidence + 0.2)
            elif abs(data["birth_year"] - result.birth_year) <= 2:
                # Agreement between Wikipedia and Wikidata — high confidence
                result.confidence = min(1.0, result.confidence + 0.15)
            else:
                # Conflict — use Wikidata (typically more structured)
                logger.debug(
                    f"Birth year conflict: Wikipedia={result.birth_year}, "
                    f"Wikidata={data['birth_year']} for '{result.name}'"
                )
                result.birth_year = data["birth_year"]
                result.death_year = data.get("death_year")

        if data.get("photo_url") and not result.photo_url:
            result.photo_url = data["photo_url"]

    def _apply_dbpedia(self, result: GroundTruthResult, data: dict, sources: list) -> None:
        """Apply DBpedia data to result."""
        if "dbpedia" not in sources:
            sources.append("dbpedia")

        if data.get("gender") and result.gender == "unknown":
            result.gender = data["gender"]
            result.confidence = min(1.0, result.confidence + 0.15)

        if data.get("birth_year") and not result.birth_year:
            result.birth_year = data["birth_year"]
            result.death_year = data.get("death_year")
            result.confidence = min(1.0, result.confidence + 0.15)

    def _apply_gemini_result(self, result: GroundTruthResult, data: dict, sources: list) -> None:
        """Apply Gemini web search biographical data to result."""
        if "gemini" not in sources:
            sources.append("gemini")

        if data.get("gender") and result.gender == "unknown":
            result.gender = data["gender"]
            result.confidence = min(1.0, result.confidence + 0.2)

        if data.get("birth_year"):
            if not result.birth_year:
                result.birth_year = data["birth_year"]
                result.death_year = data.get("death_year")
                result.confidence = min(1.0, result.confidence + 0.2)
            elif abs(data["birth_year"] - result.birth_year) <= 2:
                result.confidence = min(1.0, result.confidence + 0.1)

    # ------------------------------------------------------------------ #
    # Private: Tier 1 — Wikipedia REST direct lookup                      #
    # ------------------------------------------------------------------ #

    def _fetch_wikipedia_direct(self, name: str) -> Optional[dict]:
        """Fetch page summary via Wikipedia REST API (direct page name lookup)."""
        encoded = urllib.parse.quote(name.replace(" ", "_"))
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded}"
        data = self._cached_get_json(url)
        if data is None:
            logger.debug(f"Wikipedia direct lookup: no data for '{name}'")
        return data

    # ------------------------------------------------------------------ #
    # Private: Tier 2 — Wikipedia Search API fallback                     #
    # ------------------------------------------------------------------ #

    def _fetch_wikipedia_search(self, name: str) -> Optional[dict]:
        """Use Wikipedia search API to find the most relevant article then fetch its summary."""
        search_url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "list": "search",
            "srsearch": name,
            "srnamespace": 0,
            "srlimit": 3,
            "format": "json",
        }
        try:
            search_data = self._cached_get_json(search_url, params)
            if not search_data:
                return None
            results = search_data.get("query", {}).get("search", [])
            for item in results:
                title = item.get("title", "")
                if self._name_matches(name, title):
                    encoded = urllib.parse.quote(title.replace(" ", "_"))
                    summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded}"
                    return self._cached_get_json(summary_url)
        except Exception as e:
            logger.debug(f"Wikipedia search failed for '{name}': {e}")
        return None

    def _name_matches(self, query: str, candidate: str) -> bool:
        """Heuristic: check if candidate Wikipedia title plausibly matches the query name."""
        q_parts = set(query.lower().split())
        c_lower = candidate.lower()
        # Require that the last name (typically most unique) appears in the candidate title
        last_name = query.split()[-1].lower().strip("(),-")
        return last_name in c_lower and len(q_parts & set(c_lower.split())) >= 1

    # ------------------------------------------------------------------ #
    # Private: Tier 3 — Wikidata entity search                            #
    # ------------------------------------------------------------------ #

    def _fetch_wikidata_entity(self, name: str) -> Optional[dict]:
        """Search Wikidata for the person by name and fetch structured biographical data.

        Uses wbsearchentities (text search) instead of exact-label SPARQL, which
        is much more robust for variations in name formatting.
        """
        # Step 1: Search for entity
        entity_id = self._wikidata_search_entity(name)
        if not entity_id:
            return None

        # Step 2: Fetch entity claims (P21=gender, P569=birth, P570=death, P18=image)
        return self._wikidata_get_claims(entity_id)

    def _wikidata_search_entity(self, name: str) -> Optional[str]:
        """Search Wikidata for a person entity by name. Returns entity ID (e.g., 'Q12345')."""
        params = {
            "action": "wbsearchentities",
            "search": name,
            "language": "en",
            "type": "item",
            "limit": 5,
            "format": "json",
        }
        try:
            data = self._cached_get_json("https://www.wikidata.org/w/api.php", params)
            if not data:
                return None
            for item in data.get("search", []):
                if self._name_matches(name, item.get("label", "")):
                    return item["id"]
        except Exception as e:
            logger.debug(f"Wikidata entity search failed for '{name}': {e}")
        return None

    def _wikidata_get_claims(self, entity_id: str) -> Optional[dict]:
        """Fetch P21 (gender), P569 (birth), P570 (death), P18 (image) for an entity."""
        params = {
            "action": "wbgetentities",
            "ids": entity_id,
            "props": "claims",
            "format": "json",
        }
        try:
            resp_data = self._cached_get_json("https://www.wikidata.org/w/api.php", params)
            if not resp_data:
                return None

            entity = resp_data.get("entities", {}).get(entity_id, {})
            claims = entity.get("claims", {})
            result = {}

            # P21 = gender
            if "P21" in claims:
                gender_id = (
                    claims["P21"][0]
                    .get("mainsnak", {})
                    .get("datavalue", {})
                    .get("value", {})
                    .get("id", "")
                )
                if gender_id in _FEMALE_IDS:
                    result["gender"] = "female"
                elif gender_id in _MALE_IDS:
                    result["gender"] = "male"

            # P569 = birth date
            if "P569" in claims:
                time_val = (
                    claims["P569"][0]
                    .get("mainsnak", {})
                    .get("datavalue", {})
                    .get("value", {})
                    .get("time", "")
                )
                m = re.search(r"[+-](\d{4})", time_val)
                if m:
                    result["birth_year"] = int(m.group(1))

            # P570 = death date
            if "P570" in claims:
                time_val = (
                    claims["P570"][0]
                    .get("mainsnak", {})
                    .get("datavalue", {})
                    .get("value", {})
                    .get("time", "")
                )
                m = re.search(r"[+-](\d{4})", time_val)
                if m:
                    result["death_year"] = int(m.group(1))

            # P18 = image filename
            if "P18" in claims:
                filename = (
                    claims["P18"][0]
                    .get("mainsnak", {})
                    .get("datavalue", {})
                    .get("value", "")
                )
                if filename:
                    result["photo_url"] = self._wikimedia_cdn_url(filename)

            return result if result else None

        except Exception as e:
            logger.debug(f"Wikidata entity claims failed for '{entity_id}': {e}")
        return None

    def _wikimedia_cdn_url(self, filename: str) -> str:
        """Convert Wikidata P18 filename to Wikimedia CDN URL."""
        import hashlib
        fn = filename.replace(" ", "_")
        md5 = hashlib.md5(fn.encode("utf-8")).hexdigest()
        encoded = urllib.parse.quote(fn, safe="")
        return f"https://upload.wikimedia.org/wikipedia/commons/{md5[0]}/{md5[0:2]}/{encoded}"

    # ------------------------------------------------------------------ #
    # Private: Tier 4 — DBpedia                                           #
    # ------------------------------------------------------------------ #

    def _fetch_dbpedia(self, name: str) -> Optional[dict]:
        """Fetch biographical data from DBpedia SPARQL endpoint."""
        safe_name = name.replace('"', '\\"').replace("\\", "\\\\")
        sparql = f"""
SELECT ?birth ?death ?gender WHERE {{
  {{
    ?person foaf:name "{safe_name}"@en .
  }} UNION {{
    ?person rdfs:label "{safe_name}"@en .
  }}
  ?person a dbo:Person .
  OPTIONAL {{ ?person dbo:birthYear ?birth . }}
  OPTIONAL {{ ?person dbo:birthDate ?birthDate . }}
  OPTIONAL {{ ?person dbo:deathYear ?death . }}
  OPTIONAL {{ ?person foaf:gender ?gender . }}
}}
LIMIT 2
"""
        dbpedia_params = {"format": "application/sparql-results+json", "query": sparql}
        try:
            resp_data = self._cached_get_json("https://dbpedia.org/sparql", dbpedia_params)
            if resp_data is None:
                return None

            bindings = resp_data.get("results", {}).get("bindings", [])
            if not bindings:
                return None

            row = bindings[0]
            result = {}

            birth_val = row.get("birth", {}).get("value", "") or row.get("birthDate", {}).get("value", "")
            if birth_val:
                m = re.search(r"(\d{4})", birth_val)
                if m:
                    result["birth_year"] = int(m.group(1))

            death_val = row.get("death", {}).get("value", "")
            if death_val:
                m = re.search(r"(\d{4})", death_val)
                if m:
                    result["death_year"] = int(m.group(1))

            gender_val = row.get("gender", {}).get("value", "").lower()
            if "female" in gender_val or "woman" in gender_val:
                result["gender"] = "female"
            elif "male" in gender_val or "man" in gender_val:
                result["gender"] = "male"

            return result if result else None

        except Exception as e:
            logger.debug(f"DBpedia fetch failed for '{name}': {e}")
        return None

    # ------------------------------------------------------------------ #
    # Private: Tier 5 — Gemini web search (optional)                      #
    # ------------------------------------------------------------------ #

    def _fetch_via_gemini(self, name: str) -> Optional[dict]:
        """Use Gemini with web search grounding to get authoritative birth year.

        Only called when client is available and other tiers couldn't establish
        birth_year with confidence >= 0.7.
        """
        if not self._gemini_client:
            return None

        prompt = (
            f"What year was {name} born? What year did they die (if deceased)? "
            f"What is their gender (male/female)? "
            f"Respond ONLY with JSON: "
            f'{{ "birth_year": <int or null>, "death_year": <int or null>, "gender": "<male|female|unknown>" }}'
        )
        try:
            response = self._gemini_client.query_with_grounding(prompt)
            if not response:
                return None
            # Parse JSON from response
            import json
            text = response.strip()
            # Extract JSON object
            m = re.search(r'\{[^}]+\}', text, re.DOTALL)
            if m:
                data = json.loads(m.group(0))
                result = {}
                if data.get("birth_year"):
                    result["birth_year"] = int(data["birth_year"])
                if data.get("death_year"):
                    result["death_year"] = int(data["death_year"])
                if data.get("gender") in ("male", "female"):
                    result["gender"] = data["gender"]
                return result if result else None
        except Exception as e:
            logger.debug(f"Gemini ground truth fetch failed for '{name}': {e}")
        return None

    # ------------------------------------------------------------------ #
    # Private: Wikipedia year parsing                                     #
    # ------------------------------------------------------------------ #

    def _parse_years_from_wikipedia(self, data: dict) -> tuple[Optional[int], Optional[int]]:
        """Extract birth and death years from Wikipedia description or extract."""
        text = data.get("description", "") + " " + data.get("extract", "")[:500]

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
