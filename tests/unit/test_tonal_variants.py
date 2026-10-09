"""Tests for portrait_generator.utils.tonal_variants (2.10.0: derived JPEG variants)."""
import numpy as np
import pytest
from PIL import Image

from portrait_generator.utils import tonal_variants as tv
from portrait_generator.utils.image_utils import convert_to_bw, convert_to_sepia


def _painting(tmp_path, name="Arthur_A_Few-Painting-1.png", size=(64, 48)):
    w, h = size
    arr = np.zeros((h, w, 3), dtype=np.uint8)
    arr[:, : w // 3] = (230, 230, 230)          # light
    arr[:, w // 3: 2 * w // 3] = (128, 128, 128)  # mid
    arr[:, 2 * w // 3:] = (25, 25, 25)            # dark
    path = tmp_path / name
    Image.fromarray(arr, "RGB").save(path)
    return path


class TestVariantPath:
    def test_jpg_naming(self, tmp_path):
        p = tmp_path / "Arthur_A_Few-Painting-3.png"
        assert tv.variant_path(p, "BW") == tmp_path / "Arthur_A_Few-BW-3.jpg"
        assert tv.variant_path(p, "Sepia") == tmp_path / "Arthur_A_Few-Sepia-3.jpg"

    def test_jpg_even_from_jpg_source(self, tmp_path):
        assert tv.variant_path(tmp_path / "X-Painting-1.jpeg", "BW").suffix == ".jpg"

    def test_non_painting_stem(self, tmp_path):
        with pytest.raises(ValueError):
            tv.variant_path(tmp_path / "Arthur_A_Few-Color-1.png", "BW")


class TestTransforms:
    def test_bw_is_L_and_preserves_luminance_order(self, tmp_path):
        with Image.open(_painting(tmp_path)) as im:
            bw = tv.to_bw(im)
        assert bw.mode == "L"
        a = np.asarray(bw, dtype=float)
        w = a.shape[1]
        light, mid, dark = a[:, w // 6].mean(), a[:, w // 2].mean(), a[:, 5 * w // 6].mean()
        assert light > mid > dark

    def test_sepia_mid_grey_is_warm(self):
        im = Image.new("RGB", (16, 16), (128, 128, 128))
        r, g, b = np.asarray(tv.to_sepia(im), dtype=float).reshape(-1, 3).mean(axis=0)
        assert r > g > b


class TestDeriveVariants:
    def test_writes_jpegs(self, tmp_path):
        src = _painting(tmp_path)
        out = tv.derive_variants(src)
        assert set(out) == {"BW", "Sepia"}
        with Image.open(out["BW"]) as bw:
            assert bw.format == "JPEG" and bw.mode == "L"
        with Image.open(out["Sepia"]) as sp:
            assert sp.format == "JPEG" and sp.mode == "RGB"
            assert sp.size == (64, 48)
            # q95 luma table max is 12 (default q75 would be ~60)
            assert max(sp.quantization[0]) <= 12
        assert not list(tmp_path.glob("*.part"))

    def test_skip_existing_vs_overwrite(self, tmp_path):
        src = _painting(tmp_path)
        out = tv.derive_variants(src, ["BW"])
        before = out["BW"].stat().st_mtime_ns
        out["BW"].write_bytes(b"sentinel")
        tv.derive_variants(src, ["BW"])
        assert out["BW"].read_bytes() == b"sentinel"  # kept
        tv.derive_variants(src, ["BW"], overwrite=True)
        assert out["BW"].read_bytes() != b"sentinel"
        assert out["BW"].stat().st_mtime_ns >= before

    def test_icc_profile_copied(self, tmp_path):
        src = tmp_path / "Y-Painting-1.png"
        fake_icc = b"\x00" * 128
        Image.new("RGB", (8, 8), (100, 120, 140)).save(src, icc_profile=fake_icc)
        out = tv.derive_variants(src, ["Sepia"])
        with Image.open(out["Sepia"]) as sp:
            assert sp.info.get("icc_profile") == fake_icc

    def test_save_rejects_bad_mode(self, tmp_path):
        with pytest.raises(ValueError):
            tv._save(Image.new("RGBA", (4, 4)), tmp_path / "Z-BW-1.jpg", Image.new("RGB", (4, 4)))


class TestCli:
    def test_comma_styles(self, tmp_path, capsys):
        src = _painting(tmp_path)
        assert tv.main([str(src), "--styles", "BW,Sepia"]) == 0
        assert (tmp_path / "Arthur_A_Few-BW-1.jpg").exists()
        assert (tmp_path / "Arthur_A_Few-Sepia-1.jpg").exists()
        assert "BW\t" in capsys.readouterr().out

    def test_space_styles_single(self, tmp_path):
        src = _painting(tmp_path)
        assert tv.main([str(src), "--styles", "Sepia"]) == 0
        assert not (tmp_path / "Arthur_A_Few-BW-1.jpg").exists()

    def test_unknown_style(self, tmp_path):
        with pytest.raises(SystemExit):
            tv.main([str(_painting(tmp_path)), "--styles", "BW,Color"])

    def test_failure_rc(self, tmp_path, capsys):
        bad = tmp_path / "bad-Color-1.png"
        Image.new("RGB", (4, 4)).save(bad)
        assert tv.main([str(bad)]) == 1
        assert "FAILED" in capsys.readouterr().err


class TestImageUtilsDelegation:
    def test_convert_to_bw_rgb_gray(self):
        out = convert_to_bw(Image.new("RGB", (8, 8), (200, 50, 50)))
        assert out.mode == "RGB"
        r, g, b = np.asarray(out, dtype=int).reshape(-1, 3).T
        assert (r == g).all() and (g == b).all()

    def test_convert_to_bw_low_contrast(self):
        out = convert_to_bw(Image.new("RGB", (8, 8), (200, 50, 50)), enhance_contrast=0.5)
        assert out.mode == "RGB"

    def test_convert_to_sepia_does_not_mutate(self):
        src = Image.new("RGB", (8, 8), (128, 128, 128))
        before = src.tobytes()
        out = convert_to_sepia(src)
        assert src.tobytes() == before
        r, g, b = np.asarray(out, dtype=float).reshape(-1, 3).mean(axis=0)
        assert r > g > b

    def test_convert_to_sepia_partial_intensity(self):
        src = Image.new("RGB", (8, 8), (128, 128, 128))
        full = np.asarray(convert_to_sepia(src, intensity=1.0), dtype=float)
        half = np.asarray(convert_to_sepia(src, intensity=0.5), dtype=float)
        assert (full[..., 0] - full[..., 2]).mean() > (half[..., 0] - half[..., 2]).mean()
