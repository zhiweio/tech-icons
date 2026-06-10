"""Package-internal resource path resolution.

When tech-icons is installed (via uvx, pip, etc.) the icon catalog and SVG
files live inside the wheel under ``tech_icons/catalog/`` and
``tech_icons/icons/``. These helpers locate them at runtime without relying
on the current working directory or any ``PROJECT_ROOT`` heuristics.
"""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path


def package_root() -> Path:
    """Return the on-disk path of the installed ``tech_icons`` package."""
    return Path(str(files("tech_icons")))


def catalog_dir() -> Path:
    """Return the bundled ``catalog/`` directory."""
    return package_root() / "catalog"


def icon_path(relative: str) -> Path:
    """Resolve an ``icons/...`` path (as stored in ``icons.json``) to disk.

    ``relative`` is the value from a catalog entry's ``path`` field, e.g.
    ``"icons/aws/compute/lambda.svg"``. The leading ``icons/`` segment is
    preserved so it stays consistent across dev and installed layouts.
    """
    return package_root() / relative
