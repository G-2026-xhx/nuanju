"""Load products and services from Markdown files with YAML frontmatter."""

import os
from pathlib import Path
from typing import Optional
import frontmatter
from models import Product, Service

CONTENT_DIR = Path(__file__).parent / "content"


def _parse_frontmatter(raw: dict, body: str, slug: str) -> dict:
    """Parse raw frontmatter dict, handling comma-separated string fields."""
    result = dict(raw)
    # Parse keywords: can be list in YAML or comma-separated string
    if "keywords" in result:
        if isinstance(result["keywords"], str):
            result["keywords"] = [k.strip() for k in result["keywords"].split(",") if k.strip()]
        elif isinstance(result["keywords"], list):
            result["keywords"] = [str(k).strip() for k in result["keywords"] if str(k).strip()]
    else:
        result["keywords"] = []
    result["content"] = body
    result["slug"] = slug
    return result


def load_products() -> list[Product]:
    """Load all products from content/products/*.md."""
    products = []
    products_dir = CONTENT_DIR / "products"
    if not products_dir.exists():
        return products
    for fpath in sorted(products_dir.glob("*.md")):
        post = frontmatter.load(fpath)
        slug = fpath.stem
        data = _parse_frontmatter(post.metadata, post.content, slug)
        data["id"] = data.get("id", slug)
        data["type"] = "product"
        products.append(Product(**data))
    return products


def load_services() -> list[Service]:
    """Load all services from content/services/*.md."""
    services = []
    services_dir = CONTENT_DIR / "services"
    if not services_dir.exists():
        return services
    for fpath in sorted(services_dir.glob("*.md")):
        post = frontmatter.load(fpath)
        slug = fpath.stem
        data = _parse_frontmatter(post.metadata, post.content, slug)
        data["id"] = data.get("id", slug)
        data["type"] = "service"
        services.append(Service(**data))
    return services


def load_page(slug: str) -> Optional[dict]:
    """Load a content page (about, contact, etc.) from content/pages/."""
    fpath = CONTENT_DIR / "pages" / f"{slug}.md"
    if not fpath.exists():
        return None
    post = frontmatter.load(fpath)
    return {
        "title": post.metadata.get("title", slug),
        "content": post.content,
        "description": post.metadata.get("description", ""),
    }


def get_product(slug: str) -> Optional[Product]:
    """Get a single product by slug."""
    fpath = CONTENT_DIR / "products" / f"{slug}.md"
    if not fpath.exists():
        return None
    post = frontmatter.load(fpath)
    data = _parse_frontmatter(post.metadata, post.content, slug)
    data["id"] = data.get("id", slug)
    data["type"] = "product"
    return Product(**data)


def get_service(slug: str) -> Optional[Service]:
    """Get a single service by slug."""
    fpath = CONTENT_DIR / "services" / f"{slug}.md"
    if not fpath.exists():
        return None
    post = frontmatter.load(fpath)
    data = _parse_frontmatter(post.metadata, post.content, slug)
    data["id"] = data.get("id", slug)
    data["type"] = "service"
    return Service(**data)


def get_all_categories() -> dict[str, list[str]]:
    """Return dict of product and service categories."""
    products = load_products()
    services = load_services()
    return {
        "product_categories": sorted(set(p.category for p in products)),
        "service_categories": sorted(set(s.category for s in services)),
    }


def reload():
    """Force reload all content (call after file changes)."""
    pass  # Stateless — each call re-reads files
