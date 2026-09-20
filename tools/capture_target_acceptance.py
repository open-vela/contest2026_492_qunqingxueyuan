"""Read-only scenario/benchmark execution on a local NSH simulator."""
import argparse
import socket
import time
from pathlib import Path
from web_bridge import TelnetFilter

parser = argparse.ArgumentParser()
parser.add_argument('--port', type=int, default=10023)
parser.add_argument('--output', default='docs/evidence/target-runtime.txt')
args = parser.parse_args()
records = []
with socket.create_connection(('127.0.0.1', args.port), timeout=5) as conn:
    conn.settimeout(5)
    decoder = TelnetFilter()
    def prompt():
        chunks = b''
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            packet = conn.recv(16384)
            if not packet:
                raise OSError('Disconnected')
            chunks += decoder.feed(packet, conn)
            if b'ap>' in chunks or b'nsh>' in chunks:
                return chunks.decode('utf-8', errors='replace')
        raise TimeoutError('NSH prompt')
    records.append(prompt())
    for command in ['uname -a', 'flyreflex demo safe', 'flyreflex demo slow',
                    'flyreflex demo danger', 'flyreflex demo recovery',
                    'flyreflex demo danger',
                    'flyreflex guard query_flyreflex_status',
                    'flyreflex guard issue_agent_command FORWARD',
                    'sleep 2', 'flyreflex guard issue_agent_command FORWARD',
                    'flyreflex demo safe', 'flyreflex guard issue_agent_command FORWARD',
                    'flyreflex bench 1000', 'free']:
        conn.sendall((command + '\r\n').encode())
        records.append(prompt())
output = Path(args.output)
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text('\n'.join(records), encoding='utf-8')
print(output)
