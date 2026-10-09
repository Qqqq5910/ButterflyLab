"""Measure reference payload composition before changing storage."""
import json, time, tracemalloc, gzip
from pathlib import Path

def size(value): return len(json.dumps(value,separators=(',',':'),ensure_ascii=True).encode())

def profile(path):
    tracemalloc.start();start=time.perf_counter()
    raw=Path(path).read_bytes();record=json.loads(raw)
    seconds=time.perf_counter()-start;_,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
    result=record['result'];runs=result.get('validation',result)
    parts={'agents':0,'network':0,'events':0,'metric_series':0,'other_snapshots':0,'run_metadata':0}
    for run in runs['baseline']+runs['variant']:
        for frame in run['snapshots']:
            parts['agents']+=size(frame['agents']);parts['network']+=size(frame['edges'])
            parts['other_snapshots']+=size({k:v for k,v in frame.items() if k not in ('agents','edges')})
        parts['events']+=size(run['events']);parts['metric_series']+=size(run['series'])
        parts['run_metadata']+=size({k:v for k,v in run.items() if k not in ('snapshots','events','series')})
    return {'reference_bytes':len(raw),'compact_json_bytes':size(record),'gzip_bytes':len(gzip.compress(raw,mtime=0)),
            'load_parse_seconds':seconds,'python_peak_bytes':peak,'components_compact_bytes':parts}

if __name__=='__main__':
    import sys
    p=Path(sys.argv[1]);report=profile(p)
    target=Path('output/research/phase2c-before.json');target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
