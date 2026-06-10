"""MCP server exposing tech icons as searchable tools.

Transport: stdio (default) or local HTTP web UI (``--web`` flag).
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
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Resource, TextContent, Tool

from tech_icons._paths import icon_path
from tech_icons.formats import IconNotFoundError, format_icon
from tech_icons.search import SearchEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

server = Server("tech-icons")
engine = SearchEngine()


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="search_icons",
            description="Search cloud tech icons by query. Supports exact ID, keyword, fuzzy, and semantic matching.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (name, ID, or description)",
                    },
                    "vendor": {
                        "type": "string",
                        "description": "Filter by vendor: aws, azure, gcp, microsoft",
                        "enum": ["aws", "azure", "gcp", "microsoft"],
                    },
                    "category": {
                        "type": "string",
                        "description": "Filter by category (e.g., compute, databases)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max results to return (default 10)",
                        "default": 10,
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="get_icon",
            description="Get full details for a specific icon by its canonical ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {"type": "string", "description": "Icon ID (e.g., aws/compute/lambda)"},
                },
                "required": ["id"],
            },
        ),
        Tool(
            name="list_categories",
            description="List all available icon categories, optionally filtered by vendor.",
            inputSchema={
                "type": "object",
                "properties": {
                    "vendor": {
                        "type": "string",
                        "description": "Filter by vendor",
                        "enum": ["aws", "azure", "gcp", "microsoft"],
                    },
                },
            },
        ),
        Tool(
            name="list_vendors",
            description="List all vendors with their icon counts.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="get_icon_svg",
            description="Get icon SVG content in a specified format.",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {"type": "string", "description": "Icon ID (e.g., aws/compute/lambda)"},
                    "format": {
                        "type": "string",
                        "description": "Output format",
                        "enum": ["raw", "path", "base64", "data_uri", "ppt_master", "inline_group"],
                        "default": "raw",
                    },
                },
                "required": ["id"],
            },
        ),
        Tool(
            name="list_concepts",
            description=(
                "List all cross-vendor concept group names (e.g., kubernetes, serverless, "
                "object-storage). Use compare_icons to retrieve the icons in a group."
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="compare_icons",
            description=(
                "Get all vendor icons for a concept (e.g., 'kubernetes' returns the K8s "
                "icon from AWS, Azure, and GCP). Use list_concepts first to discover names."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "concept": {
                        "type": "string",
                        "description": "Concept group name (e.g., kubernetes, serverless)",
                    },
                },
                "required": ["concept"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        if name == "search_icons":
            return _handle_search(arguments)
        elif name == "get_icon":
            return _handle_get_icon(arguments)
        elif name == "list_categories":
            return _handle_list_categories(arguments)
        elif name == "list_vendors":
            return _handle_list_vendors()
        elif name == "get_icon_svg":
            return _handle_get_icon_svg(arguments)
        elif name == "list_concepts":
            return _handle_list_concepts()
        elif name == "compare_icons":
            return _handle_compare_icons(arguments)
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    except Exception as e:
        logger.exception(f"Error in tool {name}")
        return [TextContent(type="text", text=f"Error: {e}")]


def _handle_search(arguments: dict) -> list[TextContent]:
    query = arguments["query"]
    vendor = arguments.get("vendor")
    category = arguments.get("category")
    limit = arguments.get("limit", 10)

    results = engine.search(query, vendor=vendor, category=category, limit=limit)
    output = [r.to_dict() for r in results]
    return [TextContent(type="text", text=json.dumps(output, indent=2))]


def _handle_get_icon(arguments: dict) -> list[TextContent]:
    icon_id = arguments["id"]
    entry = engine.get_icon(icon_id)

    if not entry:
        return [TextContent(type="text", text=json.dumps({"error": f"Icon not found: {icon_id}"}))]

    return [TextContent(type="text", text=json.dumps(entry, indent=2))]


def _handle_list_categories(arguments: dict) -> list[TextContent]:
    vendor = arguments.get("vendor")
    categories = engine.list_categories(vendor=vendor)
    return [TextContent(type="text", text=json.dumps(categories, indent=2))]


def _handle_list_vendors() -> list[TextContent]:
    vendors = engine.list_vendors()
    return [TextContent(type="text", text=json.dumps(vendors, indent=2))]


def _handle_get_icon_svg(arguments: dict) -> list[TextContent]:
    icon_id = arguments["id"]
    fmt = arguments.get("format", "raw")

    entry = engine.get_icon(icon_id)
    if not entry:
        return [TextContent(type="text", text=json.dumps({"error": f"Icon not found: {icon_id}"}))]

    path = icon_path(entry["path"])

    try:
        content = format_icon(path, icon_id, fmt=fmt)
        return [TextContent(type="text", text=content)]
    except IconNotFoundError as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


def _handle_list_concepts() -> list[TextContent]:
    names = engine.concepts.list_concepts()
    return [TextContent(type="text", text=json.dumps(names, indent=2))]


def _handle_compare_icons(arguments: dict) -> list[TextContent]:
    concept = arguments["concept"]
    result = engine.compare_icons(concept)
    if result is None:
        return [
            TextContent(
                type="text",
                text=json.dumps({"error": f"Concept not found: {concept}"}),
            )
        ]
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


@server.list_resources()
async def list_resources() -> list[Resource]:
    return [
        Resource(
            uri="icon://catalog",  # type: ignore[arg-type]
            name="Icon Catalog",
            description="Full catalog of all tech icons with metadata",
            mimeType="application/json",
        ),
    ]


@server.read_resource()
async def read_resource(uri: str) -> str:
    if str(uri) == "icon://catalog":
        return json.dumps(engine.catalog, indent=2)
    raise ValueError(f"Unknown resource: {uri}")


async def _run_stdio() -> None:
    logger.info("Starting tech-icons MCP server (stdio)...")
    engine.load()
    logger.info("Catalog loaded, server ready")

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


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


def _version() -> str:
    try:
        from importlib.metadata import version

        return version("tech-icons")
    except Exception:
        return "unknown"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="tech-icons",
        description="MCP server for 3100+ cloud tech icons (stdio by default; --web for browser UI).",
    )
    parser.add_argument("--web", action="store_true", help="Run the local HTTP web UI instead of the stdio MCP server.")
    parser.add_argument("--host", default="127.0.0.1", help="Web UI bind host (default: 127.0.0.1).")
    parser.add_argument("--port", type=int, default=8765, help="Web UI bind port (default: 8765).")
    parser.add_argument("--open", action="store_true", help="Open the web UI in the default browser on startup.")
    parser.add_argument("--log-level", default="info", help="Log level (default: info).")
    parser.add_argument("--version", action="version", version=f"tech-icons {_version()}")

    args = parser.parse_args(argv)

    logging.getLogger().setLevel(args.log_level.upper())

    if args.web:
        _run_web(host=args.host, port=args.port, open_browser=args.open, log_level=args.log_level)
    else:
        asyncio.run(_run_stdio())


if __name__ == "__main__":
    main()
