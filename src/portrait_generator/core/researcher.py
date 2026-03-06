"""Biographical researcher module for gathering subject data."""

import logging
import re
from typing import Optional

from ..api.models import SubjectData
from ..utils.ground_truth import GroundTruthVerifier

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Verified biographical data — locked-in facts that override Gemini research
# and ground truth lookups.  Add entries here for any subject whose birth/death
# year or gender was incorrect in automated research.
#
# Format: "Full Name": {"birth_year": int, "death_year": int|None, "gender": str}
# ---------------------------------------------------------------------------
_VERIFIED_BIOGRAPHY: dict = {
    # Chapter-Assimilation
    "Andrew Lorenc":  {"birth_year": 1951, "death_year": None, "gender": "male"},
    "David Lary":     {"birth_year": 1965, "death_year": None, "gender": "male"},
    "Eugenia Kalnay": {"birth_year": 1942, "death_year": None, "gender": "female"},
    "Mike Fisher":    {"birth_year": 1962, "death_year": None, "gender": "male"},
    "Roger Daley":    {"birth_year": 1941, "death_year": 1999, "gender": "male"},
    "Rudolf Kalman":  {"birth_year": 1930, "death_year": 2016, "gender": "male"},
    "Norbert Wiener": {"birth_year": 1894, "death_year": 1964, "gender": "male"},
    # Chapter-Simulating
    "John Pyle":      {"birth_year": 1950, "death_year": None, "gender": "male"},
    # Ancient/BCE subjects (prevent parsing errors)
    "Hippocrates":      {"birth_year": -460, "death_year": -370, "gender": "male"},
    "Theophrastus":     {"birth_year": -371, "death_year": -287, "gender": "male"},
    "Pedanius Dioscorides": {"birth_year": 40,  "death_year": 90,  "gender": "male"},
    "Avicenna":         {"birth_year": 980,  "death_year": 1037, "gender": "male"},
    "Hildegard von Bingen": {"birth_year": 1098, "death_year": 1179, "gender": "female"},
}


class BiographicalResearcher:
    """
    Researcher for gathering biographical data about historical figures.

    Uses Google Gemini text API to research subjects and extract
    relevant information for portrait generation.
    """

    def __init__(self, gemini_client):
        """
        Initialize BiographicalResearcher.

        Args:
            gemini_client: GeminiImageClient instance (uses text generation)
        """
        self.gemini_client = gemini_client
        logger.info("Initialized BiographicalResearcher")

    def research_subject(self, name: str) -> SubjectData:
        """
        Research biographical data for a subject.

        Args:
            name: Full name of the subject

        Returns:
            SubjectData with biographical information

        Raises:
            ValueError: If name is invalid
            RuntimeError: If research fails
        """
        if not name or not name.strip():
            raise ValueError("Subject name cannot be empty")

        logger.info(f"Researching subject: {name}")

        # Create research prompt
        prompt = self._create_research_prompt(name)

        try:
            # Use Gemini for research
            response = self._query_gemini(prompt)

            # Parse response into structured data
            subject_data = self._parse_research_response(name, response)

            # Cross-validate and enrich with multi-source ground truth cascade
            # (Wikipedia REST → Wikipedia Search → Wikidata → DBpedia → Gemini)
            try:
                # Pass Gemini client to enable Tier 5 (AI web search fallback)
                verifier = GroundTruthVerifier(gemini_client=self.gemini_client)
                ground_truth = verifier.fetch(name)
                # Always run cross-validate to log conflicts (even at low confidence)
                conflicts = verifier.cross_validate(subject_data, ground_truth)
                if conflicts:
                    logger.warning(
                        f"Ground truth conflicts for '{name}': {conflicts}"
                    )
                subject_data = verifier.enrich_subject_data(
                    subject_data, ground_truth
                )
                logger.info(
                    f"Ground truth enriched: gender={subject_data.gender}, "
                    f"birth={subject_data.birth_year}, "
                    f"sources=[{ground_truth.source}], "
                    f"confidence={ground_truth.confidence:.2f}"
                )
            except Exception as gt_err:
                logger.debug(f"Ground truth lookup skipped for '{name}': {gt_err}")

            # Apply verified biography overrides (highest authority — beats Gemini + ground truth)
            if name in _VERIFIED_BIOGRAPHY:
                bio = _VERIFIED_BIOGRAPHY[name]
                subject_data.birth_year = bio["birth_year"]
                subject_data.death_year = bio.get("death_year")
                subject_data.gender = bio.get("gender", subject_data.gender)
                logger.info(
                    f"Applied verified biography for '{name}': "
                    f"birth={bio['birth_year']}, death={bio.get('death_year')}, "
                    f"gender={bio.get('gender')}"
                )

            logger.info(
                f"Research complete: {subject_data.name} "
                f"({subject_data.formatted_years}, gender={subject_data.gender})"
            )

            return subject_data

        except Exception as e:
            logger.error(f"Research failed for {name}: {e}", exc_info=True)
            raise RuntimeError(f"Failed to research subject '{name}': {e}") from e

    def format_years(self, birth: int, death: Optional[int]) -> str:
        """
        Format birth and death years as a string.

        Args:
            birth: Birth year
            death: Death year or None if still alive

        Returns:
            Formatted string (e.g., "1912-1954" or "1947-Present")

        Raises:
            ValueError: If birth year is invalid
        """
        if death is not None and death < birth:
            raise ValueError("Death year cannot be before birth year")

        def _fmt(y: int) -> str:
            return f"{abs(y)} BCE" if y < 0 else str(y)

        if death:
            return f"{_fmt(birth)}-{_fmt(death)}"
        return f"{_fmt(birth)}-Present"

    def validate_data(self, data: SubjectData) -> bool:
        """
        Validate subject data for completeness.

        Args:
            data: SubjectData to validate

        Returns:
            True if data is valid and complete, False otherwise
        """
        if not data:
            logger.warning("Validation failed: Data is None")
            return False

        # Check required fields
        if not data.name or not data.name.strip():
            logger.warning("Validation failed: Name is empty")
            return False

        if not data.birth_year:
            logger.warning("Validation failed: Birth year missing")
            return False

        # Birth year can be negative for BCE dates (e.g., -460 for Hippocrates 460 BCE)
        if data.birth_year > 2100:
            logger.warning(f"Validation failed: Invalid birth year {data.birth_year}")
            return False

        if data.death_year is not None:
            # For BCE dates: birth_year=-460, death_year=-370 → -370 > -460 ✓
            # For CE dates: birth_year=1879, death_year=1955 → 1955 > 1879 ✓
            if data.death_year < data.birth_year:
                logger.warning("Validation failed: Death before birth")
                return False

            if data.death_year > 2100:
                logger.warning(f"Validation failed: Invalid death year {data.death_year}")
                return False

        if not data.era or not data.era.strip():
            logger.warning("Validation failed: Era is empty")
            return False

        logger.debug("Validation passed")
        return True

    def _create_research_prompt(self, name: str) -> str:
        """
        Create a research prompt for Gemini.

        Args:
            name: Subject name

        Returns:
            Research prompt string
        """
        prompt = f"""Research the following person and provide biographical information:

NAME: {name}

IMPORTANT: Identify the correct person by cross-checking multiple facts.
If this is a scientist or researcher, confirm the field and institution.
If the name could match multiple people, specify which one and why.

Please provide the following information in a structured format:

1. FULL NAME: The person's complete name
2. BIRTH YEAR: Year of birth (number only). If not publicly available, write "Not available" or provide best estimate.
3. DEATH YEAR: Year of death (number only, or "Present" if still alive)
4. GENDER: The person's gender (male, female, or unknown)
5. ERA: Historical era or time period (e.g., "Renaissance", "20th Century", "Medieval")
6. APPEARANCE NOTES: Physical characteristics, typical clothing style, notable features
   - List 3-5 specific details about their appearance
   - Include era-appropriate clothing and hairstyle
   - Mention any distinctive features
7. HISTORICAL CONTEXT: Brief description of their time period and cultural context
8. REFERENCE SOURCES: Key sources of information (e.g., "Historical records", "Contemporary accounts")

Format your response clearly with each section labeled.
Be historically accurate and specific.
"""
        return prompt

    def _query_gemini(self, prompt: str) -> str:
        """
        Query Gemini for research information.

        Uses the existing gemini_client's text generation capability for
        consistency and testability. The Flash model (Nano Banana 2) provides
        enhanced reasoning for accurate biographical extraction with low latency.

        Args:
            prompt: Research prompt

        Returns:
            Response text from Gemini

        Raises:
            RuntimeError: If query fails or returns empty response
        """
        try:
            # Reuse the existing client's text generation - avoids extra connection
            # overhead and keeps all API calls through one authenticated client
            response_text = self.gemini_client._query_model_text(prompt)

            if not response_text:
                raise RuntimeError("Empty response from Gemini")

            logger.debug(f"Gemini response length: {len(response_text)} chars")

            return response_text

        except RuntimeError:
            raise
        except Exception as e:
            logger.error(f"Gemini query failed: {e}", exc_info=True)
            raise RuntimeError(f"Gemini query failed: {e}") from e

    def _parse_research_response(self, name: str, response: str) -> SubjectData:
        """
        Parse Gemini response into SubjectData.

        Args:
            name: Original subject name
            response: Response text from Gemini

        Returns:
            Parsed SubjectData

        Raises:
            ValueError: If response cannot be parsed
        """
        try:
            # Extract birth year - lenient pattern handles "c. 460 BCE", "~1912", "circa 1098", etc.
            # Uses [^\n\d]*? to skip non-digit prefixes like "c.", "approximately", "~"
            birth_match = re.search(
                r"BIRTH YEAR[:\s]*\**[^\n\d]*?(\d+)", response, re.IGNORECASE
            )
            if birth_match:
                birth_year = int(birth_match.group(1))
                # Check for BCE context in the 30 chars after "BIRTH YEAR:" label
                ctx_start = birth_match.start()
                ctx_end = min(len(response), birth_match.end() + 20)
                birth_context = response[ctx_start:ctx_end]
                if re.search(r"\bBCE?\b", birth_context, re.IGNORECASE):
                    birth_year = -birth_year
                    logger.debug(f"Detected BCE birth year for {name}: {birth_year}")
            else:
                # No year extractable - use placeholder; ground truth cascade will correct
                if "not publicly available" in response.lower() or "not available" in response.lower() or "information not available" in response.lower():
                    logger.warning(f"Birth year not publicly available for {name}, using estimate: 1975")
                else:
                    logger.warning(
                        f"Could not extract birth year for '{name}' from Gemini response "
                        f"(no digit found after BIRTH YEAR label); using estimate 1975 — "
                        f"ground truth cascade will correct if actual year is known"
                    )
                birth_year = 1975

            # Extract death year - strict pattern to avoid matching embedded numbers
            # (e.g., "Not applicable, born in 1933" must NOT match 1933 as death year)
            # Only accepts: year immediately after "DEATH YEAR:" with optional short prefix
            # like "c.", "circa", "approximately", "~".
            death_year = None
            death_match = re.search(
                r"DEATH YEAR[:\s]*\**\s*(?:[cC]\.?\s*|circa\s+|approximately\s+|~\s*)?"
                r"(\d{3,4}|Present|present|living|alive|n/a|not\s+applicable)",
                response,
                re.IGNORECASE,
            )
            if death_match:
                death_str = death_match.group(1).strip()
                if re.match(r"^\d+$", death_str):
                    death_year = int(death_str)
                    # Check for BCE context
                    ctx_start = death_match.start()
                    ctx_end = min(len(response), death_match.end() + 20)
                    death_context = response[ctx_start:ctx_end]
                    if re.search(r"\bBCE?\b", death_context, re.IGNORECASE):
                        death_year = -death_year
                        logger.debug(f"Detected BCE death year for {name}: {death_year}")
                # "Present", "living", "alive", "n/a", "not applicable" → leave as None

            # Safety: if using the 1975 fallback birth year and death year precedes it,
            # the death year was likely extracted from surrounding text, not the actual
            # death date. Ground truth cascade will correct both years.
            if birth_year == 1975 and death_year is not None and death_year < birth_year:
                logger.warning(
                    f"Death year {death_year} precedes fallback birth year 1975 for '{name}'; "
                    f"clearing (ground truth will correct)"
                )
                death_year = None

            # Extract era - handle both inline and multi-line formats
            era_match = re.search(
                r"ERA[:\s]*\**\s*\n*\s*([^\n]+)", response, re.IGNORECASE
            )
            era = era_match.group(1).strip() if era_match else "Unknown Era"

            # Extract appearance notes
            appearance_notes = []
            appearance_section = re.search(
                r"APPEARANCE NOTES[:\s]+(.+?)(?=\n\d+\.|$)",
                response,
                re.IGNORECASE | re.DOTALL,
            )
            if appearance_section:
                notes_text = appearance_section.group(1)
                # Extract bullet points or lines
                for line in notes_text.split("\n"):
                    line = line.strip()
                    if line and not line.startswith(("BIRTH", "DEATH", "ERA", "HISTORICAL", "REFERENCE")):
                        # Remove leading bullets or numbers
                        line = re.sub(r"^[-*•\d.)\s]+", "", line).strip()
                        if line:
                            appearance_notes.append(line)

            # Extract historical context
            context_match = re.search(
                r"HISTORICAL CONTEXT[:\s]+([^\n]+(?:\n(?!\d+\.)[^\n]+)*)",
                response,
                re.IGNORECASE,
            )
            historical_context = (
                context_match.group(1).strip()
                if context_match
                else f"Historical figure from {era}"
            )

            # Extract gender
            gender = "unknown"
            gender_match = re.search(
                r"GENDER[:\s]*\**\s*\n*\s*(male|female|non-binary|unknown)",
                response,
                re.IGNORECASE,
            )
            if gender_match:
                gender_str = gender_match.group(1).lower()
                if "female" in gender_str or "woman" in gender_str:
                    gender = "female"
                elif "male" in gender_str or "man" in gender_str:
                    gender = "male"

            # Extract reference sources
            reference_sources = []
            sources_section = re.search(
                r"REFERENCE SOURCES[:\s]+(.+?)$",
                response,
                re.IGNORECASE | re.DOTALL,
            )
            if sources_section:
                sources_text = sources_section.group(1)
                for line in sources_text.split("\n"):
                    line = line.strip()
                    if line:
                        # Remove leading bullets or numbers
                        line = re.sub(r"^[-*•\d.)\s]+", "", line).strip()
                        if line:
                            reference_sources.append(line)

            # Create SubjectData
            subject_data = SubjectData(
                name=name,
                birth_year=birth_year,
                death_year=death_year,
                era=era,
                appearance_notes=appearance_notes[:5],  # Limit to 5
                historical_context=historical_context,
                reference_sources=reference_sources[:3],  # Limit to 3
                gender=gender,
            )

            # Validate
            if not self.validate_data(subject_data):
                raise ValueError("Parsed data failed validation")

            logger.debug(f"Parsed subject data: {subject_data.name}, gender={gender}")

            return subject_data

        except Exception as e:
            logger.error(f"Failed to parse research response: {e}", exc_info=True)
            raise ValueError(f"Failed to parse research response: {e}") from e

    def get_prompt_context(self, subject_data: SubjectData) -> dict:
        """
        Get context for prompt generation from subject data.

        Args:
            subject_data: SubjectData to extract context from

        Returns:
            Dictionary with prompt context
        """
        return {
            "name": subject_data.name,
            "era": subject_data.era,
            "birth_year": subject_data.birth_year,
            "death_year": subject_data.death_year or "Present",
            "years": subject_data.formatted_years,
            "appearance": ", ".join(subject_data.appearance_notes),
            "context": subject_data.historical_context,
        }
