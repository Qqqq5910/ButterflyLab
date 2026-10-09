"""Recompute every public trajectory and verify scientific and byte integrity."""
import gzip,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.explore_mode import scenario_request,run_explore
root=Path('frontend/public/demo')
manifest=json.loads((root/'manifest.json').read_bytes())
assert manifest['format_version']==1 and manifest['engine_version']=='social-1.0.0'
for name,meta in manifest['files'].items():
    raw=(root/name).read_bytes()
    assert len(raw)==meta['bytes'] and hashlib.sha256(raw).hexdigest()==meta['sha256'],name
for scenario in manifest['scenarios']:
    result=run_explore(scenario_request(scenario))
    summary=json.loads((root/scenario['summary']['file']).read_bytes())
    assert result['paired']==summary['paired'] and result['summary']==summary['summary']
    for i,seed in enumerate(result['seeds']):
        saved=json.loads(gzip.decompress((root/summary['trajectory_files'][str(seed)]['file']).read_bytes()))
        assert saved=={branch:result[branch][i] for branch in ('baseline','variant')}
    print(scenario['id'],'all five seeds, trajectories, events and metrics exactly match')
