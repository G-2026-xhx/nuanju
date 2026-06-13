"""Pydantic data models for products and services."""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class Product(BaseModel):
    id: str
    type: str = "product"
    name: str
    category: str
    price: float
    currency: str = "CNY"
    description: str
    location: Optional[str] = None
    availability: str = "InStock"
    image: Optional[str] = None
    keywords: list[str] = []
    content: str = ""  # full markdown body
    slug: str = ""

    def schema_org(self) -> dict:
        """Generate schema.org Product JSON-LD."""
        return {
            "@context": "https://schema.org",
            "@type": "Product",
            "name": self.name,
            "description": self.description,
            "sku": self.id,
            "offers": {
                "@type": "Offer",
                "price": str(self.price),
                "priceCurrency": self.currency,
                "availability": f"https://schema.org/{self.availability}",
            },
            "category": self.category,
            "keywords": ", ".join(self.keywords),
        }

    def to_llms_md(self, base_url: str = "") -> str:
        """Render as llms.txt entry."""
        url = f"{base_url}/products/{self.slug or self.id}"
        return f"- [{self.name}]({url}): {self.description} — ¥{self.price} | {self.category}"


class Service(BaseModel):
    id: str
    type: str = "service"
    name: str
    category: str
    price: float
    price_unit: str = "/次"
    currency: str = "CNY"
    area: Optional[str] = None
    description: str
    availability: str = "available"
    keywords: list[str] = []
    content: str = ""
    slug: str = ""

    def schema_org(self) -> dict:
        """Generate schema.org Service JSON-LD."""
        return {
            "@context": "https://schema.org",
            "@type": "Service",
            "name": self.name,
            "description": self.description,
            "serviceType": self.category,
            "provider": {
                "@type": "LocalBusiness" if self.area else "Organization",
                "name": self.name,
            },
            "areaServed": self.area.split(",") if self.area else None,
            "offers": {
                "@type": "Offer",
                "price": str(self.price),
                "priceCurrency": self.currency,
                "unitText": self.price_unit,
            },
            "keywords": ", ".join(self.keywords),
        }

    def to_llms_md(self, base_url: str = "") -> str:
        """Render as llms.txt entry."""
        url = f"{base_url}/services/{self.slug or self.id}"
        area_str = f" | 区域: {self.area}" if self.area else ""
        return f"- [{self.name}]({url}): {self.description} — ¥{self.price}{self.price_unit} | {self.category}{area_str}"


class SearchResult(BaseModel):
    """Unified search result across products and services."""
    id: str
    type: str
    name: str
    description: str
    category: str
    price: float
    currency: str
    url: str
    keywords: list[str] = []


class CatalogResponse(BaseModel):
    """Full catalog for AI consumption."""
    site_name: str
    description: str
    contact: dict = {}
    updated: str
    total_products: int
    total_services: int
    products: list[Product]
    services: list[Service]
