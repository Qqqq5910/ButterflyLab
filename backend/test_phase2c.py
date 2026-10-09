import json,time,threading,sqlite3
import pytest
from fastapi.testclient import TestClient
from .api import create_app
from .storage import Store
from .research import RunRequest,comparison
from .social_config import SocialConfig
from .exploration import ExplorationRequest,configure,detect_regions,replay_cell
from .trajectories import verify_archive
from .jobs import Jobs

def wait(client,path):
    for _ in range(500):
        r=client.get(path).json()
        state=r.get('state',r.get('experiment_status'))
        if state not in ('running','RUNNING','QUEUED','CANCEL_REQUESTED'):return r
        time.sleep(.01)
    raise AssertionError('Task timeout')

@pytest.mark.parametrize('p,good,bad',[('trust_speed',.2,.6),('incentive',.5,1.1),('transmission',0,-1),('opinion_speed',1,2),('degree',4,3),('magnitude',-50,-51),('centrality',1,2)])
def test_ranges(p,good,bad):
    configure(SocialConfig(population=10,rounds=5),p,good)
    with pytest.raises(ValueError):configure(SocialConfig(population=10,rounds=5),p,bad)

def test_disjoint_budget():
    with pytest.raises(ValueError):ExplorationRequest(seeds=[42],validation_seeds=[42,43])
    with pytest.raises(ValueError):ExplorationRequest(max_simulations=4)

def test_detection():
    def cell(x,values):return {'x':x,'paired':[{'seed':i,'intervention':{'coverage':v}} for i,v in enumerate(values)]}
    r=detect_regions([cell(0,[0,0]),cell(.5,[.01,.01]),cell(1,[.9,.9])],'coverage',.2)
    assert r[0]['candidate'] and r[0]['low']==.5
    assert not r[1]['candidate']

def test_api_cancel_retains_completed_pairs(tmp_path):
    with TestClient(create_app(tmp_path/'test.db')) as client:
        body={'world':SocialConfig(population=30,rounds=30).model_dump(),'seeds':list(range(42,142)),'validation_seeds':[1000,1001],'values':[0,.5,1]}
        eid=client.post('/api/labs',json=body).json()['id']
        for _ in range(1000):
            status=client.get('/api/jobs/'+eid).json()
            if status['completed']>=2:break
            time.sleep(.01)
        assert status['completed']>=2
        assert client.post('/api/labs/'+eid+'/cancel').status_code==200
        record=wait(client,'/api/labs/'+eid)
        assert record['state']==record['task']['state']=='CANCELLED'
        partial=record['result']['partial_cell']
        assert partial['completed_seeds']
        child=client.get('/api/experiments/'+partial['experiment_id']).json()
        assert child['experiment_status']=='cancelled' and child['result']['incomplete']
        done=record['task']['completed'];time.sleep(.05)
        assert client.get('/api/jobs/'+eid).json()['completed']==done

def test_archive_download_exact(tmp_path):
    with TestClient(create_app(tmp_path/'test.db')) as client:
        store=client.app.state.store;req=RunRequest(world=SocialConfig(population=10,rounds=5),seeds=[42,43])
        result=comparison(req);eid=store.create(req.model_dump());store.finish(eid,result)
        job=client.post('/api/experiments/'+eid+'/archive').json()
        assert wait(client,'/api/jobs/'+job['job_id'])['state']=='COMPLETED'
        response=client.get(job['download_url']);assert response.status_code==200
        path=tmp_path/'download.zip';path.write_bytes(response.content)
        assert verify_archive(path)==result
        network=client.get(f'/api/experiments/{eid}/trajectory?seed=42&start=0&end=1&view=network').json()
        assert all('memory' not in a for s in network['snapshots'] for a in s['agents'])
        full=client.get(f'/api/experiments/{eid}/trajectory?seed=42&start=0&end=1&agent=0').json()
        assert all(a['id']==0 for s in full['snapshots'] for a in s['agents'])

def test_budget_and_restart_state(tmp_path):
    jobs=Jobs(tmp_path/'budget.db')
    def work(cancel,queued):
        while not cancel():time.sleep(.001)
        raise InterruptedError()
    jobs.submit('budget',10,.01,work);jobs.shutdown()
    assert jobs.get('budget')['state']=='CANCELLED'
    with jobs.connect() as c:c.execute("INSERT INTO jobs VALUES ('interrupted','RUNNING',2,10,100,NULL,'now')")
    jobs.recover();assert jobs.get('interrupted')['state']=='FAILED'

def test_study_job_cancel_and_partial(tmp_path):
    with TestClient(create_app(tmp_path/'test.db')) as client:
        body={'world':SocialConfig(population=30,rounds=30).model_dump(),'seeds':list(range(42,142))}
        response=client.post('/api/studies/jobs',json=body);assert response.status_code==202
        eid=response.json()['world_id']
        for _ in range(500):
            if client.get('/api/jobs/'+eid).json()['completed']>=1:break
            time.sleep(.01)
        client.post('/api/experiments/'+eid+'/cancel')
        assert wait(client,'/api/jobs/'+eid)['state']=='CANCELLED'
        record=client.get('/api/worlds/'+eid).json()
        assert record['configuration']['state']=='CANCELLED'
        assert record['configuration']['result']['incomplete']
        assert record['configuration']['result']['cells'][0]['paired']

def test_chunks_archive_legacy(tmp_path):
    store=Store(tmp_path/'test.db');req=RunRequest(world=SocialConfig(population=10,rounds=5),seeds=[42,43])
    result=comparison(req);eid=store.create(req.model_dump());store.finish(eid,result)
    assert store.get(eid)['result']==result
    assert Store(store.path).get(eid)['result']==result
    assert not store.summary(eid)['result']['baseline'][0]['snapshots']
    interval=store.trajectories.interval(eid,42,'baseline',2,4)
    assert interval['snapshots']==result['baseline'][0]['snapshots'][2:5]
    path=store.trajectories.archive(eid,store.summary(eid));assert verify_archive(path)==result
    old=store.create(req.model_dump())
    with store.connect() as c:
        c.execute('INSERT INTO artifacts VALUES (?,?,?)',(old,'{}',json.dumps(result)))
        c.execute("UPDATE experiments SET experiment_status='completed' WHERE experiment_id=?",(old,))
    assert store.summary(old)['result']['paired']==result['paired']
    assert store.get(old)['result']==result

def test_scan_api_replay_grid(tmp_path):
    with TestClient(create_app(tmp_path/'test.db')) as client:
        body={'world':SocialConfig(population=10,rounds=5).model_dump(),'seeds':[42,43],'validation_seeds':[100,101],'values':[0,1],'second_parameter':'incentive','second_values':[0,1]}
        response=client.post('/api/labs',json=body);assert response.status_code==202
        eid=response.json()['id'];record=wait(client,'/api/labs/'+eid)
        assert record['state']=='COMPLETED',record
        assert len(record['result']['cells'])==4
        c=record['result']['cells'][0];assert c['summary']['coverage']['n']==2
        assert c['series'] and c['density']
        assert client.post('/api/experiments/'+c['experiment_id']+'/reproduce').json()['identical']
        assert client.get('/api/experiments/'+c['experiment_id']+'/trajectory?seed=42&start=0&end=100').status_code==422
        assert client.post('/api/labs',json=body|{'values':[-1,1]}).status_code==422

def test_critical_independent(tmp_path):
    with TestClient(create_app(tmp_path/'test.db')) as client:
        body={'world':SocialConfig(population=10,rounds=5).model_dump(),'seeds':[42,43],'validation_seeds':[100,101],'values':[0,1],'mode':'criticality','scales':[10],'topologies':['small_world'],'refinement_points':1}
        eid=client.post('/api/labs',json=body).json()['id'];r=wait(client,'/api/labs/'+eid)
        assert r['state']=='COMPLETED',r
        assert len(r['result']['cells'])==3
        assert r['result']['validation'][0]['cells'][0]['seeds']==[100,101]

def test_cancel_capacity(tmp_path):
    jobs=Jobs(tmp_path/'jobs.db',capacity=2);started=threading.Event()
    def work(cancel,queued):
        started.set()
        while not cancel():time.sleep(.005)
        raise InterruptedError()
    jobs.submit('first',10,100,work);assert started.wait(2)
    jobs.submit('second',10,100,work)
    with pytest.raises(ValueError):jobs.submit('third',10,100,work)
    jobs.cancel('first');jobs.cancel('second');jobs.shutdown()
    assert jobs.get('first')['state']=='CANCELLED'
    assert jobs.get('second')['state']=='CANCELLED'
    assert Jobs(tmp_path/'jobs.db').get('first')['state']=='CANCELLED'

def test_failure_budget(tmp_path):
    jobs=Jobs(tmp_path/'jobs.db')
    def fail(cancel,queued):raise RuntimeError('actual failure')
    jobs.submit('failure',1,100,fail);jobs.shutdown()
    assert jobs.get('failure')['state']=='FAILED'
    assert 'actual failure' in jobs.get('failure')['error']

def test_opening_database_does_not_recover_live_jobs(tmp_path):
    jobs=Jobs(tmp_path/'jobs.db');event=threading.Event()
    jobs.submit('live',1,10,lambda cancel,queued:event.wait(2))
    other=Jobs(tmp_path/'jobs.db')
    assert other.get('live')['state'] in ('QUEUED','RUNNING')
    event.set();jobs.shutdown();other.shutdown()
