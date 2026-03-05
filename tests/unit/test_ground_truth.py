"""Unit tests for utils/ground_truth.py — Wikipedia/Wikidata verification."""

import os
import pytest

from portrait_generator.utils.ground_truth import GroundTruthResult, GroundTruthVerifier
from portrait_generator.api.models import SubjectData

# Skip any test that actually hits Wikipedia/Wikidata if no internet marker set.
# These are still lightweight (no Gemini key needed) but need network.
_SKIP_NO_NET = pytest.mark.skipif(
    os.getenv("PORTRAIT_SKIP_NETWORK") == "1",
    reason="Network tests disabled (set PORTRAIT_SKIP_NETWORK=1 to skip)",
)


# ---------------------------------------------------------------------------
# GroundTruthResult dataclass
# ---------------------------------------------------------------------------

class TestGroundTruthResult:
    """Tests for GroundTruthResult dataclass construction."""

    def test_default_values(self):
        result = GroundTruthResult(name="Test Person")
        assert result.name == "Test Person"
        assert result.gender == "unknown"
        assert result.birth_year is None
        assert result.death_year is None
        assert result.wikipedia_url is None
        assert result.photo_url is None
        assert result.confidence == 0.0
        assert result.source == "none"
        assert result.conflicts == []

    def test_full_construction(self):
        result = GroundTruthResult(
            name="Alan Turing",
            gender="male",
            birth_year=1912,
            death_year=1954,
            wikipedia_url="https://en.wikipedia.org/wiki/Alan_Turing",
            photo_url="https://upload.wikimedia.org/test.jpg",
            confidence=0.9,
            source="both",
            conflicts=["some conflict"],
        )
        assert result.name == "Alan Turing"
        assert result.gender == "male"
        assert result.birth_year == 1912
        assert result.death_year == 1954
        assert result.confidence == 0.9
        assert result.source == "both"
        assert result.conflicts == ["some conflict"]


# ---------------------------------------------------------------------------
# GroundTruthVerifier — unit tests (no network)
# ---------------------------------------------------------------------------

class TestGroundTruthVerifierCrossValidate:
    """Tests for cross_validate() — pure logic, no network needed."""

    @pytest.fixture
    def verifier(self):
        return GroundTruthVerifier()

    @pytest.fixture
    def subject_data(self):
        return SubjectData(
            name="Alan Turing",
            birth_year=1912,
            death_year=1954,
            era="20th Century",
            gender="male",
        )

    def test_no_conflicts_when_data_matches(self, verifier, subject_data):
        gt = GroundTruthResult(
            name="Alan Turing",
            gender="male",
            birth_year=1912,
            death_year=1954,
            confidence=0.9,
        )
        conflicts = verifier.cross_validate(subject_data, gt)
        assert conflicts == []

    def test_detects_birth_year_mismatch(self, verifier, subject_data):
        gt = GroundTruthResult(
            name="Alan Turing",
            gender="male",
            birth_year=1900,  # differs by 12 years
            confidence=0.9,
        )
        conflicts = verifier.cross_validate(subject_data, gt)
        assert any("Birth year" in c for c in conflicts)

    def test_ignores_birth_year_within_tolerance(self, verifier, subject_data):
        gt = GroundTruthResult(
            name="Alan Turing",
            gender="male",
            birth_year=1913,  # differs by 1 (within tolerance of 2)
            confidence=0.9,
        )
        conflicts = verifier.cross_validate(subject_data, gt)
        assert not any("Birth year" in c for c in conflicts)

    def test_detects_death_year_mismatch(self, verifier, subject_data):
        gt = GroundTruthResult(
            name="Alan Turing",
            gender="male",
            birth_year=1912,
            death_year=1960,  # differs by 6
            confidence=0.9,
        )
        conflicts = verifier.cross_validate(subject_data, gt)
        assert any("Death year" in c for c in conflicts)

    def test_detects_gender_mismatch(self, verifier, subject_data):
        gt = GroundTruthResult(
            name="Alan Turing",
            gender="female",  # wrong
            birth_year=1912,
            confidence=0.9,
        )
        conflicts = verifier.cross_validate(subject_data, gt)
        assert any("Gender" in c or "gender" in c for c in conflicts)

    def test_no_conflict_when_confidence_low(self, verifier, subject_data):
        gt = GroundTruthResult(
            name="Alan Turing",
            gender="female",  # wrong — but should be ignored when confidence < 0.4
            birth_year=1900,
            confidence=0.3,
        )
        conflicts = verifier.cross_validate(subject_data, gt)
        assert conflicts == []

    def test_flags_gemini_alive_wikipedia_dead(self, verifier):
        # Gemini says still alive, Wikipedia says deceased
        data = SubjectData(
            name="Test Person",
            birth_year=1912,
            death_year=None,  # Gemini says alive
            era="20th Century",
        )
        gt = GroundTruthResult(
            name="Test Person",
            birth_year=1912,
            death_year=1954,  # Wikipedia says dead
            confidence=0.9,
        )
        conflicts = verifier.cross_validate(data, gt)
        assert any("alive" in c.lower() or "death" in c.lower() for c in conflicts)


class TestGroundTruthVerifierEnrich:
    """Tests for enrich_subject_data() — pure logic, no network."""

    @pytest.fixture
    def verifier(self):
        return GroundTruthVerifier()

    @pytest.fixture
    def subject_data(self):
        return SubjectData(
            name="Alan Turing",
            birth_year=1912,
            death_year=1954,
            era="20th Century",
            gender="unknown",
        )

    def test_gender_enriched_from_wikidata(self, verifier, subject_data):
        gt = GroundTruthResult(
            name="Alan Turing",
            gender="male",
            birth_year=1912,
            confidence=0.7,
        )
        enriched = verifier.enrich_subject_data(subject_data, gt)
        assert enriched.gender == "male"

    def test_low_confidence_does_not_override(self, verifier, subject_data):
        gt = GroundTruthResult(
            name="Alan Turing",
            gender="female",  # wrong, but low confidence
            birth_year=1900,
            confidence=0.3,  # too low
        )
        enriched = verifier.enrich_subject_data(subject_data, gt)
        # Should return original unchanged
        assert enriched.birth_year == 1912

    def test_photo_url_added_to_reference_sources(self, verifier, subject_data):
        gt = GroundTruthResult(
            name="Alan Turing",
            gender="male",
            birth_year=1912,
            photo_url="https://upload.wikimedia.org/turing.jpg",
            confidence=0.8,
        )
        enriched = verifier.enrich_subject_data(subject_data, gt)
        assert any("WIKIPEDIA_PHOTO:" in s for s in enriched.reference_sources)

    def test_wikipedia_url_added_to_reference_sources(self, verifier, subject_data):
        gt = GroundTruthResult(
            name="Alan Turing",
            gender="male",
            birth_year=1912,
            wikipedia_url="https://en.wikipedia.org/wiki/Alan_Turing",
            confidence=0.8,
        )
        enriched = verifier.enrich_subject_data(subject_data, gt)
        assert any("WIKIPEDIA:" in s for s in enriched.reference_sources)

    def test_original_data_returned_when_no_updates(self, verifier, subject_data):
        gt = GroundTruthResult(
            name="Alan Turing",
            gender="unknown",  # no gender to set
            confidence=0.8,   # high confidence but no birth year or photo
        )
        enriched = verifier.enrich_subject_data(subject_data, gt)
        assert enriched is subject_data or enriched.birth_year == subject_data.birth_year


# ---------------------------------------------------------------------------
# GroundTruthVerifier — year parsing
# ---------------------------------------------------------------------------

class TestParseYearsFromWikipedia:
    """Tests for Wikipedia year extraction regex."""

    @pytest.fixture
    def verifier(self):
        return GroundTruthVerifier()

    def test_parses_dash_range(self, verifier):
        data = {"description": "British mathematician (1912–1954)"}
        birth, death = verifier._parse_years_from_wikipedia(data)
        assert birth == 1912
        assert death == 1954

    def test_parses_born_only(self, verifier):
        data = {"description": "American scientist (born 1947)"}
        birth, death = verifier._parse_years_from_wikipedia(data)
        assert birth == 1947
        assert death is None

    def test_returns_none_when_no_years(self, verifier):
        data = {"description": "Famous scientist"}
        birth, death = verifier._parse_years_from_wikipedia(data)
        assert birth is None
        assert death is None

    def test_ignores_unrealistic_year(self, verifier):
        data = {"description": "born in year 999"}
        birth, death = verifier._parse_years_from_wikipedia(data)
        assert birth is None


# ---------------------------------------------------------------------------
# GroundTruthVerifier — network tests (Wikipedia/Wikidata)
# ---------------------------------------------------------------------------

class TestGroundTruthVerifierFetch:
    """Network tests — fetch from real Wikipedia/Wikidata APIs."""

    @pytest.fixture
    def verifier(self):
        return GroundTruthVerifier()

    @_SKIP_NO_NET
    def test_fetch_alan_turing_returns_result(self, verifier):
        """Alan Turing has a well-known Wikipedia page."""
        result = verifier.fetch("Alan Turing")
        assert result.name == "Alan Turing"
        # Should find at least Wikipedia data
        assert result.confidence > 0.0

    @_SKIP_NO_NET
    def test_fetch_alan_turing_gender(self, verifier):
        result = verifier.fetch("Alan Turing")
        # Wikidata should identify him as male
        assert result.gender == "male"

    @_SKIP_NO_NET
    def test_fetch_alan_turing_birth_year(self, verifier):
        result = verifier.fetch("Alan Turing")
        assert result.birth_year == 1912

    @_SKIP_NO_NET
    def test_fetch_unknown_person_returns_low_confidence(self, verifier):
        result = verifier.fetch("Zzz_Completely_Unknown_Person_12345")
        assert result.confidence == 0.0
        assert result.gender == "unknown"

    @_SKIP_NO_NET
    def test_fetch_returns_ground_truth_result(self, verifier):
        result = verifier.fetch("Marie Curie")
        assert isinstance(result, GroundTruthResult)
