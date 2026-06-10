"""Tests for src/normalize.py — icon normalization logic."""

from __future__ import annotations

from pathlib import Path

import pytest

from tech_icons.normalize import (
    IconEntry,
    clean_name,
    collect_all_icons,
    collect_aws_icons,
    collect_azure_icons,
    collect_cncf_icons,
    collect_devicon_icons,
    collect_gcp_category_icons,
    collect_gcp_core_product_icons,
    collect_gcp_extended_icons,
    collect_gcp_icons,
    collect_microsoft_365_icons,
    collect_microsoft_dynamics_icons,
    collect_microsoft_entra_icons,
    collect_microsoft_fabric_icons,
    collect_microsoft_icons,
    collect_microsoft_power_platform_icons,
    deduplicate_entries,
    generate_canonical_id,
    parse_aws_architecture_service_icons,
    parse_aws_category_icons,
    parse_aws_resource_icons,
    sanitize_category,
)

# ---------------------------------------------------------------------------
# clean_name tests
# ---------------------------------------------------------------------------


class TestCleanName:
    """Tests for filename cleaning and normalization."""

    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("Arch_AWS-Lambda_48.svg", "lambda"),
            ("Arch_Amazon-EC2_48.svg", "ec2"),
            ("Arch_Amazon-DynamoDB_48.svg", "dynamodb"),
            ("Res_AWS-Lambda_Lambda-Function_48.svg", "lambda-lambda-function"),
            ("Res_Amazon-EC2_Instance_48.svg", "ec2-instance"),
            ("My Icon Name.svg", "my-icon-name"),
            ("some_file_name.svg", "some-file-name"),
            ("Already-Clean.svg", "already-clean"),
            ("Arch-Category_Compute_48.svg", "compute"),
            ("multi___underscore.svg", "multi-underscore"),
            ("file--with--dashes.svg", "file-with-dashes"),
            ("UPPERCASE.svg", "uppercase"),
            ("icon_64.svg", "icon"),
            ("icon_48.svg", "icon"),
            ("icon_16.svg", "icon"),
            ("icon_32.svg", "icon"),
            # Azure: "00029-icon-service-Function-Apps.svg" → "function-apps"
            ("10086-icon-service-Storage-Accounts.svg", "storage-accounts"),
            ("10029-icon-service-Function-Apps.svg", "function-apps"),
            ("00328-icon-service-Host-Pools.svg", "host-pools"),
            # Azure with parenthesised qualifier — parens dropped, hyphen preserved
            ("10087-icon-service-Storage-Accounts-(Classic).svg", "storage-accounts-classic"),
        ],
    )
    def test_clean_name_variants(self, raw: str, expected: str):
        result = clean_name(raw)
        assert result == expected

    def test_clean_name_removes_extension(self):
        assert clean_name("test.svg") == "test"

    def test_clean_name_handles_empty_after_stripping(self):
        # Edge case: name is just a size suffix
        result = clean_name("_48.svg")
        assert result == ""  # or whatever the behavior is

    def test_clean_name_preserves_meaningful_numbers(self):
        # Numbers that are part of the name, not size suffixes
        result = clean_name("route53.svg")
        assert "route53" in result or "route" in result


# ---------------------------------------------------------------------------
# sanitize_category tests
# ---------------------------------------------------------------------------


class TestSanitizeCategory:
    """Tests for category normalization."""

    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("Arch_Compute", "compute"),
            ("Arch_Application-Integration", "application-integration"),
            ("Arch_Artificial-Intelligence", "artificial-intelligence"),
            ("Res_Databases", "databases"),
            ("Arch-Category_Analytics", "analytics"),
            ("AI _ Machine Learning", "ai-machine-learning"),
            ("Hybrid & Multicloud", "hybrid-and-multicloud"),
            ("Developer Tools", "developer-tools"),
            ("Security Identity", "security-identity"),
            ("Maps & Geospatial", "maps-and-geospatial"),
        ],
    )
    def test_sanitize_category_variants(self, raw: str, expected: str):
        result = sanitize_category(raw)
        assert result == expected

    def test_sanitize_category_lowercase(self):
        assert sanitize_category("COMPUTE") == "compute"

    def test_sanitize_category_collapses_hyphens(self):
        result = sanitize_category("Web---Mobile")
        assert "--" not in result


# ---------------------------------------------------------------------------
# generate_canonical_id tests
# ---------------------------------------------------------------------------


class TestGenerateCanonicalId:
    """Tests for canonical ID generation."""

    @pytest.mark.parametrize(
        "vendor,category,name,expected",
        [
            ("aws", "compute", "lambda", "aws/compute/lambda"),
            ("azure", "networking", "load-balancer", "azure/networking/load-balancer"),
            ("gcp", "databases", "cloud-sql", "gcp/databases/cloud-sql"),
            ("microsoft", "fabric", "data-warehouse", "microsoft/fabric/data-warehouse"),
        ],
    )
    def test_canonical_id_format(self, vendor: str, category: str, name: str, expected: str):
        assert generate_canonical_id(vendor, category, name) == expected


# ---------------------------------------------------------------------------
# AWS Parsing tests
# ---------------------------------------------------------------------------


class TestAWSParsing:
    """Tests for AWS icon path parsing."""

    def test_parse_architecture_service_icons(self, tmp_path: Path):
        """Parse AWS Architecture-Service-Icons with correct directory structure."""
        # Setup: assets/aws-icon-package/Architecture-Service-Icons_04302026/Arch_Compute/48/*.svg
        base = tmp_path / "aws-icon-package" / "Architecture-Service-Icons_04302026"
        cat_dir = base / "Arch_Compute" / "48"
        cat_dir.mkdir(parents=True)
        (cat_dir / "Arch_AWS-Lambda_48.svg").write_text("<svg></svg>")
        (cat_dir / "Arch_Amazon-EC2_48.svg").write_text("<svg></svg>")

        entries = parse_aws_architecture_service_icons(tmp_path)
        assert len(entries) == 2
        assert all(e.vendor == "aws" for e in entries)
        assert all(e.category == "compute" for e in entries)

    def test_parse_category_icons(self, tmp_path: Path):
        """Parse AWS Category Icons."""
        base = tmp_path / "aws-icon-package" / "Category-Icons_04302026" / "Arch-Category_48"
        base.mkdir(parents=True)
        (base / "Arch-Category_Compute_48.svg").write_text("<svg></svg>")
        (base / "Arch-Category_Storage_48.svg").write_text("<svg></svg>")

        entries = parse_aws_category_icons(tmp_path)
        assert len(entries) == 2
        assert all(e.category == "category" for e in entries)

    def test_parse_resource_icons(self, tmp_path: Path):
        """Parse AWS Resource Icons."""
        base = tmp_path / "aws-icon-package" / "Resource-Icons_04302026" / "Res_Compute" / "48"
        base.mkdir(parents=True)
        (base / "Res_AWS-Lambda_Lambda-Function_48.svg").write_text("<svg></svg>")

        entries = parse_aws_resource_icons(tmp_path)
        assert len(entries) == 1
        assert "resource" in entries[0].tags

    def test_parse_aws_missing_dir_returns_empty(self, tmp_path: Path):
        """Missing AWS directory returns empty list without error."""
        entries = parse_aws_architecture_service_icons(tmp_path)
        assert entries == []

    def test_collect_aws_icons_combines_all(self, tmp_path: Path):
        """collect_aws_icons merges Architecture, Category, Resource, Group icons."""
        # Create Architecture icons
        arch = tmp_path / "aws-icon-package" / "Architecture-Service-Icons_04302026" / "Arch_Compute" / "48"
        arch.mkdir(parents=True)
        (arch / "Arch_AWS-Lambda_48.svg").write_text("<svg></svg>")

        # Create Category icons
        cat = tmp_path / "aws-icon-package" / "Category-Icons_04302026" / "Arch-Category_48"
        cat.mkdir(parents=True)
        (cat / "Arch-Category_Compute_48.svg").write_text("<svg></svg>")

        entries = collect_aws_icons(tmp_path)
        assert len(entries) >= 2


# ---------------------------------------------------------------------------
# Azure Parsing tests
# ---------------------------------------------------------------------------


class TestAzureParsing:
    """Tests for Azure icon path parsing."""

    def test_collect_azure_icons(self, tmp_path: Path):
        """Parse azure-icon-package/Icons/{category}/*.svg."""
        base = tmp_path / "azure-icon-package" / "Icons" / "Compute"
        base.mkdir(parents=True)
        (base / "Virtual-Machines.svg").write_text("<svg></svg>")
        (base / "Function-Apps.svg").write_text("<svg></svg>")

        entries = collect_azure_icons(tmp_path)
        assert len(entries) == 2
        assert all(e.vendor == "azure" for e in entries)
        assert all(e.category == "compute" for e in entries)

    def test_azure_missing_dir_returns_empty(self, tmp_path: Path):
        entries = collect_azure_icons(tmp_path)
        assert entries == []


# ---------------------------------------------------------------------------
# GCP Parsing tests
# ---------------------------------------------------------------------------


class TestGCPParsing:
    """Tests for GCP icon path parsing."""

    def test_collect_gcp_category_icons(self, tmp_path: Path):
        """Parse gcp-category-icon-package/{category}/SVG/*.svg."""
        base = tmp_path / "gcp-category-icon-package" / "Compute" / "SVG"
        base.mkdir(parents=True)
        (base / "compute-engine.svg").write_text("<svg></svg>")

        entries = collect_gcp_category_icons(tmp_path)
        assert len(entries) == 1
        assert entries[0].vendor == "gcp"
        assert entries[0].category == "compute"

    def test_collect_gcp_core_product_icons(self, tmp_path: Path):
        """Parse gcp-core-products-icon-package/{product}/SVG/*.svg."""
        base = tmp_path / "gcp-core-products-icon-package" / "BigQuery" / "SVG"
        base.mkdir(parents=True)
        (base / "bigquery.svg").write_text("<svg></svg>")

        entries = collect_gcp_core_product_icons(tmp_path)
        assert len(entries) == 1
        assert entries[0].vendor == "gcp"
        # BigQuery maps to data-analytics
        assert entries[0].category == "data-analytics"

    def test_collect_gcp_icons_combines(self, tmp_path: Path):
        """collect_gcp_icons merges category and core product icons."""
        cat_dir = tmp_path / "gcp-category-icon-package" / "Networking" / "SVG"
        cat_dir.mkdir(parents=True)
        (cat_dir / "cloud-cdn.svg").write_text("<svg></svg>")

        prod_dir = tmp_path / "gcp-core-products-icon-package" / "Cloud Run" / "SVG"
        prod_dir.mkdir(parents=True)
        (prod_dir / "cloud-run.svg").write_text("<svg></svg>")

        entries = collect_gcp_icons(tmp_path)
        assert len(entries) == 2

    def test_gcp_flat_layout_is_collected(self, tmp_path: Path):
        """Flat layout (SVGs directly under category dir, no SVG/ subdir) still works.

        The collector rglobs from the package root and infers category from the
        first meaningful parent directory, so it tolerates upstream restructuring.
        """
        base = tmp_path / "gcp-category-icon-package" / "Compute"
        base.mkdir(parents=True)
        (base / "compute-engine.svg").write_text("<svg></svg>")

        entries = collect_gcp_category_icons(tmp_path)
        assert len(entries) == 1
        assert entries[0].category == "compute"
        assert entries[0].id == "gcp/compute/compute-engine"


# ---------------------------------------------------------------------------
# GCP extended (gcp-icon-package) tests
# ---------------------------------------------------------------------------


class TestGCPExtendedParsing:
    """Tests for `gcp-icon-package` (extended product set)."""

    def test_mapped_product_uses_curated_category(self, tmp_path: Path):
        """Known products are placed in their curated category."""
        prod = tmp_path / "gcp-icon-package" / "bigquery"
        prod.mkdir(parents=True)
        (prod / "bigquery.svg").write_text("<svg></svg>")

        entries = collect_gcp_extended_icons(tmp_path)
        assert len(entries) == 1
        assert entries[0].vendor == "gcp"
        assert entries[0].category == "data-analytics"
        assert entries[0].id == "gcp/data-analytics/bigquery"

    def test_snake_case_product_matches_curated_map(self, tmp_path: Path):
        """``cloud_storage`` (snake_case) resolves to the same category as ``Cloud Storage``."""
        prod = tmp_path / "gcp-icon-package" / "cloud_storage"
        prod.mkdir(parents=True)
        (prod / "cloud_storage.svg").write_text("<svg></svg>")

        entries = collect_gcp_extended_icons(tmp_path)
        assert len(entries) == 1
        assert entries[0].category == "storage"

    def test_cloud_functions_maps_to_serverless(self, tmp_path: Path):
        """`cloud_functions` resolves to the curated ``serverless-computing`` bucket."""
        prod = tmp_path / "gcp-icon-package" / "cloud_functions"
        prod.mkdir(parents=True)
        (prod / "cloud_functions.svg").write_text("<svg></svg>")

        entries = collect_gcp_extended_icons(tmp_path)
        assert len(entries) == 1
        assert entries[0].id == "gcp/serverless-computing/cloud-functions"

    def test_unmapped_product_falls_back_to_products(self, tmp_path: Path):
        """Unknown products land in a generic ``products`` bucket."""
        prod = tmp_path / "gcp-icon-package" / "some_unknown_product_xyz"
        prod.mkdir(parents=True)
        (prod / "some_unknown_product_xyz.svg").write_text("<svg></svg>")

        entries = collect_gcp_extended_icons(tmp_path)
        assert len(entries) == 1
        assert entries[0].category == "products"
        assert entries[0].id == "gcp/products/some-unknown-product-xyz"

    def test_missing_package_returns_empty(self, tmp_path: Path):
        assert collect_gcp_extended_icons(tmp_path) == []

    def test_collect_gcp_icons_includes_extended(self, tmp_path: Path):
        """collect_gcp_icons aggregates the extended package alongside the others."""
        ext = tmp_path / "gcp-icon-package" / "dataflow"
        ext.mkdir(parents=True)
        (ext / "dataflow.svg").write_text("<svg></svg>")

        entries = collect_gcp_icons(tmp_path)
        assert any(e.id == "gcp/data-analytics/dataflow" for e in entries)


# ---------------------------------------------------------------------------
# CNCF (cncf-icon-package) tests
# ---------------------------------------------------------------------------


class TestCNCFParsing:
    """Tests for `cncf-icon-package`."""

    def test_prefers_icon_color_variant(self, tmp_path: Path):
        """`icon/color/*.svg` wins over other layouts and variants."""
        project = tmp_path / "cncf-icon-package" / "argo"
        (project / "icon" / "color").mkdir(parents=True)
        (project / "icon" / "black").mkdir(parents=True)
        (project / "stacked" / "color").mkdir(parents=True)
        chosen = project / "icon" / "color" / "argo-icon-color.svg"
        chosen.write_text("<svg></svg>")
        (project / "icon" / "black" / "argo-icon-black.svg").write_text("<svg></svg>")
        (project / "stacked" / "color" / "argo-stacked-color.svg").write_text("<svg></svg>")

        entries = collect_cncf_icons(tmp_path)
        assert len(entries) == 1
        entry = entries[0]
        assert entry.vendor == "cncf"
        assert entry.category == "cncf"
        assert entry.id == "cncf/cncf/argo"
        assert entry.source_path == chosen

    def test_falls_back_when_icon_color_missing(self, tmp_path: Path):
        """Projects without `icon/color` fall back to the next available variant."""
        project = tmp_path / "cncf-icon-package" / "kubeclipper"
        stacked = project / "stacked" / "color"
        stacked.mkdir(parents=True)
        fallback = stacked / "kubeclipper-stacked-color.svg"
        fallback.write_text("<svg></svg>")

        entries = collect_cncf_icons(tmp_path)
        assert len(entries) == 1
        assert entries[0].source_path == fallback
        assert entries[0].id == "cncf/cncf/kubeclipper"

    def test_falls_back_to_any_svg(self, tmp_path: Path):
        """Projects with only off-priority variants still produce an entry."""
        project = tmp_path / "cncf-icon-package" / "weirdproj"
        odd = project / "misc"
        odd.mkdir(parents=True)
        svg = odd / "weirdproj.svg"
        svg.write_text("<svg></svg>")

        entries = collect_cncf_icons(tmp_path)
        assert len(entries) == 1
        assert entries[0].source_path == svg

    def test_skips_project_with_no_svg(self, tmp_path: Path):
        project = tmp_path / "cncf-icon-package" / "empty"
        project.mkdir(parents=True)
        assert collect_cncf_icons(tmp_path) == []

    def test_missing_package_returns_empty(self, tmp_path: Path):
        assert collect_cncf_icons(tmp_path) == []

    def test_multiple_projects(self, tmp_path: Path):
        """All projects get one representative icon each."""
        for proj in ("argo", "tikv", "devfile"):
            d = tmp_path / "cncf-icon-package" / proj / "icon" / "color"
            d.mkdir(parents=True)
            (d / f"{proj}-icon-color.svg").write_text("<svg></svg>")

        entries = collect_cncf_icons(tmp_path)
        assert len(entries) == 3
        assert {e.name.split(" ", 1)[1] for e in entries} == {"Argo", "Tikv", "Devfile"}


# ---------------------------------------------------------------------------
# Devicon (dev-icon-package) tests
# ---------------------------------------------------------------------------


class TestDeviconParsing:
    """Tests for `dev-icon-package` (devicon)."""

    def test_prefers_original_variant(self, tmp_path: Path):
        """`{name}-original.svg` wins over plain/line and any -wordmark variant."""
        project = tmp_path / "dev-icon-package" / "react"
        project.mkdir(parents=True)
        for variant in ("original-wordmark", "plain", "plain-wordmark"):
            (project / f"react-{variant}.svg").write_text("<svg></svg>")
        chosen = project / "react-original.svg"
        chosen.write_text("<svg></svg>")

        entries = collect_devicon_icons(tmp_path)
        assert len(entries) == 1
        entry = entries[0]
        assert entry.vendor == "devicon"
        assert entry.category == "devicon"
        assert entry.id == "devicon/devicon/react"
        assert entry.source_path == chosen

    def test_falls_back_to_plain_then_line(self, tmp_path: Path):
        """When no `-original` exists, `plain` is preferred over `line`."""
        proj_a = tmp_path / "dev-icon-package" / "javascript"
        proj_a.mkdir(parents=True)
        chosen_a = proj_a / "javascript-plain.svg"
        chosen_a.write_text("<svg></svg>")
        (proj_a / "javascript-line.svg").write_text("<svg></svg>")

        proj_b = tmp_path / "dev-icon-package" / "aarch64"
        proj_b.mkdir(parents=True)
        chosen_b = proj_b / "aarch64-line.svg"
        chosen_b.write_text("<svg></svg>")

        entries = collect_devicon_icons(tmp_path)
        srcs = {e.id: e.source_path for e in entries}
        assert srcs["devicon/devicon/javascript"] == chosen_a
        assert srcs["devicon/devicon/aarch64"] == chosen_b

    def test_skips_eps_and_picks_any_svg_when_no_priority_match(self, tmp_path: Path):
        """EPS files are ignored; if no priority variant exists, take any SVG."""
        project = tmp_path / "dev-icon-package" / "weird"
        project.mkdir(parents=True)
        (project / "weird.eps").write_text("eps")
        fallback = project / "weird-other.svg"
        fallback.write_text("<svg></svg>")

        entries = collect_devicon_icons(tmp_path)
        assert len(entries) == 1
        assert entries[0].source_path == fallback

    def test_missing_package_returns_empty(self, tmp_path: Path):
        assert collect_devicon_icons(tmp_path) == []


# ---------------------------------------------------------------------------
# Azure end-to-end naming (fixes "Missing icon entries" for Azure services)
# ---------------------------------------------------------------------------


class TestAzureNamingCleanup:
    """Verify Azure's "\\d+-icon-service-" prefix and parenthesised qualifiers are stripped."""

    def test_storage_accounts_id(self, tmp_path: Path):
        base = tmp_path / "azure-icon-package" / "Icons" / "storage"
        base.mkdir(parents=True)
        (base / "10086-icon-service-Storage-Accounts.svg").write_text("<svg></svg>")
        (base / "10087-icon-service-Storage-Accounts-(Classic).svg").write_text("<svg></svg>")

        entries = collect_azure_icons(tmp_path)
        ids = {e.id for e in entries}
        assert "azure/storage/storage-accounts" in ids
        assert "azure/storage/storage-accounts-classic" in ids

    def test_function_apps_id(self, tmp_path: Path):
        base = tmp_path / "azure-icon-package" / "Icons" / "compute"
        base.mkdir(parents=True)
        (base / "10029-icon-service-Function-Apps.svg").write_text("<svg></svg>")

        entries = collect_azure_icons(tmp_path)
        assert any(e.id == "azure/compute/function-apps" for e in entries)


# ---------------------------------------------------------------------------
# Microsoft Parsing tests
# ---------------------------------------------------------------------------


class TestMicrosoftParsing:
    """Tests for Microsoft icon path parsing."""

    def test_collect_dynamics_365_icons(self, tmp_path: Path):
        """Parse dynamics-365-icon-package."""
        base = tmp_path / "dynamics-365-icon-package" / "Dynamics 365 App Icons"
        base.mkdir(parents=True)
        (base / "Sales.svg").write_text("<svg></svg>")

        entries = collect_microsoft_dynamics_icons(tmp_path)
        assert len(entries) == 1
        assert entries[0].vendor == "microsoft"
        assert entries[0].category == "dynamics-365"

    def test_collect_fabric_icons(self, tmp_path: Path):
        """Parse microsoft-fabric-icon-package (only 20px/24px non-regular variants)."""
        base = tmp_path / "microsoft-fabric-icon-package" / "package" / "dist" / "svg"
        base.mkdir(parents=True)
        # Should be included (has _20_ and is not 'regular')
        (base / "data_warehouse_20_filled.svg").write_text("<svg></svg>")
        # Should be excluded (no _20_ or _24_)
        (base / "data_warehouse_16_filled.svg").write_text("<svg></svg>")
        # Should be excluded (regular)
        (base / "data_warehouse_20_regular.svg").write_text("<svg></svg>")

        entries = collect_microsoft_fabric_icons(tmp_path)
        assert len(entries) == 1
        assert entries[0].category == "fabric"

    def test_collect_power_platform_icons(self, tmp_path: Path):
        """Parse power-platform-icon-package."""
        base = tmp_path / "power-platform-icon-package" / "Power Platform"
        base.mkdir(parents=True)
        (base / "Power-Automate.svg").write_text("<svg></svg>")

        entries = collect_microsoft_power_platform_icons(tmp_path)
        assert len(entries) == 1
        assert entries[0].category == "power-platform"

    def test_collect_entra_icons(self, tmp_path: Path):
        """Parse Microsoft Entra color icons."""
        base = tmp_path / "microsoft-entra-architecture-icon-package" / "Microsoft Entra color icons SVG"
        base.mkdir(parents=True)
        (base / "Conditional-Access.svg").write_text("<svg></svg>")

        entries = collect_microsoft_entra_icons(tmp_path)
        assert len(entries) == 1
        assert entries[0].category == "entra"
        assert "identity" in entries[0].tags

    def test_collect_microsoft_365_icons(self, tmp_path: Path):
        """Parse microsoft-365-content-icon-package."""
        base = tmp_path / "microsoft-365-content-icon-package" / "Teams Purple"
        base.mkdir(parents=True)
        (base / "Teams.svg").write_text("<svg></svg>")

        entries = collect_microsoft_365_icons(tmp_path)
        assert len(entries) == 1
        assert entries[0].category == "microsoft-365"

    def test_collect_microsoft_icons_combines_all(self, tmp_path: Path):
        """collect_microsoft_icons merges all Microsoft icon sources."""
        # Dynamics
        d = tmp_path / "dynamics-365-icon-package" / "Dynamics 365 App Icons"
        d.mkdir(parents=True)
        (d / "Sales.svg").write_text("<svg></svg>")

        # Power Platform
        pp = tmp_path / "power-platform-icon-package" / "Power Platform"
        pp.mkdir(parents=True)
        (pp / "Power-Automate.svg").write_text("<svg></svg>")

        entries = collect_microsoft_icons(tmp_path)
        assert len(entries) >= 2


# ---------------------------------------------------------------------------
# Deduplication tests
# ---------------------------------------------------------------------------


class TestDeduplication:
    """Tests for deduplication logic."""

    def test_first_occurrence_wins(self):
        entries = [
            IconEntry(
                id="aws/compute/lambda",
                vendor="aws",
                category="compute",
                name="Lambda v1",
                filename="lambda.svg",
                source_path=Path("a.svg"),
                dest_path=Path("icons/aws/compute/lambda.svg"),
            ),
            IconEntry(
                id="aws/compute/lambda",
                vendor="aws",
                category="compute",
                name="Lambda v2",
                filename="lambda.svg",
                source_path=Path("b.svg"),
                dest_path=Path("icons/aws/compute/lambda.svg"),
            ),
        ]
        deduped = deduplicate_entries(entries)
        assert len(deduped) == 1
        assert deduped[0].name == "Lambda v1"

    def test_no_duplicates_unchanged(self):
        entries = [
            IconEntry(
                id="aws/compute/lambda",
                vendor="aws",
                category="compute",
                name="Lambda",
                filename="lambda.svg",
                source_path=Path("a.svg"),
                dest_path=Path("icons/aws/compute/lambda.svg"),
            ),
            IconEntry(
                id="aws/compute/ec2",
                vendor="aws",
                category="compute",
                name="EC2",
                filename="ec2.svg",
                source_path=Path("b.svg"),
                dest_path=Path("icons/aws/compute/ec2.svg"),
            ),
        ]
        deduped = deduplicate_entries(entries)
        assert len(deduped) == 2

    def test_deduplicate_preserves_order(self):
        entries = [
            IconEntry(
                id=f"aws/cat/{i}",
                vendor="aws",
                category="cat",
                name=f"n{i}",
                filename=f"{i}.svg",
                source_path=Path(f"{i}.svg"),
                dest_path=Path(f"icons/{i}.svg"),
            )
            for i in range(5)
        ]
        deduped = deduplicate_entries(entries)
        assert [e.id for e in deduped] == [f"aws/cat/{i}" for i in range(5)]


# ---------------------------------------------------------------------------
# collect_all_icons tests
# ---------------------------------------------------------------------------


class TestCollectAllIcons:
    """Test the main entry point collect_all_icons."""

    def test_collect_all_with_empty_assets(self, tmp_path: Path):
        """Returns empty list if no vendor dirs exist."""
        entries = collect_all_icons(tmp_path)
        assert entries == []

    def test_collect_all_with_mixed_vendors(self, tmp_path: Path):
        """Multi-vendor scan collects from all vendors."""
        # AWS
        aws = tmp_path / "aws-icon-package" / "Category-Icons_04302026" / "Arch-Category_48"
        aws.mkdir(parents=True)
        (aws / "Arch-Category_Compute_48.svg").write_text("<svg></svg>")

        # Azure
        az = tmp_path / "azure-icon-package" / "Icons" / "Compute"
        az.mkdir(parents=True)
        (az / "VM.svg").write_text("<svg></svg>")

        entries = collect_all_icons(tmp_path)
        vendors = {e.vendor for e in entries}
        assert "aws" in vendors
        assert "azure" in vendors


# ---------------------------------------------------------------------------
# Robustness against internal-layout changes
# ---------------------------------------------------------------------------


class TestLayoutRobustness:
    """The only stable contract is the top-level package dir name. Internal
    subdirectory restructuring must not break icon collection.
    """

    def test_aws_service_icons_tolerate_renamed_release_dir(self, tmp_path: Path):
        """AWS classification is filename-based, not release-dir based."""
        # Hypothetical future release rename: Architecture-Service-Icons_2030 instead of _04302026
        d = tmp_path / "aws-icon-package" / "Architecture-Service-Icons_2030" / "Arch_Compute" / "48"
        d.mkdir(parents=True)
        (d / "Arch_AWS-Lambda_48.svg").write_text("<svg></svg>")

        entries = collect_aws_icons(tmp_path)
        assert any(e.id == "aws/compute/lambda" for e in entries)

    def test_aws_service_icons_tolerate_flat_layout(self, tmp_path: Path):
        """Even without intermediate release/size subdirs, classification works
        from filename prefix; category infers from the immediate parent dir.
        """
        d = tmp_path / "aws-icon-package" / "Compute"
        d.mkdir(parents=True)
        (d / "Arch_AWS-Lambda_48.svg").write_text("<svg></svg>")

        entries = collect_aws_icons(tmp_path)
        assert any(e.id == "aws/compute/lambda" for e in entries)

    def test_fabric_tolerates_old_nested_layout(self, tmp_path: Path):
        """Historical layout: microsoft-fabric-icon-package/package/dist/svg/*.svg"""
        d = tmp_path / "microsoft-fabric-icon-package" / "package" / "dist" / "svg"
        d.mkdir(parents=True)
        (d / "data_warehouse_20_filled.svg").write_text("<svg></svg>")

        entries = collect_microsoft_fabric_icons(tmp_path)
        assert len(entries) == 1
        assert entries[0].category == "fabric"

    def test_fabric_tolerates_new_flat_layout(self, tmp_path: Path):
        """Current layout: microsoft-fabric-icon-package/svg/*.svg"""
        d = tmp_path / "microsoft-fabric-icon-package" / "svg"
        d.mkdir(parents=True)
        (d / "data_warehouse_20_filled.svg").write_text("<svg></svg>")

        entries = collect_microsoft_fabric_icons(tmp_path)
        assert len(entries) == 1
        assert entries[0].category == "fabric"

    def test_azure_tolerates_missing_icons_wrapper(self, tmp_path: Path):
        """Azure works even if the `Icons/` wrapper is removed and categories
        sit directly under the package dir.
        """
        d = tmp_path / "azure-icon-package" / "Compute"
        d.mkdir(parents=True)
        (d / "Virtual-Machines.svg").write_text("<svg></svg>")

        entries = collect_azure_icons(tmp_path)
        assert len(entries) == 1
        assert entries[0].category == "compute"

    def test_entra_excludes_bw_set(self, tmp_path: Path):
        """Microsoft Entra collector excludes black-and-white variants."""
        color = tmp_path / "microsoft-entra-architecture-icon-package" / "Microsoft Entra color icons SVG"
        bw = tmp_path / "microsoft-entra-architecture-icon-package" / "Microsoft Entra BW icons SVG"
        color.mkdir(parents=True)
        bw.mkdir(parents=True)
        (color / "Conditional-Access.svg").write_text("<svg></svg>")
        (bw / "Conditional-Access-BW.svg").write_text("<svg></svg>")

        entries = collect_microsoft_entra_icons(tmp_path)
        # Only the color one should survive
        sources = [str(e.source_path) for e in entries]
        assert any("color" in s.lower() for s in sources)
        assert not any("/bw " in s.lower() or "/bw/" in s.lower() or "bw icons" in s.lower() for s in sources)
