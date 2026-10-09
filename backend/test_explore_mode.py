import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient
from .explore_mode import scenario_catalog,scenario_request,run_explore,ExploreRequest
from .metrics import calculate
from .api import create_app

@pytest.mark.parametrize('index',[0,1,2])
def test_real_presets(index):
    scenario=scenario_catalog()[index];req=scenario_request(scenario).model_copy(update={'seeds':[42],'world':scenario_request(scenario).world.model_copy(update={'rounds':5})})
    if req.variant_world:req=req.model_copy(update={'variant_world':req.variant_world.model_copy(update={'rounds':5})})
    result=run_explore(req)
    assert result==run_explore(req)
    a=result['baseline'][0];b=result['variant'][0]
    assert a['initial']['agents']==b['initial']['agents'] and a['initial']['edges']==b['initial']['edges']
    for run in [a,b]:
        for snapshot,row in zip(run['snapshots'],run['series']):
            metrics=calculate(snapshot['agents'],snapshot['edges'],run['initial']['groups'])
            assert all(row[k]==v for k,v in metrics.items())
    if index==1:
        node=result['selected_nodes']['42']['agent'];degree={agent['id']:sum(agent['id'] in (e['source'],e['target']) for e in a['initial']['edges']) for agent in a['initial']['agents'] if not agent['informed']}
        assert node==min(degree,key=lambda n:(-degree[n],n))
        assert not a['snapshots'][0]['agents'][node]['informed'] and b['snapshots'][0]['agents'][node]['informed']

def test_only_one_legal_change():
    req=scenario_request(scenario_catalog()[0]).model_dump()
    req['variant_world']['incentive']=.7
    with pytest.raises(ValidationError):ExploreRequest(**req)
    req['variant_world']['transmission']=2
    with pytest.raises(ValidationError):ExploreRequest(**req)

def test_explore_saved_and_reproduced(tmp_path):
    with TestClient(create_app(tmp_path/'experiments.sqlite3')) as client:
        req=scenario_request(scenario_catalog()[2]).model_dump();req['seeds']=[42];req['world']['rounds']=5;req['variant_world']['rounds']=5
        response=client.post('/api/explore/run',json=req);assert response.status_code==201
        eid=response.json()['experiment_id']
        assert client.get(f'/api/experiments/{eid}/summary').json()['result']['summary']
        assert client.post(f'/api/experiments/{eid}/reproduce').json()['identical']
        assert client.get(f'/api/experiments/{eid}/trajectory?seed=42&branch=variant&start=0&end=5').json()['snapshots']
        assert client.delete(f'/api/experiments/{eid}').status_code==200
