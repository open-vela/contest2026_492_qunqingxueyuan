"""Generate labelled replay data by executing the existing C reference core."""
import csv
import json
import subprocess
import sys
from pathlib import Path

executable = sys.argv[1] if len(sys.argv) > 1 else 'build/flyreflex_host'
result = {'source': 'host-reference', 'description': 'Recorded C core output; synthetic inputs; not live openvela telemetry.', 'scenarios': {}}
for name in ('safe', 'slow', 'danger', 'recovery', 'noise'):
    rows = csv.DictReader(subprocess.check_output([executable, 'demo', name, '--csv'], text=True).splitlines())
    frames = []
    for row in rows:
        frames.append({
            'schema': 1, 'source': 'host-reference', 'scenario': name,
            'frame': int(row['frame']), 'size': int(row['size_milli']),
            'rate': int(row['rate_milli']), 'lplc2': int(row['lplc2_milli']),
            'lc4': int(row['lc4_milli']), 'gf': int(row['gf_milli']),
            'state': row['state'], 'ai': row['ai_cmd'], 'action': row['final_cmd'],
            'decision': row['decision'], 'latency_ns': None,
        })
    for frame in frames: frame['count'] = len(frames)
    result['scenarios'][name] = frames
destination = Path(__file__).resolve().parents[1] / 'web' / 'demo.json'
destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(destination)
