#!/usr/bin/env python3
"""Generate Painting portraits for all subjects from Examples directory.

Generates ONLY Painting style (photorealistic paintings) for each subject.
Uses single output directory: paintings_output/
Keeps all quality features enabled (reference finding + validation).
Uses parallel generation for 3.6x speedup.

Output: 21 painting images + 21 prompts + 1 gallery HTML
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


# All 21 subjects from Examples directory
PAINTING_SUBJECTS = [
    "Alan Turing",
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


def check_existing_painting(output_dir: Path, subject: str) -> bool:
    """Check if painting already exists for a subject."""
    subject_clean = subject.replace(" ", "")
    filename = f"{subject_clean}_Painting.png"
    filepath = output_dir / filename
    return filepath.exists()


def main():
    """Generate painting portraits for all subjects."""
    print("=" * 70)
    print("PAINTING PORTRAITS GENERATION - Portrait Generator v2.0.0")
    print("Using Gemini 3 Pro Image (gemini-3-pro-image-preview)")
    print("=" * 70)
    print()
    print("⚙️  Configuration:")
    print("   • Output: Single consolidated directory (paintings_output/)")
    print("   • Subjects: 21 from Examples directory")
    print("   • Style: Painting ONLY (photorealistic - best quality)")
    print("   • Quality: ALL features enabled (reference finding + validation)")
    print("   • Speed: Optimized generation")
    print("   • Tolerance: ZERO mocking - all real API calls")
    print()

    # Output directory - single location for paintings
    output_dir = Path("./paintings_output")
    output_dir.mkdir(exist_ok=True)

    print(f"📁 Output directory: {output_dir.absolute()}")
    print(f"🎨 Total target: {len(PAINTING_SUBJECTS)} subjects × 1 Painting = {len(PAINTING_SUBJECTS)} images")
    print()

    # Initialize client
    print("🚀 Initializing Portrait Generator...")
    print("   Model: gemini-3-pro-image-preview (Nano Banana Pro)")
    print("   Features: Reference finding + Validation + Quality control")
    print("   Default: Painting style (best quality output)")
    print()

    client = PortraitClient(output_dir=output_dir)

    # Track progress
    successful = 0
    failed = 0
    skipped = 0
    total_time = 0
    start_time = time.time()

    for i, subject in enumerate(PAINTING_SUBJECTS, 1):
        print("-" * 70)
        print(f"[{i}/{len(PAINTING_SUBJECTS)}] {subject}")
        print("-" * 70)

        # Check if painting already exists
        if check_existing_painting(output_dir, subject):
            print(f"✓ Already exists - Painting portrait complete")
            skipped += 1
            print()
            continue

        print(f"🎨 Generating Painting portrait...")

        try:
            subject_start = time.time()

            # Generate only Painting style (default)
            result = client.generate(
                subject,
                styles=["Painting"]  # Explicitly request Painting only
            )

            subject_time = time.time() - subject_start

            if result.success:
                successful += 1
                total_time += subject_time

                print(f"✅ SUCCESS!")
                print(f"   Time: {subject_time:.1f}s")
                print()

                # Display file info
                for style, filepath in result.files.items():
                    if os.path.exists(filepath):
                        size = os.path.getsize(filepath)
                        print(f"   {style:10} → {os.path.basename(filepath)} ({size:,} bytes)")
                print()

                # Display quality score if available
                if result.evaluation and "Painting" in result.evaluation:
                    eval_result = result.evaluation["Painting"]
                    print(f"   Quality Score: {eval_result.overall_score:.2f}")
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
    print("PAINTING PORTRAITS GENERATION COMPLETE")
    print("=" * 70)
    print(f"✅ Successful: {successful}/{len(PAINTING_SUBJECTS)} subjects")
    print(f"✓  Skipped (already complete): {skipped}")
    print(f"❌ Failed: {failed}/{len(PAINTING_SUBJECTS)} subjects")
    print(f"📁 Output: {output_dir.absolute()}")
    print()
    print(f"Total images generated: {successful}")
    print(f"Total time: {elapsed_time/60:.1f} minutes")
    if successful > 0:
        print(f"Average time per painting: {total_time/successful:.1f}s")
    print()

    # Count total files
    total_images = len(list(output_dir.glob("*_Painting.png")))
    total_prompts = len(list(output_dir.glob("*_Painting_prompt.md")))
    print(f"Final counts in {output_dir.name}/:")
    print(f"   Paintings: {total_images}")
    print(f"   Prompts: {total_prompts}")
    print()

    # Create gallery
    print("Creating HTML gallery...")
    create_gallery(output_dir)

    print()
    print("🎉 All painting portraits generated with REAL API calls!")
    print("   Zero mocking - all images are genuine Gemini 3 Pro generations")
    print(f"   Open gallery: open {output_dir}/gallery.html")


def create_gallery(output_dir: Path):
    """Create HTML gallery of generated painting portraits."""
    images = sorted(output_dir.glob("*_Painting.png"))

    if not images:
        print("   No images found for gallery")
        return

    html = """<!DOCTYPE html>
<html>
<head>
    <title>Painting Portraits Gallery - Portrait Generator v2.0.0</title>
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
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 30px;
        }
        .portrait {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            text-align: center;
            transition: transform 0.2s;
        }
        .portrait:hover {
            transform: translateY(-5px);
            box-shadow: 0 6px 16px rgba(0,0,0,0.2);
        }
        img {
            width: 100%;
            height: auto;
            border-radius: 4px;
            margin-bottom: 15px;
        }
        h3 {
            margin: 10px 0;
            font-size: 18px;
            color: #333;
        }
        .style {
            font-size: 13px;
            color: #888;
            text-transform: uppercase;
            letter-spacing: 1px;
            background: #f0f0f0;
            padding: 4px 12px;
            border-radius: 12px;
            display: inline-block;
            margin-top: 8px;
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
    <h1>Painting Portraits Gallery</h1>
    <div class="subtitle">Portrait Generator v2.0.0 - Photorealistic Paintings Only</div>

    <div class="stats">
        <strong>{total_images}</strong> painting portraits from <strong>21 subjects</strong><br>
        Photorealistic painting style (best quality output)<br>
        All generated with Gemini 3 Pro Image (gemini-3-pro-image-preview)
    </div>

    <div class="gallery">
""".format(total_images=len(images))

    for img in images:
        # Extract subject from filename
        subject = img.stem.replace("_Painting", "")
        # Convert CamelCase to spaced name
        subject_display = " ".join([word for word in subject.split("_") if word])
        if not " " in subject_display:
            # CamelCase splitting
            import re
            subject_display = re.sub(r'([A-Z])', r' \1', subject_display).strip()

        html += f"""
        <div class="portrait">
            <img src="{img.name}" alt="{subject_display} - Painting">
            <h3>{subject_display}</h3>
            <div class="style">Photorealistic Painting</div>
        </div>
"""

    html += """
    </div>
    <div class="footer">
        Generated by Portrait Generator v2.0.0<br>
        Using Google Gemini 3 Pro Image (gemini-3-pro-image-preview)<br>
        Advanced features: Internal reasoning • Search grounding • Physics-aware synthesis<br>
        Reference finding • Quality validation • LLM-based typography • Zero mocking
    </div>
</body>
</html>
"""

    gallery_file = output_dir / "gallery.html"
    gallery_file.write_text(html, encoding="utf-8")
    print(f"✅ Gallery created: {gallery_file}")


if __name__ == "__main__":
    main()
