"""Тайлы родного рельефа God of War Ragnarök для полноэкранной карты.

Источник — карта высот самой игры (TX_<мир>_h из root.texpack, см.
tools/gow_game_map.py): по ней отрисован рельеф cache/gow_game_maps/<карта>.png.
Чтобы пины и Кратос не менялись, рельеф кладётся в ту же сетку lat/lng, что и
тайлы MapGenie: data/gow_pins/gow_game_map_georef.json хранит для каждой
родной карты аффинное преобразование «пиксель Web Mercator на зуме 0 →
пиксель текстуры 2048» (получено совмещением с MapGenie,
tools/gow_game_map_register.py).

Витрина отдаёт `/gow-game-tiles/<мир>/<z>/<x>/<y>.png`; у Ванахейма две родные
карты (кратер и южные джунгли) — тайл собирается из обеих. Готовые PNG
кэшируются в cache/gow_game_tiles. MapGenie (`/gow-tiles/`) остаётся запасным.
"""
from __future__ import annotations

import io
import json
import re
import threading
from pathlib import Path

import numpy as np
from PIL import Image

from paths import ROOT, CACHE, DATA

MAPS_DIR = CACHE / "gow_game_maps"
CACHE_DIR = CACHE / "gow_game_tiles"
GEOREF_PATH = DATA / "gow_game_map_georef.json"
TEXTURE_PX = 2048
PATH_RE = re.compile(r"^/gow-game-tiles/([a-z\-]+)/(\d{1,2})/(\d{1,6})/(\d{1,6})\.png$")

_lock = threading.Lock()
_georef_cache: dict | None = None
_images: dict[str, np.ndarray] = {}


def load_georef(path: Path | None = None) -> dict:
    """{карта: {...}} только с принятыми (accepted) привязками."""
    global _georef_cache
    if path is None and _georef_cache is not None:
        return _georef_cache
    p = Path(path or GEOREF_PATH)
    data = json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}
    data = {k: v for k, v in data.items() if v.get("accepted")}
    if path is None:
        _georef_cache = data
    return data


def realms_available(georef: dict | None = None) -> list[str]:
    georef = load_georef() if georef is None else georef
    return sorted({v["realm"] for k, v in georef.items() if (MAPS_DIR / f'{k}.png').is_file()})


def parse_path(path: str, georef: dict | None = None):
    m = PATH_RE.match(path)
    if not m:
        return None
    realm, z, x, y = m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4))
    if realm not in realms_available(georef):
        return None
    if not (0 <= z <= 18 and x < (1 << z) and y < (1 << z)):
        return None
    return realm, z, x, y


def _relief(map_id: str, maps_dir: Path) -> np.ndarray:
    key = str(maps_dir / map_id)
    img = _images.get(key)
    if img is None:
        img = np.asarray(Image.open(maps_dir / f"{map_id}.png").convert("RGBA"))
        _images[key] = img
    return img


def _sample(img: np.ndarray, tx: np.ndarray, ty: np.ndarray) -> np.ndarray:
    """Билинейная выборка RGBA (float32) по координатам текстуры 2048; вне — прозрачно."""
    k = img.shape[1] / TEXTURE_PX
    fx, fy = tx * k - 0.5, ty * k - 0.5
    x0, y0 = np.floor(fx).astype(np.int64), np.floor(fy).astype(np.int64)
    wx, wy = (fx - x0)[..., None], (fy - y0)[..., None]
    h, w = img.shape[:2]
    inside = (fx >= -0.5) & (fy >= -0.5) & (fx <= w - 0.5) & (fy <= h - 0.5)

    def at(yy, xx):
        return img[np.clip(yy, 0, h - 1), np.clip(xx, 0, w - 1)].astype(np.float32)

    out = (at(y0, x0) * (1 - wx) * (1 - wy) + at(y0, x0 + 1) * wx * (1 - wy)
           + at(y0 + 1, x0) * (1 - wx) * wy + at(y0 + 1, x0 + 1) * wx * wy)
    out[~inside] = 0
    return out


def render_tile(realm: str, z: int, x: int, y: int, georef: dict | None = None,
                maps_dir: Path | None = None) -> bytes | None:
    """PNG 256×256 или None, если родная карта тайл не покрывает."""
    georef = load_georef() if georef is None else georef
    maps_dir = Path(maps_dir or MAPS_DIR)
    j, i = np.mgrid[0:256, 0:256].astype(np.float64)
    gx = (x * 256 + i + 0.5) / (1 << z)          # пиксель Web Mercator на зуме 0
    gy = (y * 256 + j + 0.5) / (1 << z)
    acc = np.zeros((256, 256, 4), np.float32)
    for map_id, ref in sorted(georef.items()):
        if ref["realm"] != realm or not (maps_dir / f'{map_id}.png').is_file():
            continue
        G = np.asarray(ref["merc0_to_texture"], dtype=np.float64)
        tx = G[0, 0] * gx + G[0, 1] * gy + G[0, 2]
        ty = G[1, 0] * gx + G[1, 1] * gy + G[1, 2]
        if tx.max() < 0 or ty.max() < 0 or tx.min() > TEXTURE_PX or ty.min() > TEXTURE_PX:
            continue
        layer = _sample(_relief(map_id, maps_dir), tx, ty)
        a = layer[..., 3:4] / 255.0
        acc[..., :3] = layer[..., :3] * a + acc[..., :3] * (1 - a)   # «поверх» — без учёта нижней альфы
        acc[..., 3:4] = 255.0 * (a + acc[..., 3:4] / 255.0 * (1 - a))
    if acc[..., 3].max() < 1:
        return None
    buf = io.BytesIO()
    Image.fromarray(np.clip(acc, 0, 255).round().astype(np.uint8), "RGBA").save(buf, "PNG", compress_level=3)
    return buf.getvalue()


def get_tile(realm: str, z: int, x: int, y: int, cache_dir: Path | None = None,
             georef: dict | None = None, maps_dir: Path | None = None) -> bytes | None:
    cache_dir = Path(cache_dir or CACHE_DIR)
    target = cache_dir / realm / str(z) / str(x) / f"{y}.png"
    miss = target.with_suffix(".none")
    if target.is_file():
        return target.read_bytes()
    if miss.is_file():
        return None
    with _lock:
        data = render_tile(realm, z, x, y, georef=georef, maps_dir=maps_dir)
        target.parent.mkdir(parents=True, exist_ok=True)
        if data is None:
            miss.write_bytes(b"")
            return None
        tmp = target.with_suffix(".tmp")
        tmp.write_bytes(data)
        tmp.replace(target)
        return data
