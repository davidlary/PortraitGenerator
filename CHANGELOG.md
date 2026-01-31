# Changelog

All notable changes to Portrait Generator will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-01-30

### Added
- Initial release of Portrait Generator
- AI-powered portrait generation using Google Gemini (gemini-exp-1206)
- Biographical research with gemini-2.0-flash-exp
- 4 portrait styles: BW, Sepia, Color, Painting
- Professional title overlays with semi-transparent bars
- Multi-criteria quality evaluation system
- Python API for programmatic use (`PortraitClient`, `generate_portrait`)
- REST API with FastAPI (5 endpoints: health, generate, batch, status, download)
- Command-line interface with 5 commands:
  - `portrait-generator generate` - Generate single portrait
  - `portrait-generator batch` - Generate multiple portraits
  - `portrait-generator status` - Check portrait status
  - `portrait-generator serve` - Start API server
  - `portrait-generator health-check` - System health check
- Comprehensive test suite (313+ unit tests, 90%+ coverage)
- Complete documentation with examples
- PyPI package support
- Conda package support
- Type hints throughout codebase
- Environment-based configuration
- Secure API key handling

### Features
- **Image Generation**: High-quality portrait generation with Google Gemini
- **Style Transformations**: Black & white, sepia tone, color, and painting styles
- **Overlay System**: Automatic title overlays with name and years
- **Quality Evaluation**: Technical, visual, style adherence, and historical accuracy checks
- **Batch Processing**: Generate multiple portraits in sequence
- **Skip Existing**: Automatic detection and skip of existing portraits
- **Error Handling**: Comprehensive error handling and logging
- **Time Tracking**: Generation time tracking and reporting

### Documentation
- Complete README with installation and usage examples
- API endpoint documentation
- Python API documentation
- CLI command documentation
- Architecture overview
- Implementation plan
- Type annotations and docstrings

### Testing
- 313+ unit tests
- 90%+ code coverage
- Integration tests
- End-to-end tests with real API calls
- Mock-based external API tests
- Test fixtures for realistic scenarios

### Package Distribution
- PyPI package: `pip install portrait-generator`
- Conda package: `conda install portrait-generator`
- Both conda-forge and custom channel support
- Entry points for CLI commands
- Python 3.10+ support

### Security
- Environment variable configuration
- API key validation
- No secrets in repository
- Comprehensive .gitignore
- Secure defaults

---

## Release Notes

### v1.0.0 - Initial Public Release

Portrait Generator v1.0.0 is production-ready with full features:

**Quick Start:**
```bash
# Install via pip
pip install portrait-generator

# Or via conda
conda install portrait-generator

# Set API key
export GOOGLE_API_KEY="your_api_key"

# Generate a portrait
portrait-generator generate "Alan Turing"

# Or use Python API
from portrait_generator import generate_portrait
result = generate_portrait("Marie Curie")
```

**Python API:**
```python
from portrait_generator import PortraitClient

client = PortraitClient(api_key="your_key")
result = client.generate("Claude Shannon", styles=["BW", "Color"])
print(f"Generated {len(result.files)} portraits")
```

**REST API:**
```bash
# Start server
portrait-generator serve

# Generate via API
curl -X POST "http://localhost:8000/api/v1/generate" \
  -H "Content-Type: application/json" \
  -d '{"subject_name": "Ada Lovelace"}'
```

**Documentation:**
- GitHub: https://github.com/davidlary/PortraitGenerator
- PyPI: https://pypi.org/project/portrait-generator/
- Docs: https://portrait-generator.readthedocs.io

**Requirements:**
- Python 3.10+
- Google Gemini API key
- ~100MB disk space for dependencies

**License:** MIT

---

[1.0.0]: https://github.com/davidlary/PortraitGenerator/releases/tag/v1.0.0
