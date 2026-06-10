"""Cross-vendor concept groups loaded from enrichments.yaml.

A concept group is a named technology concept (e.g., "kubernetes", "serverless",
"object-storage") backed by a list of icon IDs spanning multiple cloud vendors.

Source of truth: catalog/enrichments.yaml `aliases:` section. Each alias key is
treated as a concept group name, with its value list being the icon IDs.
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

DEFAULT_ENRICHMENTS_PATH = Path("catalog/enrichments.yaml")


@dataclass
class ConceptGroup:
    """A cross-vendor concept group."""

    name: str
    icon_ids: list[str]
    vendors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ConceptRegistry:
    """Loads and serves concept groups derived from enrichments.yaml."""

    def __init__(self, enrichments_path: Path = DEFAULT_ENRICHMENTS_PATH):
        self._path = enrichments_path
        self._groups: dict[str, ConceptGroup] = {}
        # Reverse index: icon_id -> list of concept names it appears in
        self._icon_to_concepts: dict[str, list[str]] = {}
        self._loaded = False

    def load(self) -> None:
        """Parse enrichments.yaml and build concept groups."""
        if not self._path.exists():
            logger.warning(f"Enrichments file not found: {self._path}")
            self._loaded = True
            return

        with open(self._path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        aliases: dict[str, list[str]] = data.get("aliases") or {}

        for name, icon_ids in aliases.items():
            if not isinstance(icon_ids, list) or not icon_ids:
                continue
            vendors = sorted({iid.split("/", 1)[0] for iid in icon_ids if "/" in iid})
            group = ConceptGroup(name=name, icon_ids=list(icon_ids), vendors=vendors)
            self._groups[name] = group

            for iid in icon_ids:
                self._icon_to_concepts.setdefault(iid, []).append(name)

        self._loaded = True
        logger.info(f"Loaded {len(self._groups)} concept groups from {self._path}")

    def _ensure_loaded(self) -> None:
        if not self._loaded:
            self.load()

    def list_concepts(self) -> list[str]:
        """Return all concept group names, sorted."""
        self._ensure_loaded()
        return sorted(self._groups.keys())

    def get_concept(self, name: str) -> ConceptGroup | None:
        """Return a concept group by name, or None if not found."""
        self._ensure_loaded()
        return self._groups.get(name)

    def get_concepts_for_icon(self, icon_id: str) -> list[str]:
        """Return all concept group names that contain this icon."""
        self._ensure_loaded()
        return list(self._icon_to_concepts.get(icon_id, []))

    @property
    def all_groups(self) -> dict[str, ConceptGroup]:
        self._ensure_loaded()
        return self._groups
