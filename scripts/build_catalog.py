#!/usr/bin/env python3
"""Build the icon catalog: normalize, generate metadata, build keyword index, compute embeddings.

Orchestrates the full pipeline:
  1. Normalize icons (scan assets, deduplicate, copy SVGs)
  2. Generate tech_icons/catalog/icons.json with full metadata per icon
  3. Generate tech_icons/catalog/keyword_index.json (inverted index)
  4. Optionally compute embeddings (tech_icons/catalog/embeddings.npz + tech_icons/catalog/embedding_ids.json)

Usage:
    python3 scripts/build_catalog.py [--skip-embeddings] [--vendor aws] [--force]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
from collections import defaultdict
from pathlib import Path

import yaml

# Add project root to path
from tech_icons.normalize import (
    ASSETS_DIR,
    IconEntry,
    collect_all_icons,
    collect_aws_icons,
    collect_azure_icons,
    collect_developer_icons,
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

CATALOG_DIR = Path("tech_icons/catalog")
HASH_FILE = CATALOG_DIR / ".build_hash"


def compute_assets_hash(assets_root: Path) -> str:
    """Compute a hash of the assets directory structure for change detection."""
    hasher = hashlib.sha256()

    # Hash directory listing (sorted for determinism)
    for svg_file in sorted(assets_root.rglob("*.svg")):
        rel = svg_file.relative_to(assets_root)
        hasher.update(str(rel).encode())
        hasher.update(str(svg_file.stat().st_size).encode())

    return hasher.hexdigest()[:16]


def needs_rebuild(assets_root: Path, force: bool = False) -> bool:
    """Check if catalog needs rebuilding based on hash."""
    if force:
        return True

    if not HASH_FILE.exists():
        return True

    current_hash = compute_assets_hash(assets_root)
    stored_hash = HASH_FILE.read_text().strip()

    if current_hash != stored_hash:
        logger.info("Assets changed since last build, rebuilding...")
        return True

    logger.info("No changes detected. Use --force to rebuild anyway.")
    return False


def load_enrichments() -> dict:
    """Load alias and tag enrichments from tech_icons/catalog/enrichments.yaml."""
    enrichments_path = CATALOG_DIR / "enrichments.yaml"
    if not enrichments_path.exists():
        logger.warning("No enrichments.yaml found, skipping enrichments")
        return {"aliases": {}, "tags": {}}

    with open(enrichments_path) as f:
        data = yaml.safe_load(f)

    return data or {"aliases": {}, "tags": {}}


def build_reverse_enrichment_map(enrichments: dict) -> dict[str, dict]:
    """Build a reverse map: icon_id -> {aliases: [...], tags: [...]}."""
    reverse: dict[str, dict] = defaultdict(lambda: {"aliases": [], "tags": []})

    # Process alias mappings
    for alias_term, icon_ids in enrichments.get("aliases", {}).items():
        if not icon_ids:
            continue
        for icon_id in icon_ids:
            if alias_term not in reverse[icon_id]["aliases"]:
                reverse[icon_id]["aliases"].append(alias_term)

    # Process tag mappings
    for tag_name, icon_ids in enrichments.get("tags", {}).items():
        if not icon_ids:
            continue
        for icon_id in icon_ids:
            if tag_name not in reverse[icon_id]["tags"]:
                reverse[icon_id]["tags"].append(tag_name)

    return dict(reverse)


def entry_to_catalog_record(entry: IconEntry, enrichment_map: dict) -> dict:
    """Convert an IconEntry to a catalog JSON record."""
    enrichment = enrichment_map.get(entry.id, {"aliases": [], "tags": []})

    # Merge enrichment aliases with any existing aliases
    all_aliases = list(set(entry.aliases + enrichment["aliases"]))
    # Add the name tokens as aliases too
    name_tokens = entry.id.split("/")[-1].split("-")
    all_aliases = list(set(all_aliases + name_tokens))

    # Merge tags
    all_tags = list(set(entry.tags + enrichment["tags"]))

    # Build description
    description = entry.description or f"{entry.name} - {entry.vendor} {entry.category} service"

    return {
        "id": entry.id,
        "vendor": entry.vendor,
        "category": entry.category,
        "name": entry.name,
        "filename": entry.filename,
        "path": str(entry.dest_path),
        "aliases": sorted(all_aliases),
        "tags": sorted(all_tags),
        "description": description,
    }


def build_keyword_index(catalog: list[dict]) -> dict[str, list[str]]:
    """Build an inverted index from tokens to icon IDs.

    Tokenizes: name words, aliases, tags, category, vendor.
    """
    index: dict[str, list[str]] = defaultdict(list)

    for record in catalog:
        icon_id = record["id"]
        tokens: set[str] = set()

        # Add name tokens
        for word in record["name"].lower().split():
            tokens.add(word)

        # Add aliases
        for alias in record["aliases"]:
            tokens.add(alias.lower())
            # Also add individual words from multi-word aliases
            for word in alias.lower().split("-"):
                tokens.add(word)

        # Add tags
        for tag in record["tags"]:
            tokens.add(tag.lower())
            for word in tag.lower().split("-"):
                tokens.add(word)

        # Add category and vendor
        tokens.add(record["category"])
        tokens.add(record["vendor"])

        # Add to inverted index
        for token in tokens:
            if token and len(token) >= 2:  # Skip single-char tokens
                if icon_id not in index[token]:
                    index[token].append(icon_id)

    # Sort keys for deterministic output
    return dict(sorted(index.items()))


def compute_embeddings(catalog: list[dict], output_dir: Path) -> None:
    """Compute sentence embeddings for catalog entries.

    Requires sentence-transformers. Outputs:
      - tech_icons/catalog/embeddings.npz (numpy array)
      - tech_icons/catalog/embedding_ids.json (ordered list of IDs matching embedding rows)
    """
    try:
        import numpy as np
        from sentence_transformers import SentenceTransformer
    except ImportError:
        logger.error(
            "sentence-transformers and numpy are required for embeddings. "
            "Install with: python3 -m pip install sentence-transformers numpy"
        )
        return

    logger.info("Loading sentence-transformer model (all-MiniLM-L6-v2)...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    # Build text representations for each icon
    texts: list[str] = []
    ids: list[str] = []

    for record in catalog:
        # Combine name, aliases, tags, description into a searchable text
        parts = [
            record["name"],
            record["description"],
            " ".join(record["aliases"]),
            " ".join(record["tags"]),
            record["category"].replace("-", " "),
            record["vendor"],
        ]
        text = " ".join(parts)
        texts.append(text)
        ids.append(record["id"])

    logger.info(f"Computing embeddings for {len(texts)} icons...")
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=128)

    # Save outputs
    embeddings_path = output_dir / "embeddings.npz"
    ids_path = output_dir / "embedding_ids.json"

    np.savez_compressed(embeddings_path, embeddings=embeddings)
    with open(ids_path, "w") as f:
        json.dump(ids, f, indent=4)

    logger.info(f"Saved embeddings: {embeddings_path} ({embeddings.shape})")
    logger.info(f"Saved embedding IDs: {ids_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build the icon catalog: normalize, index, and optionally embed.",
    )
    parser.add_argument(
        "--assets-dir",
        type=Path,
        default=ASSETS_DIR,
        help="Root directory containing vendor icon packages (default: assets/)",
    )
    parser.add_argument(
        "--skip-embeddings",
        action="store_true",
        help="Skip computing sentence embeddings",
    )
    parser.add_argument(
        "--vendor",
        choices=["aws", "azure", "gcp", "microsoft", "developer"],
        help="Process only a specific vendor",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force rebuild even if no changes detected",
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
    if not assets_root.exists():
        logger.error(f"Assets directory not found: {assets_root}")
        sys.exit(1)

    # Check if rebuild needed
    if not needs_rebuild(assets_root, force=args.force):
        return

    # Ensure catalog directory exists
    CATALOG_DIR.mkdir(parents=True, exist_ok=True)

    # Step 1: Collect icons
    logger.info("=" * 60)
    logger.info("Phase 1: Collecting icons from asset directories")
    logger.info("=" * 60)

    if args.vendor:
        collector_map = {
            "aws": collect_aws_icons,
            "azure": collect_azure_icons,
            "gcp": collect_gcp_icons,
            "microsoft": collect_microsoft_icons,
            "developer": collect_developer_icons,
        }
        entries = collector_map[args.vendor](assets_root)
    else:
        entries = collect_all_icons(assets_root)

    entries = deduplicate_entries(entries)
    logger.info(f"Collected {len(entries)} unique icons")

    # Vendor breakdown
    vendor_counts: dict[str, int] = defaultdict(int)
    for e in entries:
        vendor_counts[e.vendor] += 1
    for v, c in sorted(vendor_counts.items()):
        logger.info(f"  {v}: {c} icons")

    # Step 2: Load enrichments and build catalog
    logger.info("")
    logger.info("=" * 60)
    logger.info("Phase 2: Generating catalog with enrichments")
    logger.info("=" * 60)

    enrichments = load_enrichments()
    enrichment_map = build_reverse_enrichment_map(enrichments)
    logger.info(
        f"Loaded enrichments: {len(enrichments.get('aliases', {}))} alias terms, "
        f"{len(enrichments.get('tags', {}))} tag groups"
    )

    catalog = [entry_to_catalog_record(e, enrichment_map) for e in entries]

    # Write catalog
    catalog_path = CATALOG_DIR / "icons.json"
    with open(catalog_path, "w") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)
    logger.info(f"Wrote catalog: {catalog_path} ({len(catalog)} entries)")

    # Step 3: Build keyword index
    logger.info("")
    logger.info("=" * 60)
    logger.info("Phase 3: Building keyword index")
    logger.info("=" * 60)

    keyword_index = build_keyword_index(catalog)
    index_path = CATALOG_DIR / "keyword_index.json"
    with open(index_path, "w") as f:
        json.dump(keyword_index, f, indent=2, ensure_ascii=False)
    logger.info(f"Wrote keyword index: {index_path} ({len(keyword_index)} tokens)")

    # Step 4: Embeddings (optional)
    if not args.skip_embeddings:
        logger.info("")
        logger.info("=" * 60)
        logger.info("Phase 4: Computing embeddings")
        logger.info("=" * 60)
        compute_embeddings(catalog, CATALOG_DIR)
    else:
        logger.info("\nSkipping embeddings (--skip-embeddings)")

    # Save hash for incremental builds
    current_hash = compute_assets_hash(assets_root)
    HASH_FILE.write_text(current_hash)
    logger.info(f"\nBuild hash saved: {current_hash}")

    logger.info("")
    logger.info("=" * 60)
    logger.info("BUILD COMPLETE")
    logger.info("=" * 60)
    logger.info(f"  tech_icons/catalog/icons.json          : {len(catalog)} entries")
    logger.info(f"  tech_icons/catalog/keyword_index.json  : {len(keyword_index)} tokens")
    if not args.skip_embeddings:
        logger.info(f"  tech_icons/catalog/embeddings.npz      : {len(catalog)} vectors")
        logger.info(f"  tech_icons/catalog/embedding_ids.json  : {len(catalog)} IDs")


if __name__ == "__main__":
    main()
