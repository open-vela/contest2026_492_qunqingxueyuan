"""Local temporary fixtures test preservation; never generate contest evidence."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from scan_release_secrets import scan_files

class FinalizeTests(unittest.TestCase):
    def test_secret_location_only(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'fixture.txt'
            secret = 'sk-' + 'A' * 30
            path.write_text(secret)
            result = scan_files([path])
            self.assertEqual(result['result'], 'BLOCKED')
            self.assertNotIn(secret, json.dumps(result))

    def test_append_idempotent_and_refuse_changed_source(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            subprocess.run(['git', 'init', '-q', str(root)], check=True)
            subprocess.run(['git', '-C', str(root), 'config', 'user.name', 'Local Fixture'], check=True)
            subprocess.run(['git', '-C', str(root), 'config', 'user.email', 'fixture@example.invalid'], check=True)
            (root / 'logs/sdh12312').mkdir(parents=True)
            (root / 'docs').mkdir()
            manifest = {'team_id':'contest2026_492_qunqingxueyuan', 'github_login':'sdh12312', 'schema_version':'1.0', 'sessions':[]}
            mp = root / 'logs/sdh12312/manifest.json'
            mp.write_text(json.dumps(manifest))
            for name in ['README.md', 'docs/AI_LOG_EXPORT_MANUAL.md']:
                (root / name).write_text('<!-- AI_LOG_TOTALS -->old<!-- /AI_LOG_TOTALS -->')
            validator = root / 'fixture_validator.py'
            validator.write_text('import sys\nprint("TEST FIXTURE validator only")\n')
            source = root / 'fixture.jsonl'
            sid = '00000000-0000-0000-0000-000000000001'
            rows = [{'type':'session_meta','payload':{'id':sid}}, {'timestamp':'2026-01-01T00:00:00Z','type':'response_item','payload':{'type':'message','role':'user','content':[{'type':'input_text','text':'LOCAL UNIT TEST FIXTURE ONLY'}]}}]
            source.write_text('\n'.join(json.dumps(x) for x in rows))
            command = [sys.executable, str(ROOT / 'tools/finalize_last_codex_session.py'), str(source), '--repo', str(root), '--validator', str(validator), '--stable-seconds', '0.01', '--timeout', '2']
            subprocess.run(command, check=True, capture_output=True)
            before = {p: p.read_bytes() for p in (root / 'logs').rglob('*') if p.is_file()}
            subprocess.run(command, check=True, capture_output=True)
            self.assertTrue(all(p.read_bytes() == b for p,b in before.items()))
            subprocess.run(command + ['--commit'], check=True, capture_output=True)
            committed = subprocess.check_output(['git', '-C', str(root), 'show', '--pretty=', '--name-only', 'HEAD'], text=True)
            self.assertIn('manifest.json', committed)
            self.assertNotIn('fixture.jsonl', committed)
            self.assertNotIn('fixture_validator.py', committed)
            source.write_text(source.read_text() + '\n')
            self.assertNotEqual(subprocess.run(command, capture_output=True).returncode, 0)
            self.assertTrue(all(p.read_bytes() == b for p,b in before.items()))
            self.assertFalse((root / '.git/finalize-codex.lock').exists())

if __name__ == '__main__':
    unittest.main()
