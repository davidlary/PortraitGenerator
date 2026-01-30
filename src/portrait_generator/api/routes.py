"""API routes for Portrait Generator."""

import logging
from pathlib import Path
from typing import List

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse

from .models import (
    PortraitRequest,
    PortraitResult,
    HealthCheckResponse,
    StatusResponse,
)
from ..core.generator import PortraitGenerator
from ..core.researcher import BiographicalResearcher
from ..core.overlay import TitleOverlayEngine
from ..core.evaluator import QualityEvaluator
from ..utils.gemini_client import GeminiImageClient
from ..config.settings import get_settings

logger = logging.getLogger(__name__)

router = APIRouter()

# Dependency for getting settings
settings = get_settings()


def get_generator() -> PortraitGenerator:
    """Create and return PortraitGenerator instance."""
    # Initialize components
    gemini_client = GeminiImageClient(
        api_key=settings.google_api_key,
        model=settings.gemini_model,
    )

    researcher = BiographicalResearcher(gemini_client)
    overlay_engine = TitleOverlayEngine()
    evaluator = QualityEvaluator(gemini_client)

    generator = PortraitGenerator(
        gemini_client=gemini_client,
        researcher=researcher,
        overlay_engine=overlay_engine,
        evaluator=evaluator,
        output_dir=Path(settings.output_dir),
    )

    return generator


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint."""
    import os
    from datetime import datetime

    # Check if Gemini is configured
    gemini_configured = bool(settings.google_api_key and len(settings.google_api_key) > 0)

    # Check if output directory is writable
    output_dir = Path(settings.output_dir)
    output_dir_writable = False
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        test_file = output_dir / ".health_check"
        test_file.touch()
        test_file.unlink()
        output_dir_writable = True
    except Exception:
        pass

    return HealthCheckResponse(
        status="healthy",
        version="1.0.0",
        gemini_configured=gemini_configured,
        output_dir_writable=output_dir_writable,
        timestamp=datetime.now().isoformat(),
    )


@router.post("/generate", response_model=PortraitResult)
async def generate_portrait(
    request: PortraitRequest,
    generator: PortraitGenerator = Depends(get_generator),
):
    """
    Generate portrait(s) for a subject.

    Args:
        request: Portrait generation request

    Returns:
        Portrait generation result with files and evaluations

    Raises:
        HTTPException: If generation fails
    """
    try:
        logger.info(f"Generating portrait for: {request.subject_name}")

        result = generator.generate_portrait(
            subject_name=request.subject_name,
            force_regenerate=request.force_regenerate,
            styles=request.styles,
        )

        if not result.success:
            logger.error(f"Generation failed: {result.errors}")
            raise HTTPException(
                status_code=500,
                detail=f"Portrait generation failed: {'; '.join(result.errors)}",
            )

        logger.info(
            f"Successfully generated {len(result.files)} portraits for {request.subject_name}"
        )

        return result

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@router.post("/batch", response_model=List[PortraitResult])
async def generate_batch(
    requests: List[PortraitRequest],
    generator: PortraitGenerator = Depends(get_generator),
):
    """
    Generate portraits for multiple subjects.

    Args:
        requests: List of portrait generation requests

    Returns:
        List of portrait generation results

    Raises:
        HTTPException: If batch generation fails
    """
    if not requests:
        raise HTTPException(status_code=400, detail="Request list cannot be empty")

    try:
        logger.info(f"Starting batch generation for {len(requests)} subjects")

        results = []
        for req in requests:
            try:
                result = generator.generate_portrait(
                    subject_name=req.subject_name,
                    force_regenerate=req.force_regenerate,
                    styles=req.styles,
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to generate portrait for {req.subject_name}: {e}")
                # Continue with other subjects even if one fails
                results.append(
                    PortraitResult(
                        subject=req.subject_name,
                        files={},
                        prompts={},
                        metadata=None,
                        evaluation={},
                        generation_time_seconds=0.0,
                        success=False,
                        errors=[str(e)],
                    )
                )

        success_count = sum(1 for r in results if r.success)
        logger.info(f"Batch complete: {success_count}/{len(results)} successful")

        return results

    except Exception as e:
        logger.error(f"Batch generation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch generation failed: {e}")


@router.get("/status/{subject_name}", response_model=StatusResponse)
async def check_status(
    subject_name: str,
    generator: PortraitGenerator = Depends(get_generator),
):
    """
    Check if portraits exist for a subject.

    Args:
        subject_name: Name of subject to check

    Returns:
        Status response with existence info

    Raises:
        HTTPException: If check fails
    """
    try:
        existing = generator.check_existing_portraits(subject_name)

        # Get list of existing files
        files = [
            f"{generator._create_filename(subject_name, style)}.png"
            for style, exists in existing.items()
            if exists
        ]

        # Any portraits exist?
        any_exist = any(existing.values())

        return StatusResponse(
            subject=subject_name,
            exists=any_exist,
            files=files,
        )

    except Exception as e:
        logger.error(f"Status check error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Status check failed: {e}")


@router.get("/download/{subject_name}/{style}")
async def download_portrait(
    subject_name: str,
    style: str,
    generator: PortraitGenerator = Depends(get_generator),
):
    """
    Download a generated portrait.

    Args:
        subject_name: Name of subject
        style: Portrait style (BW, Sepia, Color, Painting)

    Returns:
        File response with portrait image

    Raises:
        HTTPException: If file not found
    """
    try:
        # Create filename
        filename = generator._create_filename(subject_name, style)
        file_path = generator.output_dir / f"{filename}.png"

        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Portrait not found for {subject_name} in {style} style",
            )

        return FileResponse(
            path=str(file_path),
            media_type="image/png",
            filename=f"{filename}.png",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Download failed: {e}")
