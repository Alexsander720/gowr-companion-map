r"""Build native God of War Ragnarok realm maps and 16-bit GPU heightmaps.

The in-game world map is NOT a painted texture: r_ui.wad holds a 20x20-unit
plane per realm (MESH_<realm>_0) displaced by a 2048x2048 BC6H heightmap
TX_<realm>_h_<hash> from root.texpack, plus decals, POI models and text meshes.
This tool extracts the heightmap at full half-float precision (imagecodecs)
and generates:
  - <realm>_h16.png: 512x512 16-bit RG-encoded Web Mercator heightmap for WebGL2
  - <map>.png (optional): 2D hillshade relief tiles for /gow-game-tiles/

Output lives strictly in %LOCALAPPDATA%\gowr-companion-map\cache\gow_game_maps\.
Game files are only read.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gow_texpack  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import paths  # noqa: E402
from paths import CACHE, DATA  # noqa: E402

OUT_DIR = CACHE / 'gow_game_maps'
GEOREF_PATH = DATA / 'gow_game_map_georef.json'

# map id -> (realm key used by the companion, heightmap texture in r_ui.wad)
GAME_MAPS = {
    'midgard': ('midgard', 'TX_mid_h_E08F852340F1D56A'),
    'vanaheim_crater': ('vanaheim', 'TX_van_crat_h_A51409AB43CE0836'),
    'vanaheim_jungle': ('vanaheim', 'TX_van_jg_h_BF81E1B5C4C9E45B'),
    'svartalfheim': ('svartalfheim', 'TX_sva_h_8D5F4A0A9449F6D8'),
    'alfheim': ('alfheim', 'TX_alf_h_B8688866E0AB1908'),
    'jotunheim': ('jotunheim', 'TX_jot_h_9A6B0FC50D8A9B68'),
    'asgard': ('asgard', 'TX_asg_h_0D8CD2428D093E4B'),
    'helheim': ('helheim', 'TX_hel_h_4E1AF665773E3B49'),
    'niflheim': ('niflheim', 'TX_nif_h_61380295CCDCFF42'),
    'muspelheim': ('muspelheim', 'TX_msp_h_496ACA3040A5560F'),
}

# Palette per realm: (low, mid, high) RGB — muted, warm, readable under gold UI.
PALETTES = {
    'midgard': ((34, 52, 66), (120, 140, 150), (226, 232, 230)),
    'vanaheim': ((30, 54, 44), (98, 120, 78), (206, 196, 150)),
    'svartalfheim': ((34, 44, 52), (110, 108, 98), (210, 192, 156)),
    'alfheim': ((28, 46, 70), (150, 132, 96), (236, 214, 166)),
    'jotunheim': ((44, 48, 40), (120, 116, 92), (214, 206, 176)),
    'asgard': ((40, 46, 48), (126, 128, 118), (222, 214, 190)),
    'helheim': ((22, 40, 44), (84, 104, 108), (190, 206, 206)),
    'niflheim': ((34, 30, 54), (112, 104, 140), (214, 206, 232)),
    'muspelheim': ((42, 18, 12), (122, 62, 34), (230, 170, 96)),
}

# Canonical 3D Web Mercator bounds, vertical relief scale, weather and lighting palette per realm.
REALM_3D_META = {
    'midgard': {
        'bounds': {'lat_min': 0.4575, 'lat_max': 0.9581, 'lng_min': -1.0567, 'lng_max': -0.3172},
        'height_scale': 0.105,
        'weather': 'snow',
        'palette': {
            'bg': '#060c13', 'fog': '#1a2c3d', 'key_light': '#f2f7fc',
            'rim_light': '#9ec8ea', 'ambient': '#667b90', 'water': '#16384d',
            'beacon': '#f5cf72', 'trail': '#8ed4ff',
        },
    },
    'vanaheim': {
        'bounds': {'lat_min': 0.2772, 'lat_max': 1.0271, 'lng_min': -0.8695, 'lng_max': -0.5775},
        'height_scale': 0.102,
        'weather': 'motes',
        'palette': {
            'bg': '#06100c', 'fog': '#142a1f', 'key_light': '#f6f0dc',
            'rim_light': '#7cd4a8', 'ambient': '#4e6958', 'water': '#102d22',
            'beacon': '#f5d47a', 'trail': '#82e0aa',
        },
    },
    'svartalfheim': {
        'bounds': {'lat_min': 0.3973, 'lat_max': 1.0097, 'lng_min': -0.9220, 'lng_max': -0.4881},
        'height_scale': 0.108,
        'weather': 'embers',
        'palette': {
            'bg': '#080c12', 'fog': '#1a232e', 'key_light': '#f7ecd4',
            'rim_light': '#90b0cc', 'ambient': '#58626e', 'water': '#142433',
            'beacon': '#f5ca70', 'trail': '#f0b65c',
        },
    },
    'alfheim': {
        'bounds': {'lat_min': 0.3425, 'lat_max': 1.0027, 'lng_min': -0.9806, 'lng_max': -0.4521},
        'height_scale': 0.098,
        'weather': 'motes',
        'palette': {
            'bg': '#090e19', 'fog': '#1c283e', 'key_light': '#fcf4de',
            'rim_light': '#92c8fc', 'ambient': '#5e647c', 'water': '#142844',
            'beacon': '#f8da8e', 'trail': '#94ccff',
        },
    },
    'jotunheim': {
        'bounds': {'lat_min': 0.3326, 'lat_max': 1.0295, 'lng_min': -0.9498, 'lng_max': -0.4518},
        'height_scale': 0.085,
        'weather': 'motes',
        'palette': {
            'bg': '#0b0d09', 'fog': '#1c2017', 'key_light': '#f4e8ca',
            'rim_light': '#9cb48a', 'ambient': '#4c5040', 'water': '#161b12',
            'beacon': '#f2d482', 'trail': '#d8c284',
        },
    },
    'asgard': {
        'bounds': {'lat_min': 0.3533, 'lat_max': 1.0556, 'lng_min': -0.9013, 'lng_max': -0.5124},
        'height_scale': 0.092,
        'weather': 'motes',
        'palette': {
            'bg': '#0a0c11', 'fog': '#1c202a', 'key_light': '#f7ebd0',
            'rim_light': '#9db4cf', 'ambient': '#4c505c', 'water': '#151a24',
            'beacon': '#f6d680', 'trail': '#ecc86e',
        },
    },
    'helheim': {
        'bounds': {'lat_min': 0.4554, 'lat_max': 0.8810, 'lng_min': -0.9530, 'lng_max': -0.4745},
        'height_scale': 0.086,
        'weather': 'snow',
        'palette': {
            'bg': '#040c10', 'fog': '#0d232b', 'key_light': '#d4f0f2',
            'rim_light': '#66c6d6', 'ambient': '#32525c', 'water': '#0b2028',
            'beacon': '#8ae8ee', 'trail': '#82d8e0',
        },
    },
    'niflheim': {
        'bounds': {'lat_min': 0.5832, 'lat_max': 0.8307, 'lng_min': -0.9721, 'lng_max': -0.4627},
        'height_scale': 0.074,
        'weather': 'snow',
        'palette': {
            'bg': '#090916', 'fog': '#1a1834', 'key_light': '#e6def8',
            'rim_light': '#8d9ef0', 'ambient': '#444064', 'water': '#14122b',
            'beacon': '#cbb8ff', 'trail': '#ae9ef6',
        },
    },
    'muspelheim': {
        'bounds': {'lat_min': 0.5227, 'lat_max': 0.8823, 'lng_min': -0.9513, 'lng_max': -0.5157},
        'height_scale': 0.105,
        'weather': 'embers',
        'palette': {
            'bg': '#0e0604', 'fog': '#2a1009', 'key_light': '#ffc484',
            'rim_light': '#ff6a36', 'ambient': '#582c1e', 'water': '#240b06',
            'beacon': '#ffc266', 'trail': '#ff823c',
        },
    },
    'sindris-house': {
        'bounds': {'lat_min': 0.5295, 'lat_max': 0.9041, 'lng_min': -0.9272, 'lng_max': -0.3142},
        'height_scale': 0.042,
        'weather': 'motes',
        'palette': {
            'bg': '#060c14', 'fog': '#102032', 'key_light': '#f0e4c8',
            'rim_light': '#7ab2ec', 'ambient': '#3b4e62', 'water': '#0c1b2c',
            'beacon': '#f2d27e', 'trail': '#92bef0',
        },
    },
}


def merc0_from_latlng(lat: float, lng: float) -> tuple[float, float]:
    """Convert Web Mercator (lat, lng) to zoom-0 pixel coordinates in [0, 256]."""
    gx = (lng + 180.0) / 360.0 * 256.0
    s = max(-0.999999, min(0.999999, math.sin(math.radians(lat))))
    gy = (0.5 - math.log((1.0 + s) / (1.0 - s)) / (4.0 * math.pi)) * 256.0
    return gx, gy


def realm_height_meta(realm: str, maps_dir: Path | None = None) -> dict | None:
    """Return canonical Web Mercator bounds, relief scale and lighting palette for a realm."""
    entry = REALM_3D_META.get(realm)
    if entry is None:
        return None
    b = entry['bounds']
    x0, y0 = merc0_from_latlng(b['lat_max'], b['lng_min'])
    x1, y1 = merc0_from_latlng(b['lat_min'], b['lng_max'])
    base_dir = Path(maps_dir) if maps_dir is not None else (paths.CACHE / 'gow_game_maps')
    h16_path = base_dir / f'{realm}_h16.png'
    has_h16 = h16_path.is_file()
    rev = int(h16_path.stat().st_mtime) if has_h16 else 0
    return {
        'realm': realm,
        'bounds': dict(b),
        'merc0': {'x_min': x0, 'x_max': x1, 'y_min': y0, 'y_max': y1},
        'height_scale': entry['height_scale'],
        'weather': entry.get('weather', 'motes'),
        'palette': dict(entry['palette']),
        'has_heightmap': has_h16,
        'rev': rev,
    }


def heightmap(map_id):
    realm, tex = GAME_MAPS[map_id]
    res = gow_texpack.extract([tex])[tex]
    if res is None:
        raise SystemExit(f'{tex} not found in texpacks')
    info, arr = res
    h = arr[..., 0].astype(np.float32) if arr.ndim == 3 else arr.astype(np.float32)
    return info, h


def _resize(a, size):
    return np.asarray(Image.fromarray(a.astype(np.float32), 'F').resize((size, size), Image.BICUBIC),
                      dtype=np.float32)


def _bilinear_sample(arr: np.ndarray, tx: np.ndarray, ty: np.ndarray, edge_pad: float = 18.0):
    """Bilinear sample float32 2D array at (tx, ty) returning (values, coverage_weight)."""
    h, w = arr.shape
    fx = tx - 0.5
    fy = ty - 0.5
    x0 = np.floor(fx).astype(np.int64)
    y0 = np.floor(fy).astype(np.int64)
    wx = (fx - x0).astype(np.float32)
    wy = (fy - y0).astype(np.float32)

    def at(yy, xx):
        return arr[np.clip(yy, 0, h - 1), np.clip(xx, 0, w - 1)]

    val = (
        at(y0, x0) * (1.0 - wx) * (1.0 - wy)
        + at(y0, x0 + 1) * wx * (1.0 - wy)
        + at(y0 + 1, x0) * (1.0 - wx) * wy
        + at(y0 + 1, x0 + 1) * wx * wy
    )
    dx = np.minimum(tx, (w - 1) - tx)
    dy = np.minimum(ty, (h - 1) - ty)
    dist = np.minimum(dx, dy)
    weight = np.clip(dist / max(edge_pad, 1.0), 0.0, 1.0).astype(np.float32)
    weight = weight * weight * (3.0 - 2.0 * weight)
    return val.astype(np.float32), weight


def encode_h16_png(h01: np.ndarray, valid_mask: np.ndarray | None = None) -> bytes:
    """Encode normalized [0, 1] height array as 16-bit RG PNG in RGB (no alpha premultiply)."""
    import io
    u16 = np.round(np.clip(h01, 0.0, 1.0) * 65535.0).astype(np.uint16)
    h, w = u16.shape
    rgb = np.empty((h, w, 3), dtype=np.uint8)
    rgb[..., 0] = (u16 >> 8).astype(np.uint8)
    rgb[..., 1] = (u16 & 0xFF).astype(np.uint8)
    rgb[..., 2] = (np.where(valid_mask, 255, 0).astype(np.uint8) if valid_mask is not None else 255)
    buf = io.BytesIO()
    Image.fromarray(rgb, 'RGB').save(buf, 'PNG', compress_level=9)
    return buf.getvalue()


def build_realm_h16(
    realm: str,
    out_dir: Path | None = None,
    maps_dir: Path | None = None,
    georef: dict | None = None,
    size: int = 1024,
) -> Path | None:
    """Build a 1024x1024 RG16 Web Mercator heightmap PNG (<realm>_h16.png) for a realm."""
    meta = realm_height_meta(realm, maps_dir=out_dir)
    if meta is None:
        return None
    if georef is None:
        georef = json.loads(GEOREF_PATH.read_text(encoding='utf-8')) if GEOREF_PATH.is_file() else {}
    entries = [(mid, ref) for mid, ref in sorted(georef.items())
               if ref.get('accepted') and ref.get('realm') == realm and ref.get('merc0_to_texture')]
    if not entries:
        return None

    out_path_dir = Path(out_dir) if out_dir is not None else (paths.CACHE / 'gow_game_maps')
    src_dir = Path(maps_dir) if maps_dir is not None else out_path_dir

    m0 = meta['merc0']
    xs = np.linspace(m0['x_min'], m0['x_max'], size, dtype=np.float64)
    ys = np.linspace(m0['y_min'], m0['y_max'], size, dtype=np.float64)
    gx, gy = np.meshgrid(xs, ys)

    fragments: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    for map_id, ref in entries:
        npy_path = src_dir / f'{map_id}_h.npy'
        if npy_path.is_file():
            h = np.load(npy_path).astype(np.float32)
        else:
            _, h = heightmap(map_id)
        # TX_<realm>_h stores depth from peak (0=peak, 1=basin/void); invert so peaks rise upward.
        elev = 1.0 - h
        q0, q1 = np.quantile(elev, [0.005, 0.995])
        hn = np.clip((elev - q0) / max(float(q1 - q0), 1e-6), 0.0, 1.0).astype(np.float32)
        G = np.asarray(ref['merc0_to_texture'], dtype=np.float64)
        k = hn.shape[1] / float(ref.get('texture_px') or 2048)
        tx = (G[0, 0] * gx + G[0, 1] * gy + G[0, 2]) * k
        ty = (G[1, 0] * gx + G[1, 1] * gy + G[1, 2]) * k
        fragments[map_id] = _bilinear_sample(hn, tx, ty)

    if realm == 'vanaheim' and 'vanaheim_crater' in fragments and 'vanaheim_jungle' in fragments:
        vc, _ = fragments['vanaheim_crater']
        vj, _ = fragments['vanaheim_jungle']
        # Match Crater & Jungle plateau heights smoothly across the uninhabited lat 0.665..0.705 gap.
        lat_grid = np.degrees(np.arctan(np.sinh(np.pi * (1.0 - 2.0 * gy / 256.0))))
        gap = (lat_grid >= 0.672) & (lat_grid <= 0.700)
        if np.any(gap):
            med_c = float(np.median(vc[gap]))
            med_j = float(np.median(vj[gap]))
            if 0.05 < med_c < 0.95 and 0.05 < med_j < 0.95:
                vc = np.where(vc <= med_c, vc * (med_j / med_c),
                              med_j + (vc - med_c) * ((1.0 - med_j) / (1.0 - med_c))).astype(np.float32)
        t = np.clip((lat_grid - 0.660) / (0.710 - 0.660), 0.0, 1.0).astype(np.float32)
        s = t * t * (3.0 - 2.0 * t)
        h01 = (vc * s + vj * (1.0 - s)).astype(np.float32)
        valid = np.ones((size, size), dtype=bool)
    else:
        num = np.zeros((size, size), dtype=np.float32)
        den = np.zeros((size, size), dtype=np.float32)
        raw_fallback = None
        for vals, weights in fragments.values():
            if raw_fallback is None:
                raw_fallback = vals
            num += vals * weights
            den += weights
        valid = den > 0.01
        h01 = np.where(valid, num / np.maximum(den, 1e-6), raw_fallback if raw_fallback is not None else 0.0).astype(np.float32)
        valid = np.ones((size, size), dtype=bool)

    # Selective cliff-edge anti-aliasing on high-res h16: smooth 1-texel sheer drops so the
    # 384x384 terrain grid doesn't produce sawtooth vertical curtains, while keeping plateaus razor-sharp.
    if size >= 256:
        gy_h, gx_h = np.gradient(h01)
        cliff_steep = np.hypot(gx_h, gy_h)
        blend_w = np.clip((cliff_steep - 0.035) / 0.12, 0.0, 1.0).astype(np.float32)
        if float(blend_w.max()) > 0.01:
            try:
                import cv2
                h_sm = cv2.GaussianBlur(h01, (0, 0), 1.05)
                blend_w = cv2.GaussianBlur(blend_w, (0, 0), 1.4)
            except ImportError:
                from PIL import ImageFilter
                u8_h = np.clip(h01 * 255.0, 0, 255).astype(np.uint8)
                h_sm = np.asarray(Image.fromarray(u8_h, 'L').filter(ImageFilter.GaussianBlur(radius=1.05)), dtype=np.float32) / 255.0
                u8_w = np.clip(blend_w * 255.0, 0, 255).astype(np.uint8)
                blend_w = np.asarray(Image.fromarray(u8_w, 'L').filter(ImageFilter.GaussianBlur(radius=1.4)), dtype=np.float32) / 255.0
            h01 = (h01 * (1.0 - blend_w * 0.82) + h_sm * (blend_w * 0.82)).astype(np.float32)

    png_bytes = encode_h16_png(h01, valid_mask=valid)
    out_path_dir.mkdir(parents=True, exist_ok=True)
    target = out_path_dir / f'{realm}_h16.png'
    tmp = target.with_suffix('.tmp')
    tmp.write_bytes(png_bytes)
    tmp.replace(target)
    return target


def render(h, realm, size=4096, z_exag=420.0):
    """Hillshade + hypsometric tint + soft ambient occlusion -> RGBA uint8."""
    hs = _resize(h, size)
    gy, gx = np.gradient(hs * z_exag * size / 2048.0)
    slope = np.arctan(np.hypot(gx, gy))
    aspect = np.arctan2(-gx, gy)
    shade = np.zeros_like(hs)
    # multi-directional light (NW dominant) avoids flat-looking slopes facing the light
    for az, w in ((315, 0.55), (270, 0.2), (0, 0.15), (225, 0.1)):
        a, alt = np.radians(az), np.radians(42)
        shade += w * (np.sin(alt) * np.cos(slope) + np.cos(alt) * np.sin(slope) * np.cos(a - aspect))
    shade = np.clip(shade, 0, 1)
    # local relief (difference to blurred) emphasises cliffs and paths
    import cv2
    blur = cv2.GaussianBlur(hs, (0, 0), size / 160)
    local = np.clip((hs - blur) * 18 + 0.5, 0, 1)
    lo, mid, hi = (np.array(c, np.float32) for c in PALETTES[realm])
    q = np.quantile(hs, [0.02, 0.98])
    t = np.clip((hs - q[0]) / max(q[1] - q[0], 1e-6), 0, 1)[..., None]
    tint = np.where(t < 0.5, lo + (mid - lo) * (t / 0.5), mid + (hi - mid) * ((t - 0.5) / 0.5))
    light = (0.35 + 0.85 * shade[..., None]) * (0.8 + 0.4 * local[..., None])
    rgb = np.clip(tint * light, 0, 255)
    # flat areas (the void around a realm: sea, sky, lava plain) fade out
    flat = (np.hypot(*np.gradient(_resize(h, 512))) > 2e-4).astype(np.float32)
    flat = cv2.GaussianBlur(cv2.dilate(flat, np.ones((9, 9), np.uint8)), (0, 0), 10)
    flat = cv2.resize(flat, (size, size), interpolation=cv2.INTER_CUBIC)
    alpha = np.clip(0.1 + flat * 0.95, 0, 1)
    edge = np.minimum.outer(*(2 * [np.minimum(np.arange(size), np.arange(size)[::-1]) / (size * 0.04)]))
    alpha *= np.clip(edge, 0, 1)
    return np.dstack([rgb, alpha * 255]).astype(np.uint8)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('maps', nargs='*', default=list(GAME_MAPS))
    ap.add_argument('--size', type=int, default=4096)
    ap.add_argument('--h16-size', type=int, default=512)
    ap.add_argument('--h16-only', action='store_true', help='Generate compact 512x512 RG16 heightmaps only')
    ap.add_argument('--out', type=Path, default=OUT_DIR)
    ap.add_argument('--src-npy', type=Path, help='Optional directory containing pre-extracted <map>_h.npy')
    ap.add_argument('--game-dir', type=Path)
    args = ap.parse_args()
    if args.game_dir:
        paths.GAME_DIR = paths.find_game_dir(args.game_dir)
    args.out.mkdir(parents=True, exist_ok=True)
    manifest = {}
    realms = sorted({GAME_MAPS[m][0] for m in args.maps if m in GAME_MAPS})
    if not args.h16_only:
        for m in args.maps:
            info, h = heightmap(m)
            np.save(args.out / f'{m}_h.npy', h)
            Image.fromarray(render(h, GAME_MAPS[m][0], args.size), 'RGBA').save(args.out / f'{m}.png', compress_level=4)
            manifest[m] = dict(realm=GAME_MAPS[m][0], texture=GAME_MAPS[m][1], source=info['texpack'],
                               format=info['dxgi_name'], heightmap_px=[info['width'], info['height']],
                               png_px=args.size)
            print(m, manifest[m], flush=True)
        path = args.out / 'manifest.json'
        old = json.loads(path.read_text(encoding='utf-8')) if path.is_file() else {}
        old.update(manifest)
        path.write_text(json.dumps(old, ensure_ascii=False, indent=1), encoding='utf-8')
    for r in realms:
        out_h16 = build_realm_h16(r, out_dir=args.out, maps_dir=args.src_npy or args.out, size=args.h16_size)
        if out_h16 is not None:
            print(f'h16: {out_h16.name} ({out_h16.stat().st_size} bytes)', flush=True)


if __name__ == '__main__':
    main()
