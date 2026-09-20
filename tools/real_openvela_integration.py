"""Live HTTP bridge + NSH acceptance. Never substitutes a host/mock runtime."""
import argparse
import json
import socket
import threading
import time
import urllib.request
import urllib.error
from pathlib import Path
from http.server import ThreadingHTTPServer
import web_bridge
from interactive_bridge import Controller


class NSH:
    def __init__(self, host, port):
        self.conn = socket.create_connection((host, port), timeout=3)
        self.decoder = web_bridge.TelnetFilter()
        self.read_prompt()

    def read_prompt(self):
        data = b''
        deadline = time.monotonic() + 6
        while time.monotonic() < deadline:
            chunk = self.conn.recv(16384)
            if not chunk:
                raise OSError('NSH disconnected')
            data += self.decoder.feed(chunk, self.conn)
            if b'ap>' in data or b'nsh>' in data:
                return data.decode(errors='replace')
        raise TimeoutError('NSH prompt')

    def command(self, command):
        self.conn.sendall((command + '\r\n').encode())
        return self.read_prompt()

    def guard(self):
        output = self.command('flyreflex guard issue_agent_command FORWARD')
        for line in output.splitlines():
            if line.startswith('{'):
                return json.loads(line)
        raise ValueError('Missing Guard JSON')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=10023)
    parser.add_argument('--output', default='docs/evidence/real-openvela-integration.json')
    args = parser.parse_args()
    control = Controller(args.host, args.port, web_bridge.TelnetFilter)
    web_bridge.controller = control
    server = ThreadingHTTPServer(('127.0.0.1', 0), web_bridge.Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    nsh = NSH(args.host, args.port)
    results = {'target': nsh.command('uname -a'), 'transport': 'HTTP -> Telnet -> openvela'}
    def step(seq, value):
        data = dict(mode='live', session='integration', seq=seq, reset=1, delay=14,
                    sa=value, ra=value, sb=value, rb=value)
        request = urllib.request.Request(f'http://127.0.0.1:{server.server_port}/step',
                                         json.dumps(data).encode(), {'Content-Type': 'application/json'})
        with urllib.request.urlopen(request, timeout=5) as response:
            return json.load(response)
    try:
        with urllib.request.urlopen(f'http://127.0.0.1:{server.server_port}/health', timeout=5) as response:
            results['health'] = json.load(response)
        assert results['health']['status'] == 'ready'
        results['help'] = nsh.command('help')
        for command in ('flyreflex', 'ai_agent', 'lvgldemo'):
            assert command in results['help'], f'Missing built-in {command}'
        results['safe'] = step(0, 0)
        assert results['safe']['action'] == 'FORWARD'
        results['safe_guard'] = nsh.guard()
        assert results['safe_guard']['final'] == 'FORWARD'
        results['danger'] = step(1, 1000)
        assert results['danger']['agent_b'] == 'FORWARD' and results['danger']['action'] == 'ESCAPE'
        results['danger_guard'] = nsh.guard()
        assert results['danger_guard']['fresh'] and results['danger_guard']['final'] == 'ESCAPE'
        # Exercise out-of-range input on the real CLI (HTTP rejects it earlier).
        control.transport.sendall(b'2 1 14 -1 0 -1 0\r\n')
        data = b''
        while b'"latency_ns"' not in data or b'}' not in data:
            data += control.read_chunk()
        line = next(line for line in data.splitlines() if b'FR2 {' in line)
        results['invalid'] = json.loads(line[line.index(b'FR2 ')+4:])
        assert results['invalid']['action'] == 'STOP'
        results['invalid_guard'] = nsh.guard()
        assert results['invalid_guard']['final'] == 'STOP'
        step(3, 1000)
        time.sleep(1.7)
        results['stale_guard'] = nsh.guard()
        assert not results['stale_guard']['fresh'] and results['stale_guard']['final'] == 'STOP'
        # Break the actual live transport; the next HTTP request must fail closed.
        control.transport.shutdown(socket.SHUT_RDWR)
        try:
            step(4, 0)
            raise AssertionError('Disconnected target was accepted')
        except urllib.error.HTTPError as exc:
            assert exc.code == 503
            results['disconnected_http'] = {'status': exc.code, 'body': json.load(exc)}
        results['result'] = 'PASS'
    finally:
        control.close()
        nsh.conn.close()
        server.shutdown()
        server.server_close()
    Path(args.output).write_text(json.dumps(results, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
