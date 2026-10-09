# ButterflyLab v0.1.1 Release Report

## Publication

- Repository: https://github.com/Qqqq5910/ButterflyLab
- Main at publication / v0.1.1 target commit: `825d1e2dbb60454d6d84385e4ec6904352cfbf52`.
- Annotated tag object SHA: `e6f3db5c37948fe41e878edb169e856455ca493a`.
- Release CI: [37893699084](https://github.com/Qqqq5910/ButterflyLab/actions/runs/37893699084), **PASS**.
- Initial Linux acceptance CI: [37893220020](https://github.com/Qqqq5910/ButterflyLab/actions/runs/37893220020), **PASS**.
- Tag-triggered CI: [37893912124](https://github.com/Qqqq5910/ButterflyLab/actions/runs/37893912124), **PASS**.
- Release: https://github.com/Qqqq5910/ButterflyLab/releases/tag/v0.1.1
- Published 2026-10-09 06:30:50 UTC; API read-back confirms normal Release,
  neither draft nor prerelease, with the requested title.
- This report's publication evidence is a subsequent documentation commit on main;
  the immutable release tag is not moved. The main SHA above is the publication snapshot.
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
- Release allowlist scan: 106 public files plus three build files, zero findings;
  no operator account/key file read. Full index/history audit also required before commit.
- Full index/history audit: 106 files and 115 historical blobs; zero findings
  before the final experience/documentation commit. No database, private logs,
  account file, key, build cache or large trajectory staged.
- No paid API request or public deployment in this release.
- Linux CI: 98 passed in 10.71 seconds; launcher smoke reports PASS for both
  real free simulation/reproduction and cleanup. Ubuntu runner image 24.04.
- Windows Ctrl+C released ports 8004/5176; incumbent ports 8001/8002/5173/5174
  still belonged to their original processes afterward.
- Remote English README: actual GitHub desktop/mobile GIF loaded at 960 x 540;
  screenshots four seconds apart differed at both widths, confirming playback.
  Badge images also loaded; Quick Start and research text rendered.
- GitHub intermittently returned 503/504 for pages and auxiliary resources;
  unrelated global-navigation 404s also occurred. These are not reported as clean
  browser console results. Chinese README exists and its 5,497-byte file was
  read back through GitHub API, but main/tag browser routes repeatedly returned
  503/504. **Chinese remote rendering NOT VERIFIED** in this session.

## Limits

- macOS not verified; Social Preview needs manual settings upload.
- Chinese README remote page rendering blocked by GitHub 503/504, despite
  successful source/API verification; no complete remote rendering claim.
- No MP4 required: GIF is well below the eight MB target.
- Real multi-seed LLM society study remains incomplete. One historical TokenHub
  connectivity request is not research evidence.
- Existing finite-size high-sensitivity observations remain candidates, not proof
  of a statistical-physics phase transition. No new research claim introduced.
