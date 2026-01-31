"""Setup configuration for Portrait Generator."""

from pathlib import Path
from setuptools import setup, find_packages

# Read long description from README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    with open(requirements_file) as f:
        requirements = [
            line.strip()
            for line in f
            if line.strip() and not line.startswith("#")
        ]

# Read dev requirements
dev_requirements_file = Path(__file__).parent / "requirements-dev.txt"
dev_requirements = []
if dev_requirements_file.exists():
    with open(dev_requirements_file) as f:
        dev_requirements = [
            line.strip()
            for line in f
            if line.strip() and not line.startswith("#")
        ]

setup(
    name="portrait-generator",
    version="1.0.0",
    author="Dr. David Lary",
    author_email="david.lary@utdallas.edu",
    description="AI-powered historical portrait generation using Google Gemini",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/davidlary/PortraitGenerator",
    project_urls={
        "Bug Reports": "https://github.com/davidlary/PortraitGenerator/issues",
        "Source": "https://github.com/davidlary/PortraitGenerator",
        "Documentation": "https://portrait-generator.readthedocs.io",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        # Development status
        "Development Status :: 5 - Production/Stable",

        # Intended audience
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",

        # Topics
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Image Processing",
        "Topic :: Multimedia :: Graphics",
        "Topic :: Software Development :: Libraries :: Python Modules",

        # License
        "License :: OSI Approved :: MIT License",

        # Python versions
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3 :: Only",

        # OS
        "Operating System :: OS Independent",

        # Framework
        "Framework :: FastAPI",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    extras_require={
        "dev": dev_requirements,
        "test": [
            "pytest>=9.0.0",
            "pytest-cov>=7.0.0",
            "pytest-asyncio>=1.3.0",
            "pytest-mock>=3.15.0",
        ],
        "docs": [
            "sphinx>=7.0.0",
            "sphinx-rtd-theme>=2.0.0",
            "sphinx-click>=6.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "portrait-generator=portrait_generator.cli:main",
            "portrait-gen=portrait_generator.cli:main",  # Short alias
        ],
    },
    include_package_data=True,
    package_data={
        "portrait_generator": [
            "py.typed",  # PEP 561 marker
        ],
    },
    zip_safe=False,
    keywords=[
        "ai",
        "artificial-intelligence",
        "portrait",
        "image-generation",
        "gemini",
        "google-ai",
        "historical-portraits",
        "computer-vision",
        "image-processing",
    ],
)
