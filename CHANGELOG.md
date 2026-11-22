# Changelog

## 0.2.0 — 2026-11-22

- Bundled RU/EN guides: all 35 Nornir chests, 52 hard-to-reach collectibles (Odin's Ravens, seasonal stags, Hel-Tears, Remnants of Asgard, artifacts, rifts, Yggdrasil's Dew and Jewels, Kvasir's Poems, Draugr Holes) and 47 favors with 77 "where to go" points; each checked against at least two public walkthroughs.
- Optional RU/EN guides from `data/guides.json`, with language fallback and mtime refresh.
- How to solve blocks in pin cards, collapsible sources, and favor walkthroughs in the panel.
- Distinct favor targets using pin anchors, current objective links, and cross-realm point navigation.
- Dismissible hints near live Kratos for confirmed uncollected guided pins and active favor points, once per site per tab session.
- Offline synthetic guide/API and Chromium regression coverage; authored guides allowed by the publication scanner.

## 0.1.1 — 2026-11-15

- Russian translation now covers every pin with a description on MapGenie as of November 2026 (1171 pins).
- Russian names for generic pins (Wood Chest, Red Coffin, Odin's Raven, Beyond Ragnarök encounters…) via `data/ru_titles.json`.

## 0.1.0 — 2026-11-15

- Standalone fullscreen map for the Steam PC version of God of War Ragnarök.
- Nine realms and Sindri's House, completion filters, search and pin descriptions.
- Optional Russian translation of pin descriptions with an Original / Translation switch in the pin card.
- Read-only save progress and favor journal with explicit unknown states.
- Read-only live position with executable fingerprint checks and calibrated projections.
- English and Russian UI with browser language detection and persistent selection.
- First-run public MapGenie downloads, user-local caches and game-local localization extraction.
- Optional native relief and opt-in screen calibration; advanced pointer diagnostics.
- Offline synthetic tests, Chromium UI checks and tracked-file publication scanner.
