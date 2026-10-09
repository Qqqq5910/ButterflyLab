"""Pre-registered, bounded rule versus hybrid comparison, with recorded replay."""
import copy
from typing import Literal
from pydantic import Field, model_validator
from .models import StrictModel
from .social_config import SocialConfig, preset
from .social import initial_social, simulate_social
from .decisions import DecisionProvider
from .research import RunRequest, paired_result
from .llm import RealProvider, settings
from .environment import environment

PROTOCOL='hybrid-pilot-1.0.0'
SEEDS=[42,43,44,45,46]


class PilotRequest(StrictModel):
    experiment_name:str=Field('Information Cascade / LLM pilot',min_length=1,max_length=120)
    mode:Literal['rule','mock','real']='rule'
    seed_count:Literal[1,5]=5
    enable_real:bool=False


def configuration(req):
    # The existing cascade preset uses BA. This protocol explicitly fixes WS as requested.
    world=SocialConfig(**(preset('cascade')|{'network':'small_world','population':50,'rounds':8,'decision_mode':'rule'}))
    return {'experiment_name':req.experiment_name,'world':world.model_dump(),'seeds':SEEDS[:req.seed_count],
            'intervention':None,'pilot':req.model_dump(),'protocol_version':PROTOCOL,'environment':environment(),
            'selection':'Initial unweighted degree descending; ties by numeric Agent ID; top three per seed',
            'primary_metric':'final information coverage','paid_calls_expected':24*req.seed_count if req.mode=='real' else 0}


def select_agents(initial):
    degree={a['id']:0 for a in initial['agents']}
    for edge in initial['edges']:
        degree[edge['source']]+=1;degree[edge['target']]+=1
    return sorted(degree,key=lambda ident:(-degree[ident],ident))[:3]


def result(config, aa, bb, metadata, incomplete=False):
    partial=dict(config,seeds=[a['seed'] for a in aa])
    data=paired_result(RunRequest(**{k:partial[k] for k in ['experiment_name','world','seeds','intervention']}),aa,bb)
    data['configuration']=partial
    deltas=[p['delta']['coverage'] for p in data['paired']]
    consistency=max(sum(x>0 for x in deltas),sum(x<0 for x in deltas))/len(deltas)
    data['pilot']={'mode':config['pilot']['mode'],'protocol_version':PROTOCOL,'primary_metric':'coverage',
                   'pairs':metadata,'direction_consistency':consistency,'incomplete':incomplete,
                   'conclusion':f"{len(deltas)} paired seeds; mean coverage difference {data['summary']['coverage']['mean']:+.4f}. "
                                +('Mock decisions are not evidence about real LLMs.' if config['pilot']['mode']=='mock' else
                                  'Free rule control; no live model calls.' if config['pilot']['mode']=='rule' else
                                  'Exploratory result confined to this simulated setting; no population significance claim.'),
                   'limitation':'Five seeds are exploratory. Live outputs may vary; recorded replay is deterministic.'}
    data['incomplete']=incomplete
    return data


def run_pilot(req,ledger,eid,cancel=None,progress=None,on_pair=None):
    config=configuration(req);aa=[];bb=[];meta=[]
    for index,seed in enumerate(config['seeds']):
        if cancel and cancel():raise InterruptedError('Pilot cancelled before seed')
        initial=initial_social(seed,config['world']);ids=select_agents(initial)
        a=simulate_social(initial=initial,cancel=cancel)
        hybrid=copy.deepcopy(initial)
        hybrid['config']['decision_mode']='rule' if req.mode=='rule' else 'mock' if req.mode=='mock' else 'external'
        provider=RealProvider(ledger,eid,cancel=cancel) if req.mode=='real' else DecisionProvider('mock') if req.mode=='mock' else None
        b=simulate_social(initial=hybrid,cancel=cancel,provider=provider,selected_agents=ids,
                          on_round=lambda t:progress(index*8+t,len(config['seeds'])*8) if progress else None)
        replay=simulate_social(initial=hybrid,tape=b['decisions'],selected_agents=ids)
        identical=all(b[k]==replay[k] for k in ['snapshots','series','events','decisions','transmission_paths','final'])
        if not identical:raise ValueError('Recorded replay mismatch')
        statuses=[d['status'] for d in b['decisions']]
        aa.append(a);bb.append(b);meta.append({'seed':seed,'agents':ids,'accepted':statuses.count('accepted'),
                   'fallbacks':len(statuses)-statuses.count('accepted'),'recorded_replay_identical':identical})
        if on_pair:on_pair(result(config,aa,bb,meta,True))
        if req.mode=='real' and (meta[-1]['fallbacks'] or ledger.totals()['input_target_exceeded']):
            raise ValueError('Pre-experiment quality/budget gate failed; remaining paid seeds stopped')
    return result(config,aa,bb,meta)


def replay_result(data):
    checks=[]
    if not data.get('variant') or len(data['variant'])!=len(data['pilot']['pairs']):raise ValueError('Incomplete replay metadata')
    for a,b,meta in zip(data['baseline'],data['variant'],data['pilot']['pairs']):
        replay=simulate_social(initial=b['initial'],tape=b['decisions'],selected_agents=meta['agents'])
        rule=simulate_social(initial=a['initial'])
        keys=['snapshots','series','events','decisions','transmission_paths','final']
        checks.append({'seed':b['seed'],'identical':all(b[k]==replay[k] and a[k]==rule[k] for k in keys)})
    return {'identical':all(c['identical'] for c in checks),'checks':checks,'mode':'Recorded Replay; no API requests'}
