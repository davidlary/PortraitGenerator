#!/usr/bin/env python3
"""Generate test portraits demonstrating all 4 styles with Gemini 3 Pro Image.

This script generates test portraits for Portrait Generator v2.0.0 to demonstrate:
- All 4 portrait styles (BW, Sepia, Color, Painting)
- Gemini 3 Pro Image advanced features
- Reference image finding
- Physics-aware synthesis
- LLM-based text rendering
- Internal reasoning and quality evaluation

Usage:
    export GOOGLE_API_KEY="your_gemini_api_key"
    python generate_test_portraits.py
"""

import os
import sys
from pathlib import Path

# Check for API key
if not os.getenv("GOOGLE_API_KEY"):
    print("❌ Error: GOOGLE_API_KEY environment variable not set")
    print("\nPlease set your Google Gemini API key:")
    print("  export GOOGLE_API_KEY='your_api_key_here'")
    print("\nGet your API key from:")
    print("  https://makersuite.google.com/app/apikey")
    sys.exit(1)

# Import after API key check
try:
    from portrait_generator import PortraitClient
except ImportError:
    print("❌ Error: portrait_generator not installed")
    print("\nInstall it with:")
    print("  pip install -e .")
    sys.exit(1)


def main():
    """Generate test portraits."""
    print("=" * 70)
    print("Portrait Generator v2.0.0 - Test Image Generation")
    print("Using Gemini 3 Pro Image (Nano Banana Pro)")
    print("=" * 70)
    print()

    # Test subjects - historical figures in AI/CS
    test_subjects = [
        "Alan Turing",      # Father of computer science
        "Ada Lovelace",     # First programmer
        "Claude Shannon",   # Information theory
    ]

    # Output directory
    output_dir = Path("./test_output")
    output_dir.mkdir(exist_ok=True)

    print(f"📁 Output directory: {output_dir.absolute()}")
    print(f"🎨 Generating portraits for {len(test_subjects)} subjects")
    print(f"   Each subject gets all 4 styles: BW, Sepia, Color, Painting")
    print()

    # Initialize client
    print("🚀 Initializing Portrait Generator...")
    print("   Model: gemini-3-pro-image-preview")
    print("   Features: Reference images, Search grounding, Internal reasoning")
    print()

    client = PortraitClient(output_dir=output_dir)

    # Generate portraits
    successful = 0
    failed = 0

    for i, subject in enumerate(test_subjects, 1):
        print("-" * 70)
        print(f"[{i}/{len(test_subjects)}] Generating portraits for: {subject}")
        print("-" * 70)

        try:
            result = client.generate(
                subject,
                styles=["BW", "Sepia", "Color", "Painting"]
            )

            if result.success:
                successful += 1
                print(f"✅ SUCCESS!")
                print(f"   Generated: {len(result.files)} portraits")
                print(f"   Time: {result.generation_time_seconds:.1f}s")
                print()
                print("   Files created:")
                for style, filepath in sorted(result.files.items()):
                    print(f"      {style:10} → {filepath}")
                print()

                if result.evaluation:
                    print("   Quality Scores:")
                    for style, eval_result in sorted(result.evaluation.items()):
                        print(f"      {style:10} → {eval_result.overall_score:.2f}")
                    print()

                # Show biographical data
                if result.metadata:
                    print(f"   Subject: {result.metadata.name}")
                    print(f"   Era: {result.metadata.era}")
                    if result.metadata.birth_year:
                        years = f"{result.metadata.birth_year}"
                        if result.metadata.death_year:
                            years += f"-{result.metadata.death_year}"
                        print(f"   Years: {years}")
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

    # Summary
    print("=" * 70)
    print("GENERATION COMPLETE")
    print("=" * 70)
    print(f"✅ Successful: {successful}/{len(test_subjects)} subjects")
    print(f"❌ Failed: {failed}/{len(test_subjects)} subjects")
    print(f"📁 Output: {output_dir.absolute()}")
    print()
    print(f"Total images generated: {successful * 4}")
    print()

    # Show how to view
    print("View images:")
    print(f"  open {output_dir}/")
    print()
    print("View specific image:")
    print(f"  open {output_dir}/AlanTuring_BW.png")
    print()

    # Create simple HTML gallery
    try:
        create_gallery(output_dir)
    except Exception as e:
        print(f"Note: Could not create gallery: {e}")


def create_gallery(output_dir: Path):
    """Create simple HTML gallery of generated images."""
    images = sorted(output_dir.glob("*.png"))

    if not images:
        return

    html = """<!DOCTYPE html>
<html>
<head>
    <title>Portrait Generator v2.0.0 - Test Gallery</title>
    <style>
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            max-width: 1400px;
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
    </style>
</head>
<body>
    <h1>Portrait Generator v2.0.0 Test Gallery</h1>
    <div class="subtitle">Generated with Gemini 3 Pro Image (Nano Banana Pro)</div>
    <div class="gallery">
"""

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
        Using Google Gemini 3 Pro Image with advanced AI features<br>
        Reference images • Search grounding • Physics-aware synthesis
    </div>
</body>
</html>
"""

    gallery_file = output_dir / "gallery.html"
    gallery_file.write_text(html, encoding="utf-8")
    print(f"📊 Created gallery: {gallery_file}")
    print(f"   Open in browser: open {gallery_file}")
    print()


if __name__ == "__main__":
    main()
