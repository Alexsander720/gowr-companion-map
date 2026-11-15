"""Repository resources are immutable; generated and personal data live elsewhere."""
from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'data'
USER = Path(os.environ.get('GOWR_DATA_DIR') or
            (Path(os.environ.get('LOCALAPPDATA', Path.home() / '.cache')) / 'gowr-companion-map'))
CACHE = USER / 'cache'
PINS = CACHE / 'pins'
LIVE_REFS = USER / 'live_realm_refs.json'
GAME_DIR: Path | None = None


def atomic_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent,
                                     prefix=path.name, suffix='.tmp', delete=False) as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
        tmp = Path(f.name)
    tmp.replace(path)


def steam_roots():
    roots = []
    if os.name == 'nt':
        import winreg
        for hive, key, value in [(winreg.HKEY_CURRENT_USER, r'Software\Valve\Steam', 'SteamPath'),
                                 (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\WOW6432Node\Valve\Steam', 'InstallPath')]:
            try:
                with winreg.OpenKey(hive, key) as k:
                    roots.append(Path(winreg.QueryValueEx(k, value)[0]))
            except OSError:
                pass
    for variable in ('ProgramFiles(x86)', 'ProgramFiles'):
        if os.environ.get(variable):
            roots.append(Path(os.environ[variable]) / 'Steam')
    return list(dict.fromkeys(roots))


def find_game_dir(game_dir=None):
    """Discover Steam libraries without assuming a drive or account identifier."""
    if game_dir:
        return Path(game_dir).expanduser().resolve()
    if GAME_DIR:
        return GAME_DIR
    import re
    libraries = steam_roots()
    for root in libraries[:]:
        vdf = root / 'steamapps' / 'libraryfolders.vdf'
        try:
            text = vdf.read_text(encoding='utf-8')
        except OSError:
            continue
        libraries.extend(Path(p.replace('\\\\', '\\')) for p in
                         re.findall(r'"path"\s*"([^"\r\n]+)"', text, re.I))
    for root in dict.fromkeys(libraries):
        manifest = root / 'steamapps' / 'appmanifest_2322010.acf'
        try:
            match = re.search(r'"installdir"\s*"([^"\r\n]+)"', manifest.read_text(encoding='utf-8'))
        except OSError:
            continue
        if match:
            candidate = root / 'steamapps' / 'common' / match[1]
            if (candidate / 'GoWR.exe').is_file():
                return candidate
    return None


def wad_dir(game_dir=None):
    game = find_game_dir(game_dir)
    return game / 'exec/wad/pc_le' if game else USER / 'missing-game'


def saved_games_roots():
    roots = [Path.home() / 'Saved Games', Path.home() / 'OneDrive/Saved Games']
    if os.name == 'nt':
        # Windows Known Folder API respects redirected Saved Games folders.
        import ctypes
        import uuid
        guid = (ctypes.c_ubyte * 16).from_buffer_copy(uuid.UUID('4c5c32ff-bb9d-43b0-b5b4-2d72e54eaaa4').bytes_le)
        target = ctypes.c_wchar_p()
        if ctypes.windll.shell32.SHGetKnownFolderPath(ctypes.byref(guid), 0, None, ctypes.byref(target)) == 0:
            roots.insert(0, Path(target.value))
            ctypes.windll.ole32.CoTaskMemFree(target)
    return list(dict.fromkeys(roots))
