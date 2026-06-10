"""Tests for src/server.py — MCP server integration tests."""

from __future__ import annotations

import json
from pathlib import Path
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


@pytest.fixture
def icon_file(tmp_path: Path) -> Path:
    """Create a real icon file for get_icon_svg tests."""
    svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><path d="M0 0"/></svg>'
    icon_path = tmp_path / "icons" / "aws" / "compute" / "lambda.svg"
    icon_path.parent.mkdir(parents=True)
    icon_path.write_text(svg)
    return tmp_path


# ---------------------------------------------------------------------------
# Server tool handler tests (unit-testing the handler functions directly)
# ---------------------------------------------------------------------------


class TestHandleSearch:
    """Test _handle_search function."""

    def test_search_returns_results(self, mock_engine: SearchEngine):
        from tech_icons.server import _handle_search

        with patch("tech_icons.server.engine", mock_engine):
            results = _handle_search({"query": "lambda"})
            assert len(results) == 1
            data = json.loads(results[0].text)
            assert isinstance(data, list)
            assert len(data) >= 1
            assert data[0]["id"] == "aws/compute/lambda"

    def test_search_with_vendor_filter(self, mock_engine: SearchEngine):
        from tech_icons.server import _handle_search

        with patch("tech_icons.server.engine", mock_engine):
            results = _handle_search({"query": "compute", "vendor": "aws"})
            data = json.loads(results[0].text)
            for item in data:
                assert item["icon_entry"]["vendor"] == "aws"

    def test_search_with_category_filter(self, mock_engine: SearchEngine):
        from tech_icons.server import _handle_search

        with patch("tech_icons.server.engine", mock_engine):
            results = _handle_search({"query": "aws", "category": "compute"})
            data = json.loads(results[0].text)
            for item in data:
                assert item["icon_entry"]["category"] == "compute"

    def test_search_with_limit(self, mock_engine: SearchEngine):
        from tech_icons.server import _handle_search

        with patch("tech_icons.server.engine", mock_engine):
            results = _handle_search({"query": "aws", "limit": 2})
            data = json.loads(results[0].text)
            assert len(data) <= 2

    def test_search_empty_query(self, mock_engine: SearchEngine):
        from tech_icons.server import _handle_search

        with patch("tech_icons.server.engine", mock_engine):
            results = _handle_search({"query": ""})
            data = json.loads(results[0].text)
            assert data == []


# ---------------------------------------------------------------------------
# get_icon handler
# ---------------------------------------------------------------------------


class TestHandleGetIcon:
    """Test _handle_get_icon function."""

    def test_get_icon_valid(self, mock_engine: SearchEngine):
        from tech_icons.server import _handle_get_icon

        with patch("tech_icons.server.engine", mock_engine):
            results = _handle_get_icon({"id": "aws/compute/lambda"})
            data = json.loads(results[0].text)
            assert data["id"] == "aws/compute/lambda"
            assert data["vendor"] == "aws"
            assert data["name"] == "AWS Lambda"

    def test_get_icon_invalid_id(self, mock_engine: SearchEngine):
        from tech_icons.server import _handle_get_icon

        with patch("tech_icons.server.engine", mock_engine):
            results = _handle_get_icon({"id": "nonexistent/foo/bar"})
            data = json.loads(results[0].text)
            assert "error" in data

    def test_get_icon_full_metadata(self, mock_engine: SearchEngine):
        from tech_icons.server import _handle_get_icon

        with patch("tech_icons.server.engine", mock_engine):
            results = _handle_get_icon({"id": "aws/databases/dynamodb"})
            data = json.loads(results[0].text)
            assert "aliases" in data
            assert "tags" in data
            assert "description" in data


# ---------------------------------------------------------------------------
# list_categories handler
# ---------------------------------------------------------------------------


class TestHandleListCategories:
    """Test _handle_list_categories function."""

    def test_list_categories_all(self, mock_engine: SearchEngine):
        from tech_icons.server import _handle_list_categories

        with patch("tech_icons.server.engine", mock_engine):
            results = _handle_list_categories({})
            data = json.loads(results[0].text)
            assert isinstance(data, list)
            assert "compute" in data
            assert "networking" in data
            assert "databases" in data

    def test_list_categories_vendor_filter(self, mock_engine: SearchEngine):
        from tech_icons.server import _handle_list_categories

        with patch("tech_icons.server.engine", mock_engine):
            results = _handle_list_categories({"vendor": "microsoft"})
            data = json.loads(results[0].text)
            assert "dynamics-365" in data
            assert "fabric" in data
            # Should not include non-microsoft categories
            assert "databases" not in data

    def test_list_categories_sorted(self, mock_engine: SearchEngine):
        from tech_icons.server import _handle_list_categories

        with patch("tech_icons.server.engine", mock_engine):
            results = _handle_list_categories({})
            data = json.loads(results[0].text)
            assert data == sorted(data)


# ---------------------------------------------------------------------------
# list_vendors handler
# ---------------------------------------------------------------------------


class TestHandleListVendors:
    """Test _handle_list_vendors function."""

    def test_list_vendors_all(self, mock_engine: SearchEngine):
        from tech_icons.server import _handle_list_vendors

        with patch("tech_icons.server.engine", mock_engine):
            results = _handle_list_vendors()
            data = json.loads(results[0].text)
            assert "aws" in data
            assert "azure" in data
            assert "gcp" in data
            assert "microsoft" in data

    def test_list_vendors_with_counts(self, mock_engine: SearchEngine):
        from tech_icons.server import _handle_list_vendors

        with patch("tech_icons.server.engine", mock_engine):
            results = _handle_list_vendors()
            data = json.loads(results[0].text)
            # Sample catalog: 4 aws, 3 azure, 3 gcp, 5 microsoft
            assert data["aws"] == 4
            assert data["azure"] == 3
            assert data["gcp"] == 3
            assert data["microsoft"] == 5


# ---------------------------------------------------------------------------
# get_icon_svg handler
# ---------------------------------------------------------------------------


class TestHandleGetIconSvg:
    """Test _handle_get_icon_svg function."""

    def test_get_svg_raw(self, mock_engine: SearchEngine, icon_file: Path):
        from tech_icons.server import _handle_get_icon_svg

        with patch("tech_icons.server.engine", mock_engine), patch("tech_icons._paths.package_root", lambda: icon_file):
            results = _handle_get_icon_svg({"id": "aws/compute/lambda", "format": "raw"})
            text = results[0].text
            assert "<svg" in text

    def test_get_svg_ppt_master(self, mock_engine: SearchEngine, icon_file: Path):
        from tech_icons.server import _handle_get_icon_svg

        with patch("tech_icons.server.engine", mock_engine), patch("tech_icons._paths.package_root", lambda: icon_file):
            results = _handle_get_icon_svg({"id": "aws/compute/lambda", "format": "ppt_master"})
            text = results[0].text
            assert "tech-icons/aws/compute/lambda" in text

    def test_get_svg_base64(self, mock_engine: SearchEngine, icon_file: Path):
        from tech_icons.server import _handle_get_icon_svg

        with patch("tech_icons.server.engine", mock_engine), patch("tech_icons._paths.package_root", lambda: icon_file):
            results = _handle_get_icon_svg({"id": "aws/compute/lambda", "format": "base64"})
            import base64

            decoded = base64.b64decode(results[0].text)
            assert b"<svg" in decoded

    def test_get_svg_data_uri(self, mock_engine: SearchEngine, icon_file: Path):
        from tech_icons.server import _handle_get_icon_svg

        with patch("tech_icons.server.engine", mock_engine), patch("tech_icons._paths.package_root", lambda: icon_file):
            results = _handle_get_icon_svg({"id": "aws/compute/lambda", "format": "data_uri"})
            assert results[0].text.startswith("data:image/svg+xml;base64,")

    def test_get_svg_invalid_id(self, mock_engine: SearchEngine):
        from tech_icons.server import _handle_get_icon_svg

        with patch("tech_icons.server.engine", mock_engine):
            results = _handle_get_icon_svg({"id": "nonexistent/icon"})
            data = json.loads(results[0].text)
            assert "error" in data

    def test_get_svg_default_format_is_raw(self, mock_engine: SearchEngine, icon_file: Path):
        from tech_icons.server import _handle_get_icon_svg

        with patch("tech_icons.server.engine", mock_engine), patch("tech_icons._paths.package_root", lambda: icon_file):
            results = _handle_get_icon_svg({"id": "aws/compute/lambda"})
            assert "<svg" in results[0].text


# ---------------------------------------------------------------------------
# call_tool dispatcher
# ---------------------------------------------------------------------------


class TestCallTool:
    """Test the call_tool dispatcher."""

    @pytest.mark.asyncio
    async def test_call_tool_search(self, mock_engine: SearchEngine):
        from tech_icons.server import call_tool

        with patch("tech_icons.server.engine", mock_engine):
            results = await call_tool("search_icons", {"query": "lambda"})
            assert len(results) == 1
            data = json.loads(results[0].text)
            assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_call_tool_unknown(self, mock_engine: SearchEngine):
        from tech_icons.server import call_tool

        with patch("tech_icons.server.engine", mock_engine):
            results = await call_tool("nonexistent_tool", {})
            assert "Unknown tool" in results[0].text

    @pytest.mark.asyncio
    async def test_call_tool_get_icon(self, mock_engine: SearchEngine):
        from tech_icons.server import call_tool

        with patch("tech_icons.server.engine", mock_engine):
            results = await call_tool("get_icon", {"id": "aws/compute/ec2"})
            data = json.loads(results[0].text)
            assert data["id"] == "aws/compute/ec2"

    @pytest.mark.asyncio
    async def test_call_tool_list_vendors(self, mock_engine: SearchEngine):
        from tech_icons.server import call_tool

        with patch("tech_icons.server.engine", mock_engine):
            results = await call_tool("list_vendors", {})
            data = json.loads(results[0].text)
            assert isinstance(data, dict)
            assert "aws" in data

    @pytest.mark.asyncio
    async def test_call_tool_list_categories(self, mock_engine: SearchEngine):
        from tech_icons.server import call_tool

        with patch("tech_icons.server.engine", mock_engine):
            results = await call_tool("list_categories", {})
            data = json.loads(results[0].text)
            assert isinstance(data, list)


# ---------------------------------------------------------------------------
# list_tools
# ---------------------------------------------------------------------------


class TestListTools:
    """Test that tool definitions are correct."""

    @pytest.mark.asyncio
    async def test_list_tools_returns_all(self):
        from tech_icons.server import list_tools

        tools = await list_tools()
        names = {t.name for t in tools}
        assert names == {
            "search_icons",
            "get_icon",
            "list_categories",
            "list_vendors",
            "get_icon_svg",
            "list_concepts",
            "compare_icons",
        }

    @pytest.mark.asyncio
    async def test_search_icons_schema(self):
        from tech_icons.server import list_tools

        tools = await list_tools()
        search_tool = next(t for t in tools if t.name == "search_icons")
        schema = search_tool.inputSchema
        assert "query" in schema["properties"]
        assert "query" in schema["required"]
