# Contributing

Use Python 3.14.6 and Node 24.19.0 with the committed dependency locks.
Run `python -m pytest backend -q`, `python -m backend.verify_pilot`, and
`npm ci && npm run build` in frontend before submitting changes.

CI uses only Rule/Mock and recorded actions. Never add provider credentials to
CI, fixtures, screenshots or reports. Preserve historical schemas and tapes.
Version intentional simulation changes and document the affected results.
Include paired configurations, seeds, actual metrics and limitations with any
research claim. A steep finite-size curve is not proof of a phase transition.

Keep changes focused; do not commit local databases, raw account files, output,
node_modules or virtual environments. Review `SECURITY.md` before publishing.
