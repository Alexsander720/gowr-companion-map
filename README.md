# God of War Ragnarök — Companion Map

[Русский](README.ru.md) · Version 0.1.0

A fullscreen second-screen map for the Steam PC version of **God of War Ragnarök**. Browse the nine realms and Sindri's House, inspect locations, follow favor objectives, and see Kratos move when a supported game build and a calibrated projection are available.

![The standalone companion at 1920 × 1080](docs/screenshot.png)

The screenshot shows this application using locally downloaded map data. No save or game screenshot is bundled. Map artwork shown in the application is provided by MapGenie and the game's rights holders.

## Requirements

- Windows 10 or 11, 64-bit Python 3.11 or newer, with the Python launcher or `python` on PATH.
- The Steam PC version of God of War Ragnarök for save progress, live position and game localization. Browsing the map also works while the game is closed.
- Internet access for Python packages on setup and for MapGenie pins and map tiles. There is no account, API key or paid service requirement.
- A modern browser, including a phone browser for LAN use.

The bundled `KNOWN_BUILDS` live-pointer profile was validated in the original implementation for **GoWR.exe size 46,685,144 bytes, PE timestamp 1,750,707,527 (`0x6859AD47`)**. The PE timestamp is a build identifier, not a release date. The profile also checks loaded module headers. It does not certify other patches. A fresh-machine live-game run has not been performed for this release.

## Start

1. Download the source ZIP and extract it, or clone the repository.
2. Double-click **`start.bat`**. It creates `.venv`, installs `requirements.txt`, downloads public map data into your user folder, and opens the browser.
3. The default address is **http://127.0.0.1:8790/**. Leave the terminal open while using the map. Press Ctrl+C to stop the server.

Steam libraries are discovered through the Steam registry entry, `libraryfolders.vdf` and the game's app manifest. If discovery fails, run from a terminal in this folder:

```bat
start.bat --game-dir "<your game installation folder>"
```

Saves are discovered in the current Windows user's Saved Games location, including redirected folders, across account subfolders. They are opened only for reading. You can select a save folder explicitly with `--save-dir "<your save folder>"`.

The browser's language chooses RU or EN initially. **RU / EN** switches the interface and persists in `localStorage`. Russian pin and region names are extracted from your installed `r_lang_en.wad` and `r_lang_ru.wad` using shared string IDs. Without those files, pin names fall back to English. Descriptions remain in their original English, and links to other locations open pins inside this map.

## Phone or second screen

```bat
start.bat --lan
```

Open the LAN address printed in the terminal on a device connected to the same local network. Allow Python through Windows Firewall on your private network if prompted. The default run listens only on loopback; `--lan` listens on all local interfaces. The LAN server has no authentication: use a trusted home network and do not expose its port to the internet. The API returns map progress and journal information to connected devices, but does not return save paths or account folders.

Additional options:

```bat
start.bat --port 8791
start.bat --offline
start.bat --no-browser
start.bat --lang ru
```

`--lang` selects terminal messages; the browser selects the interface language separately. `--offline` uses cached pins and tiles without network requests. A map region whose tiles have not been cached will have an empty background.

## Use the map

- **Left to clear** shows remaining and unknown completion pins. **All completion pins** includes completed sites. **+ Resource chests** also includes untracked loot.
- **Favors** shows active journal favors and their known remaining sites across realms. Counters appear only when the save contains a recognized value. An unknown objective location stays unknown.
- Use realm tabs, category filters, region selection, search, zoom, dragging and the pin panel. Phones support dragging and pinch zoom. The summary starts collapsed on small screens.
- **C** centers on Kratos; follow mode tracks his position. **R** fits the realm, **U** changes the completion filter, **Tab** toggles the summary, and **1–0** select realms. Keyboard and gamepad navigation are supported.
- Manual marks are kept in this browser's `localStorage`; they do not alter saves or favor journal state. A different phone or browser has its own manual marks.
- **Codex** displays available save details. Save progress updates after the game writes an autosave. It is not a live inventory feed.

## Data, cache and privacy

All downloaded pins, tiles, extracted localization, optional relief and calibration output stay under **`%LOCALAPPDATA%\gowr-companion-map\`**. Set `GOWR_DATA_DIR` before starting to choose another writable folder, such as `./cache/user`. Runtime files are excluded by `.gitignore`; avoid putting a custom data directory inside tracked source folders.

The repository contains application code, our numeric pin/save joins, measured calibration references and matrices. It does **not** contain MapGenie JSON dumps or translated descriptions, game language dumps, extracted game textures, saves, personal account identifiers or a tile cache. The UI's raster map renderer is local application code, so it needs no third party browser CDN. Python dependencies are installed normally and keep their own licenses.

The MapGenie loader performs one public data request per uncached realm, uses a neutral User-Agent and caches the result. The current website loads pins through `/api/v1/maps/<id>/data`; its HTML no longer embeds the full location list. The loader also includes a parser for older embedded `window.mapData` JSON. Upstream data can change independently of this release. New locations without a known save join remain unknown.

If downloads fail or the service returns a challenge, the map starts without those pins. There is no CAPTCHA solver, login automation or protection bypass. Failures are remembered to avoid repeated requests. After checking connectivity, retry failed realms with:

```bat
.venv\Scripts\python.exe tools\fetch_mapgenie.py --retry
```

Cached successful maps stay cached. Map tiles are fetched as viewed and cached; unavailable tile responses are cached too. Original pin descriptions are not translated. The application does not fetch pin photographs or copy screenshots from the game.

## Live position and game patches

The process is opened with **`PROCESS_VM_READ | PROCESS_QUERY_INFORMATION` (`0x0410`)**. The application does not write game memory, saves or installation files. Unknown or unverifiable executable builds hide the live marker and display a version status; browsing pins and reading saves continue to work. A valid coordinate outside a supported projection also hides the marker. Approximate projections are visibly labelled.

The arrow follows the validated position chain; its cone uses the camera heading. Some realms and inset areas lack calibration, and a single world coordinate system does not necessarily describe every place drawn on a map. Individual draugr holes and seasonal stags cannot always be distinguished in saves. Favor membership alone is not proof that a particular site is complete.

After a patch, first check for an updated companion profile. Advanced users can build a new candidate inventory and run the included **read-only** behavioral probe:

```bat
.venv\Scripts\python.exe tools\analyze_gowr_binary.py --exe "<game folder>\GoWR.exe"
.venv\Scripts\python.exe tools\gow_live_pointer_probe.py
```

The probe asks for still, move and camera-turn samples. Results go to the user folder's `probe` subfolder. Use `--help` for separate snapshots, comparisons, `--confirm-position` and `--confirm-yaw`. Candidate rankings are hypotheses; identify Kratos independently and review the result before using the emitted configuration to update `KNOWN_BUILDS` in `gow_memory.py`. No candidate is automatically enabled and no profile is automatically uploaded. Do not publish personal snapshots or binary inventories.

## Optional native relief and automatic calibration

These features are disabled on a normal launch. Install optional packages in the same environment:

```bat
.venv\Scripts\python.exe -m pip install -r requirements-optional.txt
```

Generate relief from your own installation (only accepted geographic alignments are exposed in the UI):

```bat
.venv\Scripts\python.exe tools\gow_game_map.py midgard --size 2048
```

Add `--game-dir "<game folder>"` if needed. Restart the server after extraction; the relief toggle appears only for available files with accepted alignment. Midgard is the accepted alignment in 0.1.0. The optional `imagecodecs` dependency decodes full-precision BC6H heightmaps; no third party decoder source or game texture is bundled here.

Before the first use, open the in-game map and run the one-time template setup:

```bat
.venv\Scripts\python.exe tools\gow_auto_calibrate.py --learn-templates
```

Switch to the game within five seconds. In the two selection windows, select the highlighted **MAP** tab and then a square around the circular Kratos icon; press Enter to confirm each crop. Only these two crops are saved in your user cache. They belong to your game installation and must not be committed or redistributed. Repeat setup if the game's UI language or appearance changes. Without these private templates the collector stays off and prints a setup message.

Then enable screen-based calibration explicitly:

```bat
start.bat --autocalib
```

Open the game's map while standing still. The collector reads the foreground game window, matches the map to cached/downloaded tiles, and stores accepted reference points in your user folder's `live_realm_refs.json`. It preserves the repository's baseline references and never edits the repository calibration file. Screen capture is used only by `--autocalib` or the explicitly invoked `--learn-templates` setup. Automatic calibration has synthetic coverage; a fresh-machine live-game run remains unverified.

## Development and verification

```bat
python -m pip install -r requirements-dev.txt
python -m pytest -q
python tools\check_clean.py
```

Tests use synthetic map records, generated save bytes and our calibration matrices, with external requests disabled. They never require or inspect a real game or save. Chromium rendering runs when Playwright and its browser are installed; otherwise it is explicitly skipped. Install the optional test browser with `python -m playwright install chromium`.

`check_clean.py` scans **every tracked git file**, including documentation, for private signatures, absolute Windows paths, account identifiers, credential patterns and prohibited data. Stage intended release files before running it. A clean scanner is a publishing check, not a replacement for review of data provenance.

## Disclaimer and license

An unofficial fan project, not affiliated with or endorsed by **Sony Interactive Entertainment, Santa Monica Studio or MapGenie**. God of War Ragnarök and associated artwork and names belong to their respective rights holders. Game memory is only read; nothing is written into the game.

Map data is downloaded from [MapGenie](https://mapgenie.io/god-of-war-ragnarok) on your own computer and remains subject to MapGenie's terms. No license to republish downloaded or extracted material is granted by this repository. Use the application and any optional memory tools at your own discretion.

The companion's code and our accompanying mapping data are provided under the [MIT License](LICENSE). That license does not cover third party map data, game files, artwork visible in the application screenshot or installed Python dependencies.
