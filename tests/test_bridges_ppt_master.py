"""Tests for tech_icons/bridges/ppt_master.py — ppt-master bridge integration."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from tech_icons.bridges.ppt_master import export_icons, export_vendor, get_ppt_master_reference

# The bridge imports icon_path via ``from tech_icons._paths import icon_path``,
# so we must patch the bridge module's own reference, not the _paths module.
_ICON_PATH_TARGET = "tech_icons.bridges.ppt_master.icon_path"


def _make_side_effect(mapping: dict[str, Path]):
    """Return a callable that resolves icon paths from a mapping."""

    def _resolve(relative: str) -> Path:
        rel_path = Path(relative)
        parts = list(rel_path.parts)
        if parts and parts[0] == "icons":
            parts = parts[1:]
        if parts and parts[-1].endswith(".svg"):
            parts[-1] = parts[-1][:-4]
        icon_id = "/".join(parts)
        path = mapping.get(icon_id)
        if path:
            return path
        return Path("/nonexistent/icon.svg")

    return _resolve


def _build_icon_mapping(icons_dir: Path) -> dict[str, Path]:
    """Build icon_id -> Path mapping from a directory of SVG files."""
    mapping: dict[str, Path] = {}
    for svg_file in icons_dir.rglob("*.svg"):
        rel = svg_file.relative_to(icons_dir)
        parts = list(rel.parts)
        if parts[-1].endswith(".svg"):
            parts[-1] = parts[-1][:-4]
        icon_id = "/".join(parts)
        mapping[icon_id] = svg_file
    return mapping


class TestExportIcons:
    """Test the export_icons function with corrected path layout."""

    def test_export_preserves_category_structure(self, tmp_path: Path, search_engine, tmp_icons_dir: Path):
        """Export should use tech-icons/vendor/category/name.svg layout."""
        target = tmp_path / "out"
        mapping = _build_icon_mapping(tmp_icons_dir)
        with patch(_ICON_PATH_TARGET, side_effect=_make_side_effect(mapping)):
            exported = export_icons(["aws/compute/lambda"], target, engine=search_engine)
        assert len(exported) == 1
        assert (target / "tech-icons" / "aws" / "compute" / "lambda.svg").exists()

    def test_export_creates_parent_dirs(self, tmp_path: Path, search_engine, tmp_icons_dir: Path):
        """Should create intermediate directories."""
        target = tmp_path / "nested" / "deep" / "icons"
        mapping = _build_icon_mapping(tmp_icons_dir)
        with patch(_ICON_PATH_TARGET, side_effect=_make_side_effect(mapping)):
            exported = export_icons(["aws/compute/lambda"], target, engine=search_engine)
        assert len(exported) == 1
        assert exported[0].exists()

    def test_export_skips_nonexistent_icons(self, tmp_path: Path, search_engine, tmp_icons_dir: Path):
        """Should warn and skip missing icons, not crash."""
        target = tmp_path / "out"
        mapping = _build_icon_mapping(tmp_icons_dir)
        with patch(_ICON_PATH_TARGET, side_effect=_make_side_effect(mapping)):
            exported = export_icons(["nonexistent/foo/bar", "aws/compute/lambda"], target, engine=search_engine)
        assert len(exported) == 1  # only the valid one

    def test_export_returns_paths(self, tmp_path: Path, search_engine, tmp_icons_dir: Path):
        """Returned values should be Path objects."""
        target = tmp_path / "out"
        mapping = _build_icon_mapping(tmp_icons_dir)
        with patch(_ICON_PATH_TARGET, side_effect=_make_side_effect(mapping)):
            exported = export_icons(["aws/compute/lambda"], target, engine=search_engine)
        assert all(isinstance(p, Path) for p in exported)

    def test_export_symlink_mode(self, tmp_path: Path, search_engine, tmp_icons_dir: Path):
        """Symlink mode should create symlinks."""
        target = tmp_path / "out"
        mapping = _build_icon_mapping(tmp_icons_dir)
        with patch(_ICON_PATH_TARGET, side_effect=_make_side_effect(mapping)):
            exported = export_icons(["aws/compute/lambda"], target, symlink=True, engine=search_engine)
        assert len(exported) == 1
        assert exported[0].is_symlink()


class TestExportVendor:
    """Test the export_vendor batch function."""

    def test_export_vendor_batch(self, tmp_path: Path, search_engine, tmp_icons_dir: Path):
        """Should export all icons for a vendor with correct layout."""
        target = tmp_path / "out"
        mapping = _build_icon_mapping(tmp_icons_dir)
        with patch(_ICON_PATH_TARGET, side_effect=_make_side_effect(mapping)):
            result = export_vendor("aws", target, engine=search_engine)
        # tmp_icons_dir has 2 AWS SVGs (lambda, ec2) → 2 of 4 sample entries succeed
        assert len(result) == 2
        for p in result:
            assert "tech-icons" in str(p)
            assert p.exists()

    def test_export_vendor_missing_svgs_skipped(self, tmp_path: Path, search_engine, tmp_icons_dir: Path):
        """Missing SVG files should be skipped gracefully."""
        target = tmp_path / "out"
        mapping = _build_icon_mapping(tmp_icons_dir)
        with patch(_ICON_PATH_TARGET, side_effect=_make_side_effect(mapping)):
            result = export_vendor("azure", target, engine=search_engine)
        # tmp_icons_dir has 1 azure SVG (virtual-machines.svg)
        assert len(result) == 1
        assert (target / "tech-icons" / "azure" / "compute" / "virtual-machines.svg").exists()


class TestGetPptMasterReference:
    """Test the deprecated get_ppt_master_reference function."""

    def test_reference_returns_canonical_format(self):
        """Should return tech-icons/{icon_id} format."""
        with pytest.deprecated_call():
            result = get_ppt_master_reference("aws/compute/lambda")
        assert result == "tech-icons/aws/compute/lambda"

    def test_reference_emits_deprecation_warning(self):
        """Should emit a DeprecationWarning."""
        with pytest.warns(DeprecationWarning, match="deprecated"):
            get_ppt_master_reference("aws/compute/lambda")
