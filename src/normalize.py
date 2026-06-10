"""Core normalization logic for cloud tech icons.

Provides vendor-specific handlers to parse directory structures,
extract categories, generate canonical IDs, and clean filenames
for AWS, Azure, GCP, and Microsoft icon packages.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

ASSETS_DIR = Path("assets")
ICONS_DIR = Path("icons")


@dataclass
class IconEntry:
    """Represents a normalized icon entry."""

    id: str
    vendor: str
    category: str
    name: str
    filename: str
    source_path: Path
    dest_path: Path
    aliases: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    description: str = ""


def clean_name(raw: str) -> str:
    """Convert a raw filename/dirname into a clean kebab-case name.

    Strips vendor prefixes, size suffixes, and normalizes separators.
    """
    # Remove file extension
    name = Path(raw).stem

    # Remove common size suffixes like _48, _64, _16, _32
    name = re.sub(r"[_-]\d+$", "", name)

    # Remove AWS-specific prefixes
    name = re.sub(r"^(Arch_|Res_|Arch-Category_)", "", name)

    # Remove vendor prefixes like AWS-, Amazon-
    name = re.sub(r"^(AWS-|Amazon-|Arch_AWS-|Arch_Amazon-|Res_AWS-|Res_Amazon-)", "", name)

    # Replace underscores and spaces with hyphens
    name = name.replace("_", "-").replace(" ", "-")

    # Collapse multiple hyphens
    name = re.sub(r"-+", "-", name)

    # Lowercase
    name = name.lower().strip("-")

    return name


def sanitize_category(raw: str) -> str:
    """Normalize a category directory name to kebab-case."""
    # Remove prefixes like Arch_, Res_
    cat = re.sub(r"^(Arch_|Res_|Arch-Category_)", "", raw)

    # Handle special chars
    cat = cat.replace("&", "and").replace("+", "and").replace("_", "-").replace(" ", "-")

    # Remove special characters except hyphens
    cat = re.sub(r"[^a-zA-Z0-9-]", "", cat)

    # Collapse multiple hyphens and lowercase
    cat = re.sub(r"-+", "-", cat).lower().strip("-")

    return cat


def generate_canonical_id(vendor: str, category: str, name: str) -> str:
    """Generate canonical ID: vendor/category/name."""
    return f"{vendor}/{category}/{name}"


# ---------------------------------------------------------------------------
# AWS Handler
# ---------------------------------------------------------------------------


def parse_aws_architecture_service_icons(assets_root: Path) -> list[IconEntry]:
    """Parse AWS Architecture Service Icons (48/ size variant only)."""
    entries: list[IconEntry] = []
    base = assets_root / "aws-icon-package" / "Architecture-Service-Icons_04302026"

    if not base.exists():
        logger.warning(f"AWS Architecture Service Icons not found: {base}")
        return entries

    for cat_dir in sorted(base.iterdir()):
        if not cat_dir.is_dir() or cat_dir.name.startswith("."):
            continue

        category = sanitize_category(cat_dir.name)
        size_dir = cat_dir / "48"

        if not size_dir.exists():
            logger.debug(f"No 48/ dir in {cat_dir.name}, skipping")
            continue

        for svg_file in sorted(size_dir.glob("*.svg")):
            name = clean_name(svg_file.stem)
            icon_id = generate_canonical_id("aws", category, name)
            dest = ICONS_DIR / "aws" / category / f"{name}.svg"

            entries.append(
                IconEntry(
                    id=icon_id,
                    vendor="aws",
                    category=category,
                    name=_format_display_name("aws", name),
                    filename=f"{name}.svg",
                    source_path=svg_file,
                    dest_path=dest,
                    tags=_generate_aws_tags(category, name),
                )
            )

    return entries


def parse_aws_category_icons(assets_root: Path) -> list[IconEntry]:
    """Parse AWS Category Icons (Arch-Category_48/)."""
    entries: list[IconEntry] = []
    base = assets_root / "aws-icon-package" / "Category-Icons_04302026" / "Arch-Category_48"

    if not base.exists():
        logger.warning(f"AWS Category Icons not found: {base}")
        return entries

    for svg_file in sorted(base.glob("*.svg")):
        name = clean_name(svg_file.stem)
        icon_id = generate_canonical_id("aws", "category", name)
        dest = ICONS_DIR / "aws" / "category" / f"{name}.svg"

        entries.append(
            IconEntry(
                id=icon_id,
                vendor="aws",
                category="category",
                name=_format_display_name("aws", name),
                filename=f"{name}.svg",
                source_path=svg_file,
                dest_path=dest,
                tags=["category", "aws"],
            )
        )

    return entries


def parse_aws_resource_icons(assets_root: Path) -> list[IconEntry]:
    """Parse AWS Resource Icons (Res_{Category}/ with 48/ size variant)."""
    entries: list[IconEntry] = []
    base = assets_root / "aws-icon-package" / "Resource-Icons_04302026"

    if not base.exists():
        logger.warning(f"AWS Resource Icons not found: {base}")
        return entries

    for cat_dir in sorted(base.iterdir()):
        if not cat_dir.is_dir() or cat_dir.name.startswith("."):
            continue

        category = sanitize_category(cat_dir.name)

        # Resource icons may have 48/ subdir or be directly in the category dir
        size_dir = cat_dir / "48"
        search_dir = size_dir if size_dir.exists() else cat_dir

        for svg_file in sorted(search_dir.glob("*.svg")):
            name = clean_name(svg_file.stem)
            icon_id = generate_canonical_id("aws", category, name)
            dest = ICONS_DIR / "aws" / category / f"{name}.svg"

            entries.append(
                IconEntry(
                    id=icon_id,
                    vendor="aws",
                    category=category,
                    name=_format_display_name("aws", name),
                    filename=f"{name}.svg",
                    source_path=svg_file,
                    dest_path=dest,
                    tags=[*_generate_aws_tags(category, name), "resource"],
                )
            )

    return entries


def parse_aws_group_icons(assets_root: Path) -> list[IconEntry]:
    """Parse AWS Architecture Group Icons."""
    entries: list[IconEntry] = []
    base = assets_root / "aws-icon-package" / "Architecture-Group-Icons_04302026"

    if not base.exists():
        logger.warning(f"AWS Group Icons not found: {base}")
        return entries

    for svg_file in sorted(base.glob("*.svg")):
        name = clean_name(svg_file.stem)
        icon_id = generate_canonical_id("aws", "group", name)
        dest = ICONS_DIR / "aws" / "group" / f"{name}.svg"

        entries.append(
            IconEntry(
                id=icon_id,
                vendor="aws",
                category="group",
                name=_format_display_name("aws", name),
                filename=f"{name}.svg",
                source_path=svg_file,
                dest_path=dest,
                tags=["group", "architecture", "aws"],
            )
        )

    return entries


def collect_aws_icons(assets_root: Path) -> list[IconEntry]:
    """Collect all AWS icons."""
    entries: list[IconEntry] = []
    entries.extend(parse_aws_architecture_service_icons(assets_root))
    entries.extend(parse_aws_category_icons(assets_root))
    entries.extend(parse_aws_resource_icons(assets_root))
    entries.extend(parse_aws_group_icons(assets_root))
    return entries


# ---------------------------------------------------------------------------
# Azure Handler
# ---------------------------------------------------------------------------


def collect_azure_icons(assets_root: Path) -> list[IconEntry]:
    """Collect Azure icons from azure-icon-package/Icons/."""
    entries: list[IconEntry] = []
    base = assets_root / "azure-icon-package" / "Icons"

    if not base.exists():
        logger.warning(f"Azure icons not found: {base}")
        return entries

    for cat_dir in sorted(base.iterdir()):
        if not cat_dir.is_dir() or cat_dir.name.startswith("."):
            continue

        category = sanitize_category(cat_dir.name)

        for svg_file in sorted(cat_dir.rglob("*.svg")):
            name = clean_name(svg_file.stem)
            icon_id = generate_canonical_id("azure", category, name)
            dest = ICONS_DIR / "azure" / category / f"{name}.svg"

            entries.append(
                IconEntry(
                    id=icon_id,
                    vendor="azure",
                    category=category,
                    name=_format_display_name("azure", name),
                    filename=f"{name}.svg",
                    source_path=svg_file,
                    dest_path=dest,
                    tags=_generate_azure_tags(category, name),
                )
            )

    return entries


# ---------------------------------------------------------------------------
# GCP Handler
# ---------------------------------------------------------------------------


def collect_gcp_category_icons(assets_root: Path) -> list[IconEntry]:
    """Collect gcp-category-icon-package from gcp-category-icon-package/{cat}/SVG/."""
    entries: list[IconEntry] = []
    base = assets_root / "gcp-category-icon-package"

    if not base.exists():
        logger.warning(f"gcp-category-icon-package not found: {base}")
        return entries

    for cat_dir in sorted(base.iterdir()):
        if not cat_dir.is_dir() or cat_dir.name.startswith("."):
            continue

        category = sanitize_category(cat_dir.name)
        svg_dir = cat_dir / "SVG"

        if not svg_dir.exists():
            logger.debug(f"No SVG/ dir in gcp-category-icon-package/{cat_dir.name}")
            continue

        for svg_file in sorted(svg_dir.glob("*.svg")):
            name = clean_name(svg_file.stem)
            icon_id = generate_canonical_id("gcp", category, name)
            dest = ICONS_DIR / "gcp" / category / f"{name}.svg"

            entries.append(
                IconEntry(
                    id=icon_id,
                    vendor="gcp",
                    category=category,
                    name=_format_display_name("gcp", name),
                    filename=f"{name}.svg",
                    source_path=svg_file,
                    dest_path=dest,
                    tags=_generate_gcp_tags(category, name),
                )
            )

    return entries


def collect_gcp_core_product_icons(assets_root: Path) -> list[IconEntry]:
    """Collect GCP Core Product Icons from gcp-core-products-icon-package/{product}/SVG/."""
    entries: list[IconEntry] = []
    base = assets_root / "gcp-core-products-icon-package"

    if not base.exists():
        logger.warning(f"GCP Core Product Icons not found: {base}")
        return entries

    for product_dir in sorted(base.iterdir()):
        if not product_dir.is_dir() or product_dir.name.startswith("."):
            continue

        svg_dir = product_dir / "SVG"
        if not svg_dir.exists():
            logger.debug(f"No SVG/ dir in gcp-core-products-icon-package/{product_dir.name}")
            continue

        product_name = sanitize_category(product_dir.name)
        # Infer category from product name
        category = _infer_gcp_category(product_dir.name)

        for svg_file in sorted(svg_dir.glob("*.svg")):
            name = clean_name(svg_file.stem) if clean_name(svg_file.stem) else product_name
            icon_id = generate_canonical_id("gcp", category, name)
            dest = ICONS_DIR / "gcp" / category / f"{name}.svg"

            entries.append(
                IconEntry(
                    id=icon_id,
                    vendor="gcp",
                    category=category,
                    name=_format_display_name("gcp", name),
                    filename=f"{name}.svg",
                    source_path=svg_file,
                    dest_path=dest,
                    tags=_generate_gcp_tags(category, name),
                )
            )

    return entries


def collect_gcp_icons(assets_root: Path) -> list[IconEntry]:
    """Collect all GCP icons."""
    entries: list[IconEntry] = []
    entries.extend(collect_gcp_category_icons(assets_root))
    entries.extend(collect_gcp_core_product_icons(assets_root))
    return entries


# ---------------------------------------------------------------------------
# Microsoft Handler
# ---------------------------------------------------------------------------


def collect_microsoft_dynamics_icons(assets_root: Path) -> list[IconEntry]:
    """Collect Dynamics 365 icons."""
    entries: list[IconEntry] = []
    base = assets_root / "dynamics-365-icon-package"

    if not base.exists():
        logger.warning(f"Dynamics 365 icons not found: {base}")
        return entries

    for subdir in ("Dynamics 365 App Icons", "Dynamics 365 Product Family Icons"):
        icons_dir = base / subdir
        if not icons_dir.exists():
            continue

        for svg_file in sorted(icons_dir.rglob("*.svg")):
            name = clean_name(svg_file.stem)
            icon_id = generate_canonical_id("microsoft", "dynamics-365", name)
            dest = ICONS_DIR / "microsoft" / "dynamics-365" / f"{name}.svg"

            entries.append(
                IconEntry(
                    id=icon_id,
                    vendor="microsoft",
                    category="dynamics-365",
                    name=_format_display_name("microsoft", name),
                    filename=f"{name}.svg",
                    source_path=svg_file,
                    dest_path=dest,
                    tags=["dynamics-365", "business-applications", "microsoft"],
                )
            )

    return entries


def collect_microsoft_fabric_icons(assets_root: Path) -> list[IconEntry]:
    """Collect microsoft-fabric-icon-package from package/dist/svg/."""
    entries: list[IconEntry] = []
    base = assets_root / "microsoft-fabric-icon-package" / "package" / "dist" / "svg"

    if not base.exists():
        logger.warning(f"microsoft-fabric-icon-package not found: {base}")
        return entries

    # Only grab 20px color variants to avoid duplicates
    for svg_file in sorted(base.glob("*.svg")):
        stem = svg_file.stem
        # Prefer 20px item/color variants, skip regular/filled duplicates
        if "_20_" not in stem and "_24_" not in stem:
            continue
        # Skip 'regular' when 'filled' or 'color' exists (deduplicate)
        if "regular" in stem:
            continue

        name = clean_name(stem)
        icon_id = generate_canonical_id("microsoft", "fabric", name)
        dest = ICONS_DIR / "microsoft" / "fabric" / f"{name}.svg"

        entries.append(
            IconEntry(
                id=icon_id,
                vendor="microsoft",
                category="fabric",
                name=_format_display_name("microsoft", name),
                filename=f"{name}.svg",
                source_path=svg_file,
                dest_path=dest,
                tags=["fabric", "data-platform", "microsoft"],
            )
        )

    return entries


def collect_microsoft_power_platform_icons(assets_root: Path) -> list[IconEntry]:
    """Collect Power Platform icons."""
    entries: list[IconEntry] = []
    base = assets_root / "power-platform-icon-package" / "Power Platform"

    if not base.exists():
        logger.warning(f"Power Platform icons not found: {base}")
        return entries

    for svg_file in sorted(base.glob("*.svg")):
        name = clean_name(svg_file.stem)
        icon_id = generate_canonical_id("microsoft", "power-platform", name)
        dest = ICONS_DIR / "microsoft" / "power-platform" / f"{name}.svg"

        entries.append(
            IconEntry(
                id=icon_id,
                vendor="microsoft",
                category="power-platform",
                name=_format_display_name("microsoft", name),
                filename=f"{name}.svg",
                source_path=svg_file,
                dest_path=dest,
                tags=["power-platform", "low-code", "microsoft"],
            )
        )

    return entries


def collect_microsoft_entra_icons(assets_root: Path) -> list[IconEntry]:
    """Collect Microsoft Entra identity icons (color SVG set)."""
    entries: list[IconEntry] = []
    base = assets_root / "microsoft-entra-architecture-icon-package" / "Microsoft Entra color icons SVG"

    if not base.exists():
        logger.warning(f"Microsoft Entra icons not found: {base}")
        return entries

    for svg_file in sorted(base.rglob("*.svg")):
        name = clean_name(svg_file.stem)
        icon_id = generate_canonical_id("microsoft", "entra", name)
        dest = ICONS_DIR / "microsoft" / "entra" / f"{name}.svg"

        entries.append(
            IconEntry(
                id=icon_id,
                vendor="microsoft",
                category="entra",
                name=_format_display_name("microsoft", name),
                filename=f"{name}.svg",
                source_path=svg_file,
                dest_path=dest,
                tags=["entra", "identity", "security", "microsoft"],
            )
        )

    return entries


def collect_microsoft_365_icons(assets_root: Path) -> list[IconEntry]:
    """Collect Microsoft 365 content icons."""
    entries: list[IconEntry] = []
    base = assets_root / "microsoft-365-content-icon-package"

    if not base.exists():
        logger.warning(f"Microsoft 365 icons not found: {base}")
        return entries

    for color_dir in sorted(base.iterdir()):
        if not color_dir.is_dir() or color_dir.name.startswith("."):
            continue

        for svg_file in sorted(color_dir.rglob("*.svg")):
            name = clean_name(svg_file.stem)
            icon_id = generate_canonical_id("microsoft", "microsoft-365", name)
            dest = ICONS_DIR / "microsoft" / "microsoft-365" / f"{name}.svg"

            entries.append(
                IconEntry(
                    id=icon_id,
                    vendor="microsoft",
                    category="microsoft-365",
                    name=_format_display_name("microsoft", name),
                    filename=f"{name}.svg",
                    source_path=svg_file,
                    dest_path=dest,
                    tags=["microsoft-365", "productivity", "microsoft"],
                )
            )

    return entries


def collect_microsoft_icons(assets_root: Path) -> list[IconEntry]:
    """Collect all Microsoft icons."""
    entries: list[IconEntry] = []
    entries.extend(collect_microsoft_dynamics_icons(assets_root))
    entries.extend(collect_microsoft_fabric_icons(assets_root))
    entries.extend(collect_microsoft_power_platform_icons(assets_root))
    entries.extend(collect_microsoft_entra_icons(assets_root))
    entries.extend(collect_microsoft_365_icons(assets_root))
    return entries


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _format_display_name(vendor: str, kebab_name: str) -> str:
    """Convert kebab-case name to human-readable display name."""
    # Capitalize each word
    words = kebab_name.split("-")
    # Handle known acronyms
    acronyms = {
        "aws",
        "ec2",
        "s3",
        "rds",
        "ecs",
        "eks",
        "iam",
        "vpc",
        "api",
        "cdn",
        "dns",
        "sql",
        "kms",
        "sns",
        "sqs",
        "gcp",
        "gke",
        "ai",
        "ml",
        "iot",
        "vm",
        "vpn",
        "nat",
        "waf",
        "dms",
        "emr",
        "msk",
        "nlb",
        "alb",
        "elb",
    }
    display_words = []
    for w in words:
        if w in acronyms:
            display_words.append(w.upper())
        else:
            display_words.append(w.capitalize())

    prefix_map = {"aws": "AWS", "azure": "Azure", "gcp": "GCP", "microsoft": "Microsoft"}
    prefix = prefix_map.get(vendor, vendor.capitalize())
    return f"{prefix} {' '.join(display_words)}"


def _generate_aws_tags(category: str, name: str) -> list[str]:
    """Generate tags for an AWS icon based on category and name."""
    tags = ["aws", category]
    # Add keywords from name
    tags.extend(name.split("-")[:3])
    return list(set(tags))


def _generate_azure_tags(category: str, name: str) -> list[str]:
    """Generate tags for an Azure icon."""
    tags = ["azure", category]
    tags.extend(name.split("-")[:3])
    return list(set(tags))


def _generate_gcp_tags(category: str, name: str) -> list[str]:
    """Generate tags for a GCP icon."""
    tags = ["gcp", category]
    tags.extend(name.split("-")[:3])
    return list(set(tags))


GCP_PRODUCT_CATEGORY_MAP: dict[str, str] = {
    "AI Hypercomputer": "ai-machine-learning",
    "AlloyDB": "databases",
    "Anthos": "hybrid-and-multicloud",
    "Apigee": "integration-services",
    "BigQuery": "data-analytics",
    "Cloud Run": "serverless-computing",
    "Cloud SQL": "databases",
    "Cloud Spanner": "databases",
    "Cloud Storage": "storage",
    "Compute Engine": "compute",
    "Distributed Cloud": "hybrid-and-multicloud",
    "GKE": "containers",
    "Hyperdisk": "storage",
    "Looker": "data-analytics",
    "Mandiant": "security-identity",
    "Security Command Center": "security-identity",
    "Security Operations": "security-identity",
    "Threat Intelligence": "security-identity",
    "Vertex AI": "ai-machine-learning",
}


def _infer_gcp_category(product_name: str) -> str:
    """Infer GCP category from product directory name."""
    if product_name in GCP_PRODUCT_CATEGORY_MAP:
        return GCP_PRODUCT_CATEGORY_MAP[product_name]
    return sanitize_category(product_name)


def deduplicate_entries(entries: list[IconEntry]) -> list[IconEntry]:
    """Remove duplicate entries by canonical ID, keeping the first occurrence."""
    seen: set[str] = set()
    deduped: list[IconEntry] = []
    for entry in entries:
        if entry.id not in seen:
            seen.add(entry.id)
            deduped.append(entry)
        else:
            logger.debug(f"Duplicate icon ID skipped: {entry.id}")
    return deduped


def collect_all_icons(assets_root: Path) -> list[IconEntry]:
    """Collect and deduplicate all icons from all vendors."""
    entries: list[IconEntry] = []
    entries.extend(collect_aws_icons(assets_root))
    entries.extend(collect_azure_icons(assets_root))
    entries.extend(collect_gcp_icons(assets_root))
    entries.extend(collect_microsoft_icons(assets_root))
    return deduplicate_entries(entries)
