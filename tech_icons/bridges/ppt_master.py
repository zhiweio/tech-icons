"""ppt-master integration bridge.

Copies or symlinks selected tech-icons into a target directory compatible
with ppt-master's icon resolution convention.

ppt-master's embed_icons.py resolves placeholders by splitting data-icon
on the first '/' — ``lib=tech-icons``, ``name=aws/compute/lambda`` —
and resolves to ``{icons_dir}/tech-icons/aws/compute/lambda.svg``.

Target layout: ``{target_dir}/tech-icons/{vendor}/{category}/{name}.svg``

Usage (standalone):
    python3 -m tech_icons.bridges.ppt_master --icons aws/compute/lambda,azure/compute/function-apps \\
        --target ./templates/icons/
    python3 -m tech_icons.bridges.ppt_master --vendor aws --target ./templates/icons/

Usage (via main CLI, preferred):
    tech-icons --ppt-master aws/compute/lambda,azure/compute/function-apps
    tech-icons --ppt-master aws
    tech-icons --ppt-master
"""

from __future__ import annotations

import argparse
import logging
import shutil
from pathlib import Path

from tech_icons._paths import icon_path
from tech_icons.search import SearchEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def export_icons(
    icon_ids: list[str],
    target_dir: Path,
    symlink: bool = False,
    engine: SearchEngine | None = None,
) -> list[Path]:
    """Copy or symlink icons into ppt-master target directory.

    Target layout: ``{target_dir}/tech-icons/{vendor}/{category}/{name}.svg``

    ppt-master's embed_icons.py resolves ``data-icon="tech-icons/aws/compute/lambda"``
    by splitting on the first '/' — ``lib=tech-icons``, ``name=aws/compute/lambda`` —
    and resolves to ``{icons_dir}/tech-icons/aws/compute/lambda.svg``.

    Args:
        icon_ids: List of canonical icon IDs to export.
        target_dir: Destination directory (e.g. ``./templates/icons/``).
        symlink: Use symlinks instead of copies.
        engine: SearchEngine instance (created if not provided).

    Returns:
        List of paths to exported icon files.
    """
    if engine is None:
        engine = SearchEngine()
        engine.load()

    target_dir = Path(target_dir)
    exported: list[Path] = []

    for icon_id in icon_ids:
        entry = engine.get_icon(icon_id)
        if not entry:
            logger.warning(f"Icon not found: {icon_id}, skipping")
            continue

        source = icon_path(entry["path"])
        if not source.exists():
            logger.warning(f"SVG file missing: {source}, skipping")
            continue

        # ppt-master convention: tech-icons/{vendor}/{category}/{name}.svg
        # embed_icons.py splits data-icon on first '/':
        #   lib=tech-icons, name=aws/compute/lambda -> {icons_dir}/tech-icons/aws/compute/lambda.svg
        vendor = entry["vendor"]
        category = entry["category"]
        name = entry["filename"]
        dest = target_dir / "tech-icons" / vendor / category / name
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
    """DEPRECATED: Get ppt-master compatible reference for an icon ID.

    The canonical icon ID with 'tech-icons/' prefix IS the reference now.
    For example, ``aws/compute/lambda`` is referenced as
    ``<use data-icon="tech-icons/aws/compute/lambda"/>``.

    This function exists only for backward compatibility and will be
    removed in a future version.
    """
    import warnings

    warnings.warn(
        "get_ppt_master_reference() is deprecated. Use the canonical icon ID "
        "with 'tech-icons/' prefix directly in data-icon attributes.",
        DeprecationWarning,
        stacklevel=2,
    )
    return f"tech-icons/{icon_id}"


def export_vendor(
    vendor: str,
    target_dir: Path,
    symlink: bool = False,
    engine: SearchEngine | None = None,
) -> list[Path]:
    """Export all icons for a vendor in batch mode."""
    if engine is None:
        engine = SearchEngine()
        engine.load()

    icon_ids = [entry["id"] for entry in engine.catalog if entry["vendor"] == vendor]

    if not icon_ids:
        logger.warning(f"No icons found for vendor: {vendor}")
        return []

    logger.info(f"Exporting {len(icon_ids)} icons for vendor '{vendor}'")
    return export_icons(icon_ids, target_dir, symlink=symlink, engine=engine)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export tech-icons to ppt-master compatible directory",
        epilog=(
            "Tip: use 'tech-icons --ppt-master [ICONS]' to run via the main CLI.\n"
            "Target layout: {target}/tech-icons/{vendor}/{category}/{name}.svg\n"
            "Recommended target: ./templates/icons/"
        ),
    )
    parser.add_argument(
        "--icons",
        type=str,
        help="Comma-separated list of icon IDs to export",
    )
    parser.add_argument(
        "--vendor",
        type=str,
        choices=["aws", "azure", "gcp", "microsoft", "cncf", "devicon", "developer"],
        help="Export all icons for a vendor (batch mode)",
    )
    parser.add_argument(
        "--target",
        type=str,
        default="./templates/icons/",
        help="Target directory for exported icons (default: ./templates/icons/)",
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
