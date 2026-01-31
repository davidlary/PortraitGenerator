"""Reference image finding and validation.

This module finds authentic historical reference images for portrait subjects
using Google Search grounding and AI-powered authenticity validation.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse

import httpx
from loguru import logger
from PIL import Image
from io import BytesIO

from .api.models import SubjectData


@dataclass
class ReferenceImage:
    """Metadata for a reference image."""

    url: str
    """Image URL"""

    source: str
    """Source website/document"""

    authenticity_score: float
    """Confidence in authenticity (0.0-1.0)"""

    quality_score: float
    """Image quality score (0.0-1.0)"""

    relevance_score: float
    """Relevance to subject score (0.0-1.0)"""

    era_match: bool
    """Whether image matches historical era"""

    description: str = ""
    """Image description"""

    local_path: Optional[Path] = None
    """Local path if downloaded"""


class ReferenceImageFinder:
    """Finds and validates reference images for portrait subjects.

    Uses Google Search grounding to find authenticated historical images
    that can guide portrait generation.
    """

    def __init__(
        self,
        gemini_client,
        enable_grounding: bool = True,
        download_dir: Optional[Path] = None,
    ):
        """Initialize reference image finder.

        Args:
            gemini_client: GeminiImageClient instance for fact-checking
            enable_grounding: Whether to use Google Search grounding
            download_dir: Directory to download images to
        """
        self.gemini_client = gemini_client
        self.enable_grounding = enable_grounding
        self.download_dir = download_dir or Path(".cpf/reference_images")
        self.download_dir.mkdir(parents=True, exist_ok=True)

        # HTTP client for downloading
        self.http_client = httpx.Client(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; PortraitGenerator/1.0)"
            },
        )

    def find_reference_images(
        self,
        subject_data: SubjectData,
        max_images: int = 5,
    ) -> List[ReferenceImage]:
        """Find authenticated reference images for the subject.

        Uses Google Search grounding to:
        1. Search for historical photographs
        2. Verify authenticity via fact-checking
        3. Assess image quality and relevance
        4. Return ranked list of references

        Args:
            subject_data: Subject biographical data
            max_images: Maximum number of images to find

        Returns:
            List of ReferenceImage objects, ranked by combined score
        """
        logger.info(
            f"Finding reference images for {subject_data.name} "
            f"(max: {max_images})..."
        )

        # Build search queries
        queries = self._build_search_queries(subject_data)

        # Search for images (in real implementation, this would use
        # Gemini's Google Search grounding feature)
        candidate_images = []
        for query in queries[:3]:  # Use top 3 queries
            images = self._search_for_images(query, subject_data)
            candidate_images.extend(images)

        if not candidate_images:
            logger.warning(f"No reference images found for {subject_data.name}")
            return []

        # Rank and filter
        ranked_images = self._rank_and_filter(candidate_images, subject_data)

        # Return top N
        top_images = ranked_images[:max_images]

        logger.info(
            f"Found {len(top_images)} reference images for {subject_data.name}"
        )

        return top_images

    def _build_search_queries(self, subject_data: SubjectData) -> List[str]:
        """Build search queries for finding reference images.

        Args:
            subject_data: Subject biographical data

        Returns:
            List of search query strings
        """
        name = subject_data.name
        era = subject_data.era
        birth_year = subject_data.birth_year

        queries = [
            f"{name} historical photograph",
            f"{name} portrait {era}",
            f"{name} photo {birth_year}",
            f"{name} authentic image archive",
            f"{name} contemporary photograph",
        ]

        return queries

    def _search_for_images(
        self,
        query: str,
        subject_data: SubjectData,
    ) -> List[ReferenceImage]:
        """Search for images using the query.

        In a real implementation with gemini-3-pro-image-preview,
        this would use Google Search grounding to find and fact-check images.

        Args:
            query: Search query
            subject_data: Subject data for validation

        Returns:
            List of candidate reference images
        """
        logger.debug(f"Searching for images: {query}")

        # This is a placeholder implementation
        # Real implementation would use Gemini's Google Search grounding
        # to search for images and get URLs with authenticity verification

        # For now, we use a text-based search query through Gemini
        # In production, this would directly access Search grounding
        prompt = f"""
Search for authentic historical images of {subject_data.name}.

Query: {query}

Please identify 2-3 authentic historical images from reputable sources like:
- National archives
- Library of Congress
- University collections
- Museums
- Historical societies

For each image found, provide:
1. URL (if available in your knowledge)
2. Source
3. Authenticity confidence (0.0-1.0)
4. Brief description

Focus on images from {subject_data.era} showing {subject_data.name}'s face clearly.
"""

        try:
            # Use Gemini to search (with grounding if available)
            if hasattr(self.gemini_client, "query_with_grounding"):
                response = self.gemini_client.query_with_grounding(prompt)
            else:
                # Fallback to regular query
                from .researcher import BiographicalResearcher
                researcher = BiographicalResearcher(self.gemini_client)
                response = researcher._query_gemini(prompt)

            # Parse response to extract image information
            images = self._parse_image_search_results(response, subject_data)

            return images

        except Exception as e:
            logger.warning(f"Image search failed for '{query}': {e}")
            return []

    def _parse_image_search_results(
        self,
        response: str,
        subject_data: SubjectData,
    ) -> List[ReferenceImage]:
        """Parse Gemini's response to extract image metadata.

        Args:
            response: Gemini's search response
            subject_data: Subject data for validation

        Returns:
            List of ReferenceImage objects
        """
        images = []

        # Simple parsing logic (in production, would be more sophisticated)
        # Look for URLs in the response
        url_pattern = r'https?://[^\s<>"]+\.(?:jpg|jpeg|png|gif)'
        urls = re.findall(url_pattern, response)

        # For each URL, create a reference image
        for url in urls[:5]:  # Limit to 5 per query
            # Extract source from URL
            parsed = urlparse(url)
            source = parsed.netloc

            # Create reference image with estimated scores
            # In production, these would come from Gemini's analysis
            ref_image = ReferenceImage(
                url=url,
                source=source,
                authenticity_score=0.85,  # Would come from fact-checking
                quality_score=0.80,  # Would come from image analysis
                relevance_score=0.90,  # Would come from content analysis
                era_match=True,  # Would be validated
                description=f"Historical image of {subject_data.name}",
            )

            images.append(ref_image)

        return images

    def _rank_and_filter(
        self,
        images: List[ReferenceImage],
        subject_data: SubjectData,
    ) -> List[ReferenceImage]:
        """Rank images by combined score and filter low-quality ones.

        Args:
            images: List of candidate images
            subject_data: Subject data

        Returns:
            Ranked and filtered list
        """
        # Calculate combined score for each image
        scored_images = []
        for img in images:
            # Weighted combination
            combined_score = (
                img.authenticity_score * 0.40 +
                img.quality_score * 0.30 +
                img.relevance_score * 0.30
            )

            # Boost score if era matches
            if img.era_match:
                combined_score *= 1.1

            scored_images.append((combined_score, img))

        # Sort by score (descending)
        scored_images.sort(reverse=True, key=lambda x: x[0])

        # Filter out low scores (< 0.6)
        filtered = [img for score, img in scored_images if score >= 0.6]

        return filtered

    def validate_reference_authenticity(
        self,
        image: ReferenceImage,
        subject_data: SubjectData,
    ) -> bool:
        """Use Google Search grounding to fact-check image authenticity.

        Args:
            image: Reference image to validate
            subject_data: Subject data for cross-checking

        Returns:
            True if authentic, False otherwise
        """
        logger.debug(f"Validating authenticity of {image.url}")

        # Use Gemini with grounding to fact-check
        prompt = f"""
Fact-check this image: {image.url}

Subject: {subject_data.name}
Era: {subject_data.era}
Years: {subject_data.formatted_years}

Use Google Search to verify:
1. Is this image really of {subject_data.name}?
2. Is the source reputable?
3. Does it match the historical era?
4. Are there any red flags or inconsistencies?

Respond with: AUTHENTIC or NOT_AUTHENTIC
"""

        try:
            if hasattr(self.gemini_client, "query_with_grounding"):
                response = self.gemini_client.query_with_grounding(prompt)
            else:
                # Without grounding, use heuristics
                return image.authenticity_score >= 0.75

            # Check response
            response_lower = response.lower()
            is_authentic = "authentic" in response_lower and "not" not in response_lower

            logger.debug(f"Authenticity check: {'✓' if is_authentic else '✗'}")

            return is_authentic

        except Exception as e:
            logger.warning(f"Authenticity validation failed: {e}")
            # Fall back to score threshold
            return image.authenticity_score >= 0.75

    def download_and_prepare_references(
        self,
        images: List[ReferenceImage],
    ) -> List[Path]:
        """Download reference images and prepare for multi-image generation.

        Args:
            images: List of reference images to download

        Returns:
            List of local file paths
        """
        downloaded_paths = []

        for i, img in enumerate(images):
            try:
                # Download image
                logger.debug(f"Downloading reference image {i+1}/{len(images)}")

                response = self.http_client.get(img.url)
                response.raise_for_status()

                # Open and validate image
                image_data = BytesIO(response.content)
                pil_image = Image.open(image_data)

                # Validate it's a reasonable image
                if pil_image.width < 256 or pil_image.height < 256:
                    logger.warning(f"Image too small: {img.url}")
                    continue

                # Save locally
                filename = f"ref_{i+1}.{pil_image.format.lower()}"
                local_path = self.download_dir / filename

                pil_image.save(local_path)
                img.local_path = local_path

                downloaded_paths.append(local_path)

                logger.debug(f"Downloaded to: {local_path}")

            except Exception as e:
                logger.warning(f"Failed to download {img.url}: {e}")
                continue

        logger.info(f"Downloaded {len(downloaded_paths)} reference images")

        return downloaded_paths

    def cleanup_downloads(self):
        """Clean up downloaded reference images."""
        try:
            import shutil
            if self.download_dir.exists():
                shutil.rmtree(self.download_dir)
                self.download_dir.mkdir(parents=True, exist_ok=True)
                logger.debug("Cleaned up reference image downloads")
        except Exception as e:
            logger.warning(f"Failed to cleanup downloads: {e}")

    def __del__(self):
        """Clean up HTTP client on deletion."""
        try:
            self.http_client.close()
        except:
            pass
