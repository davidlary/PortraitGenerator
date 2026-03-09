# Portrait Generator

> Generate historically accurate, publication-quality portrait images using Google Gemini Flash Image (Nano Banana 2)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://img.shields.io/badge/pypi-v2.8.0-blue.svg)](https://pypi.org/project/portrait-generator/)
[![Conda version](https://img.shields.io/badge/conda-v2.8.0-blue.svg)](https://anaconda.org/conda-forge/portrait-generator)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-599%2B%20passed-green.svg)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-67%25-orange.svg)](htmlcov/)

---

## Features

### Core Features
- 🎨 **Painting Style (Default)**: Photorealistic paintings for best quality output
- 🖼️ **Multiple Styles Available**: BW, Sepia, Color, and Painting (photorealistic)
- 🔬 **Historical Accuracy**: Deep biographical research ensures authentic representation
- ✅ **Self-Evaluation**: Quality assurance with automated validation
- 🐍 **Python API**: Simple, high-level API for programmatic use
- 🖥️ **CLI Commands**: Easy command-line interface for quick generation
- 🚀 **REST API**: FastAPI-based RESTful API for remote integration
- 📦 **PyPI & Conda**: Install via pip or conda
- 📊 **599+ Tests**: 484+ unit tests + 115 integration tests, including end-to-end with real API; no mock code
- 🔒 **Secure**: Environment-based credentials only
- 📝 **Fully Documented**: Complete API documentation and examples

### NEW in 2.8.0: HTTP Response Cache + 5 New Portrait Subjects

- 💾 **Persistent HTTP Response Cache** (`utils/http_cache.py`): All Wikipedia, Wikidata, Wikimedia Commons, and DBpedia API calls are now cached on-disk (30-day TTL) — prevents rate-limiting and 403 blocks from repeated requests to the same endpoints across runs:
  - Cache stored at `{download_dir}/../.http_cache/` (per-project, isolated per `tmp_path` in tests)
  - Atomic file writes (tmp → rename) for thread-safe concurrent portrait generation
  - Both `ground_truth.py` and `reference_finder.py` share the same caching helper
- 👥 **5 New Portrait Subjects** added to `_CONFIRMED_URLS`, `verified_biographies.yaml`, and integration tests:
  - **George Hadley** (1685–1768) — English lawyer/meteorologist who described the Hadley circulation; *no self-portrait survives* — portrait guided by familial-likeness images of his brother **John Hadley FRS** (inventor of the nautical sextant)
  - **Guy Brasseur** (b.1948) — Belgian atmospheric chemist (NCAR/Max Planck Institute); NCAR + MPIMet reference photos
  - **Susan Solomon** (b.1956) — MIT atmospheric chemist, Antarctic ozone-hole mechanism; MIT EAPS + NOAA Commons photos
  - **Martyn Chipperfield** (b.1963) — University of Leeds atmospheric scientist; NCEO 2024 portrait + Leeds
  - **Walter Bradford Cannon** (1871–1945) — Harvard physiologist, coined "fight or flight"; canonical 1934 Bachrach photo
- 🔗 **URL Accuracy Improvements**: Upgraded reference images to highest-quality verified sources (Bachrach 1934 photo for Cannon, NCEO 2024 for Chipperfield, Wikimedia NOAA for Solomon, MPIMet for Brasseur); confirmed all 94 `_CONFIRMED_URLS` entries as HTTP 200

### NEW in 2.7.0: Runtime Auto-Discovery of Image Models

- 🔍 **Runtime Model Discovery** (`GeminiImageClient`): On startup, queries the Gemini API for all available image-generation models and builds the cascade automatically — new Gemini image models are used without any code changes:
  - **Cascade order** (auto-built): Thinking Flash → Thinking Pro → pure-image fallbacks
  - Thinking Flash (Gemini 3.x Flash): thinking mode + search grounding, fastest
  - Thinking Pro (Gemini 3.x Pro): thinking mode + search grounding, highest quality
  - Pure-image-only (2.5-flash-*): no search-as-tool, no thinking mode, separate quota bucket
  - Falls back to static `QUOTA_CASCADE` if the discovery API call fails at startup
  - When quota / rate-limit is hit: auto-advance to next model → **5-second pause** after full cycle → cycle back to primary
  - Pass `model_cascade=[model]` to disable cascading for a single-model setup
- 🛡️ **Pure-Image Model Detection Fix** (v2.7.0): All `2.5-flash-*` variants (including the longer `gemini-2.5-flash-preview-image-generation` alias) are correctly excluded from search-as-tool and thinking mode, preventing API errors

### NEW in 2.6.0: Automatic Model Cascade for Rate-Limit Recovery

- 🔄 **Automatic Model Cascade** (`GeminiImageClient`): When a generation call hits a quota / rate-limit error the client automatically advances to the next model and retries — cycling back after a full round so the primary model's quota has time to recover
- 🔎 **`get_cascade_status()`** — Diagnostic method returning current model, index, and full cascade list

### NEW in 2.5.0: Name Collision Disambiguation + Research-Verified Middle Initials

- 🔖 **Name Collision Disambiguation**: Three subjects whose names collide with more-famous people on Wikipedia are now canonically disambiguated using researched middle initials or birth-year suffixes:
  - `John Pyle` → **`John A. Pyle`** (John Adrian Pyle CBE FRS, Cambridge atmospheric chemist, born 4 Apr 1951)
  - `Andrew Lorenc` → **`Andrew C. Lorenc`** (Met Office/ECMWF data assimilation, "C" confirmed in all publications)
  - `Mike Fisher` → **`Mike Fisher (1962-Present)`** (ECMWF scientist; no middle initial found; lifespan disambiguates from NHL player born 1980)
- 🗂️ **Portrait Files Renamed**: Existing portrait files renamed to match new canonical names (`JohnAPyle_Painting.png`, `AndrewCLorenc_Painting.png`, `MikeFisher1962Present_Painting.png`)
- 🎂 **Reference-Photo Age Matching** (v2.4.2): When reference images exist, portraits match the subject's *actual* age, hair colour, and appearance from those photos — not a calculated value.
- 🏷️ **`_NoRef` Filename Suffix** (v2.4.2): Portraits generated with zero reference images are automatically named `<Name>_Painting_NoRef.png`.
- 🖼️ **No Decorative Frames** (v2.4.2): Painting-style portraits explicitly forbid ornate gold frames or gilded borders.
- 📋 **YAML Verified Biographies** (v2.4.1): All 94 subjects have locked-in birth/death years and gender stored in `verified_biographies.yaml`.
- 😊 **Facial Expression + Beard Matching** (v2.4.1): Portrait prompts require replicating expression and facial hair exactly as shown in reference photos.
- 🔍 **10-Tier Progressive Cascade (Tiers 0-9)** (v2.4.0): Local images → Hardcoded table → URL cache → Wikipedia REST → Wikidata P18
  → Gemini web search → Wikipedia page images → Wikimedia Commons → DBpedia — stops at first success
- 🤖 **AI-Powered Fallback** (v2.4.0): Gemini web search understands era, field, and institutional context
  to find portraits for any subject; results self-cache for instant future access
- ✅ **Held-Out Independent Validation**: Reference images split into generation set (used for creation)
  and held-out set (withheld for independent post-generation identity verification)
- 📚 **94-Entry Confirmed URL Table**: All 94 book portrait subjects pre-researched by parallel agents
- 👤 **27 Subjects with Tier 0 Local Photos**: Human-verified reference images at highest priority (score 1.09)
- 🔄 **Self-Caching**: Gemini discoveries persisted to disk; repeat runs are free
- 🪪 **Sidecar Metadata**: `.meta.json` alongside every portrait for deterministic verification
- 📐 **3-Stage Gender Verification**: Direct → contextual → elimination; 2/3 majority required
- 🧪 **Integration Test Suite**: 94-subject parametrized test covering all book portrait subjects

---

## Adding Local Reference Images (Highest Priority — Tier 0)

When you have actual photographs of a subject, placing them in the `ExampleReferenceImages/`
directory gives the pipeline the most accurate reference data possible. Local images are
**always used first** (Tier 0, score 1.09) and outrank all online sources (Tier 1 confirmed
URLs score 1.04, Tier 4+ Wikipedia scores 0.88-0.95).

### Step 1 — Drop images into `ExampleReferenceImages/`

```
PortraitGenerator/
└── ExampleReferenceImages/
    ├── David_Lary_1.jpeg        # Accepted formats: .jpg, .jpeg, .png
    ├── David_Lary_2.jpeg
    └── David_Lary_3.jpeg
```

Use clear, well-lit headshots wherever possible. Multiple photos from different angles or
lighting conditions improve likeness fidelity. Minimum 256×256 px recommended.

### Step 2 — Register the filenames in `reference_finder.py`

Open `src/portrait_generator/reference_finder.py` and find the `_LOCAL_REFERENCE_FILES`
dictionary (around line 425). Add your subject:

```python
_LOCAL_REFERENCE_FILES: Dict[str, list] = {
    # ... existing entries ...

    # David Lary: three user-provided reference photos — glasses, dark hair, no beard
    "David Lary": ["David_Lary_1.jpeg", "David_Lary_2.jpeg", "David_Lary_3.jpeg"],
}
```

The key must exactly match the subject name used in generation. Filenames are resolved
relative to `ExampleReferenceImages/`.

### Step 3 — Regenerate

Clear the cache for that subject, then regenerate:

```bash
# Remove stale cached references for the subject
rm -rf .cpf/reference_images/david_lary/

# Force fresh generation
portrait-generator generate "David Lary" --styles Painting --output-dir output/
```

### Why Tier 0 images produce the best likenesses

| Priority | Source | Score | Notes |
|----------|--------|-------|-------|
| **Tier 0** | **Local ExampleReferenceImages** | **1.09** | User-verified — ground truth |
| Tier 1 | Confirmed URL table | 1.04 | Pre-researched institutional photos |
| Tier 4 | Wikipedia REST | 0.95 | Wikipedia photo, may be generic |
| Tier 5 | Wikidata P18 | 0.92 | Wikidata image property |
| Tier 8 | Wikimedia Commons | 0.88 | Commons search, lower confidence |

The 10-tier cascade stops as soon as enough images are gathered. Having Tier 0 images
means the AI receives high-confidence, human-verified references before any web search
is attempted, which is crucial for subjects with name collisions (e.g. scientists whose
names match more-famous people on Wikipedia).

### Tips for best results

- **Provide 2-5 photos**: Different lighting, angles, or years improve robustness
- **Clear face focus**: Cropped headshots work best; remove distracting backgrounds if possible
- **Avoid group photos**: Individual portraits give stronger facial feature signals
- **Match the era**: For historical subjects, period-appropriate photos ground the style better
- **Add to the URL table too**: If you find a public URL for an institutional profile photo,
  add it to `_CONFIRMED_URLS` in `reference_finder.py` so the image is automatically
  fetched on future runs without needing the local file

---

### NEW in 2.2.0: Flash Image Model (Nano Banana 2) as Default

- ⚡ **gemini-3.1-flash-image-preview**: New default model — ~22s vs ~45s (2x faster)
- 🔍 **Image Search Grounding**: Text + image search grounding capability
- 🧠 **Thinking Mode**: Configurable reasoning depth (low/medium/high)
- 📐 **Extended Aspect Ratios**: 1:4, 4:1, 1:8, 8:1, 2:3, 3:2, 4:5, 5:4, 21:9
- 🔄 **Batch API**: Native batch generation support
- 🚫 **No Mock Code**: All tests use real objects; API tests skip when `GOOGLE_API_KEY` not set
- 🔑 **API Key Loading**: Use `source /path/to/load_api_keys.sh` to load all credentials

**[See full Flash model documentation →](docs/GEMINI_3_PRO_IMAGE.md)**

---

### Also supported: gemini-3-pro-image-preview (Nano Banana Pro) and gemini-exp-1206 (legacy)
- 🔍 **Google Search Grounding**: Real-time fact-checking and verification
- 🖼️ **Multi-Image References**: Up to 14 authentic historical reference images
- 🧠 **Internal Reasoning**: Model thinks through tasks and refines internally
- ⚡ **Physics-Aware Synthesis**: Realistic lighting, shadows, and materials
- ✓ **Pre-Generation Validation**: Proactive error detection before generation
- 🎯 **Smart Retry**: Autonomous prompt refinement on failure
- 🤖 **Holistic AI Evaluation**: Multi-pass reasoning-based assessment
- 🔄 **100% Backward Compatible**: Works with all existing models

**[See full model documentation →](docs/GEMINI_3_PRO_IMAGE.md)**

---

## Quick Start

### Installation

**Via pip:**
```bash
pip install portrait-generator
```

**Via conda:**
```bash
conda install -c conda-forge portrait-generator
# or
conda install portrait-generator
```

**From source:**
```bash
git clone https://github.com/davidlary/PortraitGenerator.git
cd PortraitGenerator
pip install -e .
```

### Configuration

Set your Google Gemini API key:

```bash
export GOOGLE_API_KEY="your_gemini_api_key_here"
```

Or create a `.env` file:
```bash
GOOGLE_API_KEY=your_gemini_api_key_here
OUTPUT_DIR=./output
```

### Python API Usage

**Simple generation:**
```python
from portrait_generator import generate_portrait

# Generate painting portrait (default - best quality)
result = generate_portrait("Albert Einstein")

# Check results
print(f"Success: {result.success}")
print(f"Generated: {result.files['Painting']}")

# Generate all 4 styles explicitly
result = generate_portrait("Marie Curie", styles=["BW", "Sepia", "Color", "Painting"])
```

**Using the client:**
```python
from portrait_generator import PortraitClient

# Initialize client
client = PortraitClient(
    api_key="your_api_key",
    output_dir="./portraits"
)

# Generate painting portrait (default - best quality)
result = client.generate("Marie Curie")

# Generate specific styles
result = client.generate(
    "Ada Lovelace",
    styles=["BW", "Color"]
)

# Batch generation (paintings by default)
subjects = ["Alan Turing", "Grace Hopper", "Claude Shannon"]
results = client.generate_batch(subjects)

# Check status
status = client.check_status("Albert Einstein")
print(f"Painting exists: {status['Painting']}")
```

### CLI Usage

**Generate a painting portrait (default):**
```bash
portrait-generator generate "Alan Turing"
```

**Generate specific styles:**
```bash
portrait-generator generate "Claude Shannon" --styles BW Sepia Color Painting
```

**Batch generation:**
```bash
portrait-generator batch "Ada Lovelace" "Grace Hopper" "Margaret Hamilton"
```

**Check portrait status:**
```bash
portrait-generator status "Albert Einstein"
```

**Start API server:**
```bash
portrait-generator serve
# or with custom host/port
portrait-generator serve --host 0.0.0.0 --port 8080
```

**Health check:**
```bash
portrait-generator health-check
```

### REST API Usage

**Start server:**
```bash
portrait-generator serve
# Access interactive docs at http://localhost:8000/docs
```

**Generate via API:**
```bash
curl -X POST "http://localhost:8000/api/v1/generate" \
  -H "Content-Type: application/json" \
  -d '{"subject_name": "Marie Curie"}'
```

---

## Known Issues

### Google Search Grounding — Resolved in v2.4.0

**Status:** ✅ Fixed in v2.4.0 via 10-tier reference image cascade (Tiers 0-9)

In v2.1.0, the Google Search Grounding API was returning empty results, causing `enable_reference_images`
to be disabled by default. v2.4.0 completely replaces the grounding-API approach with a
multi-tier cascade that uses Wikipedia REST, Wikidata SPARQL, Wikimedia Commons, and an optional
Gemini web-search fallback — none of which depend on the grounding API.

Reference images are now enabled by default (`enable_reference_images = True`) and the cascade
successfully finds authentic portraits for the vast majority of historical subjects.

**Technical Details:** See [profiling report](docs/PROFILING_2026-02-03.md) for historical analysis.

---

## API Reference

### Python API

#### `generate_portrait()`
Convenience function for quick portrait generation.

```python
from portrait_generator import generate_portrait

result = generate_portrait(
    subject_name="Alan Turing",
    api_key=None,              # Uses GOOGLE_API_KEY env var if not provided
    output_dir=None,            # Uses ./output if not provided
    force_regenerate=False,     # Skip existing portraits
    styles=None                 # Default: ["Painting"] — best quality; pass list for other styles
)
```

#### `generate_batch()`
Generate multiple portraits in sequence.

```python
from portrait_generator import generate_batch

subjects = ["Ada Lovelace", "Grace Hopper"]
results = generate_batch(
    subject_names=subjects,
    api_key=None,
    output_dir=None,
    force_regenerate=False,
    styles=["BW", "Color"]      # Only generate BW and Color
)

for result in results:
    print(f"{result.subject}: {result.success}")
```

#### `PortraitClient`
Full-featured client for advanced usage.

```python
from portrait_generator import PortraitClient

client = PortraitClient(
    api_key="your_api_key",
    output_dir="./portraits",
    model="gemini-3.1-flash-image-preview"     # Optional: override default model
)

# Generate portrait
result = client.generate("Claude Shannon")

# Check what exists
status = client.check_status("Claude Shannon")
# Returns: {"BW": True, "Sepia": True, "Color": True, "Painting": True}

# Force regeneration
result = client.generate("Claude Shannon", force_regenerate=True)
```

### CLI Reference

#### `portrait-generator generate`
Generate portraits for a single subject.

```bash
portrait-generator generate [OPTIONS] SUBJECT_NAME

Options:
  --api-key TEXT          Google Gemini API key (or use GOOGLE_API_KEY env var)
  --output-dir PATH       Output directory (default: ./output)
  --styles TEXT           Space-separated styles: BW Sepia Color Painting
  --force                 Force regeneration even if portraits exist
  --verbose              Enable verbose logging
  --help                  Show help message
```

**Examples:**
```bash
# Generate painting portrait (default — best quality)
portrait-generator generate "Alan Turing"

# Generate specific styles
portrait-generator generate "Claude Shannon" --styles BW Color

# Force regeneration
portrait-generator generate "Ada Lovelace" --force

# Custom output directory
portrait-generator generate "Grace Hopper" --output-dir ~/portraits
```

#### `portrait-generator batch`
Generate portraits for multiple subjects.

```bash
portrait-generator batch [OPTIONS] SUBJECT_NAMES...

Options:
  --api-key TEXT          Google Gemini API key
  --output-dir PATH       Output directory
  --styles TEXT           Space-separated styles
  --force                 Force regeneration
  --verbose              Enable verbose logging
  --help                  Show help message
```

**Examples:**
```bash
# Generate for multiple subjects
portrait-generator batch "Ada Lovelace" "Grace Hopper" "Margaret Hamilton"

# Batch with specific styles
portrait-generator batch "Alan Turing" "Claude Shannon" --styles BW Sepia
```

#### `portrait-generator status`
Check which portraits exist for a subject.

```bash
portrait-generator status [OPTIONS] SUBJECT_NAME

Options:
  --output-dir PATH       Output directory (default: ./output)
  --help                  Show help message
```

**Example:**
```bash
portrait-generator status "Albert Einstein"
# Output:
# Portrait status for 'Albert Einstein':
#   BW: ✓ exists
#   Sepia: ✓ exists
#   Color: ✗ missing
#   Painting: ✗ missing
```

#### `portrait-generator serve`
Start the REST API server.

```bash
portrait-generator serve [OPTIONS]

Options:
  --host TEXT             Host to bind to (default: 0.0.0.0)
  --port INTEGER          Port to bind to (default: 8000)
  --reload               Enable auto-reload for development
  --help                  Show help message
```

**Example:**
```bash
# Start on default port
portrait-generator serve

# Start on custom port with auto-reload
portrait-generator serve --port 8080 --reload
```

#### `portrait-generator health-check`
Check system health and configuration.

```bash
portrait-generator health-check [OPTIONS]

Options:
  --api-key TEXT          Google Gemini API key to validate
  --verbose              Show detailed information
  --help                  Show help message
```

**Example:**
```bash
portrait-generator health-check --verbose
# Output:
# ✓ API key configured
# ✓ Output directory writable
# ✓ Google Gemini API accessible
# ✓ All dependencies installed
```

### REST API

#### Endpoints

**Health Check**
```bash
GET /api/v1/health
```

**Generate Single Portrait**
```bash
POST /api/v1/generate
Content-Type: application/json

{
  "subject_name": "Marie Curie",
  "styles": ["BW", "Color"],        # Optional
  "force_regenerate": false          # Optional
}
```

**Generate Batch**
```bash
POST /api/v1/batch
Content-Type: application/json

[
  {"subject_name": "Ada Lovelace", "styles": ["BW"], "force_regenerate": false},
  {"subject_name": "Grace Hopper", "styles": ["BW"], "force_regenerate": false}
]
```

**Check Status**
```bash
GET /api/v1/status/{subject_name}
```

**Download Portrait**
```bash
GET /api/v1/download/{subject_name}/{style}
```

**Examples:**
```bash
# Generate portrait
curl -X POST "http://localhost:8000/api/v1/generate" \
  -H "Content-Type: application/json" \
  -d '{"subject_name": "Alan Turing", "styles": ["BW"]}'

# Check status
curl "http://localhost:8000/api/v1/status/Alan%20Turing"

# Download portrait
curl "http://localhost:8000/api/v1/download/Alan%20Turing/BW" \
  -o alan_turing_bw.png
```

**Interactive Documentation:**
Once the server is running, visit `http://localhost:8000/docs` for interactive API documentation.

---

## Portrait Styles

### 1. Black & White (`BW`)
- Classic monochrome photography
- Enhanced contrast
- Filename: `FirstNameLastName_BW.png`

### 2. Sepia (`Sepia`)
- Warm vintage aesthetic
- Classic early photography style
- Filename: `FirstNameLastName_Sepia.png`

### 3. Color (`Color`)
- Full color photorealistic
- Natural skin tones
- Filename: `FirstNameLastName_Color.png`

### 4. Photorealistic Painting (`Painting`)
- Oil painting style with visible brushstrokes
- Highly detailed
- Filename: `FirstNameLastName_Painting.png`

---

## Architecture

### Core Components

1. **GeminiImageClient**: Google Gemini Flash Image API integration for image + text generation
2. **BiographicalResearcher**: Deep research with Gemini; cross-validated against ground truth
3. **GroundTruthVerifier**: 5-tier cascade (Wikipedia REST → Wikipedia Search → Wikidata → DBpedia → Gemini web search) for date/gender verification
4. **ReferenceFinder**: 10-tier cascade for authentic reference images (Tiers 0-9: local images → hardcoded table → URL cache → Wikipedia → Wikidata → Gemini web → Commons → DBpedia)
5. **TitleOverlayEngine**: Professional title overlays with name, dates, and era
6. **PortraitVerifier**: Post-generation verification (file size, overlay OCR, gender, identity vs reference)
7. **EnhancedPortraitGenerator**: Orchestrates complete workflow with retry on verification failure
8. **EnhancedQualityEvaluator**: Gemini Vision holistic evaluation of generated portrait
9. **API Layer**: RESTful FastAPI endpoints

### Workflow

```
Subject Name
  → BiographicalResearcher (Gemini text research)
  → GroundTruthVerifier (Wikipedia/Wikidata cross-validation, 5-tier cascade)
  → ReferenceFinder (authentic portrait images, 10-tier cascade Tiers 0-9)
  → Generate image (Gemini Flash Image, reference images injected)
  → TitleOverlayEngine (name + dates overlay)
  → PortraitVerifier (file size, OCR dates, gender check)
  → EnhancedQualityEvaluator (Gemini Vision holistic scoring)
  → Save portrait + .meta.json sidecar
```

---

## Testing

### Running Tests

```bash
# Load API keys (sets GOOGLE_API_KEY, GEMINI_API_KEY, GITHUB_TOKEN, etc.)
source /path/to/load_api_keys.sh

# Run all unit tests with coverage
pytest tests/unit/ --cov=portrait_generator --cov-report=html --cov-report=term

# Run specific test types
pytest tests/unit/ -v           # Unit tests (484+ tests)

# Run end-to-end tests with real API (requires GOOGLE_API_KEY to be set)
pytest tests/integration/test_e2e_real_api.py -m e2e -v

# Run all 94 book portrait tests in parallel (12 workers, ~12-15 min total)
# Requires GOOGLE_API_KEY; existing portraits are skipped automatically
pytest tests/integration/test_book_portraits.py -n 12 --no-cov -m integration --timeout=600

# Force regeneration of all 94 portraits
PORTRAIT_FORCE_REGENERATE=1 pytest tests/integration/test_book_portraits.py -n 12 --no-cov -m integration --timeout=600

# Run only slow tests (real portrait generation)
pytest -m slow -v

# Check coverage report
open htmlcov/index.html
```

### Test Coverage

**Current Coverage: 67%** (threshold: 55%)

- **484+ unit tests** covering all core functionality
- **No mock code**: All tests use real objects with test/real API keys
- **End-to-end tests** with real Google Gemini API calls (requires `GOOGLE_API_KEY`)
- **94-subject integration test** covering every book portrait subject
- API-dependent unit tests skip gracefully when `GOOGLE_API_KEY` is not set

### Loading API Keys

```bash
# Load all credentials (Google, OpenAI, Anthropic, GitHub, etc.)
source /path/to/load_api_keys.sh

# Or set manually
export GOOGLE_API_KEY="your_gemini_api_key"
```

### Test Organization

```
tests/
├── unit/                           # Unit tests (real objects, no mocks; 484+ tests)
│   ├── test_client.py             # Python API client (PortraitClient, generate_portrait)
│   ├── test_gemini_client.py      # GeminiImageClient — image generation + cascade
│   ├── test_generator.py          # PortraitGenerator — core generation pipeline
│   ├── test_researcher.py         # BiographicalResearcher — Gemini text research
│   ├── test_ground_truth.py       # GroundTruthVerifier — Wikipedia/Wikidata cascade
│   ├── test_reference_finder.py   # ReferenceImageFinder — 10-tier image cascade
│   ├── test_portrait_verifier.py  # PortraitVerifier — post-generation verification
│   ├── test_prompt_builder.py     # PromptBuilder — gender/dates/appearance injection
│   ├── test_overlay.py            # TitleOverlayEngine — name+dates text overlay
│   ├── test_evaluator.py          # QualityEvaluator — quality scoring
│   ├── test_pre_generation_validator.py  # Pre-generation feasibility checks
│   ├── test_model_configs.py      # Model profiles and capability detection
│   ├── test_api_models.py         # SubjectData, GenerationResult dataclasses
│   ├── test_api_server.py         # FastAPI routes and server
│   ├── test_image_utils.py        # Image format conversion helpers
│   └── test_validators.py         # Input validation helpers
├── integration/                    # Integration tests (115 tests)
│   ├── test_book_portraits.py     # 94-subject portrait generation (12 parallel workers)
│   └── test_e2e_real_api.py       # End-to-end API tests (requires GOOGLE_API_KEY)
└── ExamplePortraitTests/           # Generated portrait output (gitignored)
```

### Running E2E Tests

End-to-end tests make **real API calls** to Google Gemini and require a valid API key:

```bash
# Set API key
export GOOGLE_API_KEY="your_api_key"

# Run all e2e tests
pytest -m e2e -v

# Run specific e2e test
pytest tests/integration/test_e2e_real_api.py::TestE2ERealAPI::test_generate_single_portrait_all_styles -v
```

**Note:** E2E tests are automatically skipped if `GOOGLE_API_KEY` is not set.

---

## Development

### Project Structure

```
PortraitGenerator/
├── src/portrait_generator/          # Main package
│   ├── __init__.py                  # Package exports (PortraitClient, generate_portrait, etc.)
│   ├── client.py                    # High-level Python API (PortraitClient)
│   ├── cli.py                       # CLI: generate / batch / status / serve / health-check
│   ├── intelligence_coordinator.py  # Orchestrates research → generation → verification
│   ├── prompt_builder.py            # Builds structured Gemini prompts with gender/dates/appearance
│   ├── reference_finder.py          # 10-tier reference image cascade (Tiers 0-9)
│   ├── pre_generation_validator.py  # Pre-flight validation before generation
│   ├── api/                         # REST API (FastAPI)
│   │   ├── models.py                # SubjectData, GenerationResult dataclasses
│   │   ├── routes.py                # POST /generate, POST /batch, GET /status
│   │   └── server.py               # FastAPI app factory
│   ├── config/
│   │   ├── settings.py             # All Settings fields (Pydantic BaseSettings)
│   │   └── model_configs.py        # Model profiles for flash/pro/legacy models
│   ├── core/
│   │   ├── researcher.py           # BiographicalResearcher (Gemini text → SubjectData)
│   │   ├── generator_enhanced.py   # EnhancedPortraitGenerator (main orchestration)
│   │   ├── overlay.py              # TitleOverlayEngine (name + dates overlay)
│   │   ├── portrait_verifier.py    # PortraitVerifier (size, OCR, gender, identity)
│   │   └── evaluator_enhanced.py   # EnhancedQualityEvaluator (Gemini Vision)
│   └── utils/
│       ├── gemini_client.py        # GeminiImageClient (image + text, runtime model discovery, cascade)
│       ├── ground_truth.py         # GroundTruthVerifier (5-tier cascade: Wikipedia → Wikidata → DBpedia → Gemini)
│       ├── http_cache.py           # HttpResponseCache (on-disk JSON cache, 30-day TTL, thread-safe)
│       ├── image_utils.py          # Image format conversion utilities
│       └── validators.py           # Input validation helpers
├── tests/                           # Test suite (599+ tests, 67% coverage)
│   ├── unit/                        # Unit tests (no mocks, real objects)
│   ├── integration/
│   │   ├── test_book_portraits.py   # 94-subject parametrized portrait generation
│   │   └── test_e2e_real_api.py     # End-to-end API tests (requires GOOGLE_API_KEY)
│   └── ExamplePortraitTests/        # Generated portrait output (gitignored)
├── docs/                            # Technical documentation
├── Examples/                        # Usage examples
├── output/                          # Default portrait output directory
├── pyproject.toml                   # Modern Python package config (PEP 621)
├── pytest.ini                       # pytest settings
├── requirements.txt                 # Production dependencies
├── CHANGELOG.md                     # Version history
└── README.md                        # This file
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/

# Run all quality checks
black src/ tests/ && ruff check src/ tests/ && mypy src/ && pytest
```

### Building the Package

**Build Python package:**
```bash
python -m build
# Creates dist/portrait_generator-2.8.0.tar.gz and .whl
```

**Build Conda package:**
```bash
conda build conda.recipe/
```

**Install locally for development:**
```bash
pip install -e .
```

---

## Configuration

### Environment Variables

Portrait Generator can be configured via environment variables:

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `GOOGLE_API_KEY` | Google Gemini API key | — | **Yes** |
| `GEMINI_MODEL` | Gemini model (auto-discovered at startup) | `gemini-3.1-flash-image-preview` | No |
| `IMAGE_RESOLUTION` | Image size as `width,height` | `1024,1024` | No |
| `OUTPUT_DIR` | Output directory for portraits | `./output` | No |
| `LOG_LEVEL` | Logging level (`DEBUG`/`INFO`/`WARNING`) | `INFO` | No |
| `ENABLE_ADVANCED_FEATURES` | Enable all advanced AI features | `true` | No |
| `ENABLE_REFERENCE_IMAGES` | Use 10-tier reference image cascade | `true` | No |
| `MAX_REFERENCE_IMAGES` | Max reference images sent to Gemini (0-14) | `5` | No |
| `ENABLE_SEARCH_GROUNDING` | Enable Google Search grounding (currently returns empty results) | `false` | No |
| `ENABLE_INTERNAL_REASONING` | Enable Gemini thinking mode | `true` | No |
| `QUALITY_THRESHOLD` | Min quality score for acceptance (0.0-1.0) | `0.90` | No |
| `USE_HOLISTIC_REASONING` | Use Gemini Vision for holistic evaluation | `true` | No |
| `ENABLE_PORTRAIT_VERIFICATION` | Post-generation size/OCR/gender verification | `true` | No |
| `ENABLE_GROUND_TRUTH_LOOKUP` | Cross-validate with Wikipedia/Wikidata | `true` | No |
| `PORTRAIT_VERIFICATION_MIN_SIZE_KB` | Minimum portrait file size in KB | `300` | No |
| `SAVE_PROMPTS` | Save `_prompt.md` sidecar alongside each portrait | `true` | No |

**[See complete configuration reference →](docs/GEMINI_3_PRO_IMAGE.md#configuration-reference)**

### Configuration Methods

**1. Environment Variables (Recommended)**
```bash
export GOOGLE_API_KEY="your_api_key"
export OUTPUT_DIR="~/portraits"
```

**2. `.env` File**
```bash
# Create .env file in project root
cat > .env << EOF
GOOGLE_API_KEY=your_api_key
OUTPUT_DIR=./output
GEMINI_MODEL=gemini-3.1-flash-image-preview
LOG_LEVEL=INFO

# Advanced Features
ENABLE_ADVANCED_FEATURES=true
ENABLE_REFERENCE_IMAGES=true
MAX_REFERENCE_IMAGES=5
ENABLE_SEARCH_GROUNDING=false
ENABLE_INTERNAL_REASONING=true
QUALITY_THRESHOLD=0.90
EOF
```

**3. Programmatic Configuration**
```python
from portrait_generator import PortraitClient

client = PortraitClient(
    api_key="your_api_key",
    output_dir="~/portraits",
    model="gemini-3.1-flash-image-preview"
)
```

**4. Settings Object**
```python
from portrait_generator.config import Settings

settings = Settings(
    google_api_key="your_api_key",
    output_dir="~/portraits",
    gemini_model="gemini-3.1-flash-image-preview"
)
```

---

## Installation Details

### Package Distribution

Portrait Generator is distributed as:
- **PyPI package**: `portrait-generator` (install via `pip`)
- **Conda package**: `portrait-generator` (install via `conda`)
- **Source code**: Available on GitHub

### Entry Points

The package provides two console script entry points:
- `portrait-generator` - Main CLI command
- `portrait-gen` - Shorter alias

Both commands provide identical functionality.

### Dependencies

**Core Dependencies:**
- `google-genai>=1.0.0,<2.0.0` - Google Gemini API client
- `pillow>=11.0.0,<12.0.0` - Image processing
- `fastapi>=0.100.0,<1.0.0` - REST API framework
- `uvicorn[standard]>=0.27.0,<1.0.0` - ASGI server
- `pydantic>=2.6.0,<3.0.0` - Data validation
- `pydantic-settings>=2.1.0,<3.0.0` - Settings management
- `click>=8.0.0,<9.0.0` - CLI framework
- `httpx>=0.26.0,<1.0.0` - HTTP client
- `requests>=2.31.0,<3.0.0` - HTTP library
- `python-dotenv>=1.0.0,<2.0.0` - Environment variables
- `loguru>=0.7.0,<1.0.0` - Logging

**Development Dependencies:**
- `pytest>=9.0.0` - Testing framework
- `pytest-cov>=7.0.0` - Coverage reporting
- `pytest-asyncio>=1.3.0` - Async test support
- `pytest-mock>=3.15.0` - Mocking utilities
- `black>=24.0.0` - Code formatter
- `ruff>=0.1.0` - Fast linter
- `mypy>=1.8.0` - Type checker

### Python Version Support

- **Minimum**: Python 3.10
- **Tested**: Python 3.10, 3.11, 3.12
- **Recommended**: Python 3.11+

---

## Examples

### Example 1: Simple Portrait Generation

```python
from portrait_generator import generate_portrait

# Generate painting portrait (default — best quality)
result = generate_portrait("Ada Lovelace")

if result.success:
    print(f"✓ Generated {len(result.files)} portraits")
    print(f"  Generation time: {result.generation_time_seconds:.1f}s")

    for style, filepath in result.files.items():
        print(f"  {style}: {filepath}")
else:
    print(f"✗ Generation failed: {result.errors}")
```

### Example 2: Batch Processing

```python
from portrait_generator import PortraitClient

# Initialize client
client = PortraitClient()

# List of subjects
computer_scientists = [
    "Alan Turing",
    "Claude Shannon",
    "Grace Hopper",
    "Donald Knuth",
]

# Generate only BW portraits for all subjects
results = client.generate_batch(
    computer_scientists,
    styles=["BW"],
    force_regenerate=False
)

# Report results
successful = [r for r in results if r.success]
failed = [r for r in results if not r.success]

print(f"✓ Successful: {len(successful)}/{len(results)}")
if failed:
    print(f"✗ Failed: {len(failed)}")
    for r in failed:
        print(f"  - {r.subject}: {r.errors}")
```

### Example 3: Custom Output Directory

```python
from portrait_generator import PortraitClient
from pathlib import Path

# Create custom output directory
output_dir = Path.home() / "Documents" / "Portraits"
output_dir.mkdir(parents=True, exist_ok=True)

# Initialize with custom directory
client = PortraitClient(
    output_dir=output_dir
)

# Generate portraits
result = client.generate("Marie Curie")
print(f"Portraits saved to: {output_dir}")
```

### Example 4: Check Before Generating

```python
from portrait_generator import PortraitClient

client = PortraitClient()

subject = "Albert Einstein"

# Check what already exists
status = client.check_status(subject)

# Determine what needs to be generated
missing_styles = [style for style, exists in status.items() if not exists]

if missing_styles:
    print(f"Generating missing styles: {missing_styles}")
    result = client.generate(subject, styles=missing_styles)
else:
    print(f"All portraits already exist for {subject}")
```

### Example 5: CLI Workflow

```bash
#!/bin/bash
# batch_generate.sh - Generate portraits for multiple subjects

SUBJECTS=(
    "Alan Turing"
    "Ada Lovelace"
    "Claude Shannon"
    "Grace Hopper"
)

# Create output directory
mkdir -p ./portraits

# Generate each subject
for subject in "${SUBJECTS[@]}"; do
    echo "Generating: $subject"
    portrait-generator generate "$subject" \
        --output-dir ./portraits \
        --styles BW Color \
        --verbose
done

# Check status of all subjects
echo ""
echo "Status Report:"
for subject in "${SUBJECTS[@]}"; do
    echo "  $subject:"
    portrait-generator status "$subject" --output-dir ./portraits
done
```

### Example 6: API Integration

```python
import httpx

# API base URL
API_URL = "http://localhost:8000/api/v1"

# Generate portrait via API
response = httpx.post(
    f"{API_URL}/generate",
    json={
        "subject_name": "Alan Turing",
        "styles": ["BW", "Color"]
    },
    timeout=300.0  # 5 minutes timeout
)

if response.status_code == 200:
    result = response.json()
    print(f"Generated: {result['subject']}")
    print(f"Files: {result['files']}")
else:
    print(f"Error: {response.json()['detail']}")
```

For more examples, see the `/Examples` directory in the repository.

---

## Security

**CRITICAL**: Never commit API keys or credentials.

- Use environment variables for all secrets
- Review `.gitignore` before committing
- Check `git status` and `git diff --staged`
- API keys must be >= 20 characters

---

## Requirements

- Python 3.10+
- Google Gemini API key
- 2GB+ RAM
- ~5MB disk space per subject (4 portraits)

---

## Troubleshooting

### API Key Issues

```python
from portrait_generator.config import Settings

settings = Settings()
if not settings.validate_api_key():
    print("Invalid API key")
```

### Image Generation Fails

1. Check API quota/limits
2. Verify internet connection
3. Check logs in `.cpf/logs/`
4. Enable debug logging: `LOG_LEVEL=DEBUG`

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests for new features
4. Ensure all tests pass (`pytest tests/`)
5. Submit a pull request

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

## Authors

- **Dr. David Lary** - University of Texas at Dallas
- **Claude Sonnet 4.6** - AI Assistant (Anthropic)

---

## Acknowledgments

- Google Gemini API for image generation
- Pillow (PIL) for image processing
- FastAPI for API framework
- pytest for testing infrastructure

---

## Status

🚀 **Version 2.8.0** - Production Ready

- **Release Date**: March 9, 2026
- **Default Model**: gemini-3.1-flash-image-preview (Nano Banana 2)
- **Python Support**: 3.10, 3.11, 3.12
- **Test Coverage**: 67% (484+ unit tests; 115 integration tests; 599+ total)
- **Package Status**: Available on PyPI and Conda
- **API Status**: Stable (v1) - Backward Compatible
- **Documentation**: Complete with advanced features guide

### What's New — Recent Highlights

See [CHANGELOG.md](CHANGELOG.md) for the complete version history. Key milestones:

- **v2.8.0** — HTTP response cache prevents Wikimedia rate-limiting; 5 new portrait subjects; 94-entry confirmed URL table
- **v2.7.0** — Runtime auto-discovery of Gemini image models; no code change needed for new models
- **v2.6.0** — Automatic model cascade for rate-limit recovery (Flash → Pro → fallback)
- **v2.5.0** — Name collision disambiguation (John A. Pyle, Andrew C. Lorenc, Mike Fisher)
- **v2.4.x** — 10-tier reference image cascade; YAML verified biographies; portrait verifier; BCE date support
- **v2.2.0** — `gemini-3.1-flash-image-preview` as default model (~22s vs ~45s); zero mock code in tests

### Version History

See [CHANGELOG.md](CHANGELOG.md) for detailed version history.

---

## Publishing

### Publishing to PyPI

```bash
# Build package
python -m build

# Check distribution
twine check dist/*

# Upload to PyPI
twine upload dist/*
```

### Publishing to Conda

```bash
# Build conda package
conda build conda.recipe/

# Upload to conda channel
anaconda upload <path-to-tarball>
```

### Creating a Release

```bash
# Tag the release
git tag -a v2.8.0 -m "Release version 2.8.0"
git push origin v2.8.0

# Create GitHub release
gh release create v2.8.0 \
  --title "Portrait Generator v2.8.0" \
  --notes "See CHANGELOG.md for details"
```

---

## Documentation

### Online Documentation

- **Read the Docs**: https://portrait-generator.readthedocs.io
- **GitHub Pages**: https://davidlary.github.io/PortraitGenerator
- **PyPI**: https://pypi.org/project/portrait-generator
- **GitHub**: https://github.com/davidlary/PortraitGenerator

### Local Documentation

- [CHANGELOG.md](CHANGELOG.md) - Version history and release notes
- [docs/GEMINI_3_PRO_IMAGE.md](docs/GEMINI_3_PRO_IMAGE.md) - Advanced Gemini model features guide
- [LICENSE](LICENSE) - MIT License
- [Examples/](Examples/) - Usage examples and tutorials

### API Documentation

Interactive API documentation is available when running the server:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

---

## Roadmap

Planned features for future releases:

- [ ] Additional portrait styles (Oil Painting, Sketch, Watercolor)
- [ ] Custom style templates
- [ ] Batch parallel processing
- [ ] Portrait editing and refinement
- [ ] Video portrait generation
- [ ] Integration with other AI models
- [ ] Web UI for non-technical users
- [ ] Portrait comparison and analytics

---

## Support

### Getting Help

- **Documentation**: https://portrait-generator.readthedocs.io
- **Issues**: https://github.com/davidlary/PortraitGenerator/issues
- **Discussions**: https://github.com/davidlary/PortraitGenerator/discussions

### Reporting Bugs

Please report bugs via GitHub Issues with:
1. Description of the problem
2. Steps to reproduce
3. Expected vs actual behavior
4. System information (Python version, OS, etc.)
5. Error messages and logs

### Feature Requests

Feature requests are welcome! Please open a GitHub Issue with:
1. Description of the proposed feature
2. Use case and motivation
3. Proposed API or usage example

---

## FAQ

**Q: How much does it cost to generate portraits?**
A: The cost depends on Google Gemini API pricing. Typically ~$0.01-0.05 per portrait depending on model and resolution.

**Q: Can I use this commercially?**
A: Yes, the code is MIT licensed. However, check Google's API terms for commercial usage.

**Q: How long does it take to generate a portrait?**
A: Typically 20-60 seconds for the default Painting style. Generating all 4 styles (BW, Sepia, Color, Painting) takes ~2-4 minutes total.

**Q: Can I customize the portrait styles?**
A: Yes, you can modify the style prompts in the code or wait for the custom styles feature in a future release.

**Q: Do I need to credit the generated portraits?**
A: The portraits are AI-generated. Attribution is appreciated but not required under the MIT license.

**Q: Can I generate portraits of living people?**
A: Technically yes, but be mindful of privacy, likeness rights, and ethical considerations.

---

For questions or issues, please open an issue on GitHub.
