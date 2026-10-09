"""Lossless version-1 gzip chunks; publication is atomic, old payloads remain readable."""
import copy, gzip, hashlib, json, os, tempfile, zipfile
from pathlib import Path

HEAVY=('initial','snapshots','events','transmission_paths','decisions')
def encode(value):return json.dumps(value,separators=(',',':'),allow_nan=False).encode()
def digest(raw):return hashlib.sha256(raw).hexdigest()

class Trajectories:
    def __init__(self,root):self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True)
    def folder(self,eid):
        import uuid
        uuid.UUID(eid)
        return self.root/eid
    def exists(self,eid):return (self.folder(eid)/'manifest.json').exists()
    def save(self,eid,payload):
        folder=self.folder(eid);folder.mkdir(exist_ok=True)
        compact=copy.deepcopy({k:v for k,v in payload.items() if k not in ('baseline','variant','validation')})
        data=payload.get('validation',payload)
        if 'validation' in payload:compact['validation']={k:copy.deepcopy(v) for k,v in data.items() if k not in ('baseline','variant')}
        target=compact.get('validation',compact);manifest={'format_version':1,'chunk_rounds':10,'files':{},'runs':{}}
        def write(name,value):
            raw=encode(value);compressed=gzip.compress(raw,mtime=0)
            temporary=folder/(name+'.tmp');temporary.write_bytes(compressed);os.replace(temporary,folder/name)
            manifest['files'][name]={'sha256':digest(compressed),'raw_sha256':digest(raw),'bytes':len(compressed),'raw_bytes':len(raw)}
        for branch in ('baseline','variant'):
            target[branch]=[]
            for run in data[branch]:
                key=f'{branch}-{run["seed"]}';meta={k:v for k,v in run.items() if k not in ('snapshots','events','transmission_paths','decisions')}
                write(key+'-meta.json.gz',meta);chunks=[]
                end=max((s['round'] for s in run['series']),default=0)
                for start in range(0,end+1,10):
                    name=f'{key}-{start}.json.gz'
                    content={field:[v for v in run.get(field,[]) if start<=v['round']<start+10] for field in HEAVY if field!='initial' and field in run}
                    write(name,content);chunks.append({'start':start,'end':min(end,start+9),'file':name})
                manifest['runs'][key]={'branch':branch,'seed':run['seed'],'meta':key+'-meta.json.gz','chunks':chunks,'fields':[f for f in HEAVY if f!='initial' and f in run]}
                target[branch].append({k:copy.deepcopy(v) for k,v in run.items() if k not in HEAVY}|{'snapshots':[],'events':[],'trajectory_available':True})
        write('summary.json.gz',compact)
        temporary=folder/'manifest.tmp';temporary.write_bytes(encode(manifest));os.replace(temporary,folder/'manifest.json')
        return compact
    def manifest(self,eid):
        m=json.loads((self.folder(eid)/'manifest.json').read_bytes())
        if m['format_version']!=1:raise ValueError('Unsupported trajectory format')
        return m
    def read(self,eid,name,manifest=None):
        m=manifest or self.manifest(eid)
        if name not in m['files']:raise KeyError('Unknown trajectory chunk')
        raw=(self.folder(eid)/name).read_bytes()
        if digest(raw)!=m['files'][name]['sha256']:raise ValueError('Trajectory checksum mismatch')
        decoded=gzip.decompress(raw)
        if digest(decoded)!=m['files'][name]['raw_sha256']:raise ValueError('Content checksum mismatch')
        return json.loads(decoded)
    def summary(self,eid):return self.read(eid,'summary.json.gz')
    def interval(self,eid,seed,branch,start,end,agent=None):
        m=self.manifest(eid);run=m['runs'].get(f'{branch}-{seed}')
        if not run:raise KeyError('Seed/branch not stored')
        result={f:[] for f in run['fields']}
        for chunk in run['chunks']:
            if chunk['end']<start or chunk['start']>end:continue
            block=self.read(eid,chunk['file'],m)
            for field,values in block.items():result[field].extend(v for v in values if start<=v['round']<=end)
        if agent is not None:
            agent=int(agent) if str(agent).isdigit() else agent
            for frame in result.get('snapshots',[]):
                frame['agents']=[a for a in frame['agents'] if a['id']==agent]
                frame['edges']=[e for e in frame['edges'] if agent in (e['source'],e['target'])]
            result['events']=[e for e in result.get('events',[]) if agent in (e.get('agent'),e.get('target'))]
            if 'decisions' in result:result['decisions']=[d for d in result['decisions'] if d.get('agent')==agent]
            if 'transmission_paths' in result:result['transmission_paths']=[p for p in result['transmission_paths'] if agent in (p.get('source'),p.get('target'))]
        return result|{'seed':seed,'branch':branch,'start':start,'end':end,'format_version':1}
    def restore(self,eid):
        m=self.manifest(eid);result=self.summary(eid);target=result.get('validation',result)
        for branch in ('baseline','variant'):
            target[branch]=[]
            for r in m['runs'].values():
                if r['branch']!=branch:continue
                run=self.read(eid,r['meta'],m)
                for field in r['fields']:run[field]=[]
                for chunk in r['chunks']:
                    for field,values in self.read(eid,chunk['file'],m).items():run[field].extend(values)
                target[branch].append(run)
        return result
    def archive(self,eid,record):
        folder=self.folder(eid);m=self.manifest(eid);path=folder/'archive.zip'
        temporary=folder/'archive.tmp'
        # Already-compressed chunks are copied into ZIP without decompression or browser buffering.
        with zipfile.ZipFile(temporary,'w',compression=zipfile.ZIP_STORED) as archive:
            archive.writestr('manifest.json',encode(m))
            archive.writestr('record.json',encode({k:v for k,v in record.items() if k!='result'}))
            for name in m['files']:archive.write(folder/name,name)
        os.replace(temporary,path);return path

def verify_archive(path):
    with zipfile.ZipFile(path) as archive:
        m=json.loads(archive.read('manifest.json'))
        if m['format_version']!=1:raise ValueError('Unknown archive format')
        for name,meta in m['files'].items():
            raw=archive.read(name)
            if digest(raw)!=meta['sha256'] or digest(gzip.decompress(raw))!=meta['raw_sha256']:raise ValueError('Archive checksum mismatch')
        # Restore to an isolated temporary directory; never overwrite historical experiments.
        with tempfile.TemporaryDirectory() as temporary:
            eid=json.loads(archive.read('record.json'))['experiment_id'];store=Trajectories(temporary);folder=store.folder(eid);folder.mkdir()
            (folder/'manifest.json').write_bytes(encode(m))
            for name in m['files']:
                if Path(name).name!=name:raise ValueError('Invalid archive path')
                (folder/name).write_bytes(archive.read(name))
            return store.restore(eid)
