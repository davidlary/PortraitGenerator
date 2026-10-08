"""Suite-wide test environment.

The shared image-model ladder gate (portrait_generator.config.model_ladder)
runs a free LIVE Vertex catalog + lifecycle check once per process; unit
tests must stay hermetic, so disable it here (the OFFLINE record check still
runs and still fails closed)."""
import os

os.environ.setdefault("IMAGE_MODEL_LADDER_LIVE_CHECK", "0")
