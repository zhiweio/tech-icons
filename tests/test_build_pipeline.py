"""Tests for scripts/build_catalog.py — build pipeline."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.build_catalog import (
    build_keyword_index,
    build_reverse_enrichment_map,
    compute_assets_hash,
    entry_to_catalog_record,
    load_enrichments,
    needs_rebuild,
)
from tech_icons.normalize import IconEntry

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def assets_dir(tmp_path: Path) -> Path:
    """Create a minimal asset directory for pipeline tests."""
    aws_dir = tmp_path / "aws-icon-package" / "Category-Icons_04302026" / "Arch-Category_48"
    aws_dir.mkdir(parents=True)
    (aws_dir / "Arch-Category_Compute_48.svg").write_text("<svg>compute</svg>")
    (aws_dir / "Arch-Category_Storage_48.svg").write_text("<svg>storage</svg>")

    azure_dir = tmp_path / "azure-icon-package" / "Icons" / "Compute"
    azure_dir.mkdir(parents=True)
    (azure_dir / "VM.svg").write_text("<svg>vm</svg>")

    return tmp_path


@pytest.fixture
def catalog_dir(tmp_path: Path) -> Path:
    """Create a catalog output directory."""
    d = tmp_path / "catalog"
    d.mkdir()
    return d


@pytest.fixture
def sample_entries() -> list[IconEntry]:
    """Sample IconEntry list for catalog generation."""
    return [
        IconEntry(
            id="aws/compute/lambda",
            vendor="aws",
            category="compute",
            name="AWS Lambda",
            filename="lambda.svg",
            source_path=Path("assets/aws/lambda.svg"),
            dest_path=Path("icons/aws/compute/lambda.svg"),
            aliases=["serverless"],
            tags=["aws", "compute"],
            description="AWS Lambda serverless function",
        ),
        IconEntry(
            id="azure/compute/function-apps",
            vendor="azure",
            category="compute",
            name="Azure Function Apps",
            filename="function-apps.svg",
            source_path=Path("assets/azure/function-apps.svg"),
            dest_path=Path("icons/azure/compute/function-apps.svg"),
            aliases=["faas"],
            tags=["azure", "compute", "serverless"],
            description="Azure Functions serverless compute",
        ),
        IconEntry(
            id="gcp/databases/cloud-sql",
            vendor="gcp",
            category="databases",
            name="GCP Cloud SQL",
            filename="cloud-sql.svg",
            source_path=Path("assets/gcp/cloud-sql.svg"),
            dest_path=Path("icons/gcp/databases/cloud-sql.svg"),
            aliases=["sql-database"],
            tags=["gcp", "databases"],
            description="GCP Cloud SQL managed database",
        ),
    ]


# ---------------------------------------------------------------------------
# Hash-based change detection
# ---------------------------------------------------------------------------


class TestChangeDetection:
    """Test hash-based change detection."""

    def test_compute_assets_hash_deterministic(self, assets_dir: Path):
        """Same directory produces same hash."""
        h1 = compute_assets_hash(assets_dir)
        h2 = compute_assets_hash(assets_dir)
        assert h1 == h2

    def test_compute_assets_hash_changes_on_new_file(self, assets_dir: Path):
        """Adding a file changes the hash."""
        h1 = compute_assets_hash(assets_dir)
        new_dir = assets_dir / "azure-icon-package" / "Icons" / "Networking"
        new_dir.mkdir(parents=True)
        (new_dir / "LoadBalancer.svg").write_text("<svg>lb</svg>")
        h2 = compute_assets_hash(assets_dir)
        assert h1 != h2

    def test_needs_rebuild_true_when_no_hash_file(self, assets_dir: Path, catalog_dir: Path):
        """First build always needs rebuild."""
        with patch("scripts.build_catalog.HASH_FILE", catalog_dir / ".build_hash"):
            assert needs_rebuild(assets_dir, force=False) is True

    def test_needs_rebuild_false_when_hash_matches(self, assets_dir: Path, catalog_dir: Path):
        """No rebuild needed if hash matches."""
        hash_file = catalog_dir / ".build_hash"
        current_hash = compute_assets_hash(assets_dir)
        hash_file.write_text(current_hash)

        with patch("scripts.build_catalog.HASH_FILE", hash_file):
            assert needs_rebuild(assets_dir, force=False) is False

    def test_needs_rebuild_true_when_forced(self, assets_dir: Path, catalog_dir: Path):
        """--force always triggers rebuild."""
        hash_file = catalog_dir / ".build_hash"
        current_hash = compute_assets_hash(assets_dir)
        hash_file.write_text(current_hash)

        with patch("scripts.build_catalog.HASH_FILE", hash_file):
            assert needs_rebuild(assets_dir, force=True) is True

    def test_needs_rebuild_true_on_changed_assets(self, assets_dir: Path, catalog_dir: Path):
        """Rebuild needed when assets change."""
        hash_file = catalog_dir / ".build_hash"
        hash_file.write_text("old_hash_value")

        with patch("scripts.build_catalog.HASH_FILE", hash_file):
            assert needs_rebuild(assets_dir, force=False) is True


# ---------------------------------------------------------------------------
# Catalog generation
# ---------------------------------------------------------------------------


class TestCatalogGeneration:
    """Test catalog record generation."""

    def test_entry_to_catalog_record_basic(self, sample_entries: list[IconEntry]):
        enrichment_map: dict = {}
        record = entry_to_catalog_record(sample_entries[0], enrichment_map)

        assert record["id"] == "aws/compute/lambda"
        assert record["vendor"] == "aws"
        assert record["category"] == "compute"
        assert record["name"] == "AWS Lambda"
        assert record["filename"] == "lambda.svg"
        assert record["formats"] == {"svg": "icons/aws/compute/lambda.svg"}
        assert "serverless" in record["aliases"]
        assert "aws" in record["tags"]

    def test_entry_to_catalog_record_merges_enrichments(self, sample_entries: list[IconEntry]):
        enrichment_map = {
            "aws/compute/lambda": {
                "aliases": ["function-as-a-service", "faas"],
                "tags": ["serverless-compute"],
            }
        }
        record = entry_to_catalog_record(sample_entries[0], enrichment_map)

        assert "function-as-a-service" in record["aliases"]
        assert "faas" in record["aliases"]
        assert "serverless-compute" in record["tags"]

    def test_entry_to_catalog_record_adds_name_tokens(self, sample_entries: list[IconEntry]):
        """Name tokens from ID are added as aliases."""
        enrichment_map: dict = {}
        record = entry_to_catalog_record(sample_entries[0], enrichment_map)
        # "lambda" is the last segment of "aws/compute/lambda"
        assert "lambda" in record["aliases"]

    def test_entry_to_catalog_record_default_description(self):
        """When no description, generates default."""
        entry = IconEntry(
            id="aws/compute/test",
            vendor="aws",
            category="compute",
            name="AWS Test",
            filename="test.svg",
            source_path=Path("a.svg"),
            dest_path=Path("icons/aws/compute/test.svg"),
        )
        record = entry_to_catalog_record(entry, {})
        assert "AWS Test" in record["description"]
        assert "aws" in record["description"]

    def test_catalog_valid_json_structure(self, sample_entries: list[IconEntry]):
        enrichment_map: dict = {}
        catalog = [entry_to_catalog_record(e, enrichment_map) for e in sample_entries]

        # Should be serializable
        json_str = json.dumps(catalog, indent=2)
        parsed = json.loads(json_str)
        assert len(parsed) == 3

        # All required fields present
        required_fields = [
            "id",
            "vendor",
            "category",
            "name",
            "filename",
            "formats",
            "aliases",
            "tags",
            "description",
        ]
        for record in parsed:
            assert all(k in record for k in required_fields)


# ---------------------------------------------------------------------------
# Keyword index generation
# ---------------------------------------------------------------------------


class TestKeywordIndexGeneration:
    """Test keyword index building."""

    def test_build_keyword_index_basic(self, sample_catalog: list[dict]):
        index = build_keyword_index(sample_catalog)

        # "lambda" should map to the lambda icon
        assert "lambda" in index
        assert "aws/compute/lambda" in index["lambda"]

    def test_keyword_index_includes_aliases(self, sample_catalog: list[dict]):
        index = build_keyword_index(sample_catalog)

        assert "serverless" in index
        assert "aws/compute/lambda" in index["serverless"]

    def test_keyword_index_includes_tags(self, sample_catalog: list[dict]):
        index = build_keyword_index(sample_catalog)

        assert "nosql" in index
        assert "aws/databases/dynamodb" in index["nosql"]

    def test_keyword_index_includes_vendor(self, sample_catalog: list[dict]):
        index = build_keyword_index(sample_catalog)

        assert "aws" in index
        # All AWS icons should be under "aws" keyword
        aws_ids = [r["id"] for r in sample_catalog if r["vendor"] == "aws"]
        for aws_id in aws_ids:
            assert aws_id in index["aws"]

    def test_keyword_index_includes_category(self, sample_catalog: list[dict]):
        index = build_keyword_index(sample_catalog)

        assert "compute" in index

    def test_keyword_index_skips_short_tokens(self, sample_catalog: list[dict]):
        index = build_keyword_index(sample_catalog)

        # Single-char tokens should be excluded
        for key in index:
            assert len(key) >= 2

    def test_keyword_index_sorted_keys(self, sample_catalog: list[dict]):
        index = build_keyword_index(sample_catalog)
        keys = list(index.keys())
        assert keys == sorted(keys)

    def test_keyword_index_no_duplicates_per_token(self, sample_catalog: list[dict]):
        """Each icon ID appears at most once per token."""
        index = build_keyword_index(sample_catalog)
        for token, ids in index.items():
            assert len(ids) == len(set(ids)), f"Duplicate IDs for token '{token}'"


# ---------------------------------------------------------------------------
# Enrichment map
# ---------------------------------------------------------------------------


class TestEnrichmentMap:
    """Test enrichment map building."""

    def test_build_reverse_enrichment_map(self, sample_enrichments: dict):
        reverse = build_reverse_enrichment_map(sample_enrichments)

        # "serverless" alias should be on lambda
        assert "aws/compute/lambda" in reverse
        assert "serverless" in reverse["aws/compute/lambda"]["aliases"]

    def test_enrichment_map_tags(self, sample_enrichments: dict):
        reverse = build_reverse_enrichment_map(sample_enrichments)

        assert "aws/compute/lambda" in reverse
        assert "compute" in reverse["aws/compute/lambda"]["tags"]

    def test_enrichment_map_no_duplicates(self, sample_enrichments: dict):
        reverse = build_reverse_enrichment_map(sample_enrichments)

        for _icon_id, data in reverse.items():
            assert len(data["aliases"]) == len(set(data["aliases"]))
            assert len(data["tags"]) == len(set(data["tags"]))

    def test_enrichment_map_handles_empty(self):
        enrichments = {"aliases": {}, "tags": {}}
        reverse = build_reverse_enrichment_map(enrichments)
        assert reverse == {}


# ---------------------------------------------------------------------------
# Incremental build
# ---------------------------------------------------------------------------


class TestIncrementalBuild:
    """Test incremental build behavior."""

    def test_new_icon_added_to_catalog(self, assets_dir: Path, catalog_dir: Path):
        """Adding a new SVG file to assets triggers inclusion in catalog."""
        from tech_icons.normalize import collect_all_icons

        entries_before = collect_all_icons(assets_dir)
        count_before = len(entries_before)

        # Add a new icon
        new_dir = assets_dir / "azure-icon-package" / "Icons" / "Networking"
        new_dir.mkdir(parents=True)
        (new_dir / "LoadBalancer.svg").write_text("<svg>lb</svg>")

        entries_after = collect_all_icons(assets_dir)
        assert len(entries_after) == count_before + 1


# ---------------------------------------------------------------------------
# Vendor filter
# ---------------------------------------------------------------------------


class TestVendorFilter:
    """Test --vendor filter builds only specified vendor."""

    def test_aws_only(self, assets_dir: Path):
        from tech_icons.normalize import collect_aws_icons

        entries = collect_aws_icons(assets_dir)
        assert all(e.vendor == "aws" for e in entries)
        assert len(entries) >= 1

    def test_azure_only(self, assets_dir: Path):
        from tech_icons.normalize import collect_azure_icons

        entries = collect_azure_icons(assets_dir)
        assert all(e.vendor == "azure" for e in entries)
        assert len(entries) >= 1


# ---------------------------------------------------------------------------
# Skip embeddings
# ---------------------------------------------------------------------------


class TestSkipEmbeddings:
    """Test --skip-embeddings flag behavior."""

    def test_compute_embeddings_import_error(self, tmp_path):
        """compute_embeddings handles missing sentence-transformers gracefully."""
        from scripts.build_catalog import compute_embeddings

        # When sentence-transformers is not available, it should not crash
        with patch.dict("sys.modules", {"sentence_transformers": None, "numpy": None}):
            with patch("builtins.__import__", side_effect=ImportError("no module")):
                # Should log error and return, not crash
                compute_embeddings([], tmp_path / "test")


# ---------------------------------------------------------------------------
# Load enrichments
# ---------------------------------------------------------------------------


class TestLoadEnrichments:
    """Test enrichments loading."""

    def test_load_enrichments_file_not_found(self, tmp_path: Path):
        """Missing enrichments.yaml returns empty dict."""
        with patch("scripts.build_catalog.CATALOG_DIR", tmp_path):
            result = load_enrichments()
            assert result == {"aliases": {}, "tags": {}}

    def test_load_enrichments_valid_file(self, tmp_path: Path):
        """Valid enrichments.yaml is loaded correctly."""
        enrichments_path = tmp_path / "enrichments.yaml"
        enrichments_path.write_text(
            "aliases:\n  serverless:\n    - aws/compute/lambda\ntags:\n  compute:\n    - aws/compute/ec2\n"
        )
        with patch("scripts.build_catalog.CATALOG_DIR", tmp_path):
            result = load_enrichments()
            assert "serverless" in result["aliases"]
            assert "compute" in result["tags"]
