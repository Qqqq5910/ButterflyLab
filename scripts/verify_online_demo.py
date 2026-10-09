"""Compare deployed public data against freshly generated local engine results."""
import gzip,hashlib,json
from pathlib import Path
from urllib.request import urlopen
BASE='https://qqqq5910.github.io/ButterflyLab/demo/'
manifest=json.load(urlopen(BASE+'manifest.json',timeout=30))
local=Path('frontend/public/demo')
checked=0;exact=0;roundoff=[]
for scenario in manifest['scenarios']:
    for seed in scenario['seeds']:
        name=f'{scenario["id"]}-{seed}.json.gz'
        raw=urlopen(BASE+name,timeout=30).read()
        assert hashlib.sha256(raw).hexdigest()==manifest['files'][name]['sha256']
        online=json.loads(gzip.decompress(raw));generated=json.loads(gzip.decompress((local/name).read_bytes()))
        if online==generated:exact+=1
        else:
            def compare(a,b,path=''):
                if a==b:return
                if isinstance(a,dict) and isinstance(b,dict):
                    assert a.keys()==b.keys(),path
                    for k in a:compare(a[k],b[k],path+'/'+str(k))
                elif isinstance(a,list) and isinstance(b,list):
                    assert len(a)==len(b),path
                    for i,(x,y) in enumerate(zip(a,b)):compare(x,y,path+'/'+str(i))
                elif isinstance(a,float) and isinstance(b,(float,int)) and abs(a-b)<=1e-12:
                    roundoff.append({'file':name,'path':path,'absolute_error':abs(a-b)})
                else:raise AssertionError((name,path,a,b))
            compare(online,generated)
        checked+=1
    print(scenario['id'],'online and local trajectories verified; strict discrete states, numeric tolerance 1e-12')
report={'paired_seeds':checked,'exact_pairs':exact,'numeric_tolerance':1e-12,'roundoff_differences':roundoff,'max_absolute_error':max((d['absolute_error'] for d in roundoff),default=0),'note':'Linux CI same-runtime recomputation is exact. Windows vs Linux floating reduction may differ in last bits; values are preserved, never rounded in data.'}
out=Path('output/v020');out.mkdir(parents=True,exist_ok=True);(out/'online-recompute.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='roundoff_differences'}))
