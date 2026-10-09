# Executed experiments

Phase 2C experiments A-E, persisted IDs, all nine independent validation contrasts and measured storage results are recorded in [Phase 2C acceptance](docs/PHASE2C.md). Raw exports and measurement records are under `output/research/`.

Executed locally on 2026-10-09. These are descriptive synthetic-model outcomes, not validated claims about human societies. Artifacts and databases are ignored generated data; rerunning scripts creates new genuine records without deleting prior experiments.

## Phase 2B twelve-step browser demonstration

`frontend/e2e/phase2b.js` created a 50-agent WS small-world through World Studio, enabled trust/cooperation/diffusion, ran a baseline, applied A01 resource -1, compared 30 paired seeds 42-71, inspected seven A/B curves and per-seed effects, ran trust ablation, saved/reloaded/reopened, downloaded full JSON, checked full rule-result equality, and demonstrated Mock structured decisions with recorded-tape equality. Desktop 1440px and mobile 390px had no page overflow. All twelve requested steps completed with real model results.

| Record | ID |
| --- | --- |
| Social baseline | `32d138d3-38a9-4b79-bab3-9dae8e285d5a` |
| Resource -1 experiment | `1e651584-0eec-4d25-b7f5-5f5d18e94a55` |
| Saved world | `7dea3c40-8b27-4c7d-a86a-549825046df2` |
| Trust ablation | `97d8cc76-11ea-4a3c-b935-1aec36108122` |
| Four-cell sensitivity | `09136de5-b525-4e93-bf45-cd14a563e81c` |

### Final paired intervention effects

B is intervention, A is baseline. Sample SD uses ddof=1; intervals are paired percentile bootstrap, 2,000 resamples with seed 20261008.

| Metric | Mean B-A | Sample SD | 95% bootstrap interval |
| --- | ---: | ---: | --- |
| Cooperation | 0 | 0 | [0, 0] |
| Resource Gini | +0.0000948994 | 0.0003351463 | [-0.0000072560, +0.0002254654] |
| Opinion disagreement | -0.0000206182 | 0.0000966188 | [-0.0000587804, 0] |
| Largest component | 0 | 0 | [0, 0] |
| Information coverage | 0 | 0 | [0, 0] |
| Mean trust | -0.0000225967 | 0.0001990979 | [-0.0001022727, +0.0000344828] |
| Mean resources | -0.0200000000 | approximately 7e-15 | approximately [-0.02, -0.02] |

Removing one resource unit across 50 agents gives the expected -1/50 mean effect under conserved transfers and unchanged total treasury payout. Floating-point noise is not a substantive effect. Only seeds 55 and 60 had nonzero final trust/disagreement effects. Cooperation, connectivity and coverage did not change. This run does not demonstrate a dramatic butterfly effect or statistical significance.

Baseline final averages: cooperation 0.2786667; largest component 0.7913333; coverage 0.6086667; mean trust 0.6176884; mean resources 70.2088686.

### Trust ablation

30 seeds, B disables trust updates and A enables them, with matching initial states.

| Metric | Mean off-on | Sample SD | 95% bootstrap interval |
| --- | ---: | ---: | --- |
| Cooperation | -0.0353333 | 0.1092524 | [-0.0726833, +0.0046667] |
| Gini | +0.0868273 | 0.0254206 | [+0.0781739, +0.0954056] |
| Coverage | +0.1813333 | 0.1847969 | [+0.1226333, +0.2473333] |
| Largest component | +0.2086667 | 0.1361220 | [+0.1633167, +0.2553333] |
| Mean trust | -0.0176884 | See exported artifact | Includes zero |

Freezing trust at its initial value retains ties that dynamic trust would prune. The increased coverage/connectivity is consistent with that mechanism; it does not establish that trust universally improves every outcome.

### Full sensitivity grid

`frontend/e2e/phase2b-grid.js` ran seeds 42-46, trust_speed [0, 0.1] by incentive [0, 0.6]. All four cells were saved, shown in a heatmap and exported. Mean trust effects relative to the configured baseline were -0.0096634001 for both speed-0 cells, -0.0670634001 for (0.1, 0), and +0.3374887704 for (0.1, 0.6). This is five-seed exploratory sensitivity, not a formal significance test. Each cell's baseline/variant configuration and per-seed results are retained.

### Mock decisions

The Mock demonstration accepted 21 structured calls. Call/token budget exhaustion triggered explicit rule fallback. The tape records all 2,500 agent-round decision slots, including fallback. Replaying the stored decisions matched snapshots, metrics, events, decisions and transmission paths exactly. This proves recorded-decision replay, not fresh external-model determinism. The sanitized tape is persisted in the world catalog and exported. No external paid model was called.

## Evidence paths

Under `output/playwright/`:

- `phase2b-experiment.json`: full 147,786,323-byte configuration, seeds, results and trajectories.
- `phase2b-ablation.json`, `phase2b-grid.json`, `phase2b-decisions.json`: actual study and decision exports.
- `phase2b-desktop.png`, `phase2b-mobile.png`: full-page screenshots.
- `phase2b-desktop-top.png`, `phase2b-desktop-charts.png`, `phase2b-mobile-top.png`, `phase2b-mobile-charts.png`: readable detail captures; top captures wait for 50 loaded preview nodes.
- `phase2b-grid-desktop.png`, `phase2b-grid-mobile.png`: grid views.

## Legacy mechanism diagnosis and compatibility

`python -m backend.audit_mechanisms` ran and retained all 15 sensitivity cells (50 agents, 50 rounds, seeds 42-71) in `output/research/legacy-sensitivity.json`. Resource -1/-10 in equal/uniform worlds changed no cooperation trajectories; -50 changed 18/30 equal and 16/30 uniform trajectories. Unequal worlds changed 1/30, 6/30 and 13/30 for -1/-10/-50. Opinion -0.1 changed 5/30, 5/30 and 8/30 cooperation trajectories. Transmission -0.18 changed cascade size while all four primary final metric effects were zero. See the code dependency graph and full table in `docs/MECHANISM_AUDIT.md`.

Historical Phase 2A evidence remains intact: experiment `3f87a501-0313-4c1b-9d37-57a1f8b24357`, seeds 42-46, resource -10, final Gini +0.0000196493, other three final effects zero, full equality replay. Original held-out search `9a962107-9ac8-42dc-9dc0-f363f91528e8` used three candidates and 30 simulations, discovery 42-46 / validation 10042-10046. The held-out Gini mean +0.000517619 had an interval including zero. Regression outputs use separate `phase2a-regression-*` filenames.

The final browser regression reran the complete legacy workflow as `24ea4da0-b916-4519-b369-a5a071f26eba` (baseline `ed526bd7-6881-4369-8071-19a8f3edff58`) with exactly the original effects and full replay equality. Search regression `dfb1ca04-dd8c-4b86-b945-8a4c1e57e8be` retained three candidates, 30 actual simulations, five disjoint validation seeds and exact replay. Final social UI recovery (`phase2b-finish.js`) checked 30 experiment seeds, 14 curves, the five-seed saved grid, selected-cell switching and both responsive viewports after chart/provenance fixes.

## Verification limits

57 backend tests passed, including all 34 inherited tests and 23 social/version/provider/study tests; production frontend build passed. Python runtime/lock consistency passed. Exact rule reproduction applies to compatible engine/dependency environments. External API interoperability was not live-tested. Full trajectories are large; transport gzip does not solve browser memory or storage growth. Study requests remain synchronous without cancellation.
