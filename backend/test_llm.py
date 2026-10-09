import copy
import json
import time
import pytest
from fastapi.testclient import TestClient
from .api import create_app
from .llm import Ledger,RealProvider,settings
from .pilot import PilotRequest,configuration,run_pilot,replay_result,select_agents
from .social import initial_social,simulate_social
from .decisions import DecisionProvider


@pytest.fixture
def context():
    return {'agent':0,'round':1,'score':.6,'threshold':.5,'informed':True,'neighbors':[1,2]}


@pytest.fixture
def real_config(monkeypatch):
    monkeypatch.setenv('BUTTERFLYLAB_LLM_KEY','test-secret-never-export')
    return dict(settings(),enabled=True,price_verified=True,base_url='https://example.invalid/v1',input_cny_per_million=8,output_cny_per_million=48)


def response(model='gpt-5.6-luna',target=None,usage=True):
    class Response:
        status_code=200
        def raise_for_status(self):pass
        def json(self):
            result={'model':model,'choices':[{'message':{'content':json.dumps({'cooperate':False,'propagate':False,'target':target,'reason':'test-secret-never-export'})}}]}
            if usage:result['usage']={'prompt_tokens':100,'completion_tokens':20,'completion_tokens_details':{'reasoning_tokens':5}}
            return result
    return Response()


def test_free_rule_control_and_mock_replay(tmp_path):
    ledger=Ledger(tmp_path/'ledger.db')
    free=run_pilot(PilotRequest(),ledger,'free')
    assert all(p['delta']['coverage']==0 for p in free['paired'])
    mock=run_pilot(PilotRequest(mode='mock'),ledger,'mock')
    assert len(mock['paired'])==5 and replay_result(mock)['identical']
    assert all(len(b['decisions'])==24 for b in mock['variant'])
    assert ledger.totals()['calls']==0
    assert 'not evidence' in mock['pilot']['conclusion']


def test_initial_selection_and_only_three_agent_calls(tmp_path):
    cfg=configuration(PilotRequest())['world'];initial=initial_social(42,cfg)
    ids=select_agents(initial);assert ids==select_agents(initial)
    class Provider(DecisionProvider):
        def decide(self,context):return {'cooperate':False,'propagate':False,'target':None,'reason':'controlled intervention'},'accepted'
    hybrid=copy.deepcopy(initial);hybrid['config']['decision_mode']='external'
    run=simulate_social(initial=hybrid,selected_agents=ids,provider=Provider())
    assert {d['agent'] for d in run['decisions']}==set(ids)
    assert run['initial']['agents']==initial['agents'] and run['initial']['edges']==initial['edges']
    for frame in run['snapshots'][1:]:assert all(frame['agents'][i]['action']=='compete' for i in ids)
    assert replay_result(run_pilot(PilotRequest(mode='mock',seed_count=1),Ledger(tmp_path/'calls.db'),'unused'))['identical']


@pytest.mark.parametrize('model,target,accepted',[('gpt-5.6-luna',None,True),('other-model',None,False),('gpt-5.6-luna',99,False)])
def test_provider_route_action_usage_and_secret_redaction(tmp_path,monkeypatch,context,real_config,model,target,accepted):
    requests=[]
    monkeypatch.setattr('backend.llm.httpx.post',lambda *a,**kw:(requests.append((a,kw)) or response(model,target)))
    p=RealProvider(Ledger(tmp_path/'budget.db'),'test',real_config)
    action,status=p.decide(context)
    assert bool(action)==accepted and p.usage()['calls']==1
    assert 'test-secret-never-export' not in json.dumps([action,p.usage()])
    assert requests[0][0][0]=='https://example.invalid/v1/chat/completions'
    assert requests[0][1]['json']['max_completion_tokens']==256
    if accepted:assert p.usage()['input_tokens']==100 and p.usage()['reasoning_tokens']==5


def test_missing_usage_conservative_accounting(tmp_path,monkeypatch,context,real_config):
    monkeypatch.setattr('backend.llm.httpx.post',lambda *a,**k:response(usage=False))
    p=RealProvider(Ledger(tmp_path/'budget.db'),'test',real_config);assert p.decide(context)[0]
    assert p.usage()['usage_estimated'] and p.usage()['cost_cny']>0


def test_request_cap_survives_reopen_and_budget_cap(tmp_path):
    path=tmp_path/'budget.db';ledger=Ledger(path)
    for i in range(125):ledger.reserve('all',.001)
    with pytest.raises(ValueError):Ledger(path).reserve('more',.001)
    other=Ledger(tmp_path/'other.db');other.reserve('a',9.9)
    with pytest.raises(ValueError):other.reserve('b',.2)


def test_probe_limit_input_guard_and_free_gates(tmp_path,monkeypatch,context,real_config):
    ledger=Ledger(tmp_path/'budget.db');ledger.reserve('connectivity',1,True)
    with pytest.raises(ValueError):ledger.reserve('connectivity',1,True)
    calls=[];monkeypatch.setattr('backend.llm.httpx.post',lambda *a,**k:calls.append(1))
    p=RealProvider(ledger,'blocked',dict(real_config,price_verified=False));assert not p.decide(context)[0]
    p=RealProvider(ledger,'blocked',real_config);assert not p.decide(dict(context,memory='a'*2000))[0]
    assert not calls


def test_transport_failure_no_error_body_leak(tmp_path,monkeypatch,context,real_config):
    def fail(*a,**k):raise RuntimeError('test-secret-never-export')
    monkeypatch.setattr('backend.llm.httpx.post',fail)
    p=RealProvider(Ledger(tmp_path/'budget.db'),'test',real_config)
    assert p.decide(context)[0] is None
    assert 'test-secret-never-export' not in json.dumps(p.usage())


def test_provider_reported_input_blocks_subsequent_paid_requests(tmp_path,monkeypatch,context,real_config):
    calls=[]
    class Oversized:
        status_code=200
        def raise_for_status(self):pass
        def json(self):
            data=response().json();data['usage']['prompt_tokens']=4498;return data
    monkeypatch.setattr('backend.llm.httpx.post',lambda *a,**k:(calls.append(1) or Oversized()))
    provider=RealProvider(Ledger(tmp_path/'budget.db'),'guard',real_config)
    assert provider.decide(context)[0]
    assert provider.decide(context)[0] is None
    assert calls==[1] and provider.usage()['input_target_exceeded']


def test_cancel_retains_complete_pairs_without_new_calls(tmp_path):
    partial=[];cancelled=False
    def retain(data):
        nonlocal cancelled
        partial.append(data);cancelled=True
    with pytest.raises(InterruptedError):
        run_pilot(PilotRequest(mode='mock'),Ledger(tmp_path/'budget.db'),'cancel',lambda:cancelled,on_pair=retain)
    assert len(partial)==1 and partial[0]['incomplete']
    assert len(partial[0]['paired'])==1 and replay_result(partial[0])['identical']


def test_authentic_recorded_action_enters_engine_without_network(monkeypatch):
    from .verify_pilot import recorded_diagnostic
    def forbid(*a,**k):raise AssertionError('Replay must not call HTTP')
    monkeypatch.setattr('backend.llm.httpx.post',forbid)
    result=recorded_diagnostic()
    assert result['action_entered_engine'] and result['identical']
    assert result['historical_actions_applied']==1 and result['rule_fallbacks']==7


def test_no_unbudgeted_paid_demo_bypass(tmp_path):
    with TestClient(create_app(tmp_path/'experiments.db')) as client:
        assert client.post('/api/decisions/demo',json={'world':{'decision_mode':'external'}}).status_code==422


def test_api_enabled_real_still_requires_verified_price(tmp_path,monkeypatch):
    monkeypatch.setenv('BUTTERFLYLAB_REAL_LLM_ENABLED','1')
    monkeypatch.setenv('BUTTERFLYLAB_LLM_KEY','test-key')
    monkeypatch.setenv('BUTTERFLYLAB_PRICE_VERIFIED','0')
    with TestClient(create_app(tmp_path/'experiments.db')) as client:
        assert client.post('/api/llm/pilots',json={'mode':'real','enable_real':True}).status_code==422
        assert client.get('/api/llm/status').json()['usage']['calls']==0


@pytest.mark.parametrize('rate',['nan','inf','invalid','-1'])
def test_invalid_prices_fail_closed(monkeypatch,rate):
    monkeypatch.setenv('BUTTERFLYLAB_PRICE_VERIFIED','1')
    monkeypatch.setenv('BUTTERFLYLAB_PRICE_SOURCE','operator billing')
    monkeypatch.setenv('BUTTERFLYLAB_INPUT_CNY_PER_MILLION',rate)
    assert not settings()['price_verified']


def test_api_real_default_disabled_validation_persist_and_replay(tmp_path,monkeypatch):
    monkeypatch.delenv('BUTTERFLYLAB_REAL_LLM_ENABLED',raising=False)
    with TestClient(create_app(tmp_path/'experiments.db')) as client:
        assert not client.get('/api/llm/status').json()['real_ready']
        assert client.post('/api/llm/pilots',json={'mode':'real','enable_real':True}).status_code==422
        assert client.post('/api/llm/pilots',json={'seed_count':2}).status_code==422
        assert client.post('/api/llm/pilots',json={'api_key':'bad'}).status_code==422
        rec=client.post('/api/llm/pilots',json={'mode':'mock','seed_count':1}).json();eid=rec['experiment_id']
        for _ in range(100):
            rec=client.get(f'/api/experiments/{eid}/summary').json()
            if rec['experiment_status']!='running':break
            time.sleep(.02)
        assert rec['experiment_status']=='completed'
        assert client.post(f'/api/llm/pilots/{eid}/replay').json()['identical']
        assert client.post(f'/api/experiments/{eid}/reproduce').json()['identical']
    with TestClient(create_app(tmp_path/'experiments.db')) as client:
        assert client.get(f'/api/experiments/{eid}/summary').json()['result']['pilot']['mode']=='mock'


@pytest.mark.parametrize('url',['http://remote.invalid','https://user:pass@example.com/v1','https://example.com?key=x'])
def test_reject_unsafe_provider_url(monkeypatch,url):
    monkeypatch.setenv('BUTTERFLYLAB_LLM_BASE_URL',url)
    with pytest.raises(ValueError):settings()
