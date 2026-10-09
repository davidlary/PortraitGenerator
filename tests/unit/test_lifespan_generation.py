"""2.10.0 integration-level tests: researcher root-cause fixes, overlay years=None,
sidecar caption fields, and generator lifespan=/CAPTION-MISMATCH wiring.

Hermetic: no network, image generation is a stub returning a solid image.
"""
import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from PIL import Image

from portrait_generator.api.models import EvaluationResult, SubjectData
from portrait_generator.core import generator as basic_mod
from portrait_generator.core import generator_enhanced as enh_mod
from portrait_generator.core import researcher as researcher_mod
from portrait_generator.core.overlay import TitleOverlayEngine
from portrait_generator.core.portrait_verifier import PortraitVerifier
from portrait_generator.core.researcher import BiographicalResearcher
from portrait_generator.lifespan import Lifespan
from portrait_generator.utils.caption_check import CaptionMismatchError


# ------------------------------------------------------------------ researcher
@pytest.fixture
def researcher():
    return BiographicalResearcher(MagicMock())


class TestResearcherRootCauseFixes:
    def test_not_publicly_available_is_estimated(self, researcher):
        sd = researcher._parse_research_response(
            "Zz Unlisted Person", "FULL NAME: Zz Unlisted Person\nBIRTH YEAR: Not publicly available\nERA: Modern\n"
        )
        assert sd.birth_year_estimated is True
        assert sd.display_years is None
        assert sd.display_birth_year is None

    def test_twentieth_century_is_not_year_20(self, researcher):
        sd = researcher._parse_research_response(
            "Zz Century Person", "FULL NAME: Zz Century Person\nBIRTH YEAR: 20th century\nERA: Modern\n"
        )
        assert sd.birth_year != 20
        assert sd.birth_year_estimated is True
        assert sd.display_years is None

    def test_four_digit_year_still_parses(self, researcher):
        sd = researcher._parse_research_response(
            "Zz Real Person", "FULL NAME: Zz Real Person\nBIRTH YEAR: 1939\nDEATH YEAR: 2022\nERA: Modern\n"
        )
        assert (sd.birth_year, sd.death_year, sd.birth_year_estimated) == (1939, 2022, False)
        assert sd.display_years == "1939-2022"

    def test_bce_two_digit_year_still_parses(self, researcher):
        sd = researcher._parse_research_response(
            "Zz Ancient Person", "FULL NAME: Zz Ancient Person\nBIRTH YEAR: 69 BCE\nDEATH YEAR: 30 BCE\nERA: Ancient\n"
        )
        assert sd.birth_year == -69 and sd.birth_year_estimated is False

    def test_estimated_prompt_context(self, researcher):
        sd = researcher._parse_research_response(
            "Zz Unlisted Person", "BIRTH YEAR: unknown\nERA: Modern\n"
        )
        assert researcher.get_prompt_context(sd)["years"] == "unknown"


class TestSaveVerifiedBiography:
    @pytest.fixture
    def yaml_path(self, tmp_path, monkeypatch):
        p = tmp_path / "verified_biographies.yaml"
        monkeypatch.setattr(researcher_mod, "_BIO_YAML_PATH", p)
        return p

    def test_refuses_estimated(self, yaml_path):
        assert researcher_mod._save_verified_biography("X", 1975, None, "male", birth_year_estimated=True) is False
        assert not yaml_path.exists()

    @pytest.mark.parametrize("birth, death", [(-6000, None), (1939, 99999)])
    def test_refuses_implausible(self, yaml_path, birth, death):
        assert researcher_mod._save_verified_biography("X", birth, death, "male") is False
        assert not yaml_path.exists()

    def test_writes_real(self, yaml_path):
        assert researcher_mod._save_verified_biography("X", 1939, 2022, "male", notes="n") is True
        assert "1939" in yaml_path.read_text()


# ------------------------------------------------------------------ overlay
class TestOverlayYearsNone:
    def test_no_years_line(self):
        img = Image.new("RGB", (896, 1200), (100, 100, 100))
        out = TitleOverlayEngine().add_overlay(img, name="Arthur A. Few", years=None)
        assert out.size == img.size
        assert out.tobytes() != img.tobytes()  # bar + name were drawn

    def test_empty_years_still_rejected(self):
        with pytest.raises(ValueError):
            TitleOverlayEngine().add_overlay(Image.new("RGB", (896, 1200)), name="A", years="  ")


# ------------------------------------------------------------------ sidecar
class TestSidecarKeys:
    def test_new_keys(self, tmp_path):
        p = tmp_path / "A-Painting-1.png"
        Image.new("RGB", (4, 4)).save(p)
        sd = Lifespan(None, 2022).apply_to(SubjectData(name="A", birth_year=1940, era="Modern"))
        PortraitVerifier.write_sidecar(p, sd, caption_name="A", caption_check={"status": "ok"})
        meta = json.loads(p.with_suffix(".meta.json").read_text())
        assert meta["caption_name"] == "A"
        assert meta["caption_years"] == "d. 2022"
        assert meta["lifespan_source"] == "caller"
        assert meta["caption_check"] == {"status": "ok"}
        for old in ("name", "birth_year", "death_year", "era", "gender", "generation_timestamp", "subject_hash"):
            assert old in meta

    def test_defaults(self, tmp_path):
        p = tmp_path / "B-Painting-1.png"
        Image.new("RGB", (4, 4)).save(p)
        PortraitVerifier.write_sidecar(p, SubjectData(name="B", birth_year=1879, death_year=1955, era="x"))
        meta = json.loads(p.with_suffix(".meta.json").read_text())
        assert meta["caption_name"] == "B" and meta["caption_years"] == "1879-1955"
        assert meta["lifespan_source"] == "research" and meta["caption_check"] is None


# ------------------------------------------------------------------ generators
class _StubClient:
    def generate_image(self, *args, **kwargs):
        return Image.new("RGB", (896, 1200), (120, 100, 90))


def _researcher_stub():
    r = MagicMock()
    r.research_subject.return_value = SubjectData(
        name="Arthur A. Few", birth_year=1975, death_year=None, era="Modern",
        birth_year_estimated=True,
    )
    return r


def _evaluator_stub():
    e = MagicMock()
    e.evaluate_portrait.return_value = EvaluationResult(passed=True, scores={"overall": 1.0})
    return e


def _make(kind, tmp_path):
    args = (_StubClient(), _researcher_stub(), TitleOverlayEngine(), _evaluator_stub(), tmp_path)
    if kind == "enhanced":
        return enh_mod.EnhancedPortraitGenerator(*args, settings=None), enh_mod
    return basic_mod.PortraitGenerator(*args), basic_mod


@pytest.mark.parametrize("kind", ["enhanced", "basic"])
class TestGeneratorLifespan:
    def test_caller_lifespan_drives_sidecar(self, kind, tmp_path, monkeypatch):
        gen, mod = _make(kind, tmp_path)
        seen = {}

        def fake_gate(image, name, years, *, enforce, label=""):
            seen.update(name=name, years=years, enforce=enforce)
            return {"status": "ok", "observed_text": f"{name}\n{years}", "observed_years": years, "reason": "stub"}

        monkeypatch.setattr(mod, "caption_gate", fake_gate)
        res = gen.generate_portrait("Arthur A. Few", styles=["Painting"],
                                    lifespan={"birth_year": 1939, "death_year": 2022})
        assert res.success, res.errors
        assert seen == {"name": "Arthur A. Few", "years": "1939-2022", "enforce": True}
        meta = json.loads(Path(res.files["Painting"]).with_suffix(".meta.json").read_text())
        assert meta["lifespan_source"] == "caller"
        assert meta["caption_years"] == "1939-2022"
        assert meta["caption_check"]["status"] == "ok"

    def test_caption_mismatch_fails(self, kind, tmp_path, monkeypatch):
        gen, mod = _make(kind, tmp_path)
        calls = []

        def mismatch_gate(image, name, years, *, enforce, label=""):
            calls.append(1)
            raise CaptionMismatchError(f"{label}: years read '1975-Present' != expected {years!r}")

        monkeypatch.setattr(mod, "caption_gate", mismatch_gate)
        res = gen.generate_portrait("Arthur A. Few", styles=["Painting"],
                                    lifespan=Lifespan(1939, 2022))
        assert res.success is False
        assert res.errors and res.errors[0].startswith("CAPTION-MISMATCH:")
        assert len(calls) == 1  # no regeneration retry on a deterministic caption failure
        assert not list(tmp_path.glob("*.png"))  # nothing saved

    def test_no_lifespan_is_not_enforced_and_hides_placeholder(self, kind, tmp_path, monkeypatch):
        gen, mod = _make(kind, tmp_path)
        seen = {}

        def fake_gate(image, name, years, *, enforce, label=""):
            seen.update(years=years, enforce=enforce)
            return {"status": "mismatch", "observed_text": "", "observed_years": None, "reason": "stub"}

        monkeypatch.setattr(mod, "caption_gate", fake_gate)
        res = gen.generate_portrait("Arthur A. Few", styles=["Painting"])
        assert res.success, res.errors
        assert seen == {"years": None, "enforce": False}  # estimated 1975 never captioned
        meta = json.loads(Path(res.files["Painting"]).with_suffix(".meta.json").read_text())
        assert meta["lifespan_source"] == "research" and meta["caption_years"] is None

    def test_invalid_lifespan_fails_fast(self, kind, tmp_path):
        gen, _ = _make(kind, tmp_path)
        with pytest.raises(ValueError):
            gen.generate_portrait("Arthur A. Few", styles=["Painting"],
                                  lifespan={"birth_year": 2000, "death_year": 1990})
        gen.researcher.research_subject.assert_not_called()
