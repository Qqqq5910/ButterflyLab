# ButterflyLab v0.1.0 Release Report

Date: 2026-10-09. Publication target: https://github.com/Qqqq5910/ButterflyLab.

## Publication

Status: **SHIPPED**.

- Default branch: main; initial push succeeded without force.
- Release commit: bd12666c52121a158162c1a537c3b4a3453b226d.
- Annotated v0.1.0 tag points to that verified release commit and is pushed.
- Release: https://github.com/Qqqq5910/ButterflyLab/releases/tag/v0.1.0.
- Hosted CI passed: https://github.com/Qqqq5910/ButterflyLab/actions/runs/37885525906.
  All steps passed: locked runtime/dependencies, 98 tests, free controls,
  frontend build, public-file/bundle scan and repository hygiene.
- Remote README checked in a real browser at 1440 and 390 px: all eight
  README images/badges loaded. Chinese link and Quick Start are present;
  GitHub identifies the MIT license. GitHub emitted an unrelated global
  navigation payload 404; repository content and assets rendered successfully.
- This follow-up report commit documents publication; v0.1.0 remains pinned
  to the original validated code commit rather than moving the release tag.

## Engineering acceptance

- Backend: 98 passed, one Starlette/HTTPX deprecation warning.
- Frontend production build passed; Lucide directive and bundle-size advisory warnings.
- Windows free launcher started isolated API/frontend services and reused dependencies.
- Real browser verified baseline, five paired seeds, A/B information intervention,
  SQLite save, refresh restoration, JSON download and exact reproduction.
- Parameter scan 0.1/0.2/0.4 with five seeds completed and restored after refresh.
- Run Demo started a free 50-Agent Information Cascade baseline.
- Mock five-seed pilot completed; Recorded Replay matched states, events and metrics.
- Legacy engine 0.2.0 experiment read and reproduced with identical=true.
- Desktop 1440 and mobile 390 document widths matched viewport widths; no page errors
  in the main release workflow. Real product screenshots are in docs/assets.
- No public deployment or paid model request occurred during this release.

## Research evidence

The compact example retains original scan configuration, independent seeds
10042-10071, per-seed coverage, paired statistics and measured initial network degrees.
Its source SHA-256 is recorded in examples/transmission-validation.json.
Transmission 0.1 to 0.2 increased mean final coverage by 0.24556-0.42833 across
nine settings: three topologies and populations 30, 50, 100.
These are finite rule-model observations; density is approximately controlled,
topology comparisons retain confounding, and no strict phase transition or
prediction about real societies is claimed.

Historical TokenHub gpt-5.6-luna connectivity was verified once in Phase 2D.
The release makes no live calls. Real multi-seed LLM society research remains
unfinished because account-effective pricing is unverified. Rule and Mock
evidence must not be interpreted as real model behavior.

## Public materials and safety

Bilingual README, MIT license, contribution/security guides, architecture,
methods, experiment/design documents, locked dependencies, free-only CI,
launcher, screenshots and compact examples are included. No GIF was produced.
Full trajectories, SQLite databases, private logs, output, local credentials,
virtual environments, node_modules and internal design artifacts stay local
and are ignored. Public-file/bundle, staged-file, history and size scans are
required before push; final counts are recorded below after verification.
Final pre-push scans: 93 reviewed public files, three built frontend files,
93 history blobs; zero findings. No tracked file exceeds 5 MB. No credentials,
local database, private output or large trajectory was included in the reviewed
index. Exact private-key comparison was deliberately not used this round;
the scanner checked known credential and private-path patterns without reading
the TokenHub account file. Known-pattern scans do not constitute an exhaustive
security audit.

## Remaining scope

Linux/macOS local launcher acceptance, real LLM multi-seed research, strict
network-density matching, multiplicity correction, browser memory benchmarks,
Causal Trace and a public online demo remain future work.
