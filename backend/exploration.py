"""Versioned exploratory response scans; finite-size candidates are not phase transitions."""
import copy, json, sqlite3, uuid
from contextlib import contextmanager
from typing import Literal
import networkx as nx
from pydantic import Field, model_validator
from .research import RunRequest, paired_result
from .social_config import SocialConfig
from .models import Intervention
from .simulation import initial_world,simulate,intervention_cost
from .metrics import summarize
from .storage import now
from .environment import environment

ALGORITHM_VERSION='exploration-1.1.0'
PARAMETERS=('trust_speed','incentive','transmission','opinion_speed','degree','magnitude','centrality')
class ExplorationRequest(RunRequest):
    world:SocialConfig=Field(default_factory=SocialConfig)
    mode:Literal['sensitivity','criticality','robustness']='sensitivity'
    parameter:Literal['trust_speed','incentive','transmission','opinion_speed','degree','magnitude','centrality']='transmission'
    values:list[float]=Field(default_factory=lambda:[0,.1,.3,.6,1],min_length=2,max_length=12)
    second_parameter:Literal['trust_speed','incentive','transmission','opinion_speed','degree','magnitude','centrality']|None=None
    second_values:list[float]=Field(default_factory=lambda:[-1,-10,-30],min_length=1,max_length=12)
    metric:Literal['cooperation','inequality','disagreement','largest_component','coverage','mean_trust','resource_mean']='coverage'
    validation_seeds:list[int]=Field(default_factory=lambda:list(range(10042,10072)),min_length=2,max_length=100)
    scales:list[int]=Field(default_factory=lambda:[30,50,100],min_length=1,max_length=4)
    topologies:list[Literal['small_world','random','scale_free']]=Field(default_factory=lambda:['small_world','random','scale_free'],min_length=1,max_length=3)
    max_simulations:int=Field(3000,ge=4,le=10000)
    max_seconds:int=Field(600,ge=1,le=3600)
    refinement_points:int=Field(2,ge=0,le=4)
    response_threshold:float=Field(.1,gt=0,le=100)
    @model_validator(mode='after')
    def validate_exploration(self):
        if self.world.decision_mode!='rule':raise ValueError('Exploration uses rule mode only')
        if self.second_parameter==self.parameter:raise ValueError('Grid axes must differ')
        if self.mode=='criticality' and self.second_parameter:raise ValueError('Criticality starts with one parameter')
        if len(set(self.values))!=len(self.values) or len(set(self.second_values))!=len(self.second_values):raise ValueError('Scan values must be unique')
        if len(set(self.validation_seeds))!=len(self.validation_seeds) or set(self.seeds)&set(self.validation_seeds) or any(type(s)!=int or not 0<=s<=2147483647 for s in self.validation_seeds):raise ValueError('Validation seeds must be unique bounded integers, disjoint from discovery')
        if any(type(n)!=int or not 10<=n<=100 for n in self.scales):raise ValueError('Scale must be integer in [10,100]')
        for x in self.values:
            for y in self.second_values if self.second_parameter else [None]:configure(self.world,self.parameter,x,self.second_parameter,y,self.intervention)
        if self.mode=='criticality':
            for n in self.scales:
                for topology in self.topologies:
                    for x in self.values:configure(match_density(self.world,n,topology),self.parameter,x,intervention=self.intervention)
        needed=2*len(self.values)*(len(self.second_values) if self.second_parameter else 1)*len(self.seeds)
        if self.mode=='criticality':needed+=2*self.refinement_points*len(self.seeds)+4*len(self.validation_seeds)*len(self.scales)*len(self.topologies)
        if self.mode=='robustness':needed+=2*len(self.values)*len(self.validation_seeds)
        if needed>self.max_simulations:raise ValueError(f'Requires at most {needed} simulations, budget {self.max_simulations}')
        self.values=sorted(self.values)
        return self

def configure(world,parameter,value,second=None,y=None,intervention=None):
    cfg=world.model_dump();action=intervention.model_dump() if intervention else None;rank=None
    for p,v in [(parameter,value),(second,y)]:
        if p is None:continue
        if p=='magnitude':action=(action or Intervention().model_dump())|{'magnitude':v}
        elif p=='centrality':
            if not 0<=v<=1:raise ValueError('Centrality rank percentile in [0,1]')
            rank=v;action=action or Intervention().model_dump()
        elif p=='degree':
            n=cfg['population']
            if not 0<=v<n:raise ValueError('Degree must be in [0,N-1]')
            if cfg['network']=='random':cfg['edge_probability']=v/(n-1)
            elif cfg['network']=='small_world':
                if v!=int(v):raise ValueError('WS degree must be an even integer')
                cfg['neighbor_count']=int(v)
            else:
                if v%2 or v<2:raise ValueError('BA requested degree must be even, >=2; actual finite-size mean is reported')
                cfg['attachment']=int(v/2)
        else:cfg[p]=v
    return SocialConfig(**cfg),Intervention(**action) if action else None,rank

def match_density(world,n,network):
    cfg=world.model_dump();k=cfg['neighbor_count'] if world.network=='small_world' else 2*cfg['attachment'] if world.network=='scale_free' else cfg['edge_probability']*(world.population-1)
    even=max(2,min(n-2,2*round(k/2)));even-=even%2
    cfg.update(population=n,network=network,neighbor_count=even,attachment=max(1,min(n-1,round(k/2))),edge_probability=min(1,k/(n-1)),information_origin=min(cfg['information_origin'],n-1))
    return SocialConfig(**cfg)

def replay_cell(configuration):
    config=dict(configuration);context=config.pop('scan_context');config.pop('environment',None)
    req=RunRequest(**config);variant=SocialConfig(**context['variant_world']);aa=[];bb=[]
    for seed in req.seeds:
        action=req.intervention;b0=initial_world(seed,variant)
        if context['centrality_rank'] is not None:
            graph=nx.Graph();graph.add_nodes_from(a['id'] for a in b0['agents']);graph.add_edges_from((e['source'],e['target']) for e in b0['edges'])
            order=sorted(graph.nodes,key=lambda n:(graph.degree(n),n))
            action=Intervention(**(action.model_dump()|{'agent':order[round(context['centrality_rank']*(len(order)-1))]}))
        aa.append(simulate(initial=initial_world(seed,req.world)));bb.append(simulate(initial=b0,intervention=action))
    return paired_result(req,aa,bb)|{'scan_context':context}

def detect_regions(cells,metric,threshold=.1):
    cells=sorted(cells,key=lambda c:c['x']);regions=[]
    for left,right in zip(cells,cells[1:]):
        a={p['seed']:p['intervention'][metric] for p in left['paired']};b={p['seed']:p['intervention'][metric] for p in right['paired']}
        effects=[b[s]-a[s] for s in a if s in b];stats=summarize(effects)
        slope=stats['mean']/(right['x']-left['x'])
        excludes_zero=stats['ci95'] is not None and stats['ci95'][0]*stats['ci95'][1]>0
        candidate=abs(stats['mean'])>=threshold
        regions.append({'low':left['x'],'high':right['x'],'change':stats,'slope':slope,
                        'candidate':candidate,'classification':'candidate rapid finite-size response' if candidate and excludes_zero else 'finite-size seed variability / unresolved' if candidate else 'below response threshold'})
    slopes=[abs(r['slope']) for r in regions]
    for r in regions:
        others=[s for s in slopes if s!=abs(r['slope'])]
        reference=sum(others)/len(others) if others else abs(r['slope'])
        r['relative_slope']=abs(r['slope'])/reference if reference else None
        r['nonlinear_hint']=len(regions)>1 and abs(r['slope'])>2*reference
        r['note']='Adjacent paired contrast; threshold and slope heterogeneity are exploratory. No discontinuity or phase transition established.'
    return sorted(regions,key=lambda r:(r['candidate'],abs(r['slope'])),reverse=True)

class LabStore:
    def __init__(self,path):
        self.path=path
        with self.connect() as con:
            version=con.execute('PRAGMA user_version').fetchone()[0]
            if version>1:raise ValueError('Lab schema newer than supported')
            con.execute('CREATE TABLE IF NOT EXISTS scans(id TEXT PRIMARY KEY,created_at TEXT,configuration TEXT,result TEXT,state TEXT,error TEXT)');con.execute('PRAGMA user_version=1')
    def recover(self):
        with self.connect() as con:con.execute("UPDATE scans SET state='FAILED',error='Server interrupted scan' WHERE state IN ('QUEUED','RUNNING','CANCEL_REQUESTED')")
    @contextmanager
    def connect(self):
        con=sqlite3.connect(self.path,timeout=30)
        try:
            with con:yield con
        finally:con.close()
    def create(self,req):
        eid=str(uuid.uuid4())
        with self.connect() as con:con.execute('INSERT INTO scans VALUES (?,?,?,?,?,?)',(eid,now(),json.dumps(req.model_dump()|{'environment':environment(),'algorithm_version':ALGORITHM_VERSION}),json.dumps({'cells':[],'validation':[],'regions':[]}), 'QUEUED',None))
        return eid
    def get(self,eid):
        with self.connect() as con:
            con.row_factory=sqlite3.Row;row=con.execute('SELECT * FROM scans WHERE id=?',(eid,)).fetchone()
        if not row:raise KeyError('Scan not found')
        r=dict(row);r['configuration']=json.loads(r['configuration']);r['result']=json.loads(r['result']);return r
    def list(self):
        with self.connect() as con:
            con.row_factory=sqlite3.Row
            return [dict(r) for r in con.execute('SELECT id,created_at,state,error FROM scans ORDER BY created_at DESC')]
    def save(self,eid,result,state,error=None):
        with self.connect() as con:con.execute('UPDATE scans SET result=?,state=?,error=? WHERE id=?',(json.dumps(result,allow_nan=False),state,error,eid))

def explore(req,eid,lab,store,cancel,progress):
    result={'algorithm_version':ALGORITHM_VERSION,'cells':[],'validation':[],'regions':[],
            'note':'Exploratory finite-agent response; not a statistical-physics phase transition. Discovery selection is biased; independent validation is reported separately.'}
    done=0
    def cell(x,y=None,seeds=None,world=None,phase='discovery'):
        nonlocal done
        seeds=seeds or req.seeds;world=world or req.world
        cfg,action,rank=configure(world,req.parameter,float(x),req.second_parameter,y,req.intervention)
        q=RunRequest(world=world,seeds=seeds,intervention=action,experiment_name=f'{req.experiment_name} / {phase} {x},{y}')
        context={'variant_world':cfg.model_dump(),'centrality_rank':rank}
        child=store.create(q.model_dump()|{'environment':environment(),'scan_context':context},'scan_cell');aa=[];bb=[];targets=[];densities=[]
        try:
            for seed in seeds:
                if cancel():raise InterruptedError('Cancelled at seed boundary')
                a0=initial_world(seed,world);b0=initial_world(seed,cfg)
                local_action=action
                if rank is not None:
                    graph=nx.Graph();graph.add_nodes_from(a['id'] for a in b0['agents']);graph.add_edges_from((e['source'],e['target']) for e in b0['edges'])
                    order=sorted(graph.nodes,key=lambda n:(graph.degree(n),n));agent=order[round(rank*(len(order)-1))]
                    local_action=Intervention(**(action.model_dump()|{'agent':agent}));targets.append({'seed':seed,'agent':agent,'degree_centrality':graph.degree(agent)/(len(order)-1)})
                a=simulate(initial=a0,cancel=cancel);b=simulate(initial=b0,intervention=local_action,cancel=cancel)
                aa.append(a);bb.append(b);done+=2;progress(done)
                densities.append({'seed':seed,'A_mean_degree':2*len(a0['edges'])/world.population,'B_mean_degree':2*len(b0['edges'])/cfg.population})
        except InterruptedError:
            if aa:
                partial=paired_result(q.model_copy(update={'seeds':seeds[:len(aa)]}),aa,bb);partial['incomplete']=True;store.finish(child,partial)
            with store.connect() as con:con.execute("UPDATE experiments SET experiment_status='cancelled' WHERE experiment_id=?",(child,))
            result['partial_cell']={'experiment_id':child,'completed_seeds':seeds[:len(aa)],'requested_seeds':seeds,'x':x,'y':y}
            raise
        except Exception as error:
            store.fail(child,error);raise
        payload=paired_result(q,aa,bb);payload['scan_context']=context;store.finish(child,payload)
        paired=payload['paired']
        for m,stats in payload['summary'].items():stats['direction_consistency']=max(sum(p['delta'][m]>0 for p in paired),sum(p['delta'][m]<0 for p in paired))/len(paired)
        return {'x':x,'y':y,'phase':phase,'experiment_id':child,'world':cfg.model_dump(),'baseline_world':world.model_dump(),'intervention':action.model_dump() if action else None,
                'targets':targets,'density':densities,'seeds':seeds,'paired':paired,'summary':payload['summary'],'cost':intervention_cost(action),
                'response':summarize([p['intervention'][req.metric] for p in paired]),'series':[{'seed':a['seed'],'baseline':a['series'],'intervention':b['series']} for a,b in zip(aa,bb)]}
    try:
        lab.save(eid,result,'RUNNING')
        for x in req.values:
            for y in req.second_values if req.second_parameter else [None]:
                result['cells'].append(cell(x,y));lab.save(eid,result,'RUNNING')
        if req.mode=='criticality':
            result['regions']=detect_regions(result['cells'],req.metric,req.response_threshold)
            region=result['regions'][0]
            for i in range(req.refinement_points):
                x=region['low']+(i+1)*(region['high']-region['low'])/(req.refinement_points+1)
                try:configure(req.world,req.parameter,float(x),intervention=req.intervention)
                except ValueError:continue
                result['cells'].append(cell(x,phase='refinement'));lab.save(eid,result,'RUNNING')
            result['regions_after_refinement']=detect_regions(result['cells'],req.metric,req.response_threshold)
            for n in req.scales:
                for topology in req.topologies:
                    cfg=match_density(req.world,n,topology)
                    pair=[cell(x,seeds=req.validation_seeds,world=cfg,phase='independent') for x in [region['low'],region['high']]]
                    contrast=detect_regions(pair,req.metric,req.response_threshold)[0]
                    result['validation'].append({'population':n,'network':topology,'cells':pair,'contrast':contrast})
                    lab.save(eid,result,'RUNNING')
            result['candidate_detected']=region['candidate']
            result['stable_in_validation']=region['candidate'] and all(v['contrast']['candidate'] and v['contrast']['change']['mean']*region['change']['mean']>0 and v['contrast']['change']['ci95'] and v['contrast']['change']['ci95'][0]*v['contrast']['change']['ci95'][1]>0 for v in result['validation'])
        elif req.mode=='robustness':
            for x in req.values:
                result['validation'].append(cell(x,seeds=req.validation_seeds,phase='independent'));lab.save(eid,result,'RUNNING')
        lab.save(eid,result,'COMPLETED')
    except InterruptedError:lab.save(eid,result,'CANCELLED');raise
    except Exception as error:lab.save(eid,result,'FAILED',str(error));raise
    return result
