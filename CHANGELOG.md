# Changelog

## 0.5.0 — 2026-11-28

- **Native 3D In-Game Diorama Map Engine for All 9 Realms** (`tools/gow_native_map_3d.py`, `web/map_engine.js`, `/api/realm-3d/<realm>/*`):
  - Reverse-engineered read-only extractor reads your local Steam installation (`r_ui.wad` WTOC v2, `root.lodpack`, `root.texpack`) to reconstruct each realm's authentic 3D carved wood-and-stone world map (`midgard`, `svartalfheim`, `vanaheim`, `alfheim`, `asgard`, `helheim`, `jotunheim`, `muspelheim`, `niflheim`) directly into `%LOCALAPPDATA%\gowr-companion-map\cache\gow_native_3d\`:
    - **True 3D Landmark Geometry (`props.bin`, GOWM v1)**: extracts Tyr's Temple, all 8 Realm Towers, World Serpent coils, Nidavellir, dwarven railways and cranes, Vanaheim's Red Tree, Goddess Falls Grotto and Frozen Lightning, Asgard's Great Wall and longhouses, Helheim bridges and docks, Jotunheim's Ironwood landmarks, Muspelheim's Crucible and Surtr's Forge, and Niflheim statues using spatial-cluster rigid grounding (preventing per-vertex cliff/chasm shearing) and per-realm architectural vertical scaling.
    - **Synchronized PBR Atlases (`atlas.png` RGBA + `atlas_n.png`)**: packs diffuse + AO + tangent-space normal + gloss maps with true 8-bit alpha-cutout preservation for BC2/BC3/BC7 foliage/blossoms (while keeping BC1 textures opaque), RGB edge-dilation for zero dark bilinear fringes, and alpha-tested real-time 2048px WebGL2 directional shadow mapping (`SHADOW_FS`).
    - **2K Carved Diorama Surface & Lighting (`surface.png`, `terrain_n.png`, `water_mask.png`)**: combines full-precision BC6H heightmaps, 36-step raymarched directional cliff self-shadows, carved wood-chisel / stone-slab / frost / paint materials, radial-feathered `DCL_*` painted brushstrokes and realm-tinted carved tree decals, selective cliff-edge anti-aliasing on 1024×1024 `h16` heightmaps, animated `TX_flowmap_02` water/ice/molten-lava shaders, volumetric drifting mist clouds, and linear PBR + ACES filmic tone mapping.
    - **In-Game Map Marker Icons (`/api/map-icon/<key>.png`)** and **1-Click Native 3D / MapGenie Source Toggle** (`#gowFsSource`) with graceful fallback when game files are absent (or in Sindri's House).
- **Tablet, Phone & Desktop Reliability + Fullscreen Mode** (`gow_game_tiles.py`, `web/map_engine.js`, `web/companion_gow_map.js`, `web/companion_gow_map.css`):
  - **Fullscreen button** (`#gowFsFullscreen`) in the top bar (works on desktop browsers and Android tablets/phones).
  - **Automatic WebP (`exact=True` for RGBA) + HTTP gzip delivery**: shrinks per-realm native 3D payloads from ~21.6 MB PNG to ~4.6 MB WebP (~4.7× faster Wi-Fi/LAN loading on tablets and phones).
  - **Mobile/Tablet WebGL2 hardening**: lazy `tileAtlas` allocation (-67 MB VRAM when using Native 3D), mobile `precision highp sampler2D`, NaN-safe `pow`/`normalize` guards, 5× asset retry with truncation recovery, heightmap `?v=<rev>` cache-busting, auto-scrolling active realm tab in the top bar, compact right-toolbar layout for short landscape screens, and seamless PC Alt-Tab / DX12 `webglcontextlost` → `webglcontextrestored` recovery without falling back to a blank map.
  - Added `imagecodecs>=2024.1` to `requirements.txt` and `tools/bootstrap.py` so `start.bat` unlocks BC6H heightmaps and Native 3D dioramas automatically on first launch.

## 0.4.0 — 2026-11-27

- **Authentic In-Game Open Book Codex & Treasures** (`gow_codex.py`, `/api/codex`, `/api/codex/icon/<key>.png?ink=dark|gold`, `/api/codex/book/<asset>.png`):
  - Reads all 198 Bestiary entries (main game + Valhalla DLC toggle, 9 official categories, individual combat tips unlock status, enemy family kill counters), ~209 Lore entries (6 subcategories with Valhalla separation and story updates), **all 10 Treasure Maps** (`TreasureMap_*_Parent` with 3-state save progression: unfound / map found / dug up, official riddles, sepia clue illustrations, and exact pairing to both map-scroll and buried-treasure pins), all 49 weapon Skill Labors with official localized EN/RU names (`quests_main.dcb` pointer chain + Bronze/Silver/Gold tiers), general Labors with a **"Closest to next rank"** highlight strip, and Hero loadout (with dynamic EN gear localization via shared game string IDs), amulet sockets, currencies, XP, proven Nine Realms completion breakdown, and searchable crafting materials directly from your local game installation and read-only saves.
  - **Open Book Reader Mode** (default, with 1-click **Book / Dark view** toggle): renders Bestiary, Lore, and Treasures as an authentic open stitched leather-and-parchment journal spread matching the game UI — vertical section icon strip, frosted category rail with silver highlight, mirrored parchment pages with 4 stitched spine straps, torn charcoal ink headers & active brushstroke highlight, subtle page watermarks, diamond-bulleted combat tips, and a fold-out torn parchment flap displaying dark-ink creature/character sketches (`?ink=dark`, `mix-blend-mode: multiply`, clickable to zoom) or sepia Treasure Map clue paintings. All extracted textures and portraits live strictly in `%LOCALAPPDATA%\gowr-companion-map\cache\codex_icons\` with clean procedural CSS fallbacks when no game files are present.
- **Upgraded 3D Terrain Quality, Weather & Pulsing Icons** (`web/map_engine.js`, `tools/gow_game_map.py`, `web/companion_gow_map.css`): crisp Nordic daylight lighting and micro-contrast across all realms, sharper perspective tile LOD (`ceil(zoom + 0.35)`), dynamic heightmap normal step, animated valley mist wisps, GPU WebGL2 3D weather particles (falling snow in Midgard/Helheim/Niflheim, rising volcanic embers in Muspelheim/Svartalfheim, golden motes in other realms; toggleable via `#gowFsWeather`), automatic WebGL pause while reading the Codex, and pulsing map target/gateway/Kratos icons (respecting `prefers-reduced-motion`).
- **Universal 3D Routing & Live SSE Updates** (`/api/stream`, `web/companion_gow_map.js`):
  - **Plot 3D route** works reliably to **any target** — Buried Treasure, Treasure Map scroll, Favor objective/guide point, Boss from Bestiary/Lore, or any completion/resource pin — from **live Kratos** (updating live as Kratos walks) or automatically from the **nearest unlocked Mystic Gateway** in that realm (`Gateway: <name> · N m`), automatically switching realms, re-projecting camera bounds, and unhiding filtered pins when needed. Every pin drawer includes a 1-click **Plot 3D route** button, plus Treasure clue art and scroll/dig jump buttons on treasure pins.
  - **3D Clearing Route (`M` hotkey / `#gowFsRoute`)** chains up to 5 nearest uncollected completion pins with a terrain-following golden ribbon, numbered stop badges (`1`–`5`), and auto-rebuilding; Kratos's live movement trail renders as a tapered 3D terrain-draped ribbon.
  - Server-Sent Events stream pushes live Kratos telemetry and instant `save_updated` / `codex_delta` notifications for Bestiary, combat tips, Lore, Treasures, and skills (with `NEW` badges, session **New** filter, and golden toasts) plus **Screen Wake Lock** for tablets/phones.
- Offline synthetic test coverage for Codex & Treasure parsing, `*TEMP*` filtering, diff notifications, book/dark-ink cache & traversal guards, SSE streaming, weather toggle, Open Book UI, and cross-realm 3D routing across desktop, tablet, and phone viewports.

## 0.3.0 — 2026-11-27

- Pure local WebGL2 3D terrain renderer (`web/map_engine.js`) with drop-in `window.L` compatibility, anisotropic filtering (`EXT_texture_filter_anisotropic`), cavity AO, valley mist, water fresnel highlights, carved topographic base fallback when tiles are absent, depth-scaled pins with `.gow-fs-tip` hover tooltips, and automatic 2D DOM fallback if WebGL2 context is unavailable or lost.
- 16-bit precision heightmap pipeline (`tools/gow_game_map.py --h16-only`, `encode_h16_png`, `/api/realm-height/<realm>`) decoding game BC6H `.texpack` elevation maps via `imagecodecs` across all 9 navigable realms (`midgard`, `svartalfheim`, `alfheim`, `vanaheim` with seamless Crater/Jungle elevation transition, `jotunheim`, `asgard`, `helheim`, `niflheim`, `muspelheim`), plus calibrated Web Mercator georef bounds in `data/gow_game_map_georef.json` and procedural micro-relief fallback when local game heightmaps are absent (e.g. Sindri's House or no local game installation).
- Zero-drift Google Maps multitouch gestures (1-finger ground-anchored pan, right-drag / Ctrl+drag / Shift+drag / touchpad pinch / 2-finger pinch-zoom and yaw twist with deadzone, 2-finger vertical drag pitch tilt) plus desktop and gamepad controls (`3D` toggle `T`, rotate `[` / `]`, `+`/`-` zoom, clickable compass `N`, right-stick orbit & bumper zoom).
- **Nearest** collectible navigator (`N`), auto-advancing after manual or save completion, paired with an animated additive 3D golden beacon shaft, pulsing ground rune rings, clickable live-updating distance/compass HUD pill (`#gowFsBeaconPill`), quick search clear (`×`), and live Kratos 3D movement trail toggle.
- Mobile PWA support (`/manifest.webmanifest`, `/icon.svg`, `/icon-192.png`, `/icon-512.png`, viewport/apple-mobile meta tags), HTTP `gzip` response compression in `server.py`, and responsive topbar layout fixes across tablet and phone viewports.

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
