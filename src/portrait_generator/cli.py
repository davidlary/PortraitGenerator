"""Command-line interface for Portrait Generator.

This module provides CLI commands for portrait generation.
"""

import logging
import sys
from pathlib import Path
from typing import List, Optional

import click

from . import __version__
from .client import PortraitClient
from .config.settings import get_settings

logger = logging.getLogger(__name__)


@click.group()
@click.version_option(version=__version__, prog_name="portrait-generator")
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose output",
)
@click.pass_context
def cli(ctx, verbose):
    """Portrait Generator - AI-powered historical portrait generation.

    Generate historically accurate portraits in multiple styles using Google Gemini.

    Examples:
        portrait-generator generate "Alan Turing"
        portrait-generator generate "Marie Curie" --styles BW Sepia
        portrait-generator serve --port 8000
        portrait-generator health-check
    """
    ctx.ensure_object(dict)

    if verbose:
        logging.basicConfig(level=logging.DEBUG)
        ctx.obj["verbose"] = True
    else:
        logging.basicConfig(level=logging.INFO)
        ctx.obj["verbose"] = False


@cli.command()
@click.argument("subject_name")
@click.option(
    "--api-key",
    "-k",
    envvar="GOOGLE_API_KEY",
    help="Google Gemini API key (or set GOOGLE_API_KEY env var)",
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(),
    help="Output directory for generated portraits",
)
@click.option(
    "--styles",
    "-s",
    multiple=True,
    type=click.Choice(["BW", "Sepia", "Color", "Painting"], case_sensitive=True),
    help="Styles to generate (can specify multiple)",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Force regeneration even if files exist",
)
@click.pass_context
def generate(ctx, subject_name, api_key, output_dir, styles, force):
    """Generate portraits for a subject.

    Examples:
        portrait-generator generate "Alan Turing"
        portrait-generator generate "Marie Curie" --styles BW Sepia
        portrait-generator generate "Claude Shannon" --force
    """
    try:
        # Validate API key
        if not api_key:
            click.echo("Error: API key required. Set GOOGLE_API_KEY or use --api-key", err=True)
            sys.exit(1)

        # Convert styles tuple to list
        styles_list = list(styles) if styles else None

        # Create client
        client = PortraitClient(
            api_key=api_key,
            output_dir=output_dir,
        )

        # Generate
        click.echo(f"Generating portraits for: {subject_name}")
        if styles_list:
            click.echo(f"Styles: {', '.join(styles_list)}")
        else:
            click.echo("Styles: All (BW, Sepia, Color, Painting)")

        result = client.generate(
            subject_name=subject_name,
            force_regenerate=force,
            styles=styles_list,
        )

        # Report results
        if result.success:
            click.echo("\n✅ Success!")
            click.echo(f"Generated {len(result.files)} portraits in {result.generation_time_seconds:.1f}s")
            click.echo("\nFiles:")
            for style, filepath in result.files.items():
                click.echo(f"  - {style}: {filepath}")

            # Show evaluation summary
            passed_count = sum(1 for eval_result in result.evaluation.values() if eval_result.passed)
            click.echo(f"\nEvaluation: {passed_count}/{len(result.evaluation)} passed")
        else:
            click.echo("\n❌ Generation failed", err=True)
            for error in result.errors:
                click.echo(f"  Error: {error}", err=True)
            sys.exit(1)

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        if ctx.obj.get("verbose"):
            import traceback
            traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.argument("subject_names", nargs=-1, required=True)
@click.option(
    "--api-key",
    "-k",
    envvar="GOOGLE_API_KEY",
    help="Google Gemini API key (or set GOOGLE_API_KEY env var)",
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(),
    help="Output directory for generated portraits",
)
@click.option(
    "--styles",
    "-s",
    multiple=True,
    type=click.Choice(["BW", "Sepia", "Color", "Painting"], case_sensitive=True),
    help="Styles to generate (can specify multiple)",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Force regeneration even if files exist",
)
@click.pass_context
def batch(ctx, subject_names, api_key, output_dir, styles, force):
    """Generate portraits for multiple subjects.

    Examples:
        portrait-generator batch "Alan Turing" "Ada Lovelace" "Grace Hopper"
        portrait-generator batch "Turing" "Lovelace" --styles BW Color
    """
    try:
        # Validate API key
        if not api_key:
            click.echo("Error: API key required. Set GOOGLE_API_KEY or use --api-key", err=True)
            sys.exit(1)

        # Convert styles tuple to list
        styles_list = list(styles) if styles else None

        # Create client
        client = PortraitClient(
            api_key=api_key,
            output_dir=output_dir,
        )

        # Generate
        click.echo(f"Generating portraits for {len(subject_names)} subjects")

        results = client.generate_batch(
            subject_names=list(subject_names),
            force_regenerate=force,
            styles=styles_list,
        )

        # Report results
        success_count = sum(1 for r in results if r.success)
        click.echo(f"\n✅ Completed: {success_count}/{len(results)} successful")

        for result in results:
            if result.success:
                click.echo(f"  ✓ {result.subject}: {len(result.files)} portraits")
            else:
                click.echo(f"  ✗ {result.subject}: Failed")

        if success_count < len(results):
            sys.exit(1)

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        if ctx.obj.get("verbose"):
            import traceback
            traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.argument("subject_name")
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(),
    help="Output directory to check",
)
def status(subject_name, output_dir):
    """Check which portraits exist for a subject.

    Examples:
        portrait-generator status "Alan Turing"
    """
    try:
        # Create client (no API key needed for status check)
        settings = get_settings()
        client = PortraitClient(
            api_key=settings.google_api_key,
            output_dir=output_dir,
        )

        existing = client.check_status(subject_name)

        click.echo(f"Portrait status for: {subject_name}")
        for style, exists in existing.items():
            status_icon = "✓" if exists else "✗"
            click.echo(f"  {status_icon} {style}: {'Exists' if exists else 'Not found'}")

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--host",
    "-h",
    default="0.0.0.0",
    help="Host to bind to (default: 0.0.0.0)",
)
@click.option(
    "--port",
    "-p",
    default=8000,
    type=int,
    help="Port to bind to (default: 8000)",
)
@click.option(
    "--reload",
    is_flag=True,
    help="Enable auto-reload for development",
)
def serve(host, port, reload):
    """Start the FastAPI REST API server.

    Examples:
        portrait-generator serve
        portrait-generator serve --port 8080 --reload
    """
    try:
        import uvicorn

        click.echo(f"Starting Portrait Generator API server")
        click.echo(f"  Host: {host}")
        click.echo(f"  Port: {port}")
        click.echo(f"  API docs: http://{host if host != '0.0.0.0' else 'localhost'}:{port}/docs")

        uvicorn.run(
            "portrait_generator.api.server:app",
            host=host,
            port=port,
            reload=reload,
        )

    except ImportError:
        click.echo("❌ Error: uvicorn not installed. Install with: pip install uvicorn", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error starting server: {e}", err=True)
        sys.exit(1)


@cli.command("health-check")
@click.option(
    "--api-key",
    "-k",
    envvar="GOOGLE_API_KEY",
    help="Google Gemini API key (or set GOOGLE_API_KEY env var)",
)
def health_check(api_key):
    """Check system health and configuration.

    Examples:
        portrait-generator health-check
    """
    try:
        settings = get_settings()

        click.echo("Portrait Generator Health Check")
        click.echo("=" * 50)

        # Check API key
        if api_key or settings.google_api_key:
            click.echo("✓ API Key: Configured")
        else:
            click.echo("✗ API Key: Not configured")
            click.echo("  Set GOOGLE_API_KEY environment variable")

        # Check output directory
        output_dir = Path(settings.output_dir)
        if output_dir.exists():
            click.echo(f"✓ Output Directory: {output_dir}")
        else:
            click.echo(f"! Output Directory: {output_dir} (will be created)")

        # Check write permissions
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            test_file = output_dir / ".health_check"
            test_file.touch()
            test_file.unlink()
            click.echo("✓ Write Permissions: OK")
        except Exception as e:
            click.echo(f"✗ Write Permissions: Failed ({e})")

        # Version info
        click.echo(f"\nVersion: {__version__}")
        click.echo(f"Python: {sys.version.split()[0]}")

        click.echo("\n✅ Health check complete")

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


def main():
    """Main entry point for CLI."""
    cli(obj={})


if __name__ == "__main__":
    main()
