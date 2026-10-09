"""Synchronous social dynamics: decisions -> transfers -> diffusion -> trust -> pruning."""
import copy
from collections import defaultdict
import networkx as nx
from .social_config import SocialConfig, SOCIAL_VERSION
from .models import Intervention
from .metrics import calculate, change_points
from .decisions import DecisionProvider, Decision

def initial_social(seed,config):
    from .simulation import random_value,clip
    c=SocialConfig(**config) if isinstance(config,dict) else config
    n=c.population
    if c.network=='small_world': g=nx.watts_strogatz_graph(n,c.neighbor_count,c.rewiring,seed=seed)
    elif c.network=='random': g=nx.gnp_random_graph(n,c.edge_probability,seed=seed)
    else: g=nx.barabasi_albert_graph(n,c.attachment,seed=seed)
    # Disconnected graphs and isolates remain real experimental conditions.
    positions=nx.spring_layout(g,seed=17,iterations=80)
    agents=[]
    for i in range(n):
        u=random_value(seed,'resource',i);v=random_value(seed,'opinion',i)
        resource=c.resource_scale*(1 if c.resource_distribution=='equal' else .5+u if c.resource_distribution=='uniform' else .2+2.5*u**3)
        opinion=v if c.opinion_distribution=='uniform' else (.1 if i%2 else .8)+.1*v if c.opinion_distribution=='polarized' else .45+.1*v
        propensity=clip(c.cooperation_mean+(0 if c.cooperation_distribution=='equal' else
                        (.3 if i%2 else -.3) if c.cooperation_distribution=='bimodal' else c.heterogeneity*(random_value(seed,'propensity',i)-.5)))
        agents.append(dict(id=i,label=f'A{i+1:02d}',role=['builder','mediator','trader','organizer','scout'][i%5],
                           initial_resource=resource,resource=resource,opinion=opinion,cooperation=propensity,
                           action='cooperate' if propensity>=c.cooperation_threshold else 'compete',
                           informed=i==c.information_origin,history=.5,susceptibility=.5+.5*random_value(seed,'susceptibility',i),
                           memory=[],x=float(positions[i][0]),y=float(positions[i][1])))
    edges=[dict(source=min(i,j),target=max(i,j),weight=c.initial_trust,strength=.5+.5*random_value(seed,'strength',min(i,j),max(i,j))) for i,j in sorted(g.edges)]
    return dict(seed=seed,config=c.model_dump(),agents=agents,edges=edges,groups=[list(range(n))],treasury=c.treasury)

def simulate_social(seed=42,config=None,intervention=None,initial=None,capture=True,cancel=None,provider=None,tape=None,selected_agents=None,on_round=None):
    from .simulation import random_value,clip,apply_intervention,intervention_cost
    c=SocialConfig(**config) if isinstance(config,dict) else config or SocialConfig()
    original=copy.deepcopy(initial or initial_social(seed,c));w=copy.deepcopy(original)
    c=SocialConfig(**w['config']);seed=w['seed'];n=len(w['agents'])
    intervention=Intervention(**intervention) if isinstance(intervention,dict) else intervention
    if intervention and intervention.kind=='resource':
        a=w['agents'][intervention.agent];before=a['resource'];a['resource']=max(0,before+intervention.magnitude)
        events=[dict(round=0,type='intervention',agent=a['id'],before=before,after=a['resource'],detail='Explicit external resource injection/removal')]
    elif intervention and intervention.kind=='information':
        a=w['agents'][intervention.agent];before=a['informed'];a['informed']=intervention.magnitude>0
        events=[dict(round=0,type='intervention',agent=a['id'],before=before,after=a['informed'],detail='Information state changed')]
    else:
        events=apply_intervention(w,intervention);c=SocialConfig(**w['config'])
    snapshots=[];series=[];decisions=[];paths=[]
    provider=provider or (DecisionProvider('mock') if c.decision_mode=='mock' else None)
    tape_index={(d['round'],d['agent']):d for d in tape} if tape is not None else None
    def record(t):
        m={'round':t,**calculate(w['agents'],w['edges'],w['groups']),
           'coverage':sum(a['informed'] for a in w['agents'])/n,
           'mean_trust':sum(e['weight'] for e in w['edges'])/len(w['edges']) if w['edges'] else 0,
           'resource_mean':sum(a['resource'] for a in w['agents'])/n,'treasury':w['treasury']}
        series.append(m)
        if capture: snapshots.append(dict(round=t,agents=copy.deepcopy(w['agents']),edges=copy.deepcopy(w['edges']),metrics=m,treasury=w['treasury']))
    record(0)
    for t in range(1,c.rounds+1):
        if cancel and cancel(): raise InterruptedError('Cancelled at round boundary')
        old=copy.deepcopy(w['agents']);adj=defaultdict(list)
        for e in w['edges']:
            adj[e['source']].append((e['target'],e));adj[e['target']].append((e['source'],e))
        actions=[];propagate=[];targets=[]
        for i,a in enumerate(old):
            neighbors=sorted(adj[i],key=lambda v:v[0]);trust=sum(e['weight'] for _,e in neighbors)/len(neighbors) if neighbors else 0
            scarcity=max(0,1-a['resource']/40)
            score=.35*a['cooperation']+.25*trust+.2*a['history']+.2*c.incentive-.4*scarcity+.1*(random_value(seed,'social-action',t,i)-.5)
            action=dict(cooperate=score>=c.cooperation_threshold,propagate=True,target=None,reason='rule score')
            status='rule'
            if c.decision_mode!='rule' and (selected_agents is None or i in selected_agents):
                if tape_index is not None:
                    row=tape_index.get((t,i))
                    if row is None: raise ValueError('Incomplete decision replay tape')
                    action=Decision(**row['decision']).model_dump();status=row['status']
                    if action['target'] is not None and action['target'] not in [j for j,_ in neighbors]: raise ValueError('Invalid replay target')
                else:
                    proposal,status=provider.decide(dict(agent=i,round=t,score=score,threshold=c.cooperation_threshold,
                         resource=a['resource'],mean_trust=trust,informed=a['informed'],neighbors=[j for j,_ in neighbors],
                         role=a['role'],opinion=a['opinion'],recent_events=a['memory'][-2:])) if provider else (None,'no provider; rule fallback')
                    if proposal: action=proposal
                decisions.append(dict(round=t,agent=i,decision=action,status=status))
            actions.append(action['cooperate'] if c.cooperation_enabled else a['action']=='cooperate')
            propagate.append(action['propagate']);targets.append(action['target'])
            w['agents'][i]['action']='cooperate' if actions[-1] else 'compete'
        # Donations are simultaneous, capped by opening balance; incentives draw only from a finite treasury.
        incoming=[0.]*n;outgoing=[0.]*n
        if c.cooperation_enabled:
            for i in range(n):
                recipients=[j for j,_ in adj[i] if targets[i] is None or targets[i]==j]
                if actions[i] and recipients:
                    amount=min(old[i]['resource'],c.exchange*len(recipients));outgoing[i]=amount
                    for j in recipients: incoming[j]+=amount/len(recipients)
            requested=[c.incentive*x for x in outgoing];total=sum(requested)
            scale=min(1,w['treasury']/total) if total else 0
            rewards=[x*scale for x in requested];w['treasury']=max(0,w['treasury']-sum(rewards))
            for i,a in enumerate(w['agents']):
                a['resource']=old[i]['resource']-outgoing[i]+incoming[i]+rewards[i]
                experience=sum(actions[j] for j,_ in adj[i])/len(adj[i]) if adj[i] else old[i]['history']
                a['history']=.8*old[i]['history']+.2*experience
        transmissions=set()
        if c.diffusion_enabled:
            for i,a in enumerate(w['agents']):
                if not old[i]['informed']:
                    for j,e in sorted(adj[i],key=lambda v:v[0]):
                        probability=c.transmission*e['weight']*e['strength']*a['susceptibility']
                        if old[j]['informed'] and propagate[j] and (targets[j] is None or targets[j]==i) and random_value(seed,'social-transmission',t,j,i)<probability:
                            a['informed']=True;paths.append(dict(round=t,source=j,target=i,probability=probability));transmissions.add(tuple(sorted((i,j))))
                            if capture: events.append(dict(round=t,type='transmission',agent=j,target=i,detail=f'A{j+1:02d} -> A{i+1:02d}'))
                            break
                weights=sum(e['weight']*e['strength'] for _,e in adj[i])
                peer=sum(e['weight']*e['strength']*old[j]['opinion'] for j,e in adj[i])/weights if weights else old[i]['opinion']
                a['opinion']=clip(old[i]['opinion']+c.opinion_speed*(peer-old[i]['opinion']))
        for e in w['edges']:
            i,j=e['source'],e['target'];before=e['weight']
            if c.trust_enabled:
                reward=1 if actions[i] and actions[j] else -1 if actions[i]!=actions[j] else 0
                communication=.25 if (i,j) in transmissions else 0
                e['weight']=clip(before+c.trust_speed*(reward+communication))
            if capture and e['weight']!=before: events.append(dict(round=t,type='trust',agent=i,target=j,before=before,after=e['weight'],detail=f'A{i+1:02d} <-> A{j+1:02d}: {before:.3f} -> {e["weight"]:.3f}'))
        if c.relationships_enabled:
            removed=[e for e in w['edges'] if e['weight']<c.break_threshold]
            w['edges']=[e for e in w['edges'] if e['weight']>=c.break_threshold]
            if capture:
                for e in removed: events.append(dict(round=t,type='relationship',agent=e['source'],target=e['target'],detail='Tie removed below configured trust threshold'))
        for i,a in enumerate(w['agents']):
            a['memory']=(old[i]['memory']+[dict(round=t,action=a['action'],resource_change=a['resource']-old[i]['resource'],history=a['history'])])[-5:]
        record(t)
        if on_round:on_round(t)
    return dict(seed=seed,engine_version=SOCIAL_VERSION,intervention=intervention.model_dump() if intervention else None,
                cost=intervention_cost(intervention),initial=original if capture else None,snapshots=snapshots,series=series,final=series[-1],
                events=events if capture else [],change_points=change_points(series),transmission_paths=paths,
                decisions=decisions,decision_mode=c.decision_mode,
                provider_usage=provider.usage() if provider and tape is None else None)
