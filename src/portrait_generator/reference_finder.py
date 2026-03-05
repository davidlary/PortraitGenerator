"""Reference image finding and validation.

This module finds authentic reference images for portrait subjects using
Wikipedia, Wikimedia Commons, and verified institutional URLs.
"""

import re
import urllib.parse
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Optional

import httpx
import requests
from loguru import logger
from PIL import Image

from .api.models import SubjectData

# ---------------------------------------------------------------------------
# Verified institutional photo URLs (confirmed HTTP 200)
# Key: canonical full name, Value: direct image URL
# ---------------------------------------------------------------------------
_CONFIRMED_URLS: Dict[str, str] = {
    "John Pyle": (
        "https://www.ch.cam.ac.uk/files/styles/staff_portrait/public/portraits/jap12.jpg"
    ),
    "David Lary": (
        "https://profiles.utdallas.edu/storage/media/3494/conversions/DavidLary-medium.jpg"
    ),
    "Eugenia Kalnay": (
        "https://earth.gsfc.nasa.gov/sites/default/files/styles/max_325x325/public/maniacs/pics/eugeniaKalnay.png"
    ),
    "Ulrich Platt": (
        "https://www.uni-heidelberg.de/md/einrichtungen/mk/fellows/portrait_platt_04.jpg"
    ),
    "Henrik Svensmark": (
        "https://orbit.dtu.dk/files-asset/399006805/38287_bccf27f8.jpg"
    ),
    "Andrew Lorenc": (
        "https://blogs.surrey.ac.uk/mathsresearch/wp-content/uploads/sites/11/2022/06/Lorenc.jpg"
    ),
    "Clive Rodgers": (
        "https://www.jesus.ox.ac.uk/wp-content/uploads/2021/04/Rodgers-Clive-crop-540x400.jpg"
    ),
}

_HEADERS = {
    "User-Agent": (
        "PortraitGenerator/2.2.0 "
        "(https://github.com/davidlary/PortraitGenerator; educational use)"
    )
}
_TIMEOUT = 15  # seconds
_MIN_IMAGE_DIMENSION = 256  # pixels
_MIN_IMAGE_BYTES = 10_240   # 10 KB


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

    Strategies (in priority order):
    1. Wikipedia photo — extracted from subject_data.reference_sources
       (injected by GroundTruthVerifier during research)
    2. Confirmed institutional URL table — hardcoded verified URLs
    3. Wikipedia page images API — real images from a subject's Wikipedia page
    """

    def __init__(
        self,
        gemini_client=None,
        enable_grounding: bool = False,
        download_dir: Optional[Path] = None,
    ):
        """Initialize reference image finder.

        Args:
            gemini_client: Unused; kept for API compatibility.
            enable_grounding: Unused; kept for API compatibility.
            download_dir: Directory to download images to.
        """
        self.gemini_client = gemini_client
        self.download_dir = download_dir or Path(".cpf/reference_images")
        self.download_dir.mkdir(parents=True, exist_ok=True)

        # HTTP client for downloading (httpx for async-compatible)
        self.http_client = httpx.Client(
            timeout=_TIMEOUT,
            follow_redirects=True,
            headers={"User-Agent": _HEADERS["User-Agent"]},
        )

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def find_reference_images(
        self,
        subject_data: SubjectData,
        max_images: int = 5,
    ) -> List[ReferenceImage]:
        """Find authenticated reference images for the subject.

        Tries multiple strategies in priority order and validates each
        candidate URL (HTTP 200, PIL-openable, ≥256×256 px, ≥10 KB).

        Args:
            subject_data: Subject biographical data.
            max_images: Maximum number of images to return.

        Returns:
            List of validated ReferenceImage objects, ranked by combined score.
        """
        logger.info(
            f"Finding reference images for {subject_data.name} (max: {max_images})..."
        )

        candidates: List[ReferenceImage] = []

        # Strategy 1: Wikipedia photo from ground_truth enrichment
        wiki_photo = self._get_wikipedia_photo_url(subject_data)
        if wiki_photo:
            img = self._validate_url(
                url=wiki_photo,
                source="Wikipedia",
                authenticity_score=0.95,
                quality_score=0.85,
                relevance_score=0.95,
                description=f"Wikipedia photo of {subject_data.name}",
            )
            if img:
                candidates.append(img)

        # Strategy 2: Confirmed institutional URL table
        inst_url = self._lookup_confirmed_url(subject_data.name)
        if inst_url:
            img = self._validate_url(
                url=inst_url,
                source="Institutional",
                authenticity_score=0.90,
                quality_score=0.85,
                relevance_score=0.95,
                description=f"Institutional photo of {subject_data.name}",
            )
            if img:
                candidates.append(img)

        # Strategy 3: Wikipedia page images API
        if len(candidates) < max_images:
            wiki_imgs = self._fetch_wikipedia_page_images(
                subject_data.name,
                limit=max_images - len(candidates),
            )
            candidates.extend(wiki_imgs)

        if not candidates:
            logger.warning(f"No reference images found for {subject_data.name}")
            return []

        # Rank and return top N
        ranked = self._rank_and_filter(candidates, subject_data)
        top = ranked[:max_images]

        logger.info(
            f"Found {len(top)} reference image(s) for {subject_data.name}"
        )
        return top

    def download_and_prepare_references(
        self,
        images: List[ReferenceImage],
    ) -> List[Path]:
        """Download reference images and return local paths.

        Args:
            images: List of reference images to download.

        Returns:
            List of local file paths for successfully downloaded images.
        """
        downloaded_paths: List[Path] = []

        for i, img in enumerate(images):
            try:
                logger.debug(f"Downloading reference image {i+1}/{len(images)}: {img.url}")

                response = self.http_client.get(img.url)
                response.raise_for_status()

                image_data = BytesIO(response.content)
                pil_image = Image.open(image_data)

                if pil_image.width < _MIN_IMAGE_DIMENSION or pil_image.height < _MIN_IMAGE_DIMENSION:
                    logger.warning(
                        f"Image too small ({pil_image.width}×{pil_image.height}): {img.url}"
                    )
                    continue

                fmt = (pil_image.format or "jpeg").lower()
                filename = f"ref_{i+1}.{fmt}"
                local_path = self.download_dir / filename

                pil_image.save(local_path)
                img.local_path = local_path
                downloaded_paths.append(local_path)

                logger.debug(f"Saved reference image to: {local_path}")

            except Exception as e:
                logger.warning(f"Failed to download {img.url}: {e}")
                continue

        logger.info(f"Downloaded {len(downloaded_paths)} reference image(s)")
        return downloaded_paths

    def cleanup_downloads(self):
        """Remove all downloaded reference images."""
        try:
            import shutil
            if self.download_dir.exists():
                shutil.rmtree(self.download_dir)
                self.download_dir.mkdir(parents=True, exist_ok=True)
                logger.debug("Cleaned up reference image downloads")
        except Exception as e:
            logger.warning(f"Failed to cleanup downloads: {e}")

    # ------------------------------------------------------------------ #
    # Strategy helpers                                                     #
    # ------------------------------------------------------------------ #

    def _get_wikipedia_photo_url(self, subject_data: SubjectData) -> Optional[str]:
        """Extract Wikipedia photo URL injected by GroundTruthVerifier.

        The ground truth module stores photo URLs in reference_sources with
        the prefix 'WIKIPEDIA_PHOTO:'.
        """
        for source in subject_data.reference_sources:
            if source.startswith("WIKIPEDIA_PHOTO:"):
                return source[len("WIKIPEDIA_PHOTO:"):]
        return None

    def _lookup_confirmed_url(self, name: str) -> Optional[str]:
        """Check hardcoded table of verified institutional photo URLs."""
        # Exact match
        if name in _CONFIRMED_URLS:
            return _CONFIRMED_URLS[name]
        # Case-insensitive match
        name_lower = name.lower()
        for key, url in _CONFIRMED_URLS.items():
            if key.lower() == name_lower:
                return url
        return None

    def _fetch_wikipedia_page_images(
        self, name: str, limit: int = 3
    ) -> List[ReferenceImage]:
        """Fetch image URLs used on a subject's Wikipedia page.

        Uses the MediaWiki action API to list images on the page, then
        resolves each to its direct URL.
        """
        results: List[ReferenceImage] = []
        api_url = "https://en.wikipedia.org/w/api.php"

        # Step 1: Get list of image filenames from the Wikipedia page
        try:
            resp = requests.get(
                api_url,
                params={
                    "action": "query",
                    "titles": name.replace(" ", "_"),
                    "prop": "images",
                    "format": "json",
                    "imlimit": limit + 5,  # overshoot; we'll filter
                },
                headers=_HEADERS,
                timeout=_TIMEOUT,
            )
            if resp.status_code != 200:
                return results
            pages = resp.json().get("query", {}).get("pages", {})
        except Exception as e:
            logger.debug(f"Wikipedia images list failed for '{name}': {e}")
            return results

        image_titles: List[str] = []
        for page in pages.values():
            for img_entry in page.get("images", []):
                title = img_entry.get("title", "")
                # Skip icons, logos, maps — only keep photo-like files
                lower = title.lower()
                if any(lower.endswith(ext) for ext in (".jpg", ".jpeg", ".png")):
                    if not any(
                        skip in lower
                        for skip in ("flag", "icon", "logo", "map", "svg", "commons-logo")
                    ):
                        image_titles.append(title)
                if len(image_titles) >= limit + 2:
                    break

        # Step 2: Resolve each filename to a direct URL
        for title in image_titles[:limit + 2]:
            try:
                resp2 = requests.get(
                    api_url,
                    params={
                        "action": "query",
                        "titles": title,
                        "prop": "imageinfo",
                        "iiprop": "url",
                        "format": "json",
                    },
                    headers=_HEADERS,
                    timeout=_TIMEOUT,
                )
                if resp2.status_code != 200:
                    continue
                pages2 = resp2.json().get("query", {}).get("pages", {})
                for page2 in pages2.values():
                    for ii in page2.get("imageinfo", []):
                        direct_url = ii.get("url", "")
                        if direct_url:
                            img = self._validate_url(
                                url=direct_url,
                                source="Wikipedia page images",
                                authenticity_score=0.80,
                                quality_score=0.75,
                                relevance_score=0.85,
                                description=f"Wikipedia image for {name}",
                            )
                            if img:
                                results.append(img)
                            if len(results) >= limit:
                                return results
            except Exception as e:
                logger.debug(f"Wikipedia image URL resolve failed for '{title}': {e}")
                continue

        return results

    # ------------------------------------------------------------------ #
    # URL validation                                                       #
    # ------------------------------------------------------------------ #

    def _validate_url(
        self,
        url: str,
        source: str,
        authenticity_score: float,
        quality_score: float,
        relevance_score: float,
        description: str = "",
    ) -> Optional[ReferenceImage]:
        """Fetch URL and verify it's a usable portrait image.

        Checks: HTTP 200, PIL-openable, ≥256×256 px, ≥10 KB.

        Returns:
            ReferenceImage if valid, else None.
        """
        try:
            resp = self.http_client.get(url, timeout=_TIMEOUT)
            if resp.status_code != 200:
                logger.debug(f"HTTP {resp.status_code} for {url}")
                return None

            content = resp.content
            if len(content) < _MIN_IMAGE_BYTES:
                logger.debug(f"Image too small ({len(content)} bytes): {url}")
                return None

            pil_image = Image.open(BytesIO(content))
            if pil_image.width < _MIN_IMAGE_DIMENSION or pil_image.height < _MIN_IMAGE_DIMENSION:
                logger.debug(
                    f"Image dimensions too small ({pil_image.width}×{pil_image.height}): {url}"
                )
                return None

            parsed = urllib.parse.urlparse(url)
            return ReferenceImage(
                url=url,
                source=source or parsed.netloc,
                authenticity_score=authenticity_score,
                quality_score=quality_score,
                relevance_score=relevance_score,
                era_match=True,
                description=description,
            )

        except Exception as e:
            logger.debug(f"URL validation failed for {url}: {e}")
            return None

    # ------------------------------------------------------------------ #
    # Ranking                                                              #
    # ------------------------------------------------------------------ #

    def _rank_and_filter(
        self,
        images: List[ReferenceImage],
        subject_data: SubjectData,
    ) -> List[ReferenceImage]:
        """Rank images by combined score (authenticity × 0.4 + quality × 0.3 + relevance × 0.3)."""
        scored: List[tuple] = []
        for img in images:
            score = (
                img.authenticity_score * 0.40
                + img.quality_score * 0.30
                + img.relevance_score * 0.30
            )
            if img.era_match:
                score *= 1.1
            scored.append((score, img))

        scored.sort(reverse=True, key=lambda x: x[0])
        return [img for _, img in scored if _ >= 0.6]

    def __del__(self):
        """Close HTTP client on deletion."""
        try:
            self.http_client.close()
        except Exception:
            pass
