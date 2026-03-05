"""Unit tests for reference_finder module."""

import os
import pytest
from pathlib import Path

from portrait_generator.reference_finder import (
    ReferenceImage,
    ReferenceImageFinder,
)
from portrait_generator.api.models import SubjectData
from portrait_generator.utils.gemini_client import GeminiImageClient

# Sentinel for tests that require a real Gemini API key
_NO_API_KEY = not os.getenv("GOOGLE_API_KEY")
_SKIP_NO_KEY = pytest.mark.skipif(_NO_API_KEY, reason="Requires real Gemini API access - set GOOGLE_API_KEY")


@pytest.fixture
def gemini_client():
    """Create a real Gemini client with test API key."""
    return GeminiImageClient(api_key="test_api_key_1234567890")


@pytest.fixture
def sample_subject_data():
    """Create sample subject data."""
    return SubjectData(
        name="Alan Turing",
        birth_year=1912,
        death_year=1954,
        era="20th Century",
    )


@pytest.fixture
def reference_finder(gemini_client, tmp_path):
    """Create reference finder instance with real client."""
    return ReferenceImageFinder(
        gemini_client=gemini_client,
        enable_grounding=True,
        download_dir=tmp_path / "refs",
    )


class TestReferenceImage:
    """Tests for ReferenceImage dataclass."""

    def test_create_reference_image(self):
        """Test creating a reference image."""
        ref = ReferenceImage(
            url="https://example.com/image.jpg",
            source="example.com",
            authenticity_score=0.90,
            quality_score=0.85,
            relevance_score=0.95,
            era_match=True,
            description="Test image",
        )

        assert ref.url == "https://example.com/image.jpg"
        assert ref.source == "example.com"
        assert ref.authenticity_score == 0.90
        assert ref.quality_score == 0.85
        assert ref.relevance_score == 0.95
        assert ref.era_match is True
        assert ref.description == "Test image"
        assert ref.local_path is None

    def test_combined_score_default_zero(self):
        """combined_score starts at 0.0 and is populated by _rank_and_filter()."""
        ref = ReferenceImage(
            url="https://example.com/image.jpg",
            source="example.com",
            authenticity_score=0.90,
            quality_score=0.85,
            relevance_score=0.95,
            era_match=True,
        )
        assert ref.combined_score == 0.0

    def test_combined_score_can_be_set(self):
        """combined_score can be set directly (e.g., after ranking)."""
        ref = ReferenceImage(
            url="https://example.com/image.jpg",
            source="example.com",
            authenticity_score=0.90,
            quality_score=0.85,
            relevance_score=0.95,
            era_match=True,
            combined_score=0.924,
        )
        assert ref.combined_score == pytest.approx(0.924)


class TestReferenceImageFinder:
    """Tests for ReferenceImageFinder class."""

    def test_initialization(self, gemini_client, tmp_path):
        """Test finder initialization."""
        finder = ReferenceImageFinder(
            gemini_client=gemini_client,
            enable_grounding=True,
            download_dir=tmp_path / "refs",
        )

        assert finder.gemini_client is gemini_client
        assert finder.download_dir.exists()

    def test_lookup_confirmed_url_known_subject(self, reference_finder):
        """Test confirmed URL lookup returns URL for known subjects."""
        from portrait_generator.api.models import SubjectData
        data = SubjectData(name="David Lary", birth_year=1970, era="Contemporary")
        url = reference_finder._lookup_confirmed_url(data.name)
        assert url is not None
        assert url.startswith("https://")

    def test_lookup_confirmed_url_unknown_subject(self, reference_finder):
        """Test confirmed URL lookup returns None for unknown subjects."""
        url = reference_finder._lookup_confirmed_url("Completely Unknown Person XYZ")
        assert url is None

    def test_get_wikipedia_photo_url_present(self, reference_finder):
        """Test extracting Wikipedia photo URL from reference_sources."""
        from portrait_generator.api.models import SubjectData
        data = SubjectData(
            name="Alan Turing",
            birth_year=1912,
            death_year=1954,
            era="20th Century",
            reference_sources=["WIKIPEDIA_PHOTO:https://example.com/turing.jpg"],
        )
        url = reference_finder._get_wikipedia_photo_url(data)
        assert url == "https://example.com/turing.jpg"

    def test_get_wikipedia_photo_url_absent(self, reference_finder, sample_subject_data):
        """Test extracting Wikipedia photo URL when not present."""
        url = reference_finder._get_wikipedia_photo_url(sample_subject_data)
        assert url is None

    def test_rank_and_filter(self, reference_finder, sample_subject_data):
        """Test ranking, filtering, and combined_score population."""
        images = [
            ReferenceImage(
                url="https://example.com/image1.jpg",
                source="example.com",
                authenticity_score=0.95,
                quality_score=0.90,
                relevance_score=0.85,
                era_match=True,
            ),
            ReferenceImage(
                url="https://example.com/image2.jpg",
                source="example.com",
                authenticity_score=0.50,
                quality_score=0.45,
                relevance_score=0.40,
                era_match=False,
            ),
            ReferenceImage(
                url="https://example.com/image3.jpg",
                source="example.com",
                authenticity_score=0.85,
                quality_score=0.80,
                relevance_score=0.90,
                era_match=True,
            ),
        ]

        ranked = reference_finder._rank_and_filter(images, sample_subject_data)

        # Should filter out low-quality image
        assert len(ranked) < len(images)

        # Should be ranked by score (highest combined_score first)
        for img in ranked:
            # combined_score is populated by _rank_and_filter (not 0.0)
            assert img.combined_score > 0.0, f"combined_score not set on {img.url}"

        # Verify descending order
        scores = [img.combined_score for img in ranked]
        assert scores == sorted(scores, reverse=True)

    def test_rank_and_filter_low_score_rejected(self, reference_finder, sample_subject_data):
        """Images with combined_score < 0.6 (before era bonus) are filtered out."""
        images = [
            ReferenceImage(
                url="https://example.com/bad.jpg",
                source="example.com",
                authenticity_score=0.40,
                quality_score=0.35,
                relevance_score=0.30,
                era_match=False,  # no era bonus
            ),
        ]
        ranked = reference_finder._rank_and_filter(images, sample_subject_data)
        # Score = 0.40×0.4 + 0.35×0.3 + 0.30×0.3 = 0.16 + 0.105 + 0.09 = 0.355 < 0.6
        assert ranked == []

    def test_download_and_prepare_uses_per_person_cache_dir(
        self, reference_finder, tmp_path
    ):
        """download_and_prepare_references creates a persistent per-person subdirectory."""
        finder = ReferenceImageFinder(download_dir=tmp_path / "cache")

        # We don't actually download anything — we just verify the directory is created
        finder.download_and_prepare_references([], subject_name="Alan Turing")
        expected_dir = tmp_path / "cache" / "alan_turing"
        assert expected_dir.exists(), f"Per-person cache dir not created: {expected_dir}"

    def test_confirmed_urls_expanded(self, reference_finder):
        """v2.3.0 adds 9 more confirmed institutional URLs."""
        new_entries = [
            "Moustafa Chahine",
            "Gene Likens",
            "Marx Brook",
            "Roger Daley",
            "Rudolf Kalman",
            "Norbert Wiener",
            "Sydney Twomey",
            "Tor Bergeron",
            "F. Herbert Bormann",
        ]
        for name in new_entries:
            url = reference_finder._lookup_confirmed_url(name)
            assert url is not None, f"Missing confirmed URL for {name}"
            assert url.startswith("https://"), f"Expected https URL for {name}, got {url}"

    @_SKIP_NO_KEY
    def test_validate_reference_authenticity(self, sample_subject_data, tmp_path) -> None:
        """Test validating reference authenticity (requires real API)."""
        pass

    @pytest.mark.skip(reason="Requires real HTTP client - no external dependencies in unit tests")
    def test_download_and_prepare_references(self, reference_finder, tmp_path) -> None:
        """Test downloading reference images (requires real HTTP)."""
        pass

    def test_cleanup_downloads(self, reference_finder):
        """Test cleanup of downloaded images."""
        # Create some test files
        test_file = reference_finder.download_dir / "test.jpg"
        test_file.write_text("test")

        reference_finder.cleanup_downloads()

        # Directory should be empty
        assert reference_finder.download_dir.exists()
        assert not test_file.exists()


# ---------------------------------------------------------------------------
# Cascade tier unit tests (strategy methods)
# ---------------------------------------------------------------------------

class TestCascadeTiers:
    """Unit tests for each tier in the progressive reference-image cascade."""

    @pytest.fixture
    def finder(self, tmp_path):
        return ReferenceImageFinder(download_dir=tmp_path / "refs")

    @pytest.fixture
    def subject(self):
        return SubjectData(name="Alan Turing", birth_year=1912, death_year=1954, era="20th Century")

    # ── Tier 3: Wikipedia REST thumbnail ─────────────────────────────────────

    def test_wikipedia_rest_returns_original_image(self, finder, monkeypatch):
        """Tier 3 returns originalimage.source when available."""
        import requests as req_mod
        import io
        from unittest.mock import MagicMock
        from PIL import Image as PILImage

        # Fake REST response with original + thumbnail URLs
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "originalimage": {"source": "https://example.com/original.jpg"},
            "thumbnail": {"source": "https://example.com/thumb.jpg"},
        }

        # Fake image download (for _validate_url which uses httpx client)
        img_bytes = io.BytesIO()
        PILImage.new("RGB", (512, 682)).save(img_bytes, "JPEG")
        raw = img_bytes.getvalue() + b"\x00" * 20_000  # > MIN_IMAGE_BYTES

        mock_dl = MagicMock()
        mock_dl.status_code = 200
        mock_dl.content = raw

        # _fetch_wikipedia_rest_thumbnail uses requests.get for the REST call
        monkeypatch.setattr(req_mod, "get", lambda *a, **kw: mock_resp)
        # _validate_url uses self.http_client.get (httpx) for image download
        monkeypatch.setattr(finder.http_client, "get", lambda *a, **kw: mock_dl)

        result = finder._fetch_wikipedia_rest_thumbnail("Alan Turing")
        assert result is not None
        # Should prefer originalimage.source over thumbnail
        assert result.url == "https://example.com/original.jpg"
        assert result.source == "Wikipedia-REST"

    def test_wikipedia_rest_falls_back_to_thumbnail(self, finder, monkeypatch):
        """Tier 3 uses thumbnail URL when originalimage is absent."""
        import requests as req_mod
        import io
        from unittest.mock import MagicMock
        from PIL import Image as PILImage

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "thumbnail": {"source": "https://example.com/thumb.jpg"},
        }

        img_bytes = io.BytesIO()
        PILImage.new("RGB", (512, 682)).save(img_bytes, "JPEG")
        raw = img_bytes.getvalue() + b"\x00" * 20_000

        mock_dl = MagicMock()
        mock_dl.status_code = 200
        mock_dl.content = raw

        monkeypatch.setattr(req_mod, "get", lambda *a, **kw: mock_resp)
        monkeypatch.setattr(finder.http_client, "get", lambda *a, **kw: mock_dl)

        result = finder._fetch_wikipedia_rest_thumbnail("Alan Turing")
        assert result is not None
        assert result.url == "https://example.com/thumb.jpg"

    def test_wikipedia_rest_returns_none_on_404(self, finder, monkeypatch):
        """Tier 3 returns None when Wikipedia REST returns 404."""
        import requests as req_mod
        from unittest.mock import MagicMock

        mock_resp = MagicMock()
        mock_resp.status_code = 404

        monkeypatch.setattr(req_mod, "get", lambda *a, **kw: mock_resp)
        result = finder._fetch_wikipedia_rest_thumbnail("Nonexistent Person XYZ")
        assert result is None

    def test_wikipedia_rest_returns_none_when_no_image_keys(self, finder, monkeypatch):
        """Tier 3 returns None when REST response has no image URLs."""
        import requests as req_mod
        from unittest.mock import MagicMock

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"extract": "Some text, no images"}

        monkeypatch.setattr(req_mod, "get", lambda *a, **kw: mock_resp)
        result = finder._fetch_wikipedia_rest_thumbnail("Alan Turing")
        assert result is None

    # ── Tier 5: Wikidata P18 ──────────────────────────────────────────────────

    def test_wikidata_p18_builds_correct_cdn_url(self, finder, monkeypatch):
        """Tier 5 constructs the correct Wikimedia CDN URL from a P18 filename."""
        import requests as req_mod
        import hashlib
        import urllib.parse
        import io
        from unittest.mock import MagicMock
        from PIL import Image as PILImage

        # Entity search → returns Q7259
        search_resp = MagicMock()
        search_resp.status_code = 200
        search_resp.json.return_value = {"search": [{"id": "Q7259"}]}

        # P18 claim → filename "Alan_Turing_az.jpg"
        p18_resp = MagicMock()
        p18_resp.status_code = 200
        p18_resp.json.return_value = {
            "claims": {
                "P18": [{"mainsnak": {"datavalue": {"value": "Alan_Turing_az.jpg"}}}]
            }
        }

        # Image download mock — _validate_url uses httpx client
        img_bytes = io.BytesIO()
        PILImage.new("RGB", (512, 682)).save(img_bytes, "JPEG")
        raw = img_bytes.getvalue() + b"\x00" * 20_000

        dl_resp = MagicMock()
        dl_resp.status_code = 200
        dl_resp.content = raw

        def fake_requests_get(url, params=None, **kwargs):
            if "wbsearchentities" in str(params or {}):
                return search_resp
            if "wbgetclaims" in str(params or {}):
                return p18_resp
            return search_resp  # fallback

        monkeypatch.setattr(req_mod, "get", fake_requests_get)
        # _validate_url uses self.http_client.get (httpx) for image download
        monkeypatch.setattr(finder.http_client, "get", lambda *a, **kw: dl_resp)

        result = finder._fetch_wikidata_p18_image("Alan Turing")
        assert result is not None
        assert result.source == "Wikidata-P18"
        # Verify the CDN URL follows the correct hash formula
        fn = "Alan_Turing_az.jpg"
        md5 = hashlib.md5(fn.encode("utf-8")).hexdigest()
        expected_url = (
            f"https://upload.wikimedia.org/wikipedia/commons/"
            f"{md5[0]}/{md5[0:2]}/{urllib.parse.quote(fn, safe='')}"
        )
        assert result.url == expected_url

    def test_wikidata_p18_returns_none_when_entity_not_found(self, finder, monkeypatch):
        """Tier 5 returns None when Wikidata search finds no entity."""
        import requests as req_mod
        from unittest.mock import MagicMock

        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"search": []}

        monkeypatch.setattr(req_mod, "get", lambda *a, **kw: resp)
        result = finder._fetch_wikidata_p18_image("Completely Unknown XYZ Person")
        assert result is None

    def test_wikidata_p18_returns_none_when_no_p18_claim(self, finder, monkeypatch):
        """Tier 5 returns None when entity has no P18 (image) property."""
        import requests as req_mod
        from unittest.mock import MagicMock

        search_resp = MagicMock()
        search_resp.status_code = 200
        search_resp.json.return_value = {"search": [{"id": "Q999999"}]}

        p18_resp = MagicMock()
        p18_resp.status_code = 200
        p18_resp.json.return_value = {"claims": {}}  # no P18

        def fake_get(url, params=None, **kwargs):
            if "wbsearchentities" in str(params or {}):
                return search_resp
            return p18_resp

        monkeypatch.setattr(req_mod, "get", fake_get)
        result = finder._fetch_wikidata_p18_image("Some Person With No Image")
        assert result is None

    # ── Tier 8: Wikimedia Commons search ─────────────────────────────────────

    def test_commons_search_filters_non_portrait_files(self, finder, monkeypatch):
        """Tier 8 skips files with keywords like map, flag, icon, diagram."""
        import requests as req_mod
        from unittest.mock import MagicMock

        search_resp = MagicMock()
        search_resp.status_code = 200
        search_resp.json.return_value = {
            "query": {
                "search": [
                    {"title": "File:Alan_Turing_map.jpg"},
                    {"title": "File:Alan_Turing_icon.png"},
                    {"title": "File:Alan_Turing_diagram.jpg"},
                    {"title": "File:Alan_Turing_flag.jpg"},
                ]
            }
        }

        monkeypatch.setattr(req_mod, "get", lambda *a, **kw: search_resp)
        results = finder._fetch_wikimedia_commons_search("Alan Turing", limit=3)
        # All filtered out — no imageinfo calls needed
        assert results == []

    def test_commons_search_returns_none_on_api_error(self, finder, monkeypatch):
        """Tier 8 returns empty list gracefully when the API call fails."""
        import requests as req_mod
        from unittest.mock import MagicMock

        resp = MagicMock()
        resp.status_code = 503

        monkeypatch.setattr(req_mod, "get", lambda *a, **kw: resp)
        results = finder._fetch_wikimedia_commons_search("Alan Turing")
        assert results == []

    # ── Tier 9: DBpedia ───────────────────────────────────────────────────────

    def test_dbpedia_returns_none_when_name_not_matched(self, finder, monkeypatch):
        """Tier 9 returns None when DBpedia results don't match the name."""
        import requests as req_mod
        from unittest.mock import MagicMock

        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {
            "docs": [
                {"label": ["Completely Different Person"], "thumbnail": ["https://example.com/a.jpg"]}
            ]
        }

        monkeypatch.setattr(req_mod, "get", lambda *a, **kw: resp)
        result = finder._fetch_dbpedia_image("Alan Turing")
        assert result is None

    def test_dbpedia_returns_none_when_no_thumbnail(self, finder, monkeypatch):
        """Tier 9 returns None when DBpedia doc has no thumbnail field."""
        import requests as req_mod
        from unittest.mock import MagicMock

        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {
            "docs": [{"label": ["Alan Turing"], "thumbnail": []}]
        }

        monkeypatch.setattr(req_mod, "get", lambda *a, **kw: resp)
        result = finder._fetch_dbpedia_image("Alan Turing")
        assert result is None

    # ── URL cache (Tier 2 / Gemini self-caching) ──────────────────────────────

    def test_cache_discovered_url_persists_to_disk(self, tmp_path):
        """Gemini-discovered URLs are written to url_cache.json alongside download_dir."""
        import json
        finder = ReferenceImageFinder(download_dir=tmp_path / "refs")
        finder._cache_discovered_url("Alan Turing", "https://example.com/turing.jpg")

        cache_file = tmp_path / "url_cache.json"
        assert cache_file.exists()
        cache = json.loads(cache_file.read_text())
        assert cache["Alan Turing"] == "https://example.com/turing.jpg"

    def test_load_url_cache_returns_empty_when_no_file(self, tmp_path):
        """_load_url_cache returns {} when no cache file exists yet."""
        finder = ReferenceImageFinder(download_dir=tmp_path / "refs")
        cache = finder._load_url_cache()
        assert cache == {}

    def test_cache_roundtrip(self, tmp_path):
        """Writing and reading back the cache gives the same URL."""
        finder = ReferenceImageFinder(download_dir=tmp_path / "refs")
        finder._cache_discovered_url("Marie Curie", "https://example.com/curie.jpg")
        cache = finder._load_url_cache()
        assert cache.get("Marie Curie") == "https://example.com/curie.jpg"

    def test_cache_multiple_people(self, tmp_path):
        """Multiple people can be cached without collision."""
        finder = ReferenceImageFinder(download_dir=tmp_path / "refs")
        finder._cache_discovered_url("Alan Turing", "https://example.com/turing.jpg")
        finder._cache_discovered_url("Marie Curie", "https://example.com/curie.jpg")
        cache = finder._load_url_cache()
        assert len(cache) == 2
        assert cache["Alan Turing"] == "https://example.com/turing.jpg"
        assert cache["Marie Curie"] == "https://example.com/curie.jpg"

    # ── Cascade early-exit behavior ───────────────────────────────────────────

    def test_cascade_stops_at_tier1_when_confirmed_url_valid(
        self, tmp_path, monkeypatch
    ):
        """Cascade returns immediately after Tier 1 when confirmed URL is valid."""
        import io
        import requests as req_mod
        from unittest.mock import MagicMock
        from PIL import Image as PILImage

        # Ensure "David Lary" is in confirmed URLs
        finder = ReferenceImageFinder(download_dir=tmp_path / "refs")
        assert finder._lookup_confirmed_url("David Lary") is not None

        img_bytes = io.BytesIO()
        PILImage.new("RGB", (512, 682)).save(img_bytes, "JPEG")
        raw = img_bytes.getvalue() + b"\x00" * 20_000

        # HTTP client mock for httpx (used by _validate_url)
        from unittest.mock import patch
        dl_resp = MagicMock()
        dl_resp.status_code = 200
        dl_resp.content = raw

        with patch.object(finder.http_client, "get", return_value=dl_resp):
            subject = SubjectData(name="David Lary", birth_year=1965, era="Contemporary")
            # Track whether Tier 4+ APIs are called
            tier4_called = [False]
            original_wikidata = finder._fetch_wikidata_p18_image
            def spy_wikidata(name):
                tier4_called[0] = True
                return original_wikidata(name)
            monkeypatch.setattr(finder, "_fetch_wikidata_p18_image", spy_wikidata)

            results = finder.find_reference_images(subject, max_images=1)

        assert len(results) >= 1
        # Tier 4 should NOT have been called because Tier 1 satisfied max_images=1
        assert not tier4_called[0], "Cascade should have stopped at Tier 1"

    def test_cascade_deduplicates_same_url_from_multiple_tiers(self, tmp_path, monkeypatch):
        """If two tiers return the same URL, it only appears once in results."""
        import io
        import requests as req_mod
        from unittest.mock import MagicMock, patch
        from PIL import Image as PILImage

        finder = ReferenceImageFinder(download_dir=tmp_path / "refs")

        SAME_URL = "https://example.com/same.jpg"
        img_bytes = io.BytesIO()
        PILImage.new("RGB", (600, 800)).save(img_bytes, "JPEG")
        raw = img_bytes.getvalue() + b"\x00" * 20_000

        dl_resp = MagicMock()
        dl_resp.status_code = 200
        dl_resp.content = raw

        # Pre-populate cache with the SAME_URL so Tier 2 returns it
        finder._cache_discovered_url("Test Person", SAME_URL)

        # Make Tier 4 (Wikipedia REST) also return the same URL
        rest_resp = MagicMock()
        rest_resp.status_code = 200
        rest_resp.json.return_value = {"originalimage": {"source": SAME_URL}}

        monkeypatch.setattr(req_mod, "get", lambda *a, **kw: rest_resp)

        with patch.object(finder.http_client, "get", return_value=dl_resp):
            subject = SubjectData(name="Test Person", birth_year=1900, era="20th Century")
            results = finder.find_reference_images(subject, max_images=5)

        # Despite multiple tiers returning the same URL, it appears at most once
        urls = [r.url for r in results]
        assert urls.count(SAME_URL) <= 1, f"Duplicate URL found: {urls}"


# ---------------------------------------------------------------------------
# Held-out reference validation
# ---------------------------------------------------------------------------

class TestHeldOutValidationSplit:
    """Tests for the train/test split of reference images.

    When we have multiple reference images for a subject we split them into:
      - generation set  (sent to Gemini to guide portrait creation)
      - validation set  (withheld; used for independent post-generation check)

    This gives us zero-trust independent verification that the model has
    correctly depicted the right person.
    """

    @pytest.fixture
    def finder(self, tmp_path):
        return ReferenceImageFinder(download_dir=tmp_path / "refs")

    def _make_ref(self, url: str, score: float = 0.8) -> ReferenceImage:
        return ReferenceImage(
            url=url, source="test", authenticity_score=score,
            quality_score=score, relevance_score=score, era_match=True,
            combined_score=score,
        )

    def test_split_three_images_gives_two_gen_one_val(self, finder):
        """With 3 images: 2 go to generation, 1 is held out for validation."""
        refs = [self._make_ref(f"https://ex.com/{i}.jpg") for i in range(3)]
        gen, val = finder.split_for_generation_and_validation(refs)
        assert len(gen) == 2
        assert len(val) == 1

    def test_split_five_images_gives_three_gen_two_val(self, finder):
        """With 5 images: 3 go to generation, 2 are held out."""
        refs = [self._make_ref(f"https://ex.com/{i}.jpg") for i in range(5)]
        gen, val = finder.split_for_generation_and_validation(refs)
        assert len(gen) == 3
        assert len(val) == 2

    def test_split_one_image_all_to_gen_nothing_held_out(self, finder):
        """With 1 image: it goes to generation; validation set is empty (no penalty)."""
        refs = [self._make_ref("https://ex.com/only.jpg")]
        gen, val = finder.split_for_generation_and_validation(refs)
        assert len(gen) == 1
        assert len(val) == 0

    def test_split_two_images_gives_one_gen_one_val(self, finder):
        """With 2 images: 1 goes to generation, 1 is held out."""
        refs = [self._make_ref(f"https://ex.com/{i}.jpg") for i in range(2)]
        gen, val = finder.split_for_generation_and_validation(refs)
        assert len(gen) == 1
        assert len(val) == 1

    def test_split_empty_returns_empty_both(self, finder):
        """With 0 images: both sets are empty."""
        gen, val = finder.split_for_generation_and_validation([])
        assert gen == []
        assert val == []

    def test_split_gen_and_val_sets_are_disjoint(self, finder):
        """Generation and validation sets must not share any images."""
        refs = [self._make_ref(f"https://ex.com/{i}.jpg") for i in range(5)]
        gen, val = finder.split_for_generation_and_validation(refs)
        gen_urls = {r.url for r in gen}
        val_urls = {r.url for r in val}
        assert gen_urls.isdisjoint(val_urls), "Gen and val sets must not overlap"

    def test_split_highest_scored_images_go_to_generation(self, finder):
        """The N best-scored images go to generation; lower-scored ones to validation."""
        # Image A has highest score; Image B medium; Image C lowest
        ref_a = self._make_ref("https://ex.com/A.jpg", score=0.95)
        ref_b = self._make_ref("https://ex.com/B.jpg", score=0.80)
        ref_c = self._make_ref("https://ex.com/C.jpg", score=0.65)
        refs = [ref_a, ref_b, ref_c]
        gen, val = finder.split_for_generation_and_validation(refs)
        gen_urls = {r.url for r in gen}
        assert "https://ex.com/A.jpg" in gen_urls, "Highest-scored image must be in gen set"
        assert "https://ex.com/B.jpg" in gen_urls, "Second-highest must be in gen set"
        assert "https://ex.com/C.jpg" not in gen_urls, "Lowest-scored must be held out"

    def test_split_custom_n_gen(self, finder):
        """Custom n_gen parameter overrides the default 2."""
        refs = [self._make_ref(f"https://ex.com/{i}.jpg") for i in range(5)]
        gen, val = finder.split_for_generation_and_validation(refs, n_gen=4)
        assert len(gen) == 4
        assert len(val) == 1
