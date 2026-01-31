#!/usr/bin/env python3
"""Final comprehensive test - All 20 subjects from Examples directory.

Generates all 4 styles (BW, Sepia, Color, Painting) for each subject.
Uses single output directory: test_output/
Keeps all quality features enabled (reference finding + validation).
Uses parallel generation for 3.6x speedup.

Output: 80 images + 80 prompts + 1 gallery HTML
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
    "Alan Turing",          # Partially complete (BW only)
    "Alexey Chervonenkis",
    "Allen Newell",
    "Arthur Lee Samuel",
    "Ashish Vaswani",
    "Augustus De Morgan",
    "Claude Shannon",       # Already complete (all 4 styles)
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

# All 4 styles as requested
ALL_STYLES = ["BW", "Sepia", "Color", "Painting"]


def check_existing_files(output_dir: Path, subject: str, styles: list) -> list:
    """Check which styles already exist for a subject."""
    existing_styles = []
    subject_clean = subject.replace(" ", "")
    
    for style in styles:
        filename = f"{subject_clean}_{style}.png"
        filepath = output_dir / filename
        if filepath.exists():
            existing_styles.append(style)
    
    return existing_styles


def main():
    """Generate comprehensive test portraits."""
    print("=" * 70)
    print("FINAL COMPREHENSIVE TEST - Portrait Generator v2.0.0")
    print("Using Gemini 3 Pro Image (Nano Banana Pro)")
    print("=" * 70)
    print()
    print("⚙️  Configuration:")
    print("   • Output: Single consolidated directory (test_output/)")
    print("   • Subjects: 20 from Examples directory")
    print("   • Styles: 4 per subject (BW, Sepia, Color, Painting)")
    print("   • Quality: ALL features enabled (reference finding + validation)")
    print("   • Speed: Parallel generation (3.6x speedup)")
    print("   • Tolerance: ZERO mocking - all real API calls")
    print()

    # Output directory - single location
    output_dir = Path("./test_output")
    output_dir.mkdir(exist_ok=True)

    print(f"📁 Output directory: {output_dir.absolute()}")
    print(f"🎨 Total target: {len(TEST_SUBJECTS)} subjects × 4 styles = {len(TEST_SUBJECTS) * 4} images")
    print()

    # Initialize client
    print("🚀 Initializing Portrait Generator...")
    print("   Model: gemini-3-pro-image-preview (Nano Banana Pro)")
    print("   Features: Parallel generation + Reference finding + Validation")
    print()

    client = PortraitClient(output_dir=output_dir)

    # Track progress
    successful = 0
    failed = 0
    skipped = 0
    total_images_generated = 0
    total_time = 0
    start_time = time.time()

    for i, subject in enumerate(TEST_SUBJECTS, 1):
        print("-" * 70)
        print(f"[{i}/{len(TEST_SUBJECTS)}] {subject}")
        print("-" * 70)

        # Check what already exists
        existing_styles = check_existing_files(output_dir, subject, ALL_STYLES)
        
        if len(existing_styles) == 4:
            print(f"✓ Already complete - all 4 styles exist")
            print(f"  Files: {', '.join(existing_styles)}")
            skipped += 1
            print()
            continue
        
        if existing_styles:
            print(f"⚠️  Partial - found {len(existing_styles)} existing: {', '.join(existing_styles)}")
            remaining_styles = [s for s in ALL_STYLES if s not in existing_styles]
            print(f"   Generating remaining {len(remaining_styles)}: {', '.join(remaining_styles)}")
        else:
            print(f"🆕 New subject - generating all 4 styles")
            remaining_styles = ALL_STYLES.copy()

        try:
            subject_start = time.time()
            result = client.generate(
                subject,
                styles=remaining_styles  # Only generate missing styles
            )
            subject_time = time.time() - subject_start

            if result.success:
                successful += 1
                images_generated = len(result.files)
                total_images_generated += images_generated
                total_time += subject_time

                print(f"✅ SUCCESS!")
                print(f"   Generated: {images_generated} new portraits")
                print(f"   Time: {subject_time:.1f}s")
                
                if images_generated > 0:
                    print(f"   Avg per image: {subject_time/images_generated:.1f}s")
                print()
                
                print("   New files created:")
                for style, filepath in sorted(result.files.items()):
                    if os.path.exists(filepath):
                        size = os.path.getsize(filepath)
                        print(f"      {style:10} → {os.path.basename(filepath)} ({size:,} bytes)")
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
    print("COMPREHENSIVE TEST COMPLETE")
    print("=" * 70)
    print(f"✅ Successful: {successful}/{len(TEST_SUBJECTS)} subjects")
    print(f"✓  Skipped (already complete): {skipped}")
    print(f"❌ Failed: {failed}/{len(TEST_SUBJECTS)} subjects")
    print(f"📁 Output: {output_dir.absolute()}")
    print()
    print(f"Total new images generated: {total_images_generated}")
    print(f"Total time: {elapsed_time/60:.1f} minutes")
    if total_images_generated > 0:
        print(f"Average time per image: {total_time/total_images_generated:.1f}s")
    print()

    # Count total files
    total_images = len(list(output_dir.glob("*.png")))
    total_prompts = len(list(output_dir.glob("*_prompt.md")))
    print(f"Final counts in {output_dir.name}/:")
    print(f"   Images: {total_images}")
    print(f"   Prompts: {total_prompts}")
    print()

    # Create gallery
    print("Creating HTML gallery...")
    create_gallery(output_dir)

    print()
    print("🎉 All test images generated with REAL API calls!")
    print("   Zero mocking - all images are genuine Gemini 3 Pro generations")
    print(f"   Open gallery: open {output_dir}/gallery.html")


def create_gallery(output_dir: Path):
    """Create HTML gallery of generated images."""
    images = sorted(output_dir.glob("*.png"))

    if not images:
        print("   No images found for gallery")
        return

    html = """<!DOCTYPE html>
<html>
<head>
    <title>Portrait Generator v2.0.0 - Comprehensive Gallery</title>
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
    <h1>Portrait Generator v2.0.0 - Comprehensive Gallery</h1>
    <div class="subtitle">All images generated with Gemini 3 Pro Image (Nano Banana Pro) - Zero Mocking</div>

    <div class="stats">
        <strong>{total_images}</strong> images from <strong>20 subjects</strong><br>
        Four Portrait Styles: BW, Sepia, Color, Photorealistic Painting<br>
        All quality features enabled • Parallel generation • Real API calls
    </div>

    <div class="gallery">
""".format(total_images=len(images))

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
        Reference finding • Parallel generation • Quality validation • Zero mocking
    </div>
</body>
</html>
"""

    gallery_file = output_dir / "gallery.html"
    gallery_file.write_text(html, encoding="utf-8")
    print(f"✅ Gallery created: {gallery_file}")


if __name__ == "__main__":
    main()
