"""Synchronous bounded agents and addressable common random numbers."""
import copy, hashlib, json
from collections import defaultdict
import networkx as nx
from .models import WorldConfig, Intervention
from .metrics import calculate, change_points
ENGINE_VERSION='0.2.0'
def random_value(seed,*parts):
    raw=json.dumps([seed,*parts],separators=(',',':')).encode()
    return int.from_bytes(hashlib.blake2b(raw,digest_size=8).digest(),'big')/2**64
def clip(x,low=0,high=1): return max(low,min(high,x))
def initial_world(seed=42,config=None):
    from .social_config import is_social
    if is_social(config):
        from .social import initial_social
        return initial_social(seed,config)
    cfg=config or WorldConfig(); n=cfg.population
    if cfg.network=='small_world': graph=nx.watts_strogatz_graph(n,4,.15,seed=seed)
    elif cfg.network=='random': graph=nx.gnp_random_graph(n,min(1,5/(n-1)),seed=seed)
    else: graph=nx.stochastic_block_model([n//2,n-n//2],[[.24,.025],[.025,.24]],seed=seed)
    components=sorted([sorted(c) for c in nx.connected_components(graph)])
    for a,b in zip(components,components[1:]): graph.add_edge(a[0],b[0])
    edges=[]
    for a,b in sorted((min(a,b),max(a,b)) for a,b in graph.edges):
        w=.4+.5*random_value(seed,'trust',a,b)
        graph[a][b]['weight']=w; edges.append({'source':a,'target':b,'weight':w})
    groups=[sorted(c) for c in nx.community.greedy_modularity_communities(graph,weight='weight')]
    positions=nx.spring_layout(graph,seed=17,iterations=80)
    agents=[]
    for i in range(n):
        u=random_value(seed,'resource',i); v=random_value(seed,'opinion',i)
        resource=60 if cfg.resource_distribution=='equal' else (30+60*u if cfg.resource_distribution=='uniform' else 12+150*u**3)
        opinion=v if cfg.opinion_distribution=='uniform' else ((.1 if i%2 else .8)+.1*v if cfg.opinion_distribution=='polarized' else .45+.1*v)
        propensity=clip(.55+cfg.heterogeneity*(random_value(seed,'propensity',i)-.5))
        agents.append({'id':i,'label':f'A{i+1:02d}','role':['builder','mediator','trader','organizer','scout'][i%5],
          'goal':'balance private resources and neighborhood cooperation','initial_resource':resource,'resource':resource,
          'opinion':opinion,'cooperation':propensity,'strategy':'reciprocal' if i%3 else 'resource-sensitive',
          'action':'cooperate' if propensity>=cfg.cooperation_threshold else 'compete','informed':i==0,'memory':[],
          'x':float(positions[i][0]),'y':float(positions[i][1])})
    return {'seed':seed,'config':cfg.model_dump(),'agents':agents,'edges':edges,'groups':groups}
def intervention_cost(i):
    if isinstance(i,dict):
        if 'resource_delta' in i: return 1+abs(float(i.get('resource_delta',0)))/20
        i=Intervention(**i)
    if not i or i.magnitude==0: return 0.0
    return 1+abs(i.magnitude)/(20 if i.kind=='resource' else .2)
def apply_intervention(world,i):
    if not i: return []
    if i.kind in ['resource','opinion']:
        a=world['agents'][i.agent]; before=a[i.kind]; a[i.kind]=clip(before+i.magnitude,0,200 if i.kind=='resource' else 1); after=a[i.kind]
    elif i.kind=='trust':
        e=next((e for e in world['edges'] if {e['source'],e['target']}=={i.agent,i.target}),None)
        if e is None: raise ValueError(f'No relationship between A{i.agent+1:02d} and A{i.target+1:02d}.')
        before=e['weight']; e['weight']=clip(before+i.magnitude,.01,1); after=e['weight']
    else:
        key='cooperation_threshold' if i.kind=='threshold' else 'transmission'
        before=world['config'][key]; world['config'][key]=clip(before+i.magnitude); after=world['config'][key]
    return [{'round':0,'type':'intervention','agent':i.agent,'target':i.target if i.kind=='trust' else None,
      'before':before,'after':after,'detail':f'{i.kind}: {before:.4f} → {after:.4f}','evidence':'executed intervention',
      'requested_magnitude':i.magnitude,'actual_change':after-before}]
def simulate(seed=42,config=None,intervention=None,*,initial=None,cancel=None,capture=True):
    from .social_config import is_social
    if is_social(initial.get('config') if initial else config):
        from .social import simulate_social
        return simulate_social(seed,config,intervention,initial,capture,cancel)
    if config is None: config=WorldConfig()
    if isinstance(config,int): config=WorldConfig(rounds=config)
    if isinstance(config,dict): config=WorldConfig(**config)
    if isinstance(intervention,dict):
        if 'resource_delta' in intervention:
            raw_agent=intervention.get('agent', 'A01'); agent=int(str(raw_agent).replace('A',''))-1 if isinstance(raw_agent,str) else int(raw_agent)
            intervention=Intervention(kind='resource',agent=max(0,agent),magnitude=float(intervention['resource_delta']))
        else: intervention=Intervention(**intervention)
    original=copy.deepcopy(initial or initial_world(seed,config)); world=copy.deepcopy(original)
    cfg=world['config']; seed=world['seed']; n=len(world['agents']); events=apply_intervention(world,intervention); snapshots=[]; series=[]
    adjacency=defaultdict(list)
    for e in world['edges']:
        adjacency[e['source']].append((e['target'],e)); adjacency[e['target']].append((e['source'],e))
    def record(t):
        metrics={'round':t,**calculate(world['agents'],world['edges'],world['groups'])}; series.append(metrics)
        if capture: snapshots.append({'round':t,'agents':copy.deepcopy(world['agents']),'edges':copy.deepcopy(world['edges']),'metrics':metrics})
    record(0)
    for t in range(1,cfg['rounds']+1):
        if cancel and cancel(): raise InterruptedError('Experiment cancelled at round boundary.')
        old=copy.deepcopy(world['agents']); new=world['agents']; adopted=[]
        for i,a in enumerate(new):
            neighbors=adjacency[i]; total=sum(e['weight'] for _,e in neighbors) or 1
            peer_coop=sum(e['weight']*(old[j]['action']=='cooperate') for j,e in neighbors)/total
            peer_opinion=sum(e['weight']*old[j]['opinion'] for j,e in neighbors)/total if neighbors else old[i]['opinion']
            scarcity=max(0,(40-old[i]['resource'])/40)
            scarcity_weight=.3 if a['strategy']=='resource-sensitive' else .2
            score=.45*old[i]['cooperation']+.4*peer_coop+.15*old[i]['opinion']-scarcity_weight*scarcity
            score+=.12*(random_value(seed,'action',t,i)-.5)
            action='cooperate' if score>=cfg['cooperation_threshold'] else 'compete'
            gain=2.4*peer_coop+(0 if action=='cooperate' else 1.0)-1.4
            resource=clip(old[i]['resource']+gain,0,200)
            opinion=clip(old[i]['opinion']+.10*(peer_opinion-old[i]['opinion'])+.02*(peer_coop-.5))
            propensity=clip(old[i]['cooperation']+.045*(peer_coop-.5)-.012*scarcity)
            a.update(action=action,resource=resource,opinion=opinion,cooperation=propensity)
            a['memory']=(old[i]['memory']+[{'round':t,'action':action,'resource_change':resource-old[i]['resource'],'peer_cooperation':peer_coop}])[-5:]
            if capture and action!=old[i]['action']:
                events.append({'round':t,'type':'action','agent':i,'detail':f"{a['label']}: {old[i]['action']} → {action}",'score':score,'peer_cooperation':peer_coop,'scarcity':scarcity,'evidence':'observed transition'})
            if capture and abs(resource-old[i]['resource'])>.01:
                events.append({'round':t,'type':'resource','agent':i,'detail':f"{a['label']}: {old[i]['resource']:.2f} → {resource:.2f}",'before':old[i]['resource'],'after':resource,'evidence':'executed game payoff'})
            if not old[i]['informed']:
                for j,e in neighbors:
                    if old[j]['informed'] and random_value(seed,'transmission',t,j,i)<cfg['transmission']*e['weight']:
                        a['informed']=True; adopted.append(i)
                        if capture: events.append({'round':t,'type':'transmission','agent':j,'target':i,'detail':f'A{j+1:02d} → A{i+1:02d}','evidence':'recorded information transmission'})
                        break
        for e in world['edges']:
            before=e['weight']; i,j=e['source'],e['target']; e['weight']=clip(before+(.015 if new[i]['action']==new[j]['action'] else -.04),.01,1)
            if capture and before>=.2>e['weight']:
                events.append({'round':t,'type':'relationship','agent':i,'target':j,'detail':f'A{i+1:02d} ↔ A{j+1:02d}: trust crossed below 0.2','evidence':'observed threshold crossing'})
        if capture and len(adopted)>=max(3,n//10): events.append({'round':t,'type':'group','agent':None,'detail':f'{len(adopted)} new information adoptions','evidence':'observed count'})
        record(t)
    return {'seed':seed,'intervention':intervention.model_dump() if intervention else None,'cost':intervention_cost(intervention),
      'initial':original if capture else None,'snapshots':snapshots,'series':series,'final':series[-1],
      'events':events if capture else [],'change_points':change_points(series)}

def run_experiment(intervention=None,seeds=None):
    seeds=seeds or [42,43,44,45,46]
    baseline=[simulate(s) for s in seeds]
    variant=[simulate(s,intervention=intervention) for s in seeds]
    deltas=[round(v['final']['cooperation']-b['final']['cooperation'],4) for b,v in zip(baseline,variant)]
    return {'baseline':baseline,'variant':variant,'seeds':seeds,'delta':deltas,
            'mean_delta':round(sum(deltas)/len(deltas),4),'stability':round(sum(abs(d)>=.05 for d in deltas)/len(deltas),3)}

def search_interventions(max_experiments=12,seeds=None):
    seeds=seeds or [101,102,103]; candidates=[]
    for i in range(1,min(50,max_experiments*2)+1):
        intervention={'kind':'resource','agent':i-1,'magnitude':-5-(i%4)*3}
        exp=run_experiment(intervention,seeds); effect=abs(exp['mean_delta'])
        candidates.append({'agent':f'A{i:02d}','resource_delta':intervention['magnitude'],
          'cost':round(intervention_cost(Intervention(**intervention)),3),'effect':effect,
          'mean_delta':exp['mean_delta'],'stability':exp['stability']})
    return sorted(candidates,key=lambda x:(-x['effect'],x['cost']))[:max_experiments]
