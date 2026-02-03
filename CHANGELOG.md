# Changelog

All notable changes to Portrait Generator will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
