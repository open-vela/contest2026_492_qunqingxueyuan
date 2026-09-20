"""Synthetic validation of the C core; no camera or real-world accuracy claim."""
import argparse
import json
import random
import subprocess
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('binary')
parser.add_argument('--output', default='docs/evidence/synthetic-validation.json')
args = parser.parse_args()
rng = random.Random(492)
process = subprocess.Popen([args.binary, 'control'], stdin=subprocess.PIPE,
                           stdout=subprocess.PIPE, text=True)
assert process.stdout.readline().strip() == 'FR2 READY'
records = []
for index in range(200):
    dangerous = index >= 100
    triggered = False
    for frame in range(20):
        size = min(1000, 100 + frame * 50) if dangerous else rng.randint(0, 150)
        rate = rng.randint(700, 1000) if dangerous else rng.randint(0, 80)
        process.stdin.write(f'{frame} {int(frame == 0)} 14 {size} {rate} {size} {rate}\n')
        process.stdin.flush()
        result = json.loads(process.stdout.readline()[4:])
        triggered |= result['action'] == 'ESCAPE'
    records.append({'id': index, 'dangerous': dangerous, 'triggered': triggered})
process.stdin.write('quit\n')
process.stdin.flush()
process.wait(timeout=5)
tp = sum(r['dangerous'] and r['triggered'] for r in records)
fp = sum(not r['dangerous'] and r['triggered'] for r in records)
result = {'label': 'SYNTHETIC SCENARIO VALIDATION', 'seed': 492,
          'source': 'host-reference', 'danger_scenarios': 100, 'safe_scenarios': 100,
          'correct_triggers': tp, 'false_triggers': fp, 'missed_triggers': 100-tp,
          'trigger_rate': tp/100, 'false_positive_rate': fp/100,
          'false_negative_rate': (100-tp)/100,
          'limitation': 'Hand-defined synthetic input families; not camera accuracy or generalization.',
          'records': records}
output = Path(args.output)
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k != 'records'}, indent=2))
