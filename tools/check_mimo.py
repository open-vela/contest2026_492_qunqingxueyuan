"""Small real MiMo connectivity check; never saves the credential or prompt log."""
import getpass
import json
import os
from pathlib import Path
import time
import urllib.request
import urllib.error

key = os.environ.get('MIMO_API_KEY') or getpass.getpass('MiMo API key (hidden): ')
host = 'token-plan-cn.xiaomimimo.com' if key.startswith('tp-') else 'api.xiaomimimo.com'
body = {'model': 'mimo-v2.5', 'messages': [{'role': 'user', 'content': 'Reply only OK.'}],
        'max_completion_tokens': 32, 'thinking': {'type': 'disabled'}, 'stream': False}
request = urllib.request.Request('https://' + host + '/v1/chat/completions',
    json.dumps(body).encode(), {'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
started = time.monotonic()
try:
    with urllib.request.urlopen(request, timeout=45) as response:
        data = json.load(response)
        record = {'status': response.status, 'host': host, 'model': data.get('model'),
                  'elapsed_seconds': round(time.monotonic()-started, 3),
                  'usage': data.get('usage'), 'reply': data['choices'][0]['message'].get('content')}
except urllib.error.HTTPError as exc:
    record = {'status': exc.code, 'host': host, 'result': 'HTTP request rejected; response body omitted to protect credentials.'}
except Exception as exc:
    record = {'host': host, 'result': type(exc).__name__}
del key
Path('docs/evidence/mimo-connectivity.json').write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(record, ensure_ascii=False, indent=2))
