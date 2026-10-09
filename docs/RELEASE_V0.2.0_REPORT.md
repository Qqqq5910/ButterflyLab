# v0.2.0 — Interactive Parallel Worlds

Verified 2026-10-09. Application version changes; scientific engines remain unchanged.

## A. Product experience

Default Explore Mode is implemented: bilingual free template questions → explicit
single-change confirmation → synchronized A/B replay → actual outcomes → share.
Real Agent networks are shared with the preserved Research console. Controls expose
play/pause, restart, speed, seed, round seek, agent inspection, transmission edges,
state-derived difference rings and actual metric curves. Research Details retains
configuration, seeds, formulas, per-seed finals/deltas, SD, bootstrap intervals,
engine and runtime information. Unsupported/illegal input produces no simulation;
valid custom configurations run locally and are never silently replaced online.

Public Research Mode links to local setup; local Research Mode retains World Studio,
Rule/Mock/optional Real decisions, seven metrics, searches, studies, sensitivity,
criticality, history, lossless export and reproduction. No paid model was called.

Share links whitelist scenario, default intervention, seed and round; unknown,
duplicate or out-of-range parameters cannot restore an experiment. New tab and
refresh restoration passed on the actual deployed site. The optional result-image
generator is not implemented; links and downloadable summary JSON are available.

A new 20-second, 120-frame, 960×600 GIF was captured from the real online Information
Ripple UI (display seed 42), rendered at 6 fps: `docs/assets/butterflylab-explore.gif`,
693,557 bytes. The existing 24-second Research GIF is preserved. Frame sampling and
FFprobe confirmed the new GIF's content, dimensions and duration; it is screen capture,
not a generated simulation illustration.

## B. Online demo

**https://qqqq5910.github.io/ButterflyLab/** is deployed and browser-verified.

GitHub Pages with `.github/workflows/pages.yml` builds generated data on Ubuntu,
checks it, builds Vite with `PUBLIC_STATIC_DEMO`, uploads and deploys static files.
Only the deploy job has `pages:write` and `id-token:write`; contents permission is read.
No API key, signup or Python backend is required. No public FastAPI/database,
paid service, external model call or tracking script is deployed. It is labeled
**Interactive Replay of Real Simulations**, limited to exact precomputed presets.

Actual Edge/Chromium browser checks: question → conditions → A/B; play, pause,
round 17 seek, agent details, curves/narrative, share, new tab and reload; three
scenario outcomes, seed 42/46 switching; rejection of custom unavailable configs
and malicious/out-of-bounds URL parameters; local setup from Research entry.
Desktop 1440, tablet 1024 and mobile 390 have no horizontal overflow; reduced-motion
operation passed. Static browser request audit recorded zero backend requests and
zero page errors. Scripts: `verify-v020-browser.cjs`, `verify-v020-online-extra.cjs`.

## C. Scientific credibility

All three presets use `social-1.0.0`, rule decisions, 50 agents, 50 rounds, a BA
network with attachment 2 and paired seeds **42,43,44,45,46**. Base transmission .1,
incentive .3, trust speed .03, opinion speed .15; all other model defaults are
preserved in complete exported configurations. Global variants clone the exact
initial agents/edges and change one rule. Local information injection changes only
the selected node's informed state at round zero.

| Scenario | Declared change | Final A mean | Final B mean | Mean B−A | SD | Descriptive 95% interval |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Information Ripple | Global transmission .1 → .2 | coverage .568 | .940 | .372 | .251635 | [.176, .5601] |
| Influential Node | Initial-degree selected uninformed node gets information | coverage .568 | .808 | .240 | .230217 | [.060, .420] |
| Cooperation Dilemma | Global incentive .3 → .6 | cooperation .232 | .968 | .736 | .194628 | [.576, .8922] |

Selection: maximum initial degree among uninformed nodes, ties by smallest ID,
evaluated before the simulation for each seed. No outcome-based selection.
Displayed seed 42 is an illustrative sample; every seed is selectable and its
effect remains in the table. Five seeds provide descriptive uncertainty, not a
statistical significance claim or real-world prediction. Transmission is an
edge-probability multiplier, not guaranteed speed. These are new preset results,
not repackaged Phase 2C validation or evidence about real LLM societies.

`build_public_demo.py` executes the existing engine. `verify_public_demo.py`
recomputes all 15 paired runs and requires full equality of initial states,
snapshots, events, transmission paths, series, finals and summaries. Same-runtime
Windows checks and Linux CI passed strictly. Backend tests independently recalculate
metrics from snapshots and verify sole changes and pre-outcome node selection.

Cross-platform online/local verification (`verify_online_demo.py`) checks original
gzip SHA-256 and all data. **12/15 pairs are exactly equal**; three differ only in
modularity floating-reduction round-off. Maximum absolute error
`2.220446049250313e-16`, within declared `1e-12` tolerance; all discrete states match.
Original values are retained losslessly, not rounded to manufacture equality.
Runtime fingerprint, package versions, format version, raw/compressed checksums
and sizes are saved in the public manifest. Exact reproduction is promised for
matching engine/runtime; different platforms can have last-bit reduction differences.

## D. Engineering quality

- **103 backend tests passed**, including all original 98 and five Explore tests.
- **8 interpreter/share/narrative tests passed**, Chinese/English preset agreement,
  illegal/unsupported/custom inputs and URL whitelist bounds.
- Local and static Vite builds passed; nonfatal lucide `use client` warning remains.
- Real browser local regression passed: Explore live simulation, Research World
  Studio baseline, five-seed A/B, save, reload, JSON download, exact reproduce,
  Mock comparison and recorded replay. Persisted example:
  `33256f2e-ff7a-4813-958a-69912a6d69ac`.
- Sensitivity scan `.1,.2,.4` with five discovery seeds completed and reloaded:
  `429d2da6-12ed-44f1-9ea3-9c6908425c9e`.
- Historical experiment `5e5cab8e-43f7-4a38-9e98-163d26609fca`, engine `0.2.0`,
  remains accessible and all configurations/trajectories/events/metrics reproduced.
- Free-only Rule/Mock pilot checks passed; Linux CI launcher/API/reproduce/cleanup
  smoke passed. No real provider invocation was used.
- Release allowlist and index/full-history hygiene scans returned zero findings.
  Known-pattern scanning is not an exhaustive security audit. Generated public
  replay data is ignored and regenerated by CI; no private local database/output
  or account configuration is committed.
- Independent Impeccable review: **ship**, scoped to Explore. Mechanical detector
  returned no findings. Existing design sidecar drift was not silently repaired.

### Measured resource/performance profile

The generated static replay set is **13,502,521 bytes** plus a 12,061-byte manifest
in the local generator run. It is fetched by scenario/seed; the complete dataset is
not placed in initial frontend state. Initial preview is 23,236 raw bytes;
Information summary is 184,170 raw bytes. The first selected pair is 845,325 gzip
bytes locally versus 4,901,810 raw bytes. Compression/platform output sizes can
differ even when decoded content matches. No historical 148 MB archive is shipped.

Static JS entry: 247.29 kB / 79.09 kB gzip; CSS 21.37 kB / 5.14 kB gzip. Chart code
loads only with results (373.08 kB / 107.70 kB gzip); Research loads only locally
when selected. Browser cold-context first-page assets + manifest + preview transfer
total **94,697 bytes** (excludes the HTML document); through first A/B including
summary/chart/one seed transfer total **1,071,588 bytes**. Trajectories are cached
and repeated same-seed selections reuse them. No large full archive enters the browser.

Actual GitHub Pages fresh browser context: first real network **927 ms**, automated
open → question → confirmation → both networks **1,346 ms**. Prior fresh context
measured 891/1,429 ms; warm complete journey measured 3,103 ms. These are individual
device/network measurements, not fleet guarantees or isolated simulation timings.
The workflow includes actual user actions automated by Playwright. No forced
simulation truncation or fabricated data was used to hit the 30-second goal.

Whole browser-process memory, network animation FPS and slow-device/network
benchmarks were **not measured**; no improvement claim is made for those quantities.

## E. GitHub delivery

Implementation main SHA verified and first deployed:
`d6da64ba817e910044de64112a07422392d2a3d5`.

- Free verification: [37905527212 — success](https://github.com/Qqqq5910/ButterflyLab/actions/runs/37905527212).
- Pages build/deploy: [37905527222 — success](https://github.com/Qqqq5910/ButterflyLab/actions/runs/37905527222).
- Release target: `main` after the documentation/evidence commit; the immutable
  [v0.2.0 tag](https://github.com/Qqqq5910/ButterflyLab/tree/v0.2.0) resolves its exact SHA.
- Formal release: https://github.com/Qqqq5910/ButterflyLab/releases/tag/v0.2.0
  (created only after final checks, as recorded in the final delivery message).
- v0.1.0/v0.1.1 histories and releases are preserved; no force push or history rewrite.

## F. Remaining items and next step

Core requested experience and static deployment are complete. Optional branded
result-image download, browser-process memory/FPS and physical low-performance
device benchmarks are not implemented/measured. The interpreter is intentionally
template-based; arbitrary social questions are unsupported. No new scientific
mechanism or paid LLM expansion was attempted.

Next: test a few first-time visitors' comprehension of “global rule” versus
“local state,” then establish a slow-network/mobile performance baseline before
adding more scenarios. Keep exact configuration matching and reproducibility gates.

Local start: `powershell -ExecutionPolicy Bypass -File scripts/free-demo.ps1`,
or `sh scripts/free-demo.sh`; locked Python 3.14.6 and Node 24.19.0. Default Explore;
Research button opens the full local console. Public data generation/check commands
are in `docs/PUBLIC_DEMO.md`.
