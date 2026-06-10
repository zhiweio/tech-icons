"""Tests for ConceptRegistry."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from tech_icons.concepts import ConceptRegistry


@pytest.fixture
def concepts_path(tmp_path: Path, sample_enrichments: dict) -> Path:
    path = tmp_path / "enrichments.yaml"
    path.write_text(yaml.safe_dump(sample_enrichments))
    return path


def test_loads_concept_groups(concepts_path: Path) -> None:
    reg = ConceptRegistry(enrichments_path=concepts_path)
    reg.load()
    names = reg.list_concepts()
    assert "serverless" in names
    assert "kubernetes" in names
    assert "virtual-machine" in names


def test_get_concept_returns_full_group(concepts_path: Path) -> None:
    reg = ConceptRegistry(enrichments_path=concepts_path)
    group = reg.get_concept("kubernetes")
    assert group is not None
    assert group.name == "kubernetes"
    assert len(group.icon_ids) == 3
    assert set(group.vendors) == {"aws", "azure", "gcp"}


def test_get_concept_unknown_returns_none(concepts_path: Path) -> None:
    reg = ConceptRegistry(enrichments_path=concepts_path)
    assert reg.get_concept("nonexistent") is None


def test_get_concepts_for_icon_reverse_lookup(concepts_path: Path) -> None:
    reg = ConceptRegistry(enrichments_path=concepts_path)
    concepts = reg.get_concepts_for_icon("aws/compute/lambda")
    assert "serverless" in concepts
    assert "faas" in concepts


def test_get_concepts_for_unrelated_icon(concepts_path: Path) -> None:
    reg = ConceptRegistry(enrichments_path=concepts_path)
    concepts = reg.get_concepts_for_icon("aws/databases/dynamodb")
    assert concepts == []


def test_missing_file_does_not_raise(tmp_path: Path) -> None:
    reg = ConceptRegistry(enrichments_path=tmp_path / "missing.yaml")
    reg.load()
    assert reg.list_concepts() == []


def test_empty_aliases_section(tmp_path: Path) -> None:
    path = tmp_path / "empty.yaml"
    path.write_text("aliases: {}\n")
    reg = ConceptRegistry(enrichments_path=path)
    reg.load()
    assert reg.list_concepts() == []


def test_search_engine_compare_icons(search_engine) -> None:
    """SearchEngine.compare_icons returns vendor-grouped icons."""
    result = search_engine.compare_icons("serverless")
    assert result is not None
    assert result["name"] == "serverless"
    assert "aws" in result["icons"]
    assert "azure" in result["icons"]
    assert "gcp" in result["icons"]
    # The aws bucket should contain the lambda entry from sample_catalog
    aws_icons = result["icons"]["aws"]
    assert any(e["id"] == "aws/compute/lambda" for e in aws_icons)


def test_search_engine_compare_icons_unknown(search_engine) -> None:
    assert search_engine.compare_icons("nonexistent") is None


def test_search_engine_compare_icons_records_missing(search_engine) -> None:
    """Concept references to icons not in the catalog show up in 'missing'."""
    result = search_engine.compare_icons("kubernetes")
    assert result is not None
    # sample_catalog has no kubernetes entries, so all 3 are missing
    assert len(result["missing"]) == 3
    assert result["icons"] == {}


def test_search_results_annotated_with_concepts(search_engine) -> None:
    """search() results should carry related_concepts."""
    results = search_engine.search("lambda")
    lambda_result = next(r for r in results if r.id == "aws/compute/lambda")
    assert "serverless" in lambda_result.related_concepts
    assert "faas" in lambda_result.related_concepts
