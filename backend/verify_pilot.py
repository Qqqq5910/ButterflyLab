"""Free controls and honest historical-action integration; never makes HTTP calls."""
import copy
import json
from pathlib import Path
from .decisions import Decision, DecisionProvider
from .llm import Ledger
from .pilot import PilotRequest, configuration, run_pilot, replay_result
from .social import initial_social, simulate_social


def recorded_diagnostic():
    fixture=json.loads((Path(__file__).resolve().parents[1]/'examples/connectivity-action.json').read_text())
    class Recorded(DecisionProvider):
        def decide(self, context):
            if context['round']==1:
                return Decision(**fixture['action']).model_dump(),'accepted historical connectivity action'
            return None,'explicit rule fallback; no live request'
    initial=initial_social(42,configuration(PilotRequest())['world'])
    hybrid=copy.deepcopy(initial);hybrid['config']['decision_mode']='external'
    run=simulate_social(initial=hybrid,selected_agents=[0],provider=Recorded())
    replay=simulate_social(initial=hybrid,selected_agents=[0],tape=run['decisions'])
    keys=['snapshots','series','events','decisions','transmission_paths','final']
    return {'label':fixture['label'],'configuration':hybrid['config'],'seed':42,'model':fixture['model'],
            'live_requests':0,'historical_actions_applied':1,'rule_fallbacks':7,
            'action_entered_engine':run['snapshots'][1]['agents'][0]['action']=='cooperate',
            'identical':all(run[k]==replay[k] for k in keys),'run':run}


def main():
    out=Path('output/research');out.mkdir(parents=True,exist_ok=True)
    ledger=Ledger(out/'free-verification-budget.db')
    report={}
    for mode in ['rule','mock']:
        data=run_pilot(PilotRequest(mode=mode),ledger,'verification-'+mode)
        report[mode]={'paired':data['paired'],'summary':data['summary']['coverage'],
                      'replay':replay_result(data),'conclusion':data['pilot']['conclusion']}
    diagnostic=recorded_diagnostic()
    report['historical_action']={k:v for k,v in diagnostic.items() if k!='run'}
    (out/'phase2d-historical-action.json').write_text(json.dumps(diagnostic),encoding='utf-8')
    (out/'phase2d-free-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
