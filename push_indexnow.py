"""
IndexNow 自动推送 — 无需注册，直接通知 Bing + Yandex 收录
工作原理: 生成密钥文件 → 批量 ping 搜索引擎 → 加速索引
"""
import requests
import re
import uuid

SITE = "fqnuantong.com"
KEY_FILE = f"{SITE}/{uuid.uuid4().hex}.txt"
API_KEY = KEY_FILE.split("/")[-1].replace(".txt", "")

# 1. 从 sitemap 提取URL
with open('dist/sitemap.xml', 'r', encoding='utf-8') as f:
    urls = re.findall(r'<loc>(.*?)</loc>', f.read())

# 替换域名
urls = [u.replace('http://fqnuantong.com', f'https://{SITE}') for u in urls]

print(f'IndexNow 推送 {len(urls)} 个URL到 Bing + Yandex...')
print(f'API Key: {API_KEY[:12]}...')
print()

# 2. 生成密钥文件 (放 dist 根目录, 部署后生效)
key_path = f'dist/{KEY_FILE.split("/")[-1]}'
with open(key_path, 'w') as f:
    f.write(API_KEY)
print(f'密钥文件: {key_path}')

# 3. 批量推送 (Bing 单次最多500个, 我们26个一次搞定)
payload = {
    "host": SITE,
    "key": API_KEY,
    "keyLocation": f"https://{SITE}/{KEY_FILE.split('/')[-1]}",
    "urlList": urls
}

# 推送到 Bing
try:
    resp = requests.post(
        "https://www.bing.com/indexnow",
        json=payload,
        headers={"Content-Type": "application/json; charset=utf-8"},
        timeout=15
    )
    print(f'Bing IndexNow: {resp.status_code} - {resp.text[:200]}')
except Exception as e:
    print(f'Bing IndexNow 错误: {e}')

# 推送到 Yandex (可选, 扩大覆盖)
try:
    resp = requests.post(
        "https://yandex.com/indexnow",
        json=payload,
        headers={"Content-Type": "application/json; charset=utf-8"},
        timeout=15
    )
    print(f'Yandex IndexNow: {resp.status_code} - {resp.text[:200]}')
except Exception as e:
    print(f'Yandex IndexNow 错误: {e}')

print()
print('注意: 需要重新部署网站使密钥文件生效!')
print(f'验证: https://{SITE}/{KEY_FILE.split("/")[-1]} 应显示一串字符')
