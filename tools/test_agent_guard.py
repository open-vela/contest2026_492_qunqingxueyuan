"""Real simulator Agent -> MiMo -> runtime Skill acceptance. Credentials stay off disk."""
import argparse
import getpass
import json
import re
import socket
import threading
import time
from pathlib import Path
from web_bridge import TelnetFilter

parser = argparse.ArgumentParser()
parser.add_argument('--port', type=int, default=10024)
parser.add_argument('--skill-installed', action='store_true')
parser.add_argument('--key-file', type=Path, help='Existing private key file, outside the repository')
parser.add_argument('--output', type=Path, default=Path('docs/evidence/agent-guard-runtime.txt'))
args = parser.parse_args()
key = args.key_file.read_text(encoding='utf-8-sig').strip() if args.key_file else getpass.getpass('MiMo API key (hidden): ')
if not key or any(c.isspace() for c in key):
    raise ValueError('Expected one credential without whitespace')
records = []

class Session:
    def __init__(self):
        self.conn = socket.create_connection(('127.0.0.1', args.port), timeout=10)
        self.conn.settimeout(1)
        self.filter = TelnetFilter()
        self.pending = b''
        self.read(b'ap>', 10)
    def read(self, marker, timeout):
        result = self.pending
        self.pending = b''
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if marker in result:
                end = result.index(marker) + len(marker)
                self.pending = result[end:]
                return result[:end].decode('utf-8', 'replace')
            try:
                raw = self.conn.recv(32768)
                if not raw: raise ConnectionError('Simulator disconnected')
                result += self.filter.feed(raw, self.conn)
            except socket.timeout: pass
        record(result.decode('utf-8', 'replace'))
        raise TimeoutError('Simulator response timeout')
    def command(self, command, marker=b'ap>', timeout=15):
        self.conn.sendall((command+'\r\n').encode())
        return self.read(marker, timeout)

def sanitize(value):
    value = value.replace(key, '[REDACTED]')
    return re.sub(r'(?:tp-|sk-)[A-Za-z0-9_-]{12,}', '[REDACTED]', value)

def record(value):
    records.append(sanitize(value))
    print(sanitize(value), flush=True)
    args.output.write_text('\n'.join(records), encoding='utf-8')

stop = threading.Event()
feed_ready = threading.Event()
feed_errors = []
def danger_feed():
    stream = Session()
    try:
        stream.command('flyreflex control', b'FR2 READY')
        frame = 0
        while not stop.is_set():
            stream.conn.sendall(f'{frame} {int(frame == 0)} 14 1000 1000 1000 1000\r\n'.encode())
            stream.read(b'FR2 {', 5)
            sample = json.loads('{' + stream.read(b'}', 5))
            assert sample['source'] == 'openvela' and sample['seq'] == frame
            assert sample['state'] == 'DANGER' and sample['action'] == 'ESCAPE'
            feed_ready.set()
            frame += 1
            stop.wait(.1)
    except Exception as exc:
        feed_errors.append(str(exc))
    finally:
        stream.conn.sendall(b'quit\r\n')
        stream.conn.close()

agent = Session()
try:
    record(agent.command('uname -a'))
    agent.command('mkdir -p /data/agent/skills')
    agent.command('cd /data/agent/skills')
    payload = b'' if args.skill_installed else Path('runtime_skills/flyreflex-guard.md').read_bytes()
    # NSH printf is not POSIX printf. Its hex format writes little-endian bytes.
    # Keep every command below stock CONFIG_NSH_LINELEN=80.
    for i in range(0, len(payload), 4):
        chunk = payload[i:i+4]
        value = int.from_bytes(chunk, 'little')
        redirect = '>' if i == 0 else '>>'
        if len(chunk) == 3:
            agent.command(f"printf '\\x{value & 65535:04x}' {redirect} flyreflex-guard.md")
            agent.command(f"printf '\\x{value >> 16:02x}' >> flyreflex-guard.md")
        else:
            agent.command(f"printf '\\x{value:0{len(chunk)*2}x}' {redirect} flyreflex-guard.md")
    agent.command('cd /')
    record(agent.command('cat /data/agent/skills/flyreflex-guard.md'))
    record(agent.command('ai_agent', b'vela>', 30))
    host = 'token-plan-cn.xiaomimimo.com' if key.startswith('tp-') else 'api.xiaomimimo.com'
    # Never record this command or its echoed output.
    agent.command(f'set_llm {host} mimo-v2.5 {key}', b'vela>', 10)
    worker = threading.Thread(target=danger_feed, daemon=True)
    worker.start()
    if not feed_ready.wait(10):
        raise RuntimeError(f'Danger feed failed: {feed_errors}')
    observer = Session()
    try:
        record('Direct NSH snapshot before Agent request:')
        record(observer.command('flyreflex guard query_flyreflex_status'))
    finally:
        observer.conn.close()
    # Upstream CLI accepts at most eight tokens including "ask".
    # Its first Agent message is a working notification, not a final answer.
    agent.conn.sendall(b'ask Use flyreflex-guard; request FORWARD; report actual command.\r\n')
    working = {'正在思考中...', '稍等，处理中...', '让我查一下...', '正在分析...', '马上好...'}
    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        record(agent.read(b'[Agent]:', max(1, deadline - time.monotonic())))
        answer = agent.read(b'vela>', max(1, deadline - time.monotonic()))
        record(answer)
        if answer.removesuffix('vela>').strip() not in working:
            break
    if feed_errors:
        raise RuntimeError(f'Danger feed failed: {feed_errors}')
    observer = Session()
    try:
        record('Direct NSH snapshot after Agent response:')
        record(observer.command('flyreflex guard query_flyreflex_status'))
    finally:
        observer.conn.close()
    record('Agent response captured; verify actual tool trace before marking runtime Skill PASS.')
finally:
    stop.set()
    agent.conn.close()
    del key
