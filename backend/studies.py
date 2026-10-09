"""Full-factorial sensitivity and explicitly matched mechanism ablations."""
from itertools import product
from typing import Literal
from pydantic import Field,model_validator
from .research import RunRequest,comparison
from .social_config import SocialConfig
from .simulation import simulate,initial_world
from .metrics import summarize

class StudyRequest(RunRequest):
    world: SocialConfig = Field(default_factory=SocialConfig)
    kind: Literal['sensitivity','ablation'] = 'ablation'
    parameter: Literal['trust_speed','incentive','transmission','exchange','opinion_speed','resource_scale'] = 'trust_speed'
    values: list[float] = Field(default_factory=lambda:[0,.03,.1],min_length=1,max_length=8)
    second_parameter: Literal['trust_speed','incentive','transmission','exchange','opinion_speed','resource_scale'] = 'incentive'
    second_values: list[float] = Field(default_factory=lambda:[0,.3,.6],min_length=1,max_length=8)
    mechanism: Literal['trust_enabled','cooperation_enabled','diffusion_enabled','relationships_enabled'] = 'trust_enabled'
    @model_validator(mode='after')
    def validate_cells(self):
        if self.world.decision_mode=='external': raise ValueError('Research studies require rule or mock mode; external calls use explicit provider demo.')
        if self.intervention is not None: raise ValueError('Studies compare parameter/ablation changes; run interventions separately.')
        if self.kind=='sensitivity' and self.parameter==self.second_parameter: raise ValueError('Sensitivity axes must differ')
        if len(self.values)*len(self.second_values)*len(self.seeds)>1200: raise ValueError('Study simulation budget exceeds 1200')
        for a,b in product(self.values,self.second_values):
            SocialConfig(**(self.world.model_dump()|{self.parameter:a,self.second_parameter:b}))
        return self

def study(req,progress=None,cancel=None,on_partial=None):
    cells=[]
    combinations=[(True,False)] if req.kind=='ablation' else list(product(req.values,req.second_values))
    total=len(combinations)*len(req.seeds);done=0
    for x,y in combinations:
        if req.kind=='ablation':
            a_cfg=SocialConfig(**(req.world.model_dump()|{req.mechanism:True}))
            b_cfg=SocialConfig(**(req.world.model_dump()|{req.mechanism:False}))
        else:
            a_cfg=req.world
            b_cfg=SocialConfig(**(req.world.model_dump()|{req.parameter:x,req.second_parameter:y}))
        paired=[]
        for seed in req.seeds:
            if cancel and cancel():raise InterruptedError('Study cancelled at seed boundary')
            initial=initial_world(seed,a_cfg)
            baseline=simulate(initial=initial,capture=False,cancel=cancel)
            # Same exact initial agents/edges; altered config only (resource_scale regenerates resources explicitly).
            if req.kind=='sensitivity' and 'resource_scale' in (req.parameter,req.second_parameter):
                altered=initial_world(seed,b_cfg)
            else:
                import copy
                altered=copy.deepcopy(initial);altered['config']=b_cfg.model_dump()
            variant=simulate(initial=altered,capture=False,cancel=cancel)
            keys=('cooperation','inequality','disagreement','largest_component','coverage','mean_trust','resource_mean')
            paired.append(dict(seed=seed,baseline=baseline['final'],intervention=variant['final'],
                               delta={k:variant['final'][k]-baseline['final'][k] for k in keys}))
            if on_partial:
                partial=dict(x=x,y=y,baseline_config=a_cfg.model_dump(),variant_config=b_cfg.model_dump(),paired=list(paired),
                             summary={k:summarize([p['delta'][k] for p in paired]) for k in keys})
                on_partial(dict(kind=req.kind,configuration=req.model_dump(),cells=cells+[partial],seeds=req.seeds,incomplete=True,
                                note='Incomplete study; only completed paired seeds retained. No significance claim.'))
            done+=1
            if progress: progress(done,total)
        cells.append(dict(x=x,y=y,baseline_config=a_cfg.model_dump(),variant_config=b_cfg.model_dump(),paired=paired,
                          summary={k:summarize([p['delta'][k] for p in paired]) for k in keys}))
    return dict(kind=req.kind,configuration=req.model_dump(),cells=cells,seeds=req.seeds,
                note='All requested cells retained. Paired descriptive effects; no automatic significance claim.')
