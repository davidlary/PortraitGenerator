#!/usr/bin/env python3
"""Generate comprehensive test portraits for all subjects from Examples directory.

This script generates ALL 4 portrait styles (BW, Sepia, Color, Painting) for all 20
historical figures from the Examples directory using Gemini 3 Pro Image (Nano Banana Pro).

Usage:
    export GOOGLE_API_KEY="your_gemini_api_key"
    python generate_comprehensive_tests.py
"""

import os
import sys
from pathlib import Path
import time

# Check for API key
if not os.getenv("GOOGLE_API_KEY"):
    print("❌ Error: GOOGLE_API_KEY environment variable not set")
    print("\nPlease set your Google Gemini API key:")
    print("  export GOOGLE_API_KEY='your_api_key_here'")
    sys.exit(1)

# Import after API key check
try:
    from portrait_generator import PortraitClient
except ImportError:
    print("❌ Error: portrait_generator not installed")
    print("\nInstall it with:")
    print("  pip install -e .")
    sys.exit(1)


# All 20 subjects from Examples directory
TEST_SUBJECTS = [
    "Alexey Chervonenkis",
    "Allen Newell",
    "Arthur Lee Samuel",
    "Ashish Vaswani",
    "Augustus De Morgan",
    "Claude Shannon",
    "David Rumelhart",
    "Donald Hebb",
    "Frank Rosenblatt",
    "Geoffrey Hinton",
    "George Boole",
    "Herbert Simon",
    "Ian Goodfellow",
    "J.C. Shaw",
    "Thomas Bayes",
    "Tom Mitchell",
    "Vladimir Vapnik",
    "William of Ockham",
    "Yann LeCun",
    "Yoshua Bengio",
]

# All 4 styles as requested by user
ALL_STYLES = ["BW", "Sepia", "Color", "Painting"]


def main():
    """Generate comprehensive test portraits."""
    print("=" * 70)
    print("Portrait Generator v2.0.0 - Comprehensive Test Suite")
    print("Using Gemini 3 Pro Image (Nano Banana Pro)")
    print("ZERO TOLERANCE FOR MOCKED API CALLS - ALL REAL GENERATION")
    print("=" * 70)
    print()

    # Output directory
    output_dir = Path("./test_output_comprehensive")
    output_dir.mkdir(exist_ok=True)

    print(f"📁 Output directory: {output_dir.absolute()}")
    print(f"🎨 Generating portraits for {len(TEST_SUBJECTS)} subjects")
    print(f"   Each subject gets all 4 styles: {', '.join(ALL_STYLES)}")
    print(f"   Total images to generate: {len(TEST_SUBJECTS) * len(ALL_STYLES)}")
    print()

    # Initialize client
    print("🚀 Initializing Portrait Generator...")
    print("   Model: gemini-3-pro-image-preview (Nano Banana Pro)")
    print("   Features: Internal reasoning, Search grounding, Physics-aware synthesis")
    print()

    client = PortraitClient(output_dir=output_dir)

    # Generate portraits
    successful = 0
    failed = 0
    total_images = 0
    total_time = 0
    start_time = time.time()

    for i, subject in enumerate(TEST_SUBJECTS, 1):
        print("-" * 70)
        print(f"[{i}/{len(TEST_SUBJECTS)}] Generating: {subject}")
        print("-" * 70)

        try:
            subject_start = time.time()
            result = client.generate(
                subject,
                styles=ALL_STYLES  # All 4 styles
            )
            subject_time = time.time() - subject_start

            if result.success:
                successful += 1
                total_images += len(result.files)
                total_time += subject_time

                print(f"✅ SUCCESS!")
                print(f"   Generated: {len(result.files)} portraits")
                print(f"   Time: {subject_time:.1f}s")
                print()
                print("   Files created:")
                for style, filepath in sorted(result.files.items()):
                    if os.path.exists(filepath):
                        size = os.path.getsize(filepath)
                        print(f"      {style:10} → {filepath} ({size:,} bytes)")
                print()

                if result.evaluation:
                    print("   Quality Scores:")
                    for style, eval_result in sorted(result.evaluation.items()):
                        print(f"      {style:10} → {eval_result.overall_score:.2f}")
                    print()

            else:
                failed += 1
                print(f"❌ FAILED!")
                print(f"   Errors: {', '.join(result.errors)}")
                print()

        except Exception as e:
            failed += 1
            print(f"❌ EXCEPTION: {str(e)}")
            print()

        print()

    elapsed_time = time.time() - start_time

    # Summary
    print("=" * 70)
    print("COMPREHENSIVE TEST GENERATION COMPLETE")
    print("=" * 70)
    print(f"✅ Successful: {successful}/{len(TEST_SUBJECTS)} subjects")
    print(f"❌ Failed: {failed}/{len(TEST_SUBJECTS)} subjects")
    print(f"📁 Output: {output_dir.absolute()}")
    print()
    print(f"Total images generated: {total_images}")
    print(f"Total time: {elapsed_time/60:.1f} minutes")
    if total_images > 0:
        print(f"Average time per image: {total_time/total_images:.1f}s")
    print()

    # Create gallery
    print("Creating HTML gallery...")
    create_gallery(output_dir)

    print()
    print("🎉 All test images generated with REAL API calls!")
    print("   Zero mocking - all images are genuine Gemini 3 Pro generations")


def create_gallery(output_dir: Path):
    """Create HTML gallery of generated images."""
    images = sorted(output_dir.glob("*.png"))

    if not images:
        return

    html = """<!DOCTYPE html>
<html>
<head>
    <title>Portrait Generator v2.0.0 - Comprehensive Test Gallery</title>
    <style>
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            max-width: 1800px;
            margin: 40px auto;
            background: #f5f5f5;
            padding: 20px;
        }
        h1 {
            text-align: center;
            color: #333;
            margin-bottom: 10px;
        }
        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 40px;
            font-size: 14px;
        }
        .gallery {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 30px;
        }
        .portrait {
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            text-align: center;
        }
        img {
            width: 100%;
            height: auto;
            border-radius: 4px;
            margin-bottom: 10px;
        }
        h3 {
            margin: 10px 0;
            font-size: 16px;
            color: #333;
        }
        .style {
            font-size: 12px;
            color: #888;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .footer {
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #888;
            font-size: 12px;
        }
        .stats {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
            text-align: center;
        }
    </style>
</head>
<body>
    <h1>Portrait Generator v2.0.0 - Comprehensive Test Gallery</h1>
    <div class="subtitle">All images generated with Gemini 3 Pro Image (Nano Banana Pro) - Zero Mocking</div>

    <div class="stats">
        <strong>{total_images}</strong> images generated<br>
        <strong>{total_subjects}</strong> subjects × <strong>4 styles</strong> each<br>
        (BW, Sepia, Color, Photorealistic Painting)
    </div>

    <div class="gallery">
""".format(total_images=len(images), total_subjects=len(TEST_SUBJECTS))

    for img in images:
        # Extract subject and style from filename
        parts = img.stem.split("_")
        subject = " ".join(parts[:-1]) if len(parts) > 1 else img.stem
        style = parts[-1] if len(parts) > 1 else "Unknown"

        html += f"""
        <div class="portrait">
            <img src="{img.name}" alt="{subject} - {style}">
            <h3>{subject}</h3>
            <div class="style">{style}</div>
        </div>
"""

    html += """
    </div>
    <div class="footer">
        Generated by Portrait Generator v2.0.0<br>
        Using Google Gemini 3 Pro Image (Nano Banana Pro)<br>
        Advanced features: Internal reasoning • Search grounding • Physics-aware synthesis • Native text rendering
    </div>
</body>
</html>
"""

    gallery_file = output_dir / "gallery.html"
    gallery_file.write_text(html, encoding="utf-8")
    print(f"✅ Gallery created: {gallery_file}")


if __name__ == "__main__":
    main()
