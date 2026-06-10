"""Shared fixtures for tech-icons test suite."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

MINIMAL_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><path d="M24 4L4 44h40z" fill="#FF9900"/></svg>'
)

MINIMAL_SVG_WITH_GROUP = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
    '<g><circle cx="32" cy="32" r="28" fill="#232F3E"/>'
    '<path d="M20 30h24v4H20z" fill="#FFF"/></g>'
    "</svg>"
)


@pytest.fixture
def sample_svg_content() -> str:
    """Valid minimal SVG string."""
    return MINIMAL_SVG


@pytest.fixture
def sample_catalog() -> list[dict]:
    """Sample catalog with 15 icon entries covering all vendors."""
    return [
        {
            "id": "aws/compute/lambda",
            "vendor": "aws",
            "category": "compute",
            "name": "AWS Lambda",
            "filename": "lambda.svg",
            "path": "icons/aws/compute/lambda.svg",
            "aliases": ["serverless", "faas", "function-as-a-service", "lambda"],
            "tags": ["aws", "compute", "serverless"],
            "description": "AWS Lambda - AWS compute service",
        },
        {
            "id": "aws/compute/ec2",
            "vendor": "aws",
            "category": "compute",
            "name": "AWS EC2",
            "filename": "ec2.svg",
            "path": "icons/aws/compute/ec2.svg",
            "aliases": ["virtual-machine", "vm", "elastic-compute", "ec2"],
            "tags": ["aws", "compute", "vm"],
            "description": "AWS EC2 - AWS compute service",
        },
        {
            "id": "aws/databases/dynamodb",
            "vendor": "aws",
            "category": "databases",
            "name": "AWS DynamoDB",
            "filename": "dynamodb.svg",
            "path": "icons/aws/databases/dynamodb.svg",
            "aliases": ["nosql", "dynamo", "dynamodb"],
            "tags": ["aws", "databases", "nosql"],
            "description": "AWS DynamoDB - AWS databases service",
        },
        {
            "id": "aws/networking/elastic-load-balancing",
            "vendor": "aws",
            "category": "networking",
            "name": "AWS Elastic Load Balancing",
            "filename": "elastic-load-balancing.svg",
            "path": "icons/aws/networking/elastic-load-balancing.svg",
            "aliases": ["load-balancer", "elb", "alb", "nlb"],
            "tags": ["aws", "networking", "load-balancer"],
            "description": "AWS Elastic Load Balancing - networking service",
        },
        {
            "id": "azure/compute/virtual-machines",
            "vendor": "azure",
            "category": "compute",
            "name": "Azure Virtual Machines",
            "filename": "virtual-machines.svg",
            "path": "icons/azure/compute/virtual-machines.svg",
            "aliases": ["virtual-machine", "vm", "virtual-machines"],
            "tags": ["azure", "compute", "vm"],
            "description": "Azure Virtual Machines - Azure compute service",
        },
        {
            "id": "azure/compute/function-apps",
            "vendor": "azure",
            "category": "compute",
            "name": "Azure Function Apps",
            "filename": "function-apps.svg",
            "path": "icons/azure/compute/function-apps.svg",
            "aliases": ["serverless", "faas", "functions", "function-apps"],
            "tags": ["azure", "compute", "serverless"],
            "description": "Azure Function Apps - Azure compute service",
        },
        {
            "id": "azure/networking/load-balancer",
            "vendor": "azure",
            "category": "networking",
            "name": "Azure Load Balancer",
            "filename": "load-balancer.svg",
            "path": "icons/azure/networking/load-balancer.svg",
            "aliases": ["load-balancer", "lb"],
            "tags": ["azure", "networking", "load-balancer"],
            "description": "Azure Load Balancer - networking service",
        },
        {
            "id": "gcp/compute/compute-engine",
            "vendor": "gcp",
            "category": "compute",
            "name": "GCP Compute Engine",
            "filename": "compute-engine.svg",
            "path": "icons/gcp/compute/compute-engine.svg",
            "aliases": ["virtual-machine", "vm", "compute-engine"],
            "tags": ["gcp", "compute", "vm"],
            "description": "GCP Compute Engine - GCP compute service",
        },
        {
            "id": "gcp/serverless-computing/cloud-functions",
            "vendor": "gcp",
            "category": "serverless-computing",
            "name": "GCP Cloud Functions",
            "filename": "cloud-functions.svg",
            "path": "icons/gcp/serverless-computing/cloud-functions.svg",
            "aliases": ["serverless", "faas", "cloud-functions"],
            "tags": ["gcp", "serverless-computing", "serverless"],
            "description": "GCP Cloud Functions - serverless computing service",
        },
        {
            "id": "gcp/networking/cloud-load-balancing",
            "vendor": "gcp",
            "category": "networking",
            "name": "GCP Cloud Load Balancing",
            "filename": "cloud-load-balancing.svg",
            "path": "icons/gcp/networking/cloud-load-balancing.svg",
            "aliases": ["load-balancer", "cloud-load-balancing"],
            "tags": ["gcp", "networking", "load-balancer"],
            "description": "GCP Cloud Load Balancing - networking service",
        },
        {
            "id": "microsoft/dynamics-365/sales",
            "vendor": "microsoft",
            "category": "dynamics-365",
            "name": "Microsoft Sales",
            "filename": "sales.svg",
            "path": "icons/microsoft/dynamics-365/sales.svg",
            "aliases": ["dynamics-sales", "crm", "sales"],
            "tags": ["microsoft", "dynamics-365", "business-applications"],
            "description": "Microsoft Sales - Dynamics 365 service",
        },
        {
            "id": "microsoft/fabric/data-warehouse",
            "vendor": "microsoft",
            "category": "fabric",
            "name": "Microsoft Data Warehouse",
            "filename": "data-warehouse.svg",
            "path": "icons/microsoft/fabric/data-warehouse.svg",
            "aliases": ["data-warehouse", "synapse", "fabric"],
            "tags": ["microsoft", "fabric", "data-platform"],
            "description": "Microsoft Data Warehouse - Fabric service",
        },
        {
            "id": "microsoft/power-platform/power-automate",
            "vendor": "microsoft",
            "category": "power-platform",
            "name": "Microsoft Power Automate",
            "filename": "power-automate.svg",
            "path": "icons/microsoft/power-platform/power-automate.svg",
            "aliases": ["flow", "automation", "power-automate"],
            "tags": ["microsoft", "power-platform", "low-code"],
            "description": "Microsoft Power Automate - Power Platform service",
        },
        {
            "id": "microsoft/entra/conditional-access",
            "vendor": "microsoft",
            "category": "entra",
            "name": "Microsoft Conditional Access",
            "filename": "conditional-access.svg",
            "path": "icons/microsoft/entra/conditional-access.svg",
            "aliases": ["conditional-access", "mfa", "identity"],
            "tags": ["microsoft", "entra", "identity", "security"],
            "description": "Microsoft Conditional Access - Entra identity service",
        },
        {
            "id": "microsoft/microsoft-365/teams",
            "vendor": "microsoft",
            "category": "microsoft-365",
            "name": "Microsoft Teams",
            "filename": "teams.svg",
            "path": "icons/microsoft/microsoft-365/teams.svg",
            "aliases": ["teams", "collaboration", "chat"],
            "tags": ["microsoft", "microsoft-365", "productivity"],
            "description": "Microsoft Teams - Microsoft 365 collaboration",
        },
    ]


@pytest.fixture
def sample_keyword_index(sample_catalog: list[dict]) -> dict[str, list[str]]:
    """Inverted keyword index built from sample_catalog."""
    from collections import defaultdict

    index: dict[str, list[str]] = defaultdict(list)

    for record in sample_catalog:
        icon_id = record["id"]
        tokens: set[str] = set()

        for word in record["name"].lower().split():
            tokens.add(word)

        for alias in record["aliases"]:
            tokens.add(alias.lower())
            for word in alias.lower().split("-"):
                tokens.add(word)

        for tag in record["tags"]:
            tokens.add(tag.lower())
            for word in tag.lower().split("-"):
                tokens.add(word)

        tokens.add(record["category"])
        tokens.add(record["vendor"])

        for token in tokens:
            if token and len(token) >= 2:
                if icon_id not in index[token]:
                    index[token].append(icon_id)

    return dict(sorted(index.items()))


@pytest.fixture
def sample_enrichments() -> dict:
    """Subset of enrichments.yaml for testing."""
    return {
        "aliases": {
            "serverless": [
                "aws/compute/lambda",
                "azure/compute/function-apps",
                "gcp/serverless-computing/cloud-functions",
            ],
            "faas": [
                "aws/compute/lambda",
                "azure/compute/function-apps",
                "gcp/serverless-computing/cloud-functions",
            ],
            "virtual-machine": [
                "aws/compute/ec2",
                "azure/compute/virtual-machines",
                "gcp/compute/compute-engine",
            ],
            "kubernetes": [
                "aws/containers/elastic-kubernetes-service",
                "azure/containers/kubernetes-services",
                "gcp/containers/gke",
            ],
        },
        "tags": {
            "compute": [
                "aws/compute/lambda",
                "aws/compute/ec2",
                "azure/compute/virtual-machines",
                "gcp/compute/compute-engine",
            ],
            "serverless": [
                "aws/compute/lambda",
                "azure/compute/function-apps",
                "gcp/serverless-computing/cloud-functions",
            ],
        },
    }


@pytest.fixture
def tmp_icons_dir(tmp_path: Path) -> Path:
    """Temp directory with a few actual SVG files for format testing."""
    icons = tmp_path / "icons"
    icons.mkdir()

    # Create vendor/category dirs with SVG files
    aws_compute = icons / "aws" / "compute"
    aws_compute.mkdir(parents=True)
    (aws_compute / "lambda.svg").write_text(MINIMAL_SVG)
    (aws_compute / "ec2.svg").write_text(MINIMAL_SVG_WITH_GROUP)

    azure_compute = icons / "azure" / "compute"
    azure_compute.mkdir(parents=True)
    (azure_compute / "virtual-machines.svg").write_text(MINIMAL_SVG)

    gcp_compute = icons / "gcp" / "compute"
    gcp_compute.mkdir(parents=True)
    (gcp_compute / "compute-engine.svg").write_text(MINIMAL_SVG)

    ms_fabric = icons / "microsoft" / "fabric"
    ms_fabric.mkdir(parents=True)
    (ms_fabric / "data-warehouse.svg").write_text(MINIMAL_SVG)

    return icons


@pytest.fixture
def search_engine(
    tmp_path: Path,
    sample_catalog: list[dict],
    sample_keyword_index: dict,
    sample_enrichments: dict,
):
    """Initialized SearchEngine with sample data (no embeddings)."""
    import yaml

    from src.search import SearchEngine

    catalog_dir = tmp_path / "catalog"
    catalog_dir.mkdir()

    # Write catalog
    (catalog_dir / "icons.json").write_text(json.dumps(sample_catalog))
    (catalog_dir / "keyword_index.json").write_text(json.dumps(sample_keyword_index))
    (catalog_dir / "enrichments.yaml").write_text(yaml.safe_dump(sample_enrichments))

    engine = SearchEngine(catalog_dir=catalog_dir)
    engine.load()
    return engine
