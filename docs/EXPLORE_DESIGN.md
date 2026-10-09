# Explore surface — Operate

## Overview

Explore is a code-led extension of ButterflyLab's established **Comparative Scientific Atlas**. It makes the existing Operate task approachable: choose one change, confirm two matched conditions, inspect both networks on a shared timeline, then read the measured evidence. This surface document supplements `DESIGN.md`; it does not establish a new identity or regenerate the existing design sidecar.

`frontend/src/main.jsx` now mounts `ExploreApp.jsx` and imports the incumbent `styles.css` and `studio.css` before `explore.css`. Explore Mode is the default. Research Mode remains available through the mode bar: local deployments lazily load the preserved `ResearchApp.jsx` console; the public static demo presents local setup instructions because it has no Python backend. Research keeps World Studio, saved experiments, sensitivity studies and Rule / Mock / optional Real decision workflows.

The hero's promise, “Change One Thing. Watch Two Worlds Diverge.” leads into a labeled bilingual question field. Submission interprets a supported template and exposes a confirmation before running or opening a replay. The interpreter is deterministic and makes no LLM calls. Unsupported questions produce an explicit error. A public question with no exact precomputed configuration offers presets or local research; it never substitutes another replay.

## Colors

The surface retains the mineral grounds, parchment text, mint, coral and amber defined by the incumbent design. Mint labels World A, coral labels World B, and amber carries primary actions and the shared round cursor. Flat scenario bands and quiet separators keep the interface within the existing atlas vocabulary.

Network marks have their own state semantics, explained beside playback: mint nodes cooperate, coral nodes compete, a blue outline marks an informed agent, and blue edges show recorded transmissions for the selected round. Amber difference outlines mark actual changed agent state between A and B. The declared intervention target can also retain its incumbent intervention treatment. Labels and the key distinguish these meanings from chart series colors.

## Typography

Explore inherits the requested Manrope/system stack. The hero uses a responsive heading (`clamp(32px, 3.5vw, 54px)`, line height `1.12`) with a mint second line; below the mobile breakpoint it uses `36px`. Section titles and explanatory copy remain modest, with paragraphs limited to `75ch`. Seeds, rounds, measurements and configuration details retain monospace treatment. Font availability still depends on the runtime environment.

## Layout

The main surface is capped at `1440px` with `4vw` horizontal padding. A compact mode bar precedes a two-column hero; three example questions follow as an unframed horizontal band. Confirmation shows the explicit A/B conditions. Results then present two network viewports, one shared playback toolbar and seek control, outcome prose, two metric plots, exact round values and expandable Research Details.

The source breakpoints and reviewed viewport widths are distinct:

| Reviewed width | Source-derived layout |
| --- | --- |
| 1440px | Two-column hero, three scenario columns, paired networks and paired plots. Hero network height is `390px`; result networks are `340px`. |
| 1024px | The `1050px` breakpoint reduces hero/result network heights to `320px`/`300px` and places each world's metadata below its label. Hero, scenarios, networks and plots retain their desktop column counts. |
| 390px | Below `700px`, navigation wraps; main padding becomes `18px`; hero, scenarios, paired networks and plots stack vertically. Hero/result network heights are `240px`/`290px`. Actions and playback wrap. A/B confirmation conditions remain two columns. |

The shared seek control spans the available width. Measurements wrap and numerical tables use the incumbent horizontal scroll container. Configuration JSON wraps and has a bounded scroll area. These are functional response rules, not a new project-wide breakpoint scale.

## Elevation & Depth

Sections use the existing flat grounds and separators. Only the paired network workspaces receive a thin frame and work-surface background. Scenario choices remain flat bands; the hero network has a transparent background. Node inspection uses the incumbent network detail treatment rather than introducing a new card system.

## Shapes

Buttons and the question field retain small corners (`4px`). Agents remain circular, with size derived from recorded resource values. The shared `Network.jsx` component uses saved coordinates when present for the social engine, otherwise a deterministic agent-ID layout. Node placement is not randomized by the view.

## Components

### Matched worlds and playback

Explore and local Research use the same `Network.jsx`. Explore supplies baseline and variant snapshots for the same selected seed and round, matching agent IDs and initial ties. The difference list is calculated from actual `informed`, `action`, `resource` and `opinion` values; it is not a decorative divergence animation. Transmission edges are filtered from recorded paths for the displayed round. Clicking an agent exposes its recorded role, action, resources, opinion, information state, ties and trust.

Playback starts on user action. Play/Pause, Restart, speed (`0.5×`, `1×`, `2×`), seed selection, difference highlighting and the round slider operate on the same timeline. Seed selection and manual scrubbing pause playback. A network displays one selected seed; the outcome statement still summarizes all five paired seeds.

### Evidence plots and details

`MetricPlot.jsx` draws World A in mint and World B in coral with an amber selected-round reference line. Coverage, cooperation and mean trust use a fixed vertical domain `[0,1]`; resource mean uses an automatic domain in resource units per agent. Do not describe resource mean as a fixed ratio axis. Lines disable Recharts animation. The horizontal labels expose simulation rounds, and plot text states the metric formula and units.

The bundled records use engine `social-1.0.0`, 50 agents, 50 rounds and paired seeds `42–46`. The five-seed summary and per-seed table come from generated simulation records. Research Details exposes configuration, engine/environment metadata, final A/B values, paired differences, selected nodes, recorded events, standard deviation and a descriptive 95% paired-bootstrap interval from 2,000 resamples. Five seeds support descriptive uncertainty, not significance or real-world causal claims. A selected network seed must not replace the aggregate result.

As a read-back check, `information-summary.json` records final coverage means A `0.568`, B `0.940`, mean B−A `0.372` and interval approximately `[0.1760, 0.5601]`. `influential-summary.json` records coverage difference `0.240`; `cooperation-summary.json` records cooperation difference `0.736`. These are synthetic bundled outcomes, not promises about arbitrary inputs. Initial-degree node selection occurs before simulation, with the declared tie rule, rather than selecting a node by its outcome.

### Loading, sharing and failures

Public Explore first loads the manifest and initial preview, then loads a scenario summary when opened. The selected seed's compressed trajectory is loaded on demand. `checked()` verifies SHA-256 against manifest metadata before decoding JSON, accepts either gzip bytes or already decompressed bytes using the corresponding hash, caches in-flight/successful loads and evicts failed loads. Missing or mismatched files produce an explicit retryable error. Local Explore runs the rule simulation through the backend and requests only the selected seed's current ten-round block for both branches.

Research and metric plots are lazy imports with visible loading fallbacks. Share links contain validated scenario/intervention/seed/round identifiers; exact presets support restoring a replay. Summary download exports the actual result JSON. A local saved result exposes its experiment ID for reopening and reproduction in Research.

### Motion and access

Keyboard focus retains the mint outline; mode buttons expose pressed state, fields are labeled, playback buttons and the round slider have accessible names, and failures/status messages use alert/status roles. Network nodes remain buttons with recorded-state labels.

For `prefers-reduced-motion: reduce`, CSS disables transitions and animations and restores automatic scrolling. Opening a result also selects instant scrolling through the media query. Playback is an explicit user-controlled state progression; the reduced-motion rule does not remove its controls or change recorded results.

## Do's and Don'ts

- Do extend the established atlas through shared controls, network components and measured series.
- Do distinguish exact public replay from live local simulation, and selected-seed inspection from five-seed evidence.
- Do keep ratios on `[0,1]`, show resource units honestly, and retain labels, formulas and uncertainty alongside charts.
- Do preserve matched initial agents/ties and derive differences from recorded state.
- Don't invent successful outcomes, transmission paths, data or qualitative claims for unsupported questions.
- Don't turn this surface extension into a replacement visual identity or silently rewrite `DESIGN.md` / `.impeccable/design.json`.

Evidence checked: `PRODUCT.md`, `DESIGN.md`, `.impeccable/surface.md`, `frontend/src/main.jsx`, `ExploreApp.jsx`, `explore.css`, `explore-core.mjs`, `Network.jsx`, `MetricPlot.jsx`, the preserved `ResearchApp.jsx` entry, and the public manifest plus all three summary records. The existing review captures `.impeccable/review/desktop.png`, `tablet.png` and `mobile.png` visually show the information scenario at seed 42 / round 17, the paired layouts, expanded details and mobile stacking. This document records source and screenshot evidence; it does not claim a new independent browser interaction test or a Research ship review.
