# Generating Test Images for Portrait Generator v2.0.0

## Current Status

**❌ No test images with all 4 styles were generated during testing** because:
1. Unit tests (370 tests) use **mocked API calls** - no real image generation
2. E2E tests require a **valid GOOGLE_API_KEY** - they were skipped
3. `.gitignore` excludes `*.png` files from being committed to git

**✅ Pre-existing examples in `Examples/`:** 20 portraits (but only one style each, not all 4)

---

## How to Generate Test Images with All 4 Styles

### Prerequisites

1. **Set your Google Gemini API key:**
   ```bash
   export GOOGLE_API_KEY="your_gemini_api_key_here"
   ```

2. **Install Portrait Generator:**
   ```bash
   pip install -e .
   ```

---

## Method 1: Generate Test Images via CLI

### Single Subject - All 4 Styles

```bash
# Generate all 4 styles (BW, Sepia, Color, Painting)
portrait-generator generate "Albert Einstein"

# Output will be in ./output/ directory:
# - AlbertEinstein_BW.png
# - AlbertEinstein_Sepia.png
# - AlbertEinstein_Color.png
# - AlbertEinstein_Painting.png
```

### Multiple Subjects for Testing

```bash
# Generate portraits for multiple test subjects
portrait-generator batch "Alan Turing" "Ada Lovelace" "Marie Curie"

# Each subject gets 4 styles:
# - AlanTuring_BW.png, AlanTuring_Sepia.png, etc.
# - AdaLovelace_BW.png, AdaLovelace_Sepia.png, etc.
# - MarieCurie_BW.png, MarieCurie_Sepia.png, etc.
```

### Specific Styles Only

```bash
# Generate only BW and Sepia styles
portrait-generator generate "Claude Shannon" --styles BW Sepia
```

---

## Method 2: Generate via Python API

### Example Script

Create `generate_test_images.py`:

```python
from portrait_generator import PortraitClient
import os

# Initialize client
client = PortraitClient(
    api_key=os.getenv("GOOGLE_API_KEY"),
    output_dir="./test_output"
)

# Test subjects
test_subjects = [
    "Albert Einstein",
    "Marie Curie",
    "Alan Turing",
    "Ada Lovelace"
]

# Generate all 4 styles for each subject
for subject in test_subjects:
    print(f"\nGenerating portraits for {subject}...")

    result = client.generate(
        subject,
        styles=["BW", "Sepia", "Color", "Painting"]
    )

    if result.success:
        print(f"✅ Success! Generated {len(result.files)} portraits:")
        for style, filepath in result.files.items():
            print(f"   {style}: {filepath}")
    else:
        print(f"❌ Failed: {result.errors}")

print("\n✅ All test images generated!")
print(f"Output directory: {client.generator.output_dir}")
```

Run it:
```bash
python generate_test_images.py
```

---

## Method 3: Run E2E Tests (Generates Images)

The E2E tests will generate real images and test all functionality:

```bash
# Run all E2E tests (requires API key)
export GOOGLE_API_KEY="your_key_here"
pytest tests/integration/test_e2e_real_api.py -m e2e -v

# Run specific test for all 4 styles
pytest tests/integration/test_e2e_real_api.py::TestE2ERealAPI::test_generate_single_portrait_all_styles -v
```

**Note:** E2E tests use temporary directories but you can check output during execution.

---

## Expected Output Structure

After generation, your `output/` directory should contain:

```
output/
├── AlbertEinstein_BW.png
├── AlbertEinstein_Sepia.png
├── AlbertEinstein_Color.png
├── AlbertEinstein_Painting.png
├── AlbertEinstein_BW_prompt.md
├── AlbertEinstein_Sepia_prompt.md
├── AlbertEinstein_Color_prompt.md
├── AlbertEinstein_Painting_prompt.md
├── MarieCurie_BW.png
├── MarieCurie_Sepia.png
├── MarieCurie_Color.png
├── MarieCurie_Painting.png
└── ...
```

Each style generates:
- **`.png`** - The portrait image
- **`_prompt.md`** - The prompt used for generation

---

## Viewing Generated Images

### Option 1: Open in Finder (macOS)
```bash
open output/
```

### Option 2: View specific image
```bash
open output/AlbertEinstein_BW.png
```

### Option 3: View all images
```bash
ls -lh output/*.png
```

---

## Gemini 3 Pro Image Features in Generated Images

When using **gemini-3-pro-image-preview** (v2.0.0 default), you'll see:

### 1. **Reference Images** (Behind the scenes)
The system finds up to 5 authentic historical photos before generation.

### 2. **Physics-Aware Synthesis**
- Realistic lighting and shadows
- Correct proportions and anatomy
- Authentic material properties

### 3. **LLM-Based Text Rendering**
Title overlays use native text rendering (not pixel drawing) for better quality.

### 4. **Internal Reasoning**
The model thinks through the composition before finalizing (up to 3 iterations).

### 5. **Quality Evaluation**
Each image is evaluated with:
- Technical quality score
- Historical accuracy score
- Style adherence score
- Overall quality score (threshold: 0.90)

---

## Creating a Test Gallery

Create a simple HTML viewer for all generated images:

```python
from pathlib import Path

output_dir = Path("output")
images = sorted(output_dir.glob("*.png"))

html = """
<!DOCTYPE html>
<html>
<head>
    <title>Portrait Generator Test Gallery</title>
    <style>
        body { font-family: Arial; max-width: 1200px; margin: 40px auto; }
        .portrait { display: inline-block; margin: 20px; text-align: center; }
        img { max-width: 300px; border: 2px solid #ccc; }
        h3 { margin: 10px 0; }
    </style>
</head>
<body>
    <h1>Portrait Generator v2.0.0 - Test Gallery</h1>
"""

for img in images:
    html += f"""
    <div class="portrait">
        <img src="{img.name}" alt="{img.stem}">
        <h3>{img.stem}</h3>
    </div>
    """

html += """
</body>
</html>
"""

gallery_file = output_dir / "gallery.html"
gallery_file.write_text(html)
print(f"✅ Gallery created: {gallery_file}")
print(f"   Open in browser: open {gallery_file}")
```

---

## Quick Test Script (All-in-One)

Save as `quick_test.py`:

```python
#!/usr/bin/env python3
"""Quick test to generate sample portraits."""

import os
from portrait_generator import PortraitClient

# Check API key
if not os.getenv("GOOGLE_API_KEY"):
    print("❌ Error: Set GOOGLE_API_KEY environment variable")
    print("   export GOOGLE_API_KEY='your_key_here'")
    exit(1)

# Initialize client
print("🎨 Initializing Portrait Generator v2.0.0...")
client = PortraitClient(output_dir="./test_output")

# Generate one subject with all 4 styles
subject = "Albert Einstein"
print(f"\n📸 Generating all 4 styles for {subject}...")

result = client.generate(subject)

if result.success:
    print(f"\n✅ SUCCESS! Generated {len(result.files)} portraits:")
    print(f"\n📁 Output directory: test_output/")
    for style, filepath in result.files.items():
        print(f"   {style:10} → {filepath}")

    print(f"\n⏱️  Generation time: {result.generation_time_seconds:.1f}s")
    print(f"📊 Quality scores:")
    for style, eval_result in result.evaluation.items():
        print(f"   {style:10} → {eval_result.overall_score:.2f}")

    print(f"\n🖼️  View images: open test_output/")
else:
    print(f"\n❌ FAILED: {result.errors}")
```

Run it:
```bash
chmod +x quick_test.py
python quick_test.py
```

---

## Troubleshooting

### "API key not valid"
```bash
# Check your API key is set
echo $GOOGLE_API_KEY

# Get a new key from:
# https://makersuite.google.com/app/apikey
```

### "Module not found"
```bash
# Install in development mode
pip install -e .
```

### "Permission denied"
```bash
# Make output directory writable
chmod 755 output/
```

### Images in .gitignore
Images are excluded from git by design (large files). To commit examples:
```bash
# Move to Examples/ directory (not excluded)
cp output/AlbertEinstein_BW.png Examples/
git add Examples/AlbertEinstein_BW.png
```

---

## Cost Considerations

**Gemini 3 Pro Image Generation Costs:**
- Each subject × 4 styles = 4 API calls
- Advanced features (reference images, fact-checking) = additional API calls
- Estimate: ~6-8 API calls per subject

**For testing, start with 1-2 subjects** to verify everything works before generating many portraits.

---

## Next Steps

1. **Generate a few test portraits:**
   ```bash
   export GOOGLE_API_KEY="your_key"
   portrait-generator generate "Albert Einstein"
   ```

2. **Verify all 4 styles are created:**
   ```bash
   ls -lh output/AlbertEinstein_*.png
   ```

3. **Check quality:**
   - Open images to visually inspect
   - Review prompt files for historical accuracy
   - Check evaluation scores

4. **Generate more if satisfied:**
   ```bash
   portrait-generator batch "Marie Curie" "Alan Turing" "Ada Lovelace"
   ```

---

## Support

For issues with generation:
- Check logs: Portrait Generator uses detailed logging
- Verify API key is valid
- Ensure internet connection for Google Search grounding
- See documentation: `docs/GEMINI_3_PRO_IMAGE.md`

**Happy portrait generating!** 🎨
