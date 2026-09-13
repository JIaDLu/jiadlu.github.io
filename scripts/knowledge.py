#!/usr/bin/env python3
"""Validate the knowledge source and deterministically generate static views. Stdlib only."""
import argparse
import datetime as dt
import hashlib
import html
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
ID = re.compile(r'^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$')

def require(condition, message):
    if not condition:
        raise ValueError(message)

def string(value, label):
    require(isinstance(value, str) and bool(value.strip()), f'{label}: nonempty string required')

def strings(value, label, minimum=0):
    require(isinstance(value, list) and len(value) >= minimum, f'{label}: list required (min {minimum})')
    for v in value:
        string(v, label)

def keys(obj, expected, label):
    require(isinstance(obj, dict), f'{label}: object required')
    require(set(obj) == set(expected.split()), f'{label}: expected fields {expected}; got {list(obj)}')

def date(value):
    require(isinstance(value, str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}', value), f'Invalid date: {value}')
    return dt.date.fromisoformat(value)

def read(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, f'{path}: duplicate JSON key {key}')
            result[key] = value
        return result
    return json.loads(path.read_text(), object_pairs_hook=unique)

def load(source, demo=False):
    taxonomy = read(source / 'taxonomy.json')
    keys(taxonomy, 'version timezone branches', 'taxonomy')
    require(taxonomy['version'] == 1, 'Unsupported version')
    now = dt.datetime.now(ZoneInfo(taxonomy['timezone'])).date()
    require(isinstance(taxonomy['branches'], list), 'branches must be a list')
    branches = {}
    for b in taxonomy['branches']:
        keys(b, 'id title parent description', 'branch')
        string(b['id'], 'branch id')
        require(ID.fullmatch(b['id']) and b['id'] not in branches and b['id'] != 'knowledge-root', f'Invalid/duplicate branch ID: {b["id"]}')
        string(b['title'], b['id'])
        string(b['description'], b['id'])
        branches[b['id']] = b
    for b in branches.values():
        seen = {b['id']}
        parent = b['parent']
        while parent is not None:
            require(isinstance(parent, str) and parent in branches, f'{b["id"]}: missing parent {parent}')
            require(parent not in seen, f'Branch cycle at {parent}')
            seen.add(parent)
            parent = branches[parent]['parent']
    notes = {}
    for path in sorted((source / 'notes').glob('*.json')):
        n = read(path)
        keys(n, 'id title summary branch aliases related memory context sections examples recall sources', str(path))
        require(n['id'] == path.stem and ID.fullmatch(n['id']) and n['id'] not in branches and n['id'] != 'knowledge-root', f'Invalid note ID: {path}')
        for field in ('title', 'summary', 'context'):
            string(n[field], f'{path}:{field}')
        require(n['branch'] in branches, f'{path}: unknown branch')
        for field in ('aliases', 'related', 'memory'):
            strings(n[field], field, 1 if field == 'memory' else 0)
            require(len(n[field]) == len(set(n[field])), f'{path}: duplicate {field}')
        require(len(n['memory']) <= 2, f'{path}: only 1–2 memory anchors')
        require(isinstance(n['sections'], list) and n['sections'], f'{path}: sections required')
        for s in n['sections']:
            keys(s, 'title paragraphs', 'section')
            string(s['title'], 'section title')
            strings(s['paragraphs'], 'paragraphs', 1)
        require(isinstance(n['examples'], list) and n['examples'], f'{path}: representative example required')
        for e in n['examples']:
            keys(e, 'title scenario steps code language result', 'example')
            for field in ('title', 'scenario', 'result'):
                string(e[field], field)
            strings(e['steps'], 'steps', 1)
            require(isinstance(e['code'], str) and isinstance(e['language'], str), 'code/language must be strings')
        keys(n['recall'], 'question answer', 'recall')
        for value in n['recall'].values():
            string(value, 'recall')
        require(isinstance(n['sources'], list), 'sources must be a list')
        for s in n['sources']:
            keys(s, 'title url', 'source')
            string(s['title'], 'source title')
            u = urlparse(s['url'])
            require(u.scheme in ('https', 'http') and bool(u.netloc), f'Unsafe source URL: {s["url"]}')
        notes[n['id']] = n
    for n in notes.values():
        require(all(r in notes and r != n['id'] for r in n['related']), f'{n["id"]}: invalid related note')
    days = []
    touched = set()
    for path in sorted((source / 'days').glob('*.json')):
        d = read(path)
        keys(d, 'date summary entries', str(path))
        require(d['date'] == path.stem, f'{path}: date does not match filename')
        require(demo or date(d['date']) <= now, f'{path}: future learning date')
        date(d['date'])
        string(d['summary'], 'day summary')
        require(isinstance(d['entries'], list) and d['entries'], f'{path}: do not record empty learning days')
        seen = set()
        for e in d['entries']:
            keys(e, 'note takeaway kind', 'day entry')
            require(e['note'] in notes and e['note'] not in seen, f'{path}: unknown/duplicate note {e["note"]}')
            require(e['kind'] in ('learn', 'review'), f'{path}: invalid kind')
            string(e['takeaway'], 'takeaway')
            seen.add(e['note'])
            touched.add(e['note'])
        days.append(d)
    require(touched == set(notes), f'Notes without a learning record: {set(notes) - touched}')
    return taxonomy, notes, days

def escape(value):
    return html.escape(str(value), quote=True)

def shell(title, description, body, base, page, demo=False, extra=''):
    asset_version = hashlib.sha256(b''.join(p.read_bytes() for p in sorted((ROOT / 'knowledge/assets').glob('*')) if p.is_file())).hexdigest()[:12]
    banner = '<div class="demo-banner">演示空间 · 示例内容与日期，不计入真实学习记录 <a href="/knowledge/">返回我的知识库 ↗</a></div>' if demo else ''
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)} · Jiadong / Knowledge</title><meta name="description" content="{escape(description)}">
<meta property="og:title" content="{escape(title)}"><meta property="og:description" content="{escape(description)}"><meta name="twitter:card" content="summary"><meta name="twitter:title" content="{escape(title)}"><meta name="twitter:description" content="{escape(description)}">
<link rel="stylesheet" href="/knowledge/assets/style.css?v={asset_version}"><script defer src="/knowledge/assets/app.js?v={asset_version}"></script></head>
<body data-base="{base}" data-page="{page}"><a class="skip" href="#main">跳至正文</a>{banner}
<header class="site-header"><a class="brand" href="/">Jiadong<span>/</span><b>Knowledge</b></a><nav aria-label="主导航"><a {'aria-current="page"' if page == 'home' else ''} href="{base}/">每日学习</a><a {'aria-current="page"' if page == 'tree' else ''} href="{base}/tree/">知识树</a><a href="/">个人主页 ↗</a></nav></header>
<main id="main">{body}<noscript><p>学习日历和交互树需要启用 JavaScript；知识详情可直接阅读。</p></noscript></main><footer><span>Jiadong’s learning notebook</span><span>一点一滴，形成体系。<span class="footer-dot">●</span></span></footer>{extra}</body></html>'''

def detail(n, notes, branches, days, base, demo):
    trail = []
    parent = n['branch']
    while parent:
        b = branches[parent]
        trail.insert(0, f'<a href="{base}/tree/?node={b["id"]}">{escape(b["title"])}</a>')
        parent = b['parent']
    history = [(d, e) for d in days for e in d['entries'] if e['note'] == n['id']]
    anchors = ''.join(f'<p>{escape(m)}</p>' for m in n['memory'])
    sections = ''.join(f'<section class="prose-section"><h3>{escape(s["title"])}</h3>{"".join(f"<p>{escape(p)}</p>" for p in s["paragraphs"])}</section>' for s in n['sections'])
    examples = ''
    for i, e in enumerate(n['examples']):
        code = f'<div class="code-label">{escape(e["language"] or "示例")}<button class="copy-code" type="button">复制</button></div><pre><code>{escape(e["code"])}</code></pre>' if e['code'] else ''
        examples += f'<details class="example" {"open" if i == 0 else ""}><summary><span class="number">{i+1:02}</span>{escape(e["title"])}</summary><div class="example-body"><p>{escape(e["scenario"])}</p><ol>{"".join(f"<li>{escape(s)}</li>" for s in e["steps"])}</ol>{code}<p class="result"><b>得到什么</b><br>{escape(e["result"])}</p></div></details>'
    related_ids = set(n['related']) | {r['id'] for r in notes.values() if n['id'] in r['related']}
    related = ''.join(f'<a class="related-link" href="{base}/notes/{r}/">{escape(notes[r]["title"])} <span>↗</span></a>' for r in sorted(related_ids)) or '<p class="muted">随着学习，建立更多连接。</p>'
    sources = ''.join(f'<li><a href="{escape(s["url"])}" target="_blank" rel="noopener noreferrer">{escape(s["title"])} ↗</a></li>' for s in n['sources']) or '<li>来自当次学习讨论，尚未附外部来源。</li>'
    histories = ''.join(f'<li><a href="{base}/?day={d["date"]}">{d["date"]}</a><span class="tag">{"初学" if e["kind"] == "learn" else "回顾"}</span><p>{escape(e["takeaway"])}</p></li>' for d, e in reversed(history))
    body = f'''<article class="detail"><div class="breadcrumbs"><a href="{base}/tree/">知识树</a><span>/</span>{'<span>/</span>'.join(trail)}</div>
<div class="detail-heading"><div class="eyebrow">KNOWLEDGE NOTE</div><h1>{escape(n['title'])}</h1><p class="lede">{escape(n['summary'])}</p><div class="meta">首次学习 {history[0][0]['date']}<span>最近回顾 {history[-1][0]['date']}</span><span>{len(history)} 次学习</span></div></div>
<div class="reading-layout"><aside class="reading-nav"><span class="eyebrow">ON THIS PAGE</span><a href="#memory">记忆点</a><a href="#concept">理解概念</a><a href="#examples">完整示例</a><a href="#recall">主动回忆</a><a href="#connections">关联与来源</a><a class="back-tree" href="{base}/tree/?node={n['id']}">在知识树中定位 ↗</a></aside>
<div class="reading-body"><section id="memory" class="memory"><div class="eyebrow">TAKE THIS WITH YOU · 记忆点</div>{anchors}</section>
<section id="concept"><div class="section-heading"><span class="number">01</span><h2>理解概念</h2></div><div class="context"><b>回到当时的问题</b><p>{escape(n['context'])}</p></div>{sections}</section>
<section id="examples"><div class="section-heading"><span class="number">02</span><h2>把概念放进示例</h2></div>{examples}</section>
<section id="recall" class="recall"><div class="eyebrow">A MOMENT TO RECALL</div><h2>{escape(n['recall']['question'])}</h2><details><summary>想一想，再展开答案</summary><p>{escape(n['recall']['answer'])}</p></details></section>
<section id="connections"><div class="section-heading"><span class="number">03</span><h2>连接与回顾</h2></div><h3>相关知识</h3>{related}<details class="history"><summary>学习轨迹 · {len(history)} 次</summary><ul>{histories}</ul></details><details class="history"><summary>参考来源</summary><ul>{sources}</ul></details></section></div></div></article>'''
    return shell(n['title'], n['summary'], body, base, 'detail', demo)

def build(source, output, base='/knowledge', demo=False):
    taxonomy, notes, days = load(source, demo)
    branches = {b['id']: b for b in taxonomy['branches']}
    graph_notes = []
    for n in notes.values():
        graph_notes.append({k: n[k] for k in ('id', 'title', 'summary', 'branch', 'aliases', 'related', 'memory')})
    data = {'version': 1, 'timezone': taxonomy['timezone'], 'demo': demo, 'branches': taxonomy['branches'], 'notes': graph_notes, 'days': days}
    serialized = json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + '\n'
    revision_input = serialized + json.dumps(list(notes.values()), ensure_ascii=False, sort_keys=True) + Path(__file__).read_text()
    for asset in sorted((ROOT / 'knowledge/assets').glob('*')):
        if asset.is_file():
            revision_input += asset.read_text()
    revision = hashlib.sha256(revision_input.encode()).hexdigest()[:16]
    home = '''<section class="page-intro"><div class="eyebrow">A PERSONAL KNOWLEDGE SYSTEM</div><div class="intro-row"><div><h1>Everyday Learning<span class="period">.</span></h1><p class="lede">让今天的理解，成为明天的直觉。</p></div><a class="text-link" href="BASE/tree/">探索知识树 <span>↗</span></a></div></section>
<div id="learning-app" aria-live="polite"><p class="loading">正在展开学习记录…</p></div>'''.replace('BASE', base)
    tree = '''<section class="page-intro tree-intro"><div class="eyebrow">CONNECT THE DOTS</div><div class="intro-row"><div><h1>Knowledge Tree<span class="period">.</span></h1><p class="lede">找到位置，看见连接。</p></div><div id="tree-count" class="muted"></div></div></section>
<div id="tree-app"><p class="loading">正在展开知识树…</p></div>'''
    files = {'index.html': shell('Everyday Learning', '每天学了什么，它们如何连接。', home, base, 'home', demo), 'tree/index.html': shell('Knowledge Tree', 'Agent 算法与大模型训练的生长式知识树。', tree, base, 'tree', demo), 'data/graph.json': serialized, 'data/revision.json': json.dumps({'revision': revision}) + '\n'}
    for n in notes.values():
        files[f'notes/{n["id"]}/index.html'] = detail(n, notes, branches, days, base, demo)
    # Remove only obsolete generated note pages, never assets or source content.
    for path in (output / 'notes').glob('*/index.html'):
        if path.relative_to(output).as_posix() not in files:
            path.unlink()
            if not any(path.parent.iterdir()):
                path.parent.rmdir()
    for name, content in files.items():
        path = output / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists() or path.read_text() != content:
            temporary = path.with_suffix(path.suffix + '.tmp')
            temporary.write_text(content)
            temporary.replace(path)
    return revision

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['validate', 'build'])
    args = parser.parse_args()
    try:
        if args.command == 'validate':
            _, notes, days = load(ROOT / 'content/knowledge')
            load(ROOT / 'docs/knowledge/examples', True)
            print(f'Valid: {len(notes)} notes, {len(days)} learning days; demo isolated.')
        else:
            revision = build(ROOT / 'content/knowledge', ROOT / 'knowledge')
            build(ROOT / 'docs/knowledge/examples', ROOT / 'knowledge/demo', '/knowledge/demo', True)
            print(f'Built /knowledge/ and /knowledge/demo/ · revision {revision}')
    except (ValueError, KeyError, TypeError) as exc:
        print(f'Knowledge validation failed: {exc}', file=sys.stderr)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
