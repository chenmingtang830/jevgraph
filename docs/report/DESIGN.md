---
name: JevGraph Field Report
description: A three-screen evidence brief for the graph pipeline and its benchmarks.
colors:
  paper: "#ffffff"
  warm-paper: "#f7f6f2"
  ink: "#171a20"
  secondary-ink: "#4f5662"
  metadata-ink: "#69717c"
  rule: "#d6dbd8"
  track: "#e2e5e3"
  evidence-teal: "#0e6675"
  signal-teal: "#2e8fa3"
  teal-field: "#edf6f6"
typography:
  display:
    fontFamily: "DM Sans, Avenir Next, ui-sans-serif, sans-serif"
    fontSize: "clamp(3.6rem, 5.4vw, 5.4rem)"
    fontWeight: 600
    lineHeight: 0.95
    letterSpacing: "-0.04em"
  body:
    fontFamily: "DM Sans, Avenir Next, ui-sans-serif, sans-serif"
    fontSize: "18px"
    lineHeight: 1.45
  evidence-label:
    fontFamily: "IBM Plex Mono, SFMono-Regular, Consolas, monospace"
    fontSize: "10px"
    fontWeight: 600
    letterSpacing: "0.06em"
spacing:
  page-x: "42px"
  page-y: "28px"
  panel: "20px"
components:
  page-navigation-active:
    backgroundColor: "{colors.evidence-teal}"
    textColor: "{colors.paper}"
    width: "38px"
    height: "38px"
---

# Design System: JevGraph Field Report

## Overview

**Creative North Star: "Boardroom Clarity"**

The report is an institutional evidence artifact: bright paper, strong black rules, one restrained
teal signal, and enough warm-paper contrast to group measurements without turning them into cards.
It is designed to be read from a small presentation screen, so each page keeps one thesis and makes
the charts and numerals do most of the work.

**Key Characteristics:**

- three full-height screens that print as three A4 landscape pages;
- large declarative headings with compact evidence metadata;
- aligned horizontal bars with explicit zero axes; and
- no decorative imagery or remote runtime dependency.

## Colors

White and warm paper carry the report; near-black establishes hierarchy; teal appears only where a
reader should look first.

**The One Signal Rule.** Teal marks the principal mechanism or Jev series. Comparator data stays
neutral gray so accent never becomes decoration.

## Typography

**Display Font:** DM Sans with Avenir Next and UI sans fallbacks

**Body Font:** DM Sans with Avenir Next and UI sans fallbacks

**Label/Mono Font:** IBM Plex Mono with SFMono and Consolas fallbacks

Display headings use weight 600, a 0.95–0.98 line height, and no tighter than `-0.04em`. Body copy is
kept brief at 1.45 line height. Mono is reserved for versions, measured values, task settings, and
source metadata.

## Layout

Each `.page` fills one viewport with a minimum height of 720px and uses a 42px × 28px desktop inset.
At 1000px and below, the inset contracts to 28px × 22px while all three pages remain one-screen
compositions. Page one uses a three-stage process band; pages two and three use two- and three-column
chart grids. The fixed numbered rail provides direct and keyboard-assisted page movement.

## Elevation & Depth

The system is flat. Hierarchy comes from paper tone, 1px rules, scale, and spacing; there are no
shadows.

## Shapes

Containers and controls are square. The only circle is the small signal dot attached to the
JevGraph mark. Bars begin at a visible 1px zero axis.

## Components

### Evidence panels

Warm-paper panels use a 1px rule, 17–21px internal padding, large task titles, and aligned bar groups.

### Horizontal bars

Every comparison row has a fixed label column, flexible track, and tabular value column. Jev uses
evidence teal; comparators use neutral gray. Scales are local to each metric and never share units.

### Navigation

Three square numbered buttons sit at the right edge. The active page is teal with white type; hover
and keyboard focus use the same signal color.

## Do's and Don'ts

### Do:

- **Do** keep DocJev, the configured E2E smoke fixture, and FewRel visibly separate.
- **Do** keep accuracy beside latency and cost whenever an operational advantage is claimed.
- **Do** label Jev cost `illustrative` and chat-model costs `receipt`.
- **Do** fit each page into the 810×771 presentation viewport as well as landscape print.

### Don't:

- **Don't** imply that candidate decisions are graph truth or Human Approval.
- **Don't** generalize the repository-owned smoke fixture into an external quality claim.
- **Don't** add remote fonts, APIs, or runtime dependencies to the self-contained report.
