"""
ping_search_engines.py — 网站更新后通知搜索引擎来抓取
=====================================================
用法: python ping_search_engines.py
在每次部署后运行，主动通知百度/Google/Bing 有新内容。
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import urllib.request
import urllib.parse

SITEMAP_URL = "https://g-2026-xhx.github.io/nuanju/sitemap.xml"
SITE_URL = "https://g-2026-xhx.github.io/nuanju"

# ⚠️ 去百度站长平台 https://ziyuan.baidu.com/ 获取你的 token 后填入
BAIDU_API_TOKEN = ""
BAIDU_SITE = "https://g-2026-xhx.github.io"

# ⚠️ 去 Bing Webmaster https://www.bing.com/webmasters 获取 API Key
INDEXNOW_KEY = ""
INDEXNOW_KEY_LOCATION = "https://g-2026-xhx.github.io/nuanju/{key}.txt"


def ping_google():
    """通知 Google 重新抓取 sitemap."""
    url = f"https://www.google.com/ping?sitemap={urllib.parse.quote(SITEMAP_URL, safe='')}"
    try:
        req = urllib.request.Request(url, method="GET")
        req.add_header("User-Agent", "nuanju-seo-bot/1.0")
        resp = urllib.request.urlopen(req, timeout=10)
        print(f"✅ Google ping: HTTP {resp.status}")
    except Exception as e:
        print(f"❌ Google ping 失败: {e}")


def ping_baidu():
    """通过百度站长 API 提交 sitemap."""
    if not BAIDU_API_TOKEN:
        print("⚠️  百度 API Token 未配置，跳过。获取方法见下方说明。")
        return
    url = f"http://data.zz.baidu.com/urls?site={BAIDU_SITE}&token={BAIDU_API_TOKEN}"
    # 提交 sitemap URL
    data = SITEMAP_URL.encode("utf-8")
    try:
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Content-Type", "text/plain")
        resp = urllib.request.urlopen(req, timeout=10)
        result = resp.read().decode("utf-8")
        print(f"✅ 百度推送: {result}")
    except Exception as e:
        print(f"❌ 百度推送失败: {e}")


def ping_indexnow():
    """通过 IndexNow 协议通知 Bing/Yandex/Naver."""
    if not INDEXNOW_KEY:
        print("⚠️  IndexNow Key 未配置，跳过。")
        return

    # 列出所有需要通知的 URL
    urls = [
        f"{SITE_URL}/",
        f"{SITE_URL}/products/",
        f"{SITE_URL}/services/",
        f"{SITE_URL}/about/",
        f"{SITE_URL}/products/floor-heating/",
        f"{SITE_URL}/products/rinnai-boiler-package/",
        f"{SITE_URL}/products/new-energy-air-package/",
        f"{SITE_URL}/products/rinnai-air-package/",
        f"{SITE_URL}/products/new-energy-2in1-package/",
        f"{SITE_URL}/products/rinnai-dual-energy-3in1/",
        f"{SITE_URL}/services/design-plan/",
        f"{SITE_URL}/services/inspection/",
    ]

    import json
    data = json.dumps({
        "host": "g-2026-xhx.github.io",
        "key": INDEXNOW_KEY,
        "keyLocation": INDEXNOW_KEY_LOCATION.format(key=INDEXNOW_KEY),
        "urlList": urls,
    }).encode("utf-8")

    indexnow_url = "https://api.indexnow.org/IndexNow"
    try:
        req = urllib.request.Request(indexnow_url, data=data, method="POST")
        req.add_header("Content-Type", "application/json; charset=utf-8")
        resp = urllib.request.urlopen(req, timeout=10)
        print(f"✅ IndexNow: HTTP {resp.status}")
    except Exception as e:
        print(f"❌ IndexNow 失败: {e}")


def print_baidu_guide():
    """打印百度站长平台注册指南."""
    print("""
╔══════════════════════════════════════════════════════════╗
║          📋 百度站长平台注册步骤（5分钟搞定）              ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  1. 打开 https://ziyuan.baidu.com/                       ║
║  2. 点击「立即注册」，用手机号注册                        ║
║  3. 登录后点击「添加站点」                                ║
║  4. 站点域名填写: g-2026-xhx.github.io                   ║
║     ⚠️ 选「站点域名」类型，不要选「网站域名」             ║
║  5. 验证方式选「HTML标签验证」                            ║
║     → 复制那行 <meta name="baidu-site-verification"...    ║
║     → 把 codeva-xxxxxxxx 后面的码告诉我                   ║
║  6. 验证通过后，进入「普通收录」→「API提交」              ║
║     → 复制接口调用地址中的 token 告诉我                   ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
""")


def print_google_guide():
    """打印 Google Search Console 注册指南."""
    print("""
╔══════════════════════════════════════════════════════════╗
║       📋 Google Search Console 注册步骤（5分钟搞定）       ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  1. 打开 https://search.google.com/search-console        ║
║  2. 用 Google 账号登录（没有就注册一个）                  ║
║  3. 点击「添加资源」选「网址前缀」                        ║
║  4. 输入: https://g-2026-xhx.github.io/nuanju/           ║
║  5. 验证方式选「HTML标记」                                ║
║     → 复制 <meta name="google-site-verification"...       ║
║     → 把 content="..." 里面的值告诉我                     ║
║  6. 验证通过后 → 左侧「站点地图」→ 提交 sitemap.xml       ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
""")


def print_bing_guide():
    """打印 Bing Webmaster 注册指南."""
    print("""
╔══════════════════════════════════════════════════════════╗
║         📋 Bing Webmaster 注册步骤（3分钟搞定）            ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  1. 打开 https://www.bing.com/webmasters                 ║
║  2. 用 Microsoft 账号登录                                 ║
║  3. 点击「添加网站」                                      ║
║  4. 输入: https://g-2026-xhx.github.io/nuanju/           ║
║  5. 验证方式选「Meta Tag」                                ║
║     → 把 content 值告诉我                                 ║
║  6. 验证通过后 → 左侧「站点地图」→ 提交 sitemap.xml       ║
║                                                          ║
║  💡 小技巧: Bing 可以直接导入 Google Search Console 数据  ║
║     如果先注册了 Google，Bing 可以一键导入！               ║
╚══════════════════════════════════════════════════════════╝
""")


if __name__ == "__main__":
    print("🔔 通知搜索引擎抓取更新...\n")
    ping_google()
    ping_baidu()
    ping_indexnow()
    print("\n---")
    print_baidu_guide()
    print_google_guide()
    print_bing_guide()
