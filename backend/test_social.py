import copy
import pytest
from fastapi.testclient import TestClient
from .social_config import SocialConfig,SOCIAL_VERSION
from .social import initial_social,simulate_social
from .simulation import simulate,initial_world
from .models import Intervention
from .research import RunRequest,SearchRequest,comparison,discover
from .decisions import DecisionProvider,ProviderConfig,Decision
from .studies import StudyRequest,study
from .api import create_app
from .test_research import wait_done

@pytest.mark.parametrize('network',['small_world','random','scale_free'])
def test_network_generation_and_reproducibility(network):
    c=SocialConfig(population=10,rounds=5,network=network)
    assert initial_world(42,c)==initial_world(42,c)
    assert simulate(42,c)==simulate(42,c)
    assert initial_world(42,c)['config']['engine']==SOCIAL_VERSION

def test_parameters_change_world_and_disconnected_graph_stays_disconnected():
    a=initial_world(7,SocialConfig(population=10,rounds=5,resource_scale=20))
    b=initial_world(7,SocialConfig(population=10,rounds=5,resource_scale=40,initial_trust=.8))
    assert b['agents'][0]['resource']==pytest.approx(2*a['agents'][0]['resource'])
    assert b['edges'][0]['weight']==.8
    c=SocialConfig(population=10,rounds=5,network='random',edge_probability=0)
    r=simulate(7,c)
    assert not r['initial']['edges'] and r['final']['largest_component']==.1

@pytest.mark.parametrize('field,value',[('neighbor_count',3),('neighbor_count',50),('information_origin',50),('trust_speed',.8),('transmission',1.1)])
def test_invalid_social_parameters(field,value):
    with pytest.raises(ValueError):SocialConfig(**{field:value})

def test_trust_influences_next_decisions():
    common=dict(population=10,rounds=5,resource_distribution='equal',resource_scale=60,cooperation_distribution='equal',cooperation_mean=.5,cooperation_threshold=.55,relationships_enabled=False,trust_enabled=False,incentive=.3)
    low=simulate(42,SocialConfig(**common,initial_trust=0))
    high=simulate(42,SocialConfig(**common,initial_trust=1))
    assert low['series'][1]['cooperation']==0
    assert high['series'][1]['cooperation']>low['series'][1]['cooperation']

def test_resource_economy_and_real_feedback():
    c=SocialConfig(population=10,rounds=5,cooperation_threshold=0,trust_speed=.1,initial_trust=.2,treasury=3)
    r=simulate(42,c)
    opening=sum(a['resource'] for a in r['initial']['agents'])+3
    for frame in r['snapshots']:
        assert sum(a['resource'] for a in frame['agents'])+frame['treasury']==pytest.approx(opening)
        assert frame['treasury']>=-1e-8
        assert all(a['resource']>=0 for a in frame['agents'])
    assert r['snapshots'][1]['agents'][0]['resource']!=r['initial']['agents'][0]['resource']
    assert r['snapshots'][1]['edges'][0]['weight']>.2

def test_diffusion_paths_use_opening_round_edges():
    c=SocialConfig(population=10,rounds=10,transmission=1,initial_trust=1,cooperation_threshold=0,relationships_enabled=False)
    r=simulate(3,c)
    assert r['transmission_paths']
    for event in r['transmission_paths']:
        old=r['snapshots'][event['round']-1]
        assert any({e['source'],e['target']}=={event['source'],event['target']} for e in old['edges'])
        assert old['agents'][event['source']]['informed'] and not old['agents'][event['target']]['informed']

@pytest.mark.parametrize('mechanism',['trust_enabled','cooperation_enabled','diffusion_enabled','relationships_enabled'])
def test_mechanism_ablation_stops_corresponding_update(mechanism):
    c=SocialConfig(population=10,rounds=5,**{mechanism:False})
    r=simulate(42,c);initial=r['snapshots'][0];final=r['snapshots'][-1]
    if mechanism=='trust_enabled':assert all(e['weight']==c.initial_trust for e in final['edges'])
    elif mechanism=='cooperation_enabled':assert [a['resource'] for a in initial['agents']]==[a['resource'] for a in final['agents']]
    elif mechanism=='diffusion_enabled':
        assert [a['opinion'] for a in initial['agents']]==[a['opinion'] for a in final['agents']]
        assert [a['informed'] for a in initial['agents']]==[a['informed'] for a in final['agents']]
        assert not r['transmission_paths']
    else:assert len(initial['edges'])==len(final['edges'])

def test_30_paired_seeds_intervention_and_replay():
    q=RunRequest(world=SocialConfig(population=10,rounds=5),seeds=list(range(30)),intervention=Intervention(magnitude=-1))
    r=comparison(q)
    assert len(r['paired'])==30 and r==comparison(q)
    for a,b in zip(r['baseline'],r['variant']):
        assert a['initial']==b['initial']
        for i in range(1,10):assert a['snapshots'][0]['agents'][i]==b['snapshots'][0]['agents'][i]
        assert a['snapshots'][0]['edges']==b['snapshots'][0]['edges']
    assert r['summary']['mean_trust']['n']==30

def test_mock_structured_actions_budget_and_tape_replay():
    c=SocialConfig(population=10,rounds=5,decision_mode='mock')
    provider=DecisionProvider(config=ProviderConfig(max_calls=3,token_budget=100000))
    r=simulate_social(42,c,provider=provider)
    assert r['provider_usage']['calls']==3 and len(r['decisions'])==50
    replay=simulate_social(42,c,tape=r['decisions'])
    assert r['snapshots']==replay['snapshots'] and r['decisions']==replay['decisions']
    with pytest.raises(ValueError):Decision(cooperate='yes',propagate=True,target=1,reason='invalid')
    bad=copy.deepcopy(r['decisions']);bad[0]['decision']['target']=999
    with pytest.raises(ValueError):simulate_social(42,c,tape=bad)

def test_invalid_external_output_falls_back_without_mutation(monkeypatch):
    class Response:
        def raise_for_status(self):pass
        def json(self):return {'choices':[{'message':{'content':'{"cooperate":true,"propagate":true,"target":999,"reason":"bad"}'}}]}
    monkeypatch.setattr('backend.decisions.httpx.post',lambda *a,**k:Response())
    provider=DecisionProvider('external',ProviderConfig(max_calls=2,token_budget=100000),key='secret-test-key')
    r=simulate_social(42,SocialConfig(population=10,rounds=5,decision_mode='external'),provider=provider)
    assert provider.failures==2
    assert 'secret-test-key' not in str(r)
    assert all(d['decision']['target'] is None for d in r['decisions'])

def test_grid_keeps_all_cells_and_ablation_matches_initial():
    q=StudyRequest(world=SocialConfig(population=10,rounds=5),seeds=[42,43],kind='sensitivity',values=[0,.1],second_values=[0,.5])
    r=study(q)
    assert len(r['cells'])==4 and r==study(q)
    a=study(StudyRequest(world=q.world,seeds=q.seeds,mechanism='diffusion_enabled'))
    assert a['cells'][0]['summary']['coverage']['mean']<=0

def test_social_search_heldout_truth():
    q=SearchRequest(world=SocialConfig(population=10,rounds=5),seeds=[42,43],evaluation_seeds=[1042,1043],max_experiments=2,metric='mean_trust')
    r=discover(q)
    assert not set(r['discovery_seeds'])&set(r['evaluation_seeds'])
    assert r['validation']==comparison(RunRequest(world=q.world,seeds=q.evaluation_seeds,intervention=r['results'][0]['intervention'],experiment_name=q.experiment_name))

def test_world_persistence_branch_social_experiment_and_legacy(tmp_path):
    path=tmp_path/'experiments.db'
    with TestClient(create_app(path)) as client:
        cfg=SocialConfig(population=10,rounds=5).model_dump()
        world=client.post('/api/worlds',json={'name':'test','configuration':cfg}).json()
        branch=client.post('/api/worlds',json={'name':'branch','configuration':cfg,'parent_id':world['world_id']}).json()
        assert branch['parent_id']==world['world_id']
        req={'world':cfg,'seeds':[42,43],'experiment_name':'new','intervention':{'kind':'resource','magnitude':-1}}
        record=client.post('/api/experiments',json=req).json();eid=record['experiment_id'];wait_done(client,eid)
        assert client.post(f'/api/experiments/{eid}/reproduce').json()['identical']
        legacy=client.post('/api/experiments',json={'seeds':[42],'world':{'population':10,'rounds':5}}).json();wait_done(client,legacy['experiment_id'])
        assert client.get('/api/experiments/'+legacy['experiment_id']).json()['engine_version']=='0.2.0'
        assert client.post('/api/experiments/'+legacy['experiment_id']+'/reproduce').json()['identical']
    with TestClient(create_app(path)) as client:
        assert client.get('/api/worlds/'+world['world_id']).json()==world
        assert client.get('/api/experiments/'+eid).json()['engine_version']==SOCIAL_VERSION
        assert client.post('/api/decisions/demo',json={'world':cfg|{'decision_mode':'mock'}}).json()['replay_identical']

def test_external_requires_explicit_provider_and_tape_is_persisted(tmp_path):
    with TestClient(create_app(tmp_path/'experiments.db')) as client:
        cfg=SocialConfig(population=10,rounds=5).model_dump()
        assert client.post('/api/experiment',json={'world':cfg|{'decision_mode':'external'},'seeds':[42]}).status_code==422
        result=client.post('/api/decisions/demo',json={'world':cfg|{'decision_mode':'mock'}}).json()
        saved=client.get('/api/worlds/'+result['world_id']).json()
        assert saved['configuration']['decision_demo']['run']['decisions']==result['run']['decisions']
        assert 'key' not in saved['configuration']['decision_demo']['provider_configuration']
