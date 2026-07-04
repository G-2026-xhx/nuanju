"""
build.py — 把整个 AI-First 网站生成纯静态文件
==============================================
跑一次产出 dist/ 目录，可直接部署到 Vercel / Netlify。
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import json
import shutil
from pathlib import Path
from datetime import datetime

from jinja2 import Environment, FileSystemLoader
from markdown import markdown

from content_loader import load_products, load_services, load_page, load_articles, load_reviews, load_cities, get_all_categories
from models import Product, Service, SearchResult

ROOT = Path(__file__).parent
DIST = ROOT / "dist"
TEMPLATES = ROOT / "templates"
STATIC = ROOT / "static"
CONTENT = ROOT / "content"

SITE_NAME = "福泉美佳精工暖通有限公司"
SITE_DESC = "福泉采暖地暖中央空调一站式服务 — 林内壁挂炉 | 纽恩泰空气能 | 地暖铺设 | 中央空调 | 装修设计监理"
BASE_URL = "http://fqnuantong.com"  # 独立域名 (HTTPS证书生效后改回https)

# ── 统计分析 ID（注册后填入，用于站点验证和流量分析）──
BAIDU_TONGJI_ID = ""     # 百度统计: https://tongji.baidu.com/ 注册获取
GOOGLE_ANALYTICS_ID = "" # Google Analytics: https://analytics.google.com/ 注册获取

SITE_CONTACT = {
    "phones": ["13595498010", "15286280516"],
    "wechat": "微信同号",
    "address": "贵州省黔南州福泉市麒龙美家居10号楼大厅39号门面",
    "douyin": "福泉市林内供暖设备销售店",
    "company": "福泉美佳精工暖通有限公司",
}

# ── Jinja2 ─────────────────────────────────────────
env = Environment(loader=FileSystemLoader(str(TEMPLATES)))
env.filters["markdown"] = lambda text: markdown(text, output_format="html")


def render_html(template: str, context: dict, path: str):
    """Render Jinja2 → write to dist/path."""
    # 注入追踪 ID 到所有页面
    context.setdefault("baidu_tongji_id", BAIDU_TONGJI_ID)
    context.setdefault("google_analytics_id", GOOGLE_ANALYTICS_ID)
    tmpl = env.get_template(template)
    html = tmpl.render(**context)
    out = DIST / path
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"  HTML → {path}")


def write_json(data: dict | list, path: str):
    """Write JSON to dist/path."""
    out = DIST / path
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  JSON → {path}")


def write_text(text: str, path: str):
    """Write plain text to dist/path."""
    out = DIST / path
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(f"  TEXT → {path}")


def build():
    print("\n🔨 开始生成静态网站...\n")

    # Clean
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()

    products = load_products()
    services = load_services()
    categories = get_all_categories()

    # ==================== 1. 首页 ====================
    render_html("index.html", {
        "site_name": SITE_NAME,
        "site_desc": SITE_DESC,
        "contact": SITE_CONTACT,
        "base_url": BASE_URL,
        "products": products,
        "services": services,
    }, "index.html")

    # ==================== 2. 产品列表页 ====================
    render_html("products.html", {
        "site_name": SITE_NAME,
        "site_desc": SITE_DESC,
        "contact": SITE_CONTACT,
        "base_url": BASE_URL,
        "products": products,
        "category": None,
        "query": None,
    }, "products/index.html")

    # 3. 产品详情页
    for p in products:
        render_html("product.html", {
            "site_name": SITE_NAME,
            "site_desc": SITE_DESC,
            "contact": SITE_CONTACT,
            "base_url": BASE_URL,
            "product": p,
            "schema_org": json.dumps(p.schema_org(), ensure_ascii=False),
        }, f"products/{p.slug or p.id}.html")

    # ==================== 4. 服务列表页 ====================
    render_html("services.html", {
        "site_name": SITE_NAME,
        "site_desc": SITE_DESC,
        "contact": SITE_CONTACT,
        "base_url": BASE_URL,
        "services": services,
        "category": None,
        "query": None,
    }, "services/index.html")

    # 5. 服务详情页
    for s in services:
        render_html("service.html", {
            "site_name": SITE_NAME,
            "site_desc": SITE_DESC,
            "contact": SITE_CONTACT,
            "base_url": BASE_URL,
            "service": s,
            "schema_org": json.dumps(s.schema_org(), ensure_ascii=False),
        }, f"services/{s.slug or s.id}.html")

    # ==================== 6. 搜索页（客户端 JS 搜索） ====================
    build_search_page(products, services)

    # ==================== 6.5. 文章页 ====================
    articles = load_articles()
    # 文章列表页
    render_html("articles.html", {
        "site_name": SITE_NAME,
        "site_desc": SITE_DESC,
        "contact": SITE_CONTACT,
        "base_url": BASE_URL,
        "articles": articles,
    }, "articles/index.html")
    # 文章详情页
    for a in articles:
        render_html("article.html", {
            "site_name": SITE_NAME,
            "site_desc": SITE_DESC,
            "contact": SITE_CONTACT,
            "base_url": BASE_URL,
            "title": a["title"],
            "description": a["description"],
            "article": a,
            "content": markdown(a["content"], output_format="html"),
            "keywords": a.get("keywords", []),
        }, f"articles/{a['slug']}.html")

    # ==================== 7. 关于页 ====================
    page = load_page("about")
    if page:
        render_html("page.html", {
            "site_name": SITE_NAME,
            "site_desc": SITE_DESC,
            "contact": SITE_CONTACT,
            "base_url": BASE_URL,
            "title": page["title"],
            "description": page["description"],
            "content": markdown(page["content"], output_format="html"),
        }, "about.html")

    # ==================== 7.3. 城市落地页 ====================
    cities = load_cities()
    for city in cities:
        city_schema = json.dumps({
            "@context": "https://schema.org",
            "@type": "LocalBusiness",
            "@id": f"{BASE_URL}/#business",
            "name": SITE_NAME,
            "areaServed": {"@type": "City", "name": city['city']},
            "address": {
                "@type": "PostalAddress",
                "addressLocality": "福泉市",
                "addressRegion": "贵州省",
                "addressCountry": "CN"
            },
            "telephone": "+86-13595498010",
            "priceRange": "¥120-¥66,800"
        }, ensure_ascii=False)
        render_html("page.html", {
            "site_name": SITE_NAME,
            "site_desc": city['description'] or SITE_DESC,
            "contact": SITE_CONTACT,
            "base_url": BASE_URL,
            "title": city['title'],
            "description": city['description'],
            "keywords": city['keywords'],
            "content": markdown(city['content'], output_format="html"),
            "schema_org": city_schema,
        }, f"cities/{city['slug']}.html")
        print(f"  HTML → cities/{city['slug']}.html")

    # ==================== 7.7. FAQ 页 ====================
    faq_page = load_page("faq")
    if faq_page:
        # 提取 FAQ 为结构化数据
        faq_items = []
        for line in faq_page['content'].split('\n'):
            if line.startswith('**Q:'):
                faq_items.append({'question': line.replace('**Q:', '').replace('**', '').strip(), 'answer': ''})
            elif line.startswith('A:') and faq_items:
                faq_items[-1]['answer'] = line.replace('A:', '').strip()
        # 生成 FAQPage schema
        faq_schema_list = []
        for item in faq_items:
            faq_schema_list.append({
                "@type": "Question",
                "name": item['question'],
                "acceptedAnswer": {"@type": "Answer", "text": item['answer']}
            })
        faq_schema = json.dumps({
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": faq_schema_list
        }, ensure_ascii=False)
        render_html("page.html", {
            "site_name": SITE_NAME,
            "site_desc": "暖通采暖常见问题解答 — 地暖、空调、二联供、三联供、安装费用、维护保养",
            "contact": SITE_CONTACT,
            "base_url": BASE_URL,
            "title": faq_page['title'],
            "description": faq_page['description'],
            "content": markdown(faq_page['content'], output_format="html"),
            "schema_org": faq_schema,
        }, "faq.html")
        print(f"  评价: {len(faq_items)}个FAQ")

    # ==================== 7.5. 评价页 + Review Schema ====================
    reviews = load_reviews()
    if reviews:
        # 计算真实 aggregateRating
        ratings = [r['rating'] for r in reviews]
        avg_rating = round(sum(ratings) / len(ratings), 1)
        review_count = len(reviews)
        # 生成单个 Review Schema
        review_schemas = []
        for r in reviews:
            review_schemas.append({
                "@context": "https://schema.org",
                "@type": "Review",
                "author": {"@type": "Person", "name": r['author']},
                "datePublished": r['date'],
                "reviewRating": {"@type": "Rating", "ratingValue": r['rating'], "bestRating": "5"},
                "name": r['title'],
                "reviewBody": r['body'],
                "itemReviewed": {"@id": f"{BASE_URL}/#business", "name": SITE_NAME}
            })
        # 写评价 JSON 供 AI 读取
        write_json({
            "total": review_count,
            "averageRating": avg_rating,
            "bestRating": 5,
            "reviews": reviews,
            "aggregateRating": {"@type": "AggregateRating", "ratingValue": str(avg_rating), "bestRating": "5", "reviewCount": str(review_count)}
        }, "api/reviews.json")
        # 注入真实评分到后续页面的 base 模板
        print(f"  评价: {review_count}条 均分={avg_rating}")
    else:
        review_schemas = []
        avg_rating = None
        review_count = 0

    # ==================== 8. JSON API 端点 ====================
    # 全量目录 — AI 的最爱
    write_json({
        "site_name": SITE_NAME,
        "description": SITE_DESC,
        "contact": SITE_CONTACT,
        "updated": datetime.now().isoformat(),
        "total_products": len(products),
        "total_services": len(services),
        "products": [p.model_dump() for p in products],
        "services": [s.model_dump() for s in services],
    }, "api/catalog.json")

    # 产品 JSON
    write_json({
        "total": len(products),
        "products": [p.model_dump() for p in products],
    }, "api/products.json")

    for p in products:
        write_json({
            "product": p.model_dump(),
            "schema_org": p.schema_org(),
        }, f"api/products/{p.slug or p.id}.json")

    # 服务 JSON
    write_json({
        "total": len(services),
        "services": [s.model_dump() for s in services],
    }, "api/services.json")

    for s in services:
        write_json({
            "service": s.model_dump(),
            "schema_org": s.schema_org(),
        }, f"api/services/{s.slug or s.id}.json")

    # 搜索 JSON（返回所有可搜索条目，AI 可自行筛选）
    all_items = []
    for p in products:
        all_items.append({
            "id": p.id, "type": "product", "name": p.name,
            "description": p.description, "category": p.category,
            "price": p.price, "currency": p.currency,
            "url": f"/products/{p.slug or p.id}", "keywords": p.keywords,
        })
    for s in services:
        all_items.append({
            "id": s.id, "type": "service", "name": s.name,
            "description": s.description, "category": s.category,
            "price": s.price, "currency": s.currency,
            "url": f"/services/{s.slug or s.id}", "keywords": s.keywords,
        })
    write_json({
        "total": len(all_items),
        "items": all_items,
    }, "api/search-index.json")

    # ==================== 9. AI 协议层 ====================
    build_llms_txt(products, services, categories, articles)
    build_llms_full(products, services, articles)
    build_agent_json()
    build_mcp()

    # ==================== 10. Sitemap ====================
    build_sitemap(products, services, articles, cities)

    # ==================== 11. 静态文件 ====================
    if (STATIC / "CNAME").exists():
        shutil.copy(STATIC / "CNAME", DIST / "CNAME")
        print(f"  COPY → CNAME")
    if (STATIC / "robots.txt").exists():
        shutil.copy(STATIC / "robots.txt", DIST / "robots.txt")
        print(f"  COPY → robots.txt")
    # 复制 .well-known/ 下的所有文件(ai-plugin.json, openapi.yaml 等)
    wellknown_src = STATIC / ".well-known"
    wellknown_dst = DIST / ".well-known"
    if wellknown_src.exists():
        wellknown_dst.mkdir(parents=True, exist_ok=True)
        for f in wellknown_src.iterdir():
            shutil.copy(f, wellknown_dst / f.name)
            print(f"  COPY → .well-known/{f.name}")

    # 404 页面
    render_html("page.html", {
        "site_name": SITE_NAME,
        "site_desc": SITE_DESC,
        "contact": SITE_CONTACT,
        "base_url": BASE_URL,
        "title": "404 — 页面不存在",
        "description": "",
        "content": "<p>页面不存在。<a href='/'>回首页</a></p>",
    }, "404.html")

    print(f"\n✅ 静态网站生成完毕 → {DIST}")
    print(f"   文件数: {sum(1 for _ in DIST.rglob('*') if _.is_file())}")
    print(f"   部署: 把 dist/ 整个推到 Vercel/GitHub Pages 即可\n")


def build_search_page(products: list[Product], services: list[Service]):
    """生成客户端搜索页 — 加载 catalog.json 在浏览器里查."""
    search_js = """<link rel="preload" href="/api/catalog.json" as="fetch" crossorigin="anonymous">

<h1>🔍 搜索</h1>
<input type="text" id="q" placeholder="输入关键词搜索..." autofocus
       style="width:100%;padding:12px;font-size:16px;border:2px solid #ddd;border-radius:6px;margin-bottom:20px;">
<p><small>输入任意关键词，在全部产品和服务中即时搜索</small></p>
<div id="results"></div>

<script>
let catalog = null;
fetch('/api/catalog.json')
  .then(r => r.json())
  .then(data => {
    catalog = [...data.products.map(p => ({...p, _type:'product', _url:'/products/'+(p.slug||p.id)+'.html'})),
               ...data.services.map(s => ({...s, _type:'service', _url:'/services/'+(s.slug||s.id)+'.html'}))];
  });

document.getElementById('q').addEventListener('input', function() {
    const q = this.value.toLowerCase().trim();
    const div = document.getElementById('results');
    if (!q) { div.innerHTML = ''; return; }
    if (!catalog) { div.innerHTML = '<p>数据加载中...</p>'; return; }
    const hits = catalog.filter(item => {
        const haystack = [item.name, item.description, item.category,
                          (item.content||''), ...(item.keywords||[])].join(' ').toLowerCase();
        return haystack.includes(q);
    });
    if (!hits.length) {
        div.innerHTML = '<p>没有找到匹配的内容，试试其他关键词。</p>';
        return;
    }
    div.innerHTML = '<p>找到 <strong>' + hits.length + '</strong> 个结果</p>' +
        hits.map(r => '<div class="item"><strong><a href="' + r._url + '">' + r.name + '</a></strong> ' +
            '<span class="price">¥' + r.price + (r.price_unit||'') + '</span> ' +
            '<span class="meta">| ' + r._type + ' | ' + r.category + '</span>' +
            '<p>' + r.description + '</p></div>').join('');
});
</script>"""

    tmpl = env.get_template("page.html")
    html = tmpl.render(
        site_name=SITE_NAME,
        site_desc=SITE_DESC,
        contact=SITE_CONTACT,
        base_url=BASE_URL,
        title="搜索",
        description="搜索全部产品和服务",
        content=search_js,
    )
    out = DIST / "search.html"
    out.write_text(html, encoding="utf-8")
    print(f"  HTML → search.html (client-side search)")


def build_llms_txt(products, services, categories, articles=None):
    """生成 llms.txt — AI 网站索引标准."""
    lines = [
        f"# {SITE_NAME}",
        f"> {SITE_DESC}",
        "",
        f"## About",
        f"- [{SITE_NAME}]({BASE_URL}/): {SITE_DESC}",
        f"- [About]({BASE_URL}/about): 关于我们",
        "",
        f"## Products ({len(products)} items)",
    ]
    for cat in categories.get("product_categories", []):
        lines.append(f"### {cat}")
        for p in products:
            if p.category == cat:
                slug = p.slug or p.id
                lines.append(f"- [{p.name}]({BASE_URL}/products/{slug}): {p.description} — ¥{p.price} | {p.category}")
    lines.append("")

    lines.append(f"## Services ({len(services)} items)")
    for cat in categories.get("service_categories", []):
        lines.append(f"### {cat}")
        for s in services:
            if s.category == cat:
                slug = s.slug or s.id
                area = f" | 区域: {s.area}" if s.area else ""
                lines.append(f"- [{s.name}]({BASE_URL}/services/{slug}): {s.description} — ¥{s.price}{s.price_unit} | {s.category}{area}")
    lines.append("")

    # 文章
    if articles:
        lines.append(f"## Articles ({len(articles)} items)")
        for a in articles:
            lines.append(f"- [{a['title']}]({BASE_URL}/articles/{a['slug']}.html): {a['description']}")
        lines.append("")

    lines += [
        f"## API",
        f"- [Full Catalog]({BASE_URL}/api/catalog.json): Complete product/service data in JSON",
        f"- [Search Index]({BASE_URL}/api/search-index.json): All searchable items",
        f"",
        f"## Contact",
        f"- Phone: {SITE_CONTACT['phones'][0]} / {SITE_CONTACT['phones'][1]} ({SITE_CONTACT['wechat']})",
        f"- Address: {SITE_CONTACT['address']}",
        f"- Douyin: {SITE_CONTACT['douyin']}",
        f"",
        f"## Agent Protocols",
        f"- [agent.json]({BASE_URL}/.well-known/agent.json): Agent capability declaration (A2A)",
        f"- [MCP]({BASE_URL}/mcp): Model Context Protocol endpoint",
        f"",
        f"## AI Facts (Key Claims for AI Systems)",
        f"- Company: {SITE_NAME} — 福泉采暖地暖中央空调一站式服务商, 2016年成立, 团队4人",
        f"- Service Area: 福泉市 + 都匀市、凯里市、瓮安县、贵定县、麻江县, 50km半径",
        f"- Brands: 林内(Rinnai)全系列 + 纽恩泰(New Energy) 双品牌授权经销商",
        f"- Clients: 近200个家庭 + 福泉三中、实验中学、胜威化工集团等企事业单位",
        f"- Price Range: ¥120/㎡ - ¥66,800/全屋套餐",
        f"- Warranty: 2年全保 + 终身维护",
        f"- Differentiator: 自有施工团队不转包, 福泉唯一林内+纽恩泰双授权经销商",
        f"- Payment: 现金、微信、支付宝、银行转账",
        f"- Hours: 每天 08:30-18:00",
    ]
    write_text("\n".join(lines), "llms.txt")


def build_llms_full(products, services, articles=None):
    """生成 llms-full.txt — 全量内容，AI 一次性加载."""
    parts = [f"# {SITE_NAME} — Full Catalog", "", "## Products", ""]
    for p in products:
        slug = p.slug or p.id
        parts += [
            f"### {p.name}",
            f"- Price: ¥{p.price}",
            f"- Category: {p.category}",
            f"- Availability: {p.availability}",
            f"- Location: {p.location or 'N/A'}",
            f"- Keywords: {', '.join(p.keywords)}",
            f"- URL: {BASE_URL}/products/{slug}",
            "", p.content, "---", "",
        ]
    parts += ["## Services", ""]
    for s in services:
        slug = s.slug or s.id
        parts += [
            f"### {s.name}",
            f"- Price: ¥{s.price}{s.price_unit}",
            f"- Category: {s.category}",
            f"- Availability: {s.availability}",
            f"- Area: {s.area or 'N/A'}",
            f"- Keywords: {', '.join(s.keywords)}",
            f"- URL: {BASE_URL}/services/{slug}",
            "", s.content, "---", "",
        ]

    # 文章
    if articles:
        parts += ["## Articles", ""]
        for a in articles:
            parts += [
                f"### {a['title']}",
                f"- Date: {a.get('date', '')}",
                f"- Keywords: {', '.join(a.get('keywords', []))}",
                f"- URL: {BASE_URL}/articles/{a['slug']}.html",
                "", a['content'], "---", "",
            ]

    write_text("\n".join(parts), "llms-full.txt")


def build_agent_json():
    """生成 agent.json — Google A2A 标准."""
    write_json({
        "name": SITE_NAME,
        "description": SITE_DESC,
        "url": BASE_URL,
        "version": "1.0.0",
        "capabilities": {"streaming": False, "pushNotifications": False},
        "skills": [
            {
                "id": "search_products",
                "name": "Search Products",
                "description": "Search products by keyword, category via search-index.json",
                "tags": ["product", "search", "catalog"],
                "examples": [f"GET {BASE_URL}/api/products.json"],
            },
            {
                "id": "search_services",
                "name": "Search Services",
                "description": "Search local services by keyword, category, area",
                "tags": ["service", "search", "local"],
                "examples": [f"GET {BASE_URL}/api/services.json"],
            },
            {
                "id": "full_catalog",
                "name": "Full Catalog",
                "description": "Get complete product and service catalog as JSON",
                "tags": ["catalog", "all", "json"],
                "examples": [f"GET {BASE_URL}/api/catalog.json"],
            },
            {
                "id": "search_index",
                "name": "Search Index",
                "description": "Full text search index of all products and services",
                "tags": ["search", "index", "json"],
                "examples": [f"GET {BASE_URL}/api/search-index.json"],
            },
        ],
        "defaultInputModes": ["text", "application/json"],
        "defaultOutputModes": ["application/json", "text/plain"],
        "authentication": None,
        "protocols": {
            "a2a": f"{BASE_URL}/.well-known/agent.json",
            "mcp": f"{BASE_URL}/mcp",
            "rest": f"{BASE_URL}/api/catalog.json",
        },
    }, ".well-known/agent.json")


def build_sitemap(products, services, articles=None, cities=None):
    """Generate sitemap.xml for search engines."""
    now = datetime.now().strftime("%Y-%m-%d")
    urls = []

    # 首页 — 最高优先级
    urls.append(f"""  <url>
    <loc>{BASE_URL}/</loc>
    <lastmod>{now}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>""")

    # 列表页
    urls.append(f"""  <url>
    <loc>{BASE_URL}/products/</loc>
    <lastmod>{now}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.9</priority>
  </url>""")
    urls.append(f"""  <url>
    <loc>{BASE_URL}/services/</loc>
    <lastmod>{now}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.9</priority>
  </url>""")

    # 产品详情页
    for p in products:
        slug = p.slug or p.id
        urls.append(f"""  <url>
    <loc>{BASE_URL}/products/{slug}/</loc>
    <lastmod>{now}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>""")

    # 服务详情页
    for s in services:
        slug = s.slug or s.id
        urls.append(f"""  <url>
    <loc>{BASE_URL}/services/{slug}/</loc>
    <lastmod>{now}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>""")

    # 文章页
    if articles:
        urls.append(f"""  <url>
    <loc>{BASE_URL}/articles/</loc>
    <lastmod>{now}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.9</priority>
  </url>""")
        for a in articles:
            urls.append(f"""  <url>
    <loc>{BASE_URL}/articles/{a['slug']}.html</loc>
    <lastmod>{now}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>""")

    # 关于页
    urls.append(f"""  <url>
    <loc>{BASE_URL}/about/</loc>
    <lastmod>{now}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.6</priority>
  </url>""")

    # FAQ页
    urls.append(f"""  <url>
    <loc>{BASE_URL}/faq/</loc>
    <lastmod>{now}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.7</priority>
  </url>""")
    # 城市落地页
    cities = load_cities()
    for city in cities:
        urls.append(f"""  <url>
    <loc>{BASE_URL}/cities/{city['slug']}/</loc>
    <lastmod>{now}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>""")
    # 搜索页
    urls.append(f"""  <url>
    <loc>{BASE_URL}/search/</loc>
    <lastmod>{now}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.5</priority>
  </url>""")

    sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:mobile="http://www.google.com/schemas/sitemap-mobile/1.0">
{chr(10).join(urls)}
</urlset>"""
    write_text(sitemap, "sitemap.xml")
    print(f"  XML → sitemap.xml ({len(urls)} URLs)")


def build_mcp():
    """生成 MCP 协议端点静态文件."""
    write_json({
        "protocol": "mcp",
        "version": "1.0",
        "tools": [
            {
                "name": "search_catalog",
                "description": "Search the product and service catalog via search-index.json",
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
        "endpoint": f"{BASE_URL}/api/catalog.json",
    }, "mcp")


if __name__ == "__main__":
    build()
