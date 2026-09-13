#!/usr/bin/env python3
"""Publish reviewed daily knowledge changes to the existing GitHub Pages branch."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from urllib.request import Request, urlopen
from knowledge import ROOT, build, load, date, require

BRANCH = 'furbish'
REPOSITORY = 'JIaDLu/jiadlu.github.io'

def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()

def allowed(path):
    return (path == 'content/knowledge/taxonomy.json' or
            path.startswith('content/knowledge/notes/') or path.startswith('content/knowledge/days/') or
            path in ('knowledge/index.html', 'knowledge/tree/index.html', 'knowledge/data/graph.json', 'knowledge/data/revision.json') or
            path.startswith('knowledge/notes/'))

def publish(day):
    date(day)
    require(git('branch', '--show-current') == BRANCH, f'Publish from {BRANCH}; do not silently switch branches')
    require(git('remote', 'get-url', '--push', 'origin').lower().rstrip('/').removesuffix('.git') in (
        f'https://github.com/{REPOSITORY}'.lower(), f'git@github.com:{REPOSITORY}'.lower()), 'Unexpected origin push destination')
    require(not git('diff', '--cached', '--name-only'), 'Index has staged changes; leave them intact and finish separately')
    source = ROOT / 'content/knowledge'
    _, _, days = load(source)
    require(any(d['date'] == day for d in days), 'No learning record for this day')
    subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests'], cwd=ROOT, check=True)
    subprocess.run(['node', '--check', 'knowledge/assets/app.js'], cwd=ROOT, check=True)
    build(source, ROOT / 'knowledge')
    changed = set(git('diff', '--name-only', '-z').split('\0') + git('ls-files', '--others', '--exclude-standard', '-z').split('\0')) - {''}
    relevant = sorted(p for p in changed if allowed(p))
    require(not any(p.startswith('knowledge/') and not allowed(p) for p in changed), 'Uncommitted Knowledge code/demo changes need a separate implementation commit')
    subprocess.run(['git', 'fetch', 'origin', BRANCH], cwd=ROOT, check=True)
    ahead = git('rev-list', f'origin/{BRANCH}..HEAD').splitlines()
    behind = git('rev-list', f'HEAD..origin/{BRANCH}').splitlines()
    require(not behind, 'Remote has new commits: reconcile them and revalidate before publishing')
    # A retry may push already-created daily commits, but never unrelated history.
    for commit in ahead:
        files = git('diff-tree', '--no-commit-id', '--name-only', '-r', commit).splitlines()
        require(files and all(allowed(p) for p in files) and git('show', '-s', '--format=%s', commit).startswith('knowledge: '), 'Unpushed unrelated commits exist; review them before publishing')
    if relevant:
        subprocess.run(['git', 'add', '--', *relevant], cwd=ROOT, check=True)
        subprocess.run(['git', 'commit', '-m', f'knowledge: {day} learning notes'], cwd=ROOT, check=True)
    else:
        print('No new content commit needed.')
    subprocess.run(['git', 'push', 'origin', f'HEAD:refs/heads/{BRANCH}'], cwd=ROOT, check=True)
    print(f'Pushed {git("rev-parse", "--short", "HEAD")}. Pages may still be building.')
    verify()

def verify():
    expected = json.loads((ROOT / 'knowledge/data/revision.json').read_text())['revision']
    request = Request(f'https://jiadlu.github.io/knowledge/data/revision.json?revision={expected}', headers={'Cache-Control':'no-cache'})
    try:
        with urlopen(request, timeout=20) as response:
            actual = json.load(response).get('revision')
        if actual == expected:
            print('Live content verified: https://jiadlu.github.io/knowledge/')
            return True
        print('Push complete; live revision is still pending. Run --verify after Pages finishes.')
    except Exception as exc:
        print(f'Live verification pending ({type(exc).__name__}). Run --verify after Pages finishes.')
    return False

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--date')
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    try:
        if args.verify:
            return 0 if verify() else 2
        require(args.date, '--date is required to publish')
        publish(args.date)
        return 0
    except (ValueError, subprocess.CalledProcessError) as exc:
        print(f'Publish stopped: {exc}', file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())
