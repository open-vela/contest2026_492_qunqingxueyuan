"""Start the final clean-built WSL simulator and bridge; Ctrl+C stops this run."""
import argparse
import os
from pathlib import Path
import re
import socket
import subprocess
import threading
import time

ROOT = Path(__file__).resolve().parents[1]

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--workspace', type=Path, default=Path('/mnt/d/openvela_official'))
    p.add_argument('--no-bridge', action='store_true')
    p.add_argument('--serial-log', type=Path, default=ROOT / '.qa/final-demo-serial.txt')
    a = p.parse_args()
    if os.name == 'nt':
        p.error('Run this launcher in WSL Ubuntu-D using start_final_demo.ps1')
    for port in [10025, 5558, 5559, 8558] + ([] if a.no_bridge else [8090]):
        with socket.socket() as sock:
            try:
                sock.bind(('127.0.0.1', port))
            except OSError:
                p.error(f'Port {port} is occupied; an existing demo may already be running. No process was killed.')
    firmware = a.workspace / 'cmake_out/vela_goldfish-arm64-v8a-ap'
    for name in ['nuttx', '.config', 'vela_system.bin', 'vela_data.bin']:
        if not (firmware / name).is_file():
            p.error(f'Missing final build artifact: {firmware / name}')
    env = dict(os.environ, FLYREFLEX_EMULATOR_PORTS='5558,5559', FLYREFLEX_GRPC_PORT='8558', FLYREFLEX_FIRMWARE_DIR=str(firmware))
    proc = subprocess.Popen(['bash', str(ROOT / 'tools/run_web_emulator.sh'), str(a.workspace)], env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, start_new_session=True)
    ready = threading.Event()
    a.serial_log.parent.mkdir(parents=True, exist_ok=True)
    def pump():
        with a.serial_log.open('w', encoding='utf-8') as out:
            for raw in iter(proc.stdout.readline, b''):
                text = raw.decode(errors='replace')
                text = re.sub(r'(?:tp-|sk-)[A-Za-z0-9_-]{12,}', '[REDACTED]', text)
                text = re.sub(r'(?i)Bearer\s+[A-Za-z0-9._+/=-]{12,}', 'Bearer [REDACTED]', text)
                out.write(text)
                out.flush()
                if 'NuttShell' in text:
                    ready.set()
    threading.Thread(target=pump, daemon=True).start()
    bridge = None
    try:
        if not ready.wait(90):
            raise RuntimeError(f'No NSH boot; inspect {a.serial_log}')
        time.sleep(2)
        for command in [b'ifconfig eth0 10.0.2.15 netmask 255.255.255.0\n', b'ifup eth0\n', b'\x01c', b'hostfwd_add tcp:127.0.0.1:10025-:23\n', b'\x01c']:
            proc.stdin.write(command)
            proc.stdin.flush()
            time.sleep(1)
        with socket.create_connection(('127.0.0.1', 10025), timeout=10):
            pass
        if not a.no_bridge:
            bridge = subprocess.Popen(['python3', str(ROOT / 'tools/web_bridge.py'), '--port', '8090', '--target-port', '10025'])
        print('Final openvela target ready: 10025; browser http://127.0.0.1:8090', flush=True)
        print('Ctrl+C stops only processes started by this launcher.', flush=True)
        while proc.poll() is None:
            if bridge and bridge.poll() is not None:
                raise RuntimeError('Bridge exited')
            time.sleep(1)
        raise RuntimeError(f'Emulator exited: {proc.returncode}')
    except KeyboardInterrupt:
        return 0
    finally:
        import signal
        if bridge and bridge.poll() is None:
            bridge.terminate()
            bridge.wait(timeout=10)
        if proc.poll() is None:
            os.killpg(proc.pid, signal.SIGTERM)
            proc.wait(timeout=15)

if __name__ == '__main__':
    raise SystemExit(main())
