"""Inventory candidate files and scan credential-shaped strings without printing them."""
import hashlib
import io
import json
import re
import subprocess
import zipfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
files = subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=root).decode().split('\0')
patterns = [rb'gh[pousr]_[A-Za-z0-9]{30,}', rb'github_pat_[A-Za-z0-9_]{30,}',
            rb'(?:sk-|tp-)[A-Za-z0-9_-]{24,}', rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
            rb'(?i)[A-Z]:[\\/]+Users[\\/]+[A-Za-z0-9][^\s<>"\x00]{2,}',
            rb'(?i)(?:authorization:\s*Bearer|cookie:)\s+[A-Za-z0-9_=-]{20,}']
inventory, findings, archive_skipped = [], [], []

def scan(name, content, depth=0):
    if any(re.search(p, content) for p in patterns):
        findings.append(name)
    suffix = Path(name).suffix.lower()
    if suffix == '.pdf':
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(content))
            decoded = '\n'.join(page.extract_text() or '' for page in reader.pages)
            decoded += str(reader.metadata)
            if any(re.search(p, decoded.encode('utf-8')) for p in patterns):
                findings.append(name + ':decoded-pdf')
        except Exception as exc:
            archive_skipped.append(name + ':PDF-' + type(exc).__name__)
    if suffix in ('.zip', '.docx', '.pptx', '.xlsx'):
        if depth >= 3:
            archive_skipped.append(name + ':nesting-limit')
            return
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                budget = 64 * 1024 * 1024
                for member in archive.infolist():
                    if member.is_dir():
                        continue
                    if member.file_size > budget or member.flag_bits & 1:
                        archive_skipped.append(f'{name}!{member.filename}')
                        continue
                    budget -= member.file_size
                    scan(f'{name}!{member.filename}', archive.read(member), depth + 1)
        except (zipfile.BadZipFile, RuntimeError, OSError):
            archive_skipped.append(name)
for name in sorted(set(files)):
    path = root / name
    if not name or not path.is_file() or name == 'docs/evidence/release-inventory.json':
        continue
    content = path.read_bytes()
    inventory.append({'path': name, 'bytes': len(content), 'sha256': hashlib.sha256(content).hexdigest()})
    scan(name, content)
result = {'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root).decode().strip(),
          'status': subprocess.check_output(['git', 'status', '--short'], cwd=root).decode(),
          'credential_pattern_findings': findings,
          'archive_members_not_scanned': archive_skipped,
          'scope': 'Tracked/nonignored files, PDF decoded text/metadata, ZIP/Office recursively to depth 3 with 64 MiB per archive. Heuristic only; excludes Git history and ignored local caches. Any skipped member needs review. Arbitrary passwords cannot be reliably detected by patterns.',
          'files': inventory}
output = root / 'docs/evidence/release-inventory.json'
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(f'Inventoried {len(inventory)} files; credential-pattern finding files: {len(findings)}')
for name in findings:
    print(name)
