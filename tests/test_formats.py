"""Tests for src/formats.py — output format adapters."""

from __future__ import annotations

import base64
from pathlib import Path

import pytest

from tech_icons.formats import (
    IconNotFoundError,
    base64_svg,
    data_uri,
    format_icon,
    inline_group,
    ppt_master_placeholder,
    raw_svg,
    svg_path,
)

# ---------------------------------------------------------------------------
# raw_svg
# ---------------------------------------------------------------------------


class TestRawSvg:
    """Tests for raw_svg format."""

    def test_raw_svg_returns_content(self, tmp_icons_dir: Path):
        path = tmp_icons_dir / "aws" / "compute" / "lambda.svg"
        content = raw_svg(path)
        assert content.startswith("<svg")
        assert "</svg>" in content

    def test_raw_svg_preserves_full_content(self, tmp_icons_dir: Path, sample_svg_content: str):
        path = tmp_icons_dir / "aws" / "compute" / "lambda.svg"
        content = raw_svg(path)
        assert content == sample_svg_content

    def test_raw_svg_missing_file_raises(self, tmp_path: Path):
        with pytest.raises(IconNotFoundError, match="not found"):
            raw_svg(tmp_path / "nonexistent.svg")


# ---------------------------------------------------------------------------
# svg_path
# ---------------------------------------------------------------------------


class TestSvgPath:
    """Tests for svg_path format."""

    def test_svg_path_returns_absolute(self, tmp_icons_dir: Path):
        path = tmp_icons_dir / "aws" / "compute" / "lambda.svg"
        result = svg_path(path)
        assert Path(result).is_absolute()
        assert result.endswith("lambda.svg")

    def test_svg_path_resolves_symlinks(self, tmp_icons_dir: Path):
        path = tmp_icons_dir / "aws" / "compute" / "lambda.svg"
        result = svg_path(path)
        # Should be the resolved path
        assert Path(result).exists()

    def test_svg_path_missing_file_raises(self, tmp_path: Path):
        with pytest.raises(IconNotFoundError):
            svg_path(tmp_path / "ghost.svg")


# ---------------------------------------------------------------------------
# base64_svg
# ---------------------------------------------------------------------------


class TestBase64Svg:
    """Tests for base64_svg format."""

    def test_base64_valid_encoding(self, tmp_icons_dir: Path):
        path = tmp_icons_dir / "aws" / "compute" / "lambda.svg"
        encoded = base64_svg(path)
        # Should be valid base64
        decoded = base64.b64decode(encoded)
        assert b"<svg" in decoded

    def test_base64_roundtrip(self, tmp_icons_dir: Path, sample_svg_content: str):
        path = tmp_icons_dir / "aws" / "compute" / "lambda.svg"
        encoded = base64_svg(path)
        decoded = base64.b64decode(encoded).decode("utf-8")
        assert decoded == sample_svg_content

    def test_base64_ascii_only(self, tmp_icons_dir: Path):
        path = tmp_icons_dir / "aws" / "compute" / "lambda.svg"
        encoded = base64_svg(path)
        assert encoded.isascii()

    def test_base64_missing_file_raises(self, tmp_path: Path):
        with pytest.raises(IconNotFoundError):
            base64_svg(tmp_path / "missing.svg")


# ---------------------------------------------------------------------------
# data_uri
# ---------------------------------------------------------------------------


class TestDataUri:
    """Tests for data_uri format."""

    def test_data_uri_prefix(self, tmp_icons_dir: Path):
        path = tmp_icons_dir / "aws" / "compute" / "lambda.svg"
        result = data_uri(path)
        assert result.startswith("data:image/svg+xml;base64,")

    def test_data_uri_contains_valid_base64(self, tmp_icons_dir: Path):
        path = tmp_icons_dir / "aws" / "compute" / "lambda.svg"
        result = data_uri(path)
        _, encoded_part = result.split(",", 1)
        decoded = base64.b64decode(encoded_part)
        assert b"<svg" in decoded

    def test_data_uri_missing_file_raises(self, tmp_path: Path):
        with pytest.raises(IconNotFoundError):
            data_uri(tmp_path / "nope.svg")


# ---------------------------------------------------------------------------
# ppt_master_placeholder
# ---------------------------------------------------------------------------


class TestPptMasterPlaceholder:
    """Tests for ppt_master_placeholder format."""

    def test_ppt_master_correct_xml(self):
        result = ppt_master_placeholder("aws/compute/lambda")
        assert 'data-icon="tech-icons/aws/compute/lambda"' in result
        assert 'xlink:href="icons/aws/compute/lambda.svg"' in result
        assert result.startswith("<use")
        assert result.endswith("/>")

    @pytest.mark.parametrize(
        "icon_id",
        [
            "aws/compute/lambda",
            "azure/networking/load-balancer",
            "gcp/databases/cloud-sql",
            "microsoft/fabric/data-warehouse",
        ],
    )
    def test_ppt_master_all_vendors(self, icon_id: str):
        result = ppt_master_placeholder(icon_id)
        assert f"tech-icons/{icon_id}" in result
        assert f"icons/{icon_id}.svg" in result


# ---------------------------------------------------------------------------
# inline_group
# ---------------------------------------------------------------------------


class TestInlineGroup:
    """Tests for inline_group format."""

    def test_inline_group_wraps_in_g_tag(self, tmp_icons_dir: Path):
        path = tmp_icons_dir / "aws" / "compute" / "lambda.svg"
        result = inline_group(path)
        assert result.startswith("<g")
        assert result.endswith("</g>")

    def test_inline_group_preserves_viewbox(self, tmp_icons_dir: Path):
        path = tmp_icons_dir / "aws" / "compute" / "lambda.svg"
        result = inline_group(path)
        assert 'viewBox="0 0 48 48"' in result

    def test_inline_group_strips_svg_wrapper(self, tmp_icons_dir: Path):
        path = tmp_icons_dir / "aws" / "compute" / "lambda.svg"
        result = inline_group(path)
        assert "<svg" not in result
        assert "</svg>" not in result

    def test_inline_group_preserves_inner_content(self, tmp_icons_dir: Path):
        path = tmp_icons_dir / "aws" / "compute" / "lambda.svg"
        result = inline_group(path)
        assert '<path d="M24 4L4 44h40z"' in result

    def test_inline_group_invalid_svg_raises(self, tmp_path: Path):
        bad_file = tmp_path / "bad.svg"
        bad_file.write_text("not an svg at all")
        with pytest.raises(IconNotFoundError, match="Invalid SVG"):
            inline_group(bad_file)

    def test_inline_group_missing_file_raises(self, tmp_path: Path):
        with pytest.raises(IconNotFoundError):
            inline_group(tmp_path / "gone.svg")


# ---------------------------------------------------------------------------
# format_icon dispatcher
# ---------------------------------------------------------------------------


class TestFormatIconDispatcher:
    """Tests for format_icon routing."""

    @pytest.mark.parametrize(
        "fmt",
        ["raw", "path", "base64", "data_uri", "inline_group"],
    )
    def test_dispatcher_routes_correctly(self, tmp_icons_dir: Path, fmt: str):
        """All file-based formats work through dispatcher."""
        path = tmp_icons_dir / "aws" / "compute" / "lambda.svg"
        result = format_icon(path, "aws/compute/lambda", fmt=fmt)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_dispatcher_ppt_master(self, tmp_icons_dir: Path):
        """ppt_master format works via dispatcher (doesn't need file)."""
        path = tmp_icons_dir / "aws" / "compute" / "lambda.svg"
        result = format_icon(path, "aws/compute/lambda", fmt="ppt_master")
        assert "tech-icons/aws/compute/lambda" in result

    def test_dispatcher_default_is_raw(self, tmp_icons_dir: Path, sample_svg_content: str):
        """Default format is 'raw'."""
        path = tmp_icons_dir / "aws" / "compute" / "lambda.svg"
        result = format_icon(path, "aws/compute/lambda")
        assert result == sample_svg_content

    def test_dispatcher_unknown_format_raises(self, tmp_icons_dir: Path):
        path = tmp_icons_dir / "aws" / "compute" / "lambda.svg"
        with pytest.raises(ValueError, match="Unknown format"):
            format_icon(path, "aws/compute/lambda", fmt="jpeg")

    def test_dispatcher_missing_file_raises(self, tmp_path: Path):
        with pytest.raises(IconNotFoundError):
            format_icon(tmp_path / "missing.svg", "test/icon", fmt="raw")


# ---------------------------------------------------------------------------
# Multi-vendor format tests
# ---------------------------------------------------------------------------


class TestMultiVendorFormats:
    """Test formats work across different vendor icon files."""

    @pytest.mark.parametrize(
        "rel_path",
        [
            "aws/compute/lambda.svg",
            "azure/compute/virtual-machines.svg",
            "gcp/compute/compute-engine.svg",
            "microsoft/fabric/data-warehouse.svg",
        ],
    )
    def test_raw_svg_all_vendors(self, tmp_icons_dir: Path, rel_path: str):
        path = tmp_icons_dir / rel_path
        content = raw_svg(path)
        assert "<svg" in content

    @pytest.mark.parametrize(
        "rel_path",
        [
            "aws/compute/lambda.svg",
            "azure/compute/virtual-machines.svg",
            "gcp/compute/compute-engine.svg",
            "microsoft/fabric/data-warehouse.svg",
        ],
    )
    def test_base64_all_vendors(self, tmp_icons_dir: Path, rel_path: str):
        path = tmp_icons_dir / rel_path
        encoded = base64_svg(path)
        decoded = base64.b64decode(encoded)
        assert b"<svg" in decoded
