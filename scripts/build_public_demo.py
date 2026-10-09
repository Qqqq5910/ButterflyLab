"""Generate checksum-addressed static replay from the real unchanged rule engine."""
import argparse, copy, gzip, hashlib, json, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.explore_mode import scenario_catalog,scenario_request,run_explore
from backend.environment import environment

def encode(value): return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def build(destination):
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=True)
    manifest={'format_version':1,'engine_version':'social-1.0.0','environment':environment(),'scenarios':[],'files':{}}
    def write(name,value,compressed=False):
        raw=encode(value);data=gzip.compress(raw,mtime=0) if compressed else raw
        (destination/name).write_bytes(data)
        meta={'file':name,'sha256':hashlib.sha256(data).hexdigest(),'raw_sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(data),'raw_bytes':len(raw)}
        manifest['files'][name]=meta
        return meta
    for scenario in scenario_catalog():
        result=run_explore(scenario_request(scenario),centrality=scenario['id']=='influential')
        summary=copy.deepcopy(result);runs={}
        for index,seed in enumerate(result['seeds']):
            pair={branch:result[branch][index] for branch in ('baseline','variant')}
            runs[str(seed)]=write(f'{scenario["id"]}-{seed}.json.gz',pair,True)
        for branch in ('baseline','variant'):
            summary[branch]=[{k:v for k,v in run.items() if k not in ('initial','snapshots','events','transmission_paths','decisions')} for run in result[branch]]
        summary.update(scenario=scenario,trajectory_files=runs,format_version=1)
        manifest['scenarios'].append(scenario|{'summary':write(scenario['id']+'-summary.json',summary),'preview':write(scenario['id']+'-preview.json',result['baseline'][0]['initial'])})
        print(scenario['id'],result['summary'][scenario['metric']]['mean'],sum(m['bytes'] for m in runs.values()))
    (destination/'manifest.json').write_bytes(encode(manifest))
    return manifest

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',default='frontend/public/demo');args=parser.parse_args()
    build(args.output)
