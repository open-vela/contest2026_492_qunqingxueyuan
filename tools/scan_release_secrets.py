"""Credential scan; findings contain locations/types only, never matched values."""
import argparse
import io
import json
import re
import subprocess
import zipfile
from pathlib import Path

RULES = {
    'provider-key': r'(?:sk-|tp-)[A-Za-z0-9_-]{24,}',
    'github-token': r'(?:gh[pousr]_|github_pat_)[A-Za-z0-9_]{30,}',
    'bearer': r'(?i)\bBearer\s+[A-Za-z0-9._+/=-]{20,}',
    'private-key': r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
    'assigned-secret': r'''(?i)\b(?:password|passwd|api[_-]?key|mimo[_-]?key|client[_-]?secret)\b["']?\s*[:=]\s*["']([A-Za-z0-9_+/.=-]{16,})["']''',
}

def scan_files(paths):
    findings, errors = [], []
    def scan(name, data):
        if name.lower().endswith(('.docx', '.xlsx', '.pptx', '.zip')):
            try:
                with zipfile.ZipFile(io.BytesIO(data)) as z:
                    for item in z.infolist():
                        if not item.is_dir():
                            scan(name + '!' + item.filename, z.read(item))
            except Exception as e:
                errors.append({'file': name, 'type': type(e).__name__})
            return
        if name.lower().endswith('.pdf'):
            try:
                from pypdf import PdfReader
                text = '\n'.join(p.extract_text() or '' for p in PdfReader(io.BytesIO(data)).pages)
            except Exception as e:
                errors.append({'file': name, 'type': type(e).__name__})
                return
        else:
            text = data.decode('utf-8', errors='replace')
        for kind, pattern in RULES.items():
            for match in re.finditer(pattern, text):
                findings.append({'file': name, 'line': text.count('\n', 0, match.start()) + 1, 'type': kind})
    count = 0
    for path in paths:
        if path.is_file():
            scan(str(path), path.read_bytes())
            count += 1
    return {'files_scanned': count, 'findings': findings, 'errors': errors,
            'result': 'PASS' if not findings and not errors else 'BLOCKED',
            'scope': 'Credential patterns including decoded Office members and PDF text; arbitrary passwords cannot be inferred.'}

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument('--logs-only', action='store_true')
    p.add_argument('--output', type=Path)
    a = p.parse_args()
    if a.logs_only:
        paths = list((a.repo / 'logs').rglob('*.jsonl'))
    else:
        names = subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=a.repo).decode().split('\0')
        paths = [a.repo / n for n in sorted(set(names)) if n and Path(n).suffix.lower() not in ('.mp4', '.png', '.jpg')]
        # Submission reports are intentionally ignored by Git but still audited.
        paths += list((a.repo / 'submission').rglob('*.docx'))
        paths += list((a.repo / 'submission').rglob('*.pdf'))
        paths = sorted(set(paths))
    result = scan_files(paths)
    value = json.dumps(result, ensure_ascii=False, indent=2)
    if a.output:
        a.output.write_text(value + '\n', encoding='utf-8')
    print(value)
    return result['result'] != 'PASS'

if __name__ == '__main__':
    raise SystemExit(main())
