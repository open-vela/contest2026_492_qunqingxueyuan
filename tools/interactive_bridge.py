"""Serialized request/reply transport to the unchanged C safety engine."""
import json
import os
import queue
import socket
import subprocess
import threading
import time
from pathlib import Path


class Controller:
    def __init__(self, host, port, decoder):
        self.host, self.port, self.decoder_class = host, port, decoder
        self.lock = threading.Lock()
        self.session = None
        self.transport = None
        self.process = None
        self.pending = b''

    def close(self):
        if self.transport:
            self.transport.close()
        if self.process:
            try:
                self.process.stdin.close()
            except (BrokenPipeError, OSError):
                pass
            try:
                self.process.wait(timeout=.5)
            except subprocess.TimeoutExpired:
                self.process.terminate()
        self.transport = self.process = None
        self.session = None
        self.pending = b''

    def read_chunk(self):
        if self.transport:
            chunk = self.transport.recv(4096)
            if not chunk:
                raise OSError('openvela disconnected')
            return self.decoder.feed(chunk, self.transport)
        try:
            chunk = self.lines.get(timeout=2)
        except queue.Empty as exc:
            raise OSError('C core timed out') from exc
        if not chunk:
            raise OSError('C core stopped')
        return chunk

    def connect(self, session, mode):
        self.close()
        if mode == 'live':
            self.transport = socket.create_connection((self.host, self.port), timeout=2)
            self.transport.settimeout(2)
            self.decoder = self.decoder_class()
            banner = b''
            deadline = time.monotonic() + 4
            while b'ap>' not in banner and b'nsh>' not in banner:
                if time.monotonic() > deadline:
                    raise OSError('NSH prompt unavailable')
                banner = (banner + self.read_chunk())[-8192:]
            self.transport.sendall(b'flyreflex control\r\n')
        else:
            root = Path(__file__).resolve().parents[1]
            if os.name == 'nt':
                linux = '/mnt/' + root.drive[0].lower() + root.as_posix()[2:]
                distro = os.environ.get('FLYREFLEX_WSL_DISTRO')
                command = ['wsl'] + (['-d', distro] if distro else []) + ['--', linux + '/build/flyreflex_host', 'control']
            else:
                command = [str(root / 'build/flyreflex_host'), 'control']
            self.process = subprocess.Popen(command, stdin=subprocess.PIPE,
                                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            self.lines = queue.Queue()
            process, lines = self.process, self.lines
            def pump():
                for line in iter(process.stdout.readline, b''):
                    lines.put(line)
                lines.put(b'')
            threading.Thread(target=pump, daemon=True).start()
        deadline = time.monotonic() + 4
        while b'FR2 READY' not in self.pending:
            if time.monotonic() > deadline:
                raise OSError('Firmware needs flyreflex control')
            self.pending = (self.pending + self.read_chunk())[-8192:]
        self.pending = b''
        self.session = (session, mode)

    def step(self, data):
        if not isinstance(data, dict) or data.get('mode') not in ('demo', 'live'):
            raise ValueError('mode')
        session = data.get('session')
        if not isinstance(session, str) or not 1 <= len(session) <= 80:
            raise ValueError('session')
        for field, maximum in [('seq', 1000000000), ('reset', 1), ('delay', 40),
                               ('sa', 1000), ('ra', 1000), ('sb', 1000), ('rb', 1000)]:
            if type(data.get(field)) is not int or not 0 <= data[field] <= maximum:
                raise ValueError(field)
        with self.lock:
            try:
                fresh = self.session != (session, data['mode'])
                if fresh:
                    self.connect(session, data['mode'])
                values = [data['seq'], 1 if fresh else data['reset'], data['delay'],
                          data['sa'], data['ra'], data['sb'], data['rb']]
                payload = (' '.join(map(str, values)) + '\n').encode()
                if self.transport:
                    self.transport.sendall(payload.replace(b'\n', b'\r\n'))
                else:
                    self.process.stdin.write(payload)
                    self.process.stdin.flush()
                deadline = time.monotonic() + 3
                while time.monotonic() < deadline:
                    while b'\n' in self.pending:
                        line, self.pending = self.pending.split(b'\n', 1)
                        marker = line.find(b'FR2 {')
                        if marker < 0:
                            continue
                        result = json.loads(line[marker + 4:])
                        expected = 'openvela' if data['mode'] == 'live' else 'host-reference'
                        if result.get('seq') != data['seq'] or result.get('source') != expected:
                            raise OSError('Unexpected telemetry source or sequence')
                        result['restarted'] = fresh
                        return result
                    self.pending += self.read_chunk()
                    if len(self.pending) > 16384:
                        raise OSError('Oversized response')
                raise OSError('No matching response')
            except Exception:
                self.close()
                raise
