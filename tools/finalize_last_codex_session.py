"""Append a finished rollout using a validated staging copy; never push or merge."""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from scan_release_secrets import scan_files

ROOT = Path(__file__).resolve().parents[1]

def update_summary(repo, manifest, sid):
    sessions = len(manifest['sessions'])
    events = sum(s['event_count'] for s in manifest['sessions'])
    summary = f'Archived AI Coding logs: {sessions} sessions, {sessions} files, {events} events. Official validator: ALL OK. Credential scan: PASS.'
    for name in ('README.md', 'docs/AI_LOG_EXPORT_MANUAL.md'):
        path = repo / name
        text = path.read_text(encoding='utf-8')
        text = re.sub(r'<!-- AI_LOG_TOTALS -->.*?<!-- /AI_LOG_TOTALS -->', '<!-- AI_LOG_TOTALS -->\n' + summary + '\n<!-- /AI_LOG_TOTALS -->', text, flags=re.S)
        text = text.replace('PENDING CURRENT SESSION FINALIZER', 'CURRENT SESSION ARCHIVED ' + sid)
        path.write_text(text, encoding='utf-8')
    report = repo / 'docs/FINAL_RELEASE_REPORT.md'
    if report.exists():
        text = report.read_text(encoding='utf-8')
        text = re.sub(r'\| AI CODING LOGS \| PENDING USER \|[^\n]*', '| AI CODING LOGS | PASS | Current release session archived; official validator ALL OK; credential scan PASS. |', text)
        report.write_text(text, encoding='utf-8')
    print(summary)

def commit_archive(repo, manifest, sid):
    entry = next(s for s in manifest['sessions'] if s['session_id'] == sid)
    names = [entry['file_path'], 'logs/sdh12312/manifest.json', 'docs/codex_rollout_sha256.txt', 'README.md', 'docs/AI_LOG_EXPORT_MANUAL.md']
    if (repo / 'docs/FINAL_RELEASE_REPORT.md').exists():
        names.append('docs/FINAL_RELEASE_REPORT.md')
    subprocess.run(['git', 'add', '--', *names], cwd=repo, check=True)
    changed = subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=repo).returncode
    if changed == 1:
        subprocess.run(['git', 'commit', '-m', 'chore: archive final Codex release session'], cwd=repo, check=True)
    elif changed:
        raise RuntimeError('Cannot inspect staged archive changes')

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def stable(path, seconds, timeout):
    end = time.monotonic() + timeout
    previous, since = None, time.monotonic()
    while time.monotonic() < end:
        now = (path.stat().st_size, path.stat().st_mtime_ns)
        if now != previous:
            previous, since = now, time.monotonic()
        elif time.monotonic() - since >= seconds:
            return digest(path)
        time.sleep(min(2, seconds))
    raise RuntimeError('Rollout is still changing; close the Codex session before finalizing.')

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', help='Rollout path or session UUID; run only after closing that session')
    p.add_argument('--repo', type=Path, default=ROOT)
    p.add_argument('--validator', type=Path, default=Path('D:/openvela_official/.claude/skills/contest-log-collector/tools/validate-log.py'))
    p.add_argument('--stable-seconds', type=float, default=30)
    p.add_argument('--timeout', type=float, default=300)
    p.add_argument('--commit', action='store_true', help='Commit only the finalized archive and summary files locally; never push')
    a = p.parse_args()
    if a.stable_seconds <= 0 or a.timeout <= a.stable_seconds:
        p.error('Require 0 < stable-seconds < timeout')
    source = Path(a.source).expanduser()
    if not source.is_file():
        if not re.fullmatch(r'[0-9a-f-]{36}', a.source):
            p.error('Expected an existing rollout path or session UUID')
        matches = list((Path.home() / '.codex/sessions').rglob('*' + a.source + '.jsonl'))
        if len(matches) != 1:
            p.error(f'Expected one rollout, found {len(matches)}')
        source = matches[0]
    if not a.validator.is_file():
        p.error('Official validator is missing')
    repo = a.repo.resolve()
    if a.commit and subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=repo).returncode != 0:
        p.error('Index must be empty before --commit; unrelated staged files will not be included')
    lock = repo / '.git/finalize-codex.lock'
    with lock.open('x'):
        pass
    try:
        initial = stable(source, a.stable_seconds, a.timeout)
        meta = next(json.loads(line)['payload'] for line in source.read_text(encoding='utf-8').splitlines() if json.loads(line).get('type') == 'session_meta')
        sid = meta.get('id') or meta.get('session_id')
        if not re.fullmatch(r'[0-9a-f-]{36}', sid or ''):
            raise RuntimeError('Invalid source session ID')
        manifest_path = repo / 'logs/sdh12312/manifest.json'
        original_manifest = manifest_path.read_bytes()
        manifest = json.loads(original_manifest)
        old_files = {repo / s['file_path']: digest(repo / s['file_path']) for s in manifest['sessions']}
        entry = next((s for s in manifest['sessions'] if s['session_id'] == sid), None)
        if entry:
            if entry['source_integrity']['main_sha256'] != initial:
                raise RuntimeError('Session already sealed with a different source hash; refusing overwrite')
            print('Session already sealed; validating without rewriting it.')
            subprocess.run([sys.executable, '-X', 'utf8', str(a.validator), str(repo / 'logs')], check=True)
            result = scan_files(list((repo / 'logs').rglob('*.jsonl')))
            print(json.dumps(result, ensure_ascii=False))
            if result['result'] == 'PASS':
                update_summary(repo, manifest, sid)
                if a.commit:
                    commit_archive(repo, manifest, sid)
            return int(result['result'] != 'PASS')
        with tempfile.TemporaryDirectory(prefix='flyreflex-finalize-') as tmp:
            stage = Path(tmp)
            (stage / '.git').mkdir()
            shutil.copytree(repo / 'logs', stage / 'logs')
            (stage / 'docs').mkdir()
            sha = repo / 'docs/codex_rollout_sha256.txt'
            if sha.exists():
                shutil.copy2(sha, stage / 'docs' / sha.name)
            subprocess.run([sys.executable, '-X', 'utf8', str(ROOT / 'tools/codex_rollout_converter.py'), '--source', str(source), '--repo', str(stage), '--team-id', manifest['team_id'], '--github-login', manifest['github_login']], check=True)
            final_manifest = json.loads((stage / 'logs/sdh12312/manifest.json').read_text(encoding='utf-8'))
            assert final_manifest['sessions'][:-1] == manifest['sessions'], 'Old manifest sessions changed'
            subprocess.run([sys.executable, '-X', 'utf8', str(a.validator), str(stage / 'logs')], check=True)
            result = scan_files(list((stage / 'logs').rglob('*.jsonl')))
            if result['result'] != 'PASS':
                print(json.dumps(result, ensure_ascii=False))
                raise RuntimeError('Credential scan failed; repository untouched')
            if digest(source) != initial or manifest_path.read_bytes() != original_manifest:
                raise RuntimeError('Source or manifest changed during finalization; repository untouched')
            for path, value in old_files.items():
                if digest(path) != value or digest(stage / path.relative_to(repo)) != value:
                    raise RuntimeError('Sealed evidence changed; refusing publication')
            new_entry = final_manifest['sessions'][-1]
            target = repo / new_entry['file_path']
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as out:
                out.write((stage / new_entry['file_path']).read_bytes())
            temp_manifest = manifest_path.with_suffix('.json.tmp')
            shutil.copy2(stage / 'logs/sdh12312/manifest.json', temp_manifest)
            os.replace(temp_manifest, manifest_path)
            shutil.copy2(stage / 'docs' / sha.name, sha)
            update_summary(repo, final_manifest, sid)
            if a.commit:
                commit_archive(repo, final_manifest, sid)
            print('No push or merge performed. Include the local archive commit in the final GitHub review.')
        return 0
    finally:
        lock.unlink()

if __name__ == '__main__':
    raise SystemExit(main())
