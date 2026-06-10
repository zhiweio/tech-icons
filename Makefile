# Makefile for tech-icons development tasks

.DEFAULT_GOAL := help

.PHONY: help install format lint check test typecheck all

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install project with dev dependencies
	uv sync --group dev

format: ## Format code with ruff
	uv run ruff format src/ scripts/ tests/

lint: ## Lint code with ruff
	uv run ruff check src/ scripts/ tests/

lint-fix: ## Lint and auto-fix issues
	uv run ruff check --fix src/ scripts/ tests/

typecheck: ## Type check with mypy
	uv run mypy src/

check: lint typecheck ## Run all checks (lint + typecheck)

test: ## Run tests with pytest
	uv run pytest

test-cov: ## Run tests with coverage
	uv run pytest --cov=src --cov-report=term-missing

all: format lint typecheck test ## Format, lint, typecheck, and test

build-catalog: ## Build the icon catalog
	uv run python scripts/build_catalog.py

build-catalog-no-embed: ## Build catalog without embeddings
	uv run python scripts/build_catalog.py --skip-embeddings

serve: ## Start the MCP server
	uv run python src/server.py

web: ## Start the web UI (FastAPI on :8765)
	uv run uvicorn src.web.app:app --reload --port 8765

web-prod: ## Start the web UI without reload
	uv run uvicorn src.web.app:app --host 0.0.0.0 --port 8765
