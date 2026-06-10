"""Multi-tier search engine for tech icons catalog.

Supports four tiers of search (tried in order):
  1. Exact ID match
  2. Keyword search via inverted index
  3. Fuzzy match via rapidfuzz
  4. Semantic search via sentence-transformers embeddings

Results are merged, deduplicated, and scored.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

from tech_icons._paths import catalog_dir as _default_catalog_dir
from tech_icons.concepts import ConceptRegistry

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """A single search result with scoring metadata."""

    id: str
    score: float
    icon_entry: dict
    match_tier: int
    related_concepts: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "score": self.score,
            "icon_entry": self.icon_entry,
            "match_tier": self.match_tier,
            "related_concepts": self.related_concepts,
        }


class SearchEngine:
    """Multi-tier search engine over the icon catalog."""

    def __init__(
        self,
        catalog_dir: Path | None = None,
        concept_registry: ConceptRegistry | None = None,
    ):
        self._catalog_dir = catalog_dir if catalog_dir is not None else _default_catalog_dir()
        self._catalog: list[dict] = []
        self._keyword_index: dict[str, list[str]] = {}
        self._id_map: dict[str, dict] = {}
        self._embeddings = None
        self._embedding_ids: list[str] = []
        self._embed_model = None
        self._loaded = False
        self._concepts = concept_registry or ConceptRegistry(enrichments_path=self._catalog_dir / "enrichments.yaml")

    def load(self) -> None:
        """Load catalog and keyword index from disk."""
        catalog_path = self._catalog_dir / "icons.json"
        index_path = self._catalog_dir / "keyword_index.json"

        if not catalog_path.exists():
            raise FileNotFoundError(f"Catalog not found: {catalog_path}")

        with open(catalog_path) as f:
            self._catalog = json.load(f)

        self._id_map = {entry["id"]: entry for entry in self._catalog}

        if index_path.exists():
            with open(index_path) as f:
                self._keyword_index = json.load(f)
        else:
            logger.warning("Keyword index not found, tier 2 search disabled")

        self._load_embeddings()
        self._concepts.load()
        self._loaded = True
        logger.info(
            f"Search engine loaded: {len(self._catalog)} icons, "
            f"{len(self._keyword_index)} keywords, "
            f"{len(self._concepts.all_groups)} concept groups"
        )

    def _load_embeddings(self) -> None:
        """Attempt to load precomputed embeddings. Fails silently."""
        embeddings_path = self._catalog_dir / "embeddings.npz"
        ids_path = self._catalog_dir / "embedding_ids.json"

        if not embeddings_path.exists() or not ids_path.exists():
            logger.info("Embeddings not available, semantic search disabled")
            return

        try:
            import numpy as np

            data = np.load(embeddings_path)
            self._embeddings = data["embeddings"]

            with open(ids_path) as f:
                self._embedding_ids = json.load(f)

            logger.info(f"Loaded {len(self._embedding_ids)} embeddings")
        except Exception as e:
            logger.warning(f"Failed to load embeddings: {e}")
            self._embeddings = None

    def _ensure_loaded(self) -> None:
        if not self._loaded:
            self.load()

    @property
    def catalog(self) -> list[dict]:
        self._ensure_loaded()
        return self._catalog

    @property
    def id_map(self) -> dict[str, dict]:
        self._ensure_loaded()
        return self._id_map

    def search(
        self,
        query: str,
        vendor: str | None = None,
        category: str | None = None,
        limit: int = 10,
    ) -> list[SearchResult]:
        """Run multi-tier search and return merged results."""
        self._ensure_loaded()

        results: dict[str, SearchResult] = {}

        # Tier 1: Exact ID match
        tier1 = self._search_exact_id(query)
        for r in tier1:
            results[r.id] = r

        if len(results) >= limit:
            return self._apply_filters(list(results.values()), vendor, category, limit)

        # Tier 2: Keyword search
        tier2 = self._search_keywords(query)
        for r in tier2:
            if r.id not in results:
                results[r.id] = r

        if len(results) >= limit:
            return self._apply_filters(list(results.values()), vendor, category, limit)

        # Tier 3: Fuzzy match
        tier3 = self._search_fuzzy(query)
        for r in tier3:
            if r.id not in results:
                results[r.id] = r

        if len(results) >= limit:
            return self._apply_filters(list(results.values()), vendor, category, limit)

        # Tier 4: Semantic search
        tier4 = self._search_semantic(query)
        for r in tier4:
            if r.id not in results:
                results[r.id] = r

        return self._apply_filters(list(results.values()), vendor, category, limit)

    def _apply_filters(
        self,
        results: list[SearchResult],
        vendor: str | None,
        category: str | None,
        limit: int,
    ) -> list[SearchResult]:
        """Filter by vendor/category, sort by score descending, and limit."""
        if vendor:
            results = [r for r in results if r.icon_entry.get("vendor") == vendor]
        if category:
            results = [r for r in results if r.icon_entry.get("category") == category]

        results.sort(key=lambda r: (-r.match_tier == 1, -r.score))
        # Stable sort: tier 1 first (exact match), then by score
        results.sort(key=lambda r: r.match_tier)
        results.sort(key=lambda r: -r.score)

        # Annotate with concept groups
        for r in results:
            r.related_concepts = self._concepts.get_concepts_for_icon(r.id)

        return results[:limit]

    def _search_exact_id(self, query: str) -> list[SearchResult]:
        """Tier 1: Exact ID match."""
        query_lower = query.lower().strip()

        if query_lower in self._id_map:
            entry = self._id_map[query_lower]
            return [SearchResult(id=entry["id"], score=1.0, icon_entry=entry, match_tier=1)]

        # Also try partial ID match (e.g., "lambda" matches "aws/compute/lambda")
        matches = []
        for icon_id, entry in self._id_map.items():
            if icon_id.endswith("/" + query_lower):
                matches.append(SearchResult(id=entry["id"], score=0.95, icon_entry=entry, match_tier=1))

        return matches

    def _search_keywords(self, query: str) -> list[SearchResult]:
        """Tier 2: Keyword search using inverted index."""
        if not self._keyword_index:
            return []

        tokens = self._tokenize(query)
        if not tokens:
            return []

        # Count how many query tokens match each icon
        scores: dict[str, int] = {}
        for token in tokens:
            matching_ids = self._keyword_index.get(token, [])
            for icon_id in matching_ids:
                scores[icon_id] = scores.get(icon_id, 0) + 1

        if not scores:
            return []

        max_score = len(tokens)
        results = []
        for icon_id, count in scores.items():
            entry = self._id_map.get(icon_id)
            if entry:
                normalized_score = count / max_score
                results.append(
                    SearchResult(
                        id=icon_id,
                        score=normalized_score * 0.9,  # Cap below exact match
                        icon_entry=entry,
                        match_tier=2,
                    )
                )

        results.sort(key=lambda r: -r.score)
        return results[:50]  # Return generous set for merging

    def _search_fuzzy(self, query: str, threshold: float = 60.0) -> list[SearchResult]:
        """Tier 3: Fuzzy match using rapidfuzz."""
        try:
            from rapidfuzz import fuzz, process
        except ImportError:
            logger.debug("rapidfuzz not installed, skipping fuzzy search")
            return []

        query_lower = query.lower().strip()

        # Build choices: icon names and aliases
        choices: dict[str, str] = {}  # display_name -> icon_id
        for catalog_entry in self._catalog:
            choices[catalog_entry["name"].lower()] = catalog_entry["id"]
            for alias in catalog_entry.get("aliases", []):
                choices[alias.lower()] = catalog_entry["id"]

        # Run fuzzy matching
        matches = process.extract(
            query_lower,
            choices.keys(),
            scorer=fuzz.token_sort_ratio,
            limit=30,
        )

        results = []
        seen_ids: set[str] = set()
        for match_name, score, _ in matches:
            if score < threshold:
                continue
            icon_id = choices[match_name]
            if icon_id in seen_ids:
                continue
            seen_ids.add(icon_id)

            entry = self._id_map.get(icon_id)
            if entry:
                results.append(
                    SearchResult(
                        id=icon_id,
                        score=score / 100.0 * 0.8,  # Normalize and cap
                        icon_entry=entry,
                        match_tier=3,
                    )
                )

        return results

    def _search_semantic(self, query: str, top_k: int = 20) -> list[SearchResult]:
        """Tier 4: Semantic search using embeddings."""
        if self._embeddings is None:
            return []

        try:
            import numpy as np
            from sentence_transformers import SentenceTransformer
        except ImportError:
            logger.debug("sentence-transformers not installed, skipping semantic search")
            return []

        # Lazy-load model
        if self._embed_model is None:
            self._embed_model = SentenceTransformer("all-MiniLM-L6-v2")

        query_embedding = self._embed_model.encode([query])[0]

        # Cosine similarity
        norms = np.linalg.norm(self._embeddings, axis=1) * np.linalg.norm(query_embedding)
        norms = np.where(norms == 0, 1, norms)  # Avoid division by zero
        similarities = np.dot(self._embeddings, query_embedding) / norms

        # Get top-K
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in top_indices:
            if idx >= len(self._embedding_ids):
                continue
            icon_id = self._embedding_ids[idx]
            score = float(similarities[idx])
            if score < 0.2:  # Minimum threshold
                continue

            entry = self._id_map.get(icon_id)
            if entry:
                results.append(
                    SearchResult(
                        id=icon_id,
                        score=score * 0.7,  # Cap below other tiers
                        icon_entry=entry,
                        match_tier=4,
                    )
                )

        return results

    @staticmethod
    def _tokenize(query: str) -> list[str]:
        """Tokenize a query string into search terms."""
        # Lowercase, split on non-alphanumeric
        tokens = re.split(r"[^a-z0-9]+", query.lower())
        return [t for t in tokens if t and len(t) >= 2]

    def get_icon(self, icon_id: str) -> dict | None:
        """Get a single icon entry by ID."""
        self._ensure_loaded()
        return self._id_map.get(icon_id)

    def list_vendors(self) -> dict[str, int]:
        """List all vendors with icon counts."""
        self._ensure_loaded()
        counts: dict[str, int] = {}
        for entry in self._catalog:
            v = entry["vendor"]
            counts[v] = counts.get(v, 0) + 1
        return dict(sorted(counts.items()))

    def list_categories(self, vendor: str | None = None) -> list[str]:
        """List available categories, optionally filtered by vendor."""
        self._ensure_loaded()
        categories: set[str] = set()
        for entry in self._catalog:
            if vendor and entry["vendor"] != vendor:
                continue
            categories.add(entry["category"])
        return sorted(categories)

    @property
    def concepts(self) -> ConceptRegistry:
        """Access the concept registry (loaded on demand)."""
        self._ensure_loaded()
        return self._concepts

    def compare_icons(self, concept: str) -> dict | None:
        """Return concept-group icons grouped by vendor, fully resolved.

        Args:
            concept: Concept group name (e.g., "kubernetes", "serverless").

        Returns:
            Dict with keys: name, vendors, icons (dict[vendor, list[entry]]).
            None if the concept name is unknown.
        """
        self._ensure_loaded()
        group = self._concepts.get_concept(concept)
        if group is None:
            return None

        grouped: dict[str, list[dict]] = {}
        missing: list[str] = []
        for icon_id in group.icon_ids:
            entry = self._id_map.get(icon_id)
            if entry is None:
                missing.append(icon_id)
                continue
            grouped.setdefault(entry["vendor"], []).append(entry)

        return {
            "name": group.name,
            "vendors": group.vendors,
            "icons": grouped,
            "missing": missing,
        }
