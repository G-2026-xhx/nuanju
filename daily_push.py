"""
暖通网站每日运营脚本 v1
================================
独立运行, 不依赖 Claude 会话。
由 Windows 计划任务每天调用一次。

用法:
  python daily_push.py          # 发今天的
  python daily_push.py --dry-run  # 测试模式, 不实际操作

依赖: Python 3.8+, git (在 PATH 中)
"""

import os, sys, json, hashlib, re, shutil
import subprocess, time
from datetime import datetime
import urllib.request
import argparse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FEED_DIR = os.path.join(BASE_DIR, 'feed')
POOL_DIR = os.path.join(BASE_DIR, 'content_pool')
PUBLISHED_FILE = os.path.join(BASE_DIR, 'published.json')
LOG_FILE = os.path.join(BASE_DIR, 'push.log')

INDEXNOW_KEY = 'db789fd6ecbf41b4b9dff23092ad293f'
INDEXNOW_HOST = 'fqnuantong.com'
INDEXNOW_KEY_LOCATION = f'https://{INDEXNOW_HOST}/{INDEXNOW_KEY}.txt'
SITE_URL = f'https://{INDEXNOW_HOST}'
GITEE_URL = 'https://gitee.com/fuquan-meijia-precision-hvac_0/nuanju.git'
GITHUB_REMOTE = 'origin'
GITHUB_BRANCH = 'gh-pages'


def log(msg):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f'[{ts}] {msg}'
    print(line, flush=True)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(line + '\n')


def load_published():
    if os.path.exists(PUBLISHED_FILE):
        with open(PUBLISHED_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_published(data):
    with open(PUBLISHED_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_next_article():
    """从内容池选下一篇未发布的, 池空则从头循环"""
    published = set(load_published())
    files = sorted([f for f in os.listdir(POOL_DIR) if f.endswith('.html')])
    available = [f for f in files if f not in published]
    if not available:
        log('内容池已循环, 从头开始')
        save_published([])
        available = files
    return available[0] if available else None


def fill_template(pool_file):
    """替换模板占位符, 返回 (文件名, HTML内容)"""
    today = datetime.now()
    date_str = today.strftime('%Y%m%d')
    date_iso = today.strftime('%Y-%m-%d')
    hex_suffix = hashlib.md5(date_str.encode()).hexdigest()[:6]
    filename = f'{date_str}-{hex_suffix}.html'

    with open(os.path.join(POOL_DIR, pool_file), 'r', encoding='utf-8') as f:
        content = f.read()

    content = content.replace('{{DATE}}', date_str)
    content = content.replace('{{DATE_ISO}}', date_iso)
    content = content.replace('{{FILENAME_HEX}}', hex_suffix)
    content = content.replace('{{FILENAME}}', filename)
    content = content.replace('{{YEAR}}', today.strftime('%Y'))

    return filename, content


def update_feed_index(filename, title):
    """feed/index.html — 顶部插入新条目"""
    path = os.path.join(FEED_DIR, 'index.html')
    with open(path, 'r', encoding='utf-8') as f:
        html = f.read()
    today = datetime.now().strftime('%Y-%m-%d')
    entry = f'<li><a href="/feed/{filename}">{title}</a> <time datetime="{today}">{today}</time></li>'
    html = html.replace('<li>', entry + '<li>', 1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)


def update_faq_json(filename, faqs):
    """feed/faq.json — 尾部追加新问答"""
    path = os.path.join(FEED_DIR, 'faq.json')
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    today = datetime.now().strftime('%Y-%m-%d')
    for q, a in faqs:
        data.append({'date': today, 'q': q, 'a': a, 'url': f'{SITE_URL}/feed/{filename}'})
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def update_llms_feed(filename, title, faqs):
    """feed/llms-feed.txt — 头部插入新块"""
    path = os.path.join(FEED_DIR, 'llms-feed.txt')
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    today = datetime.now().strftime('%Y-%m-%d')
    block = f'## {today}\nURL: {SITE_URL}/feed/{filename}\n标题: {title}\n\n'
    for q, a in faqs:
        block += f'Q: {q}\nA: {a}\n'
    block += '\n---\n'
    with open(path, 'w', encoding='utf-8') as f:
        f.write(block + content)


def extract_meta(html):
    """从 HTML 提取标题和 FAQ 列表"""
    m = re.search(r'<title>(.+?)(?:\s*\|\s*.+)?</title>', html)
    title = m.group(1).strip() if m else '未知'
    faqs = []
    m_ld = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
    if m_ld:
        try:
            ld = json.loads(m_ld.group(1))
            for item in (ld if isinstance(ld, list) else [ld]):
                if item.get('@type') == 'FAQPage':
                    for e in item.get('mainEntity', []):
                        q = e.get('name', '')
                        a = e.get('acceptedAnswer', {}).get('text', '')
                        if q and a:
                            faqs.append((q, a))
        except Exception:
            pass
    return title, faqs


def run_git(*args, cwd=None):
    """运行 git 命令, 返回 (returncode, stdout, stderr)"""
    cwd = cwd or BASE_DIR
    try:
        r = subprocess.run(['git'] + list(args), cwd=cwd,
                           capture_output=True, text=True, timeout=60,
                           encoding='utf-8', errors='replace')
        return r.returncode, (r.stdout or '').strip(), (r.stderr or '').strip()
    except Exception as e:
        return 1, '', str(e)


def git_commit_push(filename, title, dry_run=False):
    """提交并推送到 GitHub Pages"""
    if dry_run:
        log(f'  [DRY] 跳过 git commit+push')
        return True

    # 确保在 gh-pages 分支
    code, out, err = run_git('branch', '--show-current')
    if 'gh-pages' not in out:
        code, _, err = run_git('checkout', 'gh-pages')
        if code != 0:
            log(f'  切换 gh-pages 失败: {err}')
            return False

    code, _, err = run_git('add', 'feed/')
    if code != 0:
        log(f'  git add 失败: {err}')
        return False

    code, _, err = run_git('commit', '-m', f'每日内容更新: {title}')
    # commit 可能因无变更而失败, 这是正常的(比如脚本跑重复了)
    if code != 0 and 'nothing to commit' not in err:
        log(f'  git commit: {err}')

    code, out, err = run_git('push', GITHUB_REMOTE, GITHUB_BRANCH)
    if code == 0:
        log(f'  GitHub push 成功')
        return True
    else:
        log(f'  GitHub push 失败: {err}')
        return False


def sync_gitee(dry_run=False):
    """clone Gitee gitee-deploy 分支, 覆盖 feed/, 推送"""
    if dry_run:
        log(f'  [DRY] 跳过 Gitee 同步')
        return True

    tmp = os.path.join(BASE_DIR, '.gitee_tmp')
    try:
        # 清理残留
        if os.path.exists(tmp):
            shutil.rmtree(tmp, ignore_errors=True)

        code, _, err = run_git('clone', '--depth', '1', '--branch', 'gitee-deploy',
                               GITEE_URL, tmp, cwd=BASE_DIR)
        if code != 0:
            log(f'  Gitee clone 失败: {err}')
            return False

        # 覆盖 feed/
        feed_tmp = os.path.join(tmp, 'feed')
        os.makedirs(feed_tmp, exist_ok=True)
        for f in os.listdir(FEED_DIR):
            shutil.copy2(os.path.join(FEED_DIR, f), feed_tmp)

        # 提交推送
        run_git('add', 'feed/', cwd=tmp)
        code, _, err = run_git('commit', '-m',
                               f'每日同步 {datetime.now().strftime("%m/%d")}', cwd=tmp)
        # commit 可能无变更, 正常

        code, _, err = run_git('push', 'origin', 'gitee-deploy', cwd=tmp)
        if code == 0:
            log(f'  Gitee push 成功')
        else:
            log(f'  Gitee push 结果: {err[:80] if err else "ok"}')
        return True
    except Exception as e:
        log(f'  Gitee 同步异常: {e}')
        return False
    finally:
        if os.path.exists(tmp):
            shutil.rmtree(tmp, ignore_errors=True)


def indexnow_push(urls, dry_run=False):
    """POST IndexNow API"""
    if dry_run:
        log(f'  [DRY] 跳过 IndexNow ({len(urls)} URLs)')
        return

    data = json.dumps({
        'host': INDEXNOW_HOST,
        'key': INDEXNOW_KEY,
        'keyLocation': INDEXNOW_KEY_LOCATION,
        'urlList': urls
    }).encode('utf-8')

    for engine, api_url in [('Bing', 'https://www.bing.com/indexnow'),
                             ('Yandex', 'https://yandex.com/indexnow')]:
        try:
            req = urllib.request.Request(api_url, data=data,
                                         headers={'Content-Type': 'application/json'})
            resp = urllib.request.urlopen(req, timeout=15)
            log(f'  IndexNow {engine}: {resp.status}')
        except Exception as e:
            log(f'  IndexNow {engine} 失败: {e}')


def verify_deploy(filename, dry_run=False):
    """验证 GitHub Pages 能访问到新文章"""
    if dry_run:
        log(f'  [DRY] 跳过访问验证')
        return True
    url = f'https://g-2026-xhx.github.io/nuanju/feed/{filename}'
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            resp = urllib.request.urlopen(req, timeout=15)
            if resp.status == 200:
                log(f'  GitHub Pages 验证: 200 OK')
                return True
        except Exception as e:
            if attempt < 2:
                time.sleep(2)
            else:
                log(f'  验证警告: {e}')
    return False


def main():
    parser = argparse.ArgumentParser(description='暖通网站每日运营')
    parser.add_argument('--dry-run', action='store_true', help='测试模式, 不实际操作')
    args = parser.parse_args()

    log(f'===== 暖通每日运营开始 {"[DRY-RUN]" if args.dry_run else ""} =====')

    # 1. 幂等检查: 今天已发则跳过
    today_str = datetime.now().strftime('%Y%m%d')
    existing = [f for f in os.listdir(FEED_DIR)
                if f.startswith(today_str) and f.endswith('.html')]
    if existing:
        log(f'今天已发布 ({existing[0]}), 跳过')
        return 0

    # 2. 选题
    pool_file = get_next_article()
    if not pool_file:
        log('错误: 内容池为空, 请先填充 content_pool/ 目录')
        return 1
    log(f'选题: {pool_file}')

    # 3. 生成文章
    filename, content = fill_template(pool_file)
    filepath = os.path.join(FEED_DIR, filename)
    if not args.dry_run:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    log(f'文章生成: {filename} ({len(content)} bytes)')

    # 4. 提取元数据
    title, faqs = extract_meta(content)
    log(f'标题: {title}  FAQ: {len(faqs)} 条')

    # 5. 更新三个索引
    if not args.dry_run:
        update_feed_index(filename, title)
        update_faq_json(filename, faqs)
        update_llms_feed(filename, title, faqs)
        log('索引文件已更新')
    else:
        log('[DRY] 跳过索引更新')

    # 6. 标记已发布
    published = load_published()
    published.append(pool_file)
    if not args.dry_run:
        save_published(published)

    # 7. GitHub Pages (失败不阻塞, 仅告警)
    if not git_commit_push(filename, title, args.dry_run):
        log('GitHub 推送失败, 继续推 Gitee...')
    else:
        # IndexNow (GitHub成功才推, 因为用的是 GitHub Pages 域名)
        indexnow_push([
            f'{SITE_URL}/feed/{filename}',
            f'{SITE_URL}/feed/',
        ], args.dry_run)

    # 8. Gitee 同步 (始终执行)
    sync_gitee(args.dry_run)

    # 9. 验证 GitHub Pages (可选)
    verify_deploy(filename, args.dry_run)

    log(f'===== 运营完成 =====')
    return 0


if __name__ == '__main__':
    sys.exit(main())
