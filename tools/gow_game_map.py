"""Build native God of War Ragnarok realm maps from the game's own map heightmaps.

The in-game world map is NOT a painted texture: r_ui.wad holds a 20x20-unit
plane per realm (MESH_<realm>_0) displaced by a 2048x2048 BC6H heightmap
TX_<realm>_h_<hash> from root.texpack, plus decals, POI models and text meshes.
This tool extracts the heightmap at full half-float precision (imagecodecs)
and renders a relief in the companion's GoWR palette (obsidian + gold).

Output: cache/gow_game_maps/<map>.png (RGBA, 4096 px) and <map>_h.npy.
Game files are only read.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gow_texpack  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
from paths import CACHE
OUT_DIR = CACHE / 'gow_game_maps'

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
    ap.add_argument('--out', type=Path, default=OUT_DIR)
    ap.add_argument('--game-dir', type=Path)
    args = ap.parse_args()
    if args.game_dir:
        import paths
        paths.GAME_DIR = paths.find_game_dir(args.game_dir)
    args.out.mkdir(parents=True, exist_ok=True)
    manifest = {}
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


if __name__ == '__main__':
    main()
