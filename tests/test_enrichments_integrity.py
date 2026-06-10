"""Guard test: every icon ID referenced in `tech_icons/catalog/enrichments.yaml` must
exist in `tech_icons/catalog/icons.json`. Catches drift when packages restructure or
collectors emit new ID forms.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENRICHMENTS = PROJECT_ROOT / "tech_icons" / "catalog" / "enrichments.yaml"
CATALOG = PROJECT_ROOT / "tech_icons" / "catalog" / "icons.json"


@pytest.mark.skipif(
    not (ENRICHMENTS.exists() and CATALOG.exists()),
    reason="catalog has not been built yet",
)
def test_enrichment_refs_exist_in_catalog() -> None:
    data = json.loads(CATALOG.read_text())
    icons = data.get("icons", data) if isinstance(data, dict) else data
    catalog_ids = {entry["id"] for entry in icons}

    enr = yaml.safe_load(ENRICHMENTS.read_text()) or {}
    missing: list[tuple[str, str, str]] = []
    for section in ("aliases", "tags"):
        for concept, refs in (enr.get(section) or {}).items():
            for icon_id in refs:
                if icon_id not in catalog_ids:
                    missing.append((section, concept, icon_id))

    assert not missing, "Broken icon references in enrichments.yaml:\n" + "\n".join(
        f"  [{s}] {c}: {r}" for s, c, r in missing
    )
