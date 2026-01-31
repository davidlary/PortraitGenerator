# Portrait Generator

> Generate historically accurate, publication-quality portrait images using Google Gemini

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://img.shields.io/badge/pypi-v1.0.0-blue.svg)](https://pypi.org/project/portrait-generator/)
[![Conda version](https://img.shields.io/badge/conda-v1.0.0-blue.svg)](https://anaconda.org/conda-forge/portrait-generator)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-308%20passed-green.svg)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-93%25-brightgreen.svg)](htmlcov/)

---

## Features

- 🎨 **Four Portrait Styles**: BW, Sepia, Color, Photorealistic Painting
- 🔬 **Historical Accuracy**: Deep biographical research ensures authentic representation
- ✅ **Self-Evaluation**: Quality assurance with automated validation
- 🐍 **Python API**: Simple, high-level API for programmatic use
- 🖥️ **CLI Commands**: Easy command-line interface for quick generation
- 🚀 **REST API**: FastAPI-based RESTful API for remote integration
- 📦 **PyPI & Conda**: Install via pip or conda
- 📊 **93%+ Test Coverage**: 308+ tests including end-to-end with real API
- 🔒 **Secure**: Environment-based credentials only
- 📝 **Fully Documented**: Complete API documentation and examples

---

## Quick Start

### Installation

**Via pip:**
```bash
pip install portrait-generator
```

**Via conda:**
```bash
conda install -c conda-forge portrait-generator
# or
conda install portrait-generator
```

**From source:**
```bash
git clone https://github.com/davidlary/PortraitGenerator.git
cd PortraitGenerator
pip install -e .
```

### Configuration

Set your Google Gemini API key:

```bash
export GOOGLE_API_KEY="your_gemini_api_key_here"
```

Or create a `.env` file:
```bash
GOOGLE_API_KEY=your_gemini_api_key_here
OUTPUT_DIR=./output
```

### Python API Usage

**Simple generation:**
```python
from portrait_generator import generate_portrait

# Generate all 4 styles
result = generate_portrait("Albert Einstein")

# Check results
print(f"Success: {result.success}")
print(f"Generated {len(result.files)} portraits:")
for style, filepath in result.files.items():
    print(f"  {style}: {filepath}")
```

**Using the client:**
```python
from portrait_generator import PortraitClient

# Initialize client
client = PortraitClient(
    api_key="your_api_key",
    output_dir="./portraits"
)

# Generate specific styles
result = client.generate(
    "Marie Curie",
    styles=["BW", "Color"]
)

# Batch generation
subjects = ["Alan Turing", "Ada Lovelace", "Grace Hopper"]
results = client.generate_batch(subjects, styles=["BW"])

# Check status
status = client.check_status("Albert Einstein")
print(f"BW exists: {status['BW']}")
```

### CLI Usage

**Generate a portrait:**
```bash
portrait-generator generate "Alan Turing"
```

**Generate specific styles:**
```bash
portrait-generator generate "Claude Shannon" --styles BW Sepia
```

**Batch generation:**
```bash
portrait-generator batch "Ada Lovelace" "Grace Hopper" "Margaret Hamilton"
```

**Check portrait status:**
```bash
portrait-generator status "Albert Einstein"
```

**Start API server:**
```bash
portrait-generator serve
# or with custom host/port
portrait-generator serve --host 0.0.0.0 --port 8080
```

**Health check:**
```bash
portrait-generator health-check
```

### REST API Usage

**Start server:**
```bash
portrait-generator serve
# Access interactive docs at http://localhost:8000/docs
```

**Generate via API:**
```bash
curl -X POST "http://localhost:8000/api/v1/generate" \
  -H "Content-Type: application/json" \
  -d '{"subject_name": "Marie Curie"}'
```

---

## API Reference

### Python API

#### `generate_portrait()`
Convenience function for quick portrait generation.

```python
from portrait_generator import generate_portrait

result = generate_portrait(
    subject_name="Alan Turing",
    api_key=None,              # Uses GOOGLE_API_KEY env var if not provided
    output_dir=None,            # Uses ./output if not provided
    force_regenerate=False,     # Skip existing portraits
    styles=None                 # Generate all 4 styles if not specified
)
```

#### `generate_batch()`
Generate multiple portraits in sequence.

```python
from portrait_generator import generate_batch

subjects = ["Ada Lovelace", "Grace Hopper"]
results = generate_batch(
    subject_names=subjects,
    api_key=None,
    output_dir=None,
    force_regenerate=False,
    styles=["BW", "Color"]      # Only generate BW and Color
)

for result in results:
    print(f"{result.subject}: {result.success}")
```

#### `PortraitClient`
Full-featured client for advanced usage.

```python
from portrait_generator import PortraitClient

client = PortraitClient(
    api_key="your_api_key",
    output_dir="./portraits",
    model="gemini-exp-1206"     # Optional: specify model
)

# Generate portrait
result = client.generate("Claude Shannon")

# Check what exists
status = client.check_status("Claude Shannon")
# Returns: {"BW": True, "Sepia": True, "Color": True, "Painting": True}

# Force regeneration
result = client.generate("Claude Shannon", force_regenerate=True)
```

### CLI Reference

#### `portrait-generator generate`
Generate portraits for a single subject.

```bash
portrait-generator generate [OPTIONS] SUBJECT_NAME

Options:
  --api-key TEXT          Google Gemini API key (or use GOOGLE_API_KEY env var)
  --output-dir PATH       Output directory (default: ./output)
  --styles TEXT           Space-separated styles: BW Sepia Color Painting
  --force                 Force regeneration even if portraits exist
  --verbose              Enable verbose logging
  --help                  Show help message
```

**Examples:**
```bash
# Generate all styles
portrait-generator generate "Alan Turing"

# Generate specific styles
portrait-generator generate "Claude Shannon" --styles BW Color

# Force regeneration
portrait-generator generate "Ada Lovelace" --force

# Custom output directory
portrait-generator generate "Grace Hopper" --output-dir ~/portraits
```

#### `portrait-generator batch`
Generate portraits for multiple subjects.

```bash
portrait-generator batch [OPTIONS] SUBJECT_NAMES...

Options:
  --api-key TEXT          Google Gemini API key
  --output-dir PATH       Output directory
  --styles TEXT           Space-separated styles
  --force                 Force regeneration
  --verbose              Enable verbose logging
  --help                  Show help message
```

**Examples:**
```bash
# Generate for multiple subjects
portrait-generator batch "Ada Lovelace" "Grace Hopper" "Margaret Hamilton"

# Batch with specific styles
portrait-generator batch "Alan Turing" "Claude Shannon" --styles BW Sepia
```

#### `portrait-generator status`
Check which portraits exist for a subject.

```bash
portrait-generator status [OPTIONS] SUBJECT_NAME

Options:
  --output-dir PATH       Output directory (default: ./output)
  --help                  Show help message
```

**Example:**
```bash
portrait-generator status "Albert Einstein"
# Output:
# Portrait status for 'Albert Einstein':
#   BW: ✓ exists
#   Sepia: ✓ exists
#   Color: ✗ missing
#   Painting: ✗ missing
```

#### `portrait-generator serve`
Start the REST API server.

```bash
portrait-generator serve [OPTIONS]

Options:
  --host TEXT             Host to bind to (default: 0.0.0.0)
  --port INTEGER          Port to bind to (default: 8000)
  --reload               Enable auto-reload for development
  --help                  Show help message
```

**Example:**
```bash
# Start on default port
portrait-generator serve

# Start on custom port with auto-reload
portrait-generator serve --port 8080 --reload
```

#### `portrait-generator health-check`
Check system health and configuration.

```bash
portrait-generator health-check [OPTIONS]

Options:
  --api-key TEXT          Google Gemini API key to validate
  --verbose              Show detailed information
  --help                  Show help message
```

**Example:**
```bash
portrait-generator health-check --verbose
# Output:
# ✓ API key configured
# ✓ Output directory writable
# ✓ Google Gemini API accessible
# ✓ All dependencies installed
```

### REST API

#### Endpoints

**Health Check**
```bash
GET /health
```

**Generate Single Portrait**
```bash
POST /api/v1/generate
Content-Type: application/json

{
  "subject_name": "Marie Curie",
  "styles": ["BW", "Color"],        # Optional
  "force_regenerate": false          # Optional
}
```

**Generate Batch**
```bash
POST /api/v1/batch
Content-Type: application/json

{
  "subject_names": ["Ada Lovelace", "Grace Hopper"],
  "styles": ["BW"],                  # Optional
  "force_regenerate": false          # Optional
}
```

**Check Status**
```bash
GET /api/v1/status/{subject_name}
```

**Download Portrait**
```bash
GET /api/v1/download/{subject_name}/{style}
```

**Examples:**
```bash
# Generate portrait
curl -X POST "http://localhost:8000/api/v1/generate" \
  -H "Content-Type: application/json" \
  -d '{"subject_name": "Alan Turing", "styles": ["BW"]}'

# Check status
curl "http://localhost:8000/api/v1/status/Alan%20Turing"

# Download portrait
curl "http://localhost:8000/api/v1/download/Alan%20Turing/BW" \
  -o alan_turing_bw.png
```

**Interactive Documentation:**
Once the server is running, visit `http://localhost:8000/docs` for interactive API documentation.

---

## Portrait Styles

### 1. Black & White (`BW`)
- Classic monochrome photography
- Enhanced contrast
- Filename: `FirstNameLastName_BW.png`

### 2. Sepia (`Sepia`)
- Warm vintage aesthetic
- Classic early photography style
- Filename: `FirstNameLastName_Sepia.png`

### 3. Color (`Color`)
- Full color photorealistic
- Natural skin tones
- Filename: `FirstNameLastName_Color.png`

### 4. Photorealistic Painting (`Painting`)
- Oil painting style with visible brushstrokes
- Highly detailed
- Filename: `FirstNameLastName_Painting.png`

---

## Architecture

### Core Components

1. **GeminiImageClient**: Google Gemini API integration for image generation
2. **BiographicalResearcher**: Deep research for historical accuracy
3. **TitleOverlayEngine**: Professional title overlays with name and dates
4. **PortraitGenerator**: Orchestrates complete workflow
5. **QualityEvaluator**: Self-evaluation and quality assurance
6. **API Layer**: RESTful FastAPI endpoints

### Workflow

```
Subject Name → Research → Generate (4 styles) → Add Overlays → Evaluate → Save
```

---

## Testing

### Running Tests

```bash
# Run all tests with coverage
pytest tests/ --cov=portrait_generator --cov-report=html --cov-report=term

# Run specific test types
pytest tests/unit/ -v           # Unit tests (308+ tests)
pytest tests/integration/ -v    # Integration tests

# Run end-to-end tests with real API
export GOOGLE_API_KEY="your_api_key"
pytest tests/integration/test_e2e_real_api.py -m e2e -v

# Check coverage report
open htmlcov/index.html
```

### Test Coverage

**Current Coverage: 93.11%** (exceeds 90% target)

- **308+ unit tests** covering all core functionality
- **Integration tests** with mocked external APIs
- **End-to-end tests** with real Google Gemini API calls
- **Visual tests** for quality verification

### Test Organization

```
tests/
├── unit/                       # Unit tests (fast, mocked)
│   ├── test_client.py         # Python API client tests
│   ├── test_gemini_client.py  # Gemini API client tests
│   ├── test_generator.py      # Portrait generator tests
│   ├── test_researcher.py     # Biographical research tests
│   ├── test_overlay.py        # Title overlay tests
│   └── test_evaluator.py      # Quality evaluation tests
├── integration/                # Integration tests
│   ├── test_api.py            # REST API endpoint tests
│   ├── test_workflow.py       # End-to-end workflow tests
│   └── test_e2e_real_api.py   # Real API tests (requires GOOGLE_API_KEY)
└── fixtures/                   # Test data and fixtures
```

### Running E2E Tests

End-to-end tests make **real API calls** to Google Gemini and require a valid API key:

```bash
# Set API key
export GOOGLE_API_KEY="your_api_key"

# Run all e2e tests
pytest -m e2e -v

# Run specific e2e test
pytest tests/integration/test_e2e_real_api.py::TestE2ERealAPI::test_generate_single_portrait_all_styles -v
```

**Note:** E2E tests are automatically skipped if `GOOGLE_API_KEY` is not set.

---

## Development

### Project Structure

```
PortraitGenerator/
├── src/portrait_generator/      # Main package
│   ├── __init__.py              # Package exports (PortraitClient, etc.)
│   ├── client.py                # High-level Python API
│   ├── cli.py                   # Command-line interface
│   ├── generator.py             # Portrait generation orchestration
│   ├── gemini_client.py         # Google Gemini API integration
│   ├── researcher.py            # Biographical research
│   ├── overlay.py               # Title overlay engine
│   ├── evaluator.py             # Quality evaluation
│   ├── config.py                # Configuration and settings
│   └── api/                     # REST API
│       ├── server.py            # FastAPI application
│       ├── routes.py            # API endpoints
│       └── models.py            # Request/response models
├── tests/                       # Test suite (308+ tests, 93% coverage)
│   ├── unit/                    # Unit tests with mocks
│   ├── integration/             # Integration tests (incl. e2e)
│   └── fixtures/                # Test data and fixtures
├── conda.recipe/                # Conda package recipe
│   └── meta.yaml               # Conda build configuration
├── docs/                        # Documentation
├── Examples/                    # Usage examples
├── output/                      # Generated portraits (default)
├── pyproject.toml              # Modern Python package config (PEP 621)
├── setup.py                    # Package setup script
├── requirements.txt            # Production dependencies
├── requirements-dev.txt        # Development dependencies
├── MANIFEST.in                 # Package distribution rules
├── CHANGELOG.md                # Version history
└── README.md                   # This file
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/

# Run all quality checks
black src/ tests/ && ruff check src/ tests/ && mypy src/ && pytest
```

### Building the Package

**Build Python package:**
```bash
python -m build
# Creates dist/portrait_generator-1.0.0.tar.gz and .whl
```

**Build Conda package:**
```bash
conda build conda.recipe/
```

**Install locally for development:**
```bash
pip install -e .
```

---

## Configuration

### Environment Variables

Portrait Generator can be configured via environment variables:

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `GOOGLE_API_KEY` | Google Gemini API key | - | **Yes** |
| `GEMINI_MODEL` | Gemini model name | `gemini-exp-1206` | No |
| `IMAGE_RESOLUTION` | Image size as `width,height` | `1024,1024` | No |
| `OUTPUT_DIR` | Output directory for portraits | `./output` | No |
| `LOG_LEVEL` | Logging level | `INFO` | No |

### Configuration Methods

**1. Environment Variables (Recommended)**
```bash
export GOOGLE_API_KEY="your_api_key"
export OUTPUT_DIR="~/portraits"
```

**2. `.env` File**
```bash
# Create .env file in project root
cat > .env << EOF
GOOGLE_API_KEY=your_api_key
OUTPUT_DIR=./output
GEMINI_MODEL=gemini-exp-1206
LOG_LEVEL=INFO
EOF
```

**3. Programmatic Configuration**
```python
from portrait_generator import PortraitClient

client = PortraitClient(
    api_key="your_api_key",
    output_dir="~/portraits",
    model="gemini-exp-1206"
)
```

**4. Settings Object**
```python
from portrait_generator.config import Settings

settings = Settings(
    google_api_key="your_api_key",
    output_dir="~/portraits",
    gemini_model="gemini-exp-1206"
)
```

---

## Installation Details

### Package Distribution

Portrait Generator is distributed as:
- **PyPI package**: `portrait-generator` (install via `pip`)
- **Conda package**: `portrait-generator` (install via `conda`)
- **Source code**: Available on GitHub

### Entry Points

The package provides two console script entry points:
- `portrait-generator` - Main CLI command
- `portrait-gen` - Shorter alias

Both commands provide identical functionality.

### Dependencies

**Core Dependencies:**
- `google-genai>=1.0.0,<2.0.0` - Google Gemini API client
- `pillow>=11.0.0,<12.0.0` - Image processing
- `fastapi>=0.100.0,<1.0.0` - REST API framework
- `uvicorn[standard]>=0.27.0,<1.0.0` - ASGI server
- `pydantic>=2.6.0,<3.0.0` - Data validation
- `pydantic-settings>=2.1.0,<3.0.0` - Settings management
- `click>=8.0.0,<9.0.0` - CLI framework
- `httpx>=0.26.0,<1.0.0` - HTTP client
- `requests>=2.31.0,<3.0.0` - HTTP library
- `python-dotenv>=1.0.0,<2.0.0` - Environment variables
- `loguru>=0.7.0,<1.0.0` - Logging

**Development Dependencies:**
- `pytest>=9.0.0` - Testing framework
- `pytest-cov>=7.0.0` - Coverage reporting
- `pytest-asyncio>=1.3.0` - Async test support
- `pytest-mock>=3.15.0` - Mocking utilities
- `black>=24.0.0` - Code formatter
- `ruff>=0.1.0` - Fast linter
- `mypy>=1.8.0` - Type checker

### Python Version Support

- **Minimum**: Python 3.10
- **Tested**: Python 3.10, 3.11, 3.12
- **Recommended**: Python 3.11+

---

## Examples

### Example 1: Simple Portrait Generation

```python
from portrait_generator import generate_portrait

# Generate all 4 styles with default settings
result = generate_portrait("Ada Lovelace")

if result.success:
    print(f"✓ Generated {len(result.files)} portraits")
    print(f"  Generation time: {result.generation_time_seconds:.1f}s")

    for style, filepath in result.files.items():
        print(f"  {style}: {filepath}")
else:
    print(f"✗ Generation failed: {result.errors}")
```

### Example 2: Batch Processing

```python
from portrait_generator import PortraitClient

# Initialize client
client = PortraitClient()

# List of subjects
computer_scientists = [
    "Alan Turing",
    "Claude Shannon",
    "Grace Hopper",
    "Donald Knuth",
]

# Generate only BW portraits for all subjects
results = client.generate_batch(
    computer_scientists,
    styles=["BW"],
    force_regenerate=False
)

# Report results
successful = [r for r in results if r.success]
failed = [r for r in results if not r.success]

print(f"✓ Successful: {len(successful)}/{len(results)}")
if failed:
    print(f"✗ Failed: {len(failed)}")
    for r in failed:
        print(f"  - {r.subject}: {r.errors}")
```

### Example 3: Custom Output Directory

```python
from portrait_generator import PortraitClient
from pathlib import Path

# Create custom output directory
output_dir = Path.home() / "Documents" / "Portraits"
output_dir.mkdir(parents=True, exist_ok=True)

# Initialize with custom directory
client = PortraitClient(
    output_dir=output_dir
)

# Generate portraits
result = client.generate("Marie Curie")
print(f"Portraits saved to: {output_dir}")
```

### Example 4: Check Before Generating

```python
from portrait_generator import PortraitClient

client = PortraitClient()

subject = "Albert Einstein"

# Check what already exists
status = client.check_status(subject)

# Determine what needs to be generated
missing_styles = [style for style, exists in status.items() if not exists]

if missing_styles:
    print(f"Generating missing styles: {missing_styles}")
    result = client.generate(subject, styles=missing_styles)
else:
    print(f"All portraits already exist for {subject}")
```

### Example 5: CLI Workflow

```bash
#!/bin/bash
# batch_generate.sh - Generate portraits for multiple subjects

SUBJECTS=(
    "Alan Turing"
    "Ada Lovelace"
    "Claude Shannon"
    "Grace Hopper"
)

# Create output directory
mkdir -p ./portraits

# Generate each subject
for subject in "${SUBJECTS[@]}"; do
    echo "Generating: $subject"
    portrait-generator generate "$subject" \
        --output-dir ./portraits \
        --styles BW Color \
        --verbose
done

# Check status of all subjects
echo ""
echo "Status Report:"
for subject in "${SUBJECTS[@]}"; do
    echo "  $subject:"
    portrait-generator status "$subject" --output-dir ./portraits
done
```

### Example 6: API Integration

```python
import httpx

# API base URL
API_URL = "http://localhost:8000/api/v1"

# Generate portrait via API
response = httpx.post(
    f"{API_URL}/generate",
    json={
        "subject_name": "Alan Turing",
        "styles": ["BW", "Color"]
    },
    timeout=300.0  # 5 minutes timeout
)

if response.status_code == 200:
    result = response.json()
    print(f"Generated: {result['subject']}")
    print(f"Files: {result['files']}")
else:
    print(f"Error: {response.json()['detail']}")
```

For more examples, see the `/Examples` directory in the repository.

---

## Security

**CRITICAL**: Never commit API keys or credentials.

- Use environment variables for all secrets
- Review `.gitignore` before committing
- Check `git status` and `git diff --staged`
- API keys must be >= 20 characters

---

## Requirements

- Python 3.10+
- Google Gemini API key
- 2GB+ RAM
- ~5MB disk space per subject (4 portraits)

---

## Troubleshooting

### API Key Issues

```python
from portrait_generator.config import Settings

settings = Settings()
if not settings.validate_api_key():
    print("Invalid API key")
```

### Image Generation Fails

1. Check API quota/limits
2. Verify internet connection
3. Check logs in `.cpf/logs/`
4. Enable debug logging: `LOG_LEVEL=DEBUG`

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests for new features
4. Ensure all tests pass (`pytest tests/`)
5. Submit a pull request

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

## Authors

- **Dr. David Lary** - University of Texas at Dallas
- **Claude Sonnet 4.5** - AI Assistant (Anthropic)

---

## Acknowledgments

- Google Gemini API for image generation
- Pillow (PIL) for image processing
- FastAPI for API framework
- pytest for testing infrastructure

---

## Status

🚀 **Version 1.0.0** - Production Ready

- **Release Date**: January 30, 2026
- **Python Support**: 3.10, 3.11, 3.12
- **Test Coverage**: 93.11% (308+ tests passing)
- **Package Status**: Available on PyPI and Conda
- **API Status**: Stable (v1)
- **Documentation**: Complete

### Version History

See [CHANGELOG.md](CHANGELOG.md) for detailed version history.

---

## Publishing

### Publishing to PyPI

```bash
# Build package
python -m build

# Check distribution
twine check dist/*

# Upload to PyPI
twine upload dist/*
```

### Publishing to Conda

```bash
# Build conda package
conda build conda.recipe/

# Upload to conda channel
anaconda upload <path-to-tarball>
```

### Creating a Release

```bash
# Tag the release
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0

# Create GitHub release
gh release create v1.0.0 \
  --title "Portrait Generator v1.0.0" \
  --notes "See CHANGELOG.md for details"
```

---

## Documentation

### Online Documentation

- **Read the Docs**: https://portrait-generator.readthedocs.io
- **GitHub Pages**: https://davidlary.github.io/PortraitGenerator
- **PyPI**: https://pypi.org/project/portrait-generator
- **GitHub**: https://github.com/davidlary/PortraitGenerator

### Local Documentation

- [CHANGELOG.md](CHANGELOG.md) - Version history and release notes
- [ImplementationPlan.md](ImplementationPlan.md) - Technical implementation details
- [LICENSE](LICENSE) - MIT License
- [Examples/](Examples/) - Usage examples and tutorials

### API Documentation

Interactive API documentation is available when running the server:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

---

## Roadmap

Planned features for future releases:

- [ ] Additional portrait styles (Oil Painting, Sketch, Watercolor)
- [ ] Custom style templates
- [ ] Batch parallel processing
- [ ] Portrait editing and refinement
- [ ] Video portrait generation
- [ ] Integration with other AI models
- [ ] Web UI for non-technical users
- [ ] Portrait comparison and analytics

---

## Support

### Getting Help

- **Documentation**: https://portrait-generator.readthedocs.io
- **Issues**: https://github.com/davidlary/PortraitGenerator/issues
- **Discussions**: https://github.com/davidlary/PortraitGenerator/discussions

### Reporting Bugs

Please report bugs via GitHub Issues with:
1. Description of the problem
2. Steps to reproduce
3. Expected vs actual behavior
4. System information (Python version, OS, etc.)
5. Error messages and logs

### Feature Requests

Feature requests are welcome! Please open a GitHub Issue with:
1. Description of the proposed feature
2. Use case and motivation
3. Proposed API or usage example

---

## FAQ

**Q: How much does it cost to generate portraits?**
A: The cost depends on Google Gemini API pricing. Typically ~$0.01-0.05 per portrait depending on model and resolution.

**Q: Can I use this commercially?**
A: Yes, the code is MIT licensed. However, check Google's API terms for commercial usage.

**Q: How long does it take to generate a portrait?**
A: Typically 20-60 seconds per style, so ~2-4 minutes for all 4 styles.

**Q: Can I customize the portrait styles?**
A: Yes, you can modify the style prompts in the code or wait for the custom styles feature in a future release.

**Q: Do I need to credit the generated portraits?**
A: The portraits are AI-generated. Attribution is appreciated but not required under the MIT license.

**Q: Can I generate portraits of living people?**
A: Technically yes, but be mindful of privacy, likeness rights, and ethical considerations.

---

For questions or issues, please open an issue on GitHub.
