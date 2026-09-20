"""Local-only static server and openvela NSH -> SSE bridge. No decision logic."""
import argparse
import json
import socket
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from interactive_bridge import Controller

ROOT = Path(__file__).resolve().parents[1] / 'web'
latest = None
received = 0.0
lock = threading.Lock()


def validate(sample):
    if not isinstance(sample, dict):
        raise ValueError('Expected object')
    if sample.get('schema') != 1 or sample.get('source') != 'openvela':
        raise ValueError('Not openvela telemetry')
    for key, upper in [('size', 1000), ('rate', 1000), ('lplc2', 1000),
                       ('lc4', 1000), ('gf', 1200)]:
        if type(sample.get(key)) is not int or not 0 <= sample[key] <= upper:
            raise ValueError(key)
    for key in ('seq', 'cycle', 'frame', 'count', 'latency_ns'):
        if type(sample.get(key)) is not int or sample[key] < 0:
            raise ValueError(key)
    if not 0 < sample['count'] <= 32 or sample['frame'] >= sample['count']:
        raise ValueError('frame')
    if sample.get('state') not in ('SAFE', 'CAUTION', 'DANGER', 'INVALID'):
        raise ValueError('state')
    if sample.get('action') not in ('FORWARD', 'ESCAPE', 'STOP', 'LEFT', 'RIGHT', 'IDLE'):
        raise ValueError('action')
    if sample.get('decision') not in ('AI', 'REFLEX_OVERRIDE', 'FAILSAFE'):
        raise ValueError('decision')
    if sample.get('ai') not in ('FORWARD', 'ESCAPE', 'STOP', 'LEFT', 'RIGHT', 'IDLE'):
        raise ValueError('ai')
    return sample


def publish(line):
    global latest, received
    marker = line.find(b'FR1 ')
    if marker < 0:
        return
    try:
        sample = validate(json.loads(line[marker + 4:]))
    except (ValueError, TypeError):
        return
    with lock:
        latest, received = sample, time.monotonic()


class TelnetFilter:
    """Strip IAC commands and refuse option negotiation, including split reads."""
    def __init__(self):
        self.state = 'data'
        self.command = 0

    def feed(self, data, conn):
        clean = bytearray()
        for byte in data:
            if self.state == 'data':
                if byte == 255: self.state = 'iac'
                else: clean.append(byte)
            elif self.state == 'iac':
                if byte == 255:
                    clean.append(byte)
                    self.state = 'data'
                elif byte in (251, 252, 253, 254):
                    self.command, self.state = byte, 'option'
                elif byte == 250: self.state = 'sub'
                else: self.state = 'data'
            elif self.state == 'option':
                if self.command in (251, 253):
                    conn.sendall(bytes([255, 254 if self.command == 251 else 252, byte]))
                self.state = 'data'
            elif self.state == 'sub':
                if byte == 255: self.state = 'sub-iac'
            elif self.state == 'sub-iac':
                self.state = 'data' if byte == 240 else 'sub'
        return bytes(clean)


def reader(host, port):
    global received
    while True:
        try:
            with socket.create_connection((host, port), timeout=3) as conn:
                conn.settimeout(3)
                decoder, pending = TelnetFilter(), b''
                # Wait for the actual NSH prompt before issuing the read-only demo.
                while b'ap>' not in pending and b'nsh>' not in pending:
                    chunk = conn.recv(8192)
                    if not chunk: raise OSError('NSH closed')
                    pending = (pending + decoder.feed(chunk, conn))[-16384:]
                conn.sendall(b'flyreflex stream recovery 10000\r\n')
                pending = b''
                while True:
                    chunk = conn.recv(8192)
                    if not chunk: raise OSError('NSH closed')
                    pending += decoder.feed(chunk, conn)
                    if len(pending) > 65536: raise OSError('oversized telemetry')
                    while b'\n' in pending:
                        line, pending = pending.split(b'\n', 1)
                        publish(line)
        except OSError:
            with lock: received = 0.0
            time.sleep(2)


class Handler(SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path != '/step':
            self.send_error(404)
            return
        origin = self.headers.get('Origin')
        if origin and origin != 'http://' + self.headers.get('Host', ''):
            self.send_error(403)
            return
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= 2048:
                raise ValueError('body size')
            result = controller.step(json.loads(self.rfile.read(size)))
            status = 200
        except (ValueError, TypeError):
            result, status = {'error': 'Invalid input'}, 400
        except (OSError, RuntimeError):
            result, status = {'error': 'DATA CONNECTION LOST'}, 503
        body = json.dumps(result).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == '/events':
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.end_headers()
            previous = None
            try:
                while True:
                    with lock:
                        packet = {'connected': bool(received and time.monotonic() - received < 1.5),
                                  'sample': latest}
                    encoded = json.dumps(packet, separators=(',', ':'))
                    if encoded != previous:
                        self.wfile.write(('data: ' + encoded + '\n\n').encode())
                        previous = encoded
                    else:
                        self.wfile.write(b': heartbeat\n\n')
                    self.wfile.flush()
                    time.sleep(.15)
            except (BrokenPipeError, ConnectionResetError):
                pass
            return
        # Serve only web assets; reject dot paths and directory listings.
        if any(part.startswith('.') for part in path.split('/') if part):
            self.send_error(404)
            return
        super().do_GET()

    def list_directory(self, path):
        self.send_error(404)
        return None

    def log_message(self, format, *args):
        if args and any(path in str(args[0]) for path in ('/events', '/step')): return
        super().log_message(format, *args)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8088)
    parser.add_argument('--target-host', default='127.0.0.1')
    parser.add_argument('--target-port', type=int, default=10023)
    args = parser.parse_args()
    controller = Controller(args.target_host, args.target_port, TelnetFilter)
    print(f'FlyReflex: http://127.0.0.1:{args.port} (live source {args.target_host}:{args.target_port})', flush=True)
    ThreadingHTTPServer(('127.0.0.1', args.port), Handler).serve_forever()
