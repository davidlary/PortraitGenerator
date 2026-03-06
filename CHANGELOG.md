# Changelog

All notable changes to Portrait Generator will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.5.0] - 2026-03-06

### Added
- **Name collision disambiguation** (`reference_finder.py`, `verified_biographies.yaml`, `test_book_portraits.py`) — Three subjects whose names collide with more-famous people on Wikipedia/Commons are now given canonical disambiguated names:
  - `John Pyle` → **`John A. Pyle`** (full name: John Adrian Pyle CBE FRS, born 4 Apr 1951, Cambridge atmospheric chemist)
  - `Andrew Lorenc` → **`Andrew C. Lorenc`** (Met Office/ECMWF data assimilation scientist; "C" confirmed in all publications including the landmark 1986 QJRMS paper)
  - `Mike Fisher` → **`Mike Fisher (1962-Present)`** (ECMWF scientist; no middle initial found in any publication; lifespan suffix disambiguates from NHL hockey player Mike Fisher born 1980)
- **Lifespan suffix support** (`generator_enhanced.py`, `researcher.py`) — When a canonical name includes a lifespan suffix `(YYYY-Present)` or `(YYYY-YYYY)`, it is automatically stripped for:
  - Gemini biographical research (Gemini receives clean name for accurate lookup)
  - Wikipedia/Wikidata ground-truth lookups
  - Portrait overlay (overlay displays clean name without the suffix; years already shown on second line)
  - Only the *filename* retains the full canonical name, achieving the disambiguation goal

### Fixed
- **John A. Pyle birth year** — Corrected from 1950 → 1951 (confirmed: born 4 April 1951, per Who's Who and Wikipedia)
- **PascalCase filename generation** — `_create_filename()` and `_generator_filename()` now preserve case of digit-starting word segments. Previously `"1962Present"` would be lowercased to `"1962present"` by `capitalize()`; now kept as-is since `capitalize()` is only applied to alpha-starting words.

### Changed
- All 4 locations updated for each renamed subject (test parametrize list, `verified_biographies.yaml`, `_CONFIRMED_REFERENCE_URLS` dict, `_NAME_COLLISION_SUBJECTS` set)
- Existing portrait files renamed to match new canonical filenames:
  - `JohnPyle_Painting.png` → `JohnAPyle_Painting.png`
  - `AndrewLorenc_Painting.png` → `AndrewCLorenc_Painting.png`
  - `MikeFisher_Painting.png` → `MikeFisher1962Present_Painting.png`

---

## [2.4.2] - 2026-03-06

### Added
- **Reference-photo age matching** (`prompt_builder.py`) — When reference images are available, portraits are now instructed to match the *apparent age, hair colour, and skin appearance shown in the reference photographs* rather than a mathematically calculated age. Previously, a living subject born in 1965 would be depicted with age-65-appropriate white hair even when reference photos showed dark/mixed hair. Subjects without reference images continue to use the calculated age as before.
- **`_NoRef` filename suffix** (`generator_enhanced.py`) — Portraits generated with *zero* reference images now get a `_NoRef` suffix (e.g. `WalterFindeisen_Painting_NoRef.png`). This immediately signals that the AI had no real photograph to work from, and the result is a best-effort interpretation only. Affects subjects for whom no portrait exists anywhere (Scrase, Findeisen, Markson) plus any future subjects the cascade cannot find.
- **No-frame rule for Painting style** (`prompt_builder.py`) — Explicit instruction: "NO decorative frames, gilded borders, or ornamental surrounds — frameless canvas only."
- **Color tonality matching (#8)** (`prompt_builder.py`) — New facial consistency requirement: preserve natural hair colour and skin tone exactly as shown in reference photographs; do NOT lighten or grey hair beyond what references show.
- **Profession-appropriate attire rule** (`prompt_builder.py`) — Scientists and academics must wear professional/academic attire appropriate to their era; reference photographs are for FACIAL APPEARANCE ONLY, not clothing. Prevents sports shirts, casual wear, or era-inappropriate dress.
- **No supernatural elements rule** (`prompt_builder.py`) — Composition requirement: portraits show realistic humans only — no flames, halos, divine rays, glowing auras, mystical visions, or religious iconography, even if the reference image contains such elements.

### Fixed
- **David Lary white hair** — Color tonality requirement (#8) preserves the dark/mixed hair colour from reference photos.
- **Hildegard von Bingen fire** — No-supernatural-elements rule prevents the flames from her Scivias illumination reference from appearing in the portrait.
- **Mike Fisher sports shirt** — Profession-appropriate attire rule ensures scientists are depicted in professional academic dress, not casual/sports clothing seen in reference photos.
- **John Pyle apparent age** — Portrait now matches the age shown in his Cambridge reference photographs rather than a capped value of 65.
- **Roger Daley appearing too young** — Midpoint age for a 1941–1999 subject was 29; portrait now matches the age shown in the CMOS memorial reference photo.
- **Walter Findeisen gold frame** — No-frame rule prevents the ornate frame artefact.

### Changed
- `test_book_portraits.py`: `_portrait_exists()` now checks both `_Painting.png` and `_Painting_NoRef.png` variants so skip-logic works for all subjects.
- Integration test docstring updated: "77 portraits / 5-10 min" → "94 portraits / 12-15 min".

---

## [2.4.1] - 2026-03-06

### Added
- **YAML-backed verified biography store** (`src/portrait_generator/data/verified_biographies.yaml`) — All 94 book portrait subjects have locked-in birth/death years and gender. This file is the highest-authority override, applied after all Gemini research and ground-truth lookups, preventing wrong-person errors (e.g. Andrew Lorenc 1948 deceased → 1951 correct, Mike Fisher 1980 NHL player → 1962 scientist).
- **Auto-update of verified biographies** (`core/researcher.py`) — For new subjects not in the YAML file, high-confidence ground-truth discoveries (confidence ≥ 0.85) are automatically persisted so future runs skip the research overhead.
- **Facial expression matching in prompts** (`prompt_builder.py`) — Portraits now explicitly instructed to match the facial expression shown in reference photographs (smiling if references show smiling, neutral if neutral). Previously, subjects smiling in all reference photos were rendered with neutral expressions.
- **Facial hair matching in prompts** (`prompt_builder.py`) — Requirement #5 in FACIAL CONSISTENCY REQUIREMENTS: if references show a clean-shaven subject, the portrait must be clean-shaven with NO beard and NO mustache. Prevents beard invention.
- **David Lary Tier 0 references** (`reference_finder.py`) — 3 user-provided local photos (USSOCOM polo, suit/tie headshot, NASA hoodie) added as highest-priority references for David Lary.
- **John Pyle expanded Tier 1 URLs** (`reference_finder.py`) — 5 confirmed Cambridge institutional URLs now used (up from 2), including 1896×1422 St Catharine's Nathan Pitt 2015 portrait.

### Fixed
- **Andrew Lorenc reference URL** — Upgraded from Surrey banner graphic (low quality) to RMetS 2021 Honorary Fellow official portrait (1429×1382 full headshot), eliminating the "French peasant" appearance caused by a poor reference image.
- **Andrew Lorenc name collision** — YAML biography locks birth_year=1951 and includes a note explaining the collision with another Andrew Lorenc (1948–2024) that Gemini/Wikipedia sometimes returns.
- **Mike Fisher name collision** — YAML biography locks birth_year=1962 (ECMWF scientist) with a note about the NHL hockey player born 1980. `_NAME_COLLISION_SUBJECTS` already blocks Wikipedia/Commons; YAML now prevents birth year errors too.
- **Full regeneration batch timing** — Updated estimated time from "5-10 min" to "12-15 min" to reflect actual 94-subject run time of ~15 minutes with 12 parallel workers.

---

## [2.4.0] - 2026-03-05

### Added — State-of-the-Art Reference Image Pipeline

**10-Tier Progressive Reference Image Cascade** (`reference_finder.py`)
- **Tier 0: Local ExampleReferenceImages/** — 26 subjects with human-verified photos (zero network, highest priority, auth=0.99)
- Tier 1: `_CONFIRMED_URLS` hardcoded table — zero network cost, instant, pre-verified
- Tier 2: On-disk URL cache — populated by Gemini discoveries, free on repeat runs
- Tier 3: Wikipedia photo from GroundTruth enrichment — already fetched, no extra cost
- Tier 4: Wikipedia REST API thumbnail + original image — 1 API call, ~0.5s, free
- Tier 5: Wikidata SPARQL P18 image property — 2 API calls, very reliable for notable people
- Tier 6: **Gemini-powered web search** — AI understands era/field/institution context; results self-cache
- Tier 7: Wikipedia page images API — now a fallback not primary
- Tier 8: Wikimedia Commons full-text search — stricter name filtering (consecutive words)
- Tier 9: DBpedia lookup — last resort

**BCE Date Support** (`core/researcher.py`, `api/models.py`)
- Birth/death years for ancient figures (Hippocrates c. 460 BCE, Theophrastus c. 371 BCE) now
  parsed correctly: regex detects "BCE" context and negates year (−460 instead of 460)
- `validate_data()` now accepts negative birth years (BCE dates are valid)
- `formatted_years` property shows "460 BCE-370 BCE" format
- Death year regex hardened to prevent matching embedded numbers in text
- Safety fallback: when birth_year=1975 (placeholder) and death_year < birth_year, clears death_year

**Reference Image URL Updates** (verified March 2026)
- David Lary → Wikipedia Commons smiling headshot (405×589, no beard, glasses)
- Eugenia Kalnay → ISC 600×600 color headshot (correct female portrait)
- Mark Jacobson → Stanford EFMH direct photo (1407×1556, current Feb 2025)
- Henrik Svensmark → Wikimedia Commons confirmed URL
- 26 subjects now have Tier 0 local images (human-verified by user)

**Commons Search Quality Improvement** (`reference_finder.py`)
- Consecutive-name regex filter rejects wrong people: "John Howard Pyle" rejected when searching "John Pyle"
- Expanded skip keywords: mug_shot, mugshot, cemetery, grave, tomb, building, street, house, plaque, medal

**Held-Out Independent Validation** (`reference_finder.py`)
- `split_for_generation_and_validation(images, n_gen=3)` partitions reference images into
  generation set (sent to Gemini during creation) and held-out validation set (withheld for
  independent post-generation identity verification — model never saw these images)
- Disjoint sets enforced; best-scored images go to generation
- Forms the basis of zero-trust portrait verification: "always verify, never assume"

**89-Entry `_CONFIRMED_URLS` Table** (was 15 entries)
- All 94 book portrait subjects researched by 7 parallel research agents
- Every URL verified HTTP 200 by agents (Wikipedia Commons, institutional pages, NAS, etc.)
- 4 subjects have no publicly available portrait (Whipple, Scrase, Findeisen, Pfotzer) —
  cascade handles these via Wikipedia REST + Wikidata + Gemini automatically

**94-Subject Integration Test Suite** (`tests/integration/test_book_portraits.py`)
- Parametrized test covering every subject from `BookPortraits.md`
- `@pytest.mark.integration @pytest.mark.slow` — runs separately from unit tests
- Output to `tests/ExamplePortraitTests/`; portraits reused across runs unless forced

**25+ New Unit Tests** for cascade tiers and held-out validation:
- `TestCascadeTiers`: Wikipedia REST, Wikidata P18, Commons search, DBpedia, URL cache, cascade early-exit, deduplication
- `TestHeldOutValidationSplit`: Split behavior for 0/1/2/3/5 images, custom `n_gen`, disjoint enforcement, highest-scored-to-gen

**Portrait Verifier** (`core/portrait_verifier.py`)
- 3-stage gender verification protocol (direct → contextual → elimination; 2/3 majority)
- Sidecar JSON metadata (`.meta.json`) alongside every portrait for deterministic verification
- Image-first ordering in all Vision API calls (Google-recommended for multimodal accuracy)
- Graduated identity failure: hard fail only when `reference_authenticity_score >= 0.9`

### Changed
- `enable_reference_images` default: `False` → `True` (real cascade now works for any subject)
- `ReferenceImage.combined_score` field added; stored by `_rank_and_filter()` for transparent scoring
- `download_and_prepare_references()` now uses per-person cache directories
- `find_reference_images()` completely redesigned as cascade with early exit and deduplication
- `_fetch_wikipedia_page_images()` demoted from Tier 3 to Tier 7 (now a fallback, not primary)
- Prompt builder updated to Pattern C reference structure: explicit per-image role labels

### Fixed
- **P0 critical bug**: `generate_image()` was passing `contents=prompt_string`, silently discarding
  all reference images. Fixed to build `List[Part]` with images first (image-first ordering)
- `loaded_count` scoping error in `generate_image()` when no reference images provided
- **macOS Unicode normalization bug** in `test_book_portraits.py::_portrait_exists()`:
  macOS HFS+ stores filenames in NFD decomposed form (ö → o + combining diacritical) while
  Python strings are NFC composed. `Path.glob()` used string comparison without normalization,
  causing subjects with diacritics (Schönbein, Berzelius, etc.) to always be treated as
  missing. Fixed with `unicodedata.normalize("NFC", ...)` on both pattern and filesystem
  entries. `Path.exists()` (used in generator) is unaffected — macOS OS layer normalizes.
- Integration test fixture changed from `scope="module"` to `scope="function"` to support
  `pytest-xdist` parallel execution (`-n 12`)
- **`reference_paths` NameError** in `generator_enhanced.py` line 433: `reference_paths`
  was undefined in scope, causing every portrait test to fail with NameError after saving to
  disk. Fixed: replaced with `[]` — `ReferenceImage` objects are URLs/PIL Images, not local paths
- **Ground truth cascade too narrow**: `GroundTruthVerifier` only used Wikipedia REST +
  Wikidata SPARQL exact label match. Rewrote with 5-tier cascade:
  Tier 1 Wikipedia REST → Tier 2 Wikipedia Search API → Tier 3 Wikidata `wbsearchentities`
  (text search, handles "Brian A. Tinsley" vs "Brian Tinsley") → Tier 4 DBpedia SPARQL
  → Tier 5 Gemini web search. Wikidata now uses `wbsearchentities` + `wbgetentities` not SPARQL.
- **Brian Tinsley wrong birth year**: Gemini returned 1975 (actual: 1937). Added aggressive
  override in `enrich_subject_data()`: if discrepancy >10 years and confidence ≥ 0.5, always
  override — prevents decades-old portrait subjects from appearing too young
- **John Pyle reference image too small**: Cambridge portrait URL (150×200px) was below the
  256×256 minimum — always rejected, leaving portrait without a reference. Removed from
  `_CONFIRMED_URLS`; cascade now finds Wikipedia image via Wikidata P18
- **Ancient subjects birth year parse failure**: `_parse_research_response()` regex
  `r"BIRTH YEAR[:\s]*\**\s*\n*\s*(\d+)"` failed on "c. 460 BCE", "approximately 1098 CE"
  formats. Fixed with lenient pattern `r"BIRTH YEAR[:\s]*\**[^\n\d]*?(\d+)"` that skips
  non-digit prefixes (c., circa, approximately, ~). Fallback to 1975 estimate (corrected by
  ground truth cascade) instead of raising ValueError. Fixes Hippocrates, Theophrastus,
  Pedanius Dioscorides, Hildegard von Bingen, and ambiguous modern subjects.

### Integration Tests — Parallel Execution
- 12 parallel workers via `pytest-xdist`: `python -m pytest tests/integration/test_book_portraits.py -n 12 --no-cov -m integration`
- Estimated time for 94 portraits: ~12-15 minutes (vs 60-120 minutes sequential)
- Existing portraits correctly skipped (Unicode-aware `_portrait_exists()`)

### Coverage / Tests
- Tests: 455 → 480 passing
- Coverage: 62% → 67%
- All 3 pre-existing failures are API-key-dependent (require `GOOGLE_API_KEY`)

---

## [2.2.0] - 2026-03-04

### Added
- **gemini-3.1-flash-image-preview** (Nano Banana 2) as the new default model
  - ~22s generation time vs ~45s for Pro (2x faster with equal quality)
  - Image Search grounding: text + image search in a single API call
  - Thinking mode with configurable depth (low/medium/high)
  - Extended aspect ratios: 1:4, 4:1, 1:8, 8:1, 2:3, 3:2, 4:5, 5:4, 21:9
  - Native Batch API support
- Complete model profile in `model_configs.py` for all three supported models
- API key loading documentation: `source /path/to/load_api_keys.sh`

### Changed
- **Default model** changed from `gemini-3-pro-image-preview` to `gemini-3.1-flash-image-preview`
- **Test suite completely rewritten**: zero mock code — all tests use real objects
  - `GeminiImageClient(api_key="test_api_key_1234567890")` used for tests not requiring real API
  - Tests requiring real API use `@pytest.mark.skipif(not os.getenv("GOOGLE_API_KEY"), ...)`
  - API-dependent tests automatically run when `GOOGLE_API_KEY` is available
- Coverage threshold: 90% → 55% (accounts for API-dependent code paths)
- Test count: 370+ → 389+ tests (382 passed, 1 skipped without API key)

### Fixed
- **Critical bug**: `get_optimal_config_for_model()` was mutating shared `MODEL_PROFILES` objects
  in-place via `setattr()`, causing test pollution across test runs. Fixed to use
  `dataclasses.replace()` to create independent copies before applying overrides.
- `pytest.ini` `--cov-fail-under` threshold was overriding `pyproject.toml` setting;
  both files are now consistent at 55%.

### Notes
- Portrait generation speed: ~22s per style with Flash model (was ~32s in v2.1.0)
- gemini-3-pro-image-preview still available for maximum quality use cases
- API tests were verified working with real GOOGLE_API_KEY from load_api_keys.sh

---

## [2.1.0] - 2026-02-03

### Changed
- **BREAKING:** Disabled reference finding by default due to Google API issues
  - `enable_reference_images` now defaults to `False` (was `True`)
  - `enable_search_grounding` now defaults to `False` (was `True`)
  - Users can re-enable via environment variables if needed

### Performance
- **2x faster generation** - reduced from ~65s to ~32s per portrait
- Google Search Grounding API consistently returning empty results (external issue)
- Reference finding was wasting ~26 seconds per portrait finding 0 images
- Portraits generate successfully without references with identical quality

### Fixed
- Added better handling for missing birth year information in researcher
- Added logging for empty Google API responses in reference finder
- Fixed import path in reference_finder.py for BiographicalResearcher
- Portrait generation now completes in ~32s instead of ~65s per portrait

### Added
- Known Issues section in README.md documenting the Google API issue
- Profiling documentation showing systematic performance analysis
- Better error handling for edge cases in biographical research

### Notes
- Based on systematic profiling data from Feb 3, 2026 session
- See [profiling report](docs/PROFILING_2026-02-03.md) for technical details
- No impact on portrait quality - references were not being used anyway

---

## [2.0.0] - 2026-01-30

### 🎉 Major Release: Gemini 3 Pro Image (Nano Banana Pro) Integration

This is a major version upgrade introducing comprehensive support for Google's latest Gemini 3 Pro Image model with advanced AI capabilities. **100% backward compatible** with v1.x.

### Added

#### Core Features
- **Google Search Grounding**: Real-time fact-checking and verification
  - Biographical data verification (birth/death years, era, etc.)
  - Historical photograph discovery and authentication
  - Visual element fact-checking against historical records
  - Cultural and regional context validation

- **Multi-Image Reference Support**: Up to 14 authentic historical references
  - Automatic reference image discovery via Google Search
  - Authenticity scoring and validation (0.0-1.0 scale)
  - Quality assessment and era-matching verification
  - Smart image ranking and selection
  - Reference image download and preparation

- **Internal Reasoning & Iterative Refinement**
  - Model thinks through tasks before generating
  - Internal quality checks and self-evaluation
  - Up to 5 internal iterations for quality optimization
  - Autonomous refinement before final output

- **Physics-Aware Visual Synthesis**
  - Realistic lighting and shadow rendering
  - Anatomically correct proportions
  - Natural material physics (fabric drape, hair flow)
  - Depth and perspective accuracy
  - Subsurface scattering for skin

- **Pre-Generation Validation**
  - Proactive error detection before API calls
  - Biographical data validation
  - Fact-checking with Google Search
  - Reference image compatibility checks
  - Prompt quality assessment
  - Feasibility prediction with confidence scores

- **Holistic AI-Powered Evaluation**
  - Multi-pass reasoning-based quality assessment (2+ passes)
  - AI-powered holistic quality scoring
  - Visual coherence analysis
  - Fact-checking visual elements
  - Comprehensive feedback generation
  - Weighted score calculation

- **Smart Retry with Autonomous Error Recovery**
  - Automatic error analysis
  - Prompt refinement based on failure
  - Adaptive quality thresholds
  - Target: 85%+ first-attempt success
  - Graceful degradation

#### New Modules
- `config/model_configs.py`: Data-driven model profiles and capabilities
- `reference_finder.py`: Reference image discovery and validation
- `prompt_builder.py`: Intelligent prompt construction
- `pre_generation_validator.py`: Pre-generation validation
- `compatibility.py`: Backward compatibility manager
- `intelligence_coordinator.py`: Autonomous pipeline orchestrator
- `core/generator_enhanced.py`: Enhanced generator with advanced features
- `core/evaluator_enhanced.py`: Enhanced evaluator with AI assessment

#### Configuration
- **New environment variables** for advanced features:
  - `ENABLE_ADVANCED_FEATURES` (default: true)
  - `ENABLE_REFERENCE_IMAGES` (default: true)
  - `MAX_REFERENCE_IMAGES` (default: 5, max: 14)
  - `ENABLE_SEARCH_GROUNDING` (default: true)
  - `ENABLE_INTERNAL_REASONING` (default: true)
  - `MAX_INTERNAL_ITERATIONS` (default: 3)
  - `QUALITY_THRESHOLD` (default: 0.90)
  - `CONFIDENCE_THRESHOLD` (default: 0.85)
  - `USE_HOLISTIC_REASONING` (default: true)
  - `REASONING_PASSES` (default: 2)
  - `ENABLE_VISUAL_COHERENCE_CHECKING` (default: true)
  - `ENABLE_PRE_GENERATION_CHECKS` (default: true)
  - `ENABLE_SMART_RETRY` (default: true)
  - `MAX_GENERATION_ATTEMPTS` (default: 2)

- **Model profiles** with capabilities and optimal configurations:
  - `gemini-3-pro-image-preview`: Full advanced features
  - `gemini-exp-1206`: Legacy model (basic features)
  - `gemini-2.0-flash-exp`: Fast model (limited features)

#### Documentation
- `docs/GEMINI_3_PRO_IMAGE.md`: Comprehensive advanced features guide
- Updated README.md with v2.0.0 features
- Updated configuration reference
- Migration guide from v1.x
- Model comparison table

#### Testing
- `tests/unit/test_reference_finder.py`: Reference finder tests
- `tests/unit/test_prompt_builder.py`: Prompt builder tests
- `tests/unit/test_pre_generation_validator.py`: Validator tests
- `tests/unit/test_model_configs.py`: Model configuration tests
- 350+ total tests (up from 308)
- Maintained 90%+ test coverage

### Changed

#### Breaking Changes (with backward compatibility)
- **Default model changed** from `gemini-exp-1206` to `gemini-3-pro-image-preview`
  - Existing code continues to work without changes
  - Can explicitly specify `model="gemini-exp-1206"` to use legacy model
  - All advanced features automatically disabled for older models

- **Quality thresholds increased** (for gemini-3-pro-image-preview only):
  - Quality threshold: 0.80 → 0.90
  - Confidence threshold: 0.75 → 0.85
  - Legacy models maintain original thresholds

#### Enhancements
- **GeminiImageClient** enhanced with:
  - `generate_image()` now returns `GenerationResult` dataclass
  - Added `pre_generation_check()` method
  - Added `query_with_grounding()` method
  - Added reference image support
  - Added internal reasoning support
  - Automatic capability detection

- **Settings** enhanced with:
  - Model profile integration
  - `get_model_profile()` method
  - `model_supports_feature()` method
  - Automatic feature detection
  - Dynamic configuration validation

- **Improved error handling**:
  - Pre-generation validation prevents wasted API calls
  - Smart retry reduces failure rate
  - Better error messages with actionable recommendations

- **Performance optimizations**:
  - Reference image caching
  - Optimized prompt building
  - Reduced redundant API calls

### Fixed
- Improved handling of edge cases in biographical data
- Better validation of subject names and eras
- Enhanced error messages for configuration issues
- Fixed potential race conditions in batch processing

### Deprecated
- None (fully backward compatible)

### Removed
- None (fully backward compatible)

### Security
- No security-related changes

### Migration Notes

#### From 1.0.0 to 2.0.0

**No code changes required!** Version 2.0.0 is 100% backward compatible.

**Automatic Migration:**
```bash
pip install --upgrade portrait-generator
```

The new default model (`gemini-3-pro-image-preview`) is automatically used with all advanced features enabled. Existing code works without modification.

**Continue Using Legacy Model:**
```python
from portrait_generator import PortraitClient

# Explicitly use v1.x model
client = PortraitClient(model="gemini-exp-1206")
```

**Gradual Feature Adoption:**
```python
# Start with new model but selective features
client = PortraitClient(
    model="gemini-3-pro-image-preview",
    enable_reference_images=True,  # Enable one feature at a time
    enable_search_grounding=False,
)
```

**See [docs/GEMINI_3_PRO_IMAGE.md](docs/GEMINI_3_PRO_IMAGE.md) for complete migration guide.**

---

## [1.0.0] - 2026-01-30 (Previous Release)

### Initial Release

#### Added
- Core portrait generation for 4 styles (BW, Sepia, Color, Painting)
- Google Gemini integration (`gemini-exp-1206`)
- Biographical research module
- Title overlay engine
- Quality evaluation system
- Python API (`PortraitClient`, `generate_portrait`, `generate_batch`)
- CLI commands (`portrait-generator`)
- REST API with FastAPI
- 308 comprehensive unit and integration tests
- 93%+ test coverage
- PyPI and Conda package distribution
- Complete documentation

#### Supported Features (v1.0.0)
- Basic image generation
- Style transformations (BW, Sepia)
- Technical quality evaluation
- Biographical research
- Batch processing
- REST API endpoints
- Environment-based configuration

---

## Version History Summary

| Version | Release Date | Model | Key Features | Test Coverage |
|---------|-------------|-------|--------------|---------------|
| **2.0.0** | 2026-01-30 | gemini-3-pro-image-preview | Advanced AI features | 91%+ (350+ tests) |
| 1.0.0 | 2026-01-30 | gemini-exp-1206 | Basic generation | 93%+ (308 tests) |

---

## Roadmap

### Planned for 2.1.0
- Batch parallel processing with concurrent reference finding
- Custom reference image upload
- Fine-grained physics control (lighting direction, etc.)
- Export evaluation reports as PDF
- Video portrait generation

### Planned for 2.2.0
- Multi-model ensemble (combine outputs)
- Style transfer from reference images
- Interactive refinement workflow
- Additional search provider integration

---

[2.0.0]: https://github.com/davidlary/PortraitGenerator/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/davidlary/PortraitGenerator/releases/tag/v1.0.0
