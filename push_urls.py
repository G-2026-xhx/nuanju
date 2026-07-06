"""
百度主动推送 — 将26个URL推送给百度收录
使用: python push_urls.py
需要先在百度站长平台获取API密钥: https://ziyuan.baidu.com/linksubmit/
"""
import requests
import re

# 从 sitemap.xml 提取所有 URL
with open('dist/sitemap.xml', 'r', encoding='utf-8') as f:
    sitemap = f.read()

urls = re.findall(r'<loc>(.*?)</loc>', sitemap)

print(f'找到 {len(urls)} 个URL:')
for u in urls:
    print(f'  {u}')

# ===== 填入你的百度站长API地址 =====
# 在 https://ziyuan.baidu.com/linksubmit/ 获取
BAIDU_API = "http://data.zz.baidu.com/urls?site=g-2026-xhx.github.io&token=YOUR_TOKEN_HERE"

if "YOUR_TOKEN" in BAIDU_API:
    print(f'\n⚠ 请先在百度站长平台获取API token')
    print(f'  1. 登录 https://ziyuan.baidu.com/')
    print(f'  2. 添加站点 g-2026-xhx.github.io')
    print(f'  3. 验证通过后，进入"链接提交"页面')
    print(f'  4. 复制API地址中的token参数')
    print(f'  5. 替换本脚本中 BAIDU_API 的 token=YOUR_TOKEN')
    print(f'\n  可以手动提交: 将 sitemap.xml URL 贴入百度站长"提交sitemap"')
else:
    resp = requests.post(BAIDU_API, data='\n'.join(urls))
    print(f'\n推送结果: {resp.json()}')
