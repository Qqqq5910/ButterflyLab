"""Matched comparisons and bounded extension of the original candidate search."""
from .models import StrictModel, WorldConfig, Intervention
from pydantic import Field, model_validator, field_validator
from typing import Literal
from typing import Annotated
from .simulation import initial_world, simulate, intervention_cost, ENGINE_VERSION
from .metrics import summarize, DEFINITIONS
from .social_config import SocialConfig, engine_for, is_social

METRICS=('cooperation','inequality','disagreement','largest_component')
LIMITATION='Synthetic rule simulation only. Small seed samples give descriptive uncertainty, not proof of statistical significance or real-world causality.'

class RunRequest(StrictModel):
    experiment_name: str = Field('Fragile society comparison',min_length=1,max_length=120)
    world: SocialConfig | WorldConfig = Field(default_factory=WorldConfig)
    intervention: Intervention | None = None
    seeds: list[Annotated[int,Field(strict=True)]] = Field(default_factory=lambda:list(range(42,47)),min_length=1,max_length=100)
    @field_validator('world',mode='before')
    @classmethod
    def select_engine(cls,value):
        if isinstance(value,dict):
            return SocialConfig(**value) if 'engine' in value else WorldConfig(**value)
        return value
    @model_validator(mode='after')
    def validate_run(self):
        if len(set(self.seeds))!=len(self.seeds) or any(s<0 or s>2147483647 for s in self.seeds):
            raise ValueError('Seeds must be distinct integers in [0,2147483647].')
        if self.intervention and (self.intervention.agent>=self.world.population or self.intervention.target>=self.world.population):
            raise ValueError('Agent outside world population.')
        if self.intervention and self.intervention.kind=='information' and not is_social(self.world):
            raise ValueError('Information intervention requires social engine.')
        return self

class SearchRequest(RunRequest):
    metric: Literal['cooperation','inequality','disagreement','largest_component','coverage','mean_trust','resource_mean'] = 'cooperation'
    direction: Literal['decrease','increase'] = 'decrease'
    max_experiments: int = Field(8,ge=1,le=24)
    evaluation_seeds: list[Annotated[int,Field(strict=True)]] = Field(default_factory=lambda:list(range(142,147)),min_length=2,max_length=100)
    @model_validator(mode='after')
    def validate_search(self):
        if self.metric not in METRICS and not is_social(self.world):
            raise ValueError('Social metric requires social engine.')
        values=self.evaluation_seeds
        if len(set(values))!=len(values) or any(s<0 or s>2147483647 for s in values) or set(values)&set(self.seeds):
            raise ValueError('Evaluation seeds must be unique, bounded and disjoint from discovery seeds.')
        return self

def comparison(req,progress=None,capture=True,cancel=None,on_pair=None):
    metrics=METRICS+('coverage','mean_trust','resource_mean') if is_social(req.world) else METRICS
    baseline=[]; variant=[]
    for index,seed in enumerate(req.seeds):
        if cancel and cancel():raise InterruptedError('Cancelled before seed')
        initial=initial_world(seed,req.world)
        a=simulate(initial=initial,capture=capture,cancel=cancel)
        b=simulate(initial=initial,intervention=req.intervention,capture=capture,cancel=cancel)
        baseline.append(a);variant.append(b)
        if on_pair:on_pair(seed,a,b)
        if progress: progress(index+1,len(req.seeds))
    return paired_result(req,baseline,variant)

def paired_result(req,baseline,variant):
    metrics=METRICS+('coverage','mean_trust','resource_mean') if is_social(req.world) else METRICS
    paired=[{'seed':s,'baseline':a['final'],'intervention':b['final'],
             'delta':{m:b['final'][m]-a['final'][m] for m in metrics}}
            for s,a,b in zip(req.seeds,baseline,variant)]
    summary={m:{**summarize([p['delta'][m] for p in paired]),
                'baseline_mean':sum(p['baseline'][m] for p in paired)/len(paired),
                'intervention_mean':sum(p['intervention'][m] for p in paired)/len(paired)} for m in metrics}
    return {'schema_version':2,'engine_version':engine_for(req.world),'configuration':req.model_dump(),
            'baseline':baseline,'variant':variant,'seeds':req.seeds,'paired':paired,'summary':summary,
            'metric_definitions':{m:DEFINITIONS[m] for m in metrics},'limitation':LIMITATION,
            'delta':[p['delta']['cooperation'] for p in paired],
            'mean_delta':summary['cooperation']['mean']}

def discover(req,progress=None,cancel=None,on_pair=None,on_candidate=None):
    # Preserve the original bounded agent/resource candidate schedule; reuse matched baselines.
    total=(req.max_experiments+1)*len(req.seeds)+2*len(req.evaluation_seeds)
    baselines={}; results=[]; completed=0
    for seed in req.seeds:
        baselines[seed]=simulate(seed,req.world,capture=False,cancel=cancel)
        completed+=1
        if progress: progress(completed,total)
    for index in range(req.max_experiments):
        i=index+1
        intervention=Intervention(kind='resource',agent=index%req.world.population,magnitude=-5-(i%4)*3)
        deltas=[]
        for seed in req.seeds:
            outcome=simulate(seed,req.world,intervention,capture=False,cancel=cancel)
            deltas.append(outcome['final'][req.metric]-baselines[seed]['final'][req.metric])
            completed+=1
            if progress: progress(completed,total)
        stats=summarize(deltas,direction=req.direction)
        results.append({'agent':f'A{intervention.agent+1:02d}','resource_delta':intervention.magnitude,
                        'intervention':intervention.model_dump(),'cost':intervention_cost(intervention),
                        'mean_delta':stats['mean'],'uncertainty':stats,'stability':stats['frequency']})
        if on_candidate:on_candidate(results[-1])
    sign=-1 if req.direction=='decrease' else 1
    results.sort(key=lambda c:(-sign*c['mean_delta'],c['cost']))
    chosen=results[0]
    validation=comparison(RunRequest(experiment_name=req.experiment_name,world=req.world,
                                    intervention=chosen['intervention'],seeds=req.evaluation_seeds),
                          progress=lambda done,n:progress(completed+2*done,total) if progress else None,cancel=cancel,on_pair=on_pair)
    return {'results':results,'configuration':req.model_dump(),'metric':req.metric,
            'discovery_seeds':req.seeds,'evaluation_seeds':req.evaluation_seeds,
            'validation':validation,'simulations':total,'limitation':LIMITATION,
            'selection_note':'Best discovery candidate evaluated once on disjoint held-out seeds; no significance claim.'}
