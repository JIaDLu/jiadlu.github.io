#!/usr/bin/env python3
"""Validate and build the independently authored Ideas log. Python standard library only."""
import argparse
import datetime as dt
import hashlib
import html
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit
from xml.etree import ElementTree as ET
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
SLUG = re.compile(r'^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$')
KINDS = {'idea': 'Idea', 'note': '随记', 'essay': '长文'}
SITE = 'https://jiadlu.github.io'
PAGE_SIZE = 12


def need(condition, message):
    if not condition:
        raise ValueError(message)


def text(value, label, empty=False):
    need(isinstance(value, str) and (empty or value.strip()), f'{label}: expected text')


def fields(value, required, optional='', label='record'):
    need(isinstance(value, dict), f'{label}: expected object')
    need(set(required.split()) <= set(value) <= set((required+' '+optional).split()), f'{label}: incorrect fields {list(value)}')


def identifier(value):
    need(isinstance(value, str) and SLUG.fullmatch(value), f'Invalid ID: {value}')
    return value


def day(value):
    need(isinstance(value, str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}', value), f'Invalid date: {value}')
    return dt.date.fromisoformat(value)


def url(value):
    text(value, 'url')
    parsed = urlsplit(value)
    need(parsed.scheme in ('http', 'https') and parsed.hostname and not parsed.username and not parsed.password, f'Invalid public URL: {value}')
    need(not any(c.isspace() for c in value), 'URL may not contain whitespace')


def read(path):
    def unique(pairs):
        result = {}
        for key, val in pairs:
            need(key not in result, f'{path}: duplicate key {key}')
            result[key] = val
        return result
    return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=unique)


def plain(block):
    return '\n'.join(block['items']) if block['type'] == 'list' else block.get('text', block.get('code', ''))


def title(post):
    return post['title'] or next((plain(b).split('\n')[0][:60] for b in post['blocks'] if plain(b)), '一闪而过的想法')


def load(source, demo=False):
    settings = read(source/'settings.json')
    fields(settings, 'version timezone title description tags')
    need(settings['version'] == 1, 'Unsupported Ideas schema version')
    text(settings['title'], 'site title')
    text(settings['description'], 'site description')
    today = dt.datetime.now(ZoneInfo(settings['timezone'])).date()
    need(isinstance(settings['tags'], list), 'tags must be a list')
    tags = {}
    for tag in settings['tags']:
        fields(tag, 'id label')
        identifier(tag['id'])
        text(tag['label'], 'tag label')
        need(tag['id'] not in tags, 'Duplicate tag ID')
        tags[tag['id']] = tag['label']
    need(len(set(tags.values())) == len(tags), 'Duplicate tag label')
    posts = []
    for path in sorted((source/'posts').glob('*.json')):
        post = read(path)
        fields(post, 'id title date updated kind tags excerpt blocks sources updates', label=str(path))
        identifier(post['id'])
        need(path.stem == post['id'], 'ID and filename must match')
        need(post['kind'] in KINDS, 'Unknown content kind')
        text(post['title'], 'post title', post['kind'] == 'idea')
        text(post['excerpt'], 'excerpt', True)
        need(len(post['excerpt']) <= 300, 'Keep excerpts under 300 characters')
        need(day(post['date']) <= day(post['updated']), 'Updated date precedes publication')
        need(demo or day(post['updated']) <= today, 'Future publication is not supported')
        need(isinstance(post['tags'], list) and len(post['tags']) <= 3, 'Use at most three tags')
        need(all(isinstance(t, str) and t in tags for t in post['tags']), 'Unknown tag')
        need(len(set(post['tags'])) == len(post['tags']), 'Repeated tag')
        need(isinstance(post['sources'], list), 'sources must be a list')
        sources = set()
        for source_item in post['sources']:
            fields(source_item, 'id title url publisher published accessed')
            identifier(source_item['id'])
            need(source_item['id'] not in sources, 'Duplicate source ID')
            sources.add(source_item['id'])
            text(source_item['title'], 'source title')
            text(source_item['publisher'], 'source publisher')
            url(source_item['url'])
            if source_item['published'] is not None:
                day(source_item['published'])
            accessed = day(source_item['accessed'])
            need(accessed <= day(post['updated']), 'Source access is after this revision')
            need(source_item['published'] is None or day(source_item['published']) <= accessed, 'Source publication is after access')
        need(isinstance(post['blocks'], list) and post['blocks'], 'A post needs content')
        substantive = False
        for block in post['blocks']:
            need(isinstance(block, dict), 'Block must be an object')
            kind = block.get('type')
            schema = {
                'paragraph': ('type text', 'refs'), 'heading': ('type text', ''),
                'quote': ('type text attribution', 'refs'), 'code': ('type code language', ''),
                'callout': ('type text label', 'refs'), 'list': ('type items ordered', 'refs'),
                'divider': ('type', '')
            }
            need(kind in schema, f'Unsupported block: {kind}')
            fields(block, *schema[kind], label=f'block {kind}')
            if kind == 'list':
                need(isinstance(block['items'], list) and block['items'], 'Empty list')
                need(type(block['ordered']) is bool, 'ordered must be boolean')
                for item in block['items']:
                    text(item, 'list item')
            elif kind == 'code':
                text(block['code'], 'code')
                text(block['language'], 'language', True)
            elif kind != 'divider':
                text(block['text'], 'block text')
                if kind == 'quote':
                    text(block['attribution'], 'quote attribution')
                if kind == 'callout':
                    text(block['label'], 'callout label')
            refs = block.get('refs', [])
            need(isinstance(refs, list) and all(isinstance(r,str) and r in sources for r in refs), 'Unknown source reference')
            need(len(set(refs)) == len(refs), 'Repeated source reference')
            substantive |= kind not in ('heading', 'divider')
        need(substantive, 'A heading is not a post')
        need(isinstance(post['updates'], list), 'updates must be a list')
        previous = post['date']
        for update in post['updates']:
            fields(update, 'date text')
            need(day(previous) <= day(update['date']) <= day(post['updated']), 'Unordered update history')
            text(update['text'], 'update note')
            previous = update['date']
        need(post['updated'] == post['date'] or (post['updates'] and previous == post['updated']), 'Revised posts need a dated update note')
        posts.append(post)
    posts.sort(key=lambda p:(p['date'],p['id']), reverse=True)
    return settings, posts


def e(value):
    return html.escape(str(value), quote=True)


def asset_version():
    return hashlib.sha256(b''.join(p.read_bytes() for p in sorted((ROOT/'ideas/assets').glob('*')) if p.is_file())).hexdigest()[:12]


def render_blocks(post, subset=None):
    result = []
    source_numbers = {s['id']: i+1 for i,s in enumerate(post['sources'])}
    for i, b in enumerate(post['blocks'] if subset is None else subset):
        refs = ''.join(f'<sup><a href="#source-{r}" aria-label="来源 {source_numbers[r]}">[{source_numbers[r]}]</a></sup>' for r in b.get('refs', []))
        kind = b['type']
        if kind == 'paragraph':
            result.append(f'<p>{e(b["text"])}{refs}</p>')
        elif kind == 'heading':
            result.append(f'<h2 id="section-{i}">{e(b["text"])}</h2>')
        elif kind == 'quote':
            result.append(f'<blockquote><p>{e(b["text"])}{refs}</p><cite>{e(b["attribution"])}</cite></blockquote>')
        elif kind == 'code':
            result.append(f'<div class="code-block"><div class="code-top"><span>{e(b["language"] or "code")}</span><button class="copy-code" type="button">复制代码</button></div><pre><code>{e(b["code"])}</code></pre></div>')
        elif kind == 'callout':
            result.append(f'<aside class="callout"><span>{e(b["label"])}</span><p>{e(b["text"])}{refs}</p></aside>')
        elif kind == 'list':
            tag = 'ol' if b['ordered'] else 'ul'
            result.append(f'<{tag}>{"".join(f"<li>{e(item)}</li>" for item in b["items"])}</{tag}>{refs}')
        else:
            result.append('<hr class="thought-break">')
    return '\n'.join(result)


def summary(post):
    return post['excerpt'] or next((plain(b)[:200] for b in post['blocks'] if b['type'] in ('paragraph','callout')), title(post))


def minutes(post):
    content = '\n'.join(plain(b) for b in post['blocks'])
    chinese = len(re.findall(r'[\u4e00-\u9fff]', content))
    words = len(re.findall(r'[a-zA-Z0-9]+', content))
    return max(1, round(chinese/350 + words/220))


def tag_links(post, settings, base):
    labels = {t['id']:t['label'] for t in settings['tags']}
    return ''.join(f'<a class="tag" href="{base}/archive/?tag={tag}">#{e(labels[tag])}</a>' for tag in post['tags'])


def card(post, settings, base):
    link = f'{base}/posts/{post["id"]}/'
    heading = f'<h2><a href="{link}">{e(post["title"])}</a></h2>' if post['title'] else ''
    # Tiny ideas are readable in the feed. Quotes/code/citations stay in the full note.
    tiny = post['kind'] == 'idea' and all(b['type'] == 'paragraph' and not b.get('refs') for b in post['blocks']) and sum(len(plain(b)) for b in post['blocks']) <= 500
    content = render_blocks(post) if tiny else f'<p>{e(summary(post))}</p>'
    return f'''<article class="entry {post['kind']}" data-post="{post['id']}"><div class="entry-date"><time datetime="{post['date']}">{post['date'][5:].replace('-', '.')}</time><span>{post['date'][:4]}</span></div><div class="entry-body"><div class="entry-kind"><i aria-hidden="true"></i>{KINDS[post['kind']]}{'<span>已补记</span>' if post['updates'] else ''}</div>{heading}<div class="entry-text">{content}</div><div class="entry-bottom"><div class="tags">{tag_links(post, settings, base)}</div><a class="read-link" href="{link}" aria-label="阅读 {e(title(post))}">{'永久链接' if tiny else '接着读'} <span aria-hidden="true">↗</span></a></div></div></article>'''


def shell(settings, page_title, description, body, base, route='', page='feed', demo=False):
    canonical = SITE + base + '/' + route
    banner = '<div class="demo-banner">演示空间 · 以下文字用于展示排版，不代表 Jiadong 的真实观点。<a href="/ideas/">回到 Ideas ↗</a></div>' if demo else ''
    version = asset_version()
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(page_title)} · Jiadong / Ideas</title><meta name="description" content="{e(description)}"><link rel="canonical" href="{e(canonical)}">
<meta property="og:title" content="{e(page_title)}"><meta property="og:description" content="{e(description)}"><meta property="og:url" content="{e(canonical)}"><meta property="og:type" content="{'article' if page=='post' else 'website'}"><meta name="twitter:card" content="summary"><meta name="twitter:title" content="{e(page_title)}"><meta name="twitter:description" content="{e(description)}">
{'<meta name="robots" content="noindex,follow">' if demo else ''}<link rel="alternate" type="application/atom+xml" title="Jiadong / Ideas" href="{base}/feed.xml">
<link rel="stylesheet" href="/ideas/assets/style.css?v={version}"><script defer src="/ideas/assets/app.js?v={version}"></script></head>
<body data-base="{base}" data-page="{page}"><a class="skip" href="#main">跳到正文</a>{banner}<header class="site-header"><a class="brand" href="/">Jiadong<span>/</span><strong>Ideas</strong></a><nav aria-label="主导航"><a href="{base}/" {'aria-current="page"' if page=='feed' else ''}>想法</a><a href="{base}/archive/" {'aria-current="page"' if page=='archive' else ''}>归档</a><a href="/knowledge/">Knowledge ↗</a></nav></header>
<main id="main">{body}</main><footer><a href="{base}/">Jiadong / Ideas</a><span>保持好奇。允许改主意。</span><a href="{base}/feed.xml">RSS / Atom ↗</a></footer><div class="announcement" role="status" aria-live="polite"></div></body></html>'''


def sidebar(settings, posts, base, demo):
    counts = {t['id']:sum(t['id'] in p['tags'] for p in posts) for t in settings['tags']}
    topics = ''.join(f'<a href="{base}/archive/?tag={t["id"]}"><span>#{e(t["label"])}</span><small>{counts[t["id"]]}</small></a>' for t in settings['tags'] if counts[t['id']])
    months = sorted({p['date'][:7] for p in posts}, reverse=True)
    archive = ''.join(f'<a href="{base}/archive/?month={m}"><span>{m[:4]} / {m[5:]}</span><small>{sum(p["date"].startswith(m) for p in posts)} ↗</small></a>' for m in months[:6])
    return f'''<aside class="feed-sidebar"><section class="margin-note"><div class="eyebrow">A NOTE TO SELF</div><p>有些事想明白了。<br>有些事，先记下来。</p><span>AI · 工作 · 生活 · 未完成的想法</span></section>{f'<section><h2>最近在想</h2><div class="sidebar-list">{topics}</div></section>' if topics else ''}{f'<section><h2>时间留下的痕迹</h2><div class="sidebar-list">{archive}</div></section>' if archive else ''}<section class="small-note"><a href="/knowledge/">What I learned → Knowledge</a><p>这里留下的是 What I think。</p>{'<a href="/ideas/demo/">看看不同长度的想法 ↗</a>' if not posts and not demo else ''}</section></aside>'''


def empty():
    return '<div class="empty"><span class="empty-symbol" aria-hidden="true">↳</span><h2>下一条想法，从这里开始。</h2><p>不一定想清楚了才值得写。<br>也许是一句吐槽，也许是一个值得追问的问题。</p><a class="text-link" href="/ideas/demo/">先逛逛演示空间 ↗</a></div>'


def feed(settings, posts, base, demo, number=1):
    pages = max(1, (len(posts)+PAGE_SIZE-1)//PAGE_SIZE)
    part = posts[(number-1)*PAGE_SIZE:number*PAGE_SIZE]
    latest = posts[0]['date'] if posts else None
    headline=e(settings['title']).replace('in progress.', '<em>in progress.</em>')
    heading = f'''<section class="intro"><div class="eyebrow">PERSONAL IDEAS / RESEARCH LOG</div><h1>{headline}<span class="cursor" aria-hidden="true">_</span></h1><p>{e(settings['description'])}</p><div class="intro-meta"><span class="live-dot" aria-hidden="true"></span>{f'最近一笔 {latest}' if latest else '留一点空间，给下一次灵光一闪。'}</div></section>'''
    pagination = ''
    if pages > 1:
        prev = base+'/' if number==2 else f'{base}/page/{number-1}/'
        pagination = f'<nav class="pagination" aria-label="翻页">{f"<a href=\"{prev}\">← 更新的想法</a>" if number>1 else "<span></span>"}<span>{number} / {pages}</span>{f"<a href=\"{base}/page/{number+1}/\">更早的想法 →</a>" if number<pages else "<span></span>"}</nav>'
    filters = '<a class="kind-tab selected" href="'+base+'/">全部</a>'+''.join(f'<a class="kind-tab" href="{base}/archive/?kind={k}">{v}</a>' for k,v in KINDS.items())
    body = heading+f'<div class="feed-layout"><section aria-label="最近的想法"><div class="feed-toolbar"><div class="kind-tabs">{filters}</div><a href="{base}/archive/" class="archive-link">搜索 / 日期筛选 ↗</a></div>{"".join(card(p,settings,base) for p in part) or empty()}{pagination}</section>{sidebar(settings,posts,base,demo)}</div>'
    return shell(settings,settings['title'],settings['description'],body,base,'' if number==1 else f'page/{number}/',demo=demo)


def archive(settings, posts, base, demo):
    months = sorted({p['date'][:7] for p in posts},reverse=True)
    controls = f'''<form class="filters" id="filters" role="search"><label class="search-label"><span>搜索</span><input type="search" name="q" placeholder="一个词，一次没想完的对话…" aria-label="搜索全文"></label><div class="filter-row"><label><span>形态</span><select name="kind"><option value="">所有形态</option>{''.join(f'<option value="{k}">{v}</option>' for k,v in KINDS.items())}</select></label><label><span>话题</span><select name="tag"><option value="">所有话题</option>{''.join(f'<option value="{t["id"]}">{e(t["label"])}</option>' for t in settings['tags'])}</select></label><label><span>月份</span><select name="month"><option value="">所有月份</option>{''.join(f'<option>{m}</option>' for m in months)}</select></label><label><span>从</span><input type="date" name="from" aria-label="起始日期"></label><label><span>至</span><input type="date" name="to" aria-label="结束日期"></label><button type="reset" class="reset">清除筛选</button></div></form>'''
    body = f'''<section class="intro archive-intro"><div class="eyebrow">THE RUNNING LOG</div><h1>想法有迹可循<span class="period">.</span></h1><p>顺着时间，找回当时在想什么。</p></section>{controls}<div class="results-heading"><span id="result-count" role="status">{len(posts)} 条记录</span><span>按最初记录时间 · 新 → 旧</span></div><p id="filter-error" class="filter-error" role="alert" hidden></p><div id="archive-results">{''.join(card(p,settings,base) for p in posts[:PAGE_SIZE]) or empty()}</div><div id="archive-pagination"></div><noscript><p>交互筛选需要 JavaScript。<a href="{base}/">返回可逐页浏览的时间流</a>。</p></noscript>'''
    return shell(settings,'归档',settings['description'],body,base,'archive/','archive',demo)


def detail(settings, post, posts, base, demo):
    headings = [(i,b['text']) for i,b in enumerate(post['blocks']) if b['type']=='heading']
    toc = ''
    if len(headings)>=3 and post['kind']=='essay':
        toc = '<aside class="toc"><span class="eyebrow">这一页</span>'+''.join(f'<a href="#section-{i}">{e(t)}</a>' for i,t in headings)+'</aside>'
    lead = f'<p class="post-lede">{e(post["excerpt"])}</p>' if post['excerpt'] else ''
    sources = ''
    if post['sources']:
        sources = '<section class="sources"><h2>这次讨论的背景</h2><ol>'+''.join(f'<li id="source-{s["id"]}"><a href="{e(s["url"])}" target="_blank" rel="noopener noreferrer">{e(s["title"])} ↗</a><span>{e(s["publisher"])} · {"发布 "+s["published"]+" · " if s["published"] else ""}查阅 {s["accessed"]}</span></li>' for s in post['sources'])+'</ol></section>'
    updates = '<section class="updates"><h2>后来又想了想</h2>'+''.join(f'<div><time datetime="{u["date"]}">{u["date"]}</time><p>{e(u["text"])}</p></div>' for u in post['updates'])+'</section>' if post['updates'] else ''
    neighbors = sorted((p for p in posts if p['id']!=post['id']),key=lambda p:(-len(set(p['tags'])&set(post['tags'])), -int(p['date'].replace('-','')),p['id']))[:2]
    more = '<section class="read-next"><h2>还有一些没聊完的</h2>'+''.join(f'<a href="{base}/posts/{p["id"]}/"><span>{e(title(p))}</span><small>{KINDS[p["kind"]]} · {p["date"]} ↗</small></a>' for p in neighbors)+'</section>' if neighbors else ''
    display_title = f'<h1>{e(post["title"])}</h1>' if post['title'] else '<h1 class="sr-only">'+e(title(post))+'</h1>'
    body = f'''<article class="post {post['kind']} {'has-toc' if toc else ''}"><a class="back-link" href="{base}/">← 回到想法流</a><header class="post-header"><div class="post-meta"><span class="kind-label">{KINDS[post['kind']]}</span><time datetime="{post['date']}">{post['date']}</time><span>{'片刻阅读' if post['kind']=='idea' else str(minutes(post))+' 分钟阅读'}</span></div>{display_title}{lead}<div class="tags">{tag_links(post,settings,base)}</div></header><div class="reading-layout">{toc}<div class="reading-column"><div class="prose">{render_blocks(post)}</div>{updates}<div class="post-signoff"><span class="signature">{'演示文字' if demo else 'Jiadong'}</span><button class="copy-link" type="button">复制这条想法的链接 ↗</button></div>{sources}{more}<a class="text-link" href="{base}/archive/">回到所有记录 →</a></div></div></article>'''
    return shell(settings,title(post),summary(post),body,base,f'posts/{post["id"]}/','post',demo)


def atom(settings, posts, base):
    ns = 'http://www.w3.org/2005/Atom'
    ET.register_namespace('', ns)
    def tag(parent,name,value=None,**attrs):
        el = ET.SubElement(parent,'{'+ns+'}'+name,attrs)
        if value is not None: el.text=value
        return el
    feed = ET.Element('{'+ns+'}feed')
    tag(feed,'title','Jiadong / Ideas' if '/demo' not in base else 'Ideas · 演示')
    tag(feed,'id',SITE+base+'/')
    tag(feed,'link',href=SITE+base+'/')
    tag(feed,'link',href=SITE+base+'/feed.xml',rel='self')
    author = tag(feed,'author'); tag(author,'name','Jiadong' if '/demo' not in base else '演示文字')
    tag(feed,'updated',(max((p['updated'] for p in posts),default='1970-01-01'))+'T00:00:00+08:00')
    for p in posts[:50]:
        entry=tag(feed,'entry')
        tag(entry,'title',title(p)); tag(entry,'id',SITE+base+'/posts/'+p['id']+'/')
        tag(entry,'link',href=SITE+base+'/posts/'+p['id']+'/')
        tag(entry,'published',p['date']+'T00:00:00+08:00');tag(entry,'updated',p['updated']+'T00:00:00+08:00')
        tag(entry,'summary',summary(p))
    return ET.tostring(feed,encoding='unicode',xml_declaration=True)+'\n'


def build(source, output, base='/ideas', demo=False):
    settings, posts = load(source,demo)
    manifest = {'version':1,'demo':demo,'posts':[{
        'id':p['id'],'title':title(p),'date':p['date'],'kind':p['kind'],'tags':p['tags'],
        'search':'\n'.join([title(p),p['excerpt'],*(plain(b) for b in p['blocks']),*(u['text'] for u in p['updates'])]),
        'html':card(p,settings,base)
    } for p in posts]}
    files = {'index.html':feed(settings,posts,base,demo),'archive/index.html':archive(settings,posts,base,demo),'data/index.json':json.dumps(manifest,ensure_ascii=False,indent=2)+'\n','feed.xml':atom(settings,posts,base)}
    for number in range(2,(len(posts)+PAGE_SIZE-1)//PAGE_SIZE+1):
        files[f'page/{number}/index.html']=feed(settings,posts,base,demo,number)
    for post in posts:
        files[f'posts/{post["id"]}/index.html']=detail(settings,post,posts,base,demo)
    revision = hashlib.sha256((json.dumps(files,sort_keys=True,ensure_ascii=False)+asset_version()).encode()).hexdigest()[:16]
    files['data/revision.json']=json.dumps({'revision':revision})+'\n'
    # Only remove files owned by this generator; assets/demo are independent surfaces.
    for pattern in ('posts/*/index.html','page/*/index.html'):
        for stale in output.glob(pattern):
            if stale.relative_to(output).as_posix() not in files:
                stale.unlink()
                if not any(stale.parent.iterdir()): stale.parent.rmdir()
    for name,content in files.items():
        path=output/name
        path.parent.mkdir(parents=True,exist_ok=True)
        if not path.exists() or path.read_text(encoding='utf-8') != content:
            temporary=path.with_suffix(path.suffix+'.tmp')
            temporary.write_text(content,encoding='utf-8')
            temporary.replace(path)
    return revision


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['validate','build'])
    args=parser.parse_args()
    try:
        if args.command=='validate':
            _,posts=load(ROOT/'content/ideas')
            load(ROOT/'docs/ideas/examples',True)
            print(f'Ideas valid: {len(posts)} public posts; demo separate.')
        else:
            revision=build(ROOT/'content/ideas',ROOT/'ideas')
            build(ROOT/'docs/ideas/examples',ROOT/'ideas/demo','/ideas/demo',True)
            print(f'Ideas built · {revision}')
    except (ValueError,KeyError,TypeError) as exc:
        print(f'Ideas validation failed: {exc}',file=sys.stderr)
        return 1
    return 0

if __name__=='__main__':
    sys.exit(main())
