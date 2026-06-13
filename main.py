"""
AI-First 商家网站 — FastAPI 主应用
===================================
所有端点支持内容协商: Accept: application/json → JSON, text/html → HTML
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware

from content_loader import (
    load_products, load_services, load_page,
    get_product, get_service, get_all_categories,
)
from models import Product, Service, SearchResult, CatalogResponse

# ==================== App Setup ====================
app = FastAPI(
    title="AI-First Store",
    description="An AI-first website for products and local services. "
                "Supports llms.txt, agent.json, MCP, and schema.org JSON-LD.",
    version="1.0.0",
)

BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

SITE_NAME = "暖居采暖"
SITE_DESC = "福泉采暖地暖一站式服务 — 林内壁挂炉 | 纽恩泰空气能 | 地暖铺设 | 中央空调 | 装修设计监理"

SITE_CONTACT = {
    "phones": ["13595498010", "15286280516"],
    "wechat": "微信同号",
    "address": "贵州省黔南州福泉市麒龙美家居10号楼大厅39号门面",
    "douyin": "福泉市林内供暖设备销售店",
}


# ==================== Content Negotiation ====================

class ContentNegotiationMiddleware(BaseHTTPMiddleware):
    """Lightweight content negotiation: JSON for API clients, HTML for browsers."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        return response


def wants_json(request: Request) -> bool:
    """Check if client prefers JSON over HTML."""
    accept = request.headers.get("accept", "")
    return "application/json" in accept and "text/html" not in accept


def render_or_json(request: Request, template: str, context: dict,
                   json_data: Optional[dict] = None) -> HTMLResponse | JSONResponse:
    """Return HTML or JSON based on Accept header."""
    if wants_json(request):
        return JSONResponse(content=json_data or context)
    return templates.TemplateResponse(request, template, context)


# ==================== Routes ====================

@app.get("/")
async def index(request: Request):
    products = load_products()
    services = load_services()
    categories = get_all_categories()

    json_data = {
        "site": SITE_NAME,
        "description": SITE_DESC,
        "products_count": len(products),
        "services_count": len(services),
        "categories": categories,
        "endpoints": {
            "products": "/products",
            "services": "/services",
            "search": "/search?q=",
            "catalog": "/api/catalog.json",
            "llms_txt": "/llms.txt",
            "agent_json": "/.well-known/agent.json",
        },
    }
    return render_or_json(request, "index.html", {
        "request": request,
        "site_name": SITE_NAME,
        "site_desc": SITE_DESC,
        "products": products,
        "services": services,
        "categories": categories,
    }, json_data)


# ---- Products ----

@app.get("/products")
async def list_products(
    request: Request,
    category: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    q: Optional[str] = Query(None),
):
    products = load_products()
    if category:
        products = [p for p in products if p.category == category]
    if min_price is not None:
        products = [p for p in products if p.price >= min_price]
    if max_price is not None:
        products = [p for p in products if p.price <= max_price]
    if q:
        ql = q.lower()
        products = [
            p for p in products
            if ql in p.name.lower() or ql in p.description.lower()
            or ql in p.content.lower() or any(ql in k.lower() for k in p.keywords)
        ]

    json_data = {
        "total": len(products),
        "products": [p.model_dump() for p in products],
    }
    return render_or_json(request, "products.html", {
        "request": request,
        "site_name": SITE_NAME,
        "products": products,
        "category": category,
        "query": q,
    }, json_data)


@app.get("/products/{slug}")
async def product_detail(request: Request, slug: str):
    product = get_product(slug)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    json_data = {
        "product": product.model_dump(),
        "schema_org": product.schema_org(),
    }
    return render_or_json(request, "product.html", {
        "request": request,
        "site_name": SITE_NAME,
        "product": product,
        "schema_org": json.dumps(product.schema_org(), ensure_ascii=False),
    }, json_data)


# ---- Services ----

@app.get("/services")
async def list_services(
    request: Request,
    category: Optional[str] = Query(None),
    area: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
):
    services = load_services()
    if category:
        services = [s for s in services if s.category == category]
    if area:
        services = [s for s in services if s.area and area in s.area]
    if q:
        ql = q.lower()
        services = [
            s for s in services
            if ql in s.name.lower() or ql in s.description.lower()
            or ql in s.content.lower() or any(ql in k.lower() for k in s.keywords)
        ]

    json_data = {
        "total": len(services),
        "services": [s.model_dump() for s in services],
    }
    return render_or_json(request, "services.html", {
        "request": request,
        "site_name": SITE_NAME,
        "services": services,
        "category": category,
        "query": q,
    }, json_data)


@app.get("/services/{slug}")
async def service_detail(request: Request, slug: str):
    service = get_service(slug)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    json_data = {
        "service": service.model_dump(),
        "schema_org": service.schema_org(),
    }
    return render_or_json(request, "service.html", {
        "request": request,
        "site_name": SITE_NAME,
        "service": service,
        "schema_org": json.dumps(service.schema_org(), ensure_ascii=False),
    }, json_data)


# ---- Search ----

@app.get("/search")
async def search(request: Request, q: str = Query(..., min_length=1)):
    ql = q.lower()
    products = load_products()
    services = load_services()

    results: list[SearchResult] = []

    for p in products:
        if (ql in p.name.lower() or ql in p.description.lower()
                or ql in p.content.lower() or any(ql in k.lower() for k in p.keywords)):
            results.append(SearchResult(
                id=p.id, type="product", name=p.name, description=p.description,
                category=p.category, price=p.price, currency=p.currency,
                url=f"/products/{p.slug or p.id}", keywords=p.keywords,
            ))

    for s in services:
        if (ql in s.name.lower() or ql in s.description.lower()
                or ql in s.content.lower() or any(ql in k.lower() for k in s.keywords)):
            results.append(SearchResult(
                id=s.id, type="service", name=s.name, description=s.description,
                category=s.category, price=s.price, currency=s.currency,
                url=f"/services/{s.slug or s.id}", keywords=s.keywords,
            ))

    json_data = {
        "query": q,
        "total": len(results),
        "results": [r.model_dump() for r in results],
    }
    return render_or_json(request, "search.html", {
        "request": request,
        "site_name": SITE_NAME,
        "query": q,
        "results": results,
    }, json_data)


# ---- Full Catalog (AI's favorite) ----

@app.get("/api/catalog.json")
async def full_catalog():
    products = load_products()
    services = load_services()
    return CatalogResponse(
        site_name=SITE_NAME,
        description=SITE_DESC,
        contact=SITE_CONTACT,
        updated=datetime.now().isoformat(),
        total_products=len(products),
        total_services=len(services),
        products=products,
        services=services,
    ).model_dump()


# ---- Static AI protocol files ----

@app.get("/llms.txt", response_class=PlainTextResponse)
async def llms_txt(request: Request):
    """AI-readable site index (llmstxt.org standard)."""
    base_url = str(request.base_url).rstrip("/")
    products = load_products()
    services = load_services()
    categories = get_all_categories()

    lines = [
        f"# {SITE_NAME}",
        f"",
        f"> {SITE_DESC}",
        f"",
        f"## About",
        f"- [{SITE_NAME}]({base_url}/): {SITE_DESC}",
        f"- [About]({base_url}/about): 关于我们",
        f"",
        f"## Products ({len(products)} items)",
    ]
    for cat in categories.get("product_categories", []):
        lines.append(f"### {cat}")
        for p in products:
            if p.category == cat:
                lines.append(p.to_llms_md(base_url))
    lines.append("")

    lines.append(f"## Services ({len(services)} items)")
    for cat in categories.get("service_categories", []):
        lines.append(f"### {cat}")
        for s in services:
            if s.category == cat:
                lines.append(s.to_llms_md(base_url))
    lines.append("")

    lines.extend([
        f"## API",
        f"- [Full Catalog]({base_url}/api/catalog.json): Complete product/service data in JSON",
        f"- [Search]({base_url}/search?q={{query}}): Search across all products and services",
        f"",
        f"## Agent Protocols",
        f"- [agent.json]({base_url}/.well-known/agent.json): Agent capability declaration (A2A)",
        f"- [MCP]({base_url}/mcp): Model Context Protocol endpoint",
    ])
    return PlainTextResponse("\n".join(lines), media_type="text/plain; charset=utf-8")


@app.get("/llms-full.txt", response_class=PlainTextResponse)
async def llms_full(request: Request):
    """Complete product/service content in one file for AI to load in one context."""
    base_url = str(request.base_url).rstrip("/")
    products = load_products()
    services = load_services()

    parts = [f"# {SITE_NAME} — Full Catalog", f"", f"## Products", ""]
    for p in products:
        parts.append(f"### {p.name}")
        parts.append(f"- Price: ¥{p.price}")
        parts.append(f"- Category: {p.category}")
        parts.append(f"- Availability: {p.availability}")
        if p.location:
            parts.append(f"- Location: {p.location}")
        parts.append(f"- Keywords: {', '.join(p.keywords)}")
        parts.append(f"- URL: {base_url}/products/{p.slug or p.id}")
        parts.append(f"")
        parts.append(p.content)
        parts.append(f"---")
        parts.append("")

    parts.append(f"## Services")
    parts.append("")
    for s in services:
        parts.append(f"### {s.name}")
        parts.append(f"- Price: ¥{s.price}{s.price_unit}")
        parts.append(f"- Category: {s.category}")
        parts.append(f"- Availability: {s.availability}")
        if s.area:
            parts.append(f"- Area: {s.area}")
        parts.append(f"- Keywords: {', '.join(s.keywords)}")
        parts.append(f"- URL: {base_url}/services/{s.slug or s.id}")
        parts.append(f"")
        parts.append(s.content)
        parts.append(f"---")
        parts.append("")

    return PlainTextResponse("\n".join(parts), media_type="text/plain; charset=utf-8")


@app.get("/.well-known/agent.json")
async def agent_json(request: Request):
    """Agent Card — AI capability declaration (Google A2A standard)."""
    base_url = str(request.base_url).rstrip("/")
    return {
        "name": SITE_NAME,
        "description": SITE_DESC,
        "url": base_url,
        "version": "1.0.0",
        "capabilities": {
            "streaming": False,
            "pushNotifications": False,
        },
        "skills": [
            {
                "id": "search_products",
                "name": "Search Products",
                "description": "Search products by keyword, category, or price range",
                "tags": ["product", "search", "catalog"],
                "examples": [
                    f"GET {base_url}/products?q=AI咨询",
                    f"GET {base_url}/products?category=技术服务&max_price=5000",
                ],
            },
            {
                "id": "search_services",
                "name": "Search Services",
                "description": "Search local services by keyword, category, or area",
                "tags": ["service", "search", "local"],
                "examples": [
                    f"GET {base_url}/services?q=培训",
                    f"GET {base_url}/services?area=海淀区",
                ],
            },
            {
                "id": "full_catalog",
                "name": "Full Catalog",
                "description": "Get complete product and service catalog as JSON",
                "tags": ["catalog", "all", "json"],
                "examples": [
                    f"GET {base_url}/api/catalog.json",
                ],
            },
            {
                "id": "full_text_search",
                "name": "Full Text Search",
                "description": "Search across all products and services",
                "tags": ["search", "unified"],
                "examples": [
                    f"GET {base_url}/search?q=AI",
                ],
            },
        ],
        "defaultInputModes": ["text", "application/json"],
        "defaultOutputModes": ["application/json", "text/plain"],
        "authentication": None,
        "protocols": {
            "a2a": f"{base_url}/.well-known/agent.json",
            "mcp": f"{base_url}/mcp",
            "rest": f"{base_url}/api/catalog.json",
        },
    }


@app.get("/mcp")
async def mcp_info():
    """MCP protocol info endpoint."""
    return {
        "protocol": "mcp",
        "version": "1.0",
        "tools": [
            {
                "name": "search_catalog",
                "description": "Search the product and service catalog",
                "parameters": {
                    "query": "string — search keyword",
                    "type": "string — 'product', 'service', or 'all'",
                },
            },
            {
                "name": "get_catalog",
                "description": "Get the full product and service catalog",
                "parameters": {},
            },
            {
                "name": "list_categories",
                "description": "List all product and service categories",
                "parameters": {},
            },
        ],
        "endpoint": "/api/catalog.json",
    }


# ---- Static pages ----

@app.get("/about")
async def about(request: Request):
    page = load_page("about")
    if not page:
        raise HTTPException(status_code=404)
    return render_or_json(request, "page.html", {
        "request": request,
        "site_name": SITE_NAME,
        "title": page["title"],
        "description": page["description"],
        "content": page["content"],
    }, {
        "title": page["title"],
        "description": page["description"],
        "content": page["content"],
    })


# ==================== Main ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
