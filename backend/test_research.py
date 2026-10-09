import time
import sqlite3
import numpy as np
import pytest
from fastapi.testclient import TestClient
from .metrics import gini, disagreement, largest_component, calculate, summarize
from .models import WorldConfig, Intervention
from .simulation import initial_world, simulate
from .research import RunRequest, SearchRequest, comparison, discover, METRICS
from .storage import Store
from .api import create_app

@pytest.mark.parametrize('values,expected',[([],0),([0,0],0),([10,10],0),([0,10],.5),([0,0,12],2/3)])
def test_gini(values,expected):
    assert gini(values)==pytest.approx(expected)

@pytest.mark.parametrize('values,expected',[([],0),([1],0),([0,1],1),([0,.5,1],2/3),([.4,.4],0)])
def test_disagreement(values,expected):
    assert disagreement(values)==pytest.approx(expected)

def test_actual_components_and_isolates():
    agents=[{'id':i} for i in range(3)]
    assert largest_component([],[])==0
    assert largest_component(agents,[])==1/3
    assert largest_component(agents,[{'source':0,'target':1,'weight':1}])==2/3
    assert largest_component(agents,[{'source':0,'target':1,'weight':0}])==1/3

def test_cooperation_opportunities():
    agents=[dict(id=i,opinion=.5,resource=0,action=action,informed=False) for i,action in enumerate(['cooperate','compete'])]
    assert calculate(agents,[],[[0],[1]])['cooperation']==.5
    assert calculate([],[],[])['cooperation']==0

def test_matched_initial_and_zero_intervention():
    req=RunRequest(world=WorldConfig(population=10,rounds=5),seeds=[7,8],intervention=Intervention(magnitude=0))
    r=comparison(req)
    for a,b in zip(r['baseline'],r['variant']):
        assert a['initial']==b['initial']
        assert a['series']==b['series']
        assert a['snapshots']==b['snapshots']
    assert r==comparison(req)

@pytest.mark.parametrize('kind,magnitude',[('resource',-5),('opinion',.1)])
def test_intervention_really_applied(kind,magnitude):
    initial=initial_world(7,WorldConfig(population=10,rounds=5))
    before=initial['agents'][0][kind]
    result=simulate(initial=initial,intervention=Intervention(kind=kind,magnitude=magnitude))
    assert result['initial']==initial
    assert result['snapshots'][0]['agents'][0][kind]==pytest.approx(max(0,min(1,before+magnitude)) if kind=='opinion' else max(0,before+magnitude))
    assert initial['agents'][0][kind]==before

def test_multiseed_summary_matches_independent_calculation():
    r=comparison(RunRequest(world=WorldConfig(population=10,rounds=5),seeds=list(range(5)),intervention=Intervention(magnitude=-10)))
    for m in METRICS:
        deltas=[b['final'][m]-a['final'][m] for a,b in zip(r['baseline'],r['variant'])]
        assert r['summary'][m]['mean']==pytest.approx(np.mean(deltas))
        assert r['summary'][m]['std']==pytest.approx(np.std(deltas,ddof=1))
    assert summarize([.2])['ci95'] is None

def test_store_restart_delete_and_migration(tmp_path):
    path=tmp_path/'lab.db';store=Store(path)
    req=RunRequest(world=WorldConfig(population=10,rounds=5),seeds=[1])
    eid=store.create(req.model_dump());result=comparison(req);store.finish(eid,result)
    assert Store(path).get(eid)['result']==result
    with sqlite3.connect(path) as con: assert con.execute('PRAGMA user_version').fetchone()[0]==1
    store.rename(eid,'saved');assert store.get(eid)['experiment_name']=='saved'
    store.delete(eid)
    with sqlite3.connect(path) as con: assert con.execute('SELECT count(*) FROM artifacts').fetchone()[0]==0
    with pytest.raises(KeyError):store.get(eid)

def test_interrupted_recovery_and_future_schema(tmp_path):
    path=tmp_path/'lab.db';store=Store(path);eid=store.create(RunRequest().model_dump())
    with pytest.raises(ValueError):store.delete(eid)
    store.recover();assert store.get(eid)['experiment_status']=='failed'
    with sqlite3.connect(path) as con:con.execute('PRAGMA user_version=99')
    with pytest.raises(RuntimeError):Store(path)

def test_search_real_results_heldout_and_progress():
    req=SearchRequest(world=WorldConfig(population=10,rounds=5),seeds=[1,2],evaluation_seeds=[101,102],max_experiments=3,metric='inequality',direction='increase')
    updates=[];r=discover(req,lambda d,t:updates.append((d,t)))
    assert updates[-1]==(12,12)
    assert not set(r['discovery_seeds'])&set(r['evaluation_seeds'])
    assert len(r['results'])==3
    assert [c['mean_delta'] for c in r['results']]==sorted([c['mean_delta'] for c in r['results']],reverse=True)
    for c in r['results']:
        independent=comparison(RunRequest(world=req.world,seeds=req.seeds,intervention=c['intervention']),capture=False)
        assert c['mean_delta']==independent['summary'][req.metric]['mean']
    assert r['validation']['configuration']['intervention']==r['results'][0]['intervention']

def wait_done(client,eid):
    for _ in range(200):
        r=client.get('/api/experiments/'+eid).json()
        if r['experiment_status']!='running':return r
        time.sleep(.02)
    raise AssertionError('Job did not finish')

def test_api_persistent_loop_and_reproduction(tmp_path):
    path=tmp_path/'api.db'
    with TestClient(create_app(path)) as client:
        body=RunRequest(world=WorldConfig(population=10,rounds=5),seeds=[1,2],intervention=Intervention()).model_dump()
        response=client.post('/api/experiments',json=body);assert response.status_code==202
        eid=response.json()['experiment_id'];record=wait_done(client,eid)
        assert record['experiment_status']=='completed'
        assert set(METRICS)<=set(record['result']['baseline'][0]['series'][0])
        assert client.post(f'/api/experiments/{eid}/reproduce').json()['identical']
        assert client.patch(f'/api/experiments/{eid}',json={'experiment_name':'saved'}).status_code==200
        exported=client.get(f'/api/experiments/{eid}/export');assert exported.json()['result']==record['result']
        assert 'attachment' in exported.headers['content-disposition']
    with TestClient(create_app(path)) as client:
        assert client.get('/api/experiments').json()['experiments'][0]['experiment_name']=='saved'
        assert client.get(f'/api/experiments/{eid}').json()['result']==record['result']
        assert client.delete(f'/api/experiments/{eid}').status_code==200
        assert client.get(f'/api/experiments/{eid}').status_code==404

@pytest.mark.parametrize('patch',[{'seeds':[]},{'seeds':[1,1]},{'seeds':[-1]},{'world':{'population':9}},{'intervention':{'kind':'opinion','magnitude':2}},{'intervention':{'agent':99}},{'seeds':[1.5]},{'seeds':[True]},{'extra':1}])
def test_api_illegal_parameters(tmp_path,patch):
    with TestClient(create_app(tmp_path/'api.db')) as client:
        body=RunRequest().model_dump();body.update(patch)
        assert client.post('/api/experiments',json=body).status_code==422

def test_search_api_and_legacy_simulate(tmp_path):
    with TestClient(create_app(tmp_path/'api.db')) as client:
        assert client.get('/api/search?max_experiments=25').status_code==422
        body=SearchRequest(world=WorldConfig(population=10,rounds=5),seeds=[1,2],evaluation_seeds=[101,102],max_experiments=1).model_dump()
        eid=client.post('/api/search/jobs',json=body).json()['experiment_id']
        assert wait_done(client,eid)['result']['validation']['seeds']==[101,102]
        assert client.post(f'/api/experiments/{eid}/reproduce').json()['identical']
        body['evaluation_seeds']=[1,2]
        assert client.post('/api/search/jobs',json=body).status_code==422
        assert client.post('/api/simulate',json={'rounds':5}).status_code==200
