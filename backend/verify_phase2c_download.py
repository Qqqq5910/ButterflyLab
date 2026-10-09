"""Verify every trajectory in the browser-downloaded scan archive."""
import json,zipfile,tempfile
from pathlib import Path
from .storage import Store
from .trajectories import verify_archive,encode

def verify():
    store=Store();path=Path('output/playwright/phase2c-scan.zip');checked=[]
    with zipfile.ZipFile(path) as archive,tempfile.TemporaryDirectory() as tmp:
        scan=json.loads(archive.read('scan.json'))
        for name in archive.namelist():
            if not name.endswith('.zip'):continue
            child=Path(tmp)/name;child.write_bytes(archive.read(name));eid=Path(name).stem
            assert verify_archive(child)==store.get(eid)['result']
            checked.append(eid)
    report={'scan_id':scan['id'],'verified_children':checked,'all_identical':True,'archive_bytes':path.stat().st_size}
    Path('output/research/phase2c-browser-archive-verification.json').write_bytes(encode(report))
    print(json.dumps(report))

if __name__=='__main__':verify()
