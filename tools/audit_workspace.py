"""Audit each actual repo from project.list without the repo-status wrapper."""
import argparse
import datetime
import subprocess
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('workspace', type=Path)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
lines = [f'UTC: {datetime.datetime.now(datetime.timezone.utc).isoformat()}', f'Workspace: {a.workspace}']
dirty = missing = errors = checked = 0
names = set((a.workspace / '.repo/project.list').read_text().splitlines())
manifest = a.workspace / 'contest2026_492_qunqingxueyuan/openvela.xml'
if manifest.is_file():
    names.update(p.attrib['path'] for p in ET.parse(manifest).getroot().findall('project') if 'path' in p.attrib)
def inspect(name):
    path = a.workspace / name
    if not (path / '.git').exists():
        return name, None, None
    git = ['git', '-c', 'core.safecrlf=false', '-C', str(path)]
    revision = subprocess.run(git + ['rev-parse', 'HEAD'], capture_output=True, text=True)
    result = subprocess.run(git + ['status', '--porcelain'], capture_output=True, text=True)
    return name, revision, result

with ThreadPoolExecutor(max_workers=4) as pool:
    inspected = list(pool.map(inspect, sorted(names)))
for name, revision, result in inspected:
    if revision is None:
        missing += 1
        lines.append(f'MISSING {name}')
        continue
    checked += 1
    if revision.returncode or result.returncode:
        errors += 1
        lines.append(f'ERROR {name}: {revision.stderr} {result.stderr}')
    else:
        lines.append(f'{name} {revision.stdout.strip()} ' + ('DIRTY' if result.stdout else 'CLEAN'))
        if result.stdout:
            dirty += 1
            lines.append(result.stdout.rstrip())
lines.append(f'checked={checked} dirty={dirty} missing={missing} errors={errors}')
a.output.parent.mkdir(parents=True, exist_ok=True)
a.output.write_text('\n'.join(lines) + '\n', encoding='utf-8')
print(lines[-1])
raise SystemExit(bool(errors))
