# Contributing

Use Python 3.14.6 and Node 24.19.0 with the committed dependency locks.
Fork and clone the repository, then run `scripts/free-demo.ps1` in PowerShell
or `sh scripts/free-demo.sh` on Linux/macOS. See [Quick Start](README.md#quick-start)
for installation, ports and tested platforms. Open the local page and click **Run Demo**.

Use the virtual environment's Python (`.venv/Scripts/python.exe` on Windows,
`.venv/bin/python` on Unix) for `-m pytest backend -q`, `-m backend.verify_pilot`,
`-m backend.release_scan` and `-m backend.repository_hygiene` from the project root.
Run `npm ci` and `npm run build` in `frontend`. Linux maintainers can also run
`python scripts/startup_smoke.py` to check the launcher and owned-process cleanup.

Report bugs with OS/runtime versions, expected/actual behavior and minimal steps;
attach only sanitized logs. Feature requests should explain the research or user
need. Reproduction issues should include engine/runtime fingerprints, complete
configuration, paired seeds, archive checksums and expected/observed metrics.
Use the repository's Issue templates; never attach keys or private account data.

Create a focused branch in your fork and open a Pull Request against `main`.
Describe the behavior change and actual verification, including screenshots for
UI changes. Documentation fixes, clearer errors and focused regression tests
are suitable first contributions; these are suggestions, not existing Issues.

CI uses only Rule/Mock and recorded actions. Never add provider credentials to
CI, fixtures, screenshots or reports. Preserve historical schemas and tapes.
Version intentional simulation changes and document the affected results.
Include paired configurations, seeds, actual metrics and limitations with any
research claim. A steep finite-size curve is not proof of a phase transition.

Keep changes focused; do not commit local databases, raw account files, output,
node_modules or virtual environments. Review `SECURITY.md` before publishing.
