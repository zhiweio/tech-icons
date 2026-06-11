<!-- markdownlint-disable MD033 MD041 -->
<!-- mcp-name: tech-icons -->
# tech-icons

[English](./README.md) | **中文**

<p align="center">
  <img src="./docs/images/brand-logo.jpg" alt="tech-icons" width="150 onerror="this.style.display='none'">
</p>

<p align="center">
  <strong>3,100+ 技术图标 · MCP 搜索服务 · 架构图</strong>
</p>

<p align="center">
  <a href="https://pypi.org/project/tech-icons/"><img src="https://img.shields.io/pypi/v/tech-icons?color=blue" alt="PyPI"></a>
  <a href="https://github.com/zhiweio/tech-icons/blob/master/LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="License"></a>
  <a href="https://pypi.org/project/tech-icons/"><img src="https://img.shields.io/pypi/pyversions/tech-icons" alt="Python"></a>
  <a href="https://modelcontextprotocol.io"><img src="https://img.shields.io/badge/MCP-Server-orange" alt="MCP"></a>
  <a href="https://fastmcp.org"><img src="https://img.shields.io/badge/FastMCP-3.4-blue" alt="FastMCP"></a>
</p>

<p align="center">
  <img src="docs/images/banner.png" alt="tech-icons" />
</p>

面向 AI 辅助架构图绘制的图标层。让 LLM 能够*看到*并*放置* AWS、Azure、GCP、Microsoft 的云服务图标——无需切换标签页或在各厂商文档中翻找。

## ✨ 功能特性

- 🔍 **多级搜索** — 精确 ID → 关键词 → 模糊 → 语义嵌入搜索，逐级递进，兼顾精度和召回
- 🎨 **7 种输出格式** — Raw SVG、Base64、Data URI、行内 `<g>`、文件路径、ppt-master 占位符、下载——按需选用
- 🔗 **跨厂商概念** — `compare_icons("kubernetes")` 一次返回 AWS、Azure 和 GCP 的 K8s 图标
- 🌐 **Streamable HTTP + stdio** — 本地运行（`stdio`）或作为 Web 服务（`--transport http`），或同时运行两者（`--transport dual`）
- 🖥️ **内置 Web 界面** — `--web` 启动本地图标浏览器（FastAPI + SPA），支持可视化浏览
- 📦 **零构建，开箱即用** — 图标已打包在 wheel 中，无需本地构建，`uvx` 直接运行
- ⚡ **FastMCP 框架** — 现代化装饰器式工具注册，自动生成 JSON Schema
- 🧩 **可扩展** — `format="ppt_master"` 生成 [ppt-master](https://github.com/hugohe3/ppt-master) 占位符；`format="inline_group"` 直接嵌入 SVG 架构图

## 📋 目录

- [tech-icons](#tech-icons)
  - [✨ 功能特性](#-功能特性)
  - [📋 目录](#-目录)
  - [🚀 快速上手](#-快速上手)
    - [直接运行（无需安装）](#直接运行无需安装)
    - [从仓库运行（开发）](#从仓库运行开发)
  - [📦 安装与要求](#-安装与要求)
    - [Extras 速览](#extras-速览)
  - [🔧 使用模式](#-使用模式)
    - [1. MCP 服务器（stdio）](#1-mcp-服务器stdio)
    - [2. MCP 服务器（Streamable HTTP）](#2-mcp-服务器streamable-http)
    - [3. 双传输（stdio + HTTP）](#3-双传输stdio--http)
    - [4. Web 界面](#4-web-界面)
    - [5. PPT-Master 导出](#5-ppt-master-导出)
  - [🖥️ MCP 客户端配置](#️-mcp-客户端配置)
    - [Claude Desktop / Claude Code](#claude-desktop--claude-code)
    - [启用语义搜索](#启用语义搜索)
    - [Streamable HTTP（远程 / 自部署）](#streamable-http远程--自部署)
    - [Cursor / Windsurf / 其他 MCP 兼容编辑器](#cursor--windsurf--其他-mcp-兼容编辑器)
  - [🐳 Docker](#-docker)
    - [快速上手](#快速上手-1)
    - [docker-compose](#docker-compose)
    - [环境变量](#环境变量)
    - [Claude Desktop 配置 (Docker)](#claude-desktop-配置-docker)
  - [🛠️ 工具与 API 参考](#️-工具与-api-参考)
    - [工具](#工具)
    - [资源](#资源)
    - [LLM 使用示例](#llm-使用示例)
  - [🎨 输出格式](#-输出格式)
  - [🏷️ 图标 ID 规范](#️-图标-id-规范)
  - [🏗️ 架构设计](#️-架构设计)
    - [核心设计决策](#核心设计决策)
    - [技术栈](#技术栈)
  - [🔗 集成](#-集成)
    - [ppt-master](#ppt-master)
    - [架构图](#架构图)
    - [语义搜索](#语义搜索)
  - [🔬 开发指南](#-开发指南)
    - [项目结构](#项目结构)
    - [运行测试](#运行测试)
    - [开发工具](#开发工具)
  - [❓ 常见问题](#-常见问题)
  - [🏅 图标来源与归属](#-图标来源与归属)
  - [📄 许可证](#-许可证)

## 🚀 快速上手

### 直接运行（无需安装）

```bash
# stdio MCP 服务器 — 适配 Claude Desktop、Cursor 等
uvx tech-icons

# 启用语义搜索（sentence-transformers 嵌入）
uvx --with 'tech-icons[semantic]' tech-icons

# 启动 Web 图标浏览器
uvx --with 'tech-icons[web]' tech-icons --web --open

# 作为 Streamable HTTP 服务运行
uvx --with 'tech-icons[web]' tech-icons --transport http --port 8000
```

### 从仓库运行（开发）

```bash
git clone https://github.com/zhiweio/tech-icons.git
cd tech-icons
uv run tech-icons
```

即可使用。发布版 wheel 内置了完整图标目录（约 1.4 MB 元数据 + SVG）——无需本地构建，无需下载资源。

## 📦 安装与要求

| 要求 | 详情 |
|------|------|
| **Python** | ≥ 3.10 |
| **包管理器** | [uv](https://docs.astral.sh/uv/)（推荐）、pip、pipx |
| **核心依赖** | `fastmcp`、`pyyaml`、`rapidfuzz` |
| **Web 界面（可选）** | `fastapi`、`uvicorn`（`[web]` extra） |
| **语义搜索（可选）** | `sentence-transformers`、`numpy`（`[semantic]` extra） |
| **全部功能** | `[all]` extra = `[web,semantic]` |

```bash
# 安装全部功能
uvx --with 'tech-icons[all]' tech-icons

# 或全局安装
uv tool install 'tech-icons[all]'
tech-icons --web
```

### Extras 速览

| Extra | 额外提供 | 适用场景 |
|-------|---------|---------|
| *无* | 核心 MCP 服务器（stdio） | Claude Desktop、Cursor、任何 MCP 客户端 |
| `[web]` | FastAPI + uvicorn | `--web` 浏览器界面、`--transport http` |
| `[semantic]` | sentence-transformers | 第四级语义搜索，处理模糊查询 |
| `[all]` | 以上全部 | 完整功能 |

## 🔧 使用模式

`tech-icons` 支持五种运行模式，通过 CLI 参数切换：

```
tech-icons                                     # stdio MCP（默认）
tech-icons --transport http --port 8000        # Streamable HTTP MCP
tech-icons --transport dual                    # stdio + HTTP 同时运行
tech-icons --web --open                        # 本地浏览器界面
tech-icons --ppt-master aws --target ./icons/   # 批量导出图标
```

### 1. MCP 服务器（stdio）

默认模式。服务器从 stdin 读取 MCP JSON-RPC 消息，响应写入 stdout。这是 Claude Desktop、Cursor 等 MCP 客户端所期望的通信方式。

```bash
uvx tech-icons
# 或带语义搜索：
uvx --with 'tech-icons[semantic]' tech-icons
```

**工作原理**：客户端进程派生 `uvx tech-icons` 作为子进程，通过 stdin/stdout 通信。每个客户端会话一个进程。无需端口，无网络——纯本地 IPC。

### 2. MCP 服务器（Streamable HTTP）

作为持久 HTTP 服务运行。多个客户端可同时连接。使用 [Streamable HTTP 协议](https://modelcontextprotocol.io/docs/concepts/transports#streamable-http) 实现包括流式响应在内的完整双向通信。

```bash
uvx --with 'tech-icons[web]' tech-icons --transport http --host 0.0.0.0 --port 8000
```

**工作原理**：Uvicorn ASGI 服务器启动，在 `http://host:port/mcp` 上对外提供 MCP 端点。客户端通过 HTTP/2 连接并支持流式传输。服务器常驻运行——启动一次，多个客户端连接。

### 3. 双传输（stdio + HTTP）

在**单个进程**中**同时运行两种传输**，共享一个引擎实例。非常适合开发场景：既需要本地 IDE 集成，又需要网络可访问的服务。

```bash
uvx --with 'tech-icons[web]' tech-icons --transport dual --port 8000
```

**工作原理**：`asyncio.gather()` 并发运行 `run_stdio_async()` 和 `run_http_async()`。两者共享同一个 `SearchEngine` 实例（仅加载一次）。使用 **Ctrl+C** 停止。

### 4. Web 界面

启动本地图标浏览器，支持全文搜索、厂商/分类过滤、分页目录浏览和 SVG 预览/下载。

```bash
uvx --with 'tech-icons[web]' tech-icons --web --port 8765 --open
```

在浏览器中打开 `http://127.0.0.1:8765`。Web 界面使用与 MCP 服务器相同的 `SearchEngine` 类——无逻辑重复。

### 5. PPT-Master 导出

将 SVG 图标批量导出到 ppt-master 模板目录。支持厂商名、逗号分隔的图标 ID 或 `all`。

```bash
# 导出单个厂商
uvx tech-icons --ppt-master aws --target ./templates/icons/

# 导出指定图标
uvx tech-icons --ppt-master aws/compute/lambda,gcp/compute/cloud-run

# 导出全部
uvx tech-icons --ppt-master all

# 使用符号链接（无需复制文件）
uvx tech-icons --ppt-master aws --symlink
```

## 🖥️ MCP 客户端配置

### Claude Desktop / Claude Code

```json
{
  "mcpServers": {
    "tech-icons": {
      "command": "uvx",
      "args": ["tech-icons"]
    }
  }
}
```

### 启用语义搜索

```json
{
  "mcpServers": {
    "tech-icons": {
      "command": "uvx",
      "args": ["--with", "tech-icons[semantic]", "tech-icons"]
    }
  }
}
```

### Streamable HTTP（远程 / 自部署）

```json
{
  "mcpServers": {
    "tech-icons": {
      "url": "http://your-server:8000/mcp",
      "transport": "http"
    }
  }
}
```

### Cursor / Windsurf / 其他 MCP 兼容编辑器

使用与上述 Claude Desktop 相同的 `stdio` 配置。对于 HTTP 传输方式，请查阅编辑器的 MCP 文档了解 HTTP 端点支持。

## 🐳 Docker

提供预构建的 Docker 镜像，支持 MCP 服务器和 Web 界面两种模式。通过 `SERVER_MODE` 环境变量切换。

### 快速上手

```bash
# 构建镜像
docker build -t tech-icons .

# 以 MCP Streamable HTTP 服务器模式运行（默认）
docker run -p 8765:8765 tech-icons

# 以 Web 界面模式运行
docker run -p 8765:8765 -e SERVER_MODE=web tech-icons
```

### docker-compose

```bash
# MCP 服务器模式
docker compose --profile mcp up -d

# Web 界面模式
docker compose --profile web up -d
```

### 环境变量

| 变量 | 默认值 | 说明 |
|------|-------|------|
| `SERVER_MODE` | `http` | `http` = MCP Streamable HTTP 服务器，`web` = FastAPI Web 界面 |
| `HOST` | `0.0.0.0` | 绑定地址（容器内始终为 `0.0.0.0`） |
| `PORT` | `8765` | 监听端口 |
| `LOG_LEVEL` | `info` | Python 日志级别 |

### Claude Desktop 配置 (Docker)

通过 Streamable HTTP 连接容器化的 tech-icons：

```json
{
  "mcpServers": {
    "tech-icons": {
      "type": "streamableHttp",
      "url": "http://localhost:8765/mcp"
    }
  }
}
```

> **注意**：容器绑定 `0.0.0.0:8765`。如果容器运行在远程主机上，需将 `localhost` 替换为主机 IP 地址。

## 🛠️ 工具与 API 参考

`tech-icons` 提供 **7 个工具**、**1 个资源**和**跨厂商概念组**：

### 工具

| 工具 | 参数 | 返回 | 说明 |
|------|------|------|------|
| `search_icons` | `query`（必填）、`vendor`、`category`、`limit` | `list[dict]` | 四级搜索：精确 ID → 关键词 → 模糊 → 语义 |
| `get_icon` | `id`（如 `aws/compute/lambda`） | `dict` | 完整元数据：厂商、分类、名称、别名、标签、描述、路径 |
| `get_icon_image` | `id`、`format`（默认 `raw`） | `str` 或 `list` | SVG 内容，指定格式；`download` 返回图片附件 |
| `list_categories` | `vendor`（可选） | `list[str]` | 列出所有分类，可按厂商过滤 |
| `list_vendors` | *无* | `dict[str, int]` | 厂商名 → 图标数量映射 |
| `list_concepts` | *无* | `list[str]` | 跨厂商概念名（如 `kubernetes`、`serverless`） |
| `compare_icons` | `concept`（如 `kubernetes`） | `dict` | 获取某概念在各厂商的对应图标，按厂商分组 |

所有参数通过 `Annotated[type, "description"]` 类型注解，由 FastMCP 自动生成 JSON Schema。

### 资源

| URI | MIME 类型 | 内容 |
|-----|----------|------|
| `icon://catalog` | `application/json` | 完整的 3,140+ 条目图标目录及全部元数据 |

### LLM 使用示例

**查找特定的 AWS 服务图标：**
```
search_icons(query="Lambda")
```

**跨云对比 Kubernetes 图标：**
```
compare_icons(concept="kubernetes")
```

**获取用于 HTML 架构图的 Data URI：**
```
get_icon_image(id="gcp/compute/cloud-run", format="data_uri")
```

**列出所有 Azure 数据库服务：**
```
search_icons(query="database", vendor="azure", category="databases")
```

**浏览完整目录：**
```
read_resource("icon://catalog")
```

## 🎨 输出格式

每种格式对应一种集成场景：

| 格式 | 输出内容 | 应用场景 | 示例 |
|------|---------|---------|------|
| `raw` | SVG XML 字符串 | 检查、直接嵌入 | `"<svg xmlns=\"...\">...</svg>"` |
| `path` | 文件系统绝对路径 | 本地工具、文件引用 | `"/path/to/icons/aws/compute/lambda.svg"` |
| `base64` | Base64 编码的 SVG | 二进制传输、JSON 载荷 | `"PHN2ZyB4bWxucz0i..."` |
| `data_uri` | `data:image/svg+xml;base64,...` | HTML `<img>` 标签、CSS 背景 | `"data:image/svg+xml;base64,..."` |
| `inline_group` | `<g viewBox="...">...</g>` | 直接嵌入 SVG 架构图 | `"<g viewBox=\"0 0 64 64\"><path d=\"...\"/></g>"` |
| `ppt_master` | `<use data-icon="tech-icons/..."/>` | ppt-master 技能占位符 | `"<use data-icon=\"tech-icons/aws/compute/lambda\"/>"` |
| `download` | 文本摘要 + `Image` 附件 | 下载 SVG 文件 | 文本 + `Image(data=..., format="svg+xml")` |

## 🏷️ 图标 ID 规范

所有图标遵循统一的规范 ID 格式：

```
{vendor}/{category}/{name}
```

**示例：**
- `aws/compute/lambda` — AWS Lambda
- `azure/databases/cosmos-db` — Azure Cosmos DB
- `gcp/serverless-computing/cloud-run` — Cloud Run
- `microsoft/365/teams` — Microsoft Teams
- `cncf/orchestration/kubernetes` — Kubernetes
- `devicon/framework/react` — React

ID 全部为**小写**，多词名称用**连字符**分隔。使用 `list_categories(vendor="aws")` 浏览某厂商的可用分类。

## 🏗️ 架构设计

<p align="center">
  <img src="docs/images/tech-icons-architecture.png" alt="tech-icons-architecture" />
</p>

### 核心设计决策

1. **单一搜索引擎，多接口复用** — `SearchEngine` 类只有*一个*实例。MCP 服务器、FastAPI Web 应用和 ppt-master CLI 均封装同一引擎——无逻辑重复。

2. **分级搜索，早停优化** — 搜索在某一级返回 ≥ `limit` 结果后立即停止。大多数查询命中第 1 级（精确 ID）或第 2 级（关键词索引），不会触发模糊或语义搜索——快速且低成本。

3. **Wheel 内置数据** — `icons.json`、`keyword_index.json` 和 SVG 通过 `hatchling` 打包进 wheel。`importlib.resources.files()` 在运行时解析路径，开发（`uv run`）和安装后（`uvx`、`pipx`）环境均可用。

4. **懒加载** — 搜索引擎仅在首次访问时从磁盘加载目录数据（`_ensure_loaded()`）。在 stdio 模式下，`engine.load()` 在 `mcp.run()` 之前显式调用。

5. **FastMCP 装饰器模式** — 每个工具是独立的 `@mcp.tool` 装饰函数。Python 类型注解（`Annotated[str, "说明"]`、`Literal["aws", ...]`）自动生成 JSON Schema。无需手写 `inputSchema`。

6. **跨厂商概念注册表** — `enrichments.yaml` 定义技术概念（如 "kubernetes"）并将其映射到各厂商的图标 ID。概念元数据在引擎初始化时加载，可通过 `engine.concepts` 访问。

### 技术栈

| 组件 | 技术 | 选型理由 |
|------|------|---------|
| MCP 框架 | FastMCP 3.4 | 装饰器式、自动 Schema、stdio+HTTP 双传输 |
| 搜索引擎 | 自定义（4 级） | 精确 → 关键词 → 模糊 → 语义，早停优化 |
| 模糊匹配 | rapidfuzz | Token-sort ratio 评分、C 加速 |
| 语义搜索 | sentence-transformers | all-MiniLM-L6-v2，可选 extra |
| Web 界面 | FastAPI + SPA | 共享引擎实例、CORS 支持 |
| 构建系统 | hatchling | PEP 517、支持打包数据文件 |
| 包管理 | uv | 快速解析器、`uvx` 一键运行 |

## 🔗 集成

### ppt-master

`ppt_master` 格式生成 `<use data-icon="tech-icons/..."/>` 元素，与 ppt-master 的 `embed_icons.py` 钩子兼容。使用 `--ppt-master` 批量导出图标：

```bash
uvx tech-icons --ppt-master aws --target ./templates/icons/
uvx tech-icons --ppt-master aws/compute/lambda,gcp/compute/cloud-run --symlink
```

### 架构图

使用 `format="data_uri"` 嵌入 HTML `<img>` 标签，或使用 `format="inline_group"` 直接组合 SVG `<g>` 元素：

```html
<!-- data_uri：嵌入 HTML -->
<img src="DATA_URI_OUTPUT" alt="AWS Lambda" class="tech-icon--md" />

<!-- inline_group：嵌入 SVG 画布 -->
<svg viewBox="0 0 800 400">
  <g transform="translate(50, 50)">
    INLINE_GROUP_OUTPUT
  </g>
</svg>
```

完整示例（包含 CSS 样式、多云布局和厂商配色规范）请参见 [docs/integration-arch-diagram.md](docs/integration-arch-diagram.md)。

### 语义搜索

添加 `[semantic]` extra 以启用第 4 级搜索。适用于关键词匹配效果不佳的模糊查询（如"那个做 serverless 的东西"）：

```bash
uvx --with 'tech-icons[semantic]' tech-icons
```

## 🔬 开发指南

```bash
# 克隆并设置
git clone https://github.com/zhiweio/tech-icons.git
cd tech-icons
uv sync --group dev

# 运行测试
uv run pytest tests/ -v

# Lint + 类型检查
uv run ruff check tech_icons/ tests/
uv run mypy tech_icons/

# 格式化
uv run ruff format tech_icons/ tests/

# 一键检查（format + lint + typecheck + test）
make all
```

### 项目结构

```
tech-icons-skills/
├── tech_icons/                # 主包
│   ├── server.py              # FastMCP 服务器 + CLI（入口点）
│   ├── search.py              # 4 级搜索引擎
│   ├── formats.py             # 7 种 SVG 输出格式适配器
│   ├── concepts.py            # 跨厂商概念注册表
│   ├── normalize.py           # SVG 标准化与目录生成
│   ├── _paths.py              # 运行时路径解析（importlib.resources）
│   ├── web/
│   │   ├── app.py             # FastAPI HTTP API
│   │   └── static/            # SPA 前端（index.html + assets）
│   ├── bridges/
│   │   └── ppt_master.py      # ppt-master 图标导出桥接
│   ├── catalog/               # 预构建数据文件（打包在 wheel 中）
│   │   ├── icons.json         # 3,140+ 条目，完整元数据
│   │   ├── keyword_index.json # 倒排关键词索引
│   │   ├── embeddings.npz     # 句子嵌入向量（可选）
│   │   ├── embedding_ids.json # 嵌入向量到 ID 的映射
│   │   └── enrichments.yaml   # 跨厂商概念定义
│   └── icons/                 # 打包的 SVG 文件（约 3,140 个）
├── tests/                     # pytest 测试套件（264+ 个测试）
├── scripts/
│   ├── build_catalog.py       # 目录构建流水线
│   └── normalize_icons.py     # SVG 标准化脚本
├── docs/                      # 文档、截图
├── pyproject.toml             # 构建配置、依赖、工具
├── Makefile                   # 开发任务运行器
└── README.md                  # 英文文档
```

### 运行测试

```bash
uv run pytest tests/ -v              # 全部测试
uv run pytest tests/test_server.py -v  # 服务器相关
uv run pytest tests/ -v --cov        # 含覆盖率
```

### 开发工具

- **格式化：** [ruff](https://docs.astral.sh/ruff/)（行宽: 120）
- **Linter：** ruff（E, W, F, I, N, UP, B, A, S, T20, RUF）
- **类型检查：** [mypy](https://mypy-lang.org/)（disallow-untyped-defs）
- **测试框架：** [pytest](https://pytest.org/) + pytest-asyncio（asyncio_mode=auto）

## ❓ 常见问题

**Q: 需要本地构建图标目录吗？**
A: 不需要。`icons.json` 和 SVG 已打包在 wheel 中，`uvx tech-icons` 开箱即用。

**Q: 和 AWS/Azure/GCP 官方图标库有什么区别？**
A: tech-icons 将 6 个厂商的图标*聚合*到同一个可搜索的 MCP 服务器中，提供一致的 ID 格式和跨厂商概念系统。无需在多个图标集中翻找——直接向 LLM 提问即可获取正确图标。

**Q: 能否不通过 MCP 客户端使用？**
A: 可以。使用 `--web` 打开浏览器界面，`--transport http` 以 REST-like API 方式访问，或直接在 Python 中导入 `SearchEngine` 使用（`from tech_icons import SearchEngine`）。

**Q: 语义搜索需要 GPU 吗？**
A: 不需要。默认 `all-MiniLM-L6-v2` 模型在 CPU 上运行。嵌入向量已预计算——运行时仅需生成查询向量。

**Q: 可以添加自己的图标或厂商吗？**
A: 可以。将 SVG 文件放在 `assets/your-vendor-*` 下，在 `tech_icons/normalize.py` 中添加收集函数，运行 `scripts/build_catalog.py` 重建目录。详见[开发指南](#-开发指南)。

**Q: 支持什么 MCP 协议版本？**
A: FastMCP 3.4 支持 MCP 协议版本 `2025-03-26`。所有传输方式（stdio、Streamable HTTP）均使用此协议。

## 🏅 图标来源与归属

tech-icons **聚合**了以下来源的图标。项目本身（服务器、搜索引擎、工具链）采用 MIT 协议开源，但打包的图标文件保留其原始许可和条款。在重新分发或修改图标之前，请查阅每个来源的许可。

| 来源 | 厂商 | 许可 / 条款 | 备注 |
|------|------|-------------|------|
| [AWS Architecture Icons](https://aws.amazon.com/architecture/icons/) | `aws` | AWS [服务条款](https://aws.amazon.com/architecture/icons/) | 可用于架构图绘制。 |
| [Azure Architecture Icons](https://learn.microsoft.com/en-us/azure/architecture/icons/) | `azure` | [Microsoft 条款](https://learn.microsoft.com/en-us/azure/architecture/icons/) | 可用于架构图绘制。 |
| [Google Cloud Icons](https://cloud.google.com/icons) | `gcp` | Google Cloud [品牌指南](https://cloud.google.com/icons) | 可用于架构图绘制。 |
| [Microsoft 365 架构图标](https://learn.microsoft.com/en-us/previous-versions/microsoft-365/solutions/architecture-icons-templates) | `microsoft` (365) | [Microsoft 条款](https://learn.microsoft.com/en-us/previous-versions/microsoft-365/solutions/architecture-icons-templates) | |
| [Dynamics 365 图标](https://learn.microsoft.com/en-us/dynamics365/get-started/icons) | `microsoft` (dynamics-365) | [Microsoft 条款](https://learn.microsoft.com/en-us/dynamics365/get-started/icons) | |
| [Microsoft Entra 架构图标](https://learn.microsoft.com/en-us/entra/architecture/architecture-icons) | `microsoft` (entra) | [Microsoft 条款](https://learn.microsoft.com/en-us/entra/architecture/architecture-icons) | |
| [Microsoft Fabric 图标](https://learn.microsoft.com/en-us/fabric/fundamentals/icons) | `microsoft` (fabric) | [Microsoft 条款](https://learn.microsoft.com/en-us/fabric/fundamentals/icons) | |
| [Power Platform 图标](https://learn.microsoft.com/en-us/power-platform/guidance/icons) | `microsoft` (power-platform) | [Microsoft 条款](https://learn.microsoft.com/en-us/power-platform/guidance/icons) | |
| [CNCF Artwork](https://github.com/cncf/artwork) | `cncf` | CNCF [商标与徽标指南](https://github.com/cncf/artwork) | 商标归 CNCF 及各自项目所有。 |
| [Devicon](https://github.com/devicons/devicon) | `devicon` | [MIT 协议](https://github.com/devicons/devicon/blob/master/LICENSE) | 软件技术图标字体与 SVG。 |
| [Developer Icons](https://github.com/xandemon/developer-icons) | `developer` | [MIT 协议](https://github.com/xandemon/developer-icons) | 扁平化彩色技术图标。 |

> **注意**：本项目**不**对任何打包的图标文件声称所有权。图标均按其上游原始状态提供，方便 AI 辅助绘图工作流使用。本项目的 MIT 协议仅适用于服务器代码、搜索引擎、工具链和文档——**不**适用于第三方图标资源。

## 📄 许可证

**项目代码**（服务器、搜索引擎、工具链、文档）：MIT © [zhiweio](https://github.com/zhiweio)

**打包图标**：每套图标保留其原始许可和条款，详见[图标来源与归属](#-图标来源与归属)。
