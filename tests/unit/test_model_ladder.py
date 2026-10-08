"""PortraitGenerator <-> shared image-model ladder (2026-10-08).

Guards the load-bearing principle: the portrait model is the SHARED ladder's
measured production rung; non-thinking / deprecated models are never
selectable; the policy gate runs at client construction and fails closed."""
import json

import pytest

from portrait_generator.config import model_configs as mc
from portrait_generator.config import model_ladder as ml
from portrait_generator.config.settings import Settings


def test_recommended_model_is_shared_production_rung():
    assert mc.get_recommended_model() == ml.shared_production_model()
    assert mc.RECOMMENDED_MODEL == mc.DEFAULT_MODEL == ml.shared_production_model()
    assert Settings.model_fields["gemini_model"].default == ml.shared_production_model()


def test_recommended_and_cascade_are_thinking_models_with_profiles():
    allowed = set(ml.shared_allowed_models())
    assert mc.QUOTA_CASCADE == ml.shared_cascade()
    for m in mc.QUOTA_CASCADE:
        assert m in allowed, m
        assert mc.get_model_profile(m).capabilities.thinking_mode is True, m


def test_deprecated_flash_and_non_thinking_models_are_blocked():
    blocked = ml.shared_blocked_models()
    assert "gemini-3.1-flash-image" in blocked   # deprecated by Google 2026-10-06
    assert "gemini-2.5-flash-image" in blocked   # rejects thinking_config (400)
    assert not (set(mc.QUOTA_CASCADE) & blocked)
    assert mc.MODEL_PROFILES["gemini-3.1-flash-image"].is_recommended is False


def test_is_recommended_flag_cannot_select_a_blocked_model(monkeypatch):
    """A hand-set flag must never pick the model (that is how a deprecated
    model stayed recommended for seven months)."""
    import dataclasses
    monkeypatch.setitem(mc.MODEL_PROFILES, "gemini-3.1-flash-image",
                        dataclasses.replace(mc.MODEL_PROFILES["gemini-3.1-flash-image"], is_recommended=True))
    assert mc.get_recommended_model() == ml.shared_production_model() != "gemini-3.1-flash-image"


def test_gate_fails_closed_on_bad_record(tmp_path, monkeypatch):
    from image_model_ladder import load_record, record as rec_mod, policy as pol
    bad = load_record(rec_mod.RECORD_PATH)
    bad["ladder"]["fallbacks"] = ["gemini-2.5-flash-image"]  # non-thinking rung
    p = tmp_path / "ladder.json"
    p.write_text(json.dumps(bad))
    monkeypatch.setattr(pol, "RECORD_PATH", p)
    monkeypatch.setattr(ml, "enforce_ladder_policy", lambda consumer="": pol.enforce_ladder_policy(record_path=p, live=False, consumer=consumer))
    ml.reset_for_tests()
    try:
        with pytest.raises(ml.LadderPolicyError, match="no_thinking_support"):
            ml.enforce_shared_ladder()
        with pytest.raises(ml.LadderPolicyError):
            from portrait_generator.client import PortraitClient
            PortraitClient(api_key="test_api_key_1234567890", output_dir=tmp_path)
    finally:
        ml.reset_for_tests()


def test_gate_passes_with_shipped_record_and_runs_once(monkeypatch):
    ml.reset_for_tests()
    calls = []
    real = ml.enforce_ladder_policy
    monkeypatch.setattr(ml, "enforce_ladder_policy", lambda **kw: (calls.append(kw), real(**kw))[1])
    ml.enforce_shared_ladder()
    ml.enforce_shared_ladder()
    assert len(calls) == 1 and calls[0]["consumer"] == "PortraitGenerator"
    ml.reset_for_tests()


def test_discovery_drops_non_thinking_models_and_orders_shared_ladder_first():
    from portrait_generator.utils.gemini_client import GeminiImageClient

    class _M:
        def __init__(self, n): self.name = n

    class _Models:
        def list(self):
            return [_M("publishers/google/models/" + n) for n in (
                "gemini-2.5-flash-image", "gemini-nano-banana-2.1", "gemini-3-pro-image",
                "gemini-3.1-flash-image", "gemini-3.1-flash-image-preview", "gemini-3.1-flash-lite-image")]

    class _Client:
        models = _Models()

    c = GeminiImageClient.__new__(GeminiImageClient)
    c.client = _Client()
    cascade = c._discover_image_models()
    assert cascade == ml.shared_cascade()
    assert "gemini-2.5-flash-image" not in cascade and "gemini-3.1-flash-image" not in cascade


def test_explicit_blocked_pin_is_ignored_with_warning(caplog):
    from portrait_generator.utils.gemini_client import GeminiImageClient
    c = GeminiImageClient(api_key="test_api_key_1234567890", model="gemini-3.1-flash-image",
                          model_cascade=["gemini-3-pro-image", "gemini-2.5-flash-image"])
    assert c.model == "gemini-3-pro-image"
    assert c._model_cascade == ["gemini-3-pro-image"]
    assert "blocked by the shared image-model ladder" in caplog.text
