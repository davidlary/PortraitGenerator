"""Tests for portrait_generator.lifespan (2.10.0)."""
import pytest

from portrait_generator.api.models import SubjectData
from portrait_generator.lifespan import (
    EARLIEST_PLAUSIBLE_YEAR,
    MAX_PLAUSIBLE_LIFESPAN_YEARS,
    Lifespan,
    coerce_lifespan,
    current_year,
    format_year,
    plausible_year,
)


def _subject(**kw):
    base = dict(name="Arthur A. Few", birth_year=1975, death_year=None, era="Modern")
    base.update(kw)
    return SubjectData(**base)


class TestPlausibleYear:
    @pytest.mark.parametrize("y", [EARLIEST_PLAUSIBLE_YEAR, -460, 0, 1939, current_year()])
    def test_accepts(self, y):
        assert plausible_year(y)

    @pytest.mark.parametrize("y", [None, True, False, 1939.0, "1939",
                                   EARLIEST_PLAUSIBLE_YEAR - 1, current_year() + 1])
    def test_rejects(self, y):
        assert not plausible_year(y)

    def test_format_year(self):
        assert format_year(1939) == "1939"
        assert format_year(-460) == "460 BCE"


class TestCaptionYears:
    @pytest.mark.parametrize("ls, expected", [
        (Lifespan(1939, 2022), "1939-2022"),
        (Lifespan(1939, None, True), "1939-Present"),
        (Lifespan(1939, None), "b. 1939"),
        (Lifespan(1939, None, False), "b. 1939"),
        (Lifespan(None, 2022), "d. 2022"),
        (Lifespan(None, None), None),
        (Lifespan(None, None, True), None),
        (Lifespan(-460, -370), "460 BCE-370 BCE"),
        (Lifespan(-69, -30), "69 BCE-30 BCE"),
    ])
    def test_forms(self, ls, expected):
        assert ls.caption_years() == expected


class TestValidate:
    def test_valid_returns_self(self):
        ls = Lifespan(1939, 2022)
        assert ls.validate() is ls

    def test_small_year_is_numerically_plausible(self):
        # Plausibility is a range check; "20th century" artefacts are rejected
        # by the researcher's \d{3,4} regex, not by validate().
        Lifespan(20, None).validate()

    @pytest.mark.parametrize("ls, fragment", [
        (Lifespan(current_year() + 1, None), "not a plausible year"),
        (Lifespan(None, EARLIEST_PLAUSIBLE_YEAR - 1), "not a plausible year"),
        (Lifespan(True, None), "not a plausible year"),
        (Lifespan(1950, 1940), "precedes"),
        (Lifespan(1800, 1800 + MAX_PLAUSIBLE_LIFESPAN_YEARS + 1), "exceeds"),
        (Lifespan(1939, 2022, True), "contradicts"),
        (Lifespan(current_year() - 130, None, True), "implies age"),
        (Lifespan(1939, None, "yes"), "still_alive must be"),
    ])
    def test_invalid(self, ls, fragment):
        with pytest.raises(ValueError, match=fragment):
            ls.validate()

    def test_boundary_lifespan_ok(self):
        Lifespan(1800, 1800 + MAX_PLAUSIBLE_LIFESPAN_YEARS).validate()


class TestFromRecord:
    def test_ints(self):
        assert Lifespan.from_record({"birth_year": 1939, "death_year": 2022}) == Lifespan(1939, 2022)

    def test_strings_and_floats(self):
        ls = Lifespan.from_record({"birth_year": "1939", "death_year": 2022.0})
        assert (ls.birth_year, ls.death_year) == (1939, 2022)

    @pytest.mark.parametrize("raw, expected", [
        ("460 BCE", -460), ("460 BC", -460), ("-460", -460), ("1066 AD", 1066), ("1939.0", 1939),
    ])
    def test_era_strings(self, raw, expected):
        assert Lifespan.from_record({"birth_year": raw}).birth_year == expected

    @pytest.mark.parametrize("raw", ["", "Unknown", "none", "NULL", "n/a", "?", "-", None])
    def test_unknown_tokens(self, raw):
        assert Lifespan.from_record({"birth_year": raw, "death_year": 2022}).birth_year is None

    @pytest.mark.parametrize("raw", ["living", "Alive", "present", "Still Alive"])
    def test_living_death(self, raw):
        ls = Lifespan.from_record({"birth_year": 1960, "death_year": raw})
        assert ls.still_alive is True and ls.death_year is None
        assert ls.caption_years() == "1960-Present"

    def test_living_contradicts_still_alive_false(self):
        with pytest.raises(ValueError, match="contradicts"):
            Lifespan.from_record({"birth_year": 1960, "death_year": "living", "still_alive": False})

    @pytest.mark.parametrize("raw, expected", [
        ("true", True), ("No", False), (1, True), (0, False), ("unknown", None), (None, None),
    ])
    def test_still_alive_coercion(self, raw, expected):
        assert Lifespan.from_record({"birth_year": 1960, "still_alive": raw}).still_alive is expected

    @pytest.mark.parametrize("record", [
        {"birth_year": "circa 1900"},
        {"birth_year": 1939.5},
        {"birth_year": True},
        {"birth_year": [1939]},
        {"birth_year": "-460 BCE"},
        {"birth_year": 1960, "still_alive": "maybe"},
        {"birth_year": 1960, "still_alive": 2},
    ])
    def test_unparseable_raises(self, record):
        with pytest.raises(ValueError):
            Lifespan.from_record(record)

    def test_none_record(self):
        with pytest.raises(ValueError):
            Lifespan.from_record(None)

    def test_validates(self):
        with pytest.raises(ValueError, match="precedes"):
            Lifespan.from_record({"birth_year": 2000, "death_year": 1990})


class TestCoerceLifespan:
    def test_none(self):
        assert coerce_lifespan(None) is None

    def test_instance(self):
        ls = Lifespan(1939, 2022)
        assert coerce_lifespan(ls) is ls

    def test_mapping(self):
        assert coerce_lifespan({"birth_year": 1939, "death_year": 2022}) == Lifespan(1939, 2022)

    def test_invalid_instance(self):
        with pytest.raises(ValueError):
            coerce_lifespan(Lifespan(2000, 1990))

    def test_wrong_type(self):
        with pytest.raises(TypeError):
            coerce_lifespan((1939, 2022))


class TestApplyTo:
    def test_full(self):
        sd = Lifespan(1939, 2022).apply_to(_subject())
        assert sd.birth_year == 1939 and sd.death_year == 2022
        assert sd.caption_years == "1939-2022"
        assert sd.lifespan_source == "caller"
        assert sd.display_years == "1939-2022"
        assert sd.display_birth_year == 1939
        assert sd.birth_year_estimated is False

    def test_clears_estimated_flag(self):
        sd = Lifespan(1939, None, True).apply_to(_subject(birth_year_estimated=True))
        assert sd.birth_year_estimated is False
        assert sd.display_years == "1939-Present"

    def test_none_birth_keeps_research_but_never_displays(self):
        sd = Lifespan(None, 2022).apply_to(_subject(birth_year=1940))
        assert sd.birth_year == 1940  # kept for age arithmetic only
        assert sd.display_years == "d. 2022"
        assert sd.display_birth_year is None
        assert sd.birth_year_estimated is False

    def test_none_birth_inconsistent_research_marked_estimated(self):
        sd = Lifespan(None, 1900).apply_to(_subject(birth_year=1975))
        assert sd.birth_year_estimated is True
        assert sd.display_years == "d. 1900"
        sd2 = Lifespan(None, 1900).apply_to(_subject(birth_year=1700))
        assert sd2.birth_year_estimated is True

    def test_neither_known(self):
        sd = Lifespan(None, None).apply_to(_subject(death_year=2020, birth_year=1930))
        assert sd.death_year is None
        assert sd.display_years is None
        assert sd.display_birth_year is None

    def test_does_not_mutate_original(self):
        original = _subject()
        Lifespan(1939, 2022).apply_to(original)
        assert original.lifespan_source == "research" and original.caption_years is None

    def test_apply_validates(self):
        with pytest.raises(ValueError):
            Lifespan(2000, 1990).apply_to(_subject())


class TestSubjectDataDisplay:
    def test_research_default(self):
        sd = _subject(birth_year=1879, death_year=1955)
        assert sd.display_years == sd.formatted_years == "1879-1955"
        assert sd.display_birth_year == 1879

    def test_estimated_hides_birth(self):
        assert _subject(birth_year_estimated=True).display_years is None
        sd = _subject(birth_year_estimated=True, death_year=2001)
        assert sd.display_years == "d. 2001"
        assert sd.display_birth_year is None


def test_caption_display_name_strips_trailing_parentheticals():
    from portrait_generator.lifespan import caption_display_name

    assert caption_display_name("Mike Fisher (1962-Present)") == "Mike Fisher"
    assert caption_display_name('Robert Charles Geary ("Roy" Geary)') == "Robert Charles Geary"
    assert caption_display_name("bell hooks (born Gloria Jean Watkins)") == "bell hooks"
    assert caption_display_name("Richard C. Thompson (Richard Charles Thompson) (1963-Present)") == "Richard C. Thompson"
    assert caption_display_name("Arthur A. Few") == "Arthur A. Few"
    assert caption_display_name("(odd)") == "(odd)"
