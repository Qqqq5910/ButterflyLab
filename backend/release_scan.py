"""Build a reviewed public-file allowlist; print paths/counts, never matched secrets."""
import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PUBLIC_DIRS=['backend','frontend/src','frontend/e2e','frontend/public','examples','docs','scripts','.github']
PATTERNS=[r'(?i)sk-[a-z0-9_-]{24,}',r'(?i)Bearer\s+[a-z0-9_-]{24,}',
          r'(?i)[A-Z]:[\\/]+Users[\\/]+[^\\/\s]+',r'(?i)(?:api_key|password)\s*[:=]\s*["\'][a-z0-9_-]{24,}']


def public_files():
    files=[p for p in ROOT.iterdir() if p.is_file() and p.suffix in ['.md','.txt']]
    files += [ROOT/n for n in ['LICENSE','.gitignore','.env.example','.python-version','.node-version']]
    files += [ROOT/'frontend'/n for n in ['index.html','package.json','package-lock.json','vite.config.mjs']]
    for directory in PUBLIC_DIRS:
        files.extend(p for p in (ROOT/directory).rglob('*') if p.is_file() and
                     not any(x in p.parts for x in ['__pycache__','.pytest_cache']))
    return sorted(set(p for p in files if p.exists()))


def scan(account=None):
    secret=None
    if account:
        from .tokenhub_probe import account_config
        _,secret=account_config(account)
    files=public_files();bundle=list((ROOT/'frontend/dist').rglob('*'))
    findings=[]
    for path in files+[p for p in bundle if p.is_file()]:
        content=path.read_bytes()
        text=content.decode('utf-8',errors='replace')
        if (secret and secret.encode() in content) or any(re.search(p,text) for p in PATTERNS):
            findings.append(str(path.relative_to(ROOT)))
    history='not applicable: no Git repository'
    if (ROOT/'.git').exists():
        history='requires separate full-history audit before release'
    # The allowlist is deliberate: local research databases and outputs are never copied.
    report={'public_files':len(files),'built_files_checked':sum(p.is_file() for p in bundle),
            'exact_operator_key_checked':bool(secret),'findings':sorted(set(findings)),
            'git_history':history,'allowlist':[str(p.relative_to(ROOT)).replace('\\','/') for p in files],
            'scope':'Known patterns and optional exact key; not an exhaustive security audit'}
    out=ROOT/'output/research';out.mkdir(parents=True,exist_ok=True)
    (out/'release-scan.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='allowlist'},indent=2))
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--account');args=parser.parse_args()
    raise SystemExit(1 if scan(args.account)['findings'] else 0)
