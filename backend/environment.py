"""Runtime and installed-distribution fingerprint for compatibility checks."""
import platform
import hashlib
import json
from importlib.metadata import distributions

def environment():
    packages={d.metadata['Name']:d.version for d in distributions() if d.metadata['Name']}
    detail={'python':platform.python_version(),'packages':dict(sorted(packages.items()))}
    return detail|{'fingerprint':hashlib.sha256(json.dumps(detail,sort_keys=True).encode()).hexdigest()}
