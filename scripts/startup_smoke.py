"""Exercise the real Unix launcher and free API, including process cleanup."""
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import tempfile
import time
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]

def request(port, path, body=None):
    data = None if body is None else json.dumps(body).encode()
    with urlopen(Request(f'http://127.0.0.1:{port}{path}', data=data,
                        headers={'Content-Type':'application/json'}), timeout=10) as response:
        return json.load(response)

def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0))
        return sock.getsockname()[1]

def main():
    api, web = free_port(), free_port()
    while api == web:
        web = free_port()
    with tempfile.TemporaryDirectory() as temp:
        env = dict(os.environ, BUTTERFLYLAB_DB=str(Path(temp)/'experiments.sqlite3'),
                   BUTTERFLYLAB_REAL_LLM_ENABLED='0', BUTTERFLYLAB_LLM_KEY='')
        with open(Path(temp)/'startup.log','w+') as log:
            process = subprocess.Popen(['sh','scripts/free-demo.sh','--api-port',str(api),
                                       '--web-port',str(web)], cwd=ROOT, env=env, stdout=log, stderr=log)
            try:
                deadline=time.monotonic()+120
                while True:
                    try:
                        health=request(web,'/api/health')
                        with urlopen(f'http://127.0.0.1:{web}/',timeout=2) as response:
                            assert b'ButterflyLab' in response.read()
                        break
                    except Exception:
                        if process.poll() is not None or time.monotonic()>deadline:
                            log.seek(0); print(log.read()); raise RuntimeError('Startup failed')
                        time.sleep(.5)
                world=request(web,'/api/scenarios')['cascade']
                experiment=request(web,'/api/experiments?light=true',{
                    'experiment_name':'CI free cascade','world':world,'seeds':[42,43,44,45,46],
                    'intervention':{'kind':'information','agent':1,'magnitude':1}})
                eid=experiment['experiment_id']
                deadline=time.monotonic()+90
                while experiment['experiment_status']=='running':
                    assert time.monotonic()<deadline
                    time.sleep(.2)
                    experiment=request(web,f'/api/experiments/{eid}/summary')
                assert experiment['experiment_status']=='completed'
                assert request(web,f'/api/experiments/{eid}/reproduce',{})['identical']
                assert not request(web,'/api/llm/status')['real_ready']
                print('PASS: launcher, frontend, proxied health, 50-Agent five-seed A/B, exact reproduction, free gate')
            finally:
                if process.poll() is None:
                    process.send_signal(signal.SIGTERM)
                    process.wait(timeout=20)
            assert process.returncode==0
            for port in [api,web]:
                with socket.socket() as sock:
                    assert sock.connect_ex(('127.0.0.1',port)) != 0, f'Child still listening on {port}'
            print('PASS: launcher and both owned services exited; temporary database removed')

if __name__=='__main__': main()
