"""Local real experiments and lossless reference measurements; never calls model providers."""
import json,time,tracemalloc,zipfile,urllib.request
from pathlib import Path
from .storage import Store
from .trajectories import verify_archive,encode
from .social_config import SocialConfig
from .research import RunRequest,paired_result
from .simulation import simulate,initial_world
from .environment import environment

ROOT=Path('output/research');ROOT.mkdir(parents=True,exist_ok=True)
def measure():
    store=Store();eid='1e651584-0eec-4d25-b7f5-5f5d18e94a55'
    start=time.perf_counter();summary=store.summary(eid);index=time.perf_counter()-start
    raw=encode(summary);path=ROOT/'phase2c-reference-summary.json';path.write_bytes(raw)
    tracemalloc.start();start=time.perf_counter();decoded=json.loads(path.read_bytes());elapsed=time.perf_counter()-start;_,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
    start=time.perf_counter();chunk=store.trajectories.interval(eid,42,'baseline',0,9);chunk_seconds=time.perf_counter()-start
    archive=store.trajectories.archive(eid,summary)
    original=json.loads(Path('output/playwright/phase2b-experiment.json').read_bytes())['result']
    restored=verify_archive(archive);identical=restored==original
    assert identical
    report={'summary_bytes':len(raw),'summary_parse_seconds':elapsed,'summary_python_peak_bytes':peak,'first_index_seconds':index,'chunk_bytes':len(encode(chunk)),'chunk_seconds':chunk_seconds,'archive_bytes':archive.stat().st_size,'restore_identical':identical,'chunk_rounds':10,'measurement':'Local filesystem, Python tracemalloc parse peak; not browser RSS or network latency'}
    (ROOT/'phase2c-after.json').write_bytes(encode(report));print(json.dumps(report),flush=True)

def api(path,body=None):
    req=urllib.request.Request('http://127.0.0.1:8001/api'+path,data=encode(body) if body is not None else None,headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=120) as response:return json.load(response)
def scan(body):
    r=api('/labs',body);eid=r['id'];print('Started',body['experiment_name'],eid,flush=True)
    while r['state'] in ('QUEUED','RUNNING','CANCEL_REQUESTED'):
        time.sleep(1);r=api('/labs/'+eid)
    assert r['state']=='COMPLETED',(r['id'],r['state'],r.get('error'))
    (ROOT/(body['experiment_name']+'.json')).write_bytes(encode(r))
    print('Completed',body['experiment_name'],flush=True);return r

def experiments():
    world=SocialConfig().model_dump();base={'world':world,'seeds':list(range(42,47)),'validation_seeds':list(range(10042,10072)),'max_seconds':3600}
    a=api('/labs/175fcd8d-40da-4934-9aad-dee81b834957')
    b=api('/labs/13d1fe9d-2e8a-4367-8a22-48be7262a78f')
    assert a['state']==b['state']=='COMPLETED'
    (ROOT/'phase2c-BCE-transmission.json').write_bytes(encode(b))
    store=Store();ablations=[]
    for mechanism in ('trust_enabled','cooperation_enabled','diffusion_enabled'):
        req=RunRequest(experiment_name='phase2c-D-'+mechanism,world=SocialConfig(),seeds=list(range(42,72)))
        variant=SocialConfig(**(world|{mechanism:False}));context={'variant_world':variant.model_dump(),'centrality_rank':None}
        eid=store.create(req.model_dump()|{'environment':environment(),'scan_context':context},'scan_cell')
        aa=[];bb=[]
        for seed in req.seeds:aa.append(simulate(initial=initial_world(seed,req.world)));bb.append(simulate(initial=initial_world(seed,variant)))
        result=paired_result(req,aa,bb)|{'scan_context':context};store.finish(eid,result)
        ablations.append({'mechanism':mechanism,'experiment_id':eid,'summary':result['summary']});print('Ablation',mechanism,eid,flush=True)
    report={'A':a['id'],'BCE':b['id'],'D':ablations,'candidate_detected':b['result']['candidate_detected'],'stable_in_validation':b['result']['stable_in_validation']}
    (ROOT/'phase2c-science.json').write_bytes(encode(report));print(json.dumps(report),flush=True)

if __name__=='__main__':
    import sys
    measure() if sys.argv[1]=='measure' else experiments()
