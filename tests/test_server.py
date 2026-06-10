"""Tests for server.py — FastMCP tool functions."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from tech_icons.search import SearchEngine

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_engine(search_engine: SearchEngine) -> SearchEngine:
    """Use the shared search_engine fixture as our mock engine."""
    return search_engine


# ---------------------------------------------------------------------------
# search_icons
# ---------------------------------------------------------------------------


class TestSearchIcons:
    """Test search_icons tool function."""

    def test_search_returns_results(self, mock_engine: SearchEngine):
        from tech_icons.server import search_icons

        with patch("tech_icons.server.engine", mock_engine):
            data = search_icons(query="lambda")
            assert isinstance(data, list)
            assert len(data) >= 1
            assert data[0]["id"] == "aws/compute/lambda"

    def test_search_with_vendor_filter(self, mock_engine: SearchEngine):
        from tech_icons.server import search_icons

        with patch("tech_icons.server.engine", mock_engine):
            data = search_icons(query="compute", vendor="aws")
            for item in data:
                assert item["icon_entry"]["vendor"] == "aws"

    def test_search_with_category_filter(self, mock_engine: SearchEngine):
        from tech_icons.server import search_icons

        with patch("tech_icons.server.engine", mock_engine):
            data = search_icons(query="aws", category="compute")
            for item in data:
                assert item["icon_entry"]["category"] == "compute"

    def test_search_with_limit(self, mock_engine: SearchEngine):
        from tech_icons.server import search_icons

        with patch("tech_icons.server.engine", mock_engine):
            data = search_icons(query="aws", limit=2)
            assert len(data) <= 2

    def test_search_empty_query(self, mock_engine: SearchEngine):
        from tech_icons.server import search_icons

        with patch("tech_icons.server.engine", mock_engine):
            data = search_icons(query="")
            assert data == []


# ---------------------------------------------------------------------------
# get_icon
# ---------------------------------------------------------------------------


class TestGetIcon:
    """Test get_icon tool function."""

    def test_get_icon_valid(self, mock_engine: SearchEngine):
        from tech_icons.server import get_icon

        with patch("tech_icons.server.engine", mock_engine):
            data = get_icon(id="aws/compute/lambda")
            assert data["id"] == "aws/compute/lambda"
            assert data["vendor"] == "aws"
            assert data["name"] == "AWS Lambda"

    def test_get_icon_invalid_id(self, mock_engine: SearchEngine):
        from tech_icons.server import get_icon

        with patch("tech_icons.server.engine", mock_engine):
            data = get_icon(id="nonexistent/foo/bar")
            assert "error" in data

    def test_get_icon_full_metadata(self, mock_engine: SearchEngine):
        from tech_icons.server import get_icon

        with patch("tech_icons.server.engine", mock_engine):
            data = get_icon(id="aws/databases/dynamodb")
            assert "aliases" in data
            assert "tags" in data
            assert "description" in data


# ---------------------------------------------------------------------------
# list_categories
# ---------------------------------------------------------------------------


class TestListCategories:
    """Test list_categories tool function."""

    def test_list_categories_all(self, mock_engine: SearchEngine):
        from tech_icons.server import list_categories

        with patch("tech_icons.server.engine", mock_engine):
            data = list_categories()
            assert isinstance(data, list)
            assert "compute" in data
            assert "networking" in data
            assert "databases" in data

    def test_list_categories_vendor_filter(self, mock_engine: SearchEngine):
        from tech_icons.server import list_categories

        with patch("tech_icons.server.engine", mock_engine):
            data = list_categories(vendor="microsoft")
            assert "dynamics-365" in data
            assert "fabric" in data
            # Should not include non-microsoft categories
            assert "databases" not in data

    def test_list_categories_sorted(self, mock_engine: SearchEngine):
        from tech_icons.server import list_categories

        with patch("tech_icons.server.engine", mock_engine):
            data = list_categories()
            assert data == sorted(data)


# ---------------------------------------------------------------------------
# list_vendors
# ---------------------------------------------------------------------------


class TestListVendors:
    """Test list_vendors tool function."""

    def test_list_vendors_all(self, mock_engine: SearchEngine):
        from tech_icons.server import list_vendors

        with patch("tech_icons.server.engine", mock_engine):
            data = list_vendors()
            assert "aws" in data
            assert "azure" in data
            assert "gcp" in data
            assert "microsoft" in data

    def test_list_vendors_with_counts(self, mock_engine: SearchEngine):
        from tech_icons.server import list_vendors

        with patch("tech_icons.server.engine", mock_engine):
            data = list_vendors()
            # Sample catalog: 4 aws, 3 azure, 3 gcp, 5 microsoft
            assert data["aws"] == 4
            assert data["azure"] == 3
            assert data["gcp"] == 3
            assert data["microsoft"] == 5


# ---------------------------------------------------------------------------
# get_icon_svg
# ---------------------------------------------------------------------------


class TestGetIconSvg:
    """Test get_icon_svg tool function."""

    def test_get_svg_raw(self, mock_engine: SearchEngine, tmp_path):
        from tech_icons.server import get_icon_svg

        svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><path d="M0 0"/></svg>'
        icon_dir = tmp_path / "icons" / "aws" / "compute"
        icon_dir.mkdir(parents=True)
        (icon_dir / "lambda.svg").write_text(svg)

        with patch("tech_icons.server.engine", mock_engine), patch("tech_icons._paths.package_root", lambda: tmp_path):
            text = get_icon_svg(id="aws/compute/lambda", format="raw")
            assert isinstance(text, str)
            assert "<svg" in text

    def test_get_svg_ppt_master(self, mock_engine: SearchEngine, tmp_path):
        from tech_icons.server import get_icon_svg

        svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><path d="M0 0"/></svg>'
        icon_dir = tmp_path / "icons" / "aws" / "compute"
        icon_dir.mkdir(parents=True)
        (icon_dir / "lambda.svg").write_text(svg)

        with patch("tech_icons.server.engine", mock_engine), patch("tech_icons._paths.package_root", lambda: tmp_path):
            text = get_icon_svg(id="aws/compute/lambda", format="ppt_master")
            assert isinstance(text, str)
            assert "tech-icons/aws/compute/lambda" in text
            assert "xlink:href" not in text

    def test_get_svg_base64(self, mock_engine: SearchEngine, tmp_path):
        from tech_icons.server import get_icon_svg

        svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><path d="M0 0"/></svg>'
        icon_dir = tmp_path / "icons" / "aws" / "compute"
        icon_dir.mkdir(parents=True)
        (icon_dir / "lambda.svg").write_text(svg)

        with patch("tech_icons.server.engine", mock_engine), patch("tech_icons._paths.package_root", lambda: tmp_path):
            text = get_icon_svg(id="aws/compute/lambda", format="base64")
            import base64

            decoded = base64.b64decode(text)
            assert b"<svg" in decoded

    def test_get_svg_data_uri(self, mock_engine: SearchEngine, tmp_path):
        from tech_icons.server import get_icon_svg

        svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><path d="M0 0"/></svg>'
        icon_dir = tmp_path / "icons" / "aws" / "compute"
        icon_dir.mkdir(parents=True)
        (icon_dir / "lambda.svg").write_text(svg)

        with patch("tech_icons.server.engine", mock_engine), patch("tech_icons._paths.package_root", lambda: tmp_path):
            text = get_icon_svg(id="aws/compute/lambda", format="data_uri")
            assert text.startswith("data:image/svg+xml;base64,")

    def test_get_svg_invalid_id(self, mock_engine: SearchEngine):
        from tech_icons.server import get_icon_svg

        with patch("tech_icons.server.engine", mock_engine):
            text = get_icon_svg(id="nonexistent/icon")
            data = json.loads(text)
            assert "error" in data

    def test_get_svg_default_format_is_raw(self, mock_engine: SearchEngine, tmp_path):
        from tech_icons.server import get_icon_svg

        svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><path d="M0 0"/></svg>'
        icon_dir = tmp_path / "icons" / "aws" / "compute"
        icon_dir.mkdir(parents=True)
        (icon_dir / "lambda.svg").write_text(svg)

        with patch("tech_icons.server.engine", mock_engine), patch("tech_icons._paths.package_root", lambda: tmp_path):
            text = get_icon_svg(id="aws/compute/lambda")
            assert isinstance(text, str)
            assert "<svg" in text

    def test_get_svg_download(self, mock_engine: SearchEngine, tmp_path):
        from fastmcp.utilities.types import Image

        from tech_icons.server import get_icon_svg

        svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><path d="M0 0"/></svg>'
        icon_dir = tmp_path / "icons" / "aws" / "compute"
        icon_dir.mkdir(parents=True)
        (icon_dir / "lambda.svg").write_text(svg)

        with patch("tech_icons.server.engine", mock_engine), patch("tech_icons._paths.package_root", lambda: tmp_path):
            result = get_icon_svg(id="aws/compute/lambda", format="download")
            assert isinstance(result, list)
            assert len(result) == 2

            # First item: text summary
            text_item = result[0]
            assert isinstance(text_item, str)
            assert "aws/compute/lambda" in text_item
            assert "KB" in text_item

            # Second item: Image object
            image_item = result[1]
            assert isinstance(image_item, Image)


# ---------------------------------------------------------------------------
# list_concepts / compare_icons
# ---------------------------------------------------------------------------


class TestConceptsTools:
    """Test list_concepts and compare_icons tool functions."""

    def test_list_concepts(self, mock_engine: SearchEngine):
        from tech_icons.server import list_concepts

        with patch("tech_icons.server.engine", mock_engine):
            names = list_concepts()
            assert isinstance(names, list)

    def test_compare_icons_valid(self, mock_engine: SearchEngine):
        from tech_icons.server import compare_icons

        with patch("tech_icons.server.engine", mock_engine):
            result = compare_icons(concept="serverless")
            assert any(entry["vendor"] == "aws" and entry["name"] == "AWS Lambda" for entry in result["icons"]["aws"])

    def test_compare_icons_not_found(self, mock_engine: SearchEngine):
        from tech_icons.server import compare_icons

        with patch("tech_icons.server.engine", mock_engine):
            result = compare_icons(concept="nonexistent-concept")
            assert "error" in result


# ---------------------------------------------------------------------------
# Resource
# ---------------------------------------------------------------------------


class TestResource:
    """Test icon_catalog resource."""

    def test_icon_catalog_resource(self, mock_engine: SearchEngine):
        from tech_icons.server import icon_catalog

        with patch("tech_icons.server.engine", mock_engine):
            data = json.loads(icon_catalog())
            assert isinstance(data, list)
            assert len(data) == 15


# ---------------------------------------------------------------------------
# CLI transport flags
# ---------------------------------------------------------------------------


class TestCLITransport:
    """Test main() CLI argument routing for transport modes."""

    @pytest.fixture(autouse=True)
    def _mock_engine(self, mock_engine: SearchEngine):
        """Ensure engine is patched for all CLI tests."""
        pass

    def test_default_is_stdio(self, mock_engine: SearchEngine):
        from tech_icons.server import main

        with (
            patch("tech_icons.server.engine", mock_engine),
            patch("tech_icons.server.mcp.run") as mock_run,
        ):
            main([])
            mock_run.assert_called_once()

    def test_transport_stdio_explicit(self, mock_engine: SearchEngine):
        from tech_icons.server import main

        with (
            patch("tech_icons.server.engine", mock_engine),
            patch("tech_icons.server.mcp.run") as mock_run,
        ):
            main(["--transport", "stdio"])
            mock_run.assert_called_once()

    def test_transport_http(self, mock_engine: SearchEngine):
        from tech_icons.server import main

        with (
            patch("tech_icons.server.engine", mock_engine),
            patch("tech_icons.server.mcp.run") as mock_run,
        ):
            main(["--transport", "http", "--port", "8000"])
            mock_run.assert_called_once_with(transport="http", host="127.0.0.1", port=8000)

    def test_transport_dual(self, mock_engine: SearchEngine):
        from tech_icons.server import main

        with (
            patch("tech_icons.server.engine", mock_engine),
            patch("tech_icons.server.mcp.run_stdio_async") as mock_stdio,
            patch("tech_icons.server.mcp.run_http_async") as mock_http,
            patch("tech_icons.server.asyncio.run") as mock_asyncio_run,
        ):
            main(["--transport", "dual", "--port", "9000"])
            mock_asyncio_run.assert_called_once()
            mock_stdio.assert_not_called()  # not called yet — inside gather
            mock_http.assert_not_called()  # not called yet — inside gather

    def test_transport_http_with_host(self, mock_engine: SearchEngine):
        from tech_icons.server import main

        with (
            patch("tech_icons.server.engine", mock_engine),
            patch("tech_icons.server.mcp.run") as mock_run,
        ):
            main(["--transport", "http", "--host", "0.0.0.0", "--port", "8080"])  # noqa: S104
            mock_run.assert_called_once_with(transport="http", host="0.0.0.0", port=8080)  # noqa: S104

    def test_invalid_transport_rejected(self):
        from tech_icons.server import main

        with pytest.raises(SystemExit):
            main(["--transport", "bogus"])
