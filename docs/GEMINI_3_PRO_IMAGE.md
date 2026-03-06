## Gemini Image Models - Advanced Features Guide

**Version 2.5.0** | **Default Model: gemini-3.1-flash-image-preview (Nano Banana 2)**
> Also supports: gemini-3-pro-image-preview (maximum quality) and gemini-exp-1206 (legacy)

---

### Overview

Portrait Generator 2.0.0 introduces comprehensive support for Gemini 3 Pro Image (code-named "Nano Banana Pro"), Google's most advanced image generation model. This upgrade brings state-of-the-art AI capabilities to portrait generation with an autonomous, intelligent pipeline designed for 85%+ first-attempt success rate.

### What's New in 2.0.0

**Core Enhancements:**
- Google Search grounding for real-time fact-checking
- Multi-image reference support (up to 14 reference images)
- Internal reasoning and iterative refinement
- Physics-aware visual synthesis
- Native LLM-based text rendering
- Pre-generation feasibility checks
- Autonomous error detection and prevention
- Smart retry with prompt refinement

**Model Change:**
- **Previous Default:** `gemini-exp-1206` (legacy)
- **New Default:** `gemini-3-pro-image-preview` (recommended)
- Backward compatible with all existing models

---

### Advanced Capabilities

#### 1. Google Search Grounding

Real-time fact-checking and verification using Google Search.

**Features:**
- Biographical data verification (birth/death years, era, etc.)
- Historical photograph discovery and authentication
- Fact-checking visual elements against historical records
- Cultural and regional context validation

**Usage:**
```python
from portrait_generator import PortraitClient

client = PortraitClient(
    model="gemini-3.1-flash-image-preview",
    enable_search_grounding=False  # Default: False (changed in v2.1.0 — grounding API returns empty results)
)

result = client.generate("Marie Curie")
# Automatically fact-checks biographical data and visual elements
```

**Configuration:**
```bash
# .env file
ENABLE_SEARCH_GROUNDING=false  # Default: false (grounding API returns empty results since v2.1.0)
```

---

#### 2. Multi-Image Reference Support

Use up to 14 authentic reference images to guide generation. Images are discovered
automatically via a **10-tier cascade (Tiers 0-9)**, or you can supply your own.

**Tier priorities (highest → lowest):**
| Tier | Source | Score | When used |
|------|--------|-------|-----------|
| 0 | `ExampleReferenceImages/` local files | 1.09 | Always (if registered) |
| 1 | Hardcoded confirmed URL table | 1.04 | Pre-researched subjects |
| 2 | On-disk Gemini URL cache | 1.00 | Repeat runs |
| 3 | Wikipedia GroundTruth photo | 0.97 | Wikipedia has a photo |
| 4 | Wikipedia REST thumbnail | 0.95 | Wikipedia page exists |
| 5 | Wikidata P18 image | 0.92 | Wikidata has photo |
| 6 | Gemini web search | 0.88 | AI-discovered image |
| 7 | Wikipedia page images | 0.88 | Embedded page images |
| 8 | Wikimedia Commons search | 0.88 | Commons category match |
| 9 | DBpedia thumbnail | 0.85 | Last resort |

**Supplying your own reference images (Tier 0 — highest priority):**

Place photos in `ExampleReferenceImages/` and register them in `reference_finder.py`:

```python
# In src/portrait_generator/reference_finder.py
_LOCAL_REFERENCE_FILES: Dict[str, list] = {
    # Add your subject here — filenames relative to ExampleReferenceImages/
    "Jane Smith": ["JaneSmith_headshot.jpg", "JaneSmith_conference.jpg"],
}
```

Then clear the cache and regenerate:
```bash
rm -rf .cpf/reference_images/jane_smith/
portrait-generator generate "Jane Smith" --styles Painting
```

**Automatic discovery usage:**
```python
from portrait_generator import PortraitClient

client = PortraitClient(
    enable_reference_images=True,  # Default: True
    max_reference_images=5  # Default: 5, max: 14
)

result = client.generate("Alan Turing")
# Automatically finds and uses historical photographs
```

**Configuration:**
```bash
# .env file
ENABLE_REFERENCE_IMAGES=true
MAX_REFERENCE_IMAGES=5
```

---

#### 3. Internal Reasoning & Iterative Refinement

Model thinks through the task and refines internally before outputting.

**Features:**
- Pre-generation analysis and planning
- Internal quality checks
- Iterative improvement (up to 5 internal iterations)
- Self-evaluation and refinement
- Autonomous quality optimization

**Usage:**
```python
client = PortraitClient(
    enable_internal_reasoning=True,  # Default: True
    max_internal_iterations=3  # Default: 3
)

result = client.generate("Ada Lovelace")
# Model internally refines the portrait 3 times before final output
```

**Configuration:**
```bash
# .env file
ENABLE_INTERNAL_REASONING=true
MAX_INTERNAL_ITERATIONS=3
```

---

#### 4. Physics-Aware Visual Synthesis

Ensures physically accurate rendering of lighting, shadows, and materials.

**Features:**
- Realistic lighting and shadows
- Anatomically correct proportions
- Natural material physics (fabric drape, hair flow)
- Depth and perspective accuracy
- Subsurface scattering for skin

**Usage:**
```python
# Automatically enabled for gemini-3-pro-image-preview
client = PortraitClient(
    enable_visual_coherence_checking=True  # Default: True
)

result = client.generate("Claude Shannon")
# Evaluator checks for physics-aware coherence
```

---

#### 5. Pre-Generation Validation

Proactive error detection before generation starts.

**Features:**
- Biographical data validation
- Fact-checking with Google Search
- Reference image compatibility checks
- Prompt quality assessment
- Feasibility prediction with confidence scores

**Usage:**
```python
client = PortraitClient(
    enable_pre_generation_checks=True  # Default: True
)

result = client.generate("Grace Hopper")
# Validates inputs before spending API credits
```

**Configuration:**
```bash
# .env file
ENABLE_PRE_GENERATION_CHECKS=true
```

---

#### 6. Holistic AI-Powered Evaluation

Multi-pass reasoning-based quality assessment.

**Features:**
- 2-pass evaluation for consistency
- AI-powered holistic quality scoring
- Visual coherence analysis
- Fact-checking visual elements
- Comprehensive feedback generation

**Usage:**
```python
client = PortraitClient(
    use_holistic_reasoning=True,  # Default: True
    reasoning_passes=2  # Default: 2
)

result = client.generate("Donald Knuth")
# Evaluation uses AI reasoning across 2 passes
```

**Configuration:**
```bash
# .env file
USE_HOLISTIC_REASONING=true
REASONING_PASSES=2
```

---

#### 7. Smart Retry with Autonomous Error Recovery

Intelligent retry logic with prompt refinement.

**Features:**
- Automatic error analysis
- Prompt refinement based on failure
- Adaptive quality thresholds
- Maximum 85%+ first-attempt success target
- Graceful degradation

**Usage:**
```python
client = PortraitClient(
    enable_smart_retry=True,  # Default: True
    max_generation_attempts=2  # Default: 2
)

result = client.generate("Margaret Hamilton")
# Automatically retries with refined prompt if first attempt fails
```

**Configuration:**
```bash
# .env file
ENABLE_SMART_RETRY=true
MAX_GENERATION_ATTEMPTS=2
```

---

### Configuration Reference

#### Model Selection

```python
from portrait_generator import PortraitClient

# Use gemini-3-pro-image-preview (recommended)
client = PortraitClient(model="gemini-3-pro-image-preview")

# Use legacy model (basic features only)
client = PortraitClient(model="gemini-exp-1206")

# Use fast model
client = PortraitClient(model="gemini-2.0-flash-exp")
```

#### Environment Variables

Complete list of environment variables for Gemini 3 Pro Image:

```bash
# Core Settings
GEMINI_MODEL=gemini-3-pro-image-preview
GOOGLE_API_KEY=your_api_key_here

# Advanced Features (all default to true for gemini-3-pro-image-preview)
ENABLE_ADVANCED_FEATURES=true

# Reference Images
ENABLE_REFERENCE_IMAGES=true
MAX_REFERENCE_IMAGES=5

# Google Search Grounding
ENABLE_SEARCH_GROUNDING=false  # Default: false — grounding API returns empty results (see README Known Issues)

# Internal Reasoning
ENABLE_INTERNAL_REASONING=true
MAX_INTERNAL_ITERATIONS=3

# Pre-Generation Validation
ENABLE_PRE_GENERATION_CHECKS=true
ENABLE_AUTONOMOUS_ERROR_DETECTION=true

# Quality Thresholds
QUALITY_THRESHOLD=0.90
CONFIDENCE_THRESHOLD=0.85

# Evaluation
USE_HOLISTIC_REASONING=true
REASONING_PASSES=2
ENABLE_VISUAL_COHERENCE_CHECKING=true

# Generation Behavior
MAX_GENERATION_ATTEMPTS=2
ENABLE_SMART_RETRY=true

# Text Rendering
USE_NATIVE_TEXT_RENDERING=true
```

#### Programmatic Configuration

```python
from portrait_generator import PortraitClient

client = PortraitClient(
    api_key="your_api_key",
    model="gemini-3-pro-image-preview",

    # Advanced features
    enable_advanced_features=True,
    enable_reference_images=True,
    max_reference_images=5,
    enable_search_grounding=True,
    enable_internal_reasoning=True,
    max_internal_iterations=3,

    # Quality settings
    quality_threshold=0.90,
    confidence_threshold=0.85,

    # Evaluation
    use_holistic_reasoning=True,
    reasoning_passes=2,
    enable_visual_coherence_checking=True,

    # Generation
    max_generation_attempts=2,
    enable_smart_retry=True,
)
```

---

### Model Comparison

| Feature | gemini-3-pro-image-preview | gemini-exp-1206 | gemini-2.0-flash-exp |
|---------|----------------------------|-----------------|----------------------|
| **Google Search Grounding** | ✓ | ✗ | ✗ |
| **Multi-Image Reference** | ✓ (14 max) | ✗ | ✗ |
| **Internal Reasoning** | ✓ | ✗ | ✗ |
| **Physics-Aware Synthesis** | ✓ | ✗ | ✗ |
| **Native Text Rendering** | ✓ | ✗ | ✓ (basic) |
| **Iterative Refinement** | ✓ | ✗ | ✗ |
| **Max Resolution** | 4096x4096 | 1024x1024 | 1024x1024 |
| **Quality Threshold** | 0.90 | 0.80 | 0.75 |
| **Typical Gen Time** | 45s | 30s | 20s |
| **Recommended** | ✓ | ✗ | ✗ |

---

### Migration from gemini-exp-1206

Portrait Generator 2.0.0 is **100% backward compatible** with gemini-exp-1206 and older models.

#### Option 1: Automatic Migration (Recommended)

Simply update to v2.0.0 - the new default model is gemini-3-pro-image-preview:

```bash
pip install --upgrade portrait-generator
```

All advanced features are automatically enabled. No code changes required.

#### Option 2: Explicit Model Selection

Continue using legacy model if preferred:

```python
from portrait_generator import PortraitClient

# Explicitly use legacy model
client = PortraitClient(model="gemini-exp-1206")

result = client.generate("Alan Turing")
# Works exactly as before - no advanced features
```

#### Option 3: Gradual Migration

Enable advanced features selectively:

```python
client = PortraitClient(
    model="gemini-3-pro-image-preview",
    enable_reference_images=True,  # Start with references
    enable_search_grounding=False,  # Disable grounding initially
    enable_internal_reasoning=False,  # Disable reasoning initially
)
```

---

### Performance Optimization

#### Quality vs Speed Tradeoffs

**Maximum Quality (Recommended):**
```python
client = PortraitClient(
    model="gemini-3-pro-image-preview",
    max_reference_images=10,
    max_internal_iterations=5,
    reasoning_passes=3,
    quality_threshold=0.95,
)
# Slower but highest quality
```

**Balanced (Default):**
```python
client = PortraitClient(
    model="gemini-3-pro-image-preview",
    # Uses default settings
)
# Optimized balance of quality and speed
```

**Fast Mode:**
```python
client = PortraitClient(
    model="gemini-2.0-flash-exp",
    enable_advanced_features=False,
    max_generation_attempts=1,
)
# Faster generation, lower quality
```

---

### Advanced Usage Examples

#### Example 1: Maximum Authenticity

```python
from portrait_generator import PortraitClient

client = PortraitClient(
    model="gemini-3-pro-image-preview",
    enable_reference_images=True,
    max_reference_images=14,  # Use maximum references
    enable_search_grounding=True,
    enable_pre_generation_checks=True,
    quality_threshold=0.95,  # Very high threshold
)

result = client.generate("Ada Lovelace")

# Check evaluation details
print(f"Quality score: {result.evaluation['BW'].scores.get('overall', 0):.2f}")
print(f"Fact-checked: {result.evaluation['BW'].scores.get('historical_accuracy', 0):.2f}")
```

#### Example 2: Academic Research Use

```python
client = PortraitClient(
    model="gemini-3-pro-image-preview",
    enable_search_grounding=True,  # Verify all facts
    enable_visual_coherence_checking=True,  # Physics accuracy
    reasoning_passes=3,  # Triple-check consistency
    max_reference_images=10,
)

# Generate for a list of historical figures
subjects = [
    "Charles Babbage",
    "Ada Lovelace",
    "George Boole",
    "Alan Turing",
]

results = client.generate_batch(subjects, styles=["BW", "Sepia"])

# Verify all passed evaluation
for result in results:
    for style, evaluation in result.evaluation.items():
        if not evaluation.passed:
            print(f"Warning: {result.subject} {style} failed evaluation")
```

#### Example 3: Custom Intelligence Coordinator

```python
from portrait_generator.intelligence_coordinator import IntelligenceCoordinator
from portrait_generator.config import Settings

# Create custom settings
settings = Settings(
    gemini_model="gemini-3-pro-image-preview",
    enable_advanced_features=True,
    quality_threshold=0.92,
    max_reference_images=8,
    reasoning_passes=2,
)

# Initialize coordinator
coordinator = IntelligenceCoordinator(settings=settings)

# Get system info
info = coordinator.get_system_info()
print(f"Model: {info['model']}")
print(f"Capabilities: {info['capabilities']}")

# Validate setup
is_valid, issues = coordinator.validate_setup()
if not is_valid:
    print(f"Setup issues: {issues}")

# Generate portrait
result = coordinator.generate_portrait("Donald Knuth")
```

---

### Troubleshooting

#### Issue: Advanced features not working

**Solution:** Verify model supports features:
```python
from portrait_generator import PortraitClient

client = PortraitClient(model="gemini-3-pro-image-preview")

# Check capabilities
if hasattr(client, '_compatibility'):
    print(f"Grounding: {client._compatibility.supports_google_search_grounding()}")
    print(f"Multi-image: {client._compatibility.supports_multi_image_reference()}")
```

#### Issue: Reference images not found

**Solution:** Enable grounding and check availability:
```bash
# Enable search grounding for reference finding
export ENABLE_SEARCH_GROUNDING=true
```

#### Issue: Quality threshold too high, all fail

**Solution:** Lower threshold for specific model:
```python
client = PortraitClient(
    quality_threshold=0.85,  # Lower from default 0.90
    confidence_threshold=0.80,
)
```

#### Issue: Generation too slow

**Solution:** Reduce advanced features:
```python
client = PortraitClient(
    max_reference_images=3,  # Reduce from 5
    max_internal_iterations=2,  # Reduce from 3
    reasoning_passes=1,  # Reduce from 2
)
```

---

### API Cost Considerations

Gemini 3 Pro Image with advanced features costs more per generation than basic models.

**Estimated Costs (as of Jan 2026):**
- Basic generation (gemini-exp-1206): ~$0.01-0.02 per portrait
- Advanced generation (gemini-3-pro-image-preview): ~$0.03-0.06 per portrait
- With maximum references (14 images): ~$0.08-0.12 per portrait

**Cost Optimization:**
- Use pre-generation checks to avoid failed generations
- Reduce max_reference_images for lower costs
- Enable smart_retry to minimize wasted attempts
- Use quality_threshold appropriately to avoid unnecessary regeneration

---

### Feature Roadmap

**Planned for 2.1.0:**
- Batch parallel processing with concurrent reference finding
- Custom reference image upload
- Fine-grained physics control (lighting direction, etc.)
- Export evaluation reports as PDF
- Video portrait generation

**Planned for future releases:**
- Multi-model ensemble (combine outputs from multiple models)
- Style transfer from reference images
- Interactive refinement workflow
- Integration with additional search providers

---

### Best Practices

1. **Always use pre-generation checks** to validate inputs before API calls
2. **Start with default settings** and optimize based on results
3. **Monitor evaluation scores** to identify patterns in failures
4. **Use reference images** for historical subjects (pre-1950)
5. **Enable fact-checking** for academic or educational use
6. **Lower thresholds** if generating for artistic purposes
7. **Use smart retry** to recover from transient failures
8. **Test with a single subject** before batch processing

---

### Support

- **Documentation:** https://portrait-generator.readthedocs.io
- **GitHub Issues:** https://github.com/davidlary/PortraitGenerator/issues
- **Discussions:** https://github.com/davidlary/PortraitGenerator/discussions

---

### Version History

**2.5.0 (March 6, 2026):**
- Name collision disambiguation: John A. Pyle, Andrew C. Lorenc, Mike Fisher (1962-Present) — researched middle initials or lifespan suffix
- Lifespan suffix auto-stripped for overlay display and Gemini/Wikipedia research; retained in filenames only
- PascalCase filename fix: digit-starting word segments (e.g. "1962Present") no longer lowercased

**2.4.2 (March 6, 2026):**
- Reference-photo age matching: portrait age/hair/skin now driven by reference photos, not calculated value
- `_NoRef` filename suffix for portraits generated without any reference images (Whipple, Scrase, Findeisen, Pfotzer)
- No decorative frames rule added to Painting style — prevents ornate gold-frame artefacts
- Color tonality matching (#8 in FACIAL CONSISTENCY): preserve hair colour from references, do not lighten/grey
- Profession-appropriate attire rule: scientists wear academic dress, not sports/casual from reference photo

**2.4.1 (March 6, 2026):**
- Facial expression matching: portrait prompts now instruct AI to replicate reference photo expression
- Facial hair matching: portraits replicate beard/clean-shaven state from reference photos
- YAML-backed verified biographies with auto-update for high-confidence discoveries
- David Lary: 3 user-provided local photos registered as Tier 0 (score 1.09, highest priority)
- John A. Pyle: expanded to 5 confirmed Cambridge URLs (St Catharine's 1896×1422 as primary)
- Andrew C. Lorenc: upgraded to RMetS full portrait (1429×1382), name collision noted in YAML
- _LOCAL_REFERENCE_FILES expanded to 26 subjects

**2.0.0 (January 30, 2026):**
- Added Gemini 3 Pro Image (Nano Banana Pro) support
- Implemented Google Search grounding
- Added multi-image reference support (up to 14 images)
- Implemented internal reasoning and iterative refinement
- Added physics-aware synthesis
- Implemented pre-generation validation
- Added holistic AI-powered evaluation
- Implemented smart retry with prompt refinement
- Changed default model to gemini-3-pro-image-preview
- Maintained 100% backward compatibility

**1.0.0 (Previous):**
- Initial release with gemini-exp-1206

---

**For complete API reference, see the main [README.md](../README.md)**
