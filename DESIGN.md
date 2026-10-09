---
name: ButterflyLab
description: A reproducible comparative research console.
colors:
  intervention-amber: "#d8a866"
  baseline-mint: "#a9ddc6"
  response-coral: "#de8877"
  candidate-gold: "#d3b96c"
  mineral-ground: "#111619"
  navigation-ground: "#0d1214"
  work-surface: "#151d1f"
  input-ground: "#101617"
  parchment-text: "#e9eee9"
  muted-text: "#a0aca6"
  quiet-separator: "#354244"
  control-border: "#465558"
typography:
  headline:
    fontFamily: 'Manrope, "Segoe UI", system-ui, sans-serif'
    fontSize: "31px"
    fontWeight: 600
    lineHeight: 1.1
    letterSpacing: "0"
  title:
    fontFamily: 'Manrope, "Segoe UI", system-ui, sans-serif'
    fontSize: "15px"
    fontWeight: 600
    letterSpacing: "0"
  section-title:
    fontSize: "13px"
    fontWeight: 600
    lineHeight: 1.5
  body:
    fontFamily: 'Manrope, "Segoe UI", system-ui, sans-serif'
    fontSize: "12px"
    lineHeight: 1.6
  measurement:
    fontFamily: "Consolas, monospace"
    fontSize: "11px"
    lineHeight: 1.5
  label:
    fontFamily: "ui-monospace, Consolas, monospace"
    fontSize: "9px"
rounded:
  preset: "3px"
  control: "4px"
  navigation: "5px"
spacing:
  tight: "8px"
  field: "12px"
  section: "16px"
  comparison: "24px"
  studio: "28px"
components:
  button-run:
    backgroundColor: "{colors.intervention-amber}"
    textColor: "#18201f"
    rounded: "{rounded.control}"
    padding: "10px 13px"
  button-export:
    backgroundColor: "#171f21"
    textColor: "#d0d9d3"
    rounded: "{rounded.control}"
    padding: "9px 12px"
  field-input:
    backgroundColor: "{colors.input-ground}"
    textColor: "#e1e8e3"
    rounded: "{rounded.control}"
    padding: "8px 10px"
  navigation-link:
    textColor: "#a9bbb3"
    padding: "12px 10px"
  research-tab:
    backgroundColor: "transparent"
    textColor: "{colors.muted-text}"
    padding: "12px 16px"
  seed-preset:
    backgroundColor: "transparent"
    rounded: "{rounded.preset}"
    padding: "4px 10px"
---

# Design System: ButterflyLab

## Overview

**Creative North Star: "Comparative Scientific Atlas"**

A dark mineral ground supports parchment-white text, warm amber interventions and cool mint baselines. Flat work areas, quiet separators and tabular measurements make repeated comparison the dominant visual task.

This is documentation of the incumbent Operate interface, not a replacement identity. The atlas direction comes from the existing surface contract; values come from the imported frontend styles and implemented research components.

**Key Characteristics:**
- Flat research work areas.
- Compact controls and measured typography.
- Stable semantic color assignments.
- Shared visual frames for comparing experiments.

## Colors

Primary: intervention amber identifies run actions, the identity mark, intervention tags and timeline accents. Secondary: baseline mint identifies baseline series, active research tabs, focused controls and positive heatmap cells. Response coral identifies the response series, competing agents and negative heatmap cells. Candidate gold softly marks candidate intervals.

Neutrals distinguish the outer ground, navigation, work surfaces and inputs without heavy elevation. Parchment text carries primary content; muted text carries labels, seeds and limitations. Quiet separators divide research sections; stronger control borders frame editable elements.

**The Semantic Color Rule.** Keep baseline mint, response coral and intervention amber attached to their measured roles, with labels that also identify the series.

## Typography

Manrope with system fallbacks carries headings, explanatory copy and controls. Monospace stacks carry seeds, field labels, experiment status and numerical tables. The implementation requests Manrope but its availability depends on the runtime font environment.

Tables use tabular numerals. Main headings remain modest; section and plot titles are smaller. Letter spacing is zero in the root styles.

**The Measurement Rule.** Keep measurements, identifiers and experiment metadata visually distinct from prose through the incumbent monospace styles and explicit units.

## Layout

The research shell uses a narrow left navigation and an unframed main workspace, capped at 1600px. Research toolbars wrap and use horizontal separators. Metric charts use two equal tracks; the studio uses a wider preview beside settings, with an additional summary column on wide screens.

At 1000px the research charts and studio become single-column layouts. At 650px navigation disappears, controls wrap, and the main inset shrinks. The base comparison view also has a 950px breakpoint; the studio gains its wide preview arrangement at 1450px. These are incumbent breakpoints, not a newly unified scale.

Plots have explicit heights; response plots are 320px, reduced to 280px on small screens. Tables retain legible columns and scroll horizontally rather than squeezing numbers. Phase 2C parameter-region enlargement changes the visible horizontal interval while preserving its metric vertical domain.

## Elevation & Depth

Research sections are flat and separated by rules. Framed tools and network viewports use slightly lighter grounds. The selected or hovered network node has the only recurring lift treatment: a small dark shadow plus scale increase. There is no general card-shadow scale.

## Shapes

Controls and navigation use small corner radii. Research tabs use a colored bottom border rather than pill shapes. Circular nodes encode agents and circular legend marks identify series; they are functional marks. Sections remain unframed bands, while actual network tools may retain their existing thin frame.

## Components

The amber run button carries the primary command. Bordered export buttons carry secondary commands. Inputs and selects share a dark inset ground, thin border, small radius and compact type. A mint focus outline provides keyboard location.

Research tabs have muted inactive text and a mint active underline. Seed presets are compact bordered buttons with a mint selected treatment. Navigation links use quiet text and a tonal hover background. Status, progress, heatmap values and experiment tables expose measured backend state.

**The Comparison Rule.** Keep chart series labels, units, uncertainty intervals and table measurements visible within the same visual vocabulary as the shared network timeline.

## Do's and Don'ts

### Do:
- Do use flat research sections and quiet separators.
- Do retain baseline, response and intervention color roles alongside textual labels.
- Do preserve explicit plot dimensions and scroll wide numerical tables.
- Do retain keyboard focus outlines and tabular measurements.

### Phase 2D LLM controls

- Rule / Mock / Real use accessible tabs; Rule is the free default.
- Status exposes provider readiness, calls, input/output/reasoning tokens and
  estimated/reserved budget. Reservations are never labeled paid invoices.
- Real consent and Run remain disabled when pricing/input gates fail.
- Pilot status uses persisted task state; cancellation stops future work and
  marks partial results incomplete. Errors are explicit, with sanitized details.
- Mint identifies Rule A; coral identifies alternative B. Shared round controls
  use the mint range accent and bounded dimensions. Coverage axes use [0,1].
- Seed table shows A, B and B-A; the curve labels units and legends.
- Replay uses recorded decisions and no live API calls. Mock and the historical
  connectivity fixture must not be described as a real multi-agent LLM study.
- Current source: `frontend/src/LLMSociety.jsx`, `frontend/src/studio.css`.

### Don't:
- Don't replace the incumbent mineral console with a new visual identity during ordinary extensions.
- Don't turn research sections into decorative floating cards.
- Don't rescale a response plot vertically when enlarging a parameter interval.

Source audit: `frontend/src/main.jsx` imports `styles.css` followed by `studio.css`; the latter therefore owns its more specific research extensions. `frontend/src/ExplorationLab.jsx` supplies the current response/candidate/heatmap semantics. `PRODUCT.md` establishes reproducibility and measured evidence; `.impeccable/surface.md` establishes the existing atlas direction. This extraction is source-verified; it does not claim browser-computed verification.
