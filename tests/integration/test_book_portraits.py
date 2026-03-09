"""Integration tests: generate all 94 book portraits from BookPortraits.md.

Each test generates a Painting-style portrait for one subject, saves it to
tests/ExamplePortraitTests/, and verifies the output passes the full
verification pipeline.

Output filename conventions:
    <Name>_Painting.png        — generated with at least one reference image
    <Name>_Painting_NoRef.png  — generated with NO reference images (no known portrait exists)

Usage:
    # Run all portrait tests in parallel (12 workers — recommended):
    python -m pytest tests/integration/test_book_portraits.py -v --timeout=600 -m integration -n 12

    # Run all portrait tests sequentially (slower):
    python -m pytest tests/integration/test_book_portraits.py -v --timeout=600 -m integration

    # Run a single subject:
    python -m pytest tests/integration/test_book_portraits.py -v -k "Alan_Turing" --timeout=600

    # Force regeneration of all portraits:
    PORTRAIT_FORCE_REGENERATE=1 python -m pytest tests/integration/test_book_portraits.py -v --timeout=600 -n 12

Notes:
    - Requires a valid GOOGLE_API_KEY environment variable.
    - Each portrait takes ~22-45 seconds with the default Flash model.
    - Total runtime for all 94 portraits: ~12-15 minutes with 12 parallel workers.
    - Portraits are saved to tests/ExamplePortraitTests/ and NOT deleted after tests.
    - force_regenerate=False by default (existing portraits reused, skipped via pytest.skip).
    - Unicode normalization (NFC/NFD) handled for macOS HFS+ filesystem compatibility.
"""

import os
import time
import unicodedata
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

OUTPUT_DIR = Path(__file__).parent.parent / "ExamplePortraitTests"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

_GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
_NO_API_KEY = not _GOOGLE_API_KEY or len(_GOOGLE_API_KEY) < 20
_SKIP_NO_KEY = pytest.mark.skipif(
    _NO_API_KEY,
    reason="Requires valid GOOGLE_API_KEY environment variable",
)
_FORCE_REGEN = os.getenv("PORTRAIT_FORCE_REGENERATE", "0") == "1"

# ---------------------------------------------------------------------------
# Complete list of 94 unique individuals from BookPortraits.md
# Format: (canonical_name, birth_year_or_approx, death_year_or_None, chapter)
# ---------------------------------------------------------------------------

BOOK_PORTRAIT_SUBJECTS = [
    # Chapter-Introduction
    ("Christian Friedrich Schönbein", 1799, 1868, "Chapter-Introduction"),
    ("John Tyndall",                  1820, 1893, "Chapter-Introduction"),
    ("Joseph Fourier",                1768, 1830, "Chapter-Introduction"),
    ("Louis Agassiz",                 1807, 1873, "Chapter-Introduction"),
    ("Svante Arrhenius",              1859, 1927, "Chapter-Introduction"),
    ("Theodore Fujita",               1920, 1998, "Chapter-Introduction"),

    # Chapter-Global-Chemistry
    ("Carl-Gustaf Rossby",            1898, 1957, "Chapter-Global-Chemistry"),
    ("Nicolaus Copernicus",           1473, 1543, "Chapter-Global-Chemistry"),
    ("Gaspard-Gustave de Coriolis",   1792, 1843, "Chapter-Global-Chemistry"),
    ("Henry Eyring",                  1901, 1981, "Chapter-Global-Chemistry"),
    ("Jacobus van't Hoff",            1852, 1911, "Chapter-Global-Chemistry"),
    ("Johann Heinrich Lambert",       1728, 1777, "Chapter-Global-Chemistry"),
    ("Jöns Jacob Berzelius",          1779, 1848, "Chapter-Global-Chemistry"),
    ("Johannes Kepler",               1571, 1630, "Chapter-Global-Chemistry"),
    ("Léon Teisserenc de Bort",       1855, 1913, "Chapter-Global-Chemistry"),
    ("Lord Rayleigh",                 1842, 1919, "Chapter-Global-Chemistry"),
    ("Luke Howard",                   1772, 1864, "Chapter-Global-Chemistry"),
    ("Isaac Newton",                  1643, 1727, "Chapter-Global-Chemistry"),
    ("Sydney Chapman",                1888, 1970, "Chapter-Global-Chemistry"),
    ("Tor Bergeron",                  1891, 1977, "Chapter-Global-Chemistry"),
    ("Tycho Brahe",                   1546, 1601, "Chapter-Global-Chemistry"),
    ("Walter Findeisen",              1909, 1945, "Chapter-Global-Chemistry"),
    # George Hadley: no self-portrait survives; reference images are of brother
    # John Hadley FRS (1682-1744, sextant inventor) for familial likeness.
    # Sources: Cambridge Fitzwilliam Museum + Royal Museums Greenwich (both HTTP 200).
    ("George Hadley",                 1685, 1768, "Chapter-Global-Chemistry"),

    # Chapter-Air-Quality
    ("C. William Gear",               1935, 2022, "Chapter-Air-Quality"),
    ("Hiram Levy",                    1936, None, "Chapter-Air-Quality"),
    ("Mario Molina",                  1943, 2020, "Chapter-Air-Quality"),
    ("Mark Jacobson",                 1967, None, "Chapter-Air-Quality"),
    ("Paul Crutzen",                  1933, 2021, "Chapter-Air-Quality"),
    ("Guy Brasseur",                  1948, None, "Chapter-Air-Quality"),
    ("Susan Solomon",                 1956, None, "Chapter-Air-Quality"),

    # Chapter-Simulating
    ("Aleksandr Lyapunov",            1857, 1918, "Chapter-Simulating"),
    ("Henri Poincaré",                1854, 1912, "Chapter-Simulating"),
    ("John A. Pyle",                  1951, None, "Chapter-Simulating"),
    ("Joseph-Louis Lagrange",         1736, 1813, "Chapter-Simulating"),
    ("Leonhard Euler",                1707, 1783, "Chapter-Simulating"),
    ("Sherwood Rowland",              1927, 2012, "Chapter-Simulating"),
    ("Martyn Chipperfield",           1963, None, "Chapter-Simulating"),

    # Chapter-Observing
    ("Clive Rodgers",                 1940, None, "Chapter-Observing"),
    ("Moustafa Chahine",              1935, 2011, "Chapter-Observing"),
    ("Sydney Twomey",                 1927, 2012, "Chapter-Observing"),
    ("Ulrich Platt",                  1944, None, "Chapter-Observing"),

    # Chapter-Assimilation
    ("Andrew C. Lorenc",              1951, None, "Chapter-Assimilation"),
    ("David Lary",                    1965, None, "Chapter-Assimilation"),
    ("Eugenia Kalnay",                1942, None, "Chapter-Assimilation"),
    ("Mike Fisher (1962-Present)",    1962, None, "Chapter-Assimilation"),
    ("Norbert Wiener",                1894, 1964, "Chapter-Assimilation"),
    ("Roger Daley",                   1941, 1999, "Chapter-Assimilation"),
    ("Rudolf Kalman",                 1930, 2016, "Chapter-Assimilation"),

    # Chapter-ML
    ("Teuvo Kohonen",                 1934, 2021, "Chapter-ML"),

    # Chapter-Charged
    ("Benjamin Franklin",             1706, 1790, "Chapter-Charged"),
    ("Brian Tinsley",                 1940, None, "Chapter-Charged"),
    ("Charles-Augustin de Coulomb",   1736, 1806, "Chapter-Charged"),
    ("Charles T. R. Wilson",          1869, 1959, "Chapter-Charged"),
    ("Davis Sentman",                 1946, 2011, "Chapter-Charged"),
    ("Edward Appleton",               1892, 1965, "Chapter-Charged"),
    ("Francis John Welsh Whipple",    1876, 1943, "Chapter-Charged"),
    ("Frank John Scrase",             1897, 1963, "Chapter-Charged"),
    ("Georg Pfotzer",                 1909, 1981, "Chapter-Charged"),
    ("Henrik Svensmark",              1958, None, "Chapter-Charged"),
    ("John Winckler",                 1916, 2001, "Chapter-Charged"),
    ("Louis-Guillaume Le Monnier",    1717, 1799, "Chapter-Charged"),
    ("Marx Brook",                    1920, 2002, "Chapter-Charged"),
    ("Ralph Markson",                 1930, 2022, "Chapter-Charged"),
    ("Richard Carrington",            1826, 1875, "Chapter-Charged"),
    ("Scott Forbush",                 1904, 1984, "Chapter-Charged"),
    ("Victor Hess",                   1883, 1964, "Chapter-Charged"),
    ("Winfried Otto Schumann",        1888, 1974, "Chapter-Charged"),

    # Chapter-IAQ
    ("Charles Weschler",              1944, None, "Chapter-IAQ"),
    ("Lance Wallace",                 1940, 2022, "Chapter-IAQ"),
    ("Max von Pettenkofer",           1818, 1901, "Chapter-IAQ"),
    ("William Nazaroff",              1952, None, "Chapter-IAQ"),

    # Chapter-Improving-IAQ
    ("Boris Petrovich Tokin",         1900, 1982, "Chapter-Improving-IAQ"),
    ("Charles H. Blackley",           1820, 1900, "Chapter-Improving-IAQ"),
    ("Edward O. Wilson",              1929, 2021, "Chapter-Improving-IAQ"),
    ("Frank W. Went",                 1903, 1990, "Chapter-Improving-IAQ"),
    ("Jan Ingenhousz",                1730, 1799, "Chapter-Improving-IAQ"),
    ("Joseph Priestley",              1733, 1804, "Chapter-Improving-IAQ"),
    ("Melvin Calvin",                 1911, 1997, "Chapter-Improving-IAQ"),
    ("Nicolas-Théodore de Saussure",  1767, 1845, "Chapter-Improving-IAQ"),
    ("Walther Flemming",              1843, 1905, "Chapter-Improving-IAQ"),
    ("William F. Wells",              1887, 1963, "Chapter-Improving-IAQ"),
    ("Willis Carrier",                1876, 1950, "Chapter-Improving-IAQ"),

    # Chapter-Health-Impacts
    ("Avicenna",                       980, 1037, "Chapter-Health-Impacts"),
    ("Bruce McEwen",                  1938, 2020, "Chapter-Health-Impacts"),
    ("Hans Selye",                    1907, 1982, "Chapter-Health-Impacts"),
    ("Hildegard von Bingen",          1098, 1179, "Chapter-Health-Impacts"),
    ("Hippocrates",                    460,  370, "Chapter-Health-Impacts"),  # approx BCE
    ("Nicholas Culpeper",             1616, 1654, "Chapter-Health-Impacts"),
    ("Pedanius Dioscorides",            40,   90, "Chapter-Health-Impacts"),  # approx CE
    ("René-Maurice Gattefossé",       1881, 1950, "Chapter-Health-Impacts"),
    ("Ronald Ross",                   1857, 1932, "Chapter-Health-Impacts"),
    ("Rudolf Virchow",                1821, 1902, "Chapter-Health-Impacts"),
    ("Theophrastus",                   371,  287, "Chapter-Health-Impacts"),  # approx BCE
    ("Walter Bradford Cannon",        1871, 1945, "Chapter-Health-Impacts"),

    # Chapter-AQ-Plants-Birds-Animals
    ("Eugene P. Odum",                1913, 2002, "Chapter-AQ-Plants-Birds-Animals"),
    ("F. Herbert Bormann",            1922, 2012, "Chapter-AQ-Plants-Birds-Animals"),
    ("Gene Likens",                   1935, None, "Chapter-AQ-Plants-Birds-Animals"),
    ("Karl von Frisch",               1886, 1982, "Chapter-AQ-Plants-Birds-Animals"),
    ("Rachel Carson",                 1907, 1964, "Chapter-AQ-Plants-Birds-Animals"),
]

# ---------------------------------------------------------------------------
# Parametrize IDs — use sanitized name for readability in test output
# ---------------------------------------------------------------------------

def _subject_id(subject_tuple):
    """Create a safe pytest ID from subject name."""
    name = subject_tuple[0]
    return name.replace(" ", "_").replace("-", "_").replace(".", "").replace("'", "").replace("é", "e").replace("ö", "o").replace("ü", "u").replace("ä", "a").replace("ô", "o").replace("ñ", "n").replace("ó", "o").replace("é", "e").replace("è", "e").replace("ë", "e").replace("ï", "i").replace("ã", "a").replace("â", "a").replace("ê", "e").replace("ú", "u").replace("á", "a").replace("ì", "i").replace("Ö", "O").replace("ø", "o").replace("Ø", "O")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def portrait_generator():
    """Create an EnhancedPortraitGenerator for each test (compatible with pytest-xdist parallel)."""
    from portrait_generator.config.settings import Settings
    from portrait_generator.core.generator_enhanced import EnhancedPortraitGenerator
    from portrait_generator.utils.gemini_client import GeminiImageClient
    from portrait_generator.core.researcher import BiographicalResearcher
    from portrait_generator.core.overlay import TitleOverlayEngine
    from portrait_generator.core.evaluator_enhanced import EnhancedQualityEvaluator

    settings = Settings(
        google_api_key=_GOOGLE_API_KEY,
        output_dir=OUTPUT_DIR,
        enable_portrait_verification=True,
        enable_ground_truth_lookup=True,
        enable_reference_images=True,
        portrait_verification_min_size_kb=100,  # Relaxed for speed
        max_generation_attempts=2,
    )

    client = GeminiImageClient(
        api_key=_GOOGLE_API_KEY,
        model=settings.gemini_model,
    )
    researcher = BiographicalResearcher(gemini_client=client)
    overlay = TitleOverlayEngine()
    evaluator = EnhancedQualityEvaluator(
        gemini_client=client,
        model_profile=settings.get_model_profile(),
    )

    return EnhancedPortraitGenerator(
        gemini_client=client,
        researcher=researcher,
        overlay_engine=overlay,
        evaluator=evaluator,
        output_dir=OUTPUT_DIR,
        settings=settings,
    )


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _generator_filename(name: str, style: str) -> str:
    """Replicate EnhancedPortraitGenerator._create_filename() exactly.

    The generator uses:
      1. Keep only alphanumeric chars and spaces (removes hyphens, apostrophes, etc.)
      2. Split on spaces → list of words
      3. capitalize() each alpha-starting word (first char upper, rest lower);
         digit-starting words (e.g. "1962Present") are kept as-is to preserve case.
      4. Join + append style suffix

    This MUST stay in sync with generator_enhanced.py::_create_filename().
    """
    clean_name = "".join(c for c in name if c.isalnum() or c.isspace())
    parts = clean_name.split()
    base = "".join(
        word.capitalize() if word and word[0].isalpha() else word
        for word in parts
    )
    return f"{base}_{style}"


def _portrait_exists(name: str) -> bool:
    """Check if a Painting portrait already exists for this subject.

    Checks both filename variants:
      - <Name>_Painting.png        (generated with reference images)
      - <Name>_Painting_NoRef.png  (generated without any reference images)

    Three issues addressed:
    1. Case: generator uses capitalize() which lowercases mid-word chars in hyphenated
       names (e.g., "Carl-Gustaf Rossby" → "CarlgustafRossby", not "CarlGustafRossby").
       Using exact _generator_filename() logic avoids the mismatch.
    2. Unicode normalization: macOS HFS+ stores filenames in NFD decomposed form
       (ö → o + combining diacritical) while Python strings are NFC composed
       (ö → single code point U+00F6). Path.glob() uses string comparison without
       normalization, so we iterate and compare with unicodedata.normalize("NFC", ...).
    3. NoRef suffix: subjects with no known portrait get _NoRef suffix appended by
       the generator; both variants must be accepted as "already exists".
    """
    base = _generator_filename(name, "Painting")
    base_nfc = unicodedata.normalize("NFC", base)
    targets = {f"{base_nfc}.png", f"{base_nfc}_NoRef.png"}
    for f in OUTPUT_DIR.iterdir():
        fname_nfc = unicodedata.normalize("NFC", f.name)
        if fname_nfc in targets:
            return True
    return False


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@_SKIP_NO_KEY
@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.parametrize(
    "name, birth_year, death_year, chapter",
    BOOK_PORTRAIT_SUBJECTS,
    ids=[_subject_id(s) for s in BOOK_PORTRAIT_SUBJECTS],
)
def test_generate_book_portrait(
    portrait_generator,
    name: str,
    birth_year: int,
    death_year,
    chapter: str,
):
    """Generate a Painting-style portrait for one book subject.

    Skips generation if portrait already exists (unless PORTRAIT_FORCE_REGENERATE=1).
    Verifies: portrait file exists, size ≥ 100 KB, and generation result is success.
    """
    if not _FORCE_REGEN and _portrait_exists(name):
        pytest.skip(f"Portrait already exists for {name} — use PORTRAIT_FORCE_REGENERATE=1 to regenerate")

    start = time.time()
    result = portrait_generator.generate_portrait(
        subject_name=name,
        force_regenerate=_FORCE_REGEN,
        styles=["Painting"],
    )
    elapsed = time.time() - start

    # Core assertions
    assert result is not None, f"generate_portrait returned None for {name}"
    assert result.success, (
        f"Portrait generation failed for {name} (chapter: {chapter}): {result.errors}"
    )

    # Verify at least one Painting portrait file was created
    painting_files = list(OUTPUT_DIR.glob(f"*Painting*.png"))
    assert len(painting_files) > 0, f"No Painting PNG found in {OUTPUT_DIR} for {name}"

    # Find the most recently modified Painting file
    latest = max(painting_files, key=lambda p: p.stat().st_mtime)
    assert latest.stat().st_size >= 100 * 1024, (
        f"Portrait too small for {name}: {latest.stat().st_size // 1024} KB "
        f"(expected ≥ 100 KB)"
    )

    print(f"\n  [{chapter}] {name}: OK ({elapsed:.1f}s) → {latest.name}")


@pytest.mark.integration
def test_example_portrait_output_dir_exists():
    """Verify the ExamplePortraitTests output directory was created."""
    assert OUTPUT_DIR.exists(), f"Output directory not found: {OUTPUT_DIR}"
    assert OUTPUT_DIR.is_dir()


@pytest.mark.integration
@pytest.mark.skipif(_NO_API_KEY, reason="Requires GOOGLE_API_KEY")
def test_generate_single_canonical_example():
    """Generate one portrait (Alan Turing equivalent: Norbert Wiener) as a canonical smoke test.

    This verifies the full end-to-end pipeline with a well-documented subject
    who has confirmed reference images in our URL table.
    """
    from portrait_generator.config.settings import Settings
    from portrait_generator.core.generator_enhanced import EnhancedPortraitGenerator
    from portrait_generator.utils.gemini_client import GeminiImageClient
    from portrait_generator.core.researcher import BiographicalResearcher
    from portrait_generator.core.overlay import TitleOverlayEngine
    from portrait_generator.core.evaluator_enhanced import EnhancedQualityEvaluator

    settings = Settings(
        google_api_key=_GOOGLE_API_KEY,
        output_dir=OUTPUT_DIR,
        enable_portrait_verification=True,
        enable_reference_images=True,
        portrait_verification_min_size_kb=100,
        max_generation_attempts=2,
    )

    client = GeminiImageClient(api_key=_GOOGLE_API_KEY, model=settings.gemini_model)
    generator = EnhancedPortraitGenerator(
        gemini_client=client,
        researcher=BiographicalResearcher(gemini_client=client),
        overlay_engine=TitleOverlayEngine(),
        evaluator=EnhancedQualityEvaluator(
            gemini_client=client,
            model_profile=settings.get_model_profile(),
        ),
        output_dir=OUTPUT_DIR,
        settings=settings,
    )

    # Use Norbert Wiener — confirmed reference photo available, mathematically famous
    result = generator.generate_portrait(
        subject_name="Norbert Wiener",
        force_regenerate=False,
        styles=["Painting"],
    )

    assert result is not None
    assert result.success, f"Canonical smoke test failed: {result.errors}"

    # Find the portrait
    portraits = list(OUTPUT_DIR.glob("NorbertWiener*Painting*.png"))
    assert len(portraits) > 0, "NorbertWiener_Painting.png not found"
    assert portraits[0].stat().st_size >= 100 * 1024, "Canonical portrait too small"
