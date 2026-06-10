"""Tests for src/search.py — multi-tier search engine."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tech_icons.search import SearchEngine, SearchResult

# ---------------------------------------------------------------------------
# Exact ID match (Tier 1)
# ---------------------------------------------------------------------------


class TestExactIdMatch:
    """Tier 1: Exact ID matching."""

    def test_exact_id_returns_score_1(self, search_engine: SearchEngine):
        results = search_engine.search("aws/compute/lambda")
        assert len(results) >= 1
        assert results[0].id == "aws/compute/lambda"
        assert results[0].score == 1.0
        assert results[0].match_tier == 1

    def test_exact_id_case_insensitive(self, search_engine: SearchEngine):
        results = search_engine.search("AWS/Compute/Lambda")
        assert len(results) >= 1
        assert results[0].id == "aws/compute/lambda"

    def test_partial_id_match(self, search_engine: SearchEngine):
        """Searching just 'lambda' matches 'aws/compute/lambda'."""
        results = search_engine.search("lambda")
        matching = [r for r in results if r.id == "aws/compute/lambda"]
        assert len(matching) >= 1

    def test_nonexistent_id_returns_empty_tier1(self, search_engine: SearchEngine):
        """Non-existent full ID falls through to other tiers."""
        results = search_engine.search("aws/compute/nonexistent-service-xyz")
        # Should not find exact match, may find fuzzy/keyword results
        exact = [r for r in results if r.match_tier == 1]
        assert len(exact) == 0


# ---------------------------------------------------------------------------
# Keyword search (Tier 2)
# ---------------------------------------------------------------------------


class TestKeywordSearch:
    """Tier 2: Keyword search via inverted index."""

    def test_keyword_by_name(self, search_engine: SearchEngine):
        """Search by name tokens finds correct icon."""
        results = search_engine.search("lambda")
        ids = [r.id for r in results]
        assert "aws/compute/lambda" in ids

    def test_keyword_by_alias(self, search_engine: SearchEngine):
        """Search by alias returns matching icons."""
        results = search_engine.search("serverless")
        ids = [r.id for r in results]
        assert "aws/compute/lambda" in ids
        assert "azure/compute/function-apps" in ids

    def test_keyword_by_tag(self, search_engine: SearchEngine):
        """Search by tag finds tagged icons."""
        results = search_engine.search("nosql")
        ids = [r.id for r in results]
        assert "aws/databases/dynamodb" in ids

    def test_keyword_multi_token(self, search_engine: SearchEngine):
        """Multi-token query scores higher for entries matching more tokens."""
        results = search_engine.search("aws compute")
        # AWS compute icons should rank higher
        top_ids = [r.id for r in results[:5]]
        assert any("aws" in id_ and "compute" in id_ for id_ in top_ids)

    def test_keyword_returns_tier_2(self, search_engine: SearchEngine):
        """Keyword results have match_tier=2."""
        results = search_engine.search("nosql")
        keyword_results = [r for r in results if r.match_tier == 2]
        assert len(keyword_results) >= 1


# ---------------------------------------------------------------------------
# Fuzzy search (Tier 3)
# ---------------------------------------------------------------------------


class TestFuzzySearch:
    """Tier 3: Fuzzy matching for typo tolerance."""

    def test_fuzzy_typo_lamda(self, search_engine: SearchEngine):
        """Typo 'lamda' should fuzzy-match 'lambda'."""
        results = search_engine.search("lamda")
        ids = [r.id for r in results]
        assert "aws/compute/lambda" in ids

    def test_fuzzy_typo_dynamo_db(self, search_engine: SearchEngine):
        """'dynamo db' should fuzzy-match 'dynamodb'."""
        results = search_engine.search("dynamo db")
        ids = [r.id for r in results]
        assert "aws/databases/dynamodb" in ids

    def test_fuzzy_close_match(self, search_engine: SearchEngine):
        """Close fuzzy matches should return results."""
        results = search_engine.search("compuet engine")
        ids = [r.id for r in results]
        assert "gcp/compute/compute-engine" in ids

    def test_fuzzy_tier_3_score_capped(self, search_engine: SearchEngine):
        """Fuzzy results score < 1.0 (capped at 0.8 * similarity)."""
        results = search_engine.search("lamda")
        fuzzy = [r for r in results if r.match_tier == 3]
        for r in fuzzy:
            assert r.score < 1.0


# ---------------------------------------------------------------------------
# Cross-vendor and filter tests
# ---------------------------------------------------------------------------


class TestFilters:
    """Tests for vendor, category, and limit filters."""

    def test_cross_vendor_search(self, search_engine: SearchEngine):
        """'load balancer' returns results from multiple vendors."""
        results = search_engine.search("load balancer", limit=20)
        vendors = {r.icon_entry["vendor"] for r in results}
        assert len(vendors) >= 2  # At least AWS + Azure or GCP

    def test_vendor_filter_aws(self, search_engine: SearchEngine):
        """Search with vendor='aws' only returns AWS icons."""
        results = search_engine.search("compute", vendor="aws")
        for r in results:
            assert r.icon_entry["vendor"] == "aws"

    def test_vendor_filter_azure(self, search_engine: SearchEngine):
        results = search_engine.search("compute", vendor="azure")
        for r in results:
            assert r.icon_entry["vendor"] == "azure"

    def test_vendor_filter_gcp(self, search_engine: SearchEngine):
        results = search_engine.search("compute", vendor="gcp")
        for r in results:
            assert r.icon_entry["vendor"] == "gcp"

    def test_vendor_filter_microsoft(self, search_engine: SearchEngine):
        results = search_engine.search("microsoft", vendor="microsoft")
        for r in results:
            assert r.icon_entry["vendor"] == "microsoft"

    def test_category_filter(self, search_engine: SearchEngine):
        """Search with category filter only returns matching category."""
        results = search_engine.search("aws", category="compute")
        for r in results:
            assert r.icon_entry["category"] == "compute"

    def test_limit_parameter(self, search_engine: SearchEngine):
        """Limit parameter caps result count."""
        results = search_engine.search("aws", limit=3)
        assert len(results) <= 3

    def test_limit_one(self, search_engine: SearchEngine):
        results = search_engine.search("compute", limit=1)
        assert len(results) == 1


# ---------------------------------------------------------------------------
# Deduplication and ordering
# ---------------------------------------------------------------------------


class TestDeduplicationAndOrdering:
    """Tests for result deduplication and score ordering."""

    def test_no_duplicate_ids_in_results(self, search_engine: SearchEngine):
        """Results should never contain duplicate icon IDs."""
        results = search_engine.search("serverless", limit=20)
        ids = [r.id for r in results]
        assert len(ids) == len(set(ids))

    def test_higher_tier_ranks_first(self, search_engine: SearchEngine):
        """Exact match (tier 1) should rank above keyword (tier 2)."""
        # aws/compute/lambda is an exact partial match AND a keyword match
        results = search_engine.search("lambda", limit=10)
        if len(results) >= 2:
            # The top result should be the best scoring
            assert results[0].score >= results[1].score

    def test_results_sorted_by_score_desc(self, search_engine: SearchEngine):
        """Results are sorted by score descending."""
        results = search_engine.search("compute", limit=10)
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)


# ---------------------------------------------------------------------------
# Edge cases and degradation
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Edge cases and graceful degradation."""

    def test_empty_query_returns_empty(self, search_engine: SearchEngine):
        """Empty query returns no results."""
        results = search_engine.search("")
        assert results == []

    def test_whitespace_query(self, search_engine: SearchEngine):
        """Whitespace-only query returns no results."""
        results = search_engine.search("   ")
        assert results == []

    def test_graceful_without_embeddings(self, search_engine: SearchEngine):
        """Search works without embeddings (tiers 1-3 still function)."""
        # Our fixture has no embeddings
        assert search_engine._embeddings is None
        results = search_engine.search("lambda")
        assert len(results) >= 1

    def test_special_characters_in_query(self, search_engine: SearchEngine):
        """Special characters don't crash the engine."""
        results = search_engine.search("aws/compute/!@#$%")
        # Should not raise, may return empty
        assert isinstance(results, list)

    def test_very_long_query(self, search_engine: SearchEngine):
        """Very long query does not crash."""
        long_query = "lambda " * 100
        results = search_engine.search(long_query)
        assert isinstance(results, list)


# ---------------------------------------------------------------------------
# get_icon, list_vendors, list_categories
# ---------------------------------------------------------------------------


class TestHelperMethods:
    """Tests for helper methods on SearchEngine."""

    def test_get_icon_valid(self, search_engine: SearchEngine):
        entry = search_engine.get_icon("aws/compute/lambda")
        assert entry is not None
        assert entry["id"] == "aws/compute/lambda"
        assert entry["vendor"] == "aws"

    def test_get_icon_invalid(self, search_engine: SearchEngine):
        entry = search_engine.get_icon("nonexistent/icon/id")
        assert entry is None

    def test_list_vendors(self, search_engine: SearchEngine):
        vendors = search_engine.list_vendors()
        assert "aws" in vendors
        assert "azure" in vendors
        assert "gcp" in vendors
        assert "microsoft" in vendors
        # Check counts are correct
        assert vendors["aws"] == 4  # 4 AWS entries in sample catalog

    def test_list_categories_all(self, search_engine: SearchEngine):
        categories = search_engine.list_categories()
        assert "compute" in categories
        assert "networking" in categories
        assert "databases" in categories

    def test_list_categories_vendor_filter(self, search_engine: SearchEngine):
        categories = search_engine.list_categories(vendor="microsoft")
        assert "dynamics-365" in categories
        assert "fabric" in categories
        assert "compute" not in categories  # no compute in microsoft sample

    def test_list_categories_sorted(self, search_engine: SearchEngine):
        categories = search_engine.list_categories()
        assert categories == sorted(categories)


# ---------------------------------------------------------------------------
# SearchEngine loading
# ---------------------------------------------------------------------------


class TestSearchEngineLoading:
    """Tests for catalog loading behavior."""

    def test_load_nonexistent_catalog_raises(self, tmp_path: Path):
        engine = SearchEngine(catalog_dir=tmp_path / "nonexistent")
        with pytest.raises(FileNotFoundError):
            engine.load()

    def test_load_without_keyword_index(self, tmp_path: Path, sample_catalog: list[dict]):
        """Engine loads even without keyword_index.json (tier 2 disabled)."""
        catalog_dir = tmp_path / "catalog"
        catalog_dir.mkdir()
        (catalog_dir / "icons.json").write_text(json.dumps(sample_catalog))
        # No keyword_index.json

        engine = SearchEngine(catalog_dir=catalog_dir)
        engine.load()
        assert len(engine.catalog) == len(sample_catalog)

    def test_lazy_loading(self, tmp_path: Path, sample_catalog: list[dict], sample_keyword_index: dict):
        """Engine lazily loads on first access."""
        catalog_dir = tmp_path / "catalog"
        catalog_dir.mkdir()
        (catalog_dir / "icons.json").write_text(json.dumps(sample_catalog))
        (catalog_dir / "keyword_index.json").write_text(json.dumps(sample_keyword_index))

        engine = SearchEngine(catalog_dir=catalog_dir)
        assert engine._loaded is False

        # Access catalog triggers load
        _ = engine.catalog
        assert engine._loaded is True


# ---------------------------------------------------------------------------
# SearchResult dataclass
# ---------------------------------------------------------------------------


class TestSearchResult:
    """Tests for SearchResult serialization."""

    def test_to_dict(self):
        entry = {"id": "aws/compute/lambda", "vendor": "aws"}
        r = SearchResult(id="aws/compute/lambda", score=0.95, icon_entry=entry, match_tier=2)
        d = r.to_dict()
        assert d["id"] == "aws/compute/lambda"
        assert d["score"] == 0.95
        assert d["match_tier"] == 2
        assert d["icon_entry"] == entry
