# ButterflyLab v0.1.1 Release Report

## Publication

- Repository: https://github.com/Qqqq5910/ButterflyLab
- Release candidate/main verified before tagging: `5bac0c4eb7dda99cdcfb649e0976757428d4c1ec`.
- Release CI: [37893220020](https://github.com/Qqqq5910/ButterflyLab/actions/runs/37893220020), **PASS**.
- Release: https://github.com/Qqqq5910/ButterflyLab/releases/tag/v0.1.1
- Existing v0.1.0 commit retained: `bd12666c52121a158162c1a537c3b4a3453b226d`.
- Experience update only: no simulation formulas, random streams, decisions,
  search algorithms, metric definitions or historical schemas changed.

## Presentation

- Description read back: Open-source multi-agent research lab for parallel worlds,
  emergent behavior, and reproducible experiments.
- Eight topics read back: multi-agent-systems, agent-based-modeling, ai-agents,
  emergent-behavior, complex-systems, simulation, research, counterfactual-simulation.
- Homepage empty; default branch main; GitHub identifies MIT.
- `docs/assets/butterflylab-demo.gif`: 605,642 bytes; 960 x 540; 144 frames;
  24 seconds; six fps; loop enabled. FFmpeg decoding found 35 distinct frames.
- Playwright recorded actual Rule states, timeline playback, Agent 1 information
  injection and five-seed A/B coverage results. No curves or effects fabricated.
- Bilingual README puts the GIF, free Quick Start, latest release and accurate
  research limits first. Other full-size screenshots are links to limit eager loading.
  GIF uses GitHub's raw content host: the repository raw redirect intermittently
  returned 504 during acceptance, while the raw content host returned 200.
- `docs/assets/social-preview.png`: 1280 x 640, real product network screenshot.
  **Prepared, NOT SET through GitHub settings.** Upload manually: repository
  Settings > General > Social preview > Edit > Upload an image; choose this file
  and save. No automated settings upload is claimed.
- Contribution instructions, key safeguards and Bug/Feature/Reproduction templates added.

## Platforms

| Platform | Status | Actual evidence |
| --- | --- | --- |
| Windows | PASS | Python 3.14.6 / Node 24.19.0; PowerShell launcher, isolated SQLite, ports 8004/5176; browser free A/B, refresh, export and exact reproduction. |
| Linux | PASS | Ubuntu 24.04 GitHub runner, Python 3.14.6 / Node 24.19.0; locked installs, actual Unix launcher, frontend/proxied API, five-seed A/B, reproduction, free gate and child cleanup. |
| macOS | NOT TESTED | No macOS runner used; no claim based on Windows/static inspection. |

The Unix launcher reuses valid installs and owns exactly two child processes.
Ports bind to loopback and real calls are disabled. Windows reuses valid Python
and frontend installs; only its own backend is terminated on normal exit.
Incumbent local services and historical databases were preserved.

## Engineering Evidence

- Backend: **98 passed**, 8.33 seconds; one existing Starlette/HTTPX deprecation warning.
- Frontend production build: PASS; existing Lucide directive and large bundle warnings.
- `backend.verify_pilot`: PASS; fixed Rule/Mock controls and exact recorded replay;
  historical single action entered the engine with zero live requests.
- Browser Run Demo, five-seed Mock comparison and Recorded Replay: PASS.
- Historical experiment `5e5cab8e-43f7-4a38-9e98-163d26609fca`, engine `0.2.0`:
  read and reproduced exactly, including trajectories, states, logs, metrics and summaries.
- Browser widths 1440 and 390: document scroll widths respectively 1440 and 390;
  no horizontal overflow. Actual screenshots captured in ignored local output.
- Windows five-seed A/B, browser refresh, downloaded Summary JSON and exact Rule
  reproduction: PASS. Experiment `d5d02350-ad8a-4bd5-b6b8-93b728d568c0`,
  seeds 42-46, engine `social-1.0.0`, `identical: true`, `real_ready: false`,
  zero page errors. Summary downloaded to ignored local acceptance output.
- Release allowlist scan: 105 public files plus three build files, zero findings;
  no operator account/key file read. Full index/history audit also required before commit.
- No paid API request or public deployment in this release.
- Linux CI: 98 passed in 10.71 seconds; launcher smoke reports PASS for both
  real free simulation/reproduction and cleanup. Ubuntu runner image 24.04.
- Windows Ctrl+C released ports 8004/5176; incumbent ports 8001/8002/5173/5174
  still belonged to their original processes afterward.

## Limits

- macOS not verified; Social Preview needs manual settings upload.
- No MP4 required: GIF is well below the eight MB target.
- Real multi-seed LLM society study remains incomplete. One historical TokenHub
  connectivity request is not research evidence.
- Existing finite-size high-sensitivity observations remain candidates, not proof
  of a statistical-physics phase transition. No new research claim introduced.
