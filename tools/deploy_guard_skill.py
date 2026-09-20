"""Deploy the repository Guard Skill verbatim over local NSH; no credentials."""
import argparse
from pathlib import Path
from real_openvela_integration import NSH

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--host', default='127.0.0.1')
parser.add_argument('--port', type=int, default=10023)
args = parser.parse_args()
source = Path(__file__).resolve().parents[1] / 'runtime_skills/flyreflex-guard.md'
payload = source.read_bytes()
session = NSH(args.host, args.port)
try:
    session.command('mkdir -p /data/agent/skills')
    session.command('cd /data/agent/skills')
    for offset in range(0, len(payload), 4):
        chunk = payload[offset:offset+4]
        value = int.from_bytes(chunk, 'little')
        redirect = '>' if offset == 0 else '>>'
        if len(chunk) == 3:
            session.command(f"printf '\\x{value & 65535:04x}' {redirect} flyreflex-guard.md")
            session.command(f"printf '\\x{value >> 16:02x}' >> flyreflex-guard.md")
        else:
            session.command(f"printf '\\x{value:0{len(chunk)*2}x}' {redirect} flyreflex-guard.md")
    returned = session.command('cat flyreflex-guard.md').replace('\r', '')
    assert payload.decode().replace('\r', '') in returned, 'Skill read-back mismatch'
    print('PASS: repository Skill deployed and read back at /data/agent/skills/flyreflex-guard.md')
finally:
    session.conn.close()
