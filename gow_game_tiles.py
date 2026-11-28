r"""Тайлы и 3D-карты высот родного рельефа God of War Ragnarök для полноэкранной карты.

Источник — карта высот самой игры (TX_<мир>_h из root.texpack, см.
tools/gow_game_map.py): по ней отрисованы 2D-рельеф `<карта>.png` и компактные
16-bit RG-карты высот `<мир>_h16.png` (512×512) в %LOCALAPPDATA%\gowr-companion-map\cache\gow_game_maps\.
Чтобы пины и Кратос не менялись, рельеф кладётся в ту же сетку lat/lng, что и
тайлы MapGenie: data/gow_game_map_georef.json хранит для каждой родной карты
аффинное преобразование «пиксель Web Mercator на зуме 0 → пиксель текстуры 2048».

Витрина отдаёт `/gow-game-tiles/<мир>/<z>/<x>/<y>.png`, `/api/realm-height/<мир>`
и `/api/realm-height/<мир>/meta.json`. MapGenie (`/gow-tiles/`) остаётся запасным.
"""
from __future__ import annotations

import io
import json
import re
import threading
from pathlib import Path

import numpy as np
from PIL import Image

import paths
from paths import CACHE, DATA

MAPS_DIR = CACHE / "gow_game_maps"
CACHE_DIR = CACHE / "gow_game_tiles"
MAP_ASSETS_DIR = CACHE / "map_assets"
NATIVE_3D_DIR = CACHE / "gow_native_3d"
NATIVE_3D_FILES = {
    'props.bin': 'application/octet-stream',
    'atlas.png': 'image/png',
    'atlas_n.png': 'image/png',
    'surface.png': 'image/png',
    'terrain_n.png': 'image/png',
    'water_mask.png': 'image/png',
}
GEOREF_PATH = DATA / "gow_game_map_georef.json"
TEXTURE_PX = 2048
PATH_RE = re.compile(r"^/gow-game-tiles/([a-z\-]+)/(\d{1,2})/(\d{1,6})/(\d{1,6})\.png$")

MAP_DETAIL_ASSETS = {
    'micronoise_n': 'TX_micronoise_n_4818F59B632C9037',
    'micronoise': 'TX_micronoise_6A731A101C6A7F22',
    'ice_cracks': 'TX_ice_cracked_2_a_A93B35E194B08ACF',
    'smokewispy': 'TX_smokewispy_698DD14AE79E9B59',
    'flowmap': 'TX_flowmap_02_AD6BA48AAF09DE13',
    'fog_cloud': 'TX_fog_cloud_04.00_B235DE754B2D2620',
    'clouds_n': 'TX_m_clouds_B25CB8086CBE9614',
    'wood_cell_n': 'TX_wood_cell_n_1F159CE7CAFFC9C2',
}

MAP_ICON_ASSETS = {
    'mystic_gateway': ('TX_mapicon_fasttravel_e_CD361D0A12714194', None),
    'mystic_gateway_unvisited': ('TX_mapicon_fasttravel_gray_e_6B68E42E9F13179E', None),
    'shop': ('TX_mapicon_vendor_e_E88C02E60B2C95FE', 'TX_mapicon_vendor_m_62DAB1E2F8947D36'),
    'favor': ('TX_mapicon_sidequest_e_4D5C7F0ACF2D085D', 'TX_mapicon_quest_m_CE15A8CB56099E91'),
    'main_quest': ('TX_mapicon_mainquest_e_2C801F517057D839', 'TX_mapicon_quest_m_CE15A8CB56099E91'),
    'yggdrasil_rift': ('TX_mapicon_spawnportal_3CA2AD4070647847', None),
    'hel_tear': ('TX_mapicon_spawnportal_3CA2AD4070647847', None),
    'berserker_gravestone': ('TX_mapicon_warriorsoul_color_BAF28C9DEB10B727', None),
    'remnant_of_asgard': ('TX_mapicon_asgardchunk_color_03F25F0893B204CB', None),
    'remnants_of_asgard': ('TX_mapicon_asgardchunk_color_03F25F0893B204CB', None),
    'boss': ('TX_mapicon_valkyrie_color_E8CC638E5E5CEAF8', None),
    'boat_dock': ('TX_mapicon_dock_e_AC9D633E3D0C9DB6', 'TX_mapicon_dock_m_4CA7A9E37195D696'),
    'entrance': ('TX_mapicon_areaentrance_e_93369355784F8411', 'TX_mapicon_areaentrance_m_FC2EC4D7C911B8B3'),
    'muspelheim_trial': ('TX_mapicon_challengearena_CEFEB69F39A7AAAC', None),
    'celestial_altar': ('TX_mapicon_daynightswitch_e_EC0A6040A9593B1E', 'TX_mapicon_shape_circle_m_3D87FD4C8F9142EA'),
    'kol_raider_camp': ('TX_mapicon_fight_e_0D628BC593402DF3', 'TX_mapicon_shape_diamond_m_9D93118DE1490BA2'),
    'draugr_hole': ('TX_mapicon_fight_e_0D628BC593402DF3', 'TX_mapicon_shape_diamond_m_9D93118DE1490BA2'),
    'seasonal_stag': ('TX_mapicon_stag_e_420FCF3A103EDF93', 'TX_mapicon_shape_circle_m_3D87FD4C8F9142EA'),
    'wishing_well': ('TX_mapicon_wishingwell_e_884B1F277756C56D', 'TX_mapicon_shape_circle_m_3D87FD4C8F9142EA'),
}

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


def realms_available(georef: dict | None = None, maps_dir: Path | None = None) -> list[str]:
    georef = load_georef() if georef is None else georef
    base = Path(maps_dir) if maps_dir is not None else MAPS_DIR
    return sorted({v["realm"] for k, v in georef.items() if (base / f'{k}.png').is_file()})


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


def get_realm_height_png(realm: str, maps_dir: Path | None = None, allow_extract: bool = True) -> bytes | None:
    """Return 512x512 RG16 heightmap PNG bytes for a realm, extracting from game files if available."""
    base = Path(maps_dir) if maps_dir is not None else MAPS_DIR
    target = base / f"{realm}_h16.png"
    if target.is_file():
        return target.read_bytes()
    if not allow_extract or maps_dir is not None or not paths.find_game_dir():
        return None
    with _lock:
        if target.is_file():
            return target.read_bytes()
        try:
            from tools.gow_game_map import build_realm_h16
            built = build_realm_h16(realm, out_dir=base, georef=load_georef())
            if built and built.is_file():
                return built.read_bytes()
        except (ImportError, OSError, ValueError, RuntimeError, SystemExit):
            return None
    return None


def get_realm_height_meta(realm: str, maps_dir: Path | None = None) -> dict | None:
    """Return Web Mercator bounds, relief height scale, and lighting palette for a realm."""
    from tools.gow_game_map import realm_height_meta
    base = Path(maps_dir) if maps_dir is not None else MAPS_DIR
    return realm_height_meta(realm, maps_dir=base)


def get_map_detail_png(name: str, cache_dir: Path | None = None) -> bytes | None:
    """Return cached 512x512 in-game PBR micro-detail texture PNG from local root.texpack."""
    tx_name = MAP_DETAIL_ASSETS.get(name)
    if not tx_name:
        return None
    out_dir = Path(cache_dir) if cache_dir is not None else MAP_ASSETS_DIR
    target = out_dir / f'detail_{name}.png'
    if target.is_file():
        cached = target.read_bytes()
        if cached.startswith(b'\x89PNG\r\n\x1a\n') and len(cached) > 32:
            return cached
    if not paths.find_game_dir():
        return None
    with _lock:
        if target.is_file():
            cached = target.read_bytes()
            if cached.startswith(b'\x89PNG\r\n\x1a\n') and len(cached) > 32:
                return cached
        try:
            from tools import gow_texpack
            res = gow_texpack.extract([tx_name]).get(tx_name)
            if not res:
                return None
            _, arr = res
            if name in ('micronoise_n', 'clouds_n') and arr.ndim == 3:
                nx = arr[..., 0].astype(np.float32) / 127.5 - 1.0
                ny = arr[..., 1].astype(np.float32) / 127.5 - 1.0
                nz = np.sqrt(np.clip(1.0 - nx * nx - ny * ny, 0.0, 1.0))
                rgb = np.empty((arr.shape[0], arr.shape[1], 3), dtype=np.uint8)
                rgb[..., 0] = arr[..., 0]
                rgb[..., 1] = arr[..., 1]
                rgb[..., 2] = np.clip((nz * 0.5 + 0.5) * 255.0, 0, 255).astype(np.uint8)
                img = Image.fromarray(rgb, 'RGB')
            elif arr.ndim == 2:
                img = Image.fromarray(arr.astype(np.uint8), 'L')
            else:
                img = Image.fromarray(arr[..., :3].astype(np.uint8), 'RGB')
            out_sz = 256 if name in ('fog_cloud', 'flowmap', 'clouds_n') else 512
            img = img.resize((out_sz, out_sz), Image.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, 'PNG', optimize=True)
            data = buf.getvalue()
            out_dir.mkdir(parents=True, exist_ok=True)
            tmp = target.with_suffix('.tmp')
            tmp.write_bytes(data)
            tmp.replace(target)
            return data
        except (ImportError, OSError, ValueError, RuntimeError):
            return None


def get_map_icon_png(key: str, cache_dir: Path | None = None) -> bytes | None:
    """Return cached 96x96 RGBA in-game map marker icon PNG extracted from local root.texpack."""
    pair = MAP_ICON_ASSETS.get(key)
    if not pair:
        return None
    out_dir = Path(cache_dir) if cache_dir is not None else MAP_ASSETS_DIR
    target = out_dir / f'icon_{key}.png'
    if target.is_file():
        cached = target.read_bytes()
        if cached.startswith(b'\x89PNG\r\n\x1a\n') and len(cached) > 32:
            return cached
    if not paths.find_game_dir():
        return None
    with _lock:
        if target.is_file():
            cached = target.read_bytes()
            if cached.startswith(b'\x89PNG\r\n\x1a\n') and len(cached) > 32:
                return cached
        try:
            from tools import gow_texpack
            tx_c, tx_m = pair
            need = [tx_c, tx_m] if tx_m else [tx_c]
            res = gow_texpack.extract(need)
            got = res.get(tx_c)
            if not got:
                return None
            _, arr = got
            rgb = arr[..., :3].astype(np.uint8)
            got_m = res.get(tx_m) if tx_m else None
            if got_m is not None and got_m[1].ndim == 2:
                alpha = got_m[1].astype(np.uint8)
                if alpha.shape[:2] != rgb.shape[:2]:
                    alpha = np.asarray(
                        Image.fromarray(alpha, 'L').resize((rgb.shape[1], rgb.shape[0]), Image.LANCZOS),
                        dtype=np.uint8,
                    )
            else:
                # Key out pure black border pixels smoothly while preserving dark interior strokes
                mx = rgb.max(axis=2).astype(np.float32)
                h, w = mx.shape
                visited = np.zeros((h, w), dtype=bool)
                bg = mx < 18.0
                stack = []
                for x in range(w):
                    if bg[0, x]: stack.append((0, x))
                    if bg[h - 1, x]: stack.append((h - 1, x))
                for y in range(h):
                    if bg[y, 0]: stack.append((y, 0))
                    if bg[y, w - 1]: stack.append((y, w - 1))
                while stack:
                    cy, cx = stack.pop()
                    if visited[cy, cx]:
                        continue
                    visited[cy, cx] = True
                    for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
                        if 0 <= ny < h and 0 <= nx < w and not visited[ny, nx] and bg[ny, nx]:
                            stack.append((ny, nx))
                alpha = np.where(visited, 0, 255).astype(np.uint8)
                # Feather 1px edge against black bleed
                a_f = alpha.astype(np.float32)
                edge = (a_f > 0) & (mx < 42.0)
                if np.any(edge):
                    alpha[edge] = np.clip((mx[edge] - 12.0) / 30.0 * 255.0, 0, 255).astype(np.uint8)
            rgba = np.dstack([rgb, alpha])
            img = Image.fromarray(rgba, 'RGBA')
            bbox = img.getbbox()
            if bbox:
                img = img.crop(bbox)
            img.thumbnail((96, 96), Image.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, 'PNG', optimize=True)
            data = buf.getvalue()
            out_dir.mkdir(parents=True, exist_ok=True)
            tmp = target.with_suffix('.tmp')
            tmp.write_bytes(data)
            tmp.replace(target)
            return data
        except (ImportError, OSError, ValueError, RuntimeError):
            return None


def _ensure_native_3d(realm: str, native_dir: Path | None = None, allow_extract: bool = True) -> Path | None:
    """Return path to cached native 3D scene directory for a realm, building lazily if game files exist."""
    base = Path(native_dir) if native_dir is not None else NATIVE_3D_DIR
    rdir = base / realm
    meta_path = rdir / 'meta.json'
    if meta_path.is_file() and (rdir / 'surface.png').is_file() and (rdir / 'props.bin').is_file():
        return rdir
    if not allow_extract or native_dir is not None or not paths.find_game_dir():
        return None
    with _lock:
        if meta_path.is_file() and (rdir / 'surface.png').is_file() and (rdir / 'props.bin').is_file():
            return rdir
        try:
            from tools.gow_native_map_3d import NATIVE_REALMS, build_realm_native_3d
            if realm not in NATIVE_REALMS:
                return None
            built = build_realm_native_3d(realm, out_base=base)
            if built and meta_path.is_file():
                return rdir
        except (ImportError, OSError, ValueError, RuntimeError, FileNotFoundError):
            return None
    return None


def get_realm_native_3d_meta(realm: str, native_dir: Path | None = None, allow_extract: bool = True) -> dict:
    """Return metadata for a realm's reverse-engineered 3D game scene (or has_native_3d=False)."""
    rdir = _ensure_native_3d(realm, native_dir=native_dir, allow_extract=allow_extract)
    if rdir is None:
        return {
            'realm': realm, 'has_native_3d': False, 'has_surface': False,
            'has_props': False, 'has_normal_atlas': False,
        }
    try:
        meta = json.loads((rdir / 'meta.json').read_text(encoding='utf-8'))
        mtimes = [int((rdir / fn).stat().st_mtime) for fn in ('meta.json', 'surface.png', 'terrain_n.png', 'props.bin') if (rdir / fn).is_file()]
        if mtimes:
            meta['rev'] = max(mtimes)
        return meta
    except (OSError, json.JSONDecodeError):
        return {
            'realm': realm, 'has_native_3d': False, 'has_surface': False,
            'has_props': False, 'has_normal_atlas': False,
        }


def get_realm_native_3d_file(
    realm: str,
    filename: str,
    native_dir: Path | None = None,
    allow_extract: bool = True,
    prefer_webp: bool = False,
) -> tuple[bytes, str] | None:
    """Return (bytes, content_type) for a realm's props.bin, atlas.png, atlas_n.png, surface.png, terrain_n.png, or water_mask.png."""
    ctype = NATIVE_3D_FILES.get(filename)
    if not ctype:
        return None
    rdir = _ensure_native_3d(realm, native_dir=native_dir, allow_extract=allow_extract)
    if rdir is None:
        return None
    target = rdir / filename
    if not target.is_file():
        return None
    if prefer_webp and filename.endswith('.png'):
        webp_path = target.with_suffix('.webp')
        try:
            src_mtime = target.stat().st_mtime
            if webp_path.is_file() and webp_path.stat().st_mtime >= src_mtime:
                return webp_path.read_bytes(), 'image/webp'
            with _lock:
                if webp_path.is_file() and webp_path.stat().st_mtime >= src_mtime:
                    return webp_path.read_bytes(), 'image/webp'
                buf = io.BytesIO()
                with Image.open(target) as im:
                    if filename == 'water_mask.png':
                        im.save(buf, format='WEBP', lossless=True, method=4)
                    elif im.mode == 'RGBA':
                        im.save(buf, format='WEBP', quality=92, alpha_quality=100, exact=True, method=4)
                    else:
                        im.save(buf, format='WEBP', quality=92, method=4)
                raw = buf.getvalue()
                tmp = webp_path.with_suffix('.webp.tmp')
                tmp.write_bytes(raw)
                tmp.replace(webp_path)
                return raw, 'image/webp'
        except (OSError, ValueError, KeyError):
            pass
    return target.read_bytes(), ctype
