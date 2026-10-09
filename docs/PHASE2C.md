# Phase 2C acceptance and research protocol

Executed locally on 2026-10-09. Engines remain `0.2.0` and `social-1.0.0`: storage optimization does not change simulation outcomes. Reference environment: Python 3.14.6, Node 24.19.0, backend requirements lock, frontend package lock. No paid provider or public deployment was used. This directory has no Git repository; none was created.

## Workflow and parameter contracts

Create a social world. Sensitivity Lab scans one parameter or a complete two-axis grid. Criticality Explorer scans, ranks adjacent regions, adds local samples and validates selected endpoints with disjoint seeds across populations and networks. Robustness Analysis independently validates every amplitude. Presets 5/30/100 are computational choices, not significance thresholds.

Each cell links to a persisted experiment with complete A/B trajectories, configuration, seeds, engine and dependency fingerprint. Open it to inspect seven time curves and individual seeds. Agent memory/details load on selection. Refresh restores scan and experiment IDs. Summary JSON and full server-prepared archive are separate downloads.

Existing SocialConfig and Intervention validators enforce bounds: trust speed [0,.5]; incentive/transmission/opinion speed [0,1]; resource amplitude [-50,50]; normalized intervention [-1,1]. Centrality is degree-rank percentile [0,1], ties by node ID. WS degree must be even, >=2 and <N. ER expected degree maps to p=k/(N-1). BA maps k/2 to integer attachment and reports actual finite-size degree. Illegal combinations return 422 before execution.

Final effects are paired B-A. Tables retain individual values, mean, sample SD and deterministic 2,000-resample percentile-bootstrap 95% intervals. Direction consistency=max(positive count,negative count)/N; zeros count in the denominator. Small-sample intervals can mislead. No automatic significance or real-world causal claim is made.

`exploration-1.1.0` ranks adjacent candidates by response threshold then absolute slope. An exploratory heterogeneity hint marks slopes >2 times the other mean slopes. These diagnostics distinguish below-threshold/unresolved response and seed variability from candidate rapid response, but cannot prove smoothness, discontinuity or a phase transition. Independent stability requires threshold-sized, same-direction changes with intervals excluding zero in every requested validation setting. Discovery selection is biased; independent outcomes are separate. No multiplicity correction is implemented.

The large acceptance scan recorded `exploration-1.0.0`, which ranked absolute adjacent contrasts and selected .1-.2. That version and its results remain unchanged. Browser acceptance used 1.1.0 with five independent seeds. Algorithm revisions never relabel old experiments or silently change the simulation engine.

Intervention cost is dimensionless: 0 for no/zero intervention, otherwise 1+abs(amplitude)/20 for resources, or /0.2 for normalized interventions. It is not currency or resource units.

## Actual experiments A-E

All use social-1.0.0 rule mode and 50 rounds. Configurations, seeds, dependency versions and complete trajectories are retained.

A: `175fcd8d-40da-4934-9aad-dee81b834957`; resource amplitudes [-50,-10,-1,0,1,10,50], discovery 42-46, independent 10042-10071. Resource -1 produces final cooperation paired mean=0, SD=0 and trust mean=-.00012574. Resource -50 gives cooperation mean=-.016, SD=.0274929 and trust=-.00627565. Tiny perturbations do not inevitably amplify. Rule action scores include scarcity=max(0,1-resource/40); perturbations away from scarcity/action thresholds often leave actions unchanged while still altering resource metrics.

B/C/E: `13d1fe9d-2e8a-4367-8a22-48be7262a78f`; transmission [0,.01,.03,.05,.1,.2,.4,.7,1], two refinements, discovery 42-46, 30 independent seeds 10042-10071, 1190 simulations. The selected .1-.2 interval increases final coverage in all nine settings:

| N | Network | Mean coverage change | Descriptive 95% interval |
| --- | --- | ---: | --- |
| 30 | WS | .353333 | [.288889,.418917] |
| 30 | ER | .323333 | [.242194,.410000] |
| 30 | BA | .245556 | [.186667,.317778] |
| 50 | WS | .321333 | [.262000,.380683] |
| 50 | ER | .280667 | [.206000,.356667] |
| 50 | BA | .276000 | [.218667,.342667] |
| 100 | WS | .326333 | [.268325,.383008] |
| 100 | ER | .428333 | [.345658,.505342] |
| 100 | BA | .285000 | [.232317,.345000] |

This supports a candidate finite-size high-sensitivity region, not a statistical-physics phase transition. Initial agent attributes share addressable draws at fixed N. Expected degree is approximately matched at four; finite BA density is lower and ER degree fluctuates. Actual degree is recorded per seed. Between-network differences cannot be attributed purely to topology. Three populations do not establish a thermodynamic limit.

D: 30 paired seeds 42-71. Trust off: `4200c107-cf71-4134-9a5f-cfad8013f396`, cooperation mean=-.0353333, interval [-.0726833,.00466667]. Cooperation off: `2f44b088-3269-43d3-8716-6c913b3916e2`, cooperation mean=+.2993333, coverage=-.204. This switch freezes initial action labels and disables exchange/rewards; increased cooperation metric is not increased realized cooperative exchange. Diffusion off: `fab8f7b6-18c3-4ee0-b870-6e75f25d0014`, coverage=-.5886667, disagreement=+.2610510. Remaining coverage is initial-origin share 1/50.

## Storage measurements

Reference `output/playwright/phase2b-experiment.json`, experiment `1e651584-0eec-4d25-b7f5-5f5d18e94a55`, 30 paired seeds/50 agents. Actual component bytes: Agent snapshots 112,575,722; network 21,146,050; events 9,275,453; metric series 985,274; other snapshots 1,114,494; metadata 1,569,043. JSON was already compact; indentation was not the bottleneck.

| Local file measurement | Before | After |
| --- | ---: | ---: |
| Normal JSON / summary bytes | 147,786,323 | 1,059,394 |
| Python read/parse seconds | 6.110951 | .043591 |
| Python tracemalloc parse peak bytes | 746,260,037 | 3,476,947 |
| Full archive bytes | 147,786,323 JSON | 27,286,892 ZIP/gzip |

Summary is 99.28% smaller; archive is 81.54% smaller. A 10-round full chunk is 469,104 bytes, read in .009353 seconds. First legacy sidecar indexing took 5.553168 seconds. Summary intentionally excludes raw trajectories; full archive restores them exactly. These memory/time numbers measure Python/file parsing, not browser RSS or network latency. Browser request timings and response lengths are separately retained in `output/research/phase2c-browser-finish.log`. Cross-origin Resource Timing bytes were unavailable; the browser request client measured response lengths instead. Original SQLite legacy payloads remain intact, so database disk usage is not claimed to shrink.

Warm local browser request-client measurements: the recorded first sample measured summary .069s / 284,682 compressed bytes, first baseline network chunk .039s / 55,728 bytes, variant .040s / 55,424 bytes. A final settled-page recapture measured .116s/.062s/.066s respectively, with identical response lengths. Together the initial browsing payload is 395,834 compressed bytes (1,687,775 decoded bytes). These are request-to-body timings, not complete render times or a browser-memory before/after comparison. The browser also confirmed legacy 0.2.0 history and exact scan-cell reproduction.

Version-1 sidecars under `data/experiments-trajectories/{UUID}/` contain summary/metadata gzip and 10-round chunks by seed/branch, compressed/raw SHA256 checksums, atomic manifest publication. API interval limit is 20 rounds. Frontend caches the current seed/interval, strips network-memory payloads and fetches Agent details on demand. Legacy full GET/JSON export remain available and intentionally cost more memory.

ZIP copies compressed files without decompression. Record metadata retains seeds/configurations/dependency versions. Scan archives include scan.json and child archives. `python -m backend.verify_phase2c_download` restores in isolated temporary directories and checks all complete results; it never overwrites history. The original 148 MB reference and all three browser-downloaded child archives passed exact equality. No UI import-to-catalog action is provided.

Experiment schema 1 remains readable; legacy artifacts gain lazy sidecars without deleting original payloads. Separate job/scan SQLite schemas are version 1 and reject newer unknown versions. .gitignore excludes databases, data and generated output.

## Tasks and acceptance

Durable states: QUEUED/RUNNING/COMPLETED/CANCEL_REQUESTED/CANCELLED/FAILED. One worker, at most four active/queued tasks, preflight simulation limits, round/seed cooperative cancellation and runtime budgets. Completed pairs are retained and marked incomplete/cancelled; unfinished pairs are excluded. Startup marks interrupted jobs failed without automatic resume. Database opening/import does not mutate live task state.

A/B, search, scans and frontend studies use the bounded manager. New `/api/studies/jobs` supports cancellation while legacy synchronous `/api/studies` remains compatible. Archive jobs check cancellation between child archives; an individual compression/file-copy operation is not forcibly killed midway.

Real browser cancellation: `7a4b2ddc-d939-4ad6-96f0-50da353daaee` requested 1200 simulations, stopped after 10 simulations/five completed pairs. Partial child `b5d8ac6f-28d5-4a6a-8c08-3293b61e3658` is cancelled/incomplete. Refresh preserved CANCELLED with unchanged progress.

76 backend tests pass including all original 57. Added coverage: parameter/grid validation, deterministic cell replay, disjoint validation, detector fixtures, archive/chunk/legacy equality, lazy network/detail contracts, cancellation with partial pairs, queue limits, budget/failure/recovery and asynchronous study cancellation. Frontend build passes with existing Lucide directive and bundle-size warnings.

Edge acceptance created a 50-agent world, ran five-seed sensitivity/criticality scans, viewed real curves and independent validation, refreshed/reopened history, downloaded both exports, restored archives, cancelled a long task, reopened both historical engines and reproduced a stored scan cell exactly. Desktop 1440/mobile 390 checked overflow and page errors. Scripts: `frontend/e2e/phase2c.js`, `phase2c-cancel.js`, `phase2c-finish.js`; outputs under output/research and output/playwright.

Remaining limits: no phase-transition proof or multiplicity correction; approximate density control; existing population cap 100; no before/after browser-process RSS measurement; expensive first legacy migration/full JSON; sidecars of explicitly deleted experiments remain on disk pending a safe garbage collector. Paid LLM expansion, full Causal Trace, real-world data and public deployment remain outside scope.
