"""Output format adapters for icon content (SVG and PNG).

Provides multiple output formats for icons:
  - raw content (str for SVG, bytes for PNG)
  - absolute file path
  - base64 encoded
  - data URI (correct MIME per image type)
  - ppt-master placeholder
  - inline <g> element (SVG only)

The ``image_type`` parameter controls which file format is read:
``"svg"`` (default) or ``"png"``. If the requested format is unavailable,
the adapter falls back to whichever format exists.
"""

from __future__ import annotations

import base64
import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)


class IconNotFoundError(Exception):
    """Raised when an icon file does not exist."""


def get_mime_type(image_type: str) -> str:
    """Return the MIME type for a given image type."""
    return {"svg": "image/svg+xml", "png": "image/png"}.get(image_type, "application/octet-stream")


def _resolve_path(path: str | Path) -> Path:
    """Resolve and validate an icon path."""
    p = Path(path)
    if not p.exists():
        raise IconNotFoundError(f"Icon file not found: {p}")
    return p.resolve()


def raw_icon(path: str | Path, image_type: str = "svg") -> str | bytes:
    """Return icon content — str for SVG, bytes for PNG."""
    p = _resolve_path(path)
    if image_type == "png":
        return p.read_bytes()
    return p.read_text(encoding="utf-8")


def svg_path(path: str | Path) -> str:
    """Return absolute file path as string (format-agnostic)."""
    p = _resolve_path(path)
    return str(p)


def base64_icon(path: str | Path, image_type: str = "svg") -> str:
    """Return base64-encoded icon content."""
    p = _resolve_path(path)
    content = p.read_bytes()
    return base64.b64encode(content).decode("ascii")


def data_uri(path: str | Path, image_type: str = "svg") -> str:
    """Return icon as a data URI with correct MIME type."""
    encoded = base64_icon(path, image_type)
    mime = get_mime_type(image_type)
    return f"data:{mime};base64,{encoded}"


def ppt_master_placeholder(icon_id: str) -> str:
    """Return ppt-master compatible placeholder element.

    ppt-master's embed_icons.py resolves data-icon by splitting on the first '/':
      lib=tech-icons, name=aws/compute/lambda
      -> {icons_dir}/tech-icons/aws/compute/lambda.svg

    The canonical icon ID with 'tech-icons/' prefix is the complete reference.
    """
    return f'<use data-icon="tech-icons/{icon_id}"/>'


def inline_group(path: str | Path, image_type: str = "svg") -> str:
    """Extract SVG path/shape data and wrap in a <g> element.

    Strips the outer <svg> wrapper and returns inner content in a <g> tag.
    Only available for SVG images — raises ValueError for PNG.
    """
    if image_type != "svg":
        raise ValueError("inline_group format is only available for SVG icons")

    content = raw_icon(path, "svg")
    if isinstance(content, bytes):
        content = content.decode("utf-8")

    # Extract content between <svg ...> and </svg>
    match = re.search(r"<svg[^>]*>(.*)</svg>", content, re.DOTALL)
    if not match:
        raise IconNotFoundError(f"Invalid SVG file (no <svg> root): {path}")

    inner = match.group(1).strip()

    # Extract viewBox for preserving coordinate space
    viewbox_match = re.search(r'viewBox="([^"]*)"', content)
    viewbox_attr = f' viewBox="{viewbox_match.group(1)}"' if viewbox_match else ""

    return f"<g{viewbox_attr}>{inner}</g>"


def resolve_image_path(formats: dict[str, str], image_type: str = "svg") -> tuple[str, str]:
    """Resolve which file to serve from a catalog entry's ``formats`` dict.

    Args:
        formats: Dict mapping image type to relative path, e.g.
                 ``{"svg": "icons/aws/lambda.svg", "png": "icons/aws/lambda.png"}``.
        image_type: Requested image type (``"svg"`` or ``"png"``).

    Returns:
        ``(actual_image_type, resolved_path_str)`` — may differ from the
        requested ``image_type`` if it is unavailable (fallback).
    """
    if image_type in formats:
        return image_type, formats[image_type]

    # Fallback: prefer SVG, then first available
    if "svg" in formats:
        return "svg", formats["svg"]
    if "png" in formats:
        return "png", formats["png"]

    # Should never happen with valid catalog entries
    first = next(iter(formats.items()))
    return first


# ---------------------------------------------------------------------------
# Public API — kept for backward compatibility and convenience
# ---------------------------------------------------------------------------

# Aliases kept for existing calls (deprecated in favor of format_icon with image_type)
raw_svg = raw_icon
base64_svg = base64_icon


def format_icon(path: str | Path, icon_id: str, fmt: str = "raw", image_type: str = "svg") -> str | bytes:
    """Format an icon in the requested output format.

    Args:
        path: Path to the icon file (SVG or PNG).
        icon_id: Canonical icon ID (e.g., ``"aws/compute/lambda"``).
        fmt: Output format — one of ``"raw"``, ``"path"``, ``"base64"``,
             ``"data_uri"``, ``"ppt_master"``, ``"inline_group"``.
        image_type: Image type — ``"svg"`` or ``"png"``.

    Returns:
        Formatted icon content as string or bytes.

    Raises:
        ValueError: If ``fmt`` is unknown, or if ``fmt="inline_group"`` and
                    ``image_type="png"``.
    """
    if fmt == "raw":
        return raw_icon(path, image_type)
    elif fmt == "path":
        return svg_path(path)
    elif fmt == "base64":
        return base64_icon(path, image_type)
    elif fmt == "data_uri":
        return data_uri(path, image_type)
    elif fmt == "ppt_master":
        return ppt_master_placeholder(icon_id)
    elif fmt == "inline_group":
        return inline_group(path, image_type)

    raise ValueError(f"Unknown format '{fmt}'. Available: raw, path, base64, data_uri, ppt_master, inline_group")
