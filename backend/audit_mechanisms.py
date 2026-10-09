"""Run every predeclared legacy sensitivity cell; no cherry-picking."""
import json
from pathlib import Path
from .models import WorldConfig, Intervention
from .simulation import simulate
from .metrics import summarize

def run():
    cells=[]
    for distribution in ['equal','uniform','unequal']:
        for kind,magnitude in [('resource',-1),('resource',-10),('resource',-50),('opinion',-.1),('transmission',-.18)]:
            effects={key:[] for key in ['cooperation','inequality','disagreement','largest_component','cascade']}
            changed=0
            for seed in range(42,72):
                cfg=WorldConfig(resource_distribution=distribution)
                a=simulate(seed,cfg,capture=False)
                b=simulate(seed,cfg,Intervention(kind=kind,magnitude=magnitude),capture=False)
                changed+=any(x['cooperation']!=y['cooperation'] for x,y in zip(a['series'],b['series']))
                for key in effects: effects[key].append(b['final'][key]-a['final'][key])
            cells.append({'distribution':distribution,'kind':kind,'magnitude':magnitude,
                          'cooperation_trajectory_changed_seeds':changed,
                          'summary':{key:summarize(values) for key,values in effects.items()}})
    return {'engine_version':'0.2.0','seeds':list(range(42,72)),'rounds':50,'cells':cells}

if __name__=='__main__':
    result=run();path=Path('output/research/legacy-sensitivity.json')
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps([{k:c[k] for k in ['distribution','kind','magnitude','cooperation_trajectory_changed_seeds']}|
                     {'means':{k:v['mean'] for k,v in c['summary'].items()}} for c in result['cells']],indent=2))
