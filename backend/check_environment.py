"""Check the committed Python lock against the running environment."""
from pathlib import Path
from importlib.metadata import version
import platform

if __name__=='__main__':
    errors=[]
    for line in Path(__file__).with_name('requirements.lock.txt').read_text().splitlines():
        name,expected=line.split('==')
        if version(name)!=expected: errors.append(f'{name}: installed {version(name)}, expected {expected}')
    if platform.python_version()!='3.14.6':errors.append('Reference Python runtime is 3.14.6')
    print('\n'.join(errors) if errors else 'Python runtime and locked dependencies match.')
    raise SystemExit(bool(errors))
