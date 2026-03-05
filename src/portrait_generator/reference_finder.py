"""Reference image finding and validation.

This module finds authentic reference images for portrait subjects using
a smart progressive cascade of strategies — from the fastest/most reliable
to progressively more obscure fallbacks — with early exit as soon as
max_images is satisfied.

Cascade order (fastest → most obscure):
  Tier 1  — _CONFIRMED_URLS hardcoded table (zero network, instant)
  Tier 2  — Wikipedia photo from GroundTruth enrichment (zero extra network)
  Tier 3  — Wikipedia REST API thumbnail + original image (1 API call, ~0.5s)
  Tier 4  — Wikidata SPARQL P18 image property (2 calls, ~1-2s, very reliable)
  Tier 5  — Wikipedia page images API (2+ calls per image, ~2-5s)
  Tier 6  — Wikimedia Commons full-text search (2+ calls per image, ~3-5s)
  Tier 7  — DBpedia lookup thumbnail (1 call, last resort, less reliable)

Each tier is only invoked when the candidate list still has room for more
images.  As soon as max_images is satisfied the cascade short-circuits and
returns immediately.
"""

import hashlib
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
    # ==========================================================================
    # Pre-verified portrait image URLs for all 77 book portrait subjects.
    # Each URL was confirmed HTTP 200 by parallel research agents (v2.4.0).
    # Sources in priority order: Wikimedia Commons > Wikipedia > Institutional.
    #
    # Not found (4 subjects): Francis John Welsh Whipple, Frank John Scrase,
    # Walter Findeisen, Georg Pfotzer — these will be handled by the cascade.
    # ==========================================================================

    # ── Chapter-Introduction ──────────────────────────────────────────────────
    "Christian Friedrich Schönbein": (
        "https://upload.wikimedia.org/wikipedia/commons/e/e2/Sch%C3%B6nbein.jpg"
    ),
    "John Tyndall": (
        "https://upload.wikimedia.org/wikipedia/commons/b/bc/John_Tyndall_portrait_mid_career.jpg"
    ),
    "Joseph Fourier": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/d/df/Fourier2_-_restoration1.jpg/960px-Fourier2_-_restoration1.jpg"
    ),
    "Louis Agassiz": (
        "https://upload.wikimedia.org/wikipedia/commons/0/02/Louis_Agassiz_H6.jpg"
    ),
    "Svante Arrhenius": (
        "https://upload.wikimedia.org/wikipedia/commons/6/6c/Arrhenius2.jpg"
    ),
    "Theodore Fujita": (
        "https://upload.wikimedia.org/wikipedia/commons/4/49/Ted_Fujita_1972_%28cropped%29.jpg"
    ),

    # ── Chapter-Global-Chemistry ──────────────────────────────────────────────
    "Carl-Gustaf Rossby": (
        "https://upload.wikimedia.org/wikipedia/commons/e/ea/Carl_G._A._Rossby_LCCN2016875745_%28cropped%29.jpg"
    ),
    "Nicolaus Copernicus": (
        "https://upload.wikimedia.org/wikipedia/commons/e/e2/Nikolaus_Kopernikus_MOT.jpg"
    ),
    "Gaspard-Gustave de Coriolis": (
        "https://upload.wikimedia.org/wikipedia/commons/3/3b/Gaspard-Gustave_de_Coriolis.jpg"
    ),
    "Henry Eyring": (
        "https://upload.wikimedia.org/wikipedia/en/4/49/HenryEyring1951.jpg"
    ),
    "Jacobus van't Hoff": (
        "https://upload.wikimedia.org/wikipedia/commons/3/33/Jacobus_van_%27t_Hoff_by_Perscheid_1904.jpg"
    ),
    "Johann Heinrich Lambert": (
        "https://upload.wikimedia.org/wikipedia/commons/9/9b/JHLambert.jpg"
    ),
    "Jöns Jacob Berzelius": (
        "https://upload.wikimedia.org/wikipedia/commons/a/a4/J%C3%B6ns_Jacob_Berzelius_1826.jpg"
    ),
    "Johannes Kepler": (
        "https://upload.wikimedia.org/wikipedia/commons/7/74/JKepler.jpg"
    ),
    "Léon Teisserenc de Bort": (
        "https://upload.wikimedia.org/wikipedia/commons/d/d2/L%C3%A9on_Teisserenc_de_Bort.jpg"
    ),
    "Lord Rayleigh": (
        "https://upload.wikimedia.org/wikipedia/commons/2/28/John_William_Strutt.jpg"
    ),
    "Luke Howard": (
        "https://upload.wikimedia.org/wikipedia/commons/1/14/Luke_Howard.jpg"
    ),
    "Isaac Newton": (
        "https://upload.wikimedia.org/wikipedia/commons/f/f7/Portrait_of_Sir_Isaac_Newton%2C_1689_%28brightened%29.jpg"
    ),
    "Sydney Chapman": (
        "https://upload.wikimedia.org/wikipedia/commons/3/36/Sydney_Chapman.jpg"
    ),
    "Tor Bergeron": (
        "https://upload.wikimedia.org/wikipedia/commons/3/39/Tor_Bergeron.jpg"
    ),
    "Tycho Brahe": (
        "https://upload.wikimedia.org/wikipedia/commons/2/2b/Tycho_Brahe.JPG"
    ),
    # Walter Findeisen (1909-1945): no digitized portrait found anywhere

    # ── Chapter-Air-Quality ───────────────────────────────────────────────────
    "C. William Gear": (
        "https://siebelschool.illinois.edu/_sitemanager/viewphoto.aspx?id=10431&s=400"
    ),
    "Hiram Levy": (
        "https://scholar.googleusercontent.com/citations?view_op=medium_photo&user=MEkeGx8AAAAJ&citpid=1"
    ),
    "Mario Molina": (
        "https://upload.wikimedia.org/wikipedia/commons/d/db/Mario_Molina_1c389_8387.jpg"
    ),
    "Mark Jacobson": (
        "https://cee.stanford.edu/sites/g/files/sbiybj17091/files/styles/large_square/public/media/person/mark-jacobson1739316140576.jpg"
    ),
    "Paul Crutzen": (
        "https://upload.wikimedia.org/wikipedia/commons/0/00/Paul_Crutzen.jpg"
    ),

    # ── Chapter-Simulating ────────────────────────────────────────────────────
    "Aleksandr Lyapunov": (
        "https://upload.wikimedia.org/wikipedia/commons/1/1c/Aleksandr_Lyapunov.jpg"
    ),
    "Henri Poincaré": (
        "https://upload.wikimedia.org/wikipedia/commons/f/f4/PSM_V82_D416_Henri_Poincare.png"
    ),
    "John Pyle": (
        "https://www.ch.cam.ac.uk/files/styles/staff_portrait/public/portraits/jap12.jpg"
    ),
    "Joseph-Louis Lagrange": (
        "https://upload.wikimedia.org/wikipedia/commons/e/e7/Lagrange_crop.jpg"
    ),
    "Leonhard Euler": (
        "https://upload.wikimedia.org/wikipedia/commons/f/f9/Leonhard_Euler_-_Jakob_Emanuel_Handmann_%28Kunstmuseum_Basel%29.jpg"
    ),
    "Sherwood Rowland": (
        "https://upload.wikimedia.org/wikipedia/commons/9/91/F._Sherwood_Rowland.jpg"
    ),

    # ── Chapter-Observing ─────────────────────────────────────────────────────
    "Clive Rodgers": (
        "https://www.jesus.ox.ac.uk/wp-content/uploads/2021/04/Rodgers-Clive-crop-540x400.jpg"
    ),
    "Moustafa Chahine": (
        "https://airs.jpl.nasa.gov/system/internal_resources/details/original/72_shapeimage_1_2.jpg"
    ),
    "Sydney Twomey": (
        "https://www.iamas.org/irc/wp-content/uploads/sites/8/2021/05/stwomey_sm.jpg"
    ),
    "Ulrich Platt": (
        "https://www.uni-heidelberg.de/md/einrichtungen/mk/fellows/portrait_platt_04.jpg"
    ),

    # ── Chapter-Assimilation ──────────────────────────────────────────────────
    "Andrew Lorenc": (
        "https://blogs.surrey.ac.uk/mathsresearch/wp-content/uploads/sites/11/2022/06/Lorenc.jpg"
    ),
    "David Lary": (
        "https://profiles.utdallas.edu/storage/media/3494/conversions/DavidLary-medium.jpg"
    ),
    "Eugenia Kalnay": (
        "https://earth.gsfc.nasa.gov/sites/default/files/styles/max_325x325/public/maniacs/pics/eugeniaKalnay.png"
    ),
    "Mike Fisher": (
        "https://scholar.googleusercontent.com/citations?view_op=medium_photo&user=roKiQSwAAAAJ&citpid=2"
    ),
    "Norbert Wiener": (
        "https://upload.wikimedia.org/wikipedia/commons/5/56/Norbert_Wiener.png"
    ),
    "Roger Daley": (
        "https://www.science.ca/images/scientists/h-daley.jpg"
    ),
    "Rudolf Kalman": (
        "https://upload.wikimedia.org/wikipedia/commons/a/ac/Rudolf_Kalman.jpg"
    ),

    # ── Chapter-ML ────────────────────────────────────────────────────────────
    "Teuvo Kohonen": (
        "https://upload.wikimedia.org/wikipedia/commons/c/c3/Teuvo-Kohonen-2.jpg"
    ),

    # ── Chapter-Charged ───────────────────────────────────────────────────────
    "Benjamin Franklin": (
        "https://upload.wikimedia.org/wikipedia/commons/8/87/Joseph_Siffrein_Duplessis_-_Benjamin_Franklin_-_Google_Art_Project.jpg"
    ),
    "Brian Tinsley": (
        "https://profiles.utdallas.edu/storage/media/405/conversions/13644_0_14001-medium.jpg"
    ),
    "Charles-Augustin de Coulomb": (
        "https://upload.wikimedia.org/wikipedia/commons/9/9f/Charles_de_Coulomb.png"
    ),
    "Charles T. R. Wilson": (
        "https://upload.wikimedia.org/wikipedia/commons/2/20/CTR_Wilson.jpg"
    ),
    "Davis Sentman": (
        "https://www.gi.alaska.edu/sites/default/files/styles/full_article_image/public/portfolio/Dave%2520Sentman.jpg?itok=OhxPtbYg"
    ),
    "Edward Appleton": (
        "https://upload.wikimedia.org/wikipedia/commons/5/58/Appleton.jpg"
    ),
    # Francis John Welsh Whipple: NPG image blocked (403) — no public URL
    # Frank John Scrase: extremely obscure — no digitized portrait found
    # Georg Pfotzer: no portrait found anywhere
    "Henrik Svensmark": (
        "https://orbit.dtu.dk/files-asset/399006805/38287_bccf27f8.jpg"
    ),
    "John Winckler": (
        "https://upload.wikimedia.org/wikipedia/en/e/e6/John_r_winckler.jpg"
    ),
    "Louis-Guillaume Le Monnier": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e2/T1-_d532_-_Fig._268._%E2%80%94_Lemonnier.png/960px-T1-_d532_-_Fig._268._%E2%80%94_Lemonnier.png"
    ),
    "Marx Brook": (
        "https://aip.brightspotcdn.com/PTO.v56.i11.86_1.f1.jpg"
    ),
    # Ralph Markson (1930-2022): no publicly accessible portrait found anywhere
    "Richard Carrington": (
        "https://upload.wikimedia.org/wikipedia/commons/8/84/Maull_%26_Polyblank_photograph_of_Richard_C._Carrington.jpg"
    ),
    "Scott Forbush": (
        "https://upload.wikimedia.org/wikipedia/commons/7/71/Scott_Forbush.JPG"
    ),
    "Victor Hess": (
        "https://upload.wikimedia.org/wikipedia/commons/c/cc/Hess.jpg"
    ),
    "Winfried Otto Schumann": (
        "https://upload.wikimedia.org/wikipedia/commons/d/dd/Winfried_Otto_Schumann.jpeg"
    ),

    # ── Chapter-IAQ ───────────────────────────────────────────────────────────
    "Charles Weschler": (
        "https://eohsi.rutgers.edu/wp-content/uploads/weschler-250x250.jpg"
    ),
    "Lance Wallace": (
        "https://scholar.googleusercontent.com/citations?view_op=medium_photo&user=de02ILAAAAAJ&citpid=3"
    ),
    "Max von Pettenkofer": (
        "https://upload.wikimedia.org/wikipedia/commons/c/c3/Max_von_Pettenkofer5.jpg"
    ),
    "William Nazaroff": (
        "https://ce.berkeley.edu/sites/default/files/styles/faculty_photo_300x300_/public/faculty_photos/nazaroff%20COE%202017.jpg"
    ),

    # ── Chapter-Improving-IAQ ─────────────────────────────────────────────────
    "Boris Petrovich Tokin": (
        "https://upload.wikimedia.org/wikipedia/ru/6/6d/%D0%A2%D0%BE%D0%BA%D0%B8%D0%BD_%D0%91%D0%BE%D1%80%D0%B8%D1%81_%D0%9F%D0%B5%D1%82%D1%80%D0%BE%D0%B2%D0%B8%D1%87.jpg"
    ),
    "Charles H. Blackley": (
        "https://upload.wikimedia.org/wikipedia/commons/2/2b/Charles_Harrison_Blackley.jpg"
    ),
    "Edward O. Wilson": (
        "https://upload.wikimedia.org/wikipedia/commons/6/63/E._O._Wilson_sitting%2C_October_16%2C_2007_%28cropped%29.jpg"
    ),
    "Frank W. Went": (
        "https://www.nationalacademies.org/read/6201/assets/images/img00019.jpg"
    ),
    "Jan Ingenhousz": (
        "https://upload.wikimedia.org/wikipedia/commons/c/cf/Jan_Ingenhousz.jpg"
    ),
    "Joseph Priestley": (
        "https://upload.wikimedia.org/wikipedia/commons/3/36/Priestley_%28cropped%29.jpg"
    ),
    "Melvin Calvin": (
        "https://upload.wikimedia.org/wikipedia/commons/8/83/Melvin_Calvin_1960s.jpg"
    ),
    "Nicolas-Théodore de Saussure": (
        "https://upload.wikimedia.org/wikipedia/commons/a/a0/Nicolas-Th%C3%A9odore_de_Saussure.jpg"
    ),
    "Walther Flemming": (
        "https://upload.wikimedia.org/wikipedia/commons/8/82/Walther_flemming_2.jpg"
    ),
    "William F. Wells": (
        "https://upload.wikimedia.org/wikipedia/commons/9/96/William_Firth_Wells_taking_air_samples_%28cropped%29.png"
    ),
    "Willis Carrier": (
        "https://upload.wikimedia.org/wikipedia/commons/a/a7/Willis_Carrier_1915.jpg"
    ),

    # ── Chapter-Health-Impacts ────────────────────────────────────────────────
    "Avicenna": (
        "https://upload.wikimedia.org/wikipedia/commons/1/1a/Avicenna_Bust%2C_left_profile_%28cropped%29.jpg"
    ),
    "Bruce McEwen": (
        "https://upload.wikimedia.org/wikipedia/commons/5/50/Bruce_McEwen_in_NCCIH_interview.png"
    ),
    "Hans Selye": (
        "https://upload.wikimedia.org/wikipedia/commons/e/e7/Portrait_Hans_Selye.jpg"
    ),
    "Hildegard von Bingen": (
        "https://upload.wikimedia.org/wikipedia/commons/b/ba/Hildegard_von_Bingen.jpg"
    ),
    "Hippocrates": (
        "https://upload.wikimedia.org/wikipedia/commons/7/7c/Hippocrates.jpg"
    ),
    "Nicholas Culpeper": (
        "https://upload.wikimedia.org/wikipedia/commons/5/54/In_Effigiam_Nicholai_Culpeper_Equitis_by_Richard_Gaywood.jpg"
    ),
    "Pedanius Dioscorides": (
        "https://upload.wikimedia.org/wikipedia/commons/a/a1/Dioscorides_Vienna_%28detail%29_%28cropped%29.jpg"
    ),
    "René-Maurice Gattefossé": (
        "https://upload.wikimedia.org/wikipedia/commons/3/3f/Ren%C3%A9-Maurice_Gattefoss%C3%A9.jpg"
    ),
    "Ronald Ross": (
        "https://upload.wikimedia.org/wikipedia/commons/7/76/Ronald_Ross.jpg"
    ),
    "Rudolf Virchow": (
        "https://upload.wikimedia.org/wikipedia/commons/9/9c/Rudolf_Virchow_NLM3.jpg"
    ),
    "Theophrastus": (
        "https://upload.wikimedia.org/wikipedia/commons/d/d3/Teofrasto_Orto_botanico_detail.jpg"
    ),

    # ── Chapter-AQ-Plants-Birds-Animals ───────────────────────────────────────
    "Eugene P. Odum": (
        "https://upload.wikimedia.org/wikipedia/en/6/67/Eugene_Odum_by_James_Stawser.jpg"
    ),
    "F. Herbert Bormann": (
        "https://environment.yale.edu/sites/default/files/styles/4x5z3_small/public/content/images/3161/F.-Herbert-Bormann.jpg"
    ),
    "Gene Likens": (
        "https://upload.wikimedia.org/wikipedia/commons/2/25/Gene_Likens_2015_Mariel_Carr.JPG"
    ),
    "Karl von Frisch": (
        "https://upload.wikimedia.org/wikipedia/commons/e/e9/Karl_von_Frisch_-_Atelier_Veritas%2C_c._1926.jpg"
    ),
    "Rachel Carson": (
        "https://upload.wikimedia.org/wikipedia/commons/f/f4/Rachel-Carson.jpg"
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

    combined_score: float = 0.0
    """Weighted combined score: authenticity×0.4 + quality×0.3 + relevance×0.3 (×1.1 era bonus).
    Populated by _rank_and_filter(). Higher = better candidate for API submission."""


class ReferenceImageFinder:
    """Finds and validates reference images for portrait subjects.

    Uses a progressive 7-tier cascade that short-circuits as soon as
    max_images is satisfied.  Tiers are ordered fastest/most-reliable first
    so the common case (Wikipedia thumbnail available) completes in ~0.5s.
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

        Runs a progressive 7-tier cascade, stopping as soon as max_images
        is satisfied.  Each candidate URL is validated (HTTP 200,
        PIL-openable, ≥256×256 px, ≥10 KB) before being added.

        Args:
            subject_data: Subject biographical data.
            max_images: Maximum number of images to return.

        Returns:
            List of validated ReferenceImage objects, ranked by combined score.
        """
        name = subject_data.name
        logger.info(f"Finding reference images for {name} (max: {max_images})…")

        candidates: List[ReferenceImage] = []
        # Track which URLs we've already added to avoid duplicates
        seen_urls: set = set()

        def _add(img: Optional[ReferenceImage]) -> bool:
            """Add image to candidates if valid and not a duplicate."""
            if img and img.url not in seen_urls:
                seen_urls.add(img.url)
                candidates.append(img)
                return True
            return False

        def _done() -> bool:
            return len(candidates) >= max_images

        # ── Pre-load on-disk URL cache (populated by previous Gemini searches) ─
        url_cache = self._load_url_cache()

        # ── Tier 1: Hardcoded confirmed URLs (zero network, instant) ──────────
        inst_url = self._lookup_confirmed_url(name)
        if inst_url:
            img = self._validate_url(
                url=inst_url,
                source="Confirmed-Institutional",
                authenticity_score=0.95,
                quality_score=0.90,
                relevance_score=0.98,
                description=f"Pre-verified institutional photo of {name}",
            )
            if _add(img):
                logger.debug(f"Tier 1 (Confirmed-URL): found image for {name}")

        if _done():
            return self._finalize(candidates, subject_data, max_images)

        # ── Tier 2: On-disk URL cache from previous Gemini discoveries ────────
        cached_url = url_cache.get(name)
        if cached_url and cached_url not in seen_urls:
            img = self._validate_url(
                url=cached_url,
                source="Cached-Gemini",
                authenticity_score=0.90,
                quality_score=0.85,
                relevance_score=0.92,
                description=f"Previously discovered by Gemini web search for {name}",
            )
            if _add(img):
                logger.debug(f"Tier 2 (URL-cache): found image for {name}")

        if _done():
            return self._finalize(candidates, subject_data, max_images)

        # ── Tier 3: Wikipedia photo already fetched by GroundTruth ────────────
        wiki_photo = self._get_wikipedia_photo_url(subject_data)
        if wiki_photo and wiki_photo not in seen_urls:
            img = self._validate_url(
                url=wiki_photo,
                source="Wikipedia-GroundTruth",
                authenticity_score=0.95,
                quality_score=0.87,
                relevance_score=0.96,
                description=f"Wikipedia photo (ground-truth enriched) of {name}",
            )
            if _add(img):
                logger.debug(f"Tier 3 (GroundTruth-photo): found image for {name}")

        if _done():
            return self._finalize(candidates, subject_data, max_images)

        # ── Tier 4: Wikipedia REST API thumbnail / original image ──────────────
        rest_img = self._fetch_wikipedia_rest_thumbnail(name)
        if _add(rest_img):
            logger.debug(f"Tier 4 (Wikipedia-REST): found image for {name}")

        if _done():
            return self._finalize(candidates, subject_data, max_images)

        # ── Tier 5: Wikidata SPARQL P18 image property ────────────────────────
        wikidata_img = self._fetch_wikidata_p18_image(name)
        if _add(wikidata_img):
            logger.debug(f"Tier 5 (Wikidata-P18): found image for {name}")

        if _done():
            return self._finalize(candidates, subject_data, max_images)

        # ── Tier 6: Gemini-powered web search (AI-driven, self-caching) ───────
        # Only fires when free deterministic APIs haven't found enough images.
        # Costs one Gemini API call but understands context (era, field, institution).
        # Result is cached to disk so subsequent runs for the same person are free.
        gemini_img = self._fetch_via_gemini_web_search(name, subject_data)
        if _add(gemini_img):
            logger.debug(f"Tier 6 (Gemini-WebSearch): found image for {name}")

        if _done():
            return self._finalize(candidates, subject_data, max_images)

        # ── Tier 7: Wikipedia page images API ─────────────────────────────────
        need = max_images - len(candidates)
        wiki_imgs = self._fetch_wikipedia_page_images(name, limit=need)
        added = sum(1 for img in wiki_imgs if _add(img))
        if added:
            logger.debug(f"Tier 7 (Wikipedia-page-images): found {added} image(s) for {name}")

        if _done():
            return self._finalize(candidates, subject_data, max_images)

        # ── Tier 8: Wikimedia Commons full-text search ────────────────────────
        need = max_images - len(candidates)
        commons_imgs = self._fetch_wikimedia_commons_search(name, limit=need)
        added = sum(1 for img in commons_imgs if _add(img))
        if added:
            logger.debug(f"Tier 8 (Commons-search): found {added} image(s) for {name}")

        if _done():
            return self._finalize(candidates, subject_data, max_images)

        # ── Tier 9: DBpedia thumbnail (last resort) ────────────────────────────
        dbpedia_img = self._fetch_dbpedia_image(name)
        if _add(dbpedia_img):
            logger.debug(f"Tier 9 (DBpedia): found image for {name}")

        # ── Final: rank, filter, and return ───────────────────────────────────
        if not candidates:
            logger.warning(f"No reference images found for {name} (all 9 tiers exhausted)")
            return []

        return self._finalize(candidates, subject_data, max_images)

    def _finalize(
        self,
        candidates: List[ReferenceImage],
        subject_data: SubjectData,
        max_images: int,
    ) -> List[ReferenceImage]:
        """Rank, filter, truncate, and log the final candidate list."""
        ranked = self._rank_and_filter(candidates, subject_data)
        top = ranked[:max_images]
        logger.info(
            f"Found {len(top)} reference image(s) for {subject_data.name} "
            f"(best score: {top[0].combined_score:.3f})" if top else
            f"No usable reference images for {subject_data.name}"
        )
        return top

    def download_and_prepare_references(
        self,
        images: List[ReferenceImage],
        subject_name: str = "",
    ) -> List[Path]:
        """Download reference images and return local paths.

        Images are stored in a persistent per-person cache directory so repeated
        runs for the same subject reuse already-downloaded files.  The cache is
        keyed by a URL-safe slug of the subject's name so different subjects never
        collide.

        Args:
            images: List of reference images to download.
            subject_name: Subject's full name (used to build per-person cache dir).

        Returns:
            List of local file paths for successfully downloaded images,
            ordered by combined_score descending (best first).
        """
        # Build a persistent per-person cache directory
        if subject_name:
            slug = re.sub(r"[^a-z0-9]+", "_", subject_name.lower()).strip("_")
            person_dir = self.download_dir / slug
        else:
            person_dir = self.download_dir
        person_dir.mkdir(parents=True, exist_ok=True)

        # Sort by combined_score so the highest-quality images are first in the list
        sorted_images = sorted(images, key=lambda x: x.combined_score, reverse=True)

        downloaded_paths: List[Path] = []

        for i, img in enumerate(sorted_images):
            try:
                fmt_suffix = img.url.rsplit(".", 1)[-1].lower()
                if fmt_suffix not in ("jpg", "jpeg", "png", "gif", "webp"):
                    fmt_suffix = "jpg"
                filename = f"ref_{i+1:02d}_score{img.combined_score:.2f}.{fmt_suffix}"
                local_path = person_dir / filename

                # Use cached file if it already exists and is large enough
                if local_path.exists() and local_path.stat().st_size >= _MIN_IMAGE_BYTES:
                    logger.debug(
                        f"Using cached reference image (score={img.combined_score:.2f}): {local_path}"
                    )
                    img.local_path = local_path
                    downloaded_paths.append(local_path)
                    continue

                logger.debug(
                    f"Downloading reference image {i+1}/{len(sorted_images)} "
                    f"(score={img.combined_score:.2f}): {img.url}"
                )
                response = self.http_client.get(img.url)
                response.raise_for_status()

                image_data = BytesIO(response.content)
                pil_image = Image.open(image_data)

                if pil_image.width < _MIN_IMAGE_DIMENSION or pil_image.height < _MIN_IMAGE_DIMENSION:
                    logger.warning(
                        f"Image too small ({pil_image.width}×{pil_image.height}): {img.url}"
                    )
                    continue

                pil_image.save(local_path)
                img.local_path = local_path
                downloaded_paths.append(local_path)

                logger.debug(
                    f"Saved reference image (score={img.combined_score:.2f}) to: {local_path}"
                )

            except Exception as e:
                logger.warning(f"Failed to download {img.url}: {e}")
                continue

        best_score = sorted_images[0].combined_score if sorted_images else 0.0
        logger.info(
            f"Prepared {len(downloaded_paths)} reference image(s) for {subject_name or 'subject'} "
            f"(best combined_score: {best_score:.2f})"
        )
        return downloaded_paths

    def split_for_generation_and_validation(
        self,
        images: List[ReferenceImage],
        n_gen: int = 3,
    ) -> tuple:
        """Split reference images into generation and held-out validation sets.

        Zero-trust independent verification requires that images used to
        *guide* portrait generation are never the same images used to *verify*
        the result.  This method sorts by combined_score and partitions:

          - **Generation set** (first n_gen, highest-scored): sent to Gemini
            during portrait creation to anchor facial appearance.
          - **Validation set** (remainder): withheld and used after generation
            for independent identity verification via Vision API.

        When only 1 image is available it goes entirely to generation (there
        is nothing to hold out).  When 2+ images are available at least 1 is
        always withheld for validation.

        Args:
            images: Candidate reference images (already ranked by combined_score).
            n_gen: Max images in the generation set.  Defaults to 2 so at
                   least 1 image is held out when ≥3 are available.

        Returns:
            (generation_set, validation_set) tuple of ReferenceImage lists.
            Both lists contain distinct images (no overlap).
        """
        if not images:
            return [], []

        # Sort by combined_score descending so the best images go to generation
        sorted_imgs = sorted(images, key=lambda x: x.combined_score, reverse=True)

        if len(sorted_imgs) == 1:
            # Only one image — must use it for generation; nothing to hold out
            return [sorted_imgs[0]], []

        # With 2+ images, always hold out at least 1 for independent validation
        actual_n_gen = min(n_gen, len(sorted_imgs) - 1)
        gen_set = sorted_imgs[:actual_n_gen]
        val_set = sorted_imgs[actual_n_gen:]

        logger.info(
            f"Reference split: {len(gen_set)} for generation, "
            f"{len(val_set)} held out for independent validation"
        )
        return gen_set, val_set

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

    def _fetch_via_gemini_web_search(self, name: str, subject_data: SubjectData) -> Optional[ReferenceImage]:
        """Use Gemini with Google Search grounding to find the best image URL.

        This is the most intelligent tier — it uses LLM understanding of the
        person's field, era, nationality, and institutional affiliation to
        choose the most appropriate image source.  Only invoked when simpler
        deterministic tiers have not found enough images.

        Results are written to the on-disk URL cache so subsequent runs for
        the same person skip this expensive call entirely.

        Args:
            name: Subject's canonical name.
            subject_data: Full subject biographical data.

        Returns:
            Validated ReferenceImage or None.
        """
        if not self.gemini_client:
            return None

        era = getattr(subject_data, "era", "")
        birth = getattr(subject_data, "birth_year", "")
        field_hint = ""
        if subject_data.reference_sources:
            # Use first reference source as a field hint
            field_hint = subject_data.reference_sources[0][:120] if subject_data.reference_sources else ""

        prompt = (
            f"Find the best, most authentic publicly accessible photograph of "
            f"{name} ({era}, born {birth}). "
            f"Respond with ONLY a direct image URL (ending in .jpg, .jpeg, or .png) "
            f"from one of these preferred sources (in priority order): "
            f"1) Wikipedia or Wikimedia Commons, "
            f"2) their institutional/university profile page, "
            f"3) a Nobel Prize or major award page, "
            f"4) the AIP Niels Bohr Library, "
            f"5) any other authoritative biographical source. "
            f"The URL must be a direct link to an image file that can be downloaded. "
            f"If no photograph exists (e.g. very ancient historical figure), respond with NONE. "
            f"Return ONLY the URL or NONE — no other text."
        )

        try:
            # Use grounded generation via the Gemini client
            from google.genai.types import GenerateContentConfig, Tool

            config = GenerateContentConfig(
                tools=[Tool(google_search={})],
                response_modalities=["Text"],
                temperature=0.1,
            )
            response = self.gemini_client.client.models.generate_content(
                model=self.gemini_client.model,
                contents=prompt,
                config=config,
            )
            raw = ""
            if response and response.candidates:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, "text") and part.text:
                        raw = part.text.strip()
                        break

            # Extract URL from response
            url = raw.strip().strip('"').strip("'")
            if not url or url.upper() == "NONE" or not url.startswith("http"):
                logger.debug(f"Gemini web search returned no URL for '{name}': {raw[:80]}")
                return None

            img = self._validate_url(
                url=url,
                source="Gemini-WebSearch",
                authenticity_score=0.88,
                quality_score=0.83,
                relevance_score=0.92,
                description=f"Gemini web-search image for {name}",
            )
            if img:
                logger.info(f"Tier 0 (Gemini-WebSearch): found image for {name}: {url[:80]}")
                # Cache the result so future runs don't need another Gemini call
                self._cache_discovered_url(name, url)
            return img

        except Exception as e:
            logger.debug(f"Gemini web search tier failed for '{name}': {e}")
            return None

    def _cache_discovered_url(self, name: str, url: str) -> None:
        """Persist a Gemini-discovered URL to the on-disk URL cache.

        The cache is a simple JSON file alongside the download directory.
        On next run the cache is loaded before any network calls are made.
        """
        try:
            import json
            cache_file = self.download_dir.parent / "url_cache.json"
            cache: Dict[str, str] = {}
            if cache_file.exists():
                try:
                    cache = json.loads(cache_file.read_text(encoding="utf-8"))
                except Exception:
                    cache = {}
            cache[name] = url
            cache_file.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")
            logger.debug(f"Cached discovered URL for '{name}': {url[:80]}")
        except Exception as e:
            logger.debug(f"Failed to write URL cache: {e}")

    def _load_url_cache(self) -> Dict[str, str]:
        """Load the on-disk URL cache discovered by previous Gemini searches."""
        try:
            import json
            cache_file = self.download_dir.parent / "url_cache.json"
            if cache_file.exists():
                return json.loads(cache_file.read_text(encoding="utf-8"))
        except Exception:
            pass
        return {}

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

    def _fetch_wikipedia_rest_thumbnail(self, name: str) -> Optional[ReferenceImage]:
        """Fetch thumbnail + original image from the Wikipedia REST API summary endpoint.

        This is the fastest public API approach — 1 HTTP call returns the main
        infobox image for the Wikipedia article.  Prefers the full-resolution
        original over the thumbnail when available.
        """
        try:
            encoded = urllib.parse.quote(name.replace(" ", "_"), safe="")
            resp = requests.get(
                f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded}",
                headers=_HEADERS,
                timeout=_TIMEOUT,
            )
            if resp.status_code != 200:
                return None
            data = resp.json()
            # Prefer full-resolution original if available
            original_url = data.get("originalimage", {}).get("source", "")
            thumb_url = data.get("thumbnail", {}).get("source", "")
            use_url = original_url or thumb_url
            if not use_url:
                return None
            return self._validate_url(
                url=use_url,
                source="Wikipedia-REST",
                authenticity_score=0.92,
                quality_score=0.85,
                relevance_score=0.95,
                description=f"Wikipedia REST summary image for {name}",
            )
        except Exception as e:
            logger.debug(f"Wikipedia REST API failed for '{name}': {e}")
            return None

    def _fetch_wikidata_p18_image(self, name: str) -> Optional[ReferenceImage]:
        """Query Wikidata for the P18 (image) property of a person.

        Two-step process:
          1. Search Wikidata entities by name to get QID
          2. Fetch P18 claim → Commons filename → construct direct CDN URL

        Wikidata P18 is almost always a high-quality, unambiguous photograph
        when it exists.  The CDN URL formula is the standard MediaWiki hash path.
        """
        # Step 1: Resolve name → QID
        try:
            resp = requests.get(
                "https://www.wikidata.org/w/api.php",
                params={
                    "action": "wbsearchentities",
                    "search": name,
                    "language": "en",
                    "type": "item",
                    "format": "json",
                    "limit": 3,
                },
                headers=_HEADERS,
                timeout=_TIMEOUT,
            )
            if resp.status_code != 200:
                return None
            results = resp.json().get("search", [])
            if not results:
                return None
            entity_id = results[0]["id"]  # e.g. "Q7259"
        except Exception as e:
            logger.debug(f"Wikidata entity search failed for '{name}': {e}")
            return None

        # Step 2: Fetch P18 (image) claim
        try:
            resp2 = requests.get(
                "https://www.wikidata.org/w/api.php",
                params={
                    "action": "wbgetclaims",
                    "entity": entity_id,
                    "property": "P18",
                    "format": "json",
                },
                headers=_HEADERS,
                timeout=_TIMEOUT,
            )
            if resp2.status_code != 200:
                return None
            claims = resp2.json().get("claims", {}).get("P18", [])
            if not claims:
                return None
            filename: str = claims[0]["mainsnak"]["datavalue"]["value"]
        except Exception as e:
            logger.debug(f"Wikidata P18 fetch failed for '{name}' ({entity_id}): {e}")
            return None

        # Build Wikimedia Commons CDN URL from filename
        # Formula: upload.wikimedia.org/wikipedia/commons/{md5[0]}/{md5[0:2]}/{encoded_filename}
        try:
            fn = filename.replace(" ", "_")
            md5 = hashlib.md5(fn.encode("utf-8")).hexdigest()
            cdn_url = (
                "https://upload.wikimedia.org/wikipedia/commons/"
                f"{md5[0]}/{md5[0:2]}/{urllib.parse.quote(fn, safe='')}"
            )
            return self._validate_url(
                url=cdn_url,
                source="Wikidata-P18",
                authenticity_score=0.93,
                quality_score=0.87,
                relevance_score=0.95,
                description=f"Wikidata P18 image for {name} (entity {entity_id})",
            )
        except Exception as e:
            logger.debug(f"Wikidata P18 URL construction failed for '{name}': {e}")
            return None

    def _fetch_wikimedia_commons_search(
        self, name: str, limit: int = 2
    ) -> List[ReferenceImage]:
        """Full-text search Wikimedia Commons for images of the subject.

        Searches the File namespace (ns=6) for the person's name, then
        resolves each result to a direct image URL.  Filters out maps,
        flags, icons, diagrams, and other non-portrait files.
        """
        results: List[ReferenceImage] = []
        try:
            resp = requests.get(
                "https://commons.wikimedia.org/w/api.php",
                params={
                    "action": "query",
                    "list": "search",
                    "srsearch": name,
                    "srnamespace": 6,
                    "format": "json",
                    "srlimit": limit + 5,
                },
                headers=_HEADERS,
                timeout=_TIMEOUT,
            )
            if resp.status_code != 200:
                return results
            search_hits = resp.json().get("query", {}).get("search", [])
        except Exception as e:
            logger.debug(f"Wikimedia Commons search failed for '{name}': {e}")
            return results

        _skip_keywords = ("map", "flag", "icon", "logo", "diagram", "graph",
                          "chart", "signature", "coat", "arms", "stamp")

        for hit in search_hits:
            title = hit.get("title", "")
            lower = title.lower()
            if not any(lower.endswith(ext) for ext in (".jpg", ".jpeg", ".png")):
                continue
            if any(kw in lower for kw in _skip_keywords):
                continue

            try:
                resp2 = requests.get(
                    "https://commons.wikimedia.org/w/api.php",
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
                pages = resp2.json().get("query", {}).get("pages", {})
                for page in pages.values():
                    for ii in page.get("imageinfo", []):
                        url = ii.get("url", "")
                        if url:
                            img = self._validate_url(
                                url=url,
                                source="Wikimedia-Commons",
                                authenticity_score=0.82,
                                quality_score=0.78,
                                relevance_score=0.80,
                                description=f"Commons search: {title}",
                            )
                            if img:
                                results.append(img)
                            if len(results) >= limit:
                                return results
            except Exception as e:
                logger.debug(f"Commons URL resolve failed for '{title}': {e}")
                continue

        return results

    def _fetch_dbpedia_image(self, name: str) -> Optional[ReferenceImage]:
        """Fetch a thumbnail from the DBpedia Lookup Service.

        DBpedia extracts structured data from Wikipedia infoboxes and exposes
        a free search API.  Used as a final fallback when all other sources
        have failed.
        """
        try:
            encoded = urllib.parse.quote(name, safe="")
            resp = requests.get(
                f"https://lookup.dbpedia.org/api/search?query={encoded}&format=json&maxResults=5",
                headers=_HEADERS,
                timeout=_TIMEOUT,
            )
            if resp.status_code != 200:
                return None
            docs = resp.json().get("docs", [])
        except Exception as e:
            logger.debug(f"DBpedia lookup failed for '{name}': {e}")
            return None

        name_lower = name.lower()
        for doc in docs:
            labels = doc.get("label", [])
            if not any(
                name_lower in lbl.lower() or lbl.lower() in name_lower
                for lbl in labels
            ):
                continue
            thumbnails = doc.get("thumbnail", [])
            if not thumbnails:
                continue
            url = thumbnails[0] if isinstance(thumbnails, list) else thumbnails
            img = self._validate_url(
                url=url,
                source="DBpedia",
                authenticity_score=0.75,
                quality_score=0.72,
                relevance_score=0.78,
                description=f"DBpedia thumbnail for {name}",
            )
            if img:
                return img
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
        """Rank images by combined score (authenticity × 0.4 + quality × 0.3 + relevance × 0.3).

        Scores are stored back on each ReferenceImage.combined_score so callers can
        inspect exactly why an image was ranked or rejected.  Images with combined_score
        below 0.6 are discarded as too uncertain to trust for portrait conditioning.
        """
        scored: List[tuple] = []
        for img in images:
            score = (
                img.authenticity_score * 0.40
                + img.quality_score * 0.30
                + img.relevance_score * 0.30
            )
            if img.era_match:
                score *= 1.1
            img.combined_score = round(score, 3)
            scored.append((score, img))

        scored.sort(reverse=True, key=lambda x: x[0])
        filtered = [img for _, img in scored if _ >= 0.6]

        for img in filtered:
            logger.debug(
                f"  Reference [{img.source}] score={img.combined_score:.3f} "
                f"(auth={img.authenticity_score:.2f}, qual={img.quality_score:.2f}, "
                f"rel={img.relevance_score:.2f}, era={img.era_match}): {img.url[:80]}"
            )

        return filtered

    def __del__(self):
        """Close HTTP client on deletion."""
        try:
            self.http_client.close()
        except Exception:
            pass
