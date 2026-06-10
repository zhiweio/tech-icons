"""Output format adapters for icon SVG content.

Provides multiple output formats for icons:
  - raw SVG string
  - absolute file path
  - base64 encoded
  - data URI
  - ppt-master placeholder
  - inline <g> element
"""

from __future__ import annotations

import base64
import re
from pathlib import Path


class IconNotFoundError(Exception):
    """Raised when an icon file does not exist."""


def _resolve_path(path: str | Path) -> Path:
    """Resolve and validate an icon path."""
    p = Path(path)
    if not p.exists():
        raise IconNotFoundError(f"Icon file not found: {p}")
    return p.resolve()


def raw_svg(path: str | Path) -> str:
    """Return SVG file content as string."""
    p = _resolve_path(path)
    return p.read_text(encoding="utf-8")


def svg_path(path: str | Path) -> str:
    """Return absolute file path as string."""
    p = _resolve_path(path)
    return str(p)


def base64_svg(path: str | Path) -> str:
    """Return base64-encoded SVG content."""
    p = _resolve_path(path)
    content = p.read_bytes()
    return base64.b64encode(content).decode("ascii")


def data_uri(path: str | Path) -> str:
    """Return SVG as a data URI."""
    encoded = base64_svg(path)
    return f"data:image/svg+xml;base64,{encoded}"


def ppt_master_placeholder(icon_id: str) -> str:
    """Return ppt-master compatible placeholder element."""
    return f'<use data-icon="tech-icons/{icon_id}" xlink:href="icons/{icon_id}.svg"/>'


def inline_group(path: str | Path) -> str:
    """Extract SVG path/shape data and wrap in a <g> element.

    Strips the outer <svg> wrapper and returns inner content in a <g> tag.
    """
    content = raw_svg(path)

    # Extract content between <svg ...> and </svg>
    match = re.search(r"<svg[^>]*>(.*)</svg>", content, re.DOTALL)
    if not match:
        raise IconNotFoundError(f"Invalid SVG file (no <svg> root): {path}")

    inner = match.group(1).strip()

    # Extract viewBox for preserving coordinate space
    viewbox_match = re.search(r'viewBox="([^"]*)"', content)
    viewbox_attr = f' viewBox="{viewbox_match.group(1)}"' if viewbox_match else ""

    return f"<g{viewbox_attr}>{inner}</g>"


def format_icon(path: str | Path, icon_id: str, fmt: str = "raw") -> str:
    """Format an icon in the requested output format.

    Args:
        path: Path to the SVG file.
        icon_id: Canonical icon ID (e.g., "aws/compute/lambda").
        fmt: One of "raw", "path", "base64", "data_uri", "ppt_master", "inline_group".

    Returns:
        Formatted icon content as string.
    """
    formatters = {
        "raw": lambda: raw_svg(path),
        "path": lambda: svg_path(path),
        "base64": lambda: base64_svg(path),
        "data_uri": lambda: data_uri(path),
        "ppt_master": lambda: ppt_master_placeholder(icon_id),
        "inline_group": lambda: inline_group(path),
    }

    if fmt not in formatters:
        raise ValueError(f"Unknown format '{fmt}'. Available: {', '.join(formatters.keys())}")

    return formatters[fmt]()
