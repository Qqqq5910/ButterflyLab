# Public replay format 1

Run from the repository root with locked Python dependencies:

```sh
python scripts/build_public_demo.py
python scripts/verify_public_demo.py
cd frontend
npm run test:explore
VITE_APP_MODE=PUBLIC_STATIC_DEMO npm run build
```

PowerShell: set `$env:VITE_APP_MODE='PUBLIC_STATIC_DEMO'` before `npm run build`.
The Vite base is `/ButterflyLab/`. Generated `frontend/public/demo` is ignored;
Actions regenerates it from the existing rule engine rather than committing large files.

`manifest.json` lists three exact configurations, five paired seeds (42–46),
engine `social-1.0.0`, Python/package versions and environment fingerprint.
Each file has compressed and raw SHA-256, byte counts and a format version.
Summary JSON contains complete configurations, paired finals, summary statistics,
metric definitions and all time series. A small initial-world preview loads first.
Each seed's two full, losslessly gzip-compressed runs load only when selected.
Runs retain initial states, all snapshots, events, transmission paths and decisions.
Browsers handle either raw gzip or server-applied Content-Encoding; content integrity
is checked before data is rendered. Promises are cached; failed loads can retry.

Public mode is **Interactive Replay of Real Simulations**, not arbitrary live computation.
Only exact precomputed configurations run. Custom supported questions are interpreted
but require Local Research to execute; unsupported questions produce no results.
The free template interpreter implements a replaceable `interpret(text, scenarios)`
contract; no LLM implementation is activated.

For global changes the adapter clones the exact initial agents/edges and changes
only `transmission` or `incentive`. Existing counter-based random streams stay intact.
The influential scenario chooses the maximum initial-degree uninformed node for each
seed, ties by smallest ID; selection happens before any outcome. No seed is chosen
for dramatic presentation. The initial display uses seed 42; users can select all five.

Five-seed bootstrap intervals are descriptive, not evidence of significance.
Transmission is a probability multiplier using trust, edge strength and susceptibility,
not guaranteed speed. These are finite synthetic societies, not real-world forecasts.
The new adapter has no new scientific engine version because no equation, random
stream or metric changed. Application version and scientific engine version are distinct.

Cross-platform verification: deployed Linux trajectories versus Windows recomputation
matched exactly for 12/15 paired runs. The other three differ only in modularity
round-off, maximum absolute error `2.220446049250313e-16`; all discrete state and
numeric comparisons pass tolerance `1e-12`. Same-runtime CI recomputation is strict
full equality. Original floating values remain lossless. Run
`python scripts/verify_online_demo.py` after local generation to repeat the online check.

Local `/api/explore/run` validates schemas, persists through the existing Store and
trajectory format, and supports the existing summary/archive/reproduce endpoints.
The full original Research console is lazy-loaded locally. Public Research entry
explains installation instead of attempting localhost requests.

Share links allow only `scenario_id`, `intervention_id=default`, `seed`, `round`.
Unknown/duplicate/out-of-bounds parameters are rejected. No external URLs, paths,
credentials or scripts are accepted. GitHub Pages serves static files only.
