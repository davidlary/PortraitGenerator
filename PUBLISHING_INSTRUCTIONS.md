# Publishing Instructions for Portrait Generator v2.0.0

## Security Audit ✅ PASSED

**Zero Tolerance Security Check Completed:**
- ✅ No API keys in source code
- ✅ No secrets in git history
- ✅ No credential files tracked
- ✅ Environment variables used correctly
- ✅ Test fixtures are safe
- ✅ .gitignore has 7 secret patterns
- ✅ No secrets in package distribution

**Git Repository Status:**
- ✅ All changes committed
- ✅ Version 2.0.0 in all files
- ✅ Pushed to remote: https://github.com/davidlary/PortraitGenerator.git
- ✅ Latest commit: `c32b067`

---

## Package Build Status ✅ COMPLETE

**Built Packages:**
```
dist/portrait_generator-2.0.0-py3-none-any.whl (81 KB)
dist/portrait_generator-2.0.0.tar.gz (4.9 MB)
```

**Quality Checks:**
- ✅ `twine check dist/*` - **PASSED**
- ✅ No secrets in package
- ✅ All files included correctly
- ✅ Version 2.0.0 verified

---

## 1. Publishing to PyPI

### Prerequisites

You need a PyPI account and API token. If you don't have one:
1. Create account at https://pypi.org/account/register/
2. Verify your email
3. Generate API token at https://pypi.org/manage/account/token/
4. Save token securely

### Option A: Using API Token (Recommended)

```bash
# Set your PyPI token
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-YOUR_API_TOKEN_HERE

# Upload to PyPI
twine upload dist/portrait_generator-2.0.0*
```

### Option B: Using ~/.pypirc

Create `~/.pypirc`:
```ini
[pypi]
username = __token__
password = pypi-YOUR_API_TOKEN_HERE
```

Then upload:
```bash
twine upload dist/portrait_generator-2.0.0*
```

### Verification

After upload, verify at:
- https://pypi.org/project/portrait-generator/
- Test installation: `pip install portrait-generator==2.0.0`

---

## 2. Publishing to Conda

### Prerequisites

1. **Anaconda.org Account**: https://anaconda.org/
2. **Anaconda Client**: `conda install anaconda-client`
3. **Login**: `anaconda login`

### Building Conda Package

```bash
# Install conda-build if needed
conda install conda-build

# Build the package
conda build conda.recipe/

# The built package will be in:
# $CONDA_PREFIX/conda-bld/[platform]/portrait-generator-2.0.0-*.tar.bz2
```

### Uploading to Anaconda.org

```bash
# Login to Anaconda.org
anaconda login

# Upload the package
anaconda upload $CONDA_PREFIX/conda-bld/[platform]/portrait-generator-2.0.0-*.tar.bz2

# Optional: Upload to conda-forge (requires conda-forge recipe PR)
```

### Creating conda.recipe/meta.yaml

If `conda.recipe/meta.yaml` doesn't exist, create it:

```yaml
{% set name = "portrait-generator" %}
{% set version = "2.0.0" %}

package:
  name: {{ name|lower }}
  version: {{ version }}

source:
  url: https://pypi.io/packages/source/{{ name[0] }}/{{ name }}/portrait_generator-{{ version }}.tar.gz
  sha256: # Get from: shasum -a 256 dist/portrait_generator-2.0.0.tar.gz

build:
  noarch: python
  number: 0
  script: "{{ PYTHON }} -m pip install . -vv"
  entry_points:
    - portrait-generator = portrait_generator.cli:main
    - portrait-gen = portrait_generator.cli:main

requirements:
  host:
    - python >=3.10
    - pip
    - setuptools
  run:
    - python >=3.10
    - google-genai >=1.0.0,<2.0.0
    - pillow >=11.0.0,<12.0.0
    - fastapi >=0.100.0,<1.0.0
    - uvicorn >=0.27.0,<1.0.0
    - pydantic >=2.6.0,<3.0.0
    - pydantic-settings >=2.1.0,<3.0.0
    - click >=8.0.0,<9.0.0
    - httpx >=0.26.0,<1.0.0
    - requests >=2.31.0,<3.0.0
    - python-dotenv >=1.0.0,<2.0.0
    - loguru >=0.7.0,<1.0.0

test:
  imports:
    - portrait_generator
  commands:
    - portrait-generator --help

about:
  home: https://github.com/davidlary/PortraitGenerator
  license: MIT
  license_file: LICENSE
  summary: AI-powered historical portrait generation using Google Gemini 3 Pro Image
  description: |
    Portrait Generator creates historically accurate, publication-quality portraits
    using Google's Gemini 3 Pro Image (Nano Banana Pro) with advanced features like
    Google Search grounding, multi-image references, and physics-aware synthesis.
  doc_url: https://portrait-generator.readthedocs.io
  dev_url: https://github.com/davidlary/PortraitGenerator

extra:
  recipe-maintainers:
    - davidlary
```

### Verification

After upload, verify at:
- https://anaconda.org/[your-username]/portrait-generator
- Test installation: `conda install -c [your-username] portrait-generator`

---

## 3. Publishing to conda-forge (Optional)

For wider distribution, submit to conda-forge:

1. Fork https://github.com/conda-forge/staged-recipes
2. Add your recipe to `recipes/portrait-generator/meta.yaml`
3. Submit PR with your recipe
4. Wait for conda-forge review and approval
5. Once approved, your package appears at: https://anaconda.org/conda-forge/portrait-generator

---

## 4. GitHub Release

Create a release on GitHub:

```bash
# Create release using GitHub CLI (if installed)
gh release create v2.0.0 \
  dist/portrait_generator-2.0.0* \
  --title "Portrait Generator v2.0.0 - Gemini 3 Pro Image Integration" \
  --notes-file RELEASE_v2.0.0.md
```

Or manually:
1. Go to https://github.com/davidlary/PortraitGenerator/releases/new
2. Tag: `v2.0.0` (already exists)
3. Title: "Portrait Generator v2.0.0 - Gemini 3 Pro Image Integration"
4. Description: Use content from `RELEASE_v2.0.0.md`
5. Attach files from `dist/` directory
6. Publish release

---

## 5. Post-Publication Checklist

After publishing to all repositories:

- [ ] Verify PyPI package: https://pypi.org/project/portrait-generator/2.0.0/
- [ ] Test PyPI install: `pip install portrait-generator==2.0.0`
- [ ] Verify Conda package on anaconda.org
- [ ] Test Conda install: `conda install portrait-generator`
- [ ] Create GitHub release with artifacts
- [ ] Update documentation links
- [ ] Announce on social media / mailing lists (optional)

---

## Quick Commands Summary

```bash
# PyPI Publishing
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-YOUR_TOKEN
twine upload dist/portrait_generator-2.0.0*

# Conda Publishing
anaconda login
conda build conda.recipe/
anaconda upload $CONDA_PREFIX/conda-bld/[platform]/portrait-generator-2.0.0-*.tar.bz2

# GitHub Release
gh release create v2.0.0 dist/* \
  --title "Portrait Generator v2.0.0" \
  --notes-file RELEASE_v2.0.0.md
```

---

## Troubleshooting

### PyPI Upload Fails

**Error: "File already exists"**
- Solution: Version 2.0.0 already published. Increment version for new release.

**Error: "Invalid credentials"**
- Solution: Check API token is correct and has upload permissions

### Conda Build Fails

**Error: "Missing dependencies"**
- Solution: Ensure all dependencies in meta.yaml match requirements.txt

**Error: "Recipe not found"**
- Solution: Create conda.recipe/meta.yaml following template above

---

## Support

For issues with publishing:
- PyPI: https://pypi.org/help/
- Conda: https://docs.conda.io/projects/conda-build/
- GitHub: https://docs.github.com/en/repositories/releasing-projects-on-github

For Portrait Generator issues:
- GitHub Issues: https://github.com/davidlary/PortraitGenerator/issues
