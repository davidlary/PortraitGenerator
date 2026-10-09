"""Tests for portrait_generator.utils.caption_check (2.10.0 tesseract caption gate)."""
import logging

import pytest
from PIL import Image

from portrait_generator.core.overlay import TitleOverlayEngine
from portrait_generator.utils import caption_check as cc


def _rendered(name="Arthur A. Few", years="1939-2022", color=(90, 110, 130)):
    base = Image.new("RGB", (896, 1200), color)
    return TitleOverlayEngine().add_overlay(base, name=name, years=years)


def _read(lines, years=None, idx=None):
    return cc.CaptionRead(
        text="\n".join(lines), lines=tuple(lines), years=years, years_line_index=idx,
        min_confidence=95.0, mean_confidence=96.0, engine="test", crop_fraction=0.17, scale=2,
    )


# ---------------------------------------------------------------- pure logic
class TestPureComparison:
    def test_normalize(self):
        assert cc.normalize_name("  José  O'Neil ") == "jose o neil"
        assert cc.normalize_years("1939 – 2022") == "1939-2022"
        assert cc.normalize_years(None) is None

    def test_similarity(self):
        assert cc.name_similarity("Arthur A. Few", "ARTHUR A FEW") == 1.0
        assert cc.name_similarity("", "x") == 0.0
        assert cc.name_similarity("Arthur A. Few", "Marie Curie") < 0.75

    def test_compare_ok(self):
        v = cc.compare(_read(["Arthur A. Few", "1939-2022"], "1939-2022", 1), "Arthur A. Few", "1939-2022")
        assert v.ok and v.status == "ok"
        assert v.as_sidecar()["status"] == "ok"
        assert v.as_dict()["expected_years"] == "1939-2022"

    def test_compare_wrong_years(self):
        v = cc.compare(_read(["Arthur A. Few", "1975-Present"], "1975-Present", 1),
                       "Arthur A. Few", "1939-2022")
        assert not v.ok and "1975-Present" in v.reason

    def test_compare_missing_years(self):
        v = cc.compare(_read(["Arthur A. Few"]), "Arthur A. Few", "1939-2022")
        assert not v.ok and "no year token" in v.reason

    def test_compare_unexpected_years(self):
        v = cc.compare(_read(["Arthur A. Few", "b. 1939"], "b. 1939", 1), "Arthur A. Few", None)
        assert not v.ok and "no years line expected" in v.reason

    def test_compare_no_years_ok(self):
        assert cc.compare(_read(["Arthur A. Few"]), "Arthur A. Few", None).ok

    def test_compare_wrapped_name(self):
        v = cc.compare(_read(["Maria Gaetana", "Agnesi", "1718-1799"], "1718-1799", 2),
                       "Maria Gaetana Agnesi", "1718-1799")
        assert v.ok

    def test_compare_same_line(self):
        v = cc.compare(_read(["Arthur A. Few 1939-2022"], "1939-2022", 0), "Arthur A. Few", "1939-2022")
        assert v.ok

    def test_compare_wrong_name(self):
        v = cc.compare(_read(["Marie Curie", "1939-2022"], "1939-2022", 1), "Arthur A. Few", "1939-2022")
        assert not v.ok and "name similarity" in v.reason

    @pytest.mark.parametrize("text", ["1939-2022", "460 BCE-370 BCE", "1947 - Present", "1939–2022"])
    def test_year_range_re(self, text):
        assert cc.YEAR_RANGE_RE.search(text)

    @pytest.mark.parametrize("text", ["b. 1939", "d. 2022", "d. 30 BCE"])
    def test_single_year_re(self, text):
        assert cc.SINGLE_YEAR_RE.search(text)

    def test_mismatch_error_prefix(self):
        e = cc.CaptionMismatchError("detail")
        assert str(e).startswith("CAPTION-MISMATCH:")

    def test_verify_empty_name(self):
        with pytest.raises(ValueError):
            cc.verify_caption(Image.new("RGB", (10, 10)), " ", None)


# ---------------------------------------------------------------- gate wiring
class TestCaptionGate:
    def _verdict(self, ok):
        return cc.CaptionVerdict(ok=ok, expected_name="A", expected_years="1939-2022",
                                 observed_text="A\n1975-Present", observed_years="1975-Present",
                                 name_similarity=1.0, reason="r", engine="t", crop_fraction=0.17)

    def test_ok(self, monkeypatch):
        monkeypatch.setattr(cc, "verify_caption", lambda *a, **k: self._verdict(True))
        assert cc.caption_gate(Image.new("RGB", (4, 4)), "A", "1939-2022", enforce=True)["status"] == "ok"

    def test_mismatch_enforced(self, monkeypatch):
        monkeypatch.setattr(cc, "verify_caption", lambda *a, **k: self._verdict(False))
        with pytest.raises(cc.CaptionMismatchError) as ei:
            cc.caption_gate(Image.new("RGB", (4, 4)), "A", "1939-2022", enforce=True, label="Painting")
        assert str(ei.value).startswith("CAPTION-MISMATCH:")
        assert ei.value.verdict.observed_years == "1975-Present"

    def test_mismatch_not_enforced(self, monkeypatch, caplog):
        monkeypatch.setattr(cc, "verify_caption", lambda *a, **k: self._verdict(False))
        with caplog.at_level(logging.WARNING):
            out = cc.caption_gate(Image.new("RGB", (4, 4)), "A", "1939-2022", enforce=False)
        assert out["status"] == "mismatch"
        assert "mismatch" in caplog.text

    def test_unavailable(self, monkeypatch, caplog):
        def boom(*a, **k):
            raise cc.CaptionCheckUnavailable("no tesseract")
        monkeypatch.setattr(cc, "verify_caption", boom)
        with caplog.at_level(logging.WARNING):
            out = cc.caption_gate(Image.new("RGB", (4, 4)), "A", None, enforce=True)
        assert out["status"] == "unavailable" and "no tesseract" in out["reason"]


# ---------------------------------------------------------------- real OCR
needs_ocr = pytest.mark.skipif(not cc.caption_check_available(), reason="tesseract not installed")


@needs_ocr
class TestRealOcr:
    def test_rendered_caption_ok(self):
        v = cc.verify_caption(_rendered(), "Arthur A. Few", "1939-2022")
        assert v.ok, v.reason
        assert cc.normalize_years(v.observed_years) == "1939-2022"

    def test_wrong_expected_years_mismatch(self):
        v = cc.verify_caption(_rendered(), "Arthur A. Few", "1975-Present")
        assert not v.ok

    def test_no_years_line(self):
        img = _rendered(years=None)
        read = cc.read_caption(img)
        assert read.years is None
        assert cc.verify_caption(img, "Arthur A. Few", None).ok

    def test_single_year_and_path_input(self, tmp_path):
        p = tmp_path / "x.png"
        _rendered(years="b. 1939", color=(220, 220, 210)).save(p)
        v = cc.verify_caption(p, "Arthur A. Few", "b. 1939")
        assert v.ok, v.reason

    def test_gate_enforced_mismatch_raises(self):
        with pytest.raises(cc.CaptionMismatchError):
            cc.caption_gate(_rendered(), "Arthur A. Few", "1975-Present", enforce=True)
