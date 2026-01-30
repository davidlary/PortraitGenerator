"""Configuration settings for Portrait Generator."""

import os
from pathlib import Path
from typing import Tuple

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # API Keys (REQUIRED from environment)
    google_api_key: str = Field(..., description="Google Gemini API key")

    # Gemini Model Configuration
    gemini_model: str = Field(
        default="gemini-exp-1206",
        description="Gemini model for image generation",
    )

    # Image Settings
    image_resolution: str = Field(
        default="1024,1024",
        description="Image resolution as 'width,height'",
    )
    portrait_quality: int = Field(
        default=95,
        ge=1,
        le=100,
        description="JPEG quality (1-100)",
    )

    # Output Settings
    output_dir: Path = Field(
        default=Path("./output"),
        description="Output directory for generated portraits",
    )
    save_prompts: bool = Field(
        default=True,
        description="Save prompt markdown files alongside images",
    )

    # Testing Settings
    visual_inspection_enabled: bool = Field(
        default=True,
        description="Enable visual inspection tests",
    )

    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level",
    )

    # API Settings
    max_concurrent_requests: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum concurrent API requests",
    )

    @field_validator("output_dir", mode="before")
    @classmethod
    def create_output_dir(cls, v: Path | str) -> Path:
        """Ensure output directory exists."""
        path = Path(v) if isinstance(v, str) else v
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def resolution_tuple(self) -> Tuple[int, int]:
        """Parse resolution string to tuple."""
        parts = self.image_resolution.split(",")
        if len(parts) != 2:
            return (1024, 1024)
        try:
            return (int(parts[0].strip()), int(parts[1].strip()))
        except ValueError:
            return (1024, 1024)

    def validate_api_key(self) -> bool:
        """Validate that API key is set and not a placeholder."""
        if not self.google_api_key:
            return False
        if "your_" in self.google_api_key.lower():
            return False
        if len(self.google_api_key) < 20:
            return False
        return True


def get_settings() -> Settings:
    """Factory function to get settings instance."""
    return Settings()
