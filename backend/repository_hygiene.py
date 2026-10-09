"""Check staged/tracked files and history without displaying secret values."""
import re
import subprocess
from pathlib import Path
from .release_scan import PATTERNS, ROOT


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def main():
    paths = list(filter(None, git('ls-files', '-z').decode().split('\0')))
    findings = []
    forbidden = {'data', 'output', 'node_modules', '.venv', '.impeccable', '.playwright-cli', '__pycache__', 'dist'}
    for name in paths:
        path = Path(name)
        if forbidden.intersection(path.parts) or (path.name.startswith('.env') and path.name != '.env.example'):
            findings.append((name, 'private/generated path'))
        content = git('show', ':' + name)
        if len(content) > 5_000_000:
            findings.append((name, 'file exceeds 5 MB'))
        if any(re.search(p, content.decode('utf-8', errors='replace')) for p in PATTERNS):
            findings.append((name, 'sensitive pattern'))
    head = subprocess.run(['git', 'rev-parse', '--verify', 'HEAD'], cwd=ROOT, capture_output=True)
    blobs = 0
    if head.returncode == 0:
        for line in git('rev-list', '--objects', '--all').decode().splitlines():
            ident = line.split(' ', 1)[0]
            if git('cat-file', '-t', ident).strip() != b'blob':
                continue
            blobs += 1
            content = git('cat-file', 'blob', ident)
            if len(content) > 5_000_000 or any(re.search(p, content.decode('utf-8', errors='replace')) for p in PATTERNS):
                findings.append((ident, 'history blob requires review'))
    print(f'Repository hygiene: {len(paths)} files, {blobs} history blobs, {len(findings)} findings')
    for name, reason in findings:
        print(name, reason)
    return bool(findings)


if __name__ == '__main__':
    raise SystemExit(main())
