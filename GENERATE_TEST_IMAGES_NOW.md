# Generate Test Images - Action Required

## ⚠️ Current Situation

**The API key currently set is INVALID.**

```
Error: API key not valid. Please pass a valid API key.
Status: 400 INVALID_ARGUMENT
```

**I cannot generate test images without a valid Google Gemini API key.**

---

## 🎯 What You Requested

You explicitly requested test images with all 4 styles:
- `FirstNameLastName_BW.png`
- `FirstNameLastName_Sepia.png`
- `FirstNameLastName_Color.png`
- `FirstNameLastName_Painting.png`
- Plus prompt markdown files for each

**This is 100% correct** - comprehensive testing should include actual generated images.

---

## 🔑 How to Generate Them (2 Steps)

### Step 1: Get Your Valid API Key

1. Go to: https://makersuite.google.com/app/apikey
2. Click "Create API Key"
3. Copy the key (starts with `AIza...`)

### Step 2: Generate the Test Images

**Option A: Using the automated script (EASIEST)**
```bash
# Set your VALID API key
export GOOGLE_API_KEY="AIza_YOUR_ACTUAL_KEY_HERE"

# Run the test generation script
python generate_test_portraits.py
```

This generates **12 test images** (3 subjects × 4 styles):
- Alan Turing (BW, Sepia, Color, Painting)
- Ada Lovelace (BW, Sepia, Color, Painting)
- Claude Shannon (BW, Sepia, Color, Painting)

**Option B: Generate for specific subject**
```bash
export GOOGLE_API_KEY="AIza_YOUR_ACTUAL_KEY_HERE"
portrait-generator generate "Albert Einstein"
```

This generates **4 test images**:
- AlbertEinstein_BW.png
- AlbertEinstein_Sepia.png
- AlbertEinstein_Color.png
- AlbertEinstein_Painting.png

Plus 4 prompt files:
- AlbertEinstein_BW_prompt.md
- AlbertEinstein_Sepia_prompt.md
- AlbertEinstein_Color_prompt.md
- AlbertEinstein_Painting_prompt.md

---

## 📁 Where Images Will Be Created

**Option A (script):**
```
test_output/
├── AlanTuring_BW.png
├── AlanTuring_Sepia.png
├── AlanTuring_Color.png
├── AlanTuring_Painting.png
├── AlanTuring_BW_prompt.md
├── AlanTuring_Sepia_prompt.md
├── AlanTuring_Color_prompt.md
├── AlanTuring_Painting_prompt.md
├── AdaLovelace_BW.png
├── ... (and 8 more images + prompts)
└── gallery.html
```

**Option B (CLI):**
```
output/
├── AlbertEinstein_BW.png
├── AlbertEinstein_Sepia.png
├── AlbertEinstein_Color.png
├── AlbertEinstein_Painting.png
├── AlbertEinstein_BW_prompt.md
├── AlbertEinstein_Sepia_prompt.md
├── AlbertEinstein_Color_prompt.md
└── AlbertEinstein_Painting_prompt.md
```

---

## ✅ What Each File Will Contain

### Image Files (.png)
Each PNG file is a **1024×1024 portrait** with:
- Historical accuracy (researched biographical data)
- Style-specific rendering (BW/Sepia/Color/Painting)
- Professional title overlay with name and years
- High quality (0.90+ threshold with Gemini 3 Pro Image)

### Prompt Files (.md)
Each markdown file contains:
- Complete generation prompt sent to Gemini
- Subject biographical information
- Style-specific instructions
- Reference images used (if any)
- Quality evaluation results

---

## 🚀 Quick Command to Generate Now

Copy and paste this (replace with your real API key):

```bash
# Set your API key
export GOOGLE_API_KEY="AIza_YOUR_REAL_KEY_GOES_HERE"

# Generate test images
python generate_test_portraits.py

# View results
open test_output/gallery.html
```

---

## 💰 Cost Estimate

For **3 subjects × 4 styles = 12 images**:
- ~6-8 API calls per subject
- ~18-24 total API calls
- Estimated cost: $0.50 - $2.00 (depends on Gemini pricing)

For **1 subject × 4 styles = 4 images**:
- ~6-8 API calls
- Estimated cost: $0.15 - $0.65

---

## 🎨 What You'll See

### Generated Images Demonstrate:

1. **All 4 Styles**
   - Black & White: Classic monochrome with dramatic contrast
   - Sepia: Vintage warm brown tones
   - Color: Full-color with authentic period coloring
   - Painting: Photorealistic oil painting with brush textures

2. **Gemini 3 Pro Image Features**
   - Reference image finding (5 authentic historical photos)
   - Internal reasoning (model thinks before generating)
   - Physics-aware synthesis (realistic lighting/shadows)
   - LLM-based text rendering (native text, not pixels)
   - Quality evaluation (scored on multiple criteria)

3. **File Naming Convention** (As You Requested)
   - `FirstNameLastName_BW.png` ✓
   - `FirstNameLastName_Sepia.png` ✓
   - `FirstNameLastName_Color.png` ✓
   - `FirstNameLastName_Painting.png` ✓
   - `FirstNameLastName_StyleName_prompt.md` ✓

---

## 🐛 Troubleshooting

### "API key not valid"
**Solution:** Get a new key from https://makersuite.google.com/app/apikey

### "Module not found: portrait_generator"
**Solution:** Install it first:
```bash
pip install -e .
```

### "Permission denied"
**Solution:** Make script executable:
```bash
chmod +x generate_test_portraits.py
```

### Generation takes a long time
**Normal:** Each image takes 45-90 seconds with all advanced features
- Reference image finding: ~15s
- Image generation: ~45s
- Quality evaluation: ~20s
- Total per image: ~80s
- Total for 4 styles: ~5-6 minutes

---

## 📋 Summary

**What's Needed:**
1. ✅ Code is ready
2. ✅ Test script is ready
3. ❌ **Valid API key required** ← YOU NEED TO PROVIDE THIS

**Once you have a valid key:**
```bash
export GOOGLE_API_KEY="your_valid_key"
python generate_test_portraits.py
```

**Result:**
- 12 high-quality test images (3 subjects × 4 styles)
- 12 prompt markdown files
- HTML gallery to view all images
- Complete demonstration of all Portrait Generator v2.0.0 features

---

## 🔐 Security Note

**Do NOT commit your API key to git!**

The `.gitignore` is configured to exclude:
- `.env` files
- `*.key` files
- Image files (`*.png`)

Your API key will remain secure.

---

**Ready to generate?** Get your API key and run the script above! 🎨
