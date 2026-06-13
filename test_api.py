"""Quick test of all AI-first endpoints."""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import urllib.request
import urllib.parse
import json


def get(url, accept=None):
    headers = {}
    if accept:
        headers["Accept"] = accept
    # Percent-encode non-ASCII characters in URL
    scheme, netloc, path, query, fragment = urllib.parse.urlsplit(url)
    path = urllib.parse.quote(path, safe='/:@')
    query = urllib.parse.quote(query, safe='=&')
    url = urllib.parse.urlunsplit((scheme, netloc, path, query, fragment))
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        ct = resp.headers.get("Content-Type", "")
        data = resp.read().decode("utf-8")
        return ct, data


BASE = "http://localhost:8000"

# 1. llms.txt
ct, data = get(f"{BASE}/llms.txt")
print("=== 1. llms.txt (first 500 chars) ===")
print(data[:500])
print()

# 2. catalog.json
ct, data = get(f"{BASE}/api/catalog.json", "application/json")
j = json.loads(data)
print("=== 2. catalog.json ===")
print(f"Site: {j['site_name']}")
print(f"Products: {j['total_products']}, Services: {j['total_services']}")
for p in j["products"]:
    print(f"  [Product] {p['name']}: {p['price']} CNY — {p['description']}")
for s in j["services"]:
    area = s.get("area", "N/A")
    unit = s.get("price_unit", "")
    print(f"  [Service] {s['name']}: {s['price']} CNY{unit} — {s['description']} (Area: {area})")
print()

# 3. Search
ct, data = get(f"{BASE}/search?q=采暖", "application/json")
j = json.loads(data)
print(f"=== 3. Search '采暖': {j['total']} results ===")
for r in j["results"]:
    print(f"  [{r['type']}] {r['name']}: {r['description'][:60]}")
print()

# 4. Content negotiation: JSON vs HTML
_, json_data = get(f"{BASE}/products/floor-heating", "application/json")
_, html_data = get(f"{BASE}/products/floor-heating", "text/html")
print(f"=== 4. Content Negotiation ===")
print(f"JSON response: {len(json_data)} bytes")
print(f"HTML response: {len(html_data)} bytes (has <!DOCTYPE>: {'<!DOCTYPE html>' in html_data})")
print()

# 5. agent.json
ct, data = get(f"{BASE}/.well-known/agent.json")
j = json.loads(data)
print(f"=== 5. agent.json ===")
print(f"Name: {j['name']}")
print(f"Skills: {[s['id'] for s in j['skills']]}")
print(f"Protocols: {list(j['protocols'].keys())}")
print()

# 6. MCP info
ct, data = get(f"{BASE}/mcp")
j = json.loads(data)
print(f"=== 6. MCP ===")
print(f"Protocol: {j['protocol']} v{j['version']}")
print(f"Tools: {[t['name'] for t in j['tools']]}")
print()

# 7. Services by area
ct, data = get(f"{BASE}/services?area=北京", "application/json")
j = json.loads(data)
print(f"=== 7. Services in 北京: {j['total']} results ===")
for s in j["services"]:
    print(f"  {s['name']}: {s['price']} CNY{s.get('price_unit','')}")

print()
print("=== ALL TESTS PASSED ===")
