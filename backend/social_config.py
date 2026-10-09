"""Versioned opt-in configuration; legacy WorldConfig is unchanged."""
from typing import Literal
from pydantic import Field, model_validator
from .models import WorldConfig

SOCIAL_VERSION='social-1.0.0'
class SocialConfig(WorldConfig):
    schema_version: Literal[3] = 3
    engine: Literal['social-1.0.0'] = SOCIAL_VERSION
    network: Literal['small_world','random','scale_free'] = 'small_world'
    initial_seed: int = Field(42,ge=0,le=2147483647)
    neighbor_count: int = Field(4,ge=2,le=98)
    rewiring: float = Field(.15,ge=0,le=1)
    edge_probability: float = Field(.1,ge=0,le=1)
    attachment: int = Field(2,ge=1,le=99)
    resource_scale: float = Field(60,ge=0,le=200)
    cooperation_distribution: Literal['uniform','equal','bimodal'] = 'uniform'
    cooperation_mean: float = Field(.55,ge=0,le=1)
    initial_trust: float = Field(.6,ge=0,le=1)
    trust_enabled: bool = True
    cooperation_enabled: bool = True
    diffusion_enabled: bool = True
    relationships_enabled: bool = True
    trust_speed: float = Field(.03,ge=0,le=.5)
    incentive: float = Field(.3,ge=0,le=1)
    exchange: float = Field(1,ge=0,le=10)
    treasury: float = Field(500,ge=0,le=100000)
    opinion_speed: float = Field(.1,ge=0,le=1)
    break_threshold: float = Field(.1,ge=0,le=1)
    information_origin: int = Field(0,ge=0,le=99)
    decision_mode: Literal['rule','mock','external'] = 'rule'
    @model_validator(mode='after')
    def legal_network(self):
        if self.network=='small_world' and (self.neighbor_count>=self.population or self.neighbor_count%2):
            raise ValueError('Small-world neighbor count must be even and less than population.')
        if self.network=='scale_free' and self.attachment>=self.population:
            raise ValueError('Scale-free attachment must be less than population.')
        if self.information_origin>=self.population:
            raise ValueError('Information origin outside population.')
        return self

def is_social(config):
    return isinstance(config,SocialConfig) or isinstance(config,dict) and config.get('engine')==SOCIAL_VERSION

def engine_for(config):
    return SOCIAL_VERSION if is_social(config) else '0.2.0'

def preset(name):
    if name=='fragile':
        return SocialConfig(engine=SOCIAL_VERSION,resource_distribution='unequal',resource_scale=35,incentive=.25).model_dump()
    if name=='cascade':
        return SocialConfig(engine=SOCIAL_VERSION,network='scale_free',transmission=.25,opinion_speed=.15).model_dump()
    raise ValueError('Unknown scenario')
