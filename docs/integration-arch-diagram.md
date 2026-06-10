# Architecture Diagram Integration

Guide for embedding tech-icons into HTML/SVG architecture diagrams.

## Using `data_uri` Format (HTML `<img>` Tags)

Best for HTML-based diagrams where icons are positioned with CSS.

```html
<div class="arch-diagram">
  <div class="node" style="left: 100px; top: 50px;">
    <img class="tech-icon tech-icon--md" src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0i..." alt="AWS Lambda" />
    <span class="node-label">Lambda</span>
  </div>
  <div class="node" style="left: 300px; top: 50px;">
    <img class="tech-icon tech-icon--md" src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0i..." alt="DynamoDB" />
    <span class="node-label">DynamoDB</span>
  </div>
</div>
```

## Using `inline_group` Format (Direct SVG Embedding)

Best for pure SVG diagrams where icons are composed directly into the SVG canvas.

```html
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400" class="arch-diagram-svg">
  <!-- AWS Lambda icon at position (50, 50), scaled to 48x48 -->
  <g transform="translate(50, 50) scale(0.75)">
    <g viewBox="0 0 64 64"><path d="...lambda paths..."/></g>
  </g>

  <!-- Azure Function Apps at position (250, 50) -->
  <g transform="translate(250, 50) scale(0.75)">
    <g viewBox="0 0 64 64"><path d="...function-apps paths..."/></g>
  </g>

  <!-- Connection arrow -->
  <line x1="98" y1="74" x2="250" y2="74" stroke="#333" stroke-width="2" marker-end="url(#arrow)"/>

  <!-- Labels -->
  <text x="74" y="115" text-anchor="middle" class="icon-label">Lambda</text>
  <text x="274" y="115" text-anchor="middle" class="icon-label">Function Apps</text>
</svg>
```

## CSS Class Conventions

```css
/* Icon sizing */
.tech-icon--xs { width: 24px; height: 24px; }
.tech-icon--sm { width: 32px; height: 32px; }
.tech-icon--md { width: 48px; height: 48px; }
.tech-icon--lg { width: 64px; height: 64px; }
.tech-icon--xl { width: 96px; height: 96px; }

/* Vendor color accents (for borders/backgrounds) */
.tech-icon-vendor--aws { border-color: #FF9900; }
.tech-icon-vendor--azure { border-color: #0078D4; }
.tech-icon-vendor--gcp { border-color: #4285F4; }
.tech-icon-vendor--microsoft { border-color: #737373; }

/* Node container styling */
.node {
  position: absolute;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.node-label {
  font-size: 12px;
  font-family: system-ui, sans-serif;
  text-align: center;
}

/* SVG label styling */
.icon-label {
  font-size: 11px;
  font-family: system-ui, sans-serif;
  fill: #333;
}
```

## Sample: Multi-Cloud Architecture Diagram

```html
<!DOCTYPE html>
<html>
<head>
<style>
  .arch-canvas { position: relative; width: 800px; height: 400px; border: 1px solid #e0e0e0; border-radius: 8px; }
  .cloud-region { position: absolute; border: 2px dashed; border-radius: 12px; padding: 16px; }
  .cloud-region--aws { border-color: #FF9900; background: rgba(255, 153, 0, 0.03); }
  .cloud-region--azure { border-color: #0078D4; background: rgba(0, 120, 212, 0.03); }
  .cloud-region--gcp { border-color: #4285F4; background: rgba(66, 133, 244, 0.03); }
  .region-label { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
  .region-label--aws { color: #FF9900; }
  .region-label--azure { color: #0078D4; }
  .region-label--gcp { color: #4285F4; }
  .node { display: inline-flex; flex-direction: column; align-items: center; gap: 4px; margin: 8px 16px; }
  .node img { width: 48px; height: 48px; }
  .node-label { font-size: 11px; color: #444; }
</style>
</head>
<body>
<div class="arch-canvas">
  <!-- AWS Region -->
  <div class="cloud-region cloud-region--aws" style="left: 20px; top: 20px; width: 220px; height: 340px;">
    <span class="region-label region-label--aws">AWS</span>
    <div class="node">
      <img src="DATA_URI_FOR_aws/compute/lambda" alt="Lambda" />
      <span class="node-label">Lambda</span>
    </div>
    <div class="node">
      <img src="DATA_URI_FOR_aws/databases/dynamodb" alt="DynamoDB" />
      <span class="node-label">DynamoDB</span>
    </div>
    <div class="node">
      <img src="DATA_URI_FOR_aws/networking/api-gateway" alt="API Gateway" />
      <span class="node-label">API Gateway</span>
    </div>
  </div>

  <!-- Azure Region -->
  <div class="cloud-region cloud-region--azure" style="left: 280px; top: 20px; width: 220px; height: 340px;">
    <span class="region-label region-label--azure">Azure</span>
    <div class="node">
      <img src="DATA_URI_FOR_azure/compute/function-apps" alt="Functions" />
      <span class="node-label">Functions</span>
    </div>
    <div class="node">
      <img src="DATA_URI_FOR_azure/databases/cosmos-db" alt="Cosmos DB" />
      <span class="node-label">Cosmos DB</span>
    </div>
  </div>

  <!-- GCP Region -->
  <div class="cloud-region cloud-region--gcp" style="left: 540px; top: 20px; width: 220px; height: 340px;">
    <span class="region-label region-label--gcp">GCP</span>
    <div class="node">
      <img src="DATA_URI_FOR_gcp/compute/cloud-run" alt="Cloud Run" />
      <span class="node-label">Cloud Run</span>
    </div>
    <div class="node">
      <img src="DATA_URI_FOR_gcp/databases/cloud-sql" alt="Cloud SQL" />
      <span class="node-label">Cloud SQL</span>
    </div>
  </div>
</div>
</body>
</html>
```

Replace `DATA_URI_FOR_{id}` with the output of `get_icon_svg(id="{id}", format="data_uri")`.

## Workflow

1. Use `search_icons` to find icons by name or category
2. Use `get_icon_svg` with `format="data_uri"` for HTML diagrams or `format="inline_group"` for SVG composition
3. Apply CSS classes for consistent sizing
4. Wrap vendor-specific groups in styled containers
