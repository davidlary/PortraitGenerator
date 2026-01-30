"""Biographical researcher module for gathering subject data."""

import logging
import re
from typing import Optional

from ..api.models import SubjectData

logger = logging.getLogger(__name__)


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

            logger.info(
                f"Research complete: {subject_data.name} "
                f"({subject_data.formatted_years})"
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
        if birth < 0:
            raise ValueError("Birth year cannot be negative for CE dates")

        if death is not None and death < birth:
            raise ValueError("Death year cannot be before birth year")

        if death:
            return f"{birth}-{death}"
        return f"{birth}-Present"

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

        if data.birth_year < 0 or data.birth_year > 2100:
            logger.warning(f"Validation failed: Invalid birth year {data.birth_year}")
            return False

        if data.death_year is not None:
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

Please provide the following information in a structured format:

1. FULL NAME: The person's complete name
2. BIRTH YEAR: Year of birth (number only)
3. DEATH YEAR: Year of death (number only, or "Present" if still alive)
4. ERA: Historical era or time period (e.g., "Renaissance", "20th Century", "Medieval")
5. APPEARANCE NOTES: Physical characteristics, typical clothing style, notable features
   - List 3-5 specific details about their appearance
   - Include era-appropriate clothing and hairstyle
   - Mention any distinctive features
6. HISTORICAL CONTEXT: Brief description of their time period and cultural context
7. REFERENCE SOURCES: Key sources of information (e.g., "Historical records", "Contemporary accounts")

Format your response clearly with each section labeled.
Be historically accurate and specific.
"""
        return prompt

    def _query_gemini(self, prompt: str) -> str:
        """
        Query Gemini for research information.

        Note: This uses the text generation capability of Gemini.
        For now, this is a simplified implementation that would need
        to use the actual Gemini text API.

        Args:
            prompt: Research prompt

        Returns:
            Response text from Gemini

        Raises:
            RuntimeError: If query fails
        """
        try:
            # Import the Gemini client
            import google.genai as genai

            # Create client
            client = genai.Client(api_key=self.gemini_client.api_key)

            # Generate text response
            response = client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=prompt,
            )

            if not response or not response.text:
                raise RuntimeError("Empty response from Gemini")

            logger.debug(f"Gemini response length: {len(response.text)} chars")

            return response.text

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
            # Extract birth year
            birth_match = re.search(
                r"BIRTH YEAR[:\s]+(\d+)", response, re.IGNORECASE
            )
            if not birth_match:
                raise ValueError("Could not extract birth year from response")
            birth_year = int(birth_match.group(1))

            # Extract death year
            death_year = None
            death_match = re.search(
                r"DEATH YEAR[:\s]+(\d+|Present|present|living|alive)",
                response,
                re.IGNORECASE,
            )
            if death_match:
                death_str = death_match.group(1)
                if death_str.isdigit():
                    death_year = int(death_str)
                # Otherwise, leave as None (still alive)

            # Extract era
            era_match = re.search(
                r"ERA[:\s]+([^\n]+)", response, re.IGNORECASE
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
            )

            # Validate
            if not self.validate_data(subject_data):
                raise ValueError("Parsed data failed validation")

            logger.debug(f"Parsed subject data: {subject_data.name}")

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
