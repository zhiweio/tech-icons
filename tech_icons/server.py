"""MCP server exposing tech icons as searchable tools.

Transport: stdio (default), streamable HTTP (``--transport http``), or both
(``--transport dual``).
Server name: tech-icons

Tools:
  - search_icons: search the icon catalog
  - get_icon: get full icon details
  - list_categories: list available categories
  - list_vendors: list vendors with counts
  - get_icon_svg: return SVG in chosen format
  - list_concepts / compare_icons: cross-vendor concept lookup

Resources:
  - icon://catalog: full catalog metadata

Usage:
  tech-icons                         # stdio (default)
  tech-icons --transport http        # streamable HTTP on 127.0.0.1:8000
  tech-icons --transport dual        # stdio + HTTP simultaneously
  tech-icons --web                   # FastAPI web UI (browser)
  tech-icons --ppt-master aws        # icon export for ppt-master
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Annotated, Literal

from fastmcp import FastMCP
from fastmcp.utilities.types import Image

from tech_icons._paths import icon_path
from tech_icons.formats import IconNotFoundError, format_icon
from tech_icons.search import SearchEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

mcp = FastMCP("tech-icons")
engine = SearchEngine()

VENDOR_OPTIONS = Literal["aws", "azure", "gcp", "microsoft"]
FORMAT_OPTIONS = Literal["raw", "path", "base64", "data_uri", "ppt_master", "inline_group"]
TRANSPORT_OPTIONS = Literal["stdio", "http", "dual"]


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool
def search_icons(
    query: Annotated[str, "Search query (name, ID, or description)"],
    vendor: Annotated[VENDOR_OPTIONS | None, "Filter by vendor: aws, azure, gcp, microsoft"] = None,
    category: Annotated[str | None, "Filter by category (e.g., compute, databases)"] = None,
    limit: Annotated[int, "Max results to return (default 10)"] = 10,
) -> list[dict]:
    """Search cloud tech icons by query. Supports exact ID, keyword, fuzzy, and semantic matching."""
    results = engine.search(query, vendor=vendor, category=category, limit=limit)
    return [r.to_dict() for r in results]


@mcp.tool
def get_icon(
    id: Annotated[str, "Icon ID (e.g., aws/compute/lambda)"],  # noqa: A002
) -> dict:
    """Get full details for a specific icon by its canonical ID."""
    entry = engine.get_icon(id)
    if not entry:
        return {"error": f"Icon not found: {id}"}
    return entry


@mcp.tool
def list_categories(
    vendor: Annotated[VENDOR_OPTIONS | None, "Filter by vendor"] = None,
) -> list[str]:
    """List all available icon categories, optionally filtered by vendor."""
    return engine.list_categories(vendor=vendor)


@mcp.tool
def list_vendors() -> dict[str, int]:
    """List all vendors with their icon counts."""
    return engine.list_vendors()


@mcp.tool
def list_concepts() -> list[str]:
    """List all cross-vendor concept group names (e.g., kubernetes, serverless, object-storage).

    Use compare_icons to retrieve the icons in a group.
    """
    return engine.concepts.list_concepts()


@mcp.tool
def compare_icons(
    concept: Annotated[str, "Concept group name (e.g., kubernetes, serverless)"],
) -> dict:
    """Get all vendor icons for a concept (e.g., 'kubernetes' returns the K8s icon from AWS, Azure, and GCP).

    Use list_concepts first to discover names.
    """
    result = engine.compare_icons(concept)
    if result is None:
        return {"error": f"Concept not found: {concept}"}
    return result


@mcp.tool
def get_icon_svg(
    id: Annotated[str, "Icon ID (e.g., aws/compute/lambda)"],  # noqa: A002
    format: Annotated[  # noqa: A002
        FORMAT_OPTIONS | Literal["download"] | None,
        "Output format",
    ] = "raw",
) -> str | list[str | Image]:
    """Get icon SVG content in a specified format."""
    entry = engine.get_icon(id)
    if not entry:
        return json.dumps({"error": f"Icon not found: {id}"})

    path = icon_path(entry["path"])
    fmt = format or "raw"

    try:
        if fmt == "download":
            svg_bytes = path.read_bytes()
            size_kb = len(svg_bytes) / 1024
            return [
                f"Icon: {id} ({size_kb:.1f} KB SVG) — see attached image.",
                Image(data=svg_bytes, format="svg+xml"),
            ]
        return format_icon(path, id, fmt=fmt)
    except IconNotFoundError as e:
        return json.dumps({"error": str(e)})


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------


@mcp.resource("icon://catalog", mime_type="application/json")
def icon_catalog() -> str:
    """Full catalog of all tech icons with metadata."""
    return json.dumps(engine.catalog, indent=2)


# ---------------------------------------------------------------------------
# Transport runners
# ---------------------------------------------------------------------------


def _run_mcp_stdio() -> None:
    """Run MCP server over stdio (default, blocking)."""
    engine.load()
    logger.info(f"Catalog loaded: {len(engine.catalog)} icons ready")
    mcp.run()


def _run_mcp_http(host: str, port: int) -> None:
    """Run MCP server over Streamable HTTP (blocking)."""
    engine.load()
    logger.info(f"Catalog loaded: {len(engine.catalog)} icons ready")
    mcp.run(transport="http", host=host, port=port)


def _run_mcp_dual(host: str, port: int) -> None:
    """Run MCP server over both stdio and Streamable HTTP simultaneously."""
    engine.load()
    logger.info(f"Catalog loaded: {len(engine.catalog)} icons ready")
    logger.info(f"Starting dual transport: stdio + Streamable HTTP on {host}:{port}")

    async def _run_both() -> None:
        await asyncio.gather(
            mcp.run_stdio_async(),
            mcp.run_http_async(host=host, port=port),
        )

    asyncio.run(_run_both())


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def _run_web(host: str, port: int, open_browser: bool, log_level: str) -> None:
    try:
        import uvicorn

        from tech_icons.web.app import app
    except ImportError:
        sys.stderr.write(
            "Web UI requires the 'web' extra (fastapi + uvicorn).\n"
            "Install with: uvx --with 'tech-icons[web]' tech-icons --web\n"
        )
        sys.exit(1)

    if open_browser:
        import threading
        import webbrowser

        url = f"http://{host}:{port}"
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    uvicorn.run(app, host=host, port=port, log_level=log_level.lower())


def _run_ppt_master_export(icon_spec: str, target: Path, symlink: bool) -> None:
    """Export icons for ppt-master integration via the main CLI.

    Args:
        icon_spec: Comma-separated icon IDs, vendor name, or "all".
        target: Target directory (default: ./templates/icons/).
        symlink: Use symlinks instead of copies.
    """
    from tech_icons.bridges.ppt_master import export_icons, export_vendor

    export_engine = SearchEngine()
    export_engine.load()

    if icon_spec == "all":
        all_ids = [entry["id"] for entry in export_engine.catalog]
        logger.info(f"Exporting all {len(all_ids)} icons to {target}")
        export_icons(all_ids, target, symlink=symlink, engine=export_engine)
    elif icon_spec in ("aws", "azure", "gcp", "microsoft", "cncf", "devicon"):
        export_vendor(icon_spec, target, symlink=symlink, engine=export_engine)
    else:
        icon_ids = [x.strip() for x in icon_spec.split(",") if x.strip()]
        logger.info(f"Exporting {len(icon_ids)} icons to {target}")
        export_icons(icon_ids, target, symlink=symlink, engine=export_engine)


def _version() -> str:
    try:
        from importlib.metadata import version

        return version("tech-icons")
    except Exception:
        return "unknown"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="tech-icons",
        description=(
            "MCP server for 3100+ cloud tech icons "
            "(stdio by default; --transport http for Streamable HTTP; "
            "--transport dual for both)."
        ),
    )
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--web",
        action="store_true",
        help="Run the local HTTP web UI instead of the stdio MCP server.",
    )
    mode_group.add_argument(
        "--ppt-master",
        nargs="?",
        const="all",
        default=None,
        metavar="ICONS",
        help=(
            "Export icons for ppt-master. Provide comma-separated icon IDs (e.g. "
            "'aws/compute/lambda,azure/compute/function-apps'), a vendor name (aws|azure|"
            "gcp|microsoft|cncf|devicon), or omit for all icons. "
            "Use --target to set output dir (default: ./templates/icons/)."
        ),
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "http", "dual"],
        default="stdio",
        help=(
            "MCP transport protocol (default: stdio). "
            "'http' runs Streamable HTTP; 'dual' runs both stdio + HTTP. "
            "Ignored when --web or --ppt-master is set."
        ),
    )
    parser.add_argument("--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1).")
    parser.add_argument("--port", type=int, default=8765, help="Port for --web or --transport http (default: 8765).")
    parser.add_argument("--open", action="store_true", help="Open the web UI in the default browser on startup.")
    parser.add_argument("--log-level", default="info", help="Log level (default: info).")
    parser.add_argument("--version", action="version", version=f"tech-icons {_version()}")
    parser.add_argument(
        "--target",
        type=str,
        default="./templates/icons/",
        help="Target directory for ppt-master export (default: ./templates/icons/).",
    )
    parser.add_argument(
        "--symlink",
        action="store_true",
        help="Create symlinks instead of copies (ppt-master mode).",
    )

    args = parser.parse_args(argv)

    logging.getLogger().setLevel(args.log_level.upper())

    if args.ppt_master is not None:
        _run_ppt_master_export(icon_spec=args.ppt_master, target=Path(args.target), symlink=args.symlink)
    elif args.web:
        _run_web(host=args.host, port=args.port, open_browser=args.open, log_level=args.log_level)
    elif args.transport == "http":
        _run_mcp_http(host=args.host, port=args.port)
    elif args.transport == "dual":
        _run_mcp_dual(host=args.host, port=args.port)
    else:
        _run_mcp_stdio()


if __name__ == "__main__":
    main()
