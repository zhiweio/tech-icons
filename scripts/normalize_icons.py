#!/usr/bin/env python3
"""Normalize cloud tech icons from asset packages into a canonical directory structure.

Scans vendor-specific asset directories, extracts SVG files (preferring 48px variants),
and copies them into icons/{vendor}/{category}/{name}.svg with consistent naming.

Usage:
    python3 scripts/normalize_icons.py [--assets-dir DIR] [--output-dir DIR]
                                       [--vendor VENDOR] [--dry-run]
"""

from __future__ import annotations

import argparse
import logging
import shutil
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.normalize import (
    ASSETS_DIR,
    IconEntry,
    collect_aws_icons,
    collect_azure_icons,
    collect_gcp_icons,
    collect_microsoft_icons,
    deduplicate_entries,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def copy_icon(entry: IconEntry, output_dir: Path, dry_run: bool = False) -> bool:
    """Copy a single icon from source to normalized destination.

    Returns True if the file was copied (or would be in dry-run mode).
    """
    dest = output_dir / entry.dest_path
    source = entry.source_path

    if not source.exists():
        logger.warning(f"Source file missing: {source}")
        return False

    if dest.exists() and dest.stat().st_size == source.stat().st_size:
        # Skip if identical file already exists
        return False

    if dry_run:
        logger.debug(f"[DRY RUN] Would copy: {source} -> {dest}")
        return True

    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)
    return True


def normalize_vendor(
    vendor: str,
    assets_root: Path,
    output_dir: Path,
    dry_run: bool = False,
) -> list[IconEntry]:
    """Normalize icons for a specific vendor."""
    collector_map = {
        "aws": collect_aws_icons,
        "azure": collect_azure_icons,
        "gcp": collect_gcp_icons,
        "microsoft": collect_microsoft_icons,
    }

    collector = collector_map.get(vendor)
    if not collector:
        logger.error(f"Unknown vendor: {vendor}")
        return []

    logger.info(f"Processing {vendor.upper()} icons...")
    entries = collector(assets_root)
    entries = deduplicate_entries(entries)

    copied = 0
    for entry in entries:
        if copy_icon(entry, output_dir, dry_run=dry_run):
            copied += 1

    logger.info(f"  {vendor.upper()}: found {len(entries)} SVGs, copied {copied} new/updated files")
    return entries


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Normalize cloud tech icons into canonical directory structure.",
    )
    parser.add_argument(
        "--assets-dir",
        type=Path,
        default=ASSETS_DIR,
        help="Root directory containing vendor icon packages (default: assets/)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("."),
        help="Output root directory (icons/ will be created under this, default: .)",
    )
    parser.add_argument(
        "--vendor",
        choices=["aws", "azure", "gcp", "microsoft"],
        help="Process only a specific vendor (default: all)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without copying files",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable debug logging",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    assets_root = args.assets_dir.resolve()
    output_dir = args.output_dir.resolve()

    if not assets_root.exists():
        logger.error(f"Assets directory not found: {assets_root}")
        sys.exit(1)

    if args.dry_run:
        logger.info("[DRY RUN MODE] No files will be copied.")

    vendors = [args.vendor] if args.vendor else ["aws", "azure", "gcp", "microsoft"]
    all_entries: list[IconEntry] = []

    for vendor in vendors:
        entries = normalize_vendor(vendor, assets_root, output_dir, dry_run=args.dry_run)
        all_entries.extend(entries)

    total = len(all_entries)
    logger.info(f"Total: {total} icons normalized across {len(vendors)} vendor(s)")

    # Summary by vendor
    vendor_counts = {}
    for e in all_entries:
        vendor_counts[e.vendor] = vendor_counts.get(e.vendor, 0) + 1

    for v, count in sorted(vendor_counts.items()):
        logger.info(f"  {v}: {count} icons")


if __name__ == "__main__":
    main()
