"""Input validation utilities."""

import re
from typing import List


VALID_STYLES = {"BW", "Sepia", "Color", "Painting"}


def validate_subject_name(name: str) -> None:
    """
    Validate subject name.

    Args:
        name: Subject name to validate

    Raises:
        ValueError: If name is invalid
    """
    if not name:
        raise ValueError("Subject name cannot be empty")

    if not isinstance(name, str):
        raise ValueError("Subject name must be a string")

    if len(name) < 2:
        raise ValueError("Subject name too short (minimum 2 characters)")

    if len(name) > 100:
        raise ValueError("Subject name too long (maximum 100 characters)")

    # Check for invalid characters
    if re.search(r'[<>:"/\\|?*]', name):
        raise ValueError("Subject name contains invalid characters")


def validate_style(style: str) -> None:
    """
    Validate portrait style.

    Args:
        style: Style to validate (must be one of: BW, Sepia, Color, Painting)

    Raises:
        ValueError: If style is invalid
    """
    if not style:
        raise ValueError("Style cannot be empty")

    if style not in VALID_STYLES:
        raise ValueError(
            f"Invalid style '{style}'. Must be one of: {', '.join(VALID_STYLES)}"
        )


def validate_styles(styles: List[str]) -> None:
    """
    Validate list of styles.

    Args:
        styles: List of styles to validate

    Raises:
        ValueError: If any style is invalid
    """
    if not styles:
        raise ValueError("Styles list cannot be empty")

    for style in styles:
        validate_style(style)


def sanitize_filename(name: str) -> str:
    """
    Sanitize name for use as filename.

    Removes spaces and special characters, converts unicode to ASCII.

    Args:
        name: Name to sanitize

    Returns:
        Sanitized filename (e.g., "Albert Einstein" -> "AlbertEinstein")

    Examples:
        >>> sanitize_filename("Albert Einstein")
        'AlbertEinstein'
        >>> sanitize_filename("Marie Curie-Skłodowska")
        'MarieCurie-Sklodowska'
    """
    import unicodedata

    # Normalize unicode characters to ASCII equivalents
    # NFD = decompose characters, then filter out combining marks
    name = unicodedata.normalize('NFKD', name)
    name = name.encode('ascii', 'ignore').decode('ascii')

    # Remove spaces
    name = name.replace(" ", "")

    # Remove or replace special characters
    # Keep only ASCII letters, numbers, hyphens, underscores
    name = re.sub(r'[^a-zA-Z0-9\-_]', '', name)

    # Ensure first letter is capitalized
    if name:
        name = name[0].upper() + name[1:]

    return name
