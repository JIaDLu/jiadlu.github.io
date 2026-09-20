#!/usr/bin/env python3
"""Run Ideas interaction checks with a temporary, pinned DOM test dependency."""
import os
from pathlib import Path
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]


def check():
    with tempfile.TemporaryDirectory(prefix='ideas-dom-') as directory:
        subprocess.run(['npm','install','--prefix',directory,'jsdom@24.1.3','--ignore-scripts','--no-audit','--no-fund'],check=True)
        env=dict(os.environ,NODE_PATH=str(Path(directory)/'node_modules'))
        subprocess.run(['node','tests/ideas.dom.cjs'],cwd=ROOT,env=env,check=True)


if __name__=='__main__':
    check()
