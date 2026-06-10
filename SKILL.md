# tech-icons — Cloud Tech Icon Search

A skill providing searchable access to 3100+ cloud technology icons from AWS, Azure, GCP, and Microsoft via MCP tools. Returns icons in multiple formats suitable for presentations, architecture diagrams, and documentation.

## MCP Server

**Server name:** `tech-icons`  
**Transport:** stdio  
**Command:** `python3 src/server.py`

## Available Tools

### `search_icons`

Search the icon catalog by name, description, or ID. Supports exact match, keyword, fuzzy (typo-tolerant), and semantic search.

| Parameter  | Type   | Required | Description |
|-----------|--------|----------|-------------|
| query     | string | yes      | Search query (name, ID, or description) |
| vendor    | string | no       | Filter: `aws`, `azure`, `gcp`, `microsoft` |
| category  | string | no       | Filter: `compute`, `databases`, `networking`, etc. |
| limit     | integer| no       | Max results (default 10) |

### `get_icon`

Get full metadata for a specific icon by canonical ID.

| Parameter | Type   | Required | Description |
|----------|--------|----------|-------------|
| id       | string | yes      | Canonical icon ID (e.g., `aws/compute/lambda`) |

### `get_icon_svg`

Get icon SVG content in a specified output format.

| Parameter | Type   | Required | Description |
|----------|--------|----------|-------------|
| id       | string | yes      | Icon ID |
| format   | string | no       | Output format (default: `raw`) |

Format options: `raw`, `path`, `base64`, `data_uri`, `ppt_master`, `inline_group`

### `list_categories`

List all available icon categories, optionally filtered by vendor.

| Parameter | Type   | Required | Description |
|----------|--------|----------|-------------|
| vendor   | string | no       | Filter by vendor |

### `list_vendors`

List all vendors with their icon counts. No parameters.

## Format Options

| Format | Use Case | Output |
|--------|----------|--------|
| `raw` | Direct SVG embedding, inspection | Full SVG XML string |
| `path` | File references, local tooling | Absolute filesystem path |
| `base64` | Binary transport, embedding in JSON | Base64-encoded SVG |
| `data_uri` | HTML `<img>` tags, CSS backgrounds | `data:image/svg+xml;base64,...` |
| `ppt_master` | ppt-master skill integration | `<use data-icon="tech-icons/..." .../>` |
| `inline_group` | Architecture diagrams, direct SVG composition | `<g viewBox="...">...</g>` |

## Usage Examples

### Cross-vendor search
```
search_icons(query="serverless compute", limit=5)
→ Returns: aws/compute/lambda, azure/compute/function-apps, gcp/compute/cloud-run, ...
```

### Typo-tolerant search
```
search_icons(query="lamda")
→ Returns: aws/compute/lambda (fuzzy match)

search_icons(query="kubernets")
→ Returns: aws/containers/eks, azure/containers/aks, gcp/containers/gke, ...
```

### Category browsing
```
list_categories(vendor="aws")
→ ["analytics", "application-integration", "artificial-intelligence", "blockchain", "compute", "containers", "databases", ...]

search_icons(query="*", vendor="gcp", category="databases")
→ Returns all GCP database icons
```

### Get icon in specific format
```
get_icon_svg(id="aws/compute/lambda", format="data_uri")
→ "data:image/svg+xml;base64,PHN2ZyB4bWxucz0i..."

get_icon_svg(id="azure/compute/function-apps", format="ppt_master")
→ '<use data-icon="tech-icons/azure/compute/function-apps" xlink:href="icons/azure/compute/function-apps.svg"/>'
```

## Integration: ppt-master

Use `ppt_master` format to get placeholder elements compatible with the ppt-master skill's icon resolution:

```
get_icon_svg(id="aws/compute/lambda", format="ppt_master")
→ '<use data-icon="tech-icons/aws/compute/lambda" xlink:href="icons/aws/compute/lambda.svg"/>'
```

For bulk export into a ppt-master template directory:
```bash
python3 -m tech_icons.bridges.ppt_master --icons aws/compute/lambda,azure/compute/function-apps --target ./templates/icons/tech/
```

The bridge copies SVGs into the directory layout ppt-master expects: `{target}/tech/{vendor}/{name}.svg`

## Integration: architecture-diagram-generator

Use `inline_group` format to embed icons directly into SVG-based architecture diagrams:

```
get_icon_svg(id="aws/compute/lambda", format="inline_group")
→ '<g viewBox="0 0 64 64"><path d="..."/></g>'
```

Use `data_uri` format for HTML-based diagrams with `<img>` tags:

```
get_icon_svg(id="gcp/compute/cloud-run", format="data_uri")
→ "data:image/svg+xml;base64,..." (use in <img src="...">)
```

## Icon ID Format

All icons use canonical IDs: `{vendor}/{category}/{name}`

Examples:
- `aws/compute/lambda`
- `aws/databases/dynamodb`
- `azure/compute/function-apps`
- `azure/containers/aks`
- `gcp/compute/cloud-run`
- `gcp/databases/cloud-sql`
- `microsoft/365/teams`
- `microsoft/entra/entra-id`
