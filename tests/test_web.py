"""Tests for the FastAPI web app."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient


@pytest.fixture
def web_client(
    tmp_path: Path,
    sample_catalog: list[dict],
    sample_keyword_index: dict,
    sample_enrichments: dict,
    sample_svg_content: str,
    sample_png_content: bytes,
    monkeypatch,
):
    """TestClient over tech_icons.web.app with the engine pointed at temp fixtures."""
    catalog_dir = tmp_path / "catalog"
    catalog_dir.mkdir()
    (catalog_dir / "icons.json").write_text(json.dumps(sample_catalog))
    (catalog_dir / "keyword_index.json").write_text(json.dumps(sample_keyword_index))
    (catalog_dir / "enrichments.yaml").write_text(yaml.safe_dump(sample_enrichments))

    # Create the icon files at the paths declared in the sample catalog
    for entry in sample_catalog:
        for image_type, rel_path in entry["formats"].items():
            file_path = tmp_path / rel_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            if image_type == "svg":
                file_path.write_text(sample_svg_content)
            else:
                file_path.write_bytes(sample_png_content)

    # Reload module with patched paths
    import tech_icons.web.app as web_app
    from tech_icons.search import SearchEngine

    monkeypatch.setattr("tech_icons._paths.package_root", lambda: tmp_path)
    new_engine = SearchEngine(catalog_dir=catalog_dir)
    new_engine.load()
    monkeypatch.setattr(web_app, "engine", new_engine)

    # FastAPI startup hook would re-load; we already loaded. Use TestClient
    # which triggers startup once.
    with TestClient(web_app.app) as client:
        yield client


def test_health(web_client: TestClient) -> None:
    r = web_client.get("/api/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["icons"] == 18  # updated from 15 to match new catalog
    assert data["concepts"] == 4


def test_list_vendors(web_client: TestClient) -> None:
    r = web_client.get("/api/vendors")
    assert r.status_code == 200
    vendors = r.json()
    assert "aws" in vendors
    assert "alibabacloud" in vendors
    assert "kubernetes" in vendors
    assert "programming" in vendors


def test_list_categories(web_client: TestClient) -> None:
    r = web_client.get("/api/categories")
    assert r.status_code == 200
    cats = r.json()
    assert "compute" in cats
    assert "databases" in cats


def test_list_categories_filtered_by_vendor(web_client: TestClient) -> None:
    r = web_client.get("/api/categories?vendor=microsoft")
    assert r.status_code == 200
    cats = r.json()
    assert "fabric" in cats
    assert "compute" not in cats


def test_search(web_client: TestClient) -> None:
    r = web_client.get("/api/search?q=lambda")
    assert r.status_code == 200
    results = r.json()
    assert any(item["id"] == "aws/compute/lambda" for item in results)


def test_search_with_vendor_filter(web_client: TestClient) -> None:
    r = web_client.get("/api/search?q=serverless&vendor=azure")
    assert r.status_code == 200
    results = r.json()
    for item in results:
        assert item["icon_entry"]["vendor"] == "azure"


def test_list_icons_paginated(web_client: TestClient) -> None:
    r = web_client.get("/api/icons?limit=5&offset=0")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 18  # updated
    assert len(data["items"]) == 5


def test_list_icons_offset(web_client: TestClient) -> None:
    r = web_client.get("/api/icons?limit=5&offset=15")
    assert r.status_code == 200
    data = r.json()
    assert data["offset"] == 15
    assert len(data["items"]) == 3  # only 3 left


def test_get_icon(web_client: TestClient) -> None:
    r = web_client.get("/api/icons/aws/compute/lambda")
    assert r.status_code == 200
    entry = r.json()
    assert entry["id"] == "aws/compute/lambda"
    assert "svg" in entry["formats"]
    assert "png" in entry["formats"]
    assert "serverless" in entry["related_concepts"]


def test_get_icon_not_found(web_client: TestClient) -> None:
    r = web_client.get("/api/icons/aws/compute/nonexistent")
    assert r.status_code == 404


# --- New /api/icon/ route tests ---


def test_get_icon_image_raw(web_client: TestClient) -> None:
    r = web_client.get("/api/icon/aws/compute/lambda")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("image/svg+xml")
    assert r.text.startswith("<svg")


def test_get_icon_png_raw(web_client: TestClient) -> None:
    """PNG icon served with correct MIME type."""
    r = web_client.get("/api/icon/aws/compute/lambda?image_type=png")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("image/png")
    assert r.content[:4] == b"\x89PNG"


def test_get_icon_png_fallback(web_client: TestClient) -> None:
    """Requesting SVG for a PNG-only icon falls back to PNG."""
    r = web_client.get("/api/icon/alibabacloud/general/alibabacloud")
    assert r.status_code == 200
    # Falls back to PNG MIME
    assert r.headers["content-type"].startswith("image/png")


def test_get_icon_image_data_uri(web_client: TestClient) -> None:
    r = web_client.get("/api/icon/aws/compute/lambda?format=data_uri")
    assert r.status_code == 200
    assert r.text.startswith("data:image/svg+xml;base64,")


def test_get_icon_png_data_uri(web_client: TestClient) -> None:
    r = web_client.get("/api/icon/aws/compute/lambda?format=data_uri&image_type=png")
    assert r.status_code == 200
    assert r.text.startswith("data:image/png;base64,")


def test_get_icon_invalid_format(web_client: TestClient) -> None:
    r = web_client.get("/api/icon/aws/compute/lambda?format=bogus")
    assert r.status_code == 400


def test_get_icon_inline_group_png_raises(web_client: TestClient) -> None:
    """inline_group with PNG should return 400."""
    r = web_client.get("/api/icon/aws/compute/lambda?format=inline_group&image_type=png")
    assert r.status_code == 400


def test_get_icon_download_format(web_client: TestClient) -> None:
    """format=download returns raw SVG with Content-Disposition attachment header."""
    r = web_client.get("/api/icon/aws/compute/lambda?format=download")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("image/svg+xml")
    assert "attachment" in r.headers["content-disposition"]


def test_get_icon_download_query_param(web_client: TestClient) -> None:
    """?download=1 (with default format=raw) sets Content-Disposition header."""
    r = web_client.get("/api/icon/aws/compute/lambda?download=1")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("image/svg+xml")
    assert "attachment" in r.headers["content-disposition"]


def test_list_concepts(web_client: TestClient) -> None:
    r = web_client.get("/api/concepts")
    assert r.status_code == 200
    concepts = r.json()
    names = {c["name"] for c in concepts}
    assert "serverless" in names
    assert "kubernetes" in names


def test_get_concept(web_client: TestClient) -> None:
    r = web_client.get("/api/concepts/serverless")
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "serverless"
    assert "aws" in data["icons"]
    assert "azure" in data["icons"]


def test_get_concept_not_found(web_client: TestClient) -> None:
    r = web_client.get("/api/concepts/totally-fake-concept")
    assert r.status_code == 404


def test_index_html_served(web_client: TestClient) -> None:
    r = web_client.get("/")
    assert r.status_code == 200
    assert "tech-icons" in r.text.lower()
