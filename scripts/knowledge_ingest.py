#!/usr/bin/env python3
"""Merge a reviewed session batch; dry-run unless --apply is supplied."""
import argparse
import copy
import json
from pathlib import Path
import shutil
import tempfile
from knowledge import ROOT, ID, keys, load, read, require, date


def merge(source, batch, destination):
    keys(batch, 'date summary branches notes entries', 'session batch')
    date(batch['date'])
    for field in ('branches', 'notes', 'entries'):
        require(isinstance(batch[field], list), f'{field}: list required')
    require(batch['entries'], 'No learning points: do not create a learning day')
    shutil.copytree(source, destination, dirs_exist_ok=True)
    taxonomy = read(destination / 'taxonomy.json')
    existing = {b['id']: b for b in taxonomy['branches']}
    branch_ids = set()
    for b in batch['branches']:
        keys(b, 'id title parent description', 'batch branch')
        require(isinstance(b['id'], str) and ID.fullmatch(b['id']), 'Invalid branch ID')
        require(b['id'] not in branch_ids, 'Duplicate branch in batch')
        branch_ids.add(b['id'])
        existing[b['id']] = b
    taxonomy['branches'] = list(existing.values())
    (destination / 'taxonomy.json').write_text(json.dumps(taxonomy, ensure_ascii=False, indent=2)+'\n')
    note_ids = set()
    for n in batch['notes']:
        require(isinstance(n, dict) and isinstance(n.get('id'), str) and ID.fullmatch(n['id']), 'Invalid note ID')
        require(n['id'] not in note_ids, 'Duplicate note in batch')
        note_ids.add(n['id'])
        (destination / 'notes' / f'{n["id"]}.json').write_text(json.dumps(n, ensure_ascii=False, indent=2)+'\n')
    seen = set()
    for e in batch['entries']:
        keys(e, 'note takeaway kind', 'batch entry')
        require(isinstance(e['note'], str) and e['note'] not in seen, 'Duplicate note entry in batch')
        seen.add(e['note'])
    require(note_ids <= seen, 'Every edited note must be included in this learning day')
    path = destination / 'days' / f'{batch["date"]}.json'
    previous = read(path) if path.exists() else {'entries': []}
    entries = {e['note']: e for e in previous['entries']}
    entries.update({e['note']: e for e in batch['entries']})
    day = {'date': batch['date'], 'summary': batch['summary'], 'entries': list(entries.values())}
    path.write_text(json.dumps(day, ensure_ascii=False, indent=2)+'\n')
    load(destination)


def ingest(source, batch, apply=False):
    # Validation occurs in isolation before any source file is changed.
    with tempfile.TemporaryDirectory(prefix='knowledge-merge-') as tmp:
        staged = Path(tmp) / 'source'
        merge(source, batch, staged)
        changed = [p for p in staged.rglob('*.json') if not (source / p.relative_to(staged)).exists() or p.read_bytes() != (source / p.relative_to(staged)).read_bytes()]
        paths = [p.relative_to(staged).as_posix() for p in changed]
        if apply:
            original = {name: (source / name).read_bytes() if (source / name).exists() else None for name in paths}
            try:
                for name in paths:
                    dest = source / name
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    temp = dest.with_suffix('.json.tmp')
                    temp.write_bytes((staged / name).read_bytes())
                    temp.replace(dest)
            except Exception:
                for name, content in original.items():
                    dest = source / name
                    if content is None:
                        dest.unlink(missing_ok=True)
                    else:
                        dest.write_bytes(content)
                raise
        return paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('batch', type=Path)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    lock = ROOT / '.knowledge-local/ingest.lock'
    lock.parent.mkdir(exist_ok=True)
    try:
        with lock.open('x'):
            try:
                changed = ingest(ROOT / 'content/knowledge', read(args.batch), args.apply)
                print(('Applied' if args.apply else 'Dry run') + ': ' + (', '.join(changed) or 'no changes (idempotent)'))
            finally:
                lock.unlink()
    except FileExistsError:
        parser.error('Another ingest is running; inspect .knowledge-local/ingest.lock before retrying')
    except (ValueError, KeyError, TypeError) as exc:
        parser.error(str(exc))

if __name__ == '__main__':
    main()
