# tech-icons

MCP server exposing 2200+ cloud technology icons (AWS, Azure, GCP, Microsoft) as searchable tools. Features 3-tier search (exact → keyword → fuzzy → semantic), multiple output formats, and integrations with ppt-master and architecture diagram generators.

| Vendor | Icons | Source |
|--------|-------|--------|
| AWS | 767 | Architecture-Service, Category, Resource, Group Icons (48px) |
| Azure | 705 | Azure Public Service Icons |
| GCP | 45 | Category Icons + Core Product Icons |
| Microsoft | 772 | Fabric, M365, Dynamics 365, Entra, Power Platform |
| **Total** | **2,289** | Deduplicated from 5,190 raw SVGs |

## Quick Start

```bash
# Install dependencies
uv sync

# Build the icon catalog (scans assets/, generates catalog/)
uv run python scripts/build_catalog.py

# Run the MCP server (stdio transport)
uv run python src/server.py
```

### MCP Configuration

Add to your `.mcp.json` or MCP client config:

```json
{
  "mcpServers": {
    "tech-icons": {
      "command": "python3",
      "args": ["src/server.py"],
      "env": {}
    }
  }
}
```

## Architecture

```
assets/            → Raw vendor icon packages (SVG)
    ↓
scripts/normalize_icons.py → Normalize filenames, deduplicate
    ↓
scripts/build_catalog.py   → Generate metadata, keyword index, embeddings
    ↓
catalog/
  icons.json           → Full icon metadata (2289 entries)
  keyword_index.json   → Inverted index for keyword search
  embeddings.npz       → Sentence-transformer embeddings (optional)
    ↓
src/search.py          → Multi-tier search engine
src/formats.py         → Output format adapters
src/server.py          → MCP server (stdio)
```

## Available Tools

| Tool | Description |
|------|-------------|
| `search_icons` | Search icons by query with optional vendor/category filters |
| `get_icon` | Get full metadata for an icon by canonical ID |
| `get_icon_svg` | Get icon SVG content in a specified format |
| `list_categories` | List available categories (optionally per vendor) |
| `list_vendors` | List vendors with icon counts |

## Format Options

| Format | Output | Use Case |
|--------|--------|----------|
| `raw` | SVG XML string | Inspection, direct embedding |
| `path` | Absolute file path | Local tooling, file references |
| `base64` | Base64-encoded SVG | Binary transport, JSON payloads |
| `data_uri` | `data:image/svg+xml;base64,...` | HTML `<img>` tags, CSS |
| `ppt_master` | `<use data-icon="..."/>` | ppt-master skill integration |
| `inline_group` | `<g viewBox="...">...</g>` | SVG composition, arch diagrams |

## Icon IDs

Canonical format: `{vendor}/{category}/{name}`

Examples: `aws/compute/lambda`, `azure/databases/cosmos-db`, `gcp/containers/gke`, `microsoft/365/teams`

## Integrations

**ppt-master:** Use `format="ppt_master"` or the bridge script to export icons into ppt-master template directories.

```bash
python3 -m src.bridges.ppt_master --icons aws/compute/lambda,gcp/compute/cloud-run --target ./templates/icons/tech/
```

**Architecture diagrams:** Use `format="data_uri"` for HTML img tags or `format="inline_group"` for direct SVG composition. See [docs/integration-arch-diagram.md](docs/integration-arch-diagram.md).

## Development

Requires [uv](https://docs.astral.sh/uv/) for dependency management.

```bash
# Install with dev dependencies
uv sync --group dev

# Format code
make format

# Lint
make lint

# Type check
make typecheck

# All checks (lint + typecheck)
make check

# Run tests
make test

# Format + lint + typecheck + test
make all
```

Other useful commands:

```bash
# Build catalog for a single vendor
make build-catalog           # full build
uv run python scripts/build_catalog.py --vendor aws
uv run python scripts/build_catalog.py --skip-embeddings

# Start MCP server
make serve
```

### Tooling

- **Formatter/Linter:** [ruff](https://docs.astral.sh/ruff/) (line-length: 120)
- **Type checker:** [mypy](https://mypy-lang.org/) (disallow-untyped-defs)
- **Tests:** [pytest](https://pytest.org/) + pytest-asyncio
