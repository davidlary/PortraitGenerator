# Portrait Generator API - Implementation Plan

**Version**: 1.0.0
**Date**: January 29, 2026
**Author**: Claude Sonnet 4.5
**Status**: Planning Phase

---

## Executive Summary

This implementation plan details the development of a robust, extensible, modular Portrait Generator API that creates historically accurate, aesthetically beautiful portrait images with comprehensive testing, documentation, and autonomous execution capabilities.

### Key Objectives

1. **Four Portrait Versions**: BW, Sepia, Color, Photorealistic Painting per subject
2. **Historical Accuracy**: Deep research and self-evaluation for each portrait
3. **Professional Quality**: Publication-grade images with title overlays
4. **Autonomous Operation**: Fully tested, documented, zero-tolerance for failures
5. **Multi-Platform**: Claude Code, Gemini Antigravity, GitHub CLI compatibility

### Technology Stack

- **Image Generation**: Google Gemini Nano Banana Pro (`gemini-3-pro-image-preview`) exclusively
- **Image Processing**: Pillow (PIL) for overlays and transformations
- **Research**: Google Gemini for biographical data and prompt optimization
- **Testing**: pytest with 90%+ coverage, visual inspection framework
- **API**: RESTful FastAPI with comprehensive validation
- **Version Control**: Git + GitHub with automated workflows

---

## Phase 1: Foundation & Architecture (Days 1-2)

### 1.1 Project Structure Setup

```
PortraitGenerator/
├── src/
│   └── portrait_generator/
│       ├── __init__.py
│       ├── __version__.py
│       ├── api/
│       │   ├── __init__.py
│       │   ├── server.py          # FastAPI server
│       │   ├── models.py          # Pydantic models
│       │   └── routes.py          # API endpoints
│       ├── core/
│       │   ├── __init__.py
│       │   ├── generator.py       # PortraitGenerator class
│       │   ├── researcher.py      # BiographicalResearcher class
│       │   ├── evaluator.py       # QualityEvaluator class
│       │   └── overlay.py         # TitleOverlayEngine class
│       ├── utils/
│       │   ├── __init__.py
│       │   ├── gemini_client.py   # Gemini API client
│       │   ├── image_utils.py     # Image transformation utilities
│       │   └── validators.py      # Input validation
│       └── config/
│           ├── __init__.py
│           └── settings.py        # Configuration management
├── tests/
│   ├── __init__.py
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_generator.py
│   │   ├── test_researcher.py
│   │   ├── test_evaluator.py
│   │   ├── test_overlay.py
│   │   └── test_gemini_client.py
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── test_api.py
│   │   └── test_end_to_end.py
│   ├── visual/
│   │   ├── __init__.py
│   │   ├── test_visual_inspection.py
│   │   └── visual_regression.py
│   └── fixtures/
│       ├── __init__.py
│       ├── sample_subjects.json
│       └── expected_outputs/
├── docs/
│   ├── API.md                     # API documentation
│   ├── ARCHITECTURE.md            # System architecture
│   ├── CONTRIBUTING.md            # Contribution guidelines
│   └── TROUBLESHOOTING.md         # Common issues
├── examples/
│   ├── basic_usage.py
│   ├── batch_generation.py
│   └── custom_styles.py
├── output/                        # Generated portraits (gitignored)
├── .github/
│   └── workflows/
│       ├── tests.yml              # CI/CD pipeline
│       └── deploy.yml             # Deployment
├── .gitignore
├── README.md
├── requirements.txt
├── requirements-dev.txt
├── setup.py
├── pyproject.toml
├── pytest.ini
└── LICENSE

```

**Deliverables**:
- ✅ Complete directory structure
- ✅ All `__init__.py` files with proper imports
- ✅ `.gitignore` configured (secrets, output/, `__pycache__`, etc.)
- ✅ Basic README.md with project overview

### 1.2 Dependency Management

**Core Dependencies** (`requirements.txt`):
```txt
# Google Gemini (CRITICAL: gemini-3-pro-image-preview model)
google-genai>=0.2.0

# Image Processing
pillow>=10.2.0

# API Framework
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
pydantic>=2.6.0
pydantic-settings>=2.1.0

# HTTP Client
requests>=2.31.0
httpx>=0.26.0

# Utilities
python-dotenv>=1.0.0
click>=8.1.0
```

**Development Dependencies** (`requirements-dev.txt`):
```txt
# Testing
pytest>=8.0.0
pytest-cov>=4.1.0
pytest-asyncio>=0.23.0
pytest-mock>=3.12.0

# Visual Testing
pytest-visual>=1.0.0
pillow-compare>=1.0.0

# Code Quality
black>=24.1.0
ruff>=0.1.0
mypy>=1.8.0

# Documentation
mkdocs>=1.5.0
mkdocs-material>=9.5.0
```

**Installation Strategy**:
```bash
# 1. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Upgrade pip
pip install --upgrade pip

# 3. Install production dependencies
pip install -r requirements.txt

# 4. Install development dependencies
pip install -r requirements-dev.txt

# 5. Install package in editable mode
pip install -e .
```

**Deliverables**:
- ✅ `requirements.txt` with pinned versions
- ✅ `requirements-dev.txt` with testing tools
- ✅ `setup.py` with package metadata
- ✅ Automated installation verification script
- ✅ Zero optional dependencies (all explicit)

### 1.3 Configuration Management

**Environment Variables** (`.env.example`):
```bash
# Google Gemini API
GOOGLE_API_KEY=your_gemini_api_key_here

# GitHub Credentials (for CI/CD)
GITHUB_TOKEN=your_github_token
GITHUB_USER=your_github_username
GITHUB_EMAIL=your_github_email

# Application Settings
LOG_LEVEL=INFO
OUTPUT_DIR=./output
MAX_CONCURRENT_REQUESTS=5
```

**Configuration Class** (`src/portrait_generator/config/settings.py`):
```python
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    # API Keys (from environment)
    google_api_key: str

    # Gemini Model Configuration
    gemini_model: str = "gemini-3-pro-image-preview"

    # Image Settings
    image_resolution: tuple[int, int] = (1024, 1024)
    portrait_quality: int = 95  # JPEG quality

    # Output Settings
    output_dir: Path = Path("./output")
    save_prompts: bool = True

    # Testing Settings
    visual_inspection_enabled: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
```

**Deliverables**:
- ✅ `.env.example` template
- ✅ `settings.py` with Pydantic validation
- ✅ Configuration loading verification
- ✅ Security audit (no hardcoded secrets)

---

## Phase 2: Core Components (Days 3-5)

### 2.1 Gemini Client Module

**File**: `src/portrait_generator/utils/gemini_client.py`

**Responsibilities**:
1. Initialize Google Gemini client with API key
2. Generate images using `gemini-3-pro-image-preview` model
3. Handle API errors and retries
4. Validate responses
5. Return PIL Image objects

**Key Methods**:
```python
class GeminiImageClient:
    def __init__(self, api_key: str)
    def generate_image(
        self,
        prompt: str,
        aspect_ratio: str = "3:4",
        style: str = "photorealistic"
    ) -> Image.Image
    def validate_connection(self) -> bool
```

**Testing Requirements**:
- ✅ Unit tests for initialization
- ✅ Mock API responses
- ✅ Error handling (rate limits, invalid keys)
- ✅ Connection validation
- ✅ 95%+ coverage

**Deliverables**:
- ✅ Fully tested GeminiImageClient class
- ✅ Retry logic with exponential backoff
- ✅ Comprehensive error messages
- ✅ API usage logging

### 2.2 Biographical Researcher Module

**File**: `src/portrait_generator/core/researcher.py`

**Responsibilities**:
1. Research subject's biographical data
2. Determine birth/death years
3. Gather physical appearance details (for prompt engineering)
4. Identify historical era and context
5. Compile accuracy checklist

**Key Methods**:
```python
class BiographicalResearcher:
    def __init__(self, gemini_client: GeminiClient)

    def research_subject(self, name: str) -> SubjectData:
        """
        Returns:
            SubjectData(
                name: str,
                birth_year: int,
                death_year: Optional[int],
                era: str,
                appearance_notes: List[str],
                historical_context: str,
                reference_sources: List[str]
            )
        """

    def format_years(self, birth: int, death: Optional[int]) -> str:
        """Returns '1912-1954' or '1947-Present'"""

    def validate_data(self, data: SubjectData) -> ValidationResult
```

**Research Strategy**:
1. Query Gemini with specialized research prompt
2. Cross-reference multiple sources
3. Extract physical appearance details
4. Identify clothing/styling appropriate to era
5. Return structured data with confidence scores

**Testing Requirements**:
- ✅ Unit tests with mock Gemini responses
- ✅ Historical figure fixtures (Einstein, Marie Curie, etc.)
- ✅ Edge cases (recently deceased, still living, ancient figures)
- ✅ Data validation tests
- ✅ 90%+ coverage

**Deliverables**:
- ✅ BiographicalResearcher class
- ✅ SubjectData Pydantic model
- ✅ Comprehensive test suite
- ✅ Documentation with examples

### 2.3 Title Overlay Engine Module

**File**: `src/portrait_generator/core/overlay.py`

**Responsibilities**:
1. Add semi-transparent title bar to bottom of image
2. Render subject name (Line 1)
3. Render years (Line 2)
4. Ensure text is centered and legible
5. Handle different image sizes

**Key Methods**:
```python
class TitleOverlayEngine:
    def add_overlay(
        self,
        image: Image.Image,
        name: str,
        years: str,
        bar_opacity: float = 0.65,
        font_path: Optional[str] = None
    ) -> Image.Image

    def calculate_font_size(
        self,
        image_height: int,
        bar_height_ratio: float = 0.15
    ) -> tuple[int, int]:  # (name_size, years_size)

    def validate_overlay(
        self,
        image: Image.Image
    ) -> bool:
        """Visual validation that overlay is present and legible"""
```

**Overlay Specifications** (from Examples):
- Bar height: 15% of image height
- Bar color: Black with 65% opacity (RGBA: 0,0,0,166)
- Name font: Helvetica, size = bar_height * 0.4, white
- Years font: Helvetica, size = name_font * 0.7, light gray (200,200,200)
- Text alignment: Horizontally centered
- Vertical spacing: Name at 20% from top of bar, Years below with 5px gap

**Testing Requirements**:
- ✅ Unit tests for font size calculation
- ✅ Visual tests comparing to reference images
- ✅ Edge cases (very long names, different image sizes)
- ✅ Font availability tests (fallback to default)
- ✅ Pixel-perfect comparison tests
- ✅ 95%+ coverage

**Deliverables**:
- ✅ TitleOverlayEngine class
- ✅ Font loading with graceful fallbacks
- ✅ Visual regression test suite
- ✅ Example output validation

### 2.4 Portrait Generator Core Module

**File**: `src/portrait_generator/core/generator.py`

**Responsibilities**:
1. Orchestrate complete portrait generation workflow
2. Generate 4 versions (BW, Sepia, Color, Painting)
3. Apply title overlays
4. Save images and prompts
5. Handle errors gracefully

**Key Methods**:
```python
class PortraitGenerator:
    def __init__(
        self,
        gemini_client: GeminiImageClient,
        researcher: BiographicalResearcher,
        overlay_engine: TitleOverlayEngine,
        output_dir: Path
    )

    def generate_portrait(
        self,
        subject_name: str,
        force_regenerate: bool = False
    ) -> PortraitResult:
        """
        Returns:
            PortraitResult(
                subject: str,
                files: Dict[str, Path],  # {'BW': path, 'Sepia': path, ...}
                prompts: Dict[str, Path],
                metadata: SubjectData,
                validation_passed: bool
            )
        """

    def _generate_version(
        self,
        subject_data: SubjectData,
        style: str,  # 'BW', 'Sepia', 'Color', 'Painting'
        filename: str
    ) -> Path

    def _create_prompt(
        self,
        subject_data: SubjectData,
        style: str
    ) -> str:
        """Create optimized prompt for specific style"""

    def _apply_style_transformation(
        self,
        base_image: Image.Image,
        style: str
    ) -> Image.Image:
        """Apply BW, Sepia, or other transformations"""
```

**Style Specifications**:

1. **Black & White**:
   - Convert to grayscale
   - Enhance contrast
   - Filename: `FirstNameLastName_BW.png`

2. **Sepia**:
   - Apply sepia tone filter
   - Warm, vintage aesthetic
   - Filename: `FirstNameLastName_Sepia.png`

3. **Color**:
   - Full color photorealistic portrait
   - Natural skin tones
   - Filename: `FirstNameLastName_Color.png`

4. **Photorealistic Painting**:
   - Oil painting style with visible brushstrokes
   - Highly detailed
   - Filename: `FirstNameLastName_Painting.png`

**Prompt Engineering Strategy**:
```python
PROMPT_TEMPLATE = """
Generate a {style} portrait of {subject_name}.

SUBJECT DETAILS:
{appearance_notes}

HISTORICAL CONTEXT:
Era: {era}
Appropriate clothing: {clothing_style}

COMPOSITION:
- Extreme close-up, head and shoulders only
- Face fills 85% of frame
- Vertical aspect ratio (3:4)
- Minimal background

STYLE REQUIREMENTS:
{style_specific_instructions}

QUALITY:
- Publication-grade photorealism
- Historically accurate details
- Professional lighting
- No text or borders
"""
```

**Testing Requirements**:
- ✅ Unit tests for each method
- ✅ Integration tests for full workflow
- ✅ Mock Gemini responses for reproducibility
- ✅ File existence and naming validation
- ✅ Image quality checks (resolution, format)
- ✅ 90%+ coverage

**Deliverables**:
- ✅ PortraitGenerator class with full workflow
- ✅ All 4 style transformations implemented
- ✅ Comprehensive test suite
- ✅ Example outputs for validation

### 2.5 Quality Evaluator Module

**File**: `src/portrait_generator/core/evaluator.py`

**Responsibilities**:
1. Self-evaluate generated portraits for quality
2. Verify historical accuracy
3. Check technical requirements (resolution, overlay, etc.)
4. Provide detailed feedback
5. Determine pass/fail status

**Key Methods**:
```python
class QualityEvaluator:
    def __init__(self, gemini_client: GeminiClient)

    def evaluate_portrait(
        self,
        image: Image.Image,
        subject_data: SubjectData,
        style: str
    ) -> EvaluationResult:
        """
        Returns:
            EvaluationResult(
                passed: bool,
                scores: Dict[str, float],  # 0.0-1.0 per criterion
                feedback: List[str],
                issues: List[str],
                recommendations: List[str]
            )
        """

    def check_technical_requirements(
        self,
        image: Image.Image,
        expected_resolution: tuple[int, int]
    ) -> Dict[str, bool]:
        """Check resolution, format, overlay presence"""

    def check_visual_quality(
        self,
        image: Image.Image,
        style: str
    ) -> float:
        """Use Gemini to assess visual quality (0.0-1.0)"""

    def check_historical_accuracy(
        self,
        image: Image.Image,
        subject_data: SubjectData
    ) -> float:
        """Use Gemini to assess historical accuracy"""
```

**Evaluation Criteria**:

1. **Technical Requirements** (Pass/Fail):
   - ✅ Correct resolution (1024x1024 or specified)
   - ✅ Title overlay present and legible
   - ✅ Correct filename format
   - ✅ Prompt markdown file exists
   - ✅ Image quality >= 95 (JPEG)

2. **Visual Quality** (0.0-1.0 score):
   - Composition (face fills 85% of frame)
   - Lighting quality
   - Detail level
   - Style adherence (BW/Sepia/Color/Painting)
   - No artifacts or glitches

3. **Historical Accuracy** (0.0-1.0 score):
   - Appropriate era clothing/styling
   - Realistic appearance for time period
   - Age-appropriate features
   - Cultural context accuracy

**Pass Threshold**: All technical requirements + visual quality >= 0.85 + historical accuracy >= 0.80

**Testing Requirements**:
- ✅ Unit tests for each evaluation criterion
- ✅ Integration tests with sample portraits
- ✅ Edge cases (low quality, inaccurate, missing overlay)
- ✅ Mock Gemini responses for consistency
- ✅ 90%+ coverage

**Deliverables**:
- ✅ QualityEvaluator class
- ✅ Comprehensive scoring system
- ✅ Detailed feedback generation
- ✅ Test suite with fixtures

---

## Phase 3: API Layer (Days 6-7)

### 3.1 API Models

**File**: `src/portrait_generator/api/models.py`

**Pydantic Models**:

```python
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, List
from pathlib import Path

class PortraitRequest(BaseModel):
    """API request model"""
    subject_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Full name of the subject"
    )
    force_regenerate: bool = Field(
        default=False,
        description="Regenerate even if files exist"
    )
    styles: Optional[List[str]] = Field(
        default=None,
        description="Specific styles to generate (defaults to all 4)"
    )

    @validator('styles')
    def validate_styles(cls, v):
        if v is not None:
            valid_styles = {'BW', 'Sepia', 'Color', 'Painting'}
            if not all(s in valid_styles for s in v):
                raise ValueError(f"Invalid styles. Must be from: {valid_styles}")
        return v

class SubjectData(BaseModel):
    """Biographical data model"""
    name: str
    birth_year: int
    death_year: Optional[int]
    era: str
    appearance_notes: List[str]
    historical_context: str
    reference_sources: List[str]

class EvaluationResult(BaseModel):
    """Quality evaluation result"""
    passed: bool
    scores: Dict[str, float]
    feedback: List[str]
    issues: List[str]
    recommendations: List[str]

class PortraitResult(BaseModel):
    """API response model"""
    subject: str
    files: Dict[str, str]  # {'BW': '/path/to/file.png', ...}
    prompts: Dict[str, str]
    metadata: SubjectData
    evaluation: Dict[str, EvaluationResult]
    generation_time_seconds: float
    success: bool
    errors: List[str]
```

**Deliverables**:
- ✅ All Pydantic models with validation
- ✅ Request/response schemas
- ✅ Comprehensive field documentation
- ✅ Unit tests for validation

### 3.2 API Endpoints

**File**: `src/portrait_generator/api/routes.py`

**Endpoints**:

```python
from fastapi import APIRouter, HTTPException, BackgroundTasks
from .models import PortraitRequest, PortraitResult

router = APIRouter()

@router.post("/generate", response_model=PortraitResult)
async def generate_portrait(request: PortraitRequest):
    """
    Generate portrait(s) for a subject.

    Returns complete result with all files, prompts, and evaluation.
    """
    pass

@router.get("/status/{subject_name}", response_model=dict)
async def get_status(subject_name: str):
    """
    Check if portraits exist for a subject.

    Returns:
        {
            "exists": bool,
            "files": List[str],
            "generated_at": str (ISO timestamp)
        }
    """
    pass

@router.post("/batch", response_model=List[PortraitResult])
async def generate_batch(subjects: List[str], background_tasks: BackgroundTasks):
    """
    Generate portraits for multiple subjects.

    Can run in background for large batches.
    """
    pass

@router.get("/health")
async def health_check():
    """
    Health check endpoint.

    Verifies:
    - API is running
    - Gemini client is configured
    - Output directory is writable
    """
    pass
```

**Error Handling**:
```python
@router.exception_handler(ValueError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc)}
    )

@router.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
```

**Testing Requirements**:
- ✅ Unit tests for each endpoint
- ✅ Integration tests with test client
- ✅ Error handling tests
- ✅ Authentication tests (if implemented)
- ✅ 90%+ coverage

**Deliverables**:
- ✅ Complete API routes
- ✅ Comprehensive error handling
- ✅ OpenAPI documentation (auto-generated)
- ✅ Test suite

### 3.3 API Server

**File**: `src/portrait_generator/api/server.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import router
from ..config.settings import Settings

def create_app() -> FastAPI:
    """Factory function to create FastAPI app"""
    settings = Settings()

    app = FastAPI(
        title="Portrait Generator API",
        description="Generate historically accurate portrait images",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(router, prefix="/api/v1")

    # Startup event
    @app.on_event("startup")
    async def startup_event():
        # Initialize clients, check connections
        pass

    # Shutdown event
    @app.on_event("shutdown")
    async def shutdown_event():
        # Cleanup resources
        pass

    return app

if __name__ == "__main__":
    import uvicorn
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Testing Requirements**:
- ✅ Startup/shutdown tests
- ✅ CORS configuration tests
- ✅ Integration tests with full server
- ✅ 85%+ coverage

**Deliverables**:
- ✅ FastAPI application
- ✅ Uvicorn server configuration
- ✅ Middleware setup
- ✅ Deployment-ready code

---

## Phase 4: Testing Framework (Days 8-10)

### 4.1 Unit Tests

**Location**: `tests/unit/`

**Test Files**:
1. `test_gemini_client.py`: GeminiImageClient tests
2. `test_researcher.py`: BiographicalResearcher tests
3. `test_overlay.py`: TitleOverlayEngine tests
4. `test_generator.py`: PortraitGenerator tests
5. `test_evaluator.py`: QualityEvaluator tests
6. `test_api_models.py`: Pydantic model validation tests

**Coverage Target**: 90%+ overall, 95%+ for critical paths

**Test Strategy**:
```python
# Example: test_generator.py
import pytest
from unittest.mock import Mock, patch
from portrait_generator.core.generator import PortraitGenerator

@pytest.fixture
def mock_gemini_client():
    client = Mock()
    client.generate_image.return_value = create_test_image()
    return client

@pytest.fixture
def mock_researcher():
    researcher = Mock()
    researcher.research_subject.return_value = create_test_subject_data()
    return researcher

def test_generate_portrait_success(mock_gemini_client, mock_researcher):
    """Test successful portrait generation"""
    generator = PortraitGenerator(
        gemini_client=mock_gemini_client,
        researcher=mock_researcher,
        overlay_engine=Mock(),
        output_dir=Path("/tmp/test")
    )

    result = generator.generate_portrait("Albert Einstein")

    assert result.success
    assert len(result.files) == 4
    assert all(Path(f).exists() for f in result.files.values())

def test_generate_portrait_api_failure(mock_gemini_client, mock_researcher):
    """Test graceful handling of API failures"""
    mock_gemini_client.generate_image.side_effect = Exception("API Error")

    generator = PortraitGenerator(...)
    result = generator.generate_portrait("Albert Einstein")

    assert not result.success
    assert "API Error" in result.errors
```

**Deliverables**:
- ✅ Complete unit test suite
- ✅ 90%+ coverage
- ✅ All edge cases covered
- ✅ Fast execution (<30 seconds)

### 4.2 Integration Tests

**Location**: `tests/integration/`

**Test Files**:
1. `test_api.py`: Full API workflow tests
2. `test_end_to_end.py`: Complete generation pipeline tests

**Test Strategy**:
```python
# Example: test_end_to_end.py
import pytest
from portrait_generator import create_app
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)

def test_full_portrait_generation(client):
    """Test complete workflow from API call to files"""
    response = client.post(
        "/api/v1/generate",
        json={"subject_name": "Marie Curie"}
    )

    assert response.status_code == 200
    result = response.json()

    # Verify structure
    assert result["success"]
    assert len(result["files"]) == 4

    # Verify files exist
    for style, filepath in result["files"].items():
        assert Path(filepath).exists()
        assert Path(filepath).stat().st_size > 0

    # Verify prompts
    for style, prompt_path in result["prompts"].items():
        assert Path(prompt_path).exists()
        content = Path(prompt_path).read_text()
        assert "Marie Curie" in content

    # Verify evaluation
    for style, eval_result in result["evaluation"].items():
        assert eval_result["passed"]
        assert eval_result["scores"]["visual_quality"] >= 0.85

def test_batch_generation(client):
    """Test batch portrait generation"""
    subjects = ["Alan Turing", "Ada Lovelace", "Grace Hopper"]

    response = client.post(
        "/api/v1/batch",
        json=subjects
    )

    assert response.status_code == 200
    results = response.json()

    assert len(results) == 3
    assert all(r["success"] for r in results)
```

**Deliverables**:
- ✅ Complete integration test suite
- ✅ API endpoint testing
- ✅ E2E workflow validation
- ✅ Performance benchmarks

### 4.3 Visual Testing Framework

**Location**: `tests/visual/`

**Purpose**: Ensure visual quality through automated inspection

**Test Strategy**:
```python
# Example: test_visual_inspection.py
import pytest
from PIL import Image
from portrait_generator.core.evaluator import QualityEvaluator

def test_overlay_presence():
    """Verify title overlay is present and correctly positioned"""
    image = Image.open("test_outputs/Einstein_BW.png")

    # Check bottom 15% has dark background
    width, height = image.size
    bar_region = image.crop((0, int(height * 0.85), width, height))

    # Get average color of region (should be dark)
    pixels = list(bar_region.getdata())
    avg_brightness = sum(sum(p[:3]) / 3 for p in pixels) / len(pixels)

    assert avg_brightness < 100, "Overlay bar should be dark"

def test_text_legibility():
    """Verify text is readable and correctly positioned"""
    image = Image.open("test_outputs/Einstein_BW.png")

    # Use OCR to verify text is readable
    import pytesseract
    text = pytesseract.image_to_string(image)

    assert "Einstein" in text
    assert any(year in text for year in ["1879", "1955"])

def test_visual_regression():
    """Compare generated image to reference"""
    from PIL import ImageChops

    generated = Image.open("test_outputs/Einstein_BW.png")
    reference = Image.open("tests/fixtures/expected/Einstein_BW.png")

    # Calculate difference
    diff = ImageChops.difference(generated, reference)

    # Allow small differences (compression artifacts, etc.)
    bbox = diff.getbbox()
    if bbox:
        diff_area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
        total_area = generated.size[0] * generated.size[1]
        diff_ratio = diff_area / total_area

        assert diff_ratio < 0.05, "Images differ by more than 5%"

@pytest.mark.parametrize("subject,style", [
    ("Einstein", "BW"),
    ("Einstein", "Sepia"),
    ("Einstein", "Color"),
    ("Einstein", "Painting"),
])
def test_style_consistency(subject, style):
    """Verify each style has correct visual characteristics"""
    image = Image.open(f"test_outputs/{subject}_{style}.png")

    if style == "BW":
        # Check image is grayscale
        assert image.mode in ["L", "RGB"]
        if image.mode == "RGB":
            # Verify R=G=B for all pixels
            pixels = list(image.getdata())
            grayscale_pixels = [p[0] == p[1] == p[2] for p in pixels[:100]]
            assert all(grayscale_pixels)

    elif style == "Sepia":
        # Check warm tones (R > G > B)
        pixels = list(image.getdata())
        warm_pixels = [p[0] > p[1] > p[2] for p in pixels[:100]]
        assert sum(warm_pixels) / len(warm_pixels) > 0.8
```

**Visual Test Requirements**:
- ✅ Overlay presence and positioning
- ✅ Text legibility (OCR verification)
- ✅ Style consistency (BW, Sepia, Color, Painting)
- ✅ Resolution verification
- ✅ Visual regression tests
- ✅ No artifacts or glitches

**Deliverables**:
- ✅ Visual testing framework
- ✅ Reference images for comparison
- ✅ OCR-based text verification
- ✅ Style-specific validation

### 4.4 Test Configuration

**File**: `pytest.ini`

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Coverage settings
addopts =
    --cov=src/portrait_generator
    --cov-report=html
    --cov-report=term
    --cov-fail-under=90
    --verbose
    --strict-markers
    --tb=short

# Markers
markers =
    unit: Unit tests
    integration: Integration tests
    visual: Visual inspection tests
    slow: Slow-running tests (>5 seconds)
    api: API endpoint tests

# Test discovery
norecursedirs = .git .tox dist build *.egg .venv cpf

# Timeout
timeout = 300

# Asyncio mode
asyncio_mode = auto
```

**Deliverables**:
- ✅ pytest.ini configuration
- ✅ Coverage reporting setup
- ✅ Test markers for selective execution
- ✅ Performance constraints

---

## Phase 5: Documentation (Days 11-12)

### 5.1 README.md

**Structure**:
```markdown
# Portrait Generator API

> Generate historically accurate, publication-quality portrait images

[![Tests](badge)]
[![Coverage](badge)]
[![Python 3.10+](badge)]

## Features

- 🎨 Four portrait styles: BW, Sepia, Color, Painting
- 🔬 Historical accuracy through deep research
- ✅ Self-evaluation and quality assurance
- 🚀 RESTful API for easy integration
- 📊 90%+ test coverage
- 🔒 Secure (environment-based credentials)

## Quick Start

### Installation
[Step-by-step instructions]

### Basic Usage
[Code examples]

### API Documentation
[Link to full API docs]

## Examples
[Screenshots of generated portraits]

## Architecture
[High-level overview diagram]

## Testing
[How to run tests]

## Contributing
[Guidelines]

## License
[License info]
```

**Deliverables**:
- ✅ Comprehensive README
- ✅ Code examples
- ✅ Screenshots
- ✅ Badges (tests, coverage, version)

### 5.2 API Documentation

**File**: `docs/API.md`

**Contents**:
1. Authentication
2. Endpoint reference
3. Request/response schemas
4. Error codes
5. Rate limiting
6. Examples

**Auto-generated OpenAPI docs** via FastAPI:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

**Deliverables**:
- ✅ Complete API documentation
- ✅ Request/response examples
- ✅ Error handling guide
- ✅ Interactive API docs

### 5.3 Architecture Documentation

**File**: `docs/ARCHITECTURE.md`

**Contents**:
```markdown
# Architecture

## System Overview
[Diagram of components]

## Core Components

### 1. Gemini Client
[Purpose, responsibilities, interfaces]

### 2. Biographical Researcher
[Purpose, responsibilities, interfaces]

### 3. Portrait Generator
[Purpose, responsibilities, interfaces]

### 4. Quality Evaluator
[Purpose, responsibilities, interfaces]

### 5. API Layer
[Purpose, responsibilities, interfaces]

## Data Flow
[Sequence diagrams]

## Design Decisions
[Key architectural choices and rationale]

## Future Enhancements
[Planned improvements]
```

**Deliverables**:
- ✅ Architecture documentation
- ✅ Component diagrams
- ✅ Sequence diagrams
- ✅ Design decision log

### 5.4 Code Documentation

**Docstring Standards** (Google Style):
```python
def generate_portrait(
    self,
    subject_name: str,
    force_regenerate: bool = False
) -> PortraitResult:
    """Generate portrait images for a historical figure.

    Creates four versions (BW, Sepia, Color, Painting) with title overlays
    and performs quality evaluation on each.

    Args:
        subject_name: Full name of the subject (e.g., "Albert Einstein")
        force_regenerate: If True, regenerate even if files exist

    Returns:
        PortraitResult containing file paths, prompts, metadata, and evaluation

    Raises:
        ValueError: If subject_name is invalid
        APIError: If Gemini API fails
        IOError: If unable to write output files

    Examples:
        >>> generator = PortraitGenerator(...)
        >>> result = generator.generate_portrait("Marie Curie")
        >>> print(result.files["BW"])
        '/output/MarieCurie_BW.png'
    """
```

**Deliverables**:
- ✅ All public APIs documented
- ✅ Type hints on all functions
- ✅ Examples in docstrings
- ✅ Auto-generated API reference

---

## Phase 6: CI/CD & Deployment (Day 13)

### 6.1 GitHub Actions Workflow

**File**: `.github/workflows/tests.yml`

```yaml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v5
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
        pip install -e .

    - name: Run tests
      env:
        GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
      run: |
        pytest tests/ --cov=src --cov-report=xml --cov-report=term

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: true

    - name: Check coverage threshold
      run: |
        coverage report --fail-under=90
```

**Deliverables**:
- ✅ GitHub Actions CI pipeline
- ✅ Multi-Python version testing
- ✅ Coverage reporting
- ✅ Automated checks

### 6.2 Git Configuration

**File**: `.gitignore`

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
.venv/
venv/
ENV/
env/

# Testing
.pytest_cache/
.coverage
htmlcov/
*.cover
.hypothesis/

# IDEs
.vscode/
.idea/
*.swp
*.swo

# Project-specific
output/
*.png
*.jpg
*.jpeg
!tests/fixtures/**/*.png
!tests/fixtures/**/*.jpg

# Secrets
.env
*.key
credentials.json

# CPF
.cpf/logs/
.cpf/state/
```

**Deliverables**:
- ✅ Comprehensive .gitignore
- ✅ Secret protection
- ✅ Output file exclusion
- ✅ Test fixture inclusion

### 6.3 GitHub Repository Setup

**Initial Commit Strategy**:
```bash
# 1. Initialize git (if not already)
git init

# 2. Add remote
git remote add origin https://github.com/davidlary/PortraitGenerator.git

# 3. Create .gitignore
cp .gitignore.template .gitignore

# 4. Stage files (VERIFY no secrets!)
git add .
git status  # REVIEW carefully

# 5. Initial commit
git commit -m "Initial commit: Portrait Generator API v1.0.0

- Core modules: Generator, Researcher, Evaluator, Overlay
- RESTful API with FastAPI
- Comprehensive test suite (90%+ coverage)
- Visual testing framework
- Complete documentation

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# 6. Push to GitHub
git branch -M main
git push -u origin main
```

**Deliverables**:
- ✅ GitHub repository initialized
- ✅ Initial commit with full codebase
- ✅ No secrets committed
- ✅ README visible on GitHub

---

## Phase 7: Validation & Handoff (Day 14)

### 7.1 End-to-End Validation

**Test Subjects** (diverse set for validation):
1. **Historical Figure**: William of Ockham (1285-1347)
2. **Modern Figure (Deceased)**: Claude Shannon (1916-2001)
3. **Living Figure**: Geoffrey Hinton (1947-Present)
4. **Ancient Figure**: Aristotle (384 BC - 322 BC)
5. **Woman**: Marie Curie (1867-1934)

**Validation Checklist**:

For each subject:
- ✅ All 4 versions generated (BW, Sepia, Color, Painting)
- ✅ Title overlay present and legible
- ✅ Name matches subject
- ✅ Years are accurate
- ✅ Prompt markdown files exist
- ✅ Image resolution correct (1024x1024)
- ✅ File naming convention followed
- ✅ Quality evaluation passed
- ✅ Visual inspection passed
- ✅ No silent failures

**Automated Validation Script**:
```python
# validate_all.py
import sys
from pathlib import Path
from portrait_generator import PortraitGenerator

def validate_project():
    """Run comprehensive validation"""
    print("=" * 70)
    print("PORTRAIT GENERATOR - COMPREHENSIVE VALIDATION")
    print("=" * 70)

    test_subjects = [
        "William of Ockham",
        "Claude Shannon",
        "Geoffrey Hinton",
        "Aristotle",
        "Marie Curie"
    ]

    generator = PortraitGenerator.from_env()

    all_passed = True

    for subject in test_subjects:
        print(f"\n{'=' * 70}")
        print(f"Testing: {subject}")
        print("=" * 70)

        result = generator.generate_portrait(subject)

        # Check success
        if not result.success:
            print(f"❌ FAILED: {subject}")
            print(f"   Errors: {result.errors}")
            all_passed = False
            continue

        # Check files
        for style in ["BW", "Sepia", "Color", "Painting"]:
            filepath = result.files.get(style)
            if not filepath or not Path(filepath).exists():
                print(f"❌ Missing file: {style}")
                all_passed = False
            else:
                print(f"✅ {style}: {filepath}")

        # Check evaluation
        for style, eval_result in result.evaluation.items():
            if eval_result.passed:
                print(f"✅ {style} evaluation: PASSED")
            else:
                print(f"❌ {style} evaluation: FAILED")
                print(f"   Issues: {eval_result.issues}")
                all_passed = False

    print("\n" + "=" * 70)
    if all_passed:
        print("✅ ALL VALIDATION TESTS PASSED")
        return 0
    else:
        print("❌ VALIDATION FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(validate_project())
```

**Deliverables**:
- ✅ Validation script
- ✅ All test subjects pass
- ✅ Visual inspection complete
- ✅ Documentation verified

### 7.2 Performance Benchmarks

**Metrics to Collect**:
1. **Generation Time** (per portrait):
   - Research phase: < 10 seconds
   - Image generation (per style): < 30 seconds
   - Overlay application: < 1 second
   - Evaluation: < 15 seconds
   - **Total**: < 3 minutes per subject (all 4 versions)

2. **API Performance**:
   - Health check: < 100ms
   - Single portrait: < 3 minutes
   - Batch (10 subjects): < 30 minutes

3. **Resource Usage**:
   - Memory: < 2GB
   - Disk space (per subject): ~5MB

**Benchmark Script**:
```python
# benchmark.py
import time
from portrait_generator import PortraitGenerator

def benchmark():
    generator = PortraitGenerator.from_env()

    subject = "Test Subject"

    start = time.time()
    result = generator.generate_portrait(subject)
    elapsed = time.time() - start

    print(f"Total time: {elapsed:.2f}s")
    print(f"Per version: {elapsed/4:.2f}s")

    assert elapsed < 180, "Generation took too long"
    assert result.success, "Generation failed"

if __name__ == "__main__":
    benchmark()
```

**Deliverables**:
- ✅ Benchmark script
- ✅ Performance metrics documented
- ✅ Optimization opportunities identified

### 7.3 Final Checklist

**Code Quality**:
- ✅ All tests passing (pytest)
- ✅ Coverage >= 90%
- ✅ Type checking passing (mypy)
- ✅ Linting passing (ruff, black)
- ✅ No security vulnerabilities

**Documentation**:
- ✅ README.md complete
- ✅ API.md complete
- ✅ ARCHITECTURE.md complete
- ✅ All docstrings present
- ✅ Examples working

**Functionality**:
- ✅ All 4 portrait styles working
- ✅ Title overlays correct
- ✅ Research accurate
- ✅ Evaluation working
- ✅ API endpoints functional

**Deployment**:
- ✅ GitHub repository set up
- ✅ CI/CD pipeline working
- ✅ No secrets in repo
- ✅ .gitignore configured

**Testing**:
- ✅ Unit tests (90%+ coverage)
- ✅ Integration tests
- ✅ Visual tests
- ✅ API tests
- ✅ E2E validation

---

## Autonomous Execution Plan

### Execution Strategy

Once this plan is approved, implementation will proceed fully autonomously following this sequence:

**Day 1-2: Foundation**
1. Create project structure
2. Set up dependencies
3. Configure environment
4. Initialize git repository

**Day 3-5: Core Components**
1. Implement GeminiImageClient
2. Implement BiographicalResearcher
3. Implement TitleOverlayEngine
4. Implement PortraitGenerator
5. Implement QualityEvaluator
6. Unit test each component (90%+ coverage)

**Day 6-7: API Layer**
1. Implement API models
2. Implement API routes
3. Implement API server
4. Integration tests

**Day 8-10: Testing**
1. Complete unit test suite
2. Integration tests
3. Visual testing framework
4. Achieve 90%+ coverage

**Day 11-12: Documentation**
1. Write README
2. Write API docs
3. Write architecture docs
4. Code documentation

**Day 13: CI/CD**
1. Set up GitHub Actions
2. Configure git
3. Initial commit to GitHub

**Day 14: Validation**
1. E2E validation
2. Performance benchmarks
3. Final checklist
4. Handoff documentation

### Success Criteria

**Must Have**:
- ✅ All tests passing (pytest, 90%+ coverage)
- ✅ All 4 portrait styles working
- ✅ Title overlays accurate
- ✅ Visual inspection tests passing
- ✅ API functional
- ✅ Documentation complete
- ✅ GitHub repository active
- ✅ No secrets committed

**Quality Gates**:
1. Unit tests: 90%+ coverage, all passing
2. Integration tests: All passing
3. Visual tests: All passing
4. E2E validation: All test subjects pass
5. Performance: < 3 min per subject
6. Documentation: Complete and accurate

**Zero Tolerance**:
- Silent failures
- Missing tests
- Undocumented code
- Secrets in repository
- Optional dependencies without fallbacks

---

## Risk Mitigation

### Technical Risks

**Risk 1: Gemini API Model Name**
- **Issue**: `gemini-3-pro-image-preview` may not be the correct model name
- **Mitigation**:
  - Test model availability immediately
  - Document actual model name in code
  - Add model validation to startup checks
  - Fail fast with clear error message

**Risk 2: API Rate Limiting**
- **Issue**: Gemini may rate limit requests
- **Mitigation**:
  - Implement exponential backoff
  - Add retry logic (max 3 attempts)
  - Queue requests if needed
  - Monitor rate limit headers

**Risk 3: Image Quality Variation**
- **Issue**: Generated portraits may vary in quality
- **Mitigation**:
  - Implement QualityEvaluator with strict thresholds
  - Allow regeneration on failure
  - Log all evaluations for analysis
  - Maintain prompt templates for consistency

**Risk 4: Visual Testing Flakiness**
- **Issue**: Visual tests may have false positives/negatives
- **Mitigation**:
  - Use tolerance thresholds (5% difference allowed)
  - Multiple validation methods (OCR + pixel comparison)
  - Reference images for regression testing
  - Manual review option

### Process Risks

**Risk 5: Scope Creep**
- **Issue**: Additional features requested during development
- **Mitigation**:
  - Stick to this implementation plan
  - Document future enhancements separately
  - Complete core functionality first
  - Phase 2 for additional features

**Risk 6: Testing Time**
- **Issue**: Comprehensive testing may be time-consuming
- **Mitigation**:
  - Mock Gemini responses for unit tests
  - Use fixtures for integration tests
  - Parallel test execution
  - Optimize slow tests

---

## Future Enhancements (Phase 2)

Post-MVP features to consider:

1. **Additional Styles**:
   - Sketch/Drawing style
   - Watercolor style
   - Engraving style

2. **Advanced Features**:
   - Batch processing with progress tracking
   - Custom resolution support
   - Multiple aspect ratios
   - Style customization API

3. **Quality Improvements**:
   - Multiple generation attempts with best selection
   - A/B testing between prompts
   - User feedback integration
   - Model fine-tuning

4. **Scalability**:
   - Asynchronous processing
   - Job queue (Celery/RQ)
   - Caching layer (Redis)
   - CDN integration for serving

5. **User Features**:
   - Web UI for generation
   - Gallery view
   - Comparison tool
   - Export formats (PDF, SVG)

---

## Appendix

### A. Prompt Templates

**Base Portrait Prompt**:
```
Generate a {style} portrait of {subject_name}.

SUBJECT DETAILS:
- Era: {era}
- Birth: {birth_year}
- Death: {death_year}
- Historical Context: {context}
- Physical Appearance: {appearance_notes}

COMPOSITION:
- Extreme close-up, head and shoulders only
- Face fills 85% of frame
- Vertical aspect ratio (3:4)
- Minimal background with period-appropriate setting

STYLE: {style_specific_instructions}

QUALITY REQUIREMENTS:
- Publication-grade photorealism (or painting style)
- Historically accurate clothing and hairstyle
- Professional lighting
- No text, watermarks, or borders
- High detail in facial features
```

**Style-Specific Instructions**:

1. **Black & White**:
```
Classic black and white portrait photography. Deep contrast, dramatic lighting.
Reminiscent of Yousuf Karsh's iconic portraits. Rich tones, sharp focus.
```

2. **Sepia**:
```
Warm sepia tone photograph. Vintage aesthetic with slight vignetting.
Classic early photography style. Rich brown tones, soft focus on edges.
```

3. **Color**:
```
Full color photorealistic portrait. Natural skin tones, accurate hair color.
Professional studio lighting. Contemporary photography style.
```

4. **Photorealistic Painting**:
```
Hyper-detailed oil painting on canvas. Visible brushstrokes adding texture.
Classical portrait painting technique. Rich, layered colors. Painterly quality
while maintaining photographic detail. Style of John Singer Sargent or
modern hyperrealist portraiture.
```

### B. File Naming Convention

**Pattern**: `FirstNameLastName_Style.ext`

**Examples**:
- AlbertEinstein_BW.png
- MarieCurie_Sepia.png
- AlanTuring_Color.png
- AdaLovelace_Painting.png
- AlbertEinstein_BW_prompt.md

**Rules**:
1. Remove all spaces from name
2. Capitalize first letter of each name part
3. Style suffix: BW, Sepia, Color, Painting
4. Image extension: .png (PNG format)
5. Prompt extension: _prompt.md

### C. Quality Evaluation Rubric

**Technical Requirements** (Pass/Fail):
| Criterion | Pass Condition |
|-----------|----------------|
| Resolution | Exactly 1024x1024 pixels |
| Format | PNG with >= 95% quality |
| Overlay Present | Dark bar at bottom 15% |
| Name Visible | OCR detects subject name |
| Years Visible | OCR detects birth/death years |
| Prompt File | Markdown file exists |

**Visual Quality** (0.0-1.0):
| Criterion | Weight | Description |
|-----------|--------|-------------|
| Composition | 0.25 | Face fills 85% of frame |
| Lighting | 0.20 | Professional, well-lit |
| Detail | 0.25 | High level of facial detail |
| Style Adherence | 0.20 | Matches requested style |
| No Artifacts | 0.10 | No glitches or distortions |

**Historical Accuracy** (0.0-1.0):
| Criterion | Weight | Description |
|-----------|--------|-------------|
| Era Clothing | 0.35 | Period-appropriate attire |
| Hairstyle | 0.25 | Accurate to time period |
| Age | 0.20 | Appropriate age for subject |
| Cultural Context | 0.20 | Culturally accurate details |

**Overall Pass**: Technical (all pass) + Visual >= 0.85 + Historical >= 0.80

---

## Implementation Commitment

**Autonomous Execution**: Upon approval of this plan, implementation will proceed fully autonomously with:

1. **No Additional Permissions Required**: Full authority to execute all phases
2. **Testing Before Proceeding**: Each module fully tested before moving to next
3. **Documentation Alongside Code**: Every component documented as it's built
4. **Git Commits at Milestones**: Regular commits with descriptive messages
5. **Zero Tolerance for Failures**: All tests must pass before proceeding

**Reporting**: Progress updates at each phase completion with:
- Components completed
- Tests passing (count + coverage %)
- Any issues encountered and resolved
- Next phase preview

**Delivery**: Final deliverable is a production-ready Portrait Generator API with:
- ✅ All code implemented and tested (90%+ coverage)
- ✅ Complete documentation
- ✅ GitHub repository active
- ✅ CI/CD pipeline functional
- ✅ Example outputs validated
- ✅ Ready for immediate use

---

**End of Implementation Plan**

**Next Step**: Approval to begin autonomous execution

**Estimated Timeline**: 14 days

**Estimated LOC**: ~3,500 lines (excluding tests)

**Estimated Test LOC**: ~2,500 lines

**Total Deliverable**: Production-ready Portrait Generator API
