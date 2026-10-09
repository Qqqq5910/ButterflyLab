"""Product adapters only: the existing social engine and metrics are unchanged."""
import copy
from pydantic import Field, model_validator
from .models import StrictModel, Intervention
from .social_config import SocialConfig, preset
from .research import RunRequest, paired_result
from .simulation import initial_world, simulate

class ExploreRequest(RunRequest):
    world: SocialConfig = Field(default_factory=SocialConfig)
    variant_world: SocialConfig | None = None
    centrality: bool = False
    @model_validator(mode='after')
    def one_change(self):
        if self.world.decision_mode != 'rule': raise ValueError('Explore uses free rule mode.')
        if self.centrality and (self.variant_world or not self.intervention or self.intervention.kind!='information' or self.intervention.magnitude!=1):
            raise ValueError('Initial-degree selection requires only a local information injection.')
        if self.variant_world:
            if self.intervention: raise ValueError('Choose one parameter or one local intervention.')
            a=self.world.model_dump();b=self.variant_world.model_dump()
            changed=[k for k in a if a[k]!=b[k]]
            if len(changed)!=1 or changed[0] not in ('transmission','incentive','trust_speed'):
                raise ValueError('Explore permits exactly one declared global rule change.')
        return self

def scenario_catalog():
    world=SocialConfig(**(preset('cascade')|{'transmission':.1}))
    common={'world':world.model_dump(),'seeds':list(range(42,47))}
    return [
      dict(id='information',title='The Information Ripple',question='What if information transmission probability doubles?',question_zh='如果信息传播速度提高一倍，会怎样？',metric='coverage',change='Global transmission probability: 0.1 → 0.2',**common,variant_world=world.model_copy(update={'transmission':.2}).model_dump(),intervention=None),
      dict(id='influential',title='The Influential Node',question='What if the most connected uninformed agent receives the information?',question_zh='如果连接最多的未获知节点提前收到信息？',metric='coverage',change='Local information injection at round 0; node selected by initial degree, ties by smallest ID',**common,variant_world=None,intervention={'kind':'information','agent':1,'magnitude':1}),
      dict(id='cooperation',title='The Cooperation Dilemma',question='What if cooperation incentive rises from 0.3 to 0.6?',question_zh='如果合作激励从 0.3 提高到 0.6？',metric='cooperation',change='Global cooperation incentive: 0.3 → 0.6',**common,variant_world=world.model_copy(update={'incentive':.6}).model_dump(),intervention=None),
    ]

def scenario_request(scenario):
    return ExploreRequest(experiment_name=scenario['title'],centrality=scenario['id']=='influential',**{k:scenario[k] for k in ('world','variant_world','intervention','seeds')})

def run_explore(req, centrality=False, cancel=None, progress=None):
    aa=[];bb=[];targets={}
    for index,seed in enumerate(req.seeds):
        if cancel and cancel(): raise InterruptedError('Explore cancelled')
        initial=initial_world(seed,req.world)
        variant=copy.deepcopy(initial)
        action=req.intervention
        if centrality or req.centrality:
            degree={a['id']:0 for a in initial['agents'] if not a['informed']}
            for e in initial['edges']:
                for node in (e['source'],e['target']):
                    if node in degree: degree[node]+=1
            target=min(degree,key=lambda node:(-degree[node],node))
            action=Intervention(kind='information',agent=target,magnitude=1)
            targets[str(seed)]={'agent':target,'degree':degree[target],'rule':'maximum initial degree among uninformed nodes; smallest ID breaks ties'}
        if req.variant_world: variant['config']=req.variant_world.model_dump()
        aa.append(simulate(initial=initial,cancel=cancel))
        bb.append(simulate(initial=variant,intervention=action,cancel=cancel))
        if progress: progress(index+1,len(req.seeds))
    result=paired_result(req,aa,bb)
    result['selected_nodes']=targets
    return result
