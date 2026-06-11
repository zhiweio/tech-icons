"""Core normalization logic for cloud tech icons.

Strategy: only the **top-level directory under `assets/`** is a stable contract
(e.g., `aws-icon-package`, `azure-icon-package`, `microsoft-fabric-icon-package`).
Internal subdirectory layouts are discovered via `rglob` so the pipeline survives
upstream restructuring of any vendor package.

Per-vendor handlers select files by:
  * **filename pattern** (e.g., AWS `Arch_*_48.svg`, `Res_*_48.svg`, `Arch-Category_*_48.svg`)
  * **path noise skipping** when inferring category from parent dirs (skips `SVG`, `PNG`,
    numeric size dirs, `dist`, `package`, etc.)
  * **fixed category** for vendors whose packages map 1:1 to a category (Microsoft Fabric,
    Power Platform, Entra, Dynamics 365, Microsoft 365).

Icon Source Attributions
------------------------
This project aggregates SVG icons from the following upstream sources.
The MIT license of this project does NOT apply to the bundled icon files.
Each icon set retains its original license and terms.

  * AWS Architecture Icons   — https://aws.amazon.com/architecture/icons/
  * Azure Architecture Icons  — https://learn.microsoft.com/en-us/azure/architecture/icons/
  * Google Cloud Icons        — https://cloud.google.com/icons
  * Microsoft 365 Icons       — https://learn.microsoft.com/en-us/previous-versions/microsoft-365/solutions/architecture-icons-templates
  * Dynamics 365 Icons        — https://learn.microsoft.com/en-us/dynamics365/get-started/icons
  * Entra Architecture Icons  — https://learn.microsoft.com/en-us/entra/architecture/architecture-icons
  * Microsoft Fabric Icons    — https://learn.microsoft.com/en-us/fabric/fundamentals/icons
  * Power Platform Icons      — https://learn.microsoft.com/en-us/power-platform/guidance/icons
  * CNCF Artwork              — https://github.com/cncf/artwork
  * Devicon                   — https://github.com/devicons/devicon
  * Developer Icons           — https://github.com/xandemon/developer-icons

Please review each source's license before redistributing or modifying the bundled icons.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

ASSETS_DIR = Path("assets")
# Catalog path prefix for bundled SVG assets.
ICONS_DIR = Path("icons")

# Vendor → upstream source URL mapping for attribution.
# The MIT license of this project does NOT apply to bundled icon files;
# each set retains its original license and terms.
VENDOR_SOURCES: dict[str, str] = {
    "aws": "https://aws.amazon.com/architecture/icons/",
    "azure": "https://learn.microsoft.com/en-us/azure/architecture/icons/",
    "gcp": "https://cloud.google.com/icons",
    "cncf": "https://github.com/cncf/artwork",
    "devicon": "https://github.com/devicons/devicon",
    "developer": "https://github.com/xandemon/developer-icons",
    # Microsoft sub-vendors
    "microsoft-365": "https://learn.microsoft.com/en-us/previous-versions/microsoft-365/solutions/architecture-icons-templates",
    "dynamics-365": "https://learn.microsoft.com/en-us/dynamics365/get-started/icons",
    "entra": "https://learn.microsoft.com/en-us/entra/architecture/architecture-icons",
    "fabric": "https://learn.microsoft.com/en-us/fabric/fundamentals/icons",
    "power-platform": "https://learn.microsoft.com/en-us/power-platform/guidance/icons",
    "microsoft": "https://learn.microsoft.com/en-us/azure/architecture/icons/",  # generic fallback
}

# Directory names that carry no category information — skipped when walking up
# from an SVG file to infer its category.
_NOISE_DIR_NAMES = {
    "svg",
    "png",
    "icons",
    "icon",
    "dist",
    "package",
    "build",
    "src",
    "assets",
    "fonts",
    "css",
    "media",
}
# Purely numeric (size) directories like "16", "48", "48x48", "512".
_NOISE_DIR_NUMERIC = re.compile(r"^\d+(?:x\d+)?$")
# Any directory whose name is dominated by "PNG" (PNG asset folders we ignore).
_PNG_DIR_HINT = re.compile(r"\bPNG\b", re.IGNORECASE)


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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def clean_name(raw: str) -> str:
    """Convert a raw filename/dirname into a clean kebab-case name."""
    name = Path(raw).stem
    # Strip Azure-style "00029-icon-service-" prefix (numeric ID + boilerplate).
    name = re.sub(r"^\d+-icon-service-", "", name, flags=re.IGNORECASE)
    # Strip trailing size suffix: _48, -48, _48x48, _20_filled, _24_color, etc.
    name = re.sub(r"[_-]\d+(?:x\d+)?(?:[_-][a-zA-Z]+)*$", "", name)
    # Strip AWS-style category prefixes
    name = re.sub(r"^(Arch_|Res_|Arch-Category_)", "", name)
    # Strip vendor product-line prefixes
    name = re.sub(r"^(AWS-|Amazon-)", "", name)
    # Drop parenthesised qualifiers like " (Classic)" → "-classic"
    name = re.sub(r"[()]", "", name)
    # Normalize separators
    name = name.replace("_", "-").replace(" ", "-")
    name = re.sub(r"-+", "-", name)
    return name.lower().strip("-")


def sanitize_category(raw: str) -> str:
    """Normalize a category directory name to kebab-case."""
    cat = re.sub(r"^(Arch_|Res_|Arch-Category_)", "", raw)
    cat = cat.replace("&", "and").replace("+", "and").replace("_", "-").replace(" ", "-")
    cat = re.sub(r"[^a-zA-Z0-9-]", "", cat)
    cat = re.sub(r"-+", "-", cat).lower().strip("-")
    return cat


def generate_canonical_id(vendor: str, category: str, name: str) -> str:
    return f"{vendor}/{category}/{name}"


def _is_noise_dir(name: str) -> bool:
    """True if a directory name carries no semantic category information."""
    if name.startswith("."):
        return True
    if name.lower() in _NOISE_DIR_NAMES:
        return True
    if _NOISE_DIR_NUMERIC.match(name):
        return True
    return False


def _infer_category_from_parents(svg: Path, package_root: Path) -> str:
    """Walk up from `svg.parent` toward `package_root`, return the first
    non-noise directory name (sanitized). Empty string if none found.
    """
    cur = svg.parent
    try:
        cur.relative_to(package_root)
    except ValueError:
        return ""
    while cur != package_root and cur != cur.parent:
        if not _is_noise_dir(cur.name):
            return sanitize_category(cur.name)
        cur = cur.parent
    return ""


def _path_contains_png_only(svg: Path, package_root: Path) -> bool:
    """True if some directory between `svg` and `package_root` is marked PNG-only.
    Used to skip files placed in mixed PNG/SVG asset trees.
    """
    cur = svg.parent
    while cur != package_root and cur != cur.parent:
        name_upper = cur.name.upper()
        if _PNG_DIR_HINT.search(name_upper) and "SVG" not in name_upper:
            return True
        cur = cur.parent
    return False


def _iter_svgs(package_root: Path) -> list[Path]:
    """rglob all .svg files under `package_root`, sorted for determinism."""
    if not package_root.exists():
        return []
    return sorted(package_root.rglob("*.svg"))


# ---------------------------------------------------------------------------
# AWS Handler
# ---------------------------------------------------------------------------
# Package: `aws-icon-package/`. Icons classified by FILENAME PREFIX so subdir
# renames are tolerated:
#   * "Arch-Category_*_48.svg"    → category icons, fixed category="category"
#   * "Arch_*_48.svg"             → service icons, category from parent dir
#   * "Res_*_48.svg"              → resource icons, category from parent dir
#   * no prefix, "*_32.svg"       → group icons, fixed category="group"

_AWS_PKG = "aws-icon-package"


def _aws_classify(stem: str) -> tuple[str, str, list[str]] | None:
    """Classify an AWS svg stem. Returns (kind, fixed_category, base_tags) or None."""
    if stem.startswith("Arch-Category_"):
        if not stem.endswith("_48"):
            return None
        return ("category", "category", ["category", "aws"])
    if stem.startswith("Res_"):
        if not stem.endswith("_48"):
            return None
        return ("resource", "", ["resource", "aws"])
    if stem.startswith("Arch_") or stem.startswith("Arch-"):
        if not stem.endswith("_48"):
            return None
        return ("service", "", ["aws"])
    if stem.endswith("_32"):
        return ("group", "group", ["group", "architecture", "aws"])
    return None


def _aws_make_entry(svg: Path, pkg_root: Path, kind_info: tuple[str, str, list[str]]) -> IconEntry | None:
    _kind, fixed_cat, base_tags = kind_info
    category = fixed_cat or _infer_category_from_parents(svg, pkg_root) or "general"
    name = clean_name(svg.stem)
    if not name:
        return None
    extra = _generate_aws_tags(category, name) if not fixed_cat else []
    tags = list(dict.fromkeys([*base_tags, *extra]))
    icon_id = generate_canonical_id("aws", category, name)
    dest = ICONS_DIR / "aws" / category / f"{name}.svg"
    return IconEntry(
        id=icon_id,
        vendor="aws",
        category=category,
        name=_format_display_name("aws", name),
        filename=f"{name}.svg",
        source_path=svg,
        dest_path=dest,
        tags=tags,
    )


def _collect_aws_by_kind(assets_root: Path, *, kinds: set[str]) -> list[IconEntry]:
    pkg_root = assets_root / _AWS_PKG
    if not pkg_root.exists():
        logger.warning(f"AWS package not found: {pkg_root}")
        return []
    entries: list[IconEntry] = []
    for svg in _iter_svgs(pkg_root):
        info = _aws_classify(svg.stem)
        if info is None or info[0] not in kinds:
            continue
        entry = _aws_make_entry(svg, pkg_root, info)
        if entry is not None:
            entries.append(entry)
    return entries


def parse_aws_architecture_service_icons(assets_root: Path) -> list[IconEntry]:
    """AWS architecture service icons (Arch_*_48.svg) — category from parent dir."""
    return _collect_aws_by_kind(assets_root, kinds={"service"})


def parse_aws_category_icons(assets_root: Path) -> list[IconEntry]:
    """AWS top-level category icons (Arch-Category_*_48.svg) — fixed category='category'."""
    return _collect_aws_by_kind(assets_root, kinds={"category"})


def parse_aws_resource_icons(assets_root: Path) -> list[IconEntry]:
    """AWS resource icons (Res_*_48.svg) — category from parent dir."""
    return _collect_aws_by_kind(assets_root, kinds={"resource"})


def parse_aws_group_icons(assets_root: Path) -> list[IconEntry]:
    """AWS architecture group icons (no Arch_/Res_ prefix, *_32.svg)."""
    return _collect_aws_by_kind(assets_root, kinds={"group"})


def collect_aws_icons(assets_root: Path) -> list[IconEntry]:
    """All AWS icons in a single rglob pass."""
    pkg_root = assets_root / _AWS_PKG
    if not pkg_root.exists():
        logger.warning(f"AWS package not found: {pkg_root}")
        return []
    entries: list[IconEntry] = []
    for svg in _iter_svgs(pkg_root):
        info = _aws_classify(svg.stem)
        if info is None:
            continue
        entry = _aws_make_entry(svg, pkg_root, info)
        if entry is not None:
            entries.append(entry)
    return entries


# ---------------------------------------------------------------------------
# Azure Handler
# ---------------------------------------------------------------------------

_AZURE_PKG = "azure-icon-package"


def collect_azure_icons(assets_root: Path) -> list[IconEntry]:
    """All Azure icons — category from first meaningful parent dir."""
    pkg_root = assets_root / _AZURE_PKG
    if not pkg_root.exists():
        logger.warning(f"Azure package not found: {pkg_root}")
        return []

    entries: list[IconEntry] = []
    for svg in _iter_svgs(pkg_root):
        category = _infer_category_from_parents(svg, pkg_root) or "general"
        name = clean_name(svg.stem)
        if not name:
            continue
        icon_id = generate_canonical_id("azure", category, name)
        dest = ICONS_DIR / "azure" / category / f"{name}.svg"
        entries.append(
            IconEntry(
                id=icon_id,
                vendor="azure",
                category=category,
                name=_format_display_name("azure", name),
                filename=f"{name}.svg",
                source_path=svg,
                dest_path=dest,
                tags=_generate_azure_tags(category, name),
            )
        )
    return entries


# ---------------------------------------------------------------------------
# GCP Handler
# ---------------------------------------------------------------------------

_GCP_CATEGORY_PKG = "gcp-category-icon-package"
_GCP_CORE_PKG = "gcp-core-products-icon-package"
_GCP_EXTENDED_PKG = "gcp-icon-package"


def collect_gcp_category_icons(assets_root: Path) -> list[IconEntry]:
    """GCP general category icons. Category from first meaningful parent dir."""
    pkg_root = assets_root / _GCP_CATEGORY_PKG
    if not pkg_root.exists():
        logger.warning(f"{_GCP_CATEGORY_PKG} not found: {pkg_root}")
        return []

    entries: list[IconEntry] = []
    for svg in _iter_svgs(pkg_root):
        if _path_contains_png_only(svg, pkg_root):
            continue
        category = _infer_category_from_parents(svg, pkg_root) or "general"
        name = clean_name(svg.stem)
        if not name:
            continue
        icon_id = generate_canonical_id("gcp", category, name)
        dest = ICONS_DIR / "gcp" / category / f"{name}.svg"
        entries.append(
            IconEntry(
                id=icon_id,
                vendor="gcp",
                category=category,
                name=_format_display_name("gcp", name),
                filename=f"{name}.svg",
                source_path=svg,
                dest_path=dest,
                tags=_generate_gcp_tags(category, name),
            )
        )
    return entries


def collect_gcp_core_product_icons(assets_root: Path) -> list[IconEntry]:
    """GCP core product icons. Each top-level subdir is a product whose name
    maps to a higher-level category via GCP_PRODUCT_CATEGORY_MAP.
    """
    pkg_root = assets_root / _GCP_CORE_PKG
    if not pkg_root.exists():
        logger.warning(f"{_GCP_CORE_PKG} not found: {pkg_root}")
        return []

    entries: list[IconEntry] = []
    for svg in _iter_svgs(pkg_root):
        if _path_contains_png_only(svg, pkg_root):
            continue
        try:
            rel = svg.relative_to(pkg_root)
        except ValueError:
            continue
        if not rel.parts:
            continue
        product_dir = rel.parts[0]
        if Path(product_dir).suffix.lower() == ".svg":
            # Flat layout — no product dir, fall back to general
            category = "general"
            name = clean_name(svg.stem)
        else:
            category = _infer_gcp_category(product_dir)
            name = clean_name(svg.stem) or sanitize_category(product_dir)
        if not name:
            continue
        icon_id = generate_canonical_id("gcp", category, name)
        dest = ICONS_DIR / "gcp" / category / f"{name}.svg"
        entries.append(
            IconEntry(
                id=icon_id,
                vendor="gcp",
                category=category,
                name=_format_display_name("gcp", name),
                filename=f"{name}.svg",
                source_path=svg,
                dest_path=dest,
                tags=_generate_gcp_tags(category, name),
            )
        )
    return entries


def collect_gcp_extended_icons(assets_root: Path) -> list[IconEntry]:
    """GCP extended product icons (`gcp-icon-package`).

    Layout: ``{product_dir}/{product_dir}.svg`` (one product per top-level subdir).
    Categories are derived from the existing GCP product→category map (matched
    case/separator-insensitively); unmapped products fall under ``products``.
    """
    pkg_root = assets_root / _GCP_EXTENDED_PKG
    if not pkg_root.exists():
        logger.warning(f"{_GCP_EXTENDED_PKG} not found: {pkg_root}")
        return []

    entries: list[IconEntry] = []
    for svg in _iter_svgs(pkg_root):
        if _path_contains_png_only(svg, pkg_root):
            continue
        try:
            rel = svg.relative_to(pkg_root)
        except ValueError:
            continue
        if not rel.parts:
            continue
        product_dir = rel.parts[0]
        if Path(product_dir).suffix.lower() == ".svg":
            category = "products"
            name = clean_name(svg.stem)
        else:
            category = _infer_gcp_extended_category(product_dir)
            name = clean_name(svg.stem) or clean_name(product_dir)
        if not name:
            continue
        icon_id = generate_canonical_id("gcp", category, name)
        dest = ICONS_DIR / "gcp" / category / f"{name}.svg"
        entries.append(
            IconEntry(
                id=icon_id,
                vendor="gcp",
                category=category,
                name=_format_display_name("gcp", name),
                filename=f"{name}.svg",
                source_path=svg,
                dest_path=dest,
                tags=_generate_gcp_tags(category, name),
            )
        )
    return entries


def collect_gcp_icons(assets_root: Path) -> list[IconEntry]:
    """All GCP icons (category + core products + extended product set)."""
    entries: list[IconEntry] = []
    entries.extend(collect_gcp_category_icons(assets_root))
    entries.extend(collect_gcp_core_product_icons(assets_root))
    entries.extend(collect_gcp_extended_icons(assets_root))
    return entries


# ---------------------------------------------------------------------------
# CNCF Handler
# ---------------------------------------------------------------------------
# Package: `cncf-icon-package/`. Each top-level subdir is a CNCF project, with
# nested ``{layout}/{variant}/*.svg`` (e.g. ``icon/color/foo-icon-color.svg``).
# We pick a single representative SVG per project, preferring square color icons.

_CNCF_PKG = "cncf-icon-package"
_CNCF_VARIANT_PRIORITY: tuple[tuple[str, str], ...] = (
    ("icon", "color"),
    ("icon", "black"),
    ("icon", "white"),
    ("stacked", "color"),
    ("horizontal", "color"),
    ("stacked", "black"),
    ("horizontal", "black"),
)


def _pick_cncf_svg(project_dir: Path) -> Path | None:
    """Return the preferred representative SVG for a CNCF project directory."""
    for layout, variant in _CNCF_VARIANT_PRIORITY:
        cand_dir = project_dir / layout / variant
        if cand_dir.is_dir():
            svgs = sorted(cand_dir.glob("*.svg"))
            if svgs:
                return svgs[0]
    # Last resort: any SVG anywhere under the project
    all_svgs = sorted(project_dir.rglob("*.svg"))
    return all_svgs[0] if all_svgs else None


def collect_cncf_icons(assets_root: Path) -> list[IconEntry]:
    """All CNCF project icons under `cncf-icon-package/`."""
    pkg_root = assets_root / _CNCF_PKG
    if not pkg_root.exists():
        logger.warning(f"{_CNCF_PKG} not found: {pkg_root}")
        return []

    entries: list[IconEntry] = []
    for project_dir in sorted(p for p in pkg_root.iterdir() if p.is_dir()):
        chosen = _pick_cncf_svg(project_dir)
        if chosen is None:
            continue
        name = clean_name(project_dir.name)
        if not name:
            continue
        category = "cncf"
        icon_id = generate_canonical_id("cncf", category, name)
        dest = ICONS_DIR / "cncf" / category / f"{name}.svg"
        tags = list(dict.fromkeys(["cncf", "cloud-native", *name.split("-")[:3]]))
        entries.append(
            IconEntry(
                id=icon_id,
                vendor="cncf",
                category=category,
                name=_format_display_name("cncf", name),
                filename=f"{name}.svg",
                source_path=chosen,
                dest_path=dest,
                tags=tags,
            )
        )
    return entries


# ---------------------------------------------------------------------------
# Microsoft Handler
# ---------------------------------------------------------------------------


def _collect_microsoft_fixed_category(
    assets_root: Path,
    pkg_name: str,
    category: str,
    tags: list[str],
    *,
    name_includes: list[str] | None = None,
    name_excludes: list[str] | None = None,
    path_excludes: list[str] | None = None,
) -> list[IconEntry]:
    """Generic Microsoft package collector: rglob + filters + fixed category."""
    pkg_root = assets_root / pkg_name
    if not pkg_root.exists():
        logger.warning(f"{pkg_name} not found: {pkg_root}")
        return []

    entries: list[IconEntry] = []
    for svg in _iter_svgs(pkg_root):
        stem_lower = svg.stem.lower()
        path_lower = str(svg).lower()

        if name_includes and not any(tok in stem_lower for tok in name_includes):
            continue
        if name_excludes and any(tok in stem_lower for tok in name_excludes):
            continue
        if path_excludes and any(tok in path_lower for tok in path_excludes):
            continue

        name = clean_name(svg.stem)
        if not name:
            continue
        icon_id = generate_canonical_id("microsoft", category, name)
        dest = ICONS_DIR / "microsoft" / category / f"{name}.svg"
        entries.append(
            IconEntry(
                id=icon_id,
                vendor="microsoft",
                category=category,
                name=_format_display_name("microsoft", name),
                filename=f"{name}.svg",
                source_path=svg,
                dest_path=dest,
                tags=list(tags),
            )
        )
    return entries


def collect_microsoft_dynamics_icons(assets_root: Path) -> list[IconEntry]:
    return _collect_microsoft_fixed_category(
        assets_root,
        pkg_name="dynamics-365-icon-package",
        category="dynamics-365",
        tags=["dynamics-365", "business-applications", "microsoft"],
    )


def collect_microsoft_fabric_icons(assets_root: Path) -> list[IconEntry]:
    """Microsoft Fabric — prefer 20px/24px filled/color variants, drop 'regular'.
    Tolerates either historical (`package/dist/svg/`) or current (`svg/`) layouts.
    """
    return _collect_microsoft_fixed_category(
        assets_root,
        pkg_name="microsoft-fabric-icon-package",
        category="fabric",
        tags=["fabric", "data-platform", "microsoft"],
        name_includes=["_20_", "_24_"],
        name_excludes=["regular"],
    )


def collect_microsoft_power_platform_icons(assets_root: Path) -> list[IconEntry]:
    return _collect_microsoft_fixed_category(
        assets_root,
        pkg_name="power-platform-icon-package",
        category="power-platform",
        tags=["power-platform", "low-code", "microsoft"],
    )


def collect_microsoft_entra_icons(assets_root: Path) -> list[IconEntry]:
    """Microsoft Entra — exclude BW variants, keep color set."""
    return _collect_microsoft_fixed_category(
        assets_root,
        pkg_name="microsoft-entra-architecture-icon-package",
        category="entra",
        tags=["entra", "identity", "security", "microsoft"],
        path_excludes=["bw icons", "/bw/"],
    )


def collect_microsoft_365_icons(assets_root: Path) -> list[IconEntry]:
    return _collect_microsoft_fixed_category(
        assets_root,
        pkg_name="microsoft-365-content-icon-package",
        category="microsoft-365",
        tags=["microsoft-365", "productivity", "microsoft"],
    )


def collect_microsoft_icons(assets_root: Path) -> list[IconEntry]:
    """Aggregate all Microsoft icons."""
    entries: list[IconEntry] = []
    entries.extend(collect_microsoft_dynamics_icons(assets_root))
    entries.extend(collect_microsoft_fabric_icons(assets_root))
    entries.extend(collect_microsoft_power_platform_icons(assets_root))
    entries.extend(collect_microsoft_entra_icons(assets_root))
    entries.extend(collect_microsoft_365_icons(assets_root))
    return entries


# ---------------------------------------------------------------------------
# Devicon Handler
# ---------------------------------------------------------------------------
# Package: `dev-icon-package/` (the [devicon](https://devicon.dev) project).
# Each top-level subdir is one technology with multiple variant SVGs such as
# ``{name}-original.svg``, ``{name}-plain.svg``, ``{name}-line.svg`` plus
# `-wordmark` versions. We pick a single representative, preferring solid
# logo variants over wordmarks.

_DEVICON_PKG = "dev-icon-package"
_DEVICON_VARIANT_PRIORITY: tuple[str, ...] = (
    "original",
    "plain",
    "line",
    "original-wordmark",
    "plain-wordmark",
    "line-wordmark",
)


def _pick_devicon_svg(project_dir: Path) -> Path | None:
    """Return the preferred representative SVG for a devicon project directory."""
    project = project_dir.name
    for variant in _DEVICON_VARIANT_PRIORITY:
        candidate = project_dir / f"{project}-{variant}.svg"
        if candidate.is_file():
            return candidate
    # Last resort: first SVG (alphabetical) directly under the project
    svgs = sorted(project_dir.glob("*.svg"))
    return svgs[0] if svgs else None


def collect_devicon_icons(assets_root: Path) -> list[IconEntry]:
    """All technology icons under `dev-icon-package/` (devicon)."""
    pkg_root = assets_root / _DEVICON_PKG
    if not pkg_root.exists():
        logger.warning(f"{_DEVICON_PKG} not found: {pkg_root}")
        return []

    entries: list[IconEntry] = []
    for project_dir in sorted(p for p in pkg_root.iterdir() if p.is_dir()):
        chosen = _pick_devicon_svg(project_dir)
        if chosen is None:
            continue
        name = clean_name(project_dir.name)
        if not name:
            continue
        category = "devicon"
        icon_id = generate_canonical_id("devicon", category, name)
        dest = ICONS_DIR / "devicon" / category / f"{name}.svg"
        tags = list(dict.fromkeys(["devicon", "technology", *name.split("-")[:3]]))
        entries.append(
            IconEntry(
                id=icon_id,
                vendor="devicon",
                category=category,
                name=_format_display_name("devicon", name),
                filename=f"{name}.svg",
                source_path=chosen,
                dest_path=dest,
                tags=tags,
            )
        )
    return entries


# ---------------------------------------------------------------------------
# Developer Icons Handler
# ---------------------------------------------------------------------------
# Package: `developer-icons-package/` — flat layout with one SVG per icon.
# Variant priority: plain > colored > dark/light > wordmark.
# Many icons have multiple variants (e.g., `github-dark`, `github-light`,
# `github-dark-wordmark`); we pick the best representative.

_DEVELOPER_PKG = "developer-icons-package"

# Priority: plain name first, then color-specific variants, wordmarks last
_DEVELOPER_VARIANT_ORDER: tuple[str, ...] = (
    "",  # plain (e.g., android.svg)
    "original",  # original-color variants
    "colored",  # colored variants
    "color",  # color variants
    "dark",  # dark theme
    "light",  # light theme
    "basic-dark",  # basic dark
    "basic-light",  # basic light
    "wordmark",  # wordmark versions (lowest)
    "dark-wordmark",
    "light-wordmark",
    "basic",
)


def _pick_developer_svg(package_dir: Path, base_name: str, variants: list[Path]) -> Path | None:
    """Pick the best SVG variant for a developer icon."""
    # Build a lookup: variant_suffix -> Path
    by_suffix: dict[str, Path] = {}
    for p in variants:
        stem = p.stem
        if stem == base_name:
            suffix = ""
        elif stem.startswith(base_name + "-"):
            suffix = stem[len(base_name) + 1 :]
        else:
            continue
        by_suffix[suffix] = p

    for order_suffix in _DEVELOPER_VARIANT_ORDER:
        if order_suffix in by_suffix:
            return by_suffix[order_suffix]

    # Fallback: return any variant that starts with base_name
    for p in variants:
        if p.stem == base_name or p.stem.startswith(base_name + "-"):
            return p

    return None


def _group_developer_icons(package_dir: Path) -> dict[str, list[Path]]:
    """Group developer icon SVGs by base name.

    Returns dict of base_name -> list of SVG paths (including all variants).
    """
    groups: dict[str, list[Path]] = {}

    for svg_path in sorted(package_dir.glob("*.svg")):
        stem = svg_path.stem
        # Try to determine the base name by stripping known suffixes
        base = stem
        for suffix in [
            "-original",
            "-colored",
            "-color",
            "-dark-wordmark",
            "-light-wordmark",
            "-basic-dark",
            "-basic-light",
            "-dark",
            "-light",
            "-wordmark",
            "-basic",
        ]:
            if base.endswith(suffix):
                base = base[: -len(suffix)]
                break

        groups.setdefault(base, []).append(svg_path)

    return groups


def collect_developer_icons(assets_root: Path) -> list[IconEntry]:
    """All technology icons under `developer-icons-package/`."""
    pkg_root = assets_root / _DEVELOPER_PKG
    if not pkg_root.exists():
        logger.warning(f"{_DEVELOPER_PKG} not found: {pkg_root}")
        return []

    entries: list[IconEntry] = []
    groups = _group_developer_icons(pkg_root)

    for base_name, svg_list in sorted(groups.items()):
        chosen = _pick_developer_svg(pkg_root, base_name, svg_list)
        if chosen is None:
            continue
        name = clean_name(base_name)
        if not name:
            continue
        category = "developer"
        icon_id = generate_canonical_id("developer", category, name)
        dest = ICONS_DIR / "developer" / category / f"{name}.svg"
        tags = list(dict.fromkeys(["developer", "development", *name.split("-")[:3]]))
        entries.append(
            IconEntry(
                id=icon_id,
                vendor="developer",
                category=category,
                name=_format_display_name("developer", name),
                filename=f"{name}.svg",
                source_path=chosen,
                dest_path=dest,
                tags=tags,
            )
        )
    return entries


# ---------------------------------------------------------------------------
# Display / tag helpers
# ---------------------------------------------------------------------------

_ACRONYMS = {
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
_VENDOR_DISPLAY = {
    "aws": "AWS",
    "azure": "Azure",
    "gcp": "GCP",
    "microsoft": "Microsoft",
    "cncf": "CNCF",
    "devicon": "Devicon",
    "developer": "Developer",
}


def _format_display_name(vendor: str, kebab_name: str) -> str:
    words = kebab_name.split("-")
    display_words = [w.upper() if w in _ACRONYMS else w.capitalize() for w in words]
    prefix = _VENDOR_DISPLAY.get(vendor, vendor.capitalize())
    return f"{prefix} {' '.join(display_words)}"


def _generate_aws_tags(category: str, name: str) -> list[str]:
    tags = ["aws", category, *name.split("-")[:3]]
    return list(dict.fromkeys(tags))


def _generate_azure_tags(category: str, name: str) -> list[str]:
    tags = ["azure", category, *name.split("-")[:3]]
    return list(dict.fromkeys(tags))


def _generate_gcp_tags(category: str, name: str) -> list[str]:
    tags = ["gcp", category, *name.split("-")[:3]]
    return list(dict.fromkeys(tags))


GCP_PRODUCT_CATEGORY_MAP: dict[str, str] = {
    # AI / ML
    "AI Hub": "ai-machine-learning",
    "AI Hypercomputer": "ai-machine-learning",
    "AI Platform": "ai-machine-learning",
    "AI Platform Unified": "ai-machine-learning",
    "Advanced Agent Modeling": "ai-machine-learning",
    "Advanced Solutions Lab": "ai-machine-learning",
    "Agent Assist": "ai-machine-learning",
    "AutoML": "ai-machine-learning",
    "AutoML Natural Language": "ai-machine-learning",
    "AutoML Tables": "ai-machine-learning",
    "AutoML Translation": "ai-machine-learning",
    "AutoML Video Intelligence": "ai-machine-learning",
    "AutoML Vision": "ai-machine-learning",
    "Cloud Inference API": "ai-machine-learning",
    "Cloud Natural Language API": "ai-machine-learning",
    "Cloud Optimization AI": "ai-machine-learning",
    "Cloud Optimization AI - Fleet Routing API": "ai-machine-learning",
    "Cloud Translation API": "ai-machine-learning",
    "Cloud Vision API": "ai-machine-learning",
    "Contact Center AI": "ai-machine-learning",
    "Data Labeling": "ai-machine-learning",
    "Data QnA": "ai-machine-learning",
    "Dialogflow": "ai-machine-learning",
    "Dialogflow CX": "ai-machine-learning",
    "Dialogflow Insights": "ai-machine-learning",
    "Document AI": "ai-machine-learning",
    "Healthcare NLP API": "ai-machine-learning",
    "Media Translation API": "ai-machine-learning",
    "Real-World Insights": "ai-machine-learning",
    "Recommendations AI": "ai-machine-learning",
    "Retail API": "ai-machine-learning",
    "Speech-to-Text": "ai-machine-learning",
    "TensorFlow Enterprise": "ai-machine-learning",
    "Text-to-Speech": "ai-machine-learning",
    "Vertex AI": "ai-machine-learning",
    "VertexAI": "ai-machine-learning",
    "Video Intelligence API": "ai-machine-learning",
    "Visual Inspection": "ai-machine-learning",
    # Compute
    "Bare Metal Solutions": "compute",
    "Batch": "compute",
    "Cloud GPU": "compute",
    "Cloud TPU": "compute",
    "Compute Engine": "compute",
    "GCE Systems Management": "compute",
    "Local SSD": "compute",
    "Persistent Disk": "compute",
    # Serverless
    "App Engine": "serverless-computing",
    "Cloud Functions": "serverless-computing",
    "Cloud Run": "serverless-computing",
    "Cloud Run for Anthos": "serverless-computing",
    "Cloud Scheduler": "serverless-computing",
    "Cloud Tasks": "serverless-computing",
    "Eventarc": "serverless-computing",
    "KubeRun": "serverless-computing",
    "Workflows": "serverless-computing",
    # Containers
    "Artifact Registry": "containers",
    "Cloud Build": "containers",
    "Cloud Deploy": "containers",
    "Container Optimized OS": "containers",
    "Container Registry": "containers",
    "GKE": "containers",
    "GKE On-Prem": "containers",
    "Google Kubernetes Engine": "containers",
    "Migrate for Anthos": "containers",
    # Databases
    "AlloyDB": "databases",
    "BigTable": "databases",
    "Bigtable": "databases",
    "Cloud SQL": "databases",
    "Cloud Spanner": "databases",
    "Database Migration Service": "databases",
    "Datastore": "databases",
    "Firestore": "databases",
    "Memorystore": "databases",
    # Data analytics
    "Analytics Hub": "data-analytics",
    "BigQuery": "data-analytics",
    "Cloud Composer": "data-analytics",
    "Cloud Data Fusion": "data-analytics",
    "Data Catalog": "data-analytics",
    "Data Studio": "data-analytics",
    "Data Transfer": "data-analytics",
    "Dataflow": "data-analytics",
    "Datalab": "data-analytics",
    "Dataplex": "data-analytics",
    "Datapol": "data-analytics",
    "Dataprep": "data-analytics",
    "Dataproc": "data-analytics",
    "Dataproc Metastore": "data-analytics",
    "Datashare": "data-analytics",
    "Datastream": "data-analytics",
    "Looker": "data-analytics",
    "PubSub": "data-analytics",
    "Stream Suite": "data-analytics",
    # Storage
    "Cloud Storage": "storage",
    "Filestore": "storage",
    "Hyperdisk": "storage",
    "Transfer": "storage",
    "Transfer Appliance": "storage",
    # Networking
    "Cloud CDN": "networking",
    "Cloud DNS": "networking",
    "Cloud Domains": "networking",
    "Cloud External IP Addresses": "networking",
    "Cloud Firewall Rules": "networking",
    "Cloud Interconnect": "networking",
    "Cloud Load Balancing": "networking",
    "Cloud Media Edge": "networking",
    "Cloud NAT": "networking",
    "Cloud Network": "networking",
    "Cloud Router": "networking",
    "Cloud Routes": "networking",
    "Cloud VPN": "networking",
    "Connectivity Test": "networking",
    "Network Connectivity Center": "networking",
    "Network Intelligence Center": "networking",
    "Network Security": "networking",
    "Network Tiers": "networking",
    "Network Topology": "networking",
    "Partner Interconnect": "networking",
    "Premium Network Tier": "networking",
    "Private Connectivity": "networking",
    "Private Service Connect": "networking",
    "Service Discovery": "networking",
    "Standard Network Tier": "networking",
    "Traffic Director": "networking",
    "Virtual Private Cloud": "networking",
    # Security / Identity
    "Access Context Manager": "security-identity",
    "Assured Workloads": "security-identity",
    "BeyondCorp": "security-identity",
    "Binary Authorization": "security-identity",
    "Certificate Authority Service": "security-identity",
    "Certificate Manager": "security-identity",
    "Cloud Armor": "security-identity",
    "Cloud Audit Logs": "security-identity",
    "Cloud EKM": "security-identity",
    "Cloud HSM": "security-identity",
    "Cloud Healthcare API": "security-identity",
    "Cloud IDS": "security-identity",
    "Cloud Security Scanner": "security-identity",
    "Data Loss Prevention API": "security-identity",
    "IAM": "security-identity",
    "Identity and Access Management": "security-identity",
    "Identity Platform": "security-identity",
    "Identity-Aware Proxy": "security-identity",
    "Key Access Justifications": "security-identity",
    "Key Management Service": "security-identity",
    "Managed Service for Microsoft Active Directory": "security-identity",
    "Mandiant": "security-identity",
    "Phishing Protection": "security-identity",
    "Policy Analyzer": "security-identity",
    "Risk Manager": "security-identity",
    "Secret Manager": "security-identity",
    "Security Command Center": "security-identity",
    "Security Health Advisor": "security-identity",
    "Security Key Enforcement": "security-identity",
    "Security Operations": "security-identity",
    "Threat Intelligence": "security-identity",
    "Web Risk": "security-identity",
    "Web Security Scanner": "security-identity",
    "Workload Identity Pool": "security-identity",
    # Hybrid / Multicloud
    "Anthos": "hybrid-and-multicloud",
    "Anthos Config Management": "hybrid-and-multicloud",
    "Anthos Service Mesh": "hybrid-and-multicloud",
    "Configuration Management": "hybrid-and-multicloud",
    "Distributed Cloud": "hybrid-and-multicloud",
    "Migrate for Compute Engine": "hybrid-and-multicloud",
    "VMware Engine": "hybrid-and-multicloud",
    # API / Integration
    "API": "integration-services",
    "API Analytics": "integration-services",
    "API Monetization": "integration-services",
    "Apigee": "integration-services",
    "Apigee API Platform": "integration-services",
    "Apigee Sense": "integration-services",
    "Cloud API Gateway": "integration-services",
    "Cloud APIs": "integration-services",
    "Cloud Endpoints": "integration-services",
    # Developer Tools
    "Cloud Code": "developer-tools",
    "Cloud Shell": "developer-tools",
    "Debugger": "developer-tools",
    "Error Reporting": "developer-tools",
    "Profiler": "developer-tools",
    "Stackdriver": "developer-tools",
    "Tools for PowerShell": "developer-tools",
    "Trace": "developer-tools",
    # Management
    "Administration": "management-tools",
    "Asset Inventory": "management-tools",
    "Billing": "management-tools",
    "Catalog": "management-tools",
    "Cloud Asset Inventory": "management-tools",
    "Cloud Deployment Manager": "management-tools",
    "Cloud Logging": "management-tools",
    "Cloud Monitoring": "management-tools",
    "Cloud Ops": "management-tools",
    "OS Configuration Management": "management-tools",
    "OS Inventory Management": "management-tools",
    "OS Patch Management": "management-tools",
    "Performance Dashboard": "management-tools",
    "Quotas": "management-tools",
    "Runtime Config": "management-tools",
    # Marketplace / Portals
    "Cloud Healthcare Marketplace": "marketplace",
    "Developer Portal": "marketplace",
    "Financial Services Marketplace": "marketplace",
    "Google Cloud Marketplace": "marketplace",
    "Launcher": "marketplace",
    "Partner Portal": "marketplace",
    "Producer Portal": "marketplace",
    # IoT
    "IoT Core": "iot",
    "IoT Edge": "iot",
    # Specialised
    "Cloud for Marketing": "industry-solutions",
    "Cloud Jobs API": "industry-solutions",
    "Fleet Engine": "industry-solutions",
    "Game Servers": "industry-solutions",
    "Genomics": "industry-solutions",
    "Google Maps Platform": "industry-solutions",
    "Quantum Engine": "industry-solutions",
}


def _infer_gcp_category(product_name: str) -> str:
    if product_name in GCP_PRODUCT_CATEGORY_MAP:
        return GCP_PRODUCT_CATEGORY_MAP[product_name]
    return sanitize_category(product_name) or "general"


# Normalized lookup for `gcp-icon-package` whose dir names are snake_case
# (e.g. "cloud_storage" → matches "Cloud Storage" → "storage").
_GCP_NORMALIZED_CATEGORY_MAP: dict[str, str] = {sanitize_category(k): v for k, v in GCP_PRODUCT_CATEGORY_MAP.items()}


def _infer_gcp_extended_category(product_dir: str) -> str:
    """Category for a product in `gcp-icon-package`.

    Looks up via the normalized GCP product→category map; falls back to a
    generic ``products`` bucket so the catalog stays browsable rather than
    exploding into hundreds of single-icon categories.
    """
    key = sanitize_category(product_dir)
    return _GCP_NORMALIZED_CATEGORY_MAP.get(key, "products")


# ---------------------------------------------------------------------------
# Deduplication / aggregation
# ---------------------------------------------------------------------------


def deduplicate_entries(entries: list[IconEntry]) -> list[IconEntry]:
    """Remove duplicates by canonical ID; first occurrence wins."""
    seen: set[str] = set()
    deduped: list[IconEntry] = []
    for entry in entries:
        if entry.id in seen:
            logger.debug(f"Duplicate icon ID skipped: {entry.id}")
            continue
        seen.add(entry.id)
        deduped.append(entry)
    return deduped


def collect_all_icons(assets_root: Path) -> list[IconEntry]:
    """Collect and deduplicate icons from every vendor."""
    entries: list[IconEntry] = []
    entries.extend(collect_aws_icons(assets_root))
    entries.extend(collect_azure_icons(assets_root))
    entries.extend(collect_gcp_icons(assets_root))
    entries.extend(collect_microsoft_icons(assets_root))
    entries.extend(collect_cncf_icons(assets_root))
    entries.extend(collect_devicon_icons(assets_root))
    entries.extend(collect_developer_icons(assets_root))
    return deduplicate_entries(entries)
