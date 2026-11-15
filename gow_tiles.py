"""Тайлы карты God of War Ragnarök для полноэкранной карты второго экрана.

Тайлы MapGenie лежат на сплошной подложке своего цвета для каждого мира: у
Ванахейма она светло-серая, у Мидгарда ледяная. На тёмном HUD-экране такая
подложка читалась бледным прямоугольником. Вырезать её в браузере нельзя:
CDN кэширует Access-Control-Allow-Origin без учёта источника (то mapgenie.io,
то ign.com), и canvas с такими тайлами браузер блокирует.

Поэтому витрина отдаёт тайлы сама (`/gow-tiles/<мир>/<z>/<x>/<y>.png`):
один раз скачивает JPEG, вырезает цвет подложки в прозрачность с мягким краем
и снимает примесь подложки с полупрозрачной кромки. Готовый PNG кэшируется
на диске (cache/gow_tiles), поэтому уже посещённые места открываются и без сети.
"""
from __future__ import annotations

import io
import re
import threading
import urllib.error
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image

from paths import ROOT, CACHE, DATA

CACHE_DIR = CACHE / "gow_tiles"
UPSTREAM = "https://tiles.mapgenie.io/games/god-of-war-ragnarok/{realm}/default-v1/{z}/{x}/{y}.jpg"

# Цвет подложки каждого мира: сняты с внешних тайлов z=9 (13.11.2026).
TILE_BG = {
    "midgard": (172, 198, 213),
    "vanaheim": (160, 174, 177),
    "svartalfheim": (130, 148, 162),
    "alfheim": (67, 106, 137),
    "jotunheim": (147, 143, 116),
    "asgard": (173, 183, 182),
    "helheim": (41, 93, 80),
    "niflheim": (174, 185, 230),
    "muspelheim": (0, 0, 0),
    "sindris-house": (28, 66, 103),
}
KEY_NEAR = 7.0   # ближе этого к подложке — полностью прозрачно
KEY_FAR = 42.0   # дальше — пиксель карты без изменений

PATH_RE = re.compile(r"^/gow-tiles/([a-z\-]+)/(\d{1,2})/(\d{1,6})/(\d{1,6})\.png$")
_MISSING = object()
_locks: dict[str, threading.Lock] = {}
_locks_guard = threading.Lock()


def parse_path(path: str):
    """`/gow-tiles/vanaheim/11/1020/1019.png` → ('vanaheim', 11, 1020, 1019) или None."""
    m = PATH_RE.match(path)
    if not m or m.group(1) not in TILE_BG:
        return None
    realm, z, x, y = m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4))
    if not (0 <= z <= 18 and x < (1 << z) and y < (1 << z)):
        return None
    return realm, z, x, y


def key_out(rgb: np.ndarray, bg: tuple[int, int, int]) -> np.ndarray:
    """RGB (H×W×3, uint8) → RGBA: подложка прозрачна, кромка без серой каймы."""
    px = rgb.astype(np.float32)
    bgv = np.array(bg, dtype=np.float32)
    diff = px - bgv
    dist = np.sqrt((diff * diff).sum(axis=2))
    t = np.clip((dist - KEY_NEAR) / (KEY_FAR - KEY_NEAR), 0.0, 1.0)
    alpha = t * t * (3.0 - 2.0 * t)
    k = 1.0 / np.maximum(alpha, 0.3)
    edge = (alpha > 0) & (alpha < 1)
    out = px.copy()
    out[edge] = np.clip(bgv + diff[edge] * k[edge][:, None], 0, 255)
    rgba = np.dstack([out, alpha * 255.0]).round().astype(np.uint8)
    return rgba


def _lock_for(key: str) -> threading.Lock:
    with _locks_guard:
        return _locks.setdefault(key, threading.Lock())


def _fetch_upstream(realm: str, z: int, x: int, y: int, timeout: float = 8.0):
    req = urllib.request.Request(UPSTREAM.format(realm=realm, z=z, x=x, y=y),
                                 headers={"User-Agent": "gowr-companion-map/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except urllib.error.HTTPError as exc:
        if exc.code in (403, 404):
            return _MISSING     # за краем карты тайла нет
        raise


def get_tile(realm: str, z: int, x: int, y: int, cache_dir: Path | None = None,
             fetch=_fetch_upstream) -> bytes | None:
    """PNG тайла с вырезанной подложкой; None — тайла за краем карты нет."""
    cache_dir = Path(cache_dir or CACHE_DIR)
    target = cache_dir / realm / str(z) / str(x) / f"{y}.png"
    miss_mark = target.with_suffix(".none")
    if target.is_file():
        return target.read_bytes()
    if miss_mark.is_file():
        return None
    with _lock_for(str(target)):
        if target.is_file():
            return target.read_bytes()
        raw = fetch(realm, z, x, y)
        target.parent.mkdir(parents=True, exist_ok=True)
        if raw is _MISSING or not raw:
            miss_mark.write_bytes(b"")
            return None
        rgb = np.asarray(Image.open(io.BytesIO(raw)).convert("RGB"))
        buf = io.BytesIO()
        Image.fromarray(key_out(rgb, TILE_BG[realm]), "RGBA").save(buf, "PNG", optimize=False, compress_level=3)
        data = buf.getvalue()
        tmp = target.with_suffix(".tmp")
        tmp.write_bytes(data)
        tmp.replace(target)
        return data
