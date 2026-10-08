"""Shared image-model ladder (2026-10-08).

PortraitGenerator no longer decides its own image model. The production rung,
the quota-fallback cascade and the set of models that may ever be called come
from the shared private package ``image-model-ladder``
(https://github.com/davidlary/ImageModelLadder; checkout
``~/Dropbox/Environments/Code/ImageModelLadder``), which is also what
GraphicCreationSystem and CreateOpenStaxSlidesV2 use. Its record is measured
(probed: accepts ``thinking_config``, renders native 4K, in the live Vertex
catalog, not deprecated) and refreshed daily; policy is enforced at RUNTIME
before any generation (``enforce_shared_ladder``), so a non-thinking or
deprecated model can never silently become the portrait model again
(``gemini-3.1-flash-image`` was this project's recommended model for seven
months after Google deprecated it on 2026-10-06).

Backward compatibility: every public name in ``model_configs`` still exists;
only the values are now derived from the shared ladder. If the shared package
is not importable the import FAILS CLOSED with the one-line fix.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)

_SHARED_SRC_CANDIDATES = (
    Path(__file__).resolve().parents[4] / "ImageModelLadder" / "src",          # sibling checkout under Code/
    Path("/Users/davidlary/Dropbox/Environments/Code/ImageModelLadder/src"),  # canonical Dropbox path
)
try:
    import image_model_ladder as _iml
except ImportError:
    for _cand in _SHARED_SRC_CANDIDATES:
        if (_cand / "image_model_ladder" / "__init__.py").exists():
            sys.path.insert(0, str(_cand))
            break
    try:
        import image_model_ladder as _iml
    except ImportError as _e:
        raise ImportError(
            "image_model_ladder (shared image-model ladder) is not importable; run "
            "~/Dropbox/Environments/Code/ImageModelLadder/scripts/install.sh") from _e

if getattr(_iml, "API_VERSION", 0) < 1:
    raise ImportError(f"image_model_ladder API_VERSION {getattr(_iml, 'API_VERSION', None)} < 1; update the package")

from image_model_ladder import LadderPolicyError, allowed_models, enforce_ladder_policy, load_record, recommended_ladder  # noqa: E402

__all__ = ["LadderPolicyError", "shared_ladder", "shared_production_model", "shared_cascade",
           "shared_allowed_models", "shared_blocked_models", "enforce_shared_ladder", "reset_for_tests"]

_ENFORCED = False


def shared_ladder() -> dict:
    """``{"production", "fallbacks", "no_thinking_support"}`` from the shared record."""
    return recommended_ladder()


def shared_production_model() -> str:
    return shared_ladder()["production"]


def shared_cascade() -> List[str]:
    """Production + fallbacks, de-duplicated, order kept (quota cascade)."""
    lad = shared_ladder()
    out: List[str] = []
    for m in [lad["production"], *lad["fallbacks"]]:
        if m and m not in out:
            out.append(m)
    return out


def shared_allowed_models() -> List[str]:
    """Every probed model that passes policy today (thinking + 4K + not deprecated)."""
    return allowed_models()


def shared_blocked_models() -> frozenset:
    """Models the shared record says must never be called: holdlisted,
    probed non-thinking, or deprecated by Google."""
    rec = load_record() or {}
    lad = shared_ladder()
    bad = set(lad["no_thinking_support"])
    for mid, p in (rec.get("models") or {}).items():
        if p.get("thinking_rejected_400") or not p.get("thinking_ok"):
            bad.add(mid)
    for mid, d in (rec.get("deprecations") or {}).items():
        if d.get("deprecated"):
            bad.add(mid)
    return frozenset(bad)


def enforce_shared_ladder(force: bool = False) -> List[str]:
    """Run the shared policy gate once per process (offline record check +
    free live catalog/lifecycle check, fail-open on network error). Raises
    ``LadderPolicyError``; returns warnings."""
    global _ENFORCED
    if _ENFORCED and not force:
        return []
    warns = enforce_ladder_policy(consumer="PortraitGenerator")
    _ENFORCED = True
    return warns


def reset_for_tests() -> None:
    global _ENFORCED
    _ENFORCED = False
