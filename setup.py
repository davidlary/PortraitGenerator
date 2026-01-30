"""Setup configuration for Portrait Generator."""

from setuptools import setup, find_packages
from pathlib import Path

# Read version
version = {}
with open("src/portrait_generator/__version__.py") as f:
    exec(f.read(), version)

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

setup(
    name="portrait-generator",
    version=version["__version__"],
    author="Dr. David Lary",
    author_email="david.lary@utdallas.edu",
    description="Generate historically accurate portrait images using Google Gemini",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/davidlary/PortraitGenerator",
    project_urls={
        "Bug Tracker": "https://github.com/davidlary/PortraitGenerator/issues",
        "Documentation": "https://github.com/davidlary/PortraitGenerator/blob/main/docs/",
    },
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Multimedia :: Graphics",
    ],
    python_requires=">=3.10",
    install_requires=[
        "google-genai>=0.2.0",
        "pillow>=10.2.0",
        "fastapi>=0.109.0",
        "uvicorn[standard]>=0.27.0",
        "pydantic>=2.6.0",
        "pydantic-settings>=2.1.0",
        "requests>=2.31.0",
        "httpx>=0.26.0",
        "python-dotenv>=1.0.0",
        "click>=8.1.0",
        "loguru>=0.7.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0.0",
            "pytest-cov>=4.1.0",
            "pytest-asyncio>=0.23.0",
            "pytest-mock>=3.12.0",
            "pytest-timeout>=2.2.0",
            "pytesseract>=0.3.10",
            "black>=24.1.0",
            "ruff>=0.1.0",
            "mypy>=1.8.0",
            "types-requests>=2.31.0",
            "types-pillow>=10.2.0",
            "mkdocs>=1.5.0",
            "mkdocs-material>=9.5.0",
            "ipython>=8.20.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "portrait-generator=portrait_generator.cli:main",
        ],
    },
)
