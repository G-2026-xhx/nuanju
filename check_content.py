"""Quick check that all content files parse correctly."""
import frontmatter
from pathlib import Path

for f in sorted(Path('content/products').glob('*.md')):
    try:
        post = frontmatter.load(f)
        meta = post.metadata
        name = meta.get('name', 'MISSING')
        price = meta.get('price', 'MISSING')
        cat = meta.get('category', 'MISSING')
        desc = meta.get('description', 'MISSING')[:50]
        print(f'OK 产品: {name} | {price} | {cat} | {desc}')
    except Exception as e:
        print(f'FAIL {f.name}: {e}')

for f in sorted(Path('content/services').glob('*.md')):
    try:
        post = frontmatter.load(f)
        meta = post.metadata
        name = meta.get('name', 'MISSING')
        price = meta.get('price', 'MISSING')
        cat = meta.get('category', 'MISSING')
        desc = meta.get('description', 'MISSING')[:50]
        print(f'OK 服务: {name} | {price} | {cat} | {desc}')
    except Exception as e:
        print(f'FAIL {f.name}: {e}')
