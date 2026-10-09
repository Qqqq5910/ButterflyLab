"""Loopback-only free launcher; owns and cleans up exactly its two children."""
import argparse
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--api-port', type=int, default=8001)
    parser.add_argument('--web-port', type=int, default=5173)
    args = parser.parse_args()
    if args.api_port == args.web_port:
        parser.error('API and web ports must differ')
    for port in [args.api_port, args.web_port]:
        if not 1 <= port <= 65535:
            parser.error('Ports must be between 1 and 65535')
        with socket.socket() as probe:
            try:
                probe.bind(('127.0.0.1', port))
            except OSError:
                parser.error(f'Port {port} is occupied; choose a different port')
    env = dict(os.environ, BUTTERFLYLAB_REAL_LLM_ENABLED='0',
               VITE_API_URL='/api', BUTTERFLYLAB_DEV_BACKEND=f'http://127.0.0.1:{args.api_port}')
    children = []
    def stop(signum, frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        children.append(subprocess.Popen([sys.executable, '-m', 'uvicorn', 'backend.api:app',
            '--host', '127.0.0.1', '--port', str(args.api_port)], cwd=ROOT, env=env))
        children.append(subprocess.Popen(['node', 'node_modules/vite/bin/vite.js',
            '--host', '127.0.0.1', '--port', str(args.web_port), '--strictPort'], cwd=ROOT/'frontend', env=env))
        print(f'ButterflyLab: http://127.0.0.1:{args.web_port}/ (Rule/Mock only)', flush=True)
        while all(child.poll() is None for child in children):
            time.sleep(.2)
        return next((child.returncode for child in children if child.returncode), 0)
    except KeyboardInterrupt:
        return 0
    finally:
        for child in children:
            if child.poll() is None:
                child.terminate()
        for child in children:
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()

if __name__ == '__main__':
    raise SystemExit(main())
