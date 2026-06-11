"""Tests for src/formats.py — output format adapters for SVG and PNG."""

from __future__ import annotations

import base64
from pathlib import Path

import pytest

from tech_icons.formats import (
    IconNotFoundError,
    base64_icon,
    base64_svg,
    data_uri,
    format_icon,
    get_mime_type,
    inline_group,
    ppt_master_placeholder,
    raw_icon,
    raw_svg,
    resolve_image_path,
    svg_path,
)

# ---------------------------------------------------------------------------
# raw_icon / raw_svg
# ---------------------------------------------------------------------------


class TestRawIcon:
    """Tests for raw_icon (image-type-aware raw output)."""

    def test_raw_svg_returns_str(self, tmp_icons_dir: Path):
        path = tmp_icons_dir / "aws" / "compute" / "lambda.svg"
        content = raw_icon(path, "svg")
        assert isinstance(content, str)
        assert content.startswith("<svg")

    def test_raw_png_returns_bytes(self, tmp_icons_dir: Path):
        path = tmp_icons_dir / "aws" / "compute" / "lambda.png"
        content = raw_icon(path, "png")
        assert isinstance(content, bytes)
        assert content[:4] == b"\x89PNG"

    def test_raw_svg_legacy_alias(self, tmp_icons_dir: Path, sample_svg_content: str):
        """raw_svg alias works for backward compat."""
        path = tmp_icons_dir / "aws" / "compute" / "lambda.svg"
        content = raw_svg(path)
        assert content == sample_svg_content

    def test_raw_icon_missing_file_raises(self, tmp_path: Path):
        with pytest.raises(IconNotFoundError, match="not found"):
            raw_icon(tmp_path / "nonexistent.svg", "svg")


# ---------------------------------------------------------------------------
# svg_path
# ---------------------------------------------------------------------------


class TestIconPath:
    """Tests for svg_path format (format-agnostic)."""

    def test_path_returns_absolute(self, tmp_icons_dir: Path):
        path = tmp_icons_dir / "aws" / "compute" / "lambda.svg"
        result = svg_path(path)
        assert Path(result).is_absolute()
        assert result.endswith("lambda.svg")

    def test_path_for_png(self, tmp_icons_dir: Path):
        path = tmp_icons_dir / "aws" / "compute" / "lambda.png"
        result = svg_path(path)
        assert result.endswith("lambda.png")
        assert Path(result).exists()

    def test_path_missing_file_raises(self, tmp_path: Path):
        with pytest.raises(IconNotFoundError):
            svg_path(tmp_path / "ghost.svg")


# ---------------------------------------------------------------------------
# base64_icon / base64_svg
# ---------------------------------------------------------------------------


class TestBase64Icon:
    """Tests for base64_icon (image-type-aware base64 encoding)."""

    def test_base64_svg_valid_encoding(self, tmp_icons_dir: Path):
        path = tmp_icons_dir / "aws" / "compute" / "lambda.svg"
        encoded = base64_icon(path, "svg")
        decoded = base64.b64decode(encoded)
        assert b"<svg" in decoded

    def test_base64_png_valid_encoding(self, tmp_icons_dir: Path):
        path = tmp_icons_dir / "aws" / "compute" / "lambda.png"
        encoded = base64_icon(path, "png")
        decoded = base64.b64decode(encoded)
        assert decoded[:4] == b"\x89PNG"

    def test_base64_svg_roundtrip(self, tmp_icons_dir: Path, sample_svg_content: str):
        path = tmp_icons_dir / "aws" / "compute" / "lambda.svg"
        encoded = base64_icon(path, "svg")
        decoded = base64.b64decode(encoded).decode("utf-8")
        assert decoded == sample_svg_content

    def test_base64_ascii_only(self, tmp_icons_dir: Path):
        path = tmp_icons_dir / "aws" / "compute" / "lambda.svg"
        encoded = base64_icon(path, "svg")
        assert encoded.isascii()

    def test_base64_legacy_alias(self, tmp_icons_dir: Path):
        """base64_svg alias works."""
        path = tmp_icons_dir / "aws" / "compute" / "lambda.svg"
        encoded = base64_svg(path)
        decoded = base64.b64decode(encoded)
        assert b"<svg" in decoded

    def test_base64_missing_file_raises(self, tmp_path: Path):
        with pytest.raises(IconNotFoundError):
            base64_icon(tmp_path / "missing.svg", "svg")


# ---------------------------------------------------------------------------
# data_uri
# ---------------------------------------------------------------------------


class TestDataUri:
    """Tests for data_uri format (image-type-aware)."""

    def test_data_uri_svg_prefix(self, tmp_icons_dir: Path):
        path = tmp_icons_dir / "aws" / "compute" / "lambda.svg"
        result = data_uri(path, "svg")
        assert result.startswith("data:image/svg+xml;base64,")

    def test_data_uri_png_prefix(self, tmp_icons_dir: Path):
        path = tmp_icons_dir / "aws" / "compute" / "lambda.png"
        result = data_uri(path, "png")
        assert result.startswith("data:image/png;base64,")

    def test_data_uri_svg_contains_valid_base64(self, tmp_icons_dir: Path):
        path = tmp_icons_dir / "aws" / "compute" / "lambda.svg"
        result = data_uri(path, "svg")
        _, encoded_part = result.split(",", 1)
        decoded = base64.b64decode(encoded_part)
        assert b"<svg" in decoded

    def test_data_uri_missing_file_raises(self, tmp_path: Path):
        with pytest.raises(IconNotFoundError):
            data_uri(tmp_path / "nope.svg", "svg")


# ---------------------------------------------------------------------------
# ppt_master_placeholder
# ---------------------------------------------------------------------------


class TestPptMasterPlaceholder:
    """Tests for ppt_master_placeholder format."""

    def test_ppt_master_correct_xml(self):
        result = ppt_master_placeholder("aws/compute/lambda")
        assert 'data-icon="tech-icons/aws/compute/lambda"' in result
        assert result.startswith("<use")
        assert result.endswith("/>")

    @pytest.mark.parametrize(
        "icon_id",
        [
            "aws/compute/lambda",
            "azure/networking/load-balancer",
            "gcp/databases/cloud-sql",
            "microsoft/fabric/data-warehouse",
            "alibabacloud/general/alibabacloud",  # PNG-only icon
        ],
    )
    def test_ppt_master_all_vendors(self, icon_id: str):
        result = ppt_master_placeholder(icon_id)
        assert f"tech-icons/{icon_id}" in result
        assert "xlink:href" not in result


# ---------------------------------------------------------------------------
# inline_group
# ---------------------------------------------------------------------------


class TestInlineGroup:
    """Tests for inline_group format (SVG only)."""

    def test_inline_group_wraps_in_g_tag(self, tmp_icons_dir: Path):
        path = tmp_icons_dir / "aws" / "compute" / "lambda.svg"
        result = inline_group(path, "svg")
        assert result.startswith("<g")
        assert result.endswith("</g>")

    def test_inline_group_preserves_viewbox(self, tmp_icons_dir: Path):
        path = tmp_icons_dir / "aws" / "compute" / "lambda.svg"
        result = inline_group(path, "svg")
        assert 'viewBox="0 0 48 48"' in result

    def test_inline_group_strips_svg_wrapper(self, tmp_icons_dir: Path):
        path = tmp_icons_dir / "aws" / "compute" / "lambda.svg"
        result = inline_group(path, "svg")
        assert "<svg" not in result
        assert "</svg>" not in result

    def test_inline_group_png_raises(self, tmp_icons_dir: Path):
        path = tmp_icons_dir / "aws" / "compute" / "lambda.png"
        with pytest.raises(ValueError, match="only available for SVG"):
            inline_group(path, "png")

    def test_inline_group_default_svg(self, tmp_icons_dir: Path):
        """Default image_type is 'svg'."""
        path = tmp_icons_dir / "aws" / "compute" / "lambda.svg"
        result = inline_group(path)
        assert result.startswith("<g")

    def test_inline_group_invalid_svg_raises(self, tmp_path: Path):
        bad_file = tmp_path / "bad.svg"
        bad_file.write_text("not an svg at all")
        with pytest.raises(IconNotFoundError, match="Invalid SVG"):
            inline_group(bad_file, "svg")

    def test_inline_group_missing_file_raises(self, tmp_path: Path):
        with pytest.raises(IconNotFoundError):
            inline_group(tmp_path / "gone.svg", "svg")


# ---------------------------------------------------------------------------
# get_mime_type
# ---------------------------------------------------------------------------


class TestGetMimeType:
    """Tests for get_mime_type helper."""

    def test_svg_mime(self):
        assert get_mime_type("svg") == "image/svg+xml"

    def test_png_mime(self):
        assert get_mime_type("png") == "image/png"

    def test_unknown_mime(self):
        assert get_mime_type("jpeg") == "application/octet-stream"


# ---------------------------------------------------------------------------
# resolve_image_path
# ---------------------------------------------------------------------------


class TestResolveImagePath:
    """Tests for resolve_image_path fallback logic."""

    def test_svg_both_available(self):
        formats = {"svg": "icons/a.svg", "png": "icons/a.png"}
        actual_type, path_str = resolve_image_path(formats, "svg")
        assert actual_type == "svg"
        assert path_str == "icons/a.svg"

    def test_png_both_available(self):
        formats = {"svg": "icons/a.svg", "png": "icons/a.png"}
        actual_type, path_str = resolve_image_path(formats, "png")
        assert actual_type == "png"
        assert path_str == "icons/a.png"

    def test_svg_fallback_to_png(self):
        """When 'svg' requested but only PNG exists, fall back to PNG."""
        formats = {"png": "icons/a.png"}
        actual_type, path_str = resolve_image_path(formats, "svg")
        assert actual_type == "png"
        assert path_str == "icons/a.png"

    def test_png_fallback_to_svg(self):
        """When 'png' requested but only SVG exists, fall back to SVG."""
        formats = {"svg": "icons/a.svg"}
        actual_type, path_str = resolve_image_path(formats, "png")
        assert actual_type == "svg"
        assert path_str == "icons/a.svg"

    def test_prefers_svg_on_unknown_type(self):
        formats = {"svg": "icons/a.svg", "png": "icons/a.png"}
        actual_type, _ = resolve_image_path(formats, "jpg")
        assert actual_type == "svg"


# ---------------------------------------------------------------------------
# format_icon dispatcher
# ---------------------------------------------------------------------------


class TestFormatIconDispatcher:
    """Tests for format_icon routing with image_type parameter."""

    @pytest.mark.parametrize("fmt", ["raw", "path", "base64", "data_uri", "inline_group"])
    def test_dispatcher_routes_svg_correctly(self, tmp_icons_dir: Path, fmt: str):
        path = tmp_icons_dir / "aws" / "compute" / "lambda.svg"
        result = format_icon(path, "aws/compute/lambda", fmt=fmt, image_type="svg")
        assert isinstance(result, (str, bytes))
        if isinstance(result, bytes):
            assert len(result) > 0
        else:
            assert len(result) > 0

    @pytest.mark.parametrize("fmt", ["raw", "path", "base64", "data_uri"])
    def test_dispatcher_routes_png_correctly(self, tmp_icons_dir: Path, fmt: str):
        path = tmp_icons_dir / "aws" / "compute" / "lambda.png"
        result = format_icon(path, "aws/compute/lambda", fmt=fmt, image_type="png")
        if fmt == "path":
            assert isinstance(result, str)
        elif fmt == "raw":
            assert isinstance(result, bytes)
            assert result[:4] == b"\x89PNG"
        else:
            assert isinstance(result, str)
            assert len(result) > 0

    def test_dispatcher_ppt_master(self, tmp_icons_dir: Path):
        path = tmp_icons_dir / "aws" / "compute" / "lambda.svg"
        result = format_icon(path, "aws/compute/lambda", fmt="ppt_master")
        assert "tech-icons/aws/compute/lambda" in result

    def test_dispatcher_default_is_svg_raw(self, tmp_icons_dir: Path, sample_svg_content: str):
        path = tmp_icons_dir / "aws" / "compute" / "lambda.svg"
        result = format_icon(path, "aws/compute/lambda")
        assert result == sample_svg_content

    def test_dispatcher_png_default_to_svg(self, tmp_icons_dir: Path):
        """When image_type not specified, defaults to svg."""
        path = tmp_icons_dir / "aws" / "compute" / "lambda.svg"
        result = format_icon(path, "aws/compute/lambda", fmt="raw")
        assert isinstance(result, str)

    def test_dispatcher_inline_group_png_raises(self, tmp_icons_dir: Path):
        path = tmp_icons_dir / "aws" / "compute" / "lambda.png"
        with pytest.raises(ValueError, match="only available for SVG"):
            format_icon(path, "aws/compute/lambda", fmt="inline_group", image_type="png")

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
        "rel_path,image_type",
        [
            ("aws/compute/lambda.svg", "svg"),
            ("azure/compute/virtual-machines.svg", "svg"),
            ("gcp/compute/compute-engine.svg", "svg"),
            ("microsoft/fabric/data-warehouse.svg", "svg"),
            ("aws/compute/lambda.png", "png"),
            ("alibabacloud/general/alibabacloud.png", "png"),
        ],
    )
    def test_raw_all_vendors(self, tmp_icons_dir: Path, rel_path: str, image_type: str):
        path = tmp_icons_dir / rel_path
        content = raw_icon(path, image_type)
        if image_type == "svg":
            assert "<svg" in content
        else:
            assert isinstance(content, bytes)

    @pytest.mark.parametrize(
        "rel_path,image_type",
        [
            ("aws/compute/lambda.svg", "svg"),
            ("azure/compute/virtual-machines.svg", "svg"),
            ("gcp/compute/compute-engine.svg", "svg"),
            ("aws/compute/lambda.png", "png"),
        ],
    )
    def test_base64_all_vendors(self, tmp_icons_dir: Path, rel_path: str, image_type: str):
        path = tmp_icons_dir / rel_path
        encoded = base64_icon(path, image_type)
        decoded = base64.b64decode(encoded)
        if image_type == "svg":
            assert b"<svg" in decoded
        else:
            assert decoded[:4] == b"\x89PNG"
