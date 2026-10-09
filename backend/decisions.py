"""Structured, bounded decisions. Provider output never mutates world state."""
import json
import time
from typing import Literal
import httpx
from pydantic import Field, StrictBool, StrictInt
from .models import StrictModel

class Decision(StrictModel):
    cooperate: StrictBool
    propagate: StrictBool
    target: StrictInt | None = None
    reason: str = Field(max_length=160)

class ProviderConfig(StrictModel):
    base_url: str = Field('http://127.0.0.1:8080/v1',max_length=500)
    model: str = Field('mock-v1',min_length=1,max_length=120)
    temperature: float = Field(0,ge=0,le=2)
    token_budget: int = Field(20000,ge=1,le=1000000)
    max_calls: int = Field(100,ge=0,le=10000)
    timeout: float = Field(10,ge=.1,le=60)
    retries: int = Field(0,ge=0,le=2)

class DecisionProvider:
    def __init__(self,mode='mock',config=None,key=None):
        self.mode=mode; self.config=config or ProviderConfig(); self.key=key
        self.calls=0; self.tokens=0; self.failures=0
    def decide(self,context):
        cfg=self.config
        text=json.dumps(context,separators=(',',':'))
        # Conservative input allowance plus capped output, reserved before every attempt.
        allowance=len(text.encode('utf-8'))+800
        if self.calls>=cfg.max_calls or self.tokens+allowance>cfg.token_budget:
            return None,'budget exhausted; rule fallback'
        for attempt in range(cfg.retries+1):
            if self.calls>=cfg.max_calls or self.tokens+allowance>cfg.token_budget: break
            self.calls+=1; self.tokens+=allowance
            try:
                if self.mode=='mock':
                    raw={'cooperate':context['score']>=context['threshold'],
                         'propagate':context['informed'],'target':context['neighbors'][0] if context['neighbors'] else None,
                         'reason':'mock-v1: bounded score and first available neighbor'}
                else:
                    if not self.key: return None,'missing credentials; rule fallback'
                    response=httpx.post(cfg.base_url.rstrip('/')+'/chat/completions',
                        headers={'Authorization':'Bearer '+self.key},timeout=cfg.timeout,
                        json={'model':cfg.model,'temperature':cfg.temperature,'max_tokens':200,
                              'response_format':{'type':'json_object'},'messages':[
                                {'role':'system','content':'Return JSON only: cooperate boolean, propagate boolean, target integer neighbor or null, reason string <=160 characters. No other fields.'},
                                {'role':'user','content':text}]})
                    response.raise_for_status()
                    raw=json.loads(response.json()['choices'][0]['message']['content'])
                action=Decision(**raw)
                if action.target is not None and action.target not in context['neighbors']:
                    raise ValueError('Non-neighbor target')
                if self.key: action.reason=action.reason.replace(self.key,'[redacted]')
                return action.model_dump(),'accepted'
            except Exception:
                self.failures+=1
                if attempt<cfg.retries: time.sleep(.1)
        return None,'invalid output or provider failure; rule fallback'

    def usage(self):
        return {'calls':self.calls,'reserved_tokens':self.tokens,'failures':self.failures,
                'accounting':'UTF-8 input bytes + 800 reserved per attempt, output capped at 200 tokens'}
