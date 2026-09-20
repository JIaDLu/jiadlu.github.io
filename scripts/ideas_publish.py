#!/usr/bin/env python3
"""Check and publish authored Ideas to the existing Pages branch, preserving other work."""
import argparse
import json
import re
import subprocess
import sys
from urllib.request import Request, urlopen
from ideas import ROOT, build, load, need
from ideas_dom_check import check as check_dom

BRANCH='furbish'
REPOSITORY='JIaDLu/jiadlu.github.io'


def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()


def allowed(path):
    return path in ('content/ideas/settings.json','ideas/index.html','ideas/archive/index.html','ideas/data/index.json','ideas/data/revision.json','ideas/feed.xml') or bool(re.fullmatch(r'content/ideas/posts/[a-z][a-z0-9-]*\.json|ideas/posts/[a-z][a-z0-9-]*/index\.html|ideas/page/[0-9]+/index\.html',path))


def check_history(ahead):
    for commit in ahead:
        files=git('diff-tree','--no-commit-id','--name-only','-r',commit).splitlines()
        need(files and all(allowed(p) for p in files) and git('show','-s','--format=%s',commit).startswith('ideas: '), 'Unpushed unrelated commits exist; review them before publishing')


def verify():
    expected=json.loads((ROOT/'ideas/data/revision.json').read_text())['revision']
    try:
        request=Request(f'https://jiadlu.github.io/ideas/data/revision.json?revision={expected}',headers={'Cache-Control':'no-cache'})
        with urlopen(request,timeout=20) as response:
            actual=json.load(response).get('revision')
        if actual==expected:
            print('Live Ideas verified: https://jiadlu.github.io/ideas/')
            return True
        print('Push complete; Pages is still serving the previous revision.')
    except Exception as exc:
        print(f'Live verification pending ({type(exc).__name__}). Check Pages and retry --verify.')
    return False


def publish():
    need(git('branch','--show-current')==BRANCH, f'Publish on {BRANCH}; do not switch silently')
    remote=git('remote','get-url','--push','origin').lower().rstrip('/').removesuffix('.git')
    need(remote in (f'https://github.com/{REPOSITORY}'.lower(),f'git@github.com:{REPOSITORY}'.lower()), 'Unexpected origin push destination')
    need(not git('diff','--cached','--name-only'),'Pre-staged user changes must remain intact')
    _,posts=load(ROOT/'content/ideas')
    need(posts,'No authored Ideas to publish')
    subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=ROOT,check=True)
    subprocess.run(['node','--check','ideas/assets/app.js'],cwd=ROOT,check=True)
    build(ROOT/'content/ideas',ROOT/'ideas')
    check_dom()
    changed=set(git('diff','--name-only','-z').split('\0')+git('ls-files','--others','--exclude-standard','-z').split('\0'))-{''}
    need(not any(p.startswith(('ideas/','content/ideas/')) and not allowed(p) for p in changed),'Uncommitted Ideas implementation/demo changes need a separate commit')
    relevant=sorted(p for p in changed if allowed(p))
    subprocess.run(['git','fetch','origin',BRANCH],cwd=ROOT,check=True)
    need(not git('rev-list',f'HEAD..origin/{BRANCH}'),'Remote has new commits; reconcile and revalidate first')
    check_history(git('rev-list',f'origin/{BRANCH}..HEAD').splitlines())
    if relevant:
        subprocess.run(['git','add','--',*relevant],cwd=ROOT,check=True)
        subprocess.run(['git','commit','-m',f'ideas: publish updates through {max(p["updated"] for p in posts)}'],cwd=ROOT,check=True)
    else:
        print('No new content commit needed; checking for a pending push.')
    subprocess.run(['git','push','origin',f'HEAD:refs/heads/{BRANCH}'],cwd=ROOT,check=True)
    print(f'Pushed {git("rev-parse","--short","HEAD")}; Pages may still be building.')
    return verify()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify',action='store_true')
    args=parser.parse_args()
    try:
        if args.verify: return 0 if verify() else 2
        publish()
        return 0
    except (ValueError,subprocess.CalledProcessError) as exc:
        print(f'Ideas publish stopped: {exc}',file=sys.stderr)
        return 1

if __name__=='__main__':
    sys.exit(main())
