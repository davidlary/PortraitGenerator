# API Key Issue - RESOLVED

## 🔍 Problem Identified

Your API key has **TWO issues**:

### Issue 1: Wrong Format ❌
```bash
# Current (WRONG):
GOOGLE_API_KEY=google_api_key: AIzaSyC0h2RlxkEtHRYsfRbXCtCl_BArMBNvTzE

# Should be (CORRECT):
GOOGLE_API_KEY=AIzaSyC0h2RlxkEtHRYsfRbXCtCl_BArMBNvTzE
```

The prefix `google_api_key:` should NOT be there!

### Issue 2: Key is EXPIRED 🕐
```
Error: API key expired. Please renew the API key.
```

Even after fixing the format, the key is expired and needs to be renewed.

---

## ✅ Solution

### Step 1: Get a NEW API Key

1. Go to: https://makersuite.google.com/app/apikey
2. Click **"Create API Key"** (or renew existing)
3. Copy the NEW key (should start with `AIza...`)

### Step 2: Set it CORRECTLY

```bash
# Remove the old expired key
unset GOOGLE_API_KEY

# Set the NEW key (NO PREFIX!)
export GOOGLE_API_KEY="AIzaSy..."  # Your actual new key here
```

**IMPORTANT:** The key should be **just the key**, nothing else:
- ✅ Correct: `AIzaSyC0h2RlxkEt...`
- ❌ Wrong: `google_api_key: AIzaSyC0h2RlxkEt...`
- ❌ Wrong: `google_api_key:AIzaSyC0h2RlxkEt...`

### Step 3: Verify it Works

```bash
python3 << 'EOF'
import os
import google.genai as genai

api_key = os.getenv('GOOGLE_API_KEY')
print(f"Testing key: {api_key[:10]}...")

client = genai.Client(api_key=api_key)
response = client.models.generate_content(
    model='gemini-2.0-flash-exp',
    contents='Say "API works!"'
)
print(f"✅ SUCCESS: {response.text}")
EOF
```

If you see "✅ SUCCESS: API works!" then your key is valid!

### Step 4: Generate Test Images

```bash
python generate_test_portraits.py
```

This will create:
- 12 portrait images (3 subjects × 4 styles)
- All with correct naming: `FirstNameLastName_StyleName.png`
- Plus prompt markdown files
- HTML gallery to view all

---

## 🔐 Security Tip

**For permanent setup**, create a `.env` file:

```bash
# Create .env file with CORRECT format
cat > .env << 'EOF'
GOOGLE_API_KEY=AIzaSyYOUR_NEW_KEY_HERE
OUTPUT_DIR=./output
GEMINI_MODEL=gemini-3-pro-image-preview
EOF

# Verify format
cat .env
```

The `.gitignore` already excludes `.env` so it won't be committed.

---

## 📋 Quick Checklist

- [ ] Get NEW API key from makersuite.google.com
- [ ] Remove old expired key: `unset GOOGLE_API_KEY`
- [ ] Set new key WITHOUT prefix: `export GOOGLE_API_KEY="AIza..."`
- [ ] Test with verification script above
- [ ] Generate images: `python generate_test_portraits.py`
- [ ] View results: `open test_output/gallery.html`

---

## 🎨 What You'll Get

Once the key is set correctly:

```
test_output/
├── AlanTuring_BW.png               ✅ Black & White
├── AlanTuring_Sepia.png            ✅ Sepia tone
├── AlanTuring_Color.png            ✅ Full color
├── AlanTuring_Painting.png         ✅ Photorealistic painting
├── AlanTuring_BW_prompt.md         ✅ Prompt for BW
├── AlanTuring_Sepia_prompt.md      ✅ Prompt for Sepia
├── AlanTuring_Color_prompt.md      ✅ Prompt for Color
├── AlanTuring_Painting_prompt.md   ✅ Prompt for Painting
├── ... (same for Ada Lovelace and Claude Shannon)
└── gallery.html                    ✅ View all images
```

**Total: 12 images + 12 prompts + 1 gallery = 25 files**

---

## ⏱️ Generation Time

- Per image: ~60-90 seconds
- Total for 12 images: ~15-20 minutes
- With progress updates in real-time

---

## 💰 Cost

- ~6-8 API calls per subject
- ~20-24 total calls for 3 subjects
- Estimated: $0.50 - $2.00

---

**Ready?** Get your new API key and let's generate those test images! 🚀
