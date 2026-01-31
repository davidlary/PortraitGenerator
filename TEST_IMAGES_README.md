# Test Images for Portrait Generator v2.0.0

## 📸 Where Are The Test Images?

### Current Status

**❌ No test images with all 4 styles were generated yet** because:

1. **Unit Tests (370 tests)** - Use mocked API calls for fast testing
   - No real API calls = No real images generated
   - Tests verify code logic, not actual image generation

2. **E2E Tests** - Would generate real images BUT require API key
   - These tests were **skipped** (no GOOGLE_API_KEY set)
   - Would generate images in temporary directories

3. **Git Exclusions** - `.gitignore` excludes image files
   - `*.png` files are not committed to repository
   - Keeps repository size small

### What EXISTS

✅ **Pre-existing Examples:** 20 portraits in `Examples/` directory
- These are **single-style** examples (one portrait each)
- Created during v1.0.0 development
- Not showing all 4 styles per subject

```
Examples/
├── AlbertEinstein.jpg        (1 style)
├── AlanTuring.jpg             (1 style)
├── AdaLovelace.jpg            (1 style)
└── ... (17 more)
```

---

## 🎨 How to Generate Test Images with All 4 Styles

You have **3 easy options:**

### Option 1: Run the Test Generation Script (EASIEST)

We created a ready-to-use script for you:

```bash
# 1. Set your API key
export GOOGLE_API_KEY="your_gemini_api_key_here"

# 2. Run the script
python generate_test_portraits.py
```

**What it does:**
- Generates 3 test subjects (Alan Turing, Ada Lovelace, Claude Shannon)
- Each subject gets **all 4 styles**: BW, Sepia, Color, Painting
- Total: **12 test images**
- Creates HTML gallery for easy viewing
- Shows quality scores and generation time

**Output:**
```
test_output/
├── AlanTuring_BW.png
├── AlanTuring_Sepia.png
├── AlanTuring_Color.png
├── AlanTuring_Painting.png
├── AdaLovelace_BW.png
├── AdaLovelace_Sepia.png
├── AdaLovelace_Color.png
├── AdaLovelace_Painting.png
├── ClaudeShannon_BW.png
├── ClaudeShannon_Sepia.png
├── ClaudeShannon_Color.png
├── ClaudeShannon_Painting.png
└── gallery.html              ← Open this in browser!
```

---

### Option 2: Use the CLI

```bash
# Generate one subject with all 4 styles
portrait-generator generate "Albert Einstein"

# Output in ./output/ directory:
# - AlbertEinstein_BW.png
# - AlbertEinstein_Sepia.png
# - AlbertEinstein_Color.png
# - AlbertEinstein_Painting.png
```

---

### Option 3: Use Python API

```python
from portrait_generator import PortraitClient

client = PortraitClient()
result = client.generate("Albert Einstein")

# All 4 styles generated
print(result.files)
# {
#   'BW': 'output/AlbertEinstein_BW.png',
#   'Sepia': 'output/AlbertEinstein_Sepia.png',
#   'Color': 'output/AlbertEinstein_Color.png',
#   'Painting': 'output/AlbertEinstein_Painting.png'
# }
```

---

## 🚀 Quick Start (30 seconds)

```bash
# 1. Get your API key from:
#    https://makersuite.google.com/app/apikey

# 2. Set it
export GOOGLE_API_KEY="AIza..."

# 3. Generate test images
python generate_test_portraits.py

# 4. View the gallery
open test_output/gallery.html
```

---

## 🎯 What You'll See in Generated Images

### Gemini 3 Pro Image Features (v2.0.0)

Each generated portrait demonstrates:

1. **Reference Image Finding**
   - System finds 5 authentic historical photos BEFORE rendering
   - Uses Google Search grounding for authenticity

2. **Internal Reasoning**
   - Model "thinks" before generating (up to 3 iterations)
   - Self-corrects for accuracy and quality

3. **Physics-Aware Synthesis**
   - Realistic lighting and shadows
   - Correct proportions and anatomy
   - Authentic material properties

4. **LLM-Based Text Rendering**
   - Title overlays use native text rendering
   - Not pixel-by-pixel drawing = better quality

5. **Quality Evaluation**
   - Each image scored on multiple criteria:
     - Technical quality (≥ 0.90)
     - Historical accuracy (≥ 0.85)
     - Style adherence
     - Overall quality

### The 4 Portrait Styles

1. **BW (Black & White)**
   - Classic monochrome photography
   - Rich tonal range
   - Enhanced contrast with dramatic lighting

2. **Sepia**
   - Vintage photography aesthetic
   - Warm brown tones
   - Aged historical appearance

3. **Color**
   - Full-color photograph
   - Authentic period coloring
   - Natural skin tones and lighting

4. **Painting**
   - Photorealistic oil painting style
   - Traditional portrait painting aesthetic
   - Brush stroke textures

---

## 📊 Generation Performance

With Gemini 3 Pro Image, expect:

- **First attempt success**: 85%+ (target)
- **Second attempt success**: 95%+ (target)
- **Generation time per image**: ~45-60 seconds
- **With reference images**: ~60-90 seconds
- **Quality threshold**: 0.90 (up from 0.80 in v1.0)

---

## 💰 Cost Considerations

**API Calls per Subject:**
- 1 biographical research call
- 1 reference image search (if enabled)
- 4 image generation calls (one per style)
- 4 quality evaluation calls
- **Total**: ~6-8 API calls per subject

**For initial testing:**
- Start with 1-2 subjects to verify setup
- Then generate more once satisfied

---

## 📁 Directory Structure

After running `generate_test_portraits.py`:

```
PortraitGenerator/
├── test_output/              ← Generated images here
│   ├── AlanTuring_BW.png
│   ├── AlanTuring_Sepia.png
│   ├── AlanTuring_Color.png
│   ├── AlanTuring_Painting.png
│   ├── ... (8 more images)
│   └── gallery.html          ← View all images
├── Examples/                 ← Pre-existing examples
│   └── ... (20 single-style portraits)
├── output/                   ← Default CLI output
│   └── (images you generate)
└── generate_test_portraits.py ← Test generation script
```

---

## 🔍 Viewing Generated Images

### View Gallery (Recommended)
```bash
open test_output/gallery.html
```

### View Individual Image
```bash
open test_output/AlanTuring_BW.png
```

### View All Images
```bash
ls -lh test_output/*.png
```

### View in Finder
```bash
open test_output/
```

---

## 🐛 Troubleshooting

### "API key not valid"
```bash
# Check if set
echo $GOOGLE_API_KEY

# Should output your key starting with "AIza..."
# If empty, set it:
export GOOGLE_API_KEY="AIza..."
```

### "Module not found"
```bash
# Install Portrait Generator
pip install -e .
```

### "No images generated"
Check the error messages - likely one of:
- Invalid API key
- Network connectivity issue
- Rate limiting (wait a minute and retry)

### Images not appearing
```bash
# Check if they were created
ls -la test_output/

# Check permissions
chmod 755 test_output/
```

---

## 📚 Additional Resources

### Documentation
- **Full guide**: `GENERATE_TEST_IMAGES.md` (comprehensive)
- **Gemini 3 features**: `docs/GEMINI_3_PRO_IMAGE.md`
- **Publishing**: `PUBLISHING_INSTRUCTIONS.md`
- **Deployment**: `DEPLOYMENT_COMPLETE.md`

### Quick Commands
```bash
# Generate single subject
portrait-generator generate "Subject Name"

# Generate multiple subjects
portrait-generator batch "Person 1" "Person 2" "Person 3"

# Generate specific styles only
portrait-generator generate "Subject" --styles BW Sepia

# Check what exists
portrait-generator status "Subject Name"

# Run test generation script
python generate_test_portraits.py
```

---

## ✨ Summary

**To see all 4 portrait styles with Gemini 3 Pro Image features:**

1. Set your `GOOGLE_API_KEY`
2. Run: `python generate_test_portraits.py`
3. Open: `test_output/gallery.html`

**That's it!** You'll see 12 high-quality portraits demonstrating all advanced features.

---

**Questions?** See `GENERATE_TEST_IMAGES.md` for more details.
