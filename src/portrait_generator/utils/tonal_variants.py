"""Tonal variants of a finished portrait: a black-and-white (``BW``) and a
sepia-toned (``Sepia``) rendition saved beside the painting as
``<Name>-<BirthYear>-<Style>-<N>.jpg`` (2026-10-09, user requirement for
the Authura/OpenStax portrait pipeline, applied to every new portrait and
retrospectively to the whole Portraits repo).

Variants are ALWAYS written as JPEG (quality 95; BW as 8-bit ``L``, Sepia as
RGB 4:4:4; the source ICC profile is copied) whatever the painting's own
format: the painting is the lossless source and the variants are cheap,
re-derivable artefacts (PNG variants would roughly triple the size of the
Portraits git repository). ``X-Painting-1.png`` -> ``X-BW-1.jpg`` and
``X-Sepia-1.jpg``.

Command line::

    python -m portrait_generator.utils.tonal_variants <painting> [...] \
        [--styles BW,Sepia] [--overwrite] [--mix luminance|yellow|orange|red]

Existing variants are skipped unless ``--overwrite``.

Why the colour science lives here (and ``image_utils.convert_to_bw`` /
``convert_to_sepia`` now delegate to it, since 2.10.0)
----------------------------------------------------------------------
Before 2.10.0 those helpers were the textbook shortcuts and both were
visibly wrong on a painted portrait:

* ``Image.convert("L")`` mixes *gamma-encoded* sRGB with Rec. 601 weights.
  Luminance only adds linearly in linear light, so saturated colours come
  out at the wrong brightness (a strong red coat and a mid-green background
  that look equally bright end up different greys) and the result is then
  pushed through a global contrast multiplier that crushes both ends.
* The classic "sepia matrix" (0.393/0.769/0.189 ...) sums to 1.35 on a grey
  input, so every highlight above ~75 % clips to white and the whole image is
  washed in one flat yellow; it is also applied per pixel in Python.

What a *good* B&W / sepia conversion does (darkroom practice + modern colour
science), and what is implemented here
----------------------------------------------------------------------
B&W
  1. Decode sRGB to linear light (the sRGB transfer function, not a plain
     2.2 gamma).
  2. Mix the channels in linear light with the Rec. 709 / sRGB luminance
     weights (0.2126, 0.7152, 0.0722): that is the colorimetric luminance Y
     of each pixel, i.e. the tone a panchromatic film would record. A
     ``mix`` override reproduces the darkroom "yellow / orange filter"
     portrait renditions (lighter skin, darker skies) when wanted.
  3. Re-encode Y with the sRGB curve. This maps every neutral grey in the
     original to exactly itself (identity on greys), which L*-mapping would
     not.
  4. Tone balance ("well balanced"): a conservative levels stretch that
     clips only ``black_clip`` / ``white_clip`` of the pixels (0.1 % each by
     default) so a low-contrast painting uses the full range, followed by a
     mild smoothstep S-curve (``contrast`` = blend weight) for midtone
     separation. Both are endpoint-preserving and nearly idempotent.

Sepia
  A real sepia print is a *toned silver print*: the tonal structure is the
  B&W image, highlights stay close to paper white, the strongest brown sits
  in the midtones, and deep shadows stay near neutral. The hue also drifts,
  yellower in the highlights and redder in the shadows (split toning). That
  is modelled directly in OKLab/OKLCH (Ottosson 2020, the perceptual space
  adopted by CSS Color 4): lightness L is taken from the balanced B&W image
  unchanged, chroma follows a bell curve over L (``chroma_peak`` at
  ``peak_lightness``, with small ``chroma_highlight`` / ``chroma_shadow``
  floors for paper cream and warm blacks), hue interpolates from
  ``hue_shadow_deg`` to ``hue_highlight_deg``. Out-of-gamut pixels are
  brought back by reducing chroma at constant lightness (never by clipping
  RGB, which would shift tone).

Every number is a parameter of :class:`BWParams` / :class:`SepiaParams`;
the defaults are the tuned house look. Processing is float32 numpy end to
end; files are written at JPEG quality 95 with 4:4:4 chroma (sepia) or as
8-bit greyscale (BW), copying the source ICC profile when there is one.
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Optional, Tuple

import numpy as np
from PIL import Image

STYLE_BW = "BW"
STYLE_SEPIA = "Sepia"
STYLES: Tuple[str, ...] = (STYLE_BW, STYLE_SEPIA)

# <anything>-Painting-<N>  ->  group(1)=<anything>, group(2)=<N>
PAINTING_STEM_RE = re.compile(r"^(?P<base>.+)-Painting-(?P<n>\d+)$")

# Rec. 709 / sRGB luminance weights in linear light.
LUMINANCE_709: Tuple[float, float, float] = (0.2126, 0.7152, 0.0722)
# Darkroom contrast-filter renditions (linear-light channel mixes, sum 1).
CHANNEL_MIXES: Dict[str, Tuple[float, float, float]] = {
    "luminance": LUMINANCE_709,
    "yellow": (0.30, 0.62, 0.08),   # natural portrait rendition, slightly lighter skin
    "orange": (0.42, 0.52, 0.06),   # smoother skin, darker blue backgrounds
    "red": (0.60, 0.36, 0.04),      # dramatic, very light skin, black skies
}


@dataclass(frozen=True)
class BWParams:
    mix: Tuple[float, float, float] = LUMINANCE_709
    black_clip: float = 0.001   # fraction of pixels allowed to clip to black by the levels stretch
    white_clip: float = 0.001   # fraction allowed to clip to white
    contrast: float = 0.12      # smoothstep S-curve blend weight (0 = off, 1 = full smoothstep)

    def validate(self) -> None:
        if len(self.mix) != 3 or any(w < 0 for w in self.mix) or abs(sum(self.mix) - 1.0) > 1e-6:
            raise ValueError(f"mix must be three non-negative weights summing to 1, got {self.mix}")
        for name in ("black_clip", "white_clip"):
            v = getattr(self, name)
            if not 0.0 <= v < 0.5:
                raise ValueError(f"{name} must be in [0, 0.5), got {v}")
        if not 0.0 <= self.contrast <= 1.0:
            raise ValueError(f"contrast must be in [0, 1], got {self.contrast}")


@dataclass(frozen=True)
class SepiaParams:
    hue_shadow_deg: float = 50.0      # OKLCH hue in the shadows (redder brown)
    hue_highlight_deg: float = 78.0   # OKLCH hue in the highlights (yellower, paper cream)
    chroma_peak: float = 0.075        # OKLCH chroma at the tonal peak
    peak_lightness: float = 0.55      # OKLab L where the toning is strongest
    peak_width: float = 0.32          # Gaussian sigma of the bell over L
    chroma_highlight: float = 0.020   # residual warmth near white (cream paper)
    chroma_shadow: float = 0.010      # residual warmth near black

    def validate(self) -> None:
        for name in ("chroma_peak", "chroma_highlight", "chroma_shadow"):
            v = getattr(self, name)
            if not 0.0 <= v <= 0.4:
                raise ValueError(f"{name} must be in [0, 0.4], got {v}")
        if not 0.0 < self.peak_lightness < 1.0:
            raise ValueError(f"peak_lightness must be in (0, 1), got {self.peak_lightness}")
        if not 0.0 < self.peak_width <= 2.0:
            raise ValueError(f"peak_width must be in (0, 2], got {self.peak_width}")


# --------------------------------------------------------------------------
# colour science primitives (float32 numpy, values in [0, 1])
# --------------------------------------------------------------------------

def srgb_to_linear(c: np.ndarray) -> np.ndarray:
    c = np.clip(c, 0.0, 1.0).astype(np.float32)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4).astype(np.float32)


def linear_to_srgb(c: np.ndarray) -> np.ndarray:
    c = np.clip(c, 0.0, 1.0).astype(np.float32)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(c, 1 / 2.4) - 0.055).astype(np.float32)


# OKLab (Björn Ottosson, 2020): linear sRGB -> LMS -> cube root -> Lab.
_M1 = np.array([[0.4122214708, 0.5363325363, 0.0514459929],
                [0.2119034982, 0.6806995451, 0.1073969566],
                [0.0883024619, 0.2817188376, 0.6299787005]], dtype=np.float32)
_M2 = np.array([[0.2104542553, 0.7936177850, -0.0040720468],
                [1.9779984951, -2.4285922050, 0.4505937099],
                [0.0259040371, 0.7827717662, -0.8086757660]], dtype=np.float32)
_M2_INV = np.linalg.inv(_M2.astype(np.float64)).astype(np.float32)
_M1_INV = np.linalg.inv(_M1.astype(np.float64)).astype(np.float32)


def linear_srgb_to_oklab(rgb: np.ndarray) -> np.ndarray:
    lms = rgb @ _M1.T
    lms = np.cbrt(np.clip(lms, 0.0, None))
    return (lms @ _M2.T).astype(np.float32)


def oklab_to_linear_srgb(lab: np.ndarray) -> np.ndarray:
    lms = lab @ _M2_INV.T
    lms = lms ** 3
    return (lms @ _M1_INV.T).astype(np.float32)


# --------------------------------------------------------------------------
# B&W
# --------------------------------------------------------------------------

def _to_rgb_array(image: Image.Image) -> np.ndarray:
    if image.mode != "RGB":
        image = image.convert("RGB")
    return np.asarray(image, dtype=np.float32) / 255.0


def tone_balance(gray: np.ndarray, params: BWParams) -> np.ndarray:
    """Levels stretch (percentile clipping) + mild smoothstep S-curve on an
    sRGB-encoded grey image in [0, 1]. Endpoint preserving."""
    g = gray.astype(np.float32)
    if params.black_clip > 0 or params.white_clip > 0:
        low = float(np.quantile(g, params.black_clip)) if params.black_clip > 0 else float(g.min())
        high = float(np.quantile(g, 1.0 - params.white_clip)) if params.white_clip > 0 else float(g.max())
        if high - low > 1e-4:
            g = (g - low) / (high - low)
        g = np.clip(g, 0.0, 1.0)
    if params.contrast > 0:
        smooth = g * g * (3.0 - 2.0 * g)
        g = (1.0 - params.contrast) * g + params.contrast * smooth
    return g.astype(np.float32)


def bw_gray(image: Image.Image, params: Optional[BWParams] = None) -> np.ndarray:
    """sRGB-encoded, tone-balanced grey plane in [0, 1] (float32, HxW)."""
    params = params or BWParams()
    params.validate()
    rgb_lin = srgb_to_linear(_to_rgb_array(image))
    y = rgb_lin @ np.asarray(params.mix, dtype=np.float32)
    return tone_balance(linear_to_srgb(y), params)


def to_bw(image: Image.Image, params: Optional[BWParams] = None) -> Image.Image:
    """Black-and-white rendition as an 8-bit greyscale (``L``) image."""
    g = bw_gray(image, params)
    return Image.fromarray(np.clip(np.rint(g * 255.0), 0, 255).astype(np.uint8), mode="L")


# --------------------------------------------------------------------------
# Sepia (toned from the B&W plane in OKLCH)
# --------------------------------------------------------------------------

def _sepia_chroma(L: np.ndarray, p: SepiaParams) -> np.ndarray:
    bell = p.chroma_peak * np.exp(-0.5 * ((L - p.peak_lightness) / p.peak_width) ** 2)
    floor = p.chroma_shadow + (p.chroma_highlight - p.chroma_shadow) * L
    return np.maximum(bell, floor).astype(np.float32)


def _gamut_map_chroma(lab: np.ndarray, iterations: int = 10) -> np.ndarray:
    """Pull out-of-gamut OKLab pixels back inside sRGB by reducing chroma at
    constant lightness and hue (bisection on a chroma scale factor)."""
    rgb = oklab_to_linear_srgb(lab)
    out = np.any((rgb < -1e-4) | (rgb > 1.0 + 1e-4), axis=-1)
    if not np.any(out):
        return lab
    sub = lab[out]
    lo = np.zeros(len(sub), dtype=np.float32)
    hi = np.ones(len(sub), dtype=np.float32)
    for _ in range(iterations):
        mid = (lo + hi) / 2.0
        trial = sub.copy()
        trial[:, 1:] *= mid[:, None]
        r = oklab_to_linear_srgb(trial)
        ok = ~np.any((r < -1e-4) | (r > 1.0 + 1e-4), axis=-1)
        lo = np.where(ok, mid, lo)
        hi = np.where(ok, hi, mid)
    fixed = sub.copy()
    fixed[:, 1:] *= lo[:, None]
    lab = lab.copy()
    lab[out] = fixed
    return lab


def sepia_from_gray(gray: np.ndarray, params: Optional[SepiaParams] = None) -> np.ndarray:
    """sRGB-encoded HxWx3 float32 sepia image from an sRGB-encoded grey plane."""
    p = params or SepiaParams()
    p.validate()
    y = srgb_to_linear(gray)
    L = linear_srgb_to_oklab(np.stack([y, y, y], axis=-1))[..., 0]
    C = _sepia_chroma(L, p)
    h = np.deg2rad(p.hue_shadow_deg + (p.hue_highlight_deg - p.hue_shadow_deg) * L).astype(np.float32)
    lab = np.stack([L, C * np.cos(h), C * np.sin(h)], axis=-1).astype(np.float32)
    shape = lab.shape
    lab = _gamut_map_chroma(lab.reshape(-1, 3)).reshape(shape)
    return linear_to_srgb(oklab_to_linear_srgb(lab))


def to_sepia(image: Image.Image, bw: Optional[BWParams] = None,
             sepia: Optional[SepiaParams] = None) -> Image.Image:
    """Sepia-toned rendition (RGB), toned from the balanced B&W plane."""
    rgb = sepia_from_gray(bw_gray(image, bw), sepia)
    return Image.fromarray(np.clip(np.rint(rgb * 255.0), 0, 255).astype(np.uint8), mode="RGB")


# --------------------------------------------------------------------------
# File-level API: <base>-Painting-<N>.<any ext> -> <base>-<Style>-<N>.jpg
# --------------------------------------------------------------------------

VARIANT_SUFFIX = ".jpg"
VARIANT_FORMAT = "JPEG"
JPEG_QUALITY = 95


def variant_path(painting: Path, style: str) -> Path:
    """Path of the ``style`` variant of ``painting``: the ``Painting`` token
    of the stem is swapped for ``style`` and the suffix is always ``.jpg``
    (``X-Painting-1.png`` -> ``X-BW-1.jpg``)."""
    if style not in STYLES:
        raise ValueError(f"unknown style {style!r}; expected one of {STYLES}")
    painting = Path(painting)
    m = PAINTING_STEM_RE.match(painting.stem)
    if not m:
        raise ValueError(f"{painting.name} is not a <Name>-<BirthYear>-Painting-<N> file")
    return painting.with_name(f"{m.group('base')}-{style}-{m.group('n')}{VARIANT_SUFFIX}")


def _save(image: Image.Image, dest: Path, source: Image.Image) -> None:
    """Write ``image`` as JPEG q95 (4:4:4 for RGB), copying the source ICC
    profile, via ``<dest>.part`` + atomic rename so a crash never leaves a
    truncated variant under the final name."""
    kwargs: Dict[str, object] = {"quality": JPEG_QUALITY, "optimize": True}
    icc = source.info.get("icc_profile")
    if icc:
        kwargs["icc_profile"] = icc
    if image.mode == "RGB":
        kwargs["subsampling"] = 0  # 4:4:4 keeps the subtle toning free of chroma blocking
    elif image.mode != "L":
        raise ValueError(f"variant images must be mode L or RGB, got {image.mode}")
    tmp = dest.with_name(dest.name + ".part")
    image.save(tmp, format=VARIANT_FORMAT, **kwargs)
    tmp.replace(dest)


def derive_variants(painting: Path, styles: Iterable[str] = STYLES, *, overwrite: bool = False,
                    bw: Optional[BWParams] = None, sepia: Optional[SepiaParams] = None) -> Dict[str, Path]:
    """Write the requested tonal variants beside ``painting``; returns
    ``{style: path}`` for every style written or already present. Existing
    variants are kept unless ``overwrite``."""
    painting = Path(painting)
    styles = tuple(styles)
    targets = {s: variant_path(painting, s) for s in styles}
    todo = {s: p for s, p in targets.items() if overwrite or not p.exists()}
    if not todo:
        return targets
    with Image.open(painting) as src:
        src.load()
        gray = bw_gray(src, bw)
        if STYLE_BW in todo:
            _save(Image.fromarray(np.clip(np.rint(gray * 255.0), 0, 255).astype(np.uint8), mode="L"),
                  todo[STYLE_BW], src)
        if STYLE_SEPIA in todo:
            rgb = sepia_from_gray(gray, sepia)
            _save(Image.fromarray(np.clip(np.rint(rgb * 255.0), 0, 255).astype(np.uint8), mode="RGB"),
                  todo[STYLE_SEPIA], src)
    return targets


def main(argv: Optional[list] = None) -> int:
    ap = argparse.ArgumentParser(description="Write BW and Sepia variants beside a -Painting-N portrait.")
    ap.add_argument("paintings", nargs="+", type=Path)
    ap.add_argument("--styles", nargs="+", default=[",".join(STYLES)],
                    help="styles to derive, comma and/or space separated (default: BW,Sepia)")
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--mix", default="luminance", choices=sorted(CHANNEL_MIXES),
                    help="B&W channel mix (darkroom filter rendition); default luminance")
    args = ap.parse_args(argv)
    styles = [s for chunk in args.styles for s in chunk.split(",") if s]
    unknown = sorted(set(styles) - set(STYLES))
    if unknown:
        ap.error(f"unknown style(s) {unknown}; expected a subset of {list(STYLES)}")
    bw = BWParams(mix=CHANNEL_MIXES[args.mix])
    rc = 0
    for p in args.paintings:
        try:
            out = derive_variants(p, styles, overwrite=args.overwrite, bw=bw)
        except Exception as exc:  # report every file, fail the run
            print(f"FAILED {p}: {exc}", file=sys.stderr)
            rc = 1
            continue
        for style, path in out.items():
            print(f"{style}\t{path}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
