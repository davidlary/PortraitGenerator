## Gemini 3 Pro Image (Nano Banana Pro) - Advanced Features Guide

**Version 2.0.0** | **Default Model: gemini-3-pro-image-preview**

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
    model="gemini-3-pro-image-preview",
    enable_search_grounding=True  # Default: True
)

result = client.generate("Marie Curie")
# Automatically fact-checks biographical data and visual elements
```

**Configuration:**
```bash
# .env file
ENABLE_SEARCH_GROUNDING=true
```

---

#### 2. Multi-Image Reference Support

Use up to 14 authentic historical reference images to guide generation.

**Features:**
- Automatic reference image discovery via Google Search
- Authenticity scoring and validation
- Quality assessment
- Era-matching verification
- Smart image ranking and selection

**Usage:**
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
ENABLE_SEARCH_GROUNDING=true

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

**Planned for 2.2.0:**
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
