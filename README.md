# Portrait Generator API

> Generate historically accurate, publication-quality portrait images using Google Gemini

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Features

- 🎨 **Four Portrait Styles**: BW, Sepia, Color, Photorealistic Painting
- 🔬 **Historical Accuracy**: Deep research ensures authentic representation
- ✅ **Self-Evaluation**: Quality assurance with automated validation
- 🚀 **RESTful API**: Easy integration via FastAPI
- 📊 **90%+ Test Coverage**: Comprehensive unit, integration, and visual tests
- 🔒 **Secure**: Environment-based credentials only
- 📝 **Fully Documented**: Complete API documentation and examples

---

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/davidlary/PortraitGenerator.git
cd PortraitGenerator

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -e .

# For development
pip install -r requirements-dev.txt
```

### Configuration

Create a `.env` file:

```bash
# Copy example
cp .env.example .env

# Edit with your API key
# GOOGLE_API_KEY=your_gemini_api_key_here
```

### Basic Usage

```python
from portrait_generator import PortraitGenerator
from portrait_generator.config import Settings

# Initialize
settings = Settings()
generator = PortraitGenerator.from_settings(settings)

# Generate portrait
result = generator.generate_portrait("Albert Einstein")

# Check results
print(f"Generated {len(result.files)} portraits")
for style, filepath in result.files.items():
    print(f"  {style}: {filepath}")
```

### API Server

```bash
# Start API server
uvicorn portrait_generator.api.server:app --reload

# Access docs at http://localhost:8000/docs
```

---

## API Usage

### Generate Single Portrait

```bash
curl -X POST "http://localhost:8000/api/v1/generate" \
  -H "Content-Type: application/json" \
  -d '{"subject_name": "Marie Curie"}'
```

### Generate Specific Styles

```bash
curl -X POST "http://localhost:8000/api/v1/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "subject_name": "Ada Lovelace",
    "styles": ["BW", "Sepia"]
  }'
```

### Check Status

```bash
curl "http://localhost:8000/api/v1/status/Albert%20Einstein"
```

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

```bash
# Run all tests with coverage
pytest tests/ --cov=src --cov-report=html --cov-report=term

# Run specific test types
pytest tests/unit/ -v           # Unit tests
pytest tests/integration/ -v    # Integration tests
pytest tests/visual/ -v         # Visual inspection tests

# Check coverage
open htmlcov/index.html
```

**Coverage Target**: 90%+ overall

---

## Development

### Project Structure

```
PortraitGenerator/
├── src/portrait_generator/     # Main package
│   ├── api/                     # FastAPI application
│   ├── core/                    # Core modules
│   ├── utils/                   # Utilities
│   └── config/                  # Configuration
├── tests/                       # Test suite
│   ├── unit/                    # Unit tests
│   ├── integration/             # Integration tests
│   ├── visual/                  # Visual tests
│   └── fixtures/                # Test data
├── docs/                        # Documentation
├── examples/                    # Usage examples
└── output/                      # Generated portraits
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/
```

---

## Configuration

### Environment Variables

- `GOOGLE_API_KEY`: **Required**. Google Gemini API key
- `GEMINI_MODEL`: Model name (default: `gemini-exp-1206`)
- `IMAGE_RESOLUTION`: Resolution as `width,height` (default: `1024,1024`)
- `OUTPUT_DIR`: Output directory (default: `./output`)
- `LOG_LEVEL`: Logging level (default: `INFO`)

### Settings File

Edit `src/portrait_generator/config/settings.py` or override via `.env` file.

---

## Examples

See `/examples` directory for:
- Basic portrait generation
- Batch processing
- Custom styles
- API integration

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

Last Updated: January 30, 2026

---

## Documentation

- [API Documentation](docs/API.md)
- [Architecture Guide](docs/ARCHITECTURE.md)
- [Implementation Plan](ImplementationPlan.md)

---

For questions or issues, please open an issue on GitHub.
