#!/usr/bin/env python3
"""Review and merge an Ideas batch. Private voice evidence never enters public data."""
import argparse
import json
from pathlib import Path
import shutil
import tempfile
from ideas import ROOT, fields, identifier, load, need, read, text, day


def candidate(source, batch, dest):
    fields(batch, 'posts tags voice review')
    need(isinstance(batch['posts'],list) and batch['posts'], 'No authored ideas to publish')
    need(isinstance(batch['tags'],list), 'tags must be a list')
    fields(batch['review'], 'voice_preserved facts_checked privacy_checked')
    need(all(v is True for v in batch['review'].values()), 'Complete editorial review before applying')
    need(isinstance(batch['voice'],list), 'Local voice evidence is required')
    by_id = {}
    for post in batch['posts']:
        need(isinstance(post,dict), 'Post must be an object')
        identifier(post.get('id'))
        need(post['id'] not in by_id, 'Duplicate post in batch')
        by_id[post['id']] = post
    evidence = set()
    for record in batch['voice']:
        fields(record,'post anchors')
        need(record['post'] in by_id and record['post'] not in evidence, 'Voice evidence must map once to each post')
        evidence.add(record['post'])
        need(isinstance(record['anchors'],list) and record['anchors'], 'At least one real user voice anchor is required')
        for anchor in record['anchors']:
            fields(anchor,'quote supports')
            text(anchor['quote'],'user quote')
            need(isinstance(anchor['supports'],list) and anchor['supports'], 'Map user quote to content blocks')
            need(all(type(i) is int and 0 <= i < len(by_id[record['post']]['blocks']) for i in anchor['supports']), 'Invalid voice block index')
    need(evidence == set(by_id), 'AI-only content must remain a local draft, not a personal post')
    shutil.copytree(source,dest,dirs_exist_ok=True)
    settings = read(dest/'settings.json')
    tags = {t['id']:t for t in settings['tags']}
    seen = set()
    for tag in batch['tags']:
        fields(tag,'id label')
        identifier(tag['id'])
        need(tag['id'] not in seen,'Duplicate batch tag')
        seen.add(tag['id'])
        tags[tag['id']]=tag
    settings['tags']=list(tags.values())
    (dest/'settings.json').write_text(json.dumps(settings,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for post in by_id.values():
        path = dest/'posts'/f'{post["id"]}.json'
        if path.exists():
            previous = read(path)
            need(post['date'] == previous['date'], 'Keep original publication date')
            need(day(post['updated']) >= day(previous['updated']), 'Updated date cannot move backward')
        path.write_text(json.dumps(post,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    load(dest)


def ingest(source,batch,apply=False):
    with tempfile.TemporaryDirectory(prefix='ideas-batch-') as tmp:
        staged = Path(tmp)/'source'
        candidate(source,batch,staged)
        changed = [p.relative_to(staged) for p in staged.rglob('*.json') if not (source/p.relative_to(staged)).exists() or p.read_bytes() != (source/p.relative_to(staged)).read_bytes()]
        if apply:
            backup = {name:(source/name).read_bytes() if (source/name).exists() else None for name in changed}
            try:
                for name in changed:
                    dest=source/name
                    dest.parent.mkdir(parents=True,exist_ok=True)
                    temporary=dest.with_suffix('.json.tmp')
                    temporary.write_bytes((staged/name).read_bytes())
                    temporary.replace(dest)
            except Exception:
                for name,content in backup.items():
                    if content is None: (source/name).unlink(missing_ok=True)
                    else: (source/name).write_bytes(content)
                raise
        return [p.as_posix() for p in changed]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('batch',type=Path)
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    lock=ROOT/'.ideas-local/ingest.lock'
    lock.parent.mkdir(exist_ok=True)
    try:
        with lock.open('x'):
            try:
                changed=ingest(ROOT/'content/ideas',read(args.batch),args.apply)
                print(('Applied' if args.apply else 'Dry run')+': '+(', '.join(changed) or 'no changes'))
            finally:
                lock.unlink()
    except FileExistsError:
        parser.error('Another Ideas ingest is active; inspect the local lock before retrying')
    except (ValueError,KeyError,TypeError) as exc:
        parser.error(str(exc))

if __name__=='__main__':
    main()
