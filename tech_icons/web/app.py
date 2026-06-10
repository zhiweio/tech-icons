"""FastAPI HTTP wrapper around SearchEngine + ConceptRegistry.

Exposes the same capabilities as the MCP server over HTTP for a browser-based
icon browser. The SearchEngine instance is shared — no logic duplication.

Run: uv run uvicorn tech_icons.web.app:app --reload --port 8765
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from tech_icons._paths import icon_path
from tech_icons.formats import IconNotFoundError, format_icon
from tech_icons.search import SearchEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).resolve().parent / "static"

VALID_FORMATS = {"raw", "path", "base64", "data_uri", "ppt_master", "inline_group", "download"}

engine = SearchEngine()


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    logger.info("Loading search engine and concept registry...")
    engine.load()
    logger.info(f"Ready: {len(engine.catalog)} icons, {len(engine.concepts.all_groups)} concept groups")
    yield


app = FastAPI(
    title="tech-icons",
    description="HTTP API for browsing 3100+ cloud tech icons",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    return {
        "status": "ok",
        "icons": len(engine.catalog),
        "concepts": len(engine.concepts.all_groups),
    }


@app.get("/api/vendors")
def list_vendors() -> dict[str, int]:
    return engine.list_vendors()


@app.get("/api/categories")
def list_categories(vendor: str | None = Query(default=None)) -> list[str]:
    return engine.list_categories(vendor=vendor)


@app.get("/api/search")
def search(
    q: str = Query(..., description="Search query"),
    vendor: str | None = Query(default=None),
    category: str | None = Query(default=None),
    limit: int = Query(default=24, ge=1, le=200),
) -> list[dict]:
    results = engine.search(q, vendor=vendor, category=category, limit=limit)
    return [r.to_dict() for r in results]


@app.get("/api/icons")
def list_icons(
    vendor: str | None = Query(default=None),
    category: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=5000),
    offset: int = Query(default=0, ge=0),
) -> dict:
    """Paginated catalog browsing (no query needed)."""
    items = engine.catalog
    if vendor:
        items = [e for e in items if e.get("vendor") == vendor]
    if category:
        items = [e for e in items if e.get("category") == category]
    total = len(items)
    window = items[offset : offset + limit]
    return {"total": total, "offset": offset, "limit": limit, "items": window}


@app.get("/api/svg/{icon_id:path}")
def get_icon_svg(
    icon_id: str,
    format: str = Query(default="raw"),  # noqa: A002 - HTTP query name
    download: bool = Query(default=False),
) -> Response:
    if format not in VALID_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid format. Must be one of: {sorted(VALID_FORMATS)}",
        )
    entry = engine.get_icon(icon_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Icon not found: {icon_id}")

    path = icon_path(entry["path"])
    try:
        # Map "download" format to raw SVG content served as attachment
        output_fmt = "raw" if format == "download" else format
        content = format_icon(path, icon_id, fmt=output_fmt)
    except IconNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    media_type = "image/svg+xml" if format in ("raw", "download") else "text/plain"

    if download or format == "download":
        filename = entry.get("filename") or f"{icon_id.rsplit('/', 1)[-1]}.svg"
        headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
        return Response(content=content, media_type=media_type, headers=headers)

    return Response(content=content, media_type=media_type)


@app.get("/api/icons/{icon_id:path}")
def get_icon(icon_id: str) -> dict:
    entry = engine.get_icon(icon_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Icon not found: {icon_id}")
    related = engine.concepts.get_concepts_for_icon(icon_id)
    return {**entry, "related_concepts": related}


@app.get("/api/concepts")
def list_concepts() -> list[dict]:
    """List all concept groups with vendor coverage."""
    return [g.to_dict() for g in engine.concepts.all_groups.values()]


@app.get("/api/concepts/{name}")
def get_concept(name: str) -> dict:
    result = engine.compare_icons(name)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Concept not found: {name}")
    return result


# --- Static SPA ---

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")
else:

    @app.get("/")
    def _no_static() -> JSONResponse:
        return JSONResponse({"error": f"Static dir not found: {STATIC_DIR}"}, status_code=500)
