"""ppt-master integration bridge.

Copies or symlinks selected tech-icons into a target directory compatible
with ppt-master's icon resolution convention:
  <use data-icon="tech/{vendor}/{name}" xlink:href="..."/>

Usage:
    python3 -m src.bridges.ppt_master --icons aws/compute/lambda,azure/compute/function-apps \
        --target ./templates/icons/tech/
    python3 -m src.bridges.ppt_master --vendor aws --target ./templates/icons/tech/
"""

from __future__ import annotations

import argparse
import logging
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.search import SearchEngine  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def export_icons(
    icon_ids: list[str],
    target_dir: Path,
    symlink: bool = False,
    engine: SearchEngine | None = None,
) -> list[Path]:
    """Copy or symlink icons into ppt-master target directory.

    Target layout: {target_dir}/{vendor}/{name}.svg

    Args:
        icon_ids: List of canonical icon IDs to export.
        target_dir: Destination directory for icons.
        symlink: Use symlinks instead of copies.
        engine: SearchEngine instance (created if not provided).

    Returns:
        List of paths to exported icon files.
    """
    if engine is None:
        engine = SearchEngine(catalog_dir=PROJECT_ROOT / "catalog")
        engine.load()

    target_dir = Path(target_dir)
    exported: list[Path] = []

    for icon_id in icon_ids:
        entry = engine.get_icon(icon_id)
        if not entry:
            logger.warning(f"Icon not found: {icon_id}, skipping")
            continue

        source = PROJECT_ROOT / entry["path"]
        if not source.exists():
            logger.warning(f"SVG file missing: {source}, skipping")
            continue

        # ppt-master convention: tech/{vendor}/{name}.svg
        vendor = entry["vendor"]
        name = entry["filename"]
        dest = target_dir / vendor / name
        dest.parent.mkdir(parents=True, exist_ok=True)

        if dest.exists():
            dest.unlink()

        if symlink:
            dest.symlink_to(source)
            logger.info(f"Symlinked: {icon_id} -> {dest}")
        else:
            shutil.copy2(source, dest)
            logger.info(f"Copied: {icon_id} -> {dest}")

        exported.append(dest)

    logger.info(f"Exported {len(exported)} icons to {target_dir}")
    return exported


def get_ppt_master_reference(icon_id: str) -> str:
    """Get ppt-master compatible reference for an icon ID.

    Maps tech-icons ID to ppt-master's data-icon attribute format:
      aws/compute/lambda -> tech/aws/lambda
    """
    parts = icon_id.split("/")
    if len(parts) >= 3:
        vendor = parts[0]
        name = parts[-1]
    elif len(parts) == 2:
        vendor = parts[0]
        name = parts[1]
    else:
        vendor = "unknown"
        name = parts[0]

    return f"tech/{vendor}/{name}"


def export_vendor(
    vendor: str,
    target_dir: Path,
    symlink: bool = False,
) -> list[Path]:
    """Export all icons for a vendor in batch mode."""
    engine = SearchEngine(catalog_dir=PROJECT_ROOT / "catalog")
    engine.load()

    icon_ids = [entry["id"] for entry in engine.catalog if entry["vendor"] == vendor]

    if not icon_ids:
        logger.warning(f"No icons found for vendor: {vendor}")
        return []

    logger.info(f"Exporting {len(icon_ids)} icons for vendor '{vendor}'")
    return export_icons(icon_ids, target_dir, symlink=symlink, engine=engine)


def main():
    parser = argparse.ArgumentParser(description="Export tech-icons to ppt-master compatible directory")
    parser.add_argument(
        "--icons",
        type=str,
        help="Comma-separated list of icon IDs to export",
    )
    parser.add_argument(
        "--vendor",
        type=str,
        choices=["aws", "azure", "gcp", "microsoft"],
        help="Export all icons for a vendor (batch mode)",
    )
    parser.add_argument(
        "--target",
        type=str,
        required=True,
        help="Target directory for exported icons",
    )
    parser.add_argument(
        "--symlink",
        action="store_true",
        help="Create symlinks instead of copies",
    )

    args = parser.parse_args()

    if not args.icons and not args.vendor:
        parser.error("Either --icons or --vendor must be specified")

    target = Path(args.target)

    if args.vendor:
        export_vendor(args.vendor, target, symlink=args.symlink)
    else:
        icon_ids = [x.strip() for x in args.icons.split(",") if x.strip()]
        export_icons(icon_ids, target, symlink=args.symlink)


if __name__ == "__main__":
    main()
