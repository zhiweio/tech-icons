# CLAUDE.md — tech-icons

## Project Commands

Always use `uv run` to execute Python commands within this project:

```bash
# Run tests
uv run pytest tests/ -v

# Run the MCP server (stdio)
uv run tech-icons

# Run the web UI
uv run tech-icons --web

# Export icons for ppt-master
uv run tech-icons --ppt-master aws --target ./templates/icons/
```

## Development Rules

1. **Always use `uv run`** — every Python command goes through `uv run` (e.g. `uv run pytest`, `uv run tech-icons --web`). Never invoke `python` or `python3` directly.

2. **Update docs after every change** — after completing a feature, bug fix, refactor, or any development task, update the corresponding documentation files if they exist:
   - `README.md` — project overview
   - If no relevant doc file exists, skip; don't create docs unless asked.

## Architecture

- **Package**: `tech_icons` (MCP server + FastAPI web UI for 3100+ cloud tech icons)
- **Entry point**: `tech-icons` → `tech_icons.server:main`
- **Build system**: hatchling (pyproject.toml)
- **Python**: >=3.10
- **Key deps**: mcp, pyyaml, rapidfuzz; optional: fastapi+uvicorn (web), sentence-transformers+numpy (semantic)
