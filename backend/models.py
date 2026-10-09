"""Validated public experiment contract (published in /openapi.json)."""
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict, model_validator

Metric = Literal['cooperation','polarization','inequality','modularity','diversity','cascade']
class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
class WorldConfig(StrictModel):
    population: int = Field(50, ge=10, le=100)
    rounds: int = Field(50, ge=5, le=100)
    network: Literal['small_world','random','communities'] = 'small_world'
    resource_distribution: Literal['equal','uniform','unequal'] = 'uniform'
    opinion_distribution: Literal['uniform','polarized','consensus'] = 'uniform'
    heterogeneity: float = Field(.6, ge=0, le=1)
    transmission: float = Field(.18, ge=0, le=1)
    cooperation_threshold: float = Field(.5, ge=0, le=1)
class Intervention(StrictModel):
    kind: Literal['resource','opinion','trust','threshold','transmission','information'] = 'resource'
    agent: int = Field(0, ge=0, le=99)
    target: int = Field(1, ge=0, le=99)
    magnitude: float = Field(-10, ge=-50, le=50)
    @model_validator(mode='after')
    def check(self):
        if self.kind != 'resource' and abs(self.magnitude)>1: raise ValueError('Normalized changes must be within [-1,1].')
        if self.kind=='trust' and self.agent==self.target: raise ValueError('Trust requires different agents.')
        return self
class SearchConfig(StrictModel):
    method: Literal['random','grid','constrained'] = 'random'
    candidates: int = Field(8, ge=1, le=24)
    max_amplitude: float = Field(20, gt=0, le=50)
    max_cost: float = Field(3, gt=0, le=10)
    threshold: float = Field(.02, gt=0, le=1)
    metric: Metric = 'cooperation'
    direction: Literal['decrease','increase'] = 'decrease'
    search_seed: int = Field(314, ge=0, le=2147483647)
class ExperimentRequest(StrictModel):
    world: WorldConfig = Field(default_factory=WorldConfig)
    seeds: list[int] = Field(default_factory=lambda:[42,43,44,45,46], min_length=1, max_length=10)
    evaluation_seeds: list[int] = Field(default_factory=lambda:[142,143,144,145,146], min_length=2, max_length=10)
    interventions: list[Intervention] = Field(default_factory=lambda:[Intervention(),Intervention(kind='opinion',magnitude=-.15)], max_length=2)
    mode: Literal['baseline','comparison','search'] = 'comparison'
    search: SearchConfig = Field(default_factory=SearchConfig)
    max_simulations: int = Field(180, ge=1, le=300)
    @model_validator(mode='after')
    def check(self):
        for values in [self.seeds,self.evaluation_seeds]:
            if len(set(values))!=len(values) or any(s<0 or s>2147483647 for s in values): raise ValueError('Seeds must be unique, in [0,2147483647].')
        if set(self.seeds)&set(self.evaluation_seeds): raise ValueError('Discovery and evaluation seeds must be disjoint.')
        for i in self.interventions:
            if max(i.agent,i.target)>=self.world.population: raise ValueError('Agent outside world population.')
        total=len(self.seeds)*(1+(0 if self.mode=='baseline' else len(self.interventions)))
        if self.mode=='search': total=(self.search.candidates+1)*len(self.seeds)+2*len(self.evaluation_seeds)
        if total>self.max_simulations: raise ValueError(f'Requires up to {total} simulations; budget {self.max_simulations}.')
        return self
