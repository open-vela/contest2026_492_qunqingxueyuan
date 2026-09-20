"""Bounded real-target soak; JSON evidence is finalized even on failure."""
import argparse
import json
import socket
import time
from datetime import datetime, timezone
from pathlib import Path
from web_bridge import TelnetFilter

p = argparse.ArgumentParser()
p.add_argument('--port',type=int,default=10023)
p.add_argument('--seconds',type=int,default=1800)
p.add_argument('--output',default='docs/evidence/soak-target.json')
a=p.parse_args()
record={'source':'openvela ARM64 simulator','started_utc':datetime.now(timezone.utc).isoformat(),
        'requested_seconds':a.seconds,'cycles':0,'memory_samples':[],
        'status':'RUNNING','scope':'NSH scenarios and target heap; not browser bridge soak'}
def save():
    Path(a.output).write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
started=time.monotonic()
try:
    with socket.create_connection(('127.0.0.1',a.port),timeout=10) as conn:
        conn.settimeout(10)
        decoder=TelnetFilter()
        def read():
            response=b''
            while b'ap>' not in response:
                packet=conn.recv(16384)
                if not packet: raise ConnectionError('Target closed connection')
                response+=decoder.feed(packet,conn)
            return response.decode('utf-8','replace')
        def command(text):
            conn.sendall((text+'\r\n').encode())
            return read()
        read()
        record['uname']=command('uname -a')
        while time.monotonic()-started<a.seconds:
            danger=command('flyreflex demo danger')
            recovery=command('flyreflex demo recovery')
            assert 'REFLEX_OVERRIDE' in danger, 'Missing danger override'
            assert 'state=SAFE' in recovery and 'decision=AI' in recovery, 'Missing recovery'
            record['cycles']+=1
            if record['cycles']%10==1:
                record['memory_samples'].append({'elapsed_seconds':round(time.monotonic()-started,2),'free_output':command('free')})
            record['elapsed_seconds']=round(time.monotonic()-started,2)
            save()
            time.sleep(3)
        record['status']='PASS'
except Exception as exc:
    record['status']='BLOCKED'
    record['error']=f'{type(exc).__name__}: {exc}'
finally:
    record['elapsed_seconds']=round(time.monotonic()-started,2)
    record['finished_utc']=datetime.now(timezone.utc).isoformat()
    save()
print(json.dumps({k:v for k,v in record.items() if k not in ('memory_samples','uname')},indent=2))
