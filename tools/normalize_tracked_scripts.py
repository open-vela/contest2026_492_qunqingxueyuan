#!/usr/bin/env python3
"""Restore LF for tracked executable scripts only when content matches Git."""
import hashlib
import subprocess
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
projects = [root / p for p in (root / '.repo/project.list').read_text().splitlines()]
projects.append(root / 'contest2026_492_qunqingxueyuan')
changed = []
for repo in projects:
    if not (repo / '.git').exists():
        continue
    entries = subprocess.check_output(
        ['git', '-C', str(repo), 'ls-files', '-s', '-z'], stderr=subprocess.DEVNULL
    ).decode().split('\0')
    for entry in entries:
        if not entry.startswith('100755 ') or '\t' not in entry:
            continue
        meta, name = entry.split('\t', 1)
        expected = meta.split()[1]
        path = repo / name
        if not path.is_file():
            continue
        raw = path.read_bytes()
        if b'\r\n' not in raw or b'\0' in raw:
            continue
        normalized = raw.replace(b'\r\n', b'\n')
        blob = b'blob ' + str(len(normalized)).encode() + b'\0' + normalized
        if hashlib.sha1(blob).hexdigest() == expected:
            path.write_bytes(normalized)
            changed.append(str(path.relative_to(root)))
print(f'Normalized {len(changed)} tracked executable scripts to Git LF content')
