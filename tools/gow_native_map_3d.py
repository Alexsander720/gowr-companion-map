r"""Extract native God of War Ragnarök 3D World Map meshes, PBR atlases, and surfaces.

Reads directly (strictly read-only) from the local game installation:
  - exec/wad/pc_le/r_ui.wad      (WTOC v2: MESH_<realm>_0, goProto<Realm> 4x4 joints,
                                  MG_<realm>_0_gpu inline geometry, MAT_* -> TX_* links,
                                  and DCL_* map paint decals)
  - exec/wad/pc_le/root.lodpack  (uncompressed 3D landmark vertex/index buffers)
  - exec/wad/pc_le/root.texpack  (BC6H 2048x2048 heightmaps, 1024x1024 PBR POI diffuse
                                  textures, water/lava/navpath/underground masks, ice cracks)

Writes compact WebGL2-ready cache files ONLY into:
  %LOCALAPPDATA%\gowr-companion-map\cache\gow_native_3d\<realm>\
    - props.bin    (GOWM v1 binary 3D landmark mesh in WebGL2 world coordinates)
    - atlas.png    (packed PBR diffuse texture atlas for all realm landmarks)
    - surface.png  (2048x2048 pure native game terrain surface, zero MapGenie pixels)
    - meta.json    (counts, version stamp, and capability flags)

Never writes into the game directory or the git repository.
"""
from __future__ import annotations

import argparse
import io
import json
import math
import re
import struct
import sys
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import paths  # noqa: E402
import gow_texpack  # noqa: E402
from gow_game_map import GAME_MAPS, REALM_3D_META, build_realm_h16, realm_height_meta  # noqa: E402

SCHEMA_VERSION = 1
WORLD_SPAN = 2048.0
OUT_BASE = paths.CACHE / 'gow_native_3d'
GEOREF_PATH = paths.DATA / 'gow_game_map_georef.json'

NATIVE_REALMS = (
    'midgard',
    'svartalfheim',
    'vanaheim',
    'alfheim',
    'asgard',
    'helheim',
    'jotunheim',
    'muspelheim',
    'niflheim',
)

# Verified goProto<Realm> heightmap quad footprints in MESH_<realm>_0 3D space:
# map_id -> (cx, cz, half_x, half_z)
QUAD_FOOTPRINTS: dict[str, tuple[float, float, float, float]] = {
    'midgard':         (-0.1868, -0.4868, 9.9530 * 0.7794, 9.9966 * 0.7794),
    'alfheim':         (0.0,     0.0,     8.04 * 0.787,    8.04 * 0.787),
    'asgard':          (0.0,     0.0,     9.80 * 0.700,    9.80 * 0.700),
    'helheim':         (0.0,     0.0,     0.50 * 8.850,    0.50 * 8.850),
    'jotunheim':       (0.0,     0.617,   10.00 * 0.617,   10.00 * 0.617),
    'muspelheim':      (0.0,     0.0,     0.50 * 9.250,    0.50 * 9.250),
    'niflheim':        (0.0,     0.0,     0.50 * 7.500,    0.50 * 7.500),
    'svartalfheim':    (0.0,     0.0,     0.50 * 18.081,   0.50 * 18.081),
    'vanaheim_crater': (0.709,  -4.997,   6.00 * 0.785,    6.00 * 0.785),
    'vanaheim_jungle': (-0.719,  4.424,   6.00 * 0.785,    6.00 * 0.785),
}

# Authentic per-realm game terrain mask textures in root.texpack
REALM_MASKS: dict[str, dict[str, list[str]]] = {
    'midgard': {
        'lake': ['TX_mid_navpath_lake_m_DE744B4D03F2E085'],
        'navpath': ['TX_mid_navpath_d_056BB61C16A6E26E'],
        'underground': ['TX_undergroundpaths_mid_m_B39F58CF155DA604'],
        'ice_cracks': ['TX_ice_cracked_2_a_A93B35E194B08ACF'],
    },
    'svartalfheim': {
        'water': ['TX_sva_cp_water_m_E0303F2EFD53950E'],
        'wateredge': ['TX_sva_cp_wateredge_m_C5E50841DAA550D8'],
        'underground': [
            'TX_undergroundpaths_svart_m_B2C7FE4ED21DD0BB',
            'TX_undergroundpaths_svart_02_m_E5B88F900BE04C92',
            'TX_undergroundpaths_svart_03_m_70759095751DC849',
        ],
    },
    'vanaheim_crater': {
        'water': ['TX_van_crat_water_m_6DE69C071A49A901'],
        'navpath': ['TX_van_crat_navpath_m_3A1FD8F9A8F8C96B'],
    },
    'vanaheim_jungle': {
        'water': ['TX_van_jg_water_m_3ACFD39B3F944F37'],
        'navpath': ['TX_van_jg_navpath_m_A9E030F901034DD5'],
        'underground': ['TX_undergroundpaths_van_m_FA2998055D5EB8EC'],
    },
    'alfheim': {
        'water': ['TX_alf_water_m_CD61B03CB844A944'],
        'wateredge': ['TX_alf_wateredge_m_C890C839BD32B04D'],
        'underground': ['TX_undergroundpaths_alf_m_989F6CF982C3026A'],
    },
    'asgard': {
        'water': ['TX_asg_water_m_33FA612B4E36BD4A'],
    },
    'helheim': {},
    'jotunheim': {
        'water': ['TX_jot_water_m_3A6B8BD84C140F01'],
        'navpath': ['TX_jot_navpath_m_9040170036169A57'],
    },
    'muspelheim': {
        'lava': ['TX_msp_lava_m_AD04AFFC02C55576'],
        'underground': ['TX_undergroundpaths_msp_m_86130EFA3BB1BF23'],
    },
    'niflheim': {
        'underground': [
            'TX_undergroundpaths_nif_m_CDB7AF32672E7F59',
            'TX_undergroundpaths_nif_02_m_96AD24D822A38AD3',
            'TX_undergroundpaths_nif_03_m_49CC61619D493C35',
        ],
    },
}

# Authentic in-game terrain biome palettes calibrated against PC/PS5 map renders:
# Clean PBR albedo values (WebGL2 TERRAIN_FS applies dynamic daylight + relief shading)
SURFACE_STYLES: dict[str, dict[str, Any]] = {
    'midgard': {
        'low': (196, 212, 224), 'mid': (228, 235, 241), 'high': (248, 250, 253),
        'cliff': (112, 108, 102), 'water': (146, 214, 228), 'foam': (228, 247, 252),
        'deep_ice': (26, 68, 104),
        'path': (142, 126, 108), 'void': (14, 21, 30), 'is_ice_lake': True,
        'lake_h_band': (0.14, 0.25),
        'shadow_tint': (0.60, 0.67, 0.78),
    },
    'svartalfheim': {
        'low': (92, 122, 126), 'mid': (174, 166, 142), 'high': (224, 212, 184),
        'cliff': (102, 96, 86), 'water': (42, 98, 128), 'foam': (166, 214, 224),
        'path': (184, 158, 122), 'void': (14, 24, 34),
        'shadow_tint': (0.58, 0.63, 0.70),
    },
    'vanaheim': {
        'low': (76, 114, 86), 'mid': (138, 166, 114), 'high': (204, 202, 160),
        'cliff': (94, 100, 86), 'water': (48, 122, 116), 'foam': (162, 218, 204),
        'path': (168, 152, 118), 'void': (12, 26, 20),
        'shadow_tint': (0.56, 0.64, 0.62),
    },
    'alfheim': {
        'low': (144, 132, 110), 'mid': (216, 194, 154), 'high': (246, 234, 202),
        'cliff': (138, 114, 92), 'water': (64, 134, 178), 'foam': (182, 226, 244),
        'path': (194, 168, 126), 'void': (16, 22, 36),
        'shadow_tint': (0.62, 0.60, 0.66),
    },
    'asgard': {
        'low': (108, 120, 116), 'mid': (176, 182, 162), 'high': (232, 230, 212),
        'cliff': (98, 104, 112), 'water': (48, 96, 130), 'foam': (174, 210, 228),
        'path': (184, 170, 142), 'void': (16, 20, 28),
        'shadow_tint': (0.60, 0.64, 0.72),
    },
    'helheim': {
        'low': (48, 86, 96), 'mid': (122, 160, 168), 'high': (198, 224, 230),
        'cliff': (62, 92, 106), 'water': (28, 68, 84), 'foam': (132, 196, 210),
        'path': (106, 140, 148), 'void': (10, 20, 26),
        'shadow_tint': (0.54, 0.66, 0.72),
    },
    'jotunheim': {
        'low': (112, 122, 96), 'mid': (178, 176, 138), 'high': (232, 226, 194),
        'cliff': (108, 104, 90), 'water': (62, 118, 144), 'foam': (176, 214, 224),
        'path': (194, 176, 134), 'void': (18, 22, 16),
        'shadow_tint': (0.60, 0.62, 0.60),
    },
    'muspelheim': {
        'low': (68, 40, 32), 'mid': (116, 82, 66), 'high': (184, 142, 112),
        'cliff': (62, 44, 38), 'water': (242, 118, 30), 'foam': (255, 216, 94),
        'path': (142, 96, 68), 'void': (20, 10, 8), 'is_lava': True,
        'shadow_tint': (0.56, 0.50, 0.50),
    },
    'niflheim': {
        'low': (90, 98, 128), 'mid': (170, 176, 206), 'high': (230, 232, 246),
        'cliff': (88, 94, 122), 'water': (64, 80, 124), 'foam': (176, 194, 232),
        'path': (142, 146, 178), 'void': (14, 14, 28),
        'shadow_tint': (0.58, 0.62, 0.76),
    },
}

# Real in-game carved wood, stone slab, frost, and paint material textures from MESH_<realm>_0 pi=0
TERRAIN_MATERIAL_TEXTURES: dict[str, str] = {
    'wood_d': 'TX_woodbase_d_E617B2734647FFA0',
    'wood_n': 'TX_woodbase_n_6D1B4B0238F2B22D',
    'wood_ao': 'TX_woodbase_ao_76BA52C615F57DE6',
    'wood_rough_d': 'TX_wood_rough_04_d_grey_B3796E3AB17045FC',
    'wood_rough_n': 'TX_wood_rough_04_n_6A4829523B019441',
    'cell_n': 'TX_wood_cell_n_1F159CE7CAFFC9C2',
    'cell_edge': 'TX_wood_cell_edge_m_317F23EE79840C9B',
    'slab_d': 'TX_slab_d_E86C5594745B6115',
    'slab_n': 'TX_slab_n_011335E426EAF83C',
    'hel_stone': 'TX_hel_stone_m_9FC491B21879825F',
    'frost_a': 'TX_ice_decal_frost_a_274DE971A0D5E060',
    'frost_n': 'TX_ice_decal_frost_n_847540EE690315EA',
    'paint_n': 'TX_paint_n_A9573FE9878D9B5F',
}

# Real in-game carved tree & paint brushstroke textures in root.texpack
DECAL_GAME_TEXTURES: dict[str, tuple[str | None, str | None]] = {
    'tree_mid_1': ('TX_tree_01_d_1EC1489F2C74366F', 'TX_tree_01_m_E489F6F77DE50D95'),
    'tree_mid_2': ('TX_tree_02_d_C4474F2747380BD6', 'TX_tree_02_m_3EECF4861D177B61'),
    'tree_sva': (None, 'TX_treecarving_sva_01_m_0F573A2295B06F4E'),
    'tree_nif': ('TX_treecarving_nif_01_d_A276D167EC3241F6', 'TX_treecarving_nif_01_m_3C7D6F48EDA69863'),
    'paint_brush': (None, 'TX_paint_alpha512_1_FF9D5F9C310F7689'),
    'paint_ring': (None, 'TX_paint_alpha_ring_small_61093BFCB146A1CA'),
}

SKIP_TX_PREFIXES = (
    'TX_woodbase_',
    'TX_rage_noise',
    'TX_font_placeholder',
    'TX_radial_',
    'TX_flow_directional',
    'TX_slab_n_',
)

_MESH_MAGIC = b'\x0c\x00\x0a\x00\x00\x00\x00\x00\x00\x00\x00\x00\x34\x00\x00\x00'


def decode_r10g10b10a2_unorm_normals(raw_u32: np.ndarray) -> np.ndarray:
    """Decode packed R10G10B10A2_UNORM vertex normals into float32 unit XYZ."""
    nx = ((raw_u32 & 0x3FF).astype(np.float32) / 1023.0) * 2.0 - 1.0
    ny = (((raw_u32 >> 10) & 0x3FF).astype(np.float32) / 1023.0) * 2.0 - 1.0
    nz = (((raw_u32 >> 20) & 0x3FF).astype(np.float32) / 1023.0) * 2.0 - 1.0
    nrm = np.stack([nx, ny, nz], axis=1)
    lens = np.linalg.norm(nrm, axis=1, keepdims=True)
    return np.where(lens > 1e-5, nrm / np.maximum(lens, 1e-5), np.array([0.0, 1.0, 0.0], np.float32))


def compute_smooth_normals(pos: np.ndarray, tris: np.ndarray) -> np.ndarray:
    """Fallback area-weighted smooth vertex normals from CCW triangles."""
    v0, v1, v2 = pos[tris[:, 0]], pos[tris[:, 1]], pos[tris[:, 2]]
    fn = np.cross(v1 - v0, v2 - v0)
    out = np.zeros_like(pos, dtype=np.float32)
    for k in range(3):
        np.add.at(out, tris[:, k], fn)
    lens = np.linalg.norm(out, axis=1, keepdims=True)
    return np.where(lens > 1e-6, out / np.maximum(lens, 1e-6), np.array([0.0, 1.0, 0.0], np.float32))


def pack_gowm_binary(vertices: np.ndarray, indices: np.ndarray) -> bytes:
    """Serialize interleaved float32 (pos3, norm3, uv2) + uint32 indices to GOWM v1 bytes."""
    v = np.ascontiguousarray(vertices, dtype='<f4')
    idx = np.ascontiguousarray(indices, dtype='<u4').ravel()
    if v.ndim != 2 or v.shape[1] != 8:
        raise ValueError(f'Expected (N, 8) vertex array, got {v.shape}')
    hdr = struct.pack('<4sIII', b'GOWM', SCHEMA_VERSION, int(v.shape[0]), int(idx.size))
    return hdr + v.tobytes() + idx.tobytes()


def unpack_gowm_binary(data: bytes) -> tuple[np.ndarray, np.ndarray]:
    """Parse GOWM v1 binary mesh back into (vertices[N,8], indices[M])."""
    if len(data) < 16:
        raise ValueError('GOWM buffer too small')
    magic, ver, nv, ni = struct.unpack_from('<4sIII', data, 0)
    if magic != b'GOWM' or ver != SCHEMA_VERSION:
        raise ValueError(f'Unsupported GOWM header: {magic!r} v{ver}')
    v_end = 16 + nv * 32
    i_end = v_end + ni * 4
    if len(data) < i_end:
        raise ValueError(f'Truncated GOWM payload: expected {i_end}, got {len(data)}')
    verts = np.frombuffer(data[16:v_end], dtype='<f4').reshape(nv, 8).copy()
    idxs = np.frombuffer(data[v_end:i_end], dtype='<u4').copy()
    return verts, idxs


def pack_texture_atlas(
    textures: dict[str, np.ndarray],
    weights: dict[str, int] | None = None,
    atlas_w: int = 2048,
    atlas_h: int = 2048,
    pad: int = 4,
) -> tuple[Image.Image, dict[str, tuple[float, float, float, float]]]:
    """Pack named RGB textures into a shelf-packed PNG atlas with edge-bleed padding.

    Returns (PIL.Image RGB, {name: (u0, v0, u_scale, v_scale)}).
    """
    if not textures:
        return Image.new('RGB', (64, 64), (180, 180, 180)), {}
    weights = weights or {}
    # Assign slot sizes: hero textures (high triangle count) get 512px, secondary get 256px
    items = sorted(textures.keys(), key=lambda k: (-weights.get(k, 0), k))
    n = len(items)
    sizes: dict[str, int] = {}
    for rank, key in enumerate(items):
        if n <= 4:
            sizes[key] = 512
        elif n <= 16:
            sizes[key] = 512 if rank < 6 else 256
        else:
            sizes[key] = 512 if rank < 4 else 256

    def _try_pack(aw: int, ah: int):
        x, y, row_h = 0, 0, 0
        rects: dict[str, tuple[int, int, int]] = {}
        for key in sorted(items, key=lambda k: (-sizes[k], -weights.get(k, 0), k)):
            s = sizes[key]
            cell = s + pad * 2
            if x + cell > aw:
                x = 0
                y += row_h
                row_h = 0
            if y + cell > ah:
                return None
            rects[key] = (x + pad, y + pad, s)
            x += cell
            row_h = max(row_h, cell)
        return rects

    rects = _try_pack(atlas_w, atlas_h)
    if rects is None:
        atlas_h = min(4096, atlas_h * 2)
        rects = _try_pack(atlas_w, atlas_h)
    if rects is None:
        # Shrink all to 256px and repack
        sizes = {k: 256 for k in items}
        rects = _try_pack(atlas_w, atlas_h)
    if rects is None:
        sizes = {k: 128 for k in items}
        rects = _try_pack(atlas_w, atlas_h)

    atlas = np.full((atlas_h, atlas_w, 3), 24, dtype=np.uint8)
    uv_map: dict[str, tuple[float, float, float, float]] = {}
    for key, (rx, ry, s) in rects.items():
        arr = textures[key]
        if arr.ndim == 2:
            arr = np.repeat(arr[..., None], 3, axis=2)
        rgb = arr[..., :3].astype(np.uint8)
        tile = np.asarray(Image.fromarray(rgb, 'RGB').resize((s, s), Image.LANCZOS), dtype=np.uint8)
        atlas[ry:ry + s, rx:rx + s] = tile
        # Edge bleed into pad pixels so linear/mipmap filtering never bleeds dark borders
        if pad > 0:
            atlas[ry - pad:ry, rx:rx + s] = tile[0:1, :]
            atlas[ry + s:ry + s + pad, rx:rx + s] = tile[-1:, :]
            atlas[ry - pad:ry + s + pad, rx - pad:rx] = atlas[ry - pad:ry + s + pad, rx:rx + 1]
            atlas[ry - pad:ry + s + pad, rx + s:rx + s + pad] = atlas[ry - pad:ry + s + pad, rx + s - 1:rx + s]
        uv_map[key] = (
            (rx + 0.5) / atlas_w,
            (ry + 0.5) / atlas_h,
            (s - 1.0) / atlas_w,
            (s - 1.0) / atlas_h,
        )
    return Image.fromarray(atlas, 'RGB'), uv_map


def _dilate_rgba_color(rgba: np.ndarray, iters: int = 8) -> np.ndarray:
    """Dilate RGB from opaque pixels into transparent pixels so bilinear/mipmap filtering has zero black fringes."""
    if rgba.ndim != 3 or rgba.shape[2] < 4:
        return rgba
    alpha = rgba[..., 3]
    if int(alpha.min()) >= 250 or int(alpha.max()) < 32:
        return rgba
    rgb = rgba[..., :3].astype(np.float32)
    valid = alpha >= 64
    for _ in range(iters):
        if valid.all():
            break
        acc = np.zeros_like(rgb)
        cnt = np.zeros(valid.shape, dtype=np.float32)
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            sy = slice(max(0, -dy), rgb.shape[0] - max(0, dy))
            sx = slice(max(0, -dx), rgb.shape[1] - max(0, dx))
            ty = slice(max(0, dy), rgb.shape[0] - max(0, -dy))
            tx = slice(max(0, dx), rgb.shape[1] - max(0, -dx))
            v = valid[sy, sx]
            acc[ty, tx] += rgb[sy, sx] * v[..., None]
            cnt[ty, tx] += v.astype(np.float32)
        fill = (~valid) & (cnt > 0)
        if not np.any(fill):
            break
        rgb[fill] = acc[fill] / cnt[fill, None]
        valid[fill] = True
    return np.dstack([np.clip(rgb, 0, 255).astype(np.uint8), alpha])


def pack_pbr_atlases(
    diffuse_maps: dict[str, np.ndarray],
    normal_maps: dict[str, np.ndarray] | None = None,
    gloss_maps: dict[str, np.ndarray] | None = None,
    weights: dict[str, int] | None = None,
    atlas_w: int = 2048,
    atlas_h: int = 2048,
    pad: int = 4,
) -> tuple[Image.Image, Image.Image, dict[str, tuple[float, float, float, float]]]:
    """Pack synchronized diffuse (RGBA with alpha cutouts) + normal/gloss (RGBA) atlases with identical shelf UVs.

    atlas_n.png stores tangent-space normal in RGB (default 128, 128, 255) and gloss in A (default 96).
    """
    normal_maps = normal_maps or {}
    gloss_maps = gloss_maps or {}
    if not diffuse_maps:
        return (
            Image.new('RGBA', (64, 64), (180, 180, 180, 255)),
            Image.new('RGBA', (64, 64), (128, 128, 255, 96)),
            {},
        )
    weights = weights or {}
    items = sorted(diffuse_maps.keys(), key=lambda k: (-weights.get(k, 0), k))
    n = len(items)
    sizes: dict[str, int] = {}
    for rank, key in enumerate(items):
        if n <= 4:
            sizes[key] = 512
        elif n <= 16:
            sizes[key] = 512 if rank < 6 else 256
        else:
            sizes[key] = 512 if rank < 4 else 256

    def _try_pack(aw: int, ah: int):
        x, y, row_h = 0, 0, 0
        rects: dict[str, tuple[int, int, int]] = {}
        for key in sorted(items, key=lambda k: (-sizes[k], -weights.get(k, 0), k)):
            s = sizes[key]
            cell = s + pad * 2
            if x + cell > aw:
                x = 0
                y += row_h
                row_h = 0
            if y + cell > ah:
                return None
            rects[key] = (x + pad, y + pad, s)
            x += cell
            row_h = max(row_h, cell)
        return rects

    rects = _try_pack(atlas_w, atlas_h)
    if rects is None:
        atlas_h = min(4096, atlas_h * 2)
        rects = _try_pack(atlas_w, atlas_h)
    if rects is None:
        sizes = {k: 256 for k in items}
        rects = _try_pack(atlas_w, atlas_h)
    if rects is None:
        sizes = {k: 128 for k in items}
        rects = _try_pack(atlas_w, atlas_h)

    atlas_d = np.full((atlas_h, atlas_w, 4), 24, dtype=np.uint8)
    atlas_d[..., 3] = 255
    atlas_n = np.zeros((atlas_h, atlas_w, 4), dtype=np.uint8)
    atlas_n[..., 0] = 128
    atlas_n[..., 1] = 128
    atlas_n[..., 2] = 255
    atlas_n[..., 3] = 96

    def _bleed(buf: np.ndarray, rx: int, ry: int, s: int) -> None:
        if pad <= 0:
            return
        buf[ry - pad:ry, rx:rx + s] = buf[ry:ry + 1, rx:rx + s]
        buf[ry + s:ry + s + pad, rx:rx + s] = buf[ry + s - 1:ry + s, rx:rx + s]
        buf[ry - pad:ry + s + pad, rx - pad:rx] = buf[ry - pad:ry + s + pad, rx:rx + 1]
        buf[ry - pad:ry + s + pad, rx + s:rx + s + pad] = buf[ry - pad:ry + s + pad, rx + s - 1:rx + s]

    uv_map: dict[str, tuple[float, float, float, float]] = {}
    for key, (rx, ry, s) in rects.items():
        d_arr = diffuse_maps[key]
        if d_arr.ndim == 2:
            d_rgb = np.repeat(d_arr[..., None], 3, axis=2).astype(np.uint8)
            d_a = np.full(d_rgb.shape[:2], 255, dtype=np.uint8)
        elif d_arr.shape[2] >= 4:
            d_rgba = _dilate_rgba_color(d_arr[..., :4].astype(np.uint8))
            d_rgb = d_rgba[..., :3]
            d_a = d_rgba[..., 3]
        else:
            d_rgb = d_arr[..., :3].astype(np.uint8)
            d_a = np.full(d_rgb.shape[:2], 255, dtype=np.uint8)
        rgb_tile = np.asarray(Image.fromarray(d_rgb, 'RGB').resize((s, s), Image.LANCZOS), dtype=np.uint8)
        a_tile = (
            np.asarray(Image.fromarray(d_a, 'L').resize((s, s), Image.LANCZOS), dtype=np.uint8)
            if int(d_a.min()) < 250
            else np.full((s, s), 255, dtype=np.uint8)
        )
        atlas_d[ry:ry + s, rx:rx + s, :3] = rgb_tile
        atlas_d[ry:ry + s, rx:rx + s, 3] = a_tile
        _bleed(atlas_d, rx, ry, s)

        n_tile = np.empty((s, s, 4), dtype=np.uint8)
        n_tile[..., 0] = 128
        n_tile[..., 1] = 128
        n_tile[..., 2] = 255
        n_tile[..., 3] = 96
        n_src = normal_maps.get(key)
        if n_src is not None and n_src.ndim == 3 and n_src.shape[2] >= 3:
            nr = np.asarray(Image.fromarray(n_src[..., :3].astype(np.uint8), 'RGB').resize((s, s), Image.BILINEAR), dtype=np.uint8)
            # Re-normalize Z if BC5/RG-only normal had flat B channel
            if float(nr[..., 2].mean()) < 64.0:
                nx = nr[..., 0].astype(np.float32) / 127.5 - 1.0
                ny = nr[..., 1].astype(np.float32) / 127.5 - 1.0
                nz = np.sqrt(np.clip(1.0 - nx * nx - ny * ny, 0.0, 1.0))
                nr[..., 2] = np.clip((nz * 0.5 + 0.5) * 255.0, 0, 255).astype(np.uint8)
            n_tile[..., :3] = nr
        g_src = gloss_maps.get(key)
        if g_src is not None:
            g_ch = g_src[..., 0] if g_src.ndim == 3 else g_src
            g_tile = np.asarray(Image.fromarray(g_ch.astype(np.uint8), 'L').resize((s, s), Image.BILINEAR), dtype=np.uint8)
            n_tile[..., 3] = g_tile
        atlas_n[ry:ry + s, rx:rx + s] = n_tile
        _bleed(atlas_n, rx, ry, s)

        uv_map[key] = (
            (rx + 0.5) / atlas_w,
            (ry + 0.5) / atlas_h,
            (s - 1.0) / atlas_w,
            (s - 1.0) / atlas_h,
        )
    return Image.fromarray(atlas_d, 'RGBA'), Image.fromarray(atlas_n, 'RGBA'), uv_map


class _GameMapArchive:
    """Read-only loader for r_ui.wad (WTOC v2) and root.lodpack."""

    def __init__(self, wad_dir: Path | None = None):
        self.wad_dir = Path(wad_dir) if wad_dir else paths.wad_dir()
        self.wad_path = self.wad_dir / 'r_ui.wad'
        self.lod_path = self.wad_dir / 'root.lodpack'
        if not self.wad_path.is_file() or not self.lod_path.is_file():
            raise FileNotFoundError(f'Missing r_ui.wad or root.lodpack in {self.wad_dir}')

        import lz4.frame
        self.raw = lz4.frame.decompress(self.wad_path.read_bytes())
        hdr = struct.unpack_from('<16I', self.raw, 0)
        if hdr[0] != 0x434F5457:
            raise ValueError('Invalid r_ui.wad WTOC magic')
        count = hdr[2]
        self.entries: list[dict[str, Any]] = []
        self.by_name: dict[str, list[dict[str, Any]]] = {}
        for i in range(count):
            o = 0x40 + i * 0x90
            tag, flags, size = struct.unpack_from('<HHI', self.raw, o)
            name = self.raw[o + 0x18:o + 0x58].split(b'\x00', 1)[0].decode('latin1', 'replace')
            align, fl2 = struct.unpack_from('<II', self.raw, o + 0x68)
            _, doff = struct.unpack_from('<QQ', self.raw, o + 0x70)
            rec = {
                'idx': i, 'tag': tag, 'flags': flags, 'size': size,
                'name': name, 'pool': (fl2 >> 24) & 0xFF, 'doff': doff,
            }
            self.entries.append(rec)
            self.by_name.setdefault(name, []).append(rec)

        with self.lod_path.open('rb') as lf:
            pack_count, sub_count, _, _ = struct.unpack('<IIII', lf.read(16))
            self.lod_packs = list(struct.iter_unpack('<QQII', lf.read(pack_count * 24)))
            self.lod_subs: dict[int, tuple[int, int, int, int]] = {}
            for pidx, off_p, h, sz, fl in struct.iter_unpack('<IIQII', lf.read(sub_count * 24)):
                self.lod_subs[h] = (pidx, off_p, sz, fl)

        self._lod_cache: dict[int, bytes] = {}
        self._mat_tx_cache: dict[str, list[str]] = {}
        self._tex_info_cache: dict[str, tuple[dict, np.ndarray] | None] = {}

    def read_lod(self, lod_hash: int) -> bytes | None:
        if lod_hash in self._lod_cache:
            return self._lod_cache[lod_hash]
        rec = self.lod_subs.get(lod_hash)
        if not rec:
            return None
        pidx, off_p, sz, _ = rec
        if pidx >= len(self.lod_packs):
            return None
        pstart = self.lod_packs[pidx][0]
        with self.lod_path.open('rb') as lf:
            lf.seek(pstart + off_p)
            blob = lf.read(sz)
        self._lod_cache[lod_hash] = blob
        return blob

    def find_mesh_offset(self, me: dict[str, Any]) -> int | None:
        pos = 0x4400000
        cands = []
        while True:
            p = self.raw.find(_MESH_MAGIC, pos)
            if p == -1:
                break
            if struct.unpack_from('<I', self.raw, p + 0x1C)[0] == me['size']:
                cands.append(p)
            pos = p + 16
        if not cands:
            return None
        if len(cands) > 1:
            cands.sort(key=lambda p: abs((p - me['doff']) - 0x4534E66))
        return cands[0]

    def find_mat_table(self, mat60: dict[str, Any]) -> list[str]:
        needle = mat60['name'].encode('latin1')
        pos = 0x455D40
        best: list[str] = []
        while True:
            p = self.raw.find(needle, pos)
            if p == -1:
                break
            blk = self.raw[p - 0x10:p - 0x10 + mat60['size']]
            mats = [m.decode('latin1') for m in re.findall(rb'MAT_[0-9A-F]{16}', blk)]
            if len(mats) > len(best):
                best = mats
            pos = p + 1
        return best

    def resolve_mat_textures(self, mat_name: str) -> list[str]:
        if mat_name in self._mat_tx_cache:
            return self._mat_tx_cache[mat_name]
        cands = [e for e in self.by_name.get(mat_name, []) if e['size'] > 0 and e['tag'] == 1]
        txs: list[str] = []
        if cands:
            idx = cands[0]['idx']
            if idx + 1 < len(self.entries):
                nxt = self.entries[idx + 1]
                if nxt['tag'] == 60 and nxt['name'].startswith('TX_'):
                    pat = nxt['name'].encode('latin1')
                    pos = 0x455D40
                    while True:
                        p = self.raw.find(pat, pos)
                        if p == -1:
                            break
                        if self.raw[p - 16:p - 8] == b'TXET\x00ERU':
                            blk = self.raw[p - 16:p - 16 + nxt['size']]
                            txs = [x.decode('latin1') for x in re.findall(rb'TX_[A-Za-z0-9_]+', blk)]
                            break
                        pos = p + 1
                    if not txs:
                        txs = [nxt['name']]
        self._mat_tx_cache[mat_name] = txs
        return txs

    def find_inline_gpu(self, gpu_e: dict[str, Any], mdata: bytes, offs: list[int]) -> int | None:
        nparts = len(offs)
        target = None
        for pi in range(nparts):
            pe = offs[pi + 1] if pi + 1 < nparts else len(mdata)
            c = mdata[offs[pi]:pe]
            lh = struct.unpack_from('<Q', c, 0x68)[0] if len(c) >= 0x70 else 0
            if lh in self.lod_subs:
                continue
            ex, ey, ez, cx, cy, cz = struct.unpack_from('<6f', c, 0x10)
            u = struct.unpack_from('<16I', c, 0x28)
            nv, nidx, vb_off, ib_off = u[7], u[13], u[5], u[2]
            if nv >= 12 and nidx >= 12 and ib_off + nidx * 2 <= gpu_e['size']:
                target = (cx, cy, cz, ex, ey, ez, nv, nidx, vb_off, ib_off)
                break
        if target is None:
            return None
        cx, cy, cz, ex, ey, ez, nv, nidx, vb_off, ib_off = target
        for shift in (0, 2):
            lo = 0x4600000 + shift
            hi = ((len(self.raw) - shift) // 4) * 4 + shift
            arr_f = np.frombuffer(self.raw[lo:hi], '<f4')
            mask = (
                (arr_f[:-2] >= cx - ex - 0.05) & (arr_f[:-2] <= cx + ex + 0.05)
                & (arr_f[1:-1] >= cy - ey - 0.05) & (arr_f[1:-1] <= cy + ey + 0.05)
                & (arr_f[2:] >= cz - ez - 0.05) & (arr_f[2:] <= cz + ez + 0.05)
            )
            hits = np.where(mask)[0]
            if len(hits) < 4:
                continue
            d = np.diff(hits)
            ok = np.where((d[:-2] == 3) & (d[1:-1] == 3) & (d[2:] == 3))[0]
            for k in ok:
                if k > 0 and hits[k] - hits[k - 1] == 3:
                    continue
                g_start = lo + int(hits[k]) * 4 - vb_off
                if g_start < 0 or g_start + gpu_e['size'] > len(self.raw):
                    continue
                ib = np.frombuffer(self.raw[g_start + ib_off:g_start + ib_off + nidx * 2], '<u2')
                if len(ib) == nidx and int(ib.max()) == nv - 1:
                    return g_start
        return None

    def extract_textures(self, names: list[str]) -> dict[str, tuple[dict, np.ndarray] | None]:
        need = [n for n in names if n not in self._tex_info_cache and '_' in n]
        if need:
            # Guard against malformed texture names without valid 16-hex hash suffix
            valid_need = []
            for n in need:
                suf = n.rsplit('_', 1)[-1]
                if len(suf) >= 8 and all(ch in '0123456789abcdefABCDEF' for ch in suf):
                    valid_need.append(n)
                else:
                    self._tex_info_cache[n] = None
            if valid_need:
                got = gow_texpack.extract(valid_need, texpack_dir=self.wad_dir)
                for n in valid_need:
                    self._tex_info_cache[n] = got.get(n)
        return {n: self._tex_info_cache.get(n) for n in names}

    def pick_diffuse_texture(self, tx_names: list[str]) -> tuple[str, np.ndarray] | None:
        if not tx_names:
            return None
        # Filter out obvious non-diffuse names first
        for t in tx_names:
            if any(t.startswith(p) for p in SKIP_TX_PREFIXES):
                return None
            if '_h_' in t and '_poi_' not in t:
                return None

        def _to_rgba(got: tuple[dict, np.ndarray]) -> np.ndarray:
            meta, arr = got
            rgb = arr[..., :3].astype(np.uint8)
            # Only BC2/BC3/BC7 (DXGI 75/78/99) carry true 8-bit opacity cutouts;
            # BC1 (DXGI 72) uses 3-color mode a=0 for opaque pure-black pixels and must stay solid.
            if meta.get('dxgi') in (75, 78, 99) and arr.shape[2] >= 4 and int(arr[..., 3].min()) < 250:
                alpha = arr[..., 3].astype(np.uint8)
            else:
                alpha = np.full(rgb.shape[:2], 255, dtype=np.uint8)
            return np.dstack([rgb, alpha])

        # Priority 1: explicit diffuse naming (_0d_, _d_, basecolor, _albedo)
        for t in tx_names:
            tl = t.lower()
            if '_0d_' in tl or '_d_' in tl or 'basecolor' in tl or '_albedo' in tl:
                got = self.extract_textures([t]).get(t)
                if got is not None and got[1].ndim == 3:
                    return t, _to_rgba(got)
        # Priority 2: sRGB albedo/emissive-albedo (_gen_0e_ in Svartalfheim/Alfheim POIs) & truncated 36-char names
        # Diffuse albedo textures in root.texpack are ALWAYS sRGB (BC1_SRGB=72, BC2_SRGB=75, BC3_SRGB=78, BC7_SRGB=99)
        cands = [
            t for t in tx_names
            if not any(s in t.lower() for s in ('_0n_', '_0g_', '_0ao_', '_0h_', '_n_', '_ao_', '_m_', 'normal', 'roughness', 'gloss'))
        ]
        got_map = self.extract_textures(cands)
        for t in cands:
            got = got_map.get(t)
            if got is not None and got[0].get('dxgi') in (72, 75, 78, 99) and got[1].ndim == 3:
                return t, _to_rgba(got)
        for t in cands:
            got = got_map.get(t)
            if got is not None and got[1].ndim == 3:
                return t, _to_rgba(got)
        return None

    def pick_pbr_maps(
        self, tx_names: list[str], diffuse_key: str,
    ) -> tuple[np.ndarray | None, np.ndarray | None, np.ndarray | None]:
        """Extract matching (tangent_normal_rgb, gloss_u8, ao_u8) maps for a POI material."""
        others = [t for t in dict.fromkeys(tx_names) if t != diffuse_key]
        if not others:
            return None, None, None
        got_map = self.extract_textures(others)
        norm_arr: np.ndarray | None = None
        gloss_arr: np.ndarray | None = None
        ao_arr: np.ndarray | None = None

        for t in others:
            tl = t.lower()
            got = got_map.get(t)
            if got is None:
                continue
            meta, arr = got
            dxgi = meta.get('dxgi')
            if norm_arr is None and ('_0n_' in tl or '_n_' in tl or 'normal' in tl):
                if arr.ndim == 3:
                    norm_arr = arr[..., :3]
                    continue
            if gloss_arr is None and ('_0g_' in tl or 'gloss' in tl or 'roughness' in tl):
                if arr.ndim == 3:
                    gloss_arr = np.maximum(arr[..., 0], arr[..., 1]) if arr.shape[2] >= 2 else arr[..., 0]
                else:
                    gloss_arr = arr
                continue
            if ao_arr is None and ('_0ao_' in tl or '_ao_' in tl):
                ao_arr = arr[..., 0] if arr.ndim == 3 else arr
                continue
            # Truncated 36-char names: linear BC7 (98) with high blue mean is tangent-space normal
            if norm_arr is None and dxgi == 98 and arr.ndim == 3 and float(arr[..., 2].mean()) > 175.0:
                norm_arr = arr[..., :3]
                continue
            # Linear BC4 (80) or BC1 (71) without _0h_/_0ao_ is gloss/roughness
            if gloss_arr is None and dxgi in (71, 80) and '_0h_' not in tl and '_0ao_' not in tl:
                gloss_arr = arr[..., 0] if arr.ndim == 3 else arr
        return norm_arr, gloss_arr, ao_arr

    def extract_realm_decals(self, realm: str, me_idx: int, p0_base: int) -> list[dict[str, Any]]:
        """Extract DCL_* map paint decals belonging to a realm."""
        # Realm TOC block spans from me_idx to its goProto<Realm> (within ~600 entries)
        decals: list[dict[str, Any]] = []
        end_idx = min(len(self.entries), me_idx + 620)
        for j in range(me_idx, end_idx):
            e = self.entries[j]
            if j > me_idx + 15 and e['name'].startswith('MESH_') and e['pool'] == 0:
                break
            if not e['name'].startswith('DCL_') or e['pool'] != 0:
                continue
            off = p0_base + e['doff']
            if off < 0 or off + e['size'] > len(self.raw):
                continue
            chunk = self.raw[off:off + e['size']]
            zi = chunk.find(b':/int9/')
            if zi <= 0:
                continue
            zi -= 1
            zstr = chunk[zi:].split(b'\x00', 1)[0].decode('latin1', 'replace')
            m_off = zi + len(zstr) + 1
            if m_off + 64 > len(chunk):
                continue
            mat = struct.unpack_from('<16f', chunk, m_off)
            if not all(math.isfinite(v) for v in mat):
                continue
            sx = math.hypot(mat[0], mat[2])
            sz = math.hypot(mat[8], mat[10])
            if sx <= 0.01 or sz <= 0.01 or sx > 12.0 or sz > 12.0:
                continue
            decals.append({
                'name': e['name'],
                'mat': zstr.rsplit('/', 1)[-1].lower(),
                'x': mat[12], 'y': mat[13], 'z': mat[14],
                'sx': sx, 'sz': sz,
                'rot': math.atan2(mat[2], mat[0]),
            })
        return decals


def _realm_world_frame(realm: str) -> dict[str, Any]:
    meta = realm_height_meta(realm)
    if meta is None:
        raise ValueError(f'Unknown realm {realm}')
    m0 = meta['merc0']
    sx = max(1e-6, m0['x_max'] - m0['x_min'])
    sy = max(1e-6, m0['y_max'] - m0['y_min'])
    m_to_w = WORLD_SPAN / max(sx, sy)
    return {
        'meta': meta,
        'merc0': m0,
        'm_to_w': m_to_w,
        'world_w': sx * m_to_w,
        'world_h': sy * m_to_w,
        'height_amp': float(meta['height_scale']) * WORLD_SPAN,
    }


def _load_georef() -> dict[str, Any]:
    if not GEOREF_PATH.is_file():
        return {}
    return json.loads(GEOREF_PATH.read_text(encoding='utf-8'))


def _bilinear_sample_2d(arr: np.ndarray, tx: np.ndarray, ty: np.ndarray) -> np.ndarray:
    h, w = arr.shape[:2]
    fx = tx - 0.5
    fy = ty - 0.5
    x0 = np.floor(fx).astype(np.int64)
    y0 = np.floor(fy).astype(np.int64)
    wx = (fx - x0).astype(np.float32)
    wy = (fy - y0).astype(np.float32)
    if arr.ndim == 3:
        wx = wx[..., None]
        wy = wy[..., None]

    def at(yy, xx):
        return arr[np.clip(yy, 0, h - 1), np.clip(xx, 0, w - 1)].astype(np.float32)

    return (
        at(y0, x0) * (1.0 - wx) * (1.0 - wy)
        + at(y0, x0 + 1) * wx * (1.0 - wy)
        + at(y0 + 1, x0) * (1.0 - wx) * wy
        + at(y0 + 1, x0 + 1) * wx * wy
    )


def _tex_to_world_fn(map_id: str, georef: dict[str, Any], frame: dict[str, Any]):
    """Build affine 2x3 mapping from 2048x2048 texture (tx, ty) -> WebGL2 (wx, wz)."""
    ref = georef[map_id]
    G = np.asarray(ref['merc0_to_texture'], dtype=np.float64)
    A = G[:, :2]
    b = G[:, 2]
    A_inv = np.linalg.inv(A)
    m0 = frame['merc0']
    m_to_w = frame['m_to_w']
    # gx = A_inv[0,0]*(tx-b0) + A_inv[0,1]*(ty-b1)
    # wx = (gx - x_min) * m_to_w
    M = A_inv * m_to_w
    t = (-A_inv @ b - np.array([m0['x_min'], m0['y_min']], dtype=np.float64)) * m_to_w
    return M, t  # [wx, wz] = [tx, ty] @ M.T + t


def _blur_f32(arr: np.ndarray, radius: float) -> np.ndarray:
    """Fast Gaussian blur of a [0..1] float32 2D array without requiring OpenCV."""
    try:
        import cv2
        return cv2.GaussianBlur(arr.astype(np.float32), (0, 0), float(radius))
    except ImportError:
        u8 = np.clip(arr * 255.0, 0, 255).astype(np.uint8)
        return np.asarray(Image.fromarray(u8, 'L').filter(ImageFilter.GaussianBlur(radius=radius)), dtype=np.float32) / 255.0


def _tile_to_size(arr: np.ndarray, tile_px: int, out_size: int, rot90: bool = False) -> np.ndarray:
    """Resize a material texture to tile_px and seamlessly tile it to out_size x out_size."""
    if rot90:
        arr = np.rot90(arr, 1)
    if arr.ndim == 2:
        t = np.asarray(Image.fromarray(arr.astype(np.uint8), 'L').resize((tile_px, tile_px), Image.BILINEAR), dtype=np.float32) / 255.0
        reps = (out_size + tile_px - 1) // tile_px
        return np.tile(t, (reps, reps))[:out_size, :out_size]
    t = np.asarray(Image.fromarray(arr[..., :3].astype(np.uint8), 'RGB').resize((tile_px, tile_px), Image.BILINEAR), dtype=np.float32) / 255.0
    reps = (out_size + tile_px - 1) // tile_px
    return np.tile(t, (reps, reps, 1))[:out_size, :out_size, :]


def compute_raymarched_terrain_shadow(
    en: np.ndarray,
    M: np.ndarray,
    height_amp: float,
    sun_world: tuple[float, float, float] = (-0.52, 0.74, -0.42),
    steps: int = 36,
) -> np.ndarray:
    """Compute crisp soft-penumbra directional cliff self-shadows directly on a BC6H heightmap.

    Marches from each texel toward the sun in exact texture coordinates derived from M^-1,
    so shadows cast southeast in WebGL2 world space across all realms (including rotated ones).
    """
    h, w = en.shape
    lx, ly, lz = sun_world
    l_len = math.sqrt(lx * lx + ly * ly + lz * lz) or 1.0
    lx, ly, lz = lx / l_len, ly / l_len, lz / l_len
    h_len = math.hypot(lx, lz) or 1.0
    dir_w = np.array([lx / h_len, lz / h_len], dtype=np.float64)
    M_inv = np.linalg.inv(M)
    step_t = M_inv @ dir_w  # texture pixels per 1.0 world unit toward the sun
    tan_elev = (ly / h_len) / max(float(height_amp), 1.0)  # normalized height rise per world unit

    # Downsample to 1024 for fast raymarching (~0.18s) then upsample crisply back to full size
    march_n = min(1024, h)
    scale_m = march_n / float(h)
    en_m = np.asarray(Image.fromarray(en.astype(np.float32), 'F').resize((march_n, march_n), Image.BILINEAR), dtype=np.float32) if march_n != h else en

    yy, xx = np.mgrid[0:march_n, 0:march_n].astype(np.float32)
    occ = np.zeros((march_n, march_n), dtype=np.float32)
    # Geometric world-unit distances from 2.5 to 230 world units
    dists = np.geomspace(2.5, 230.0, steps).astype(np.float32)
    stx = float(step_t[0] * scale_m)
    sty = float(step_t[1] * scale_m)

    for d_w in dists:
        sx = np.clip(np.rint(xx + stx * d_w).astype(np.int32), 0, march_n - 1)
        sy = np.clip(np.rint(yy + sty * d_w).astype(np.int32), 0, march_n - 1)
        diff = en_m[sy, sx] - (en_m + float(d_w * tan_elev))
        penumbra = np.clip(diff * (22.0 / (1.0 + float(d_w) * 0.022)), 0.0, 1.0)
        np.maximum(occ, penumbra, out=occ)

    sh = 1.0 - np.clip(occ, 0.0, 1.0) * 0.72
    sh = _blur_f32(sh, 1.1)
    if march_n != h:
        sh = np.asarray(Image.fromarray(sh, 'F').resize((w, h), Image.BILINEAR), dtype=np.float32)
    return np.clip(sh, 0.24, 1.0).astype(np.float32)


def _render_map_id_layers(
    arc: _GameMapArchive,
    realm: str,
    map_id: str,
    h_raw: np.ndarray,
    decals: list[dict[str, Any]],
    M: np.ndarray,
    height_amp: float,
    size: int = 2048,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Render 1:1 Santa Monica Studio wood-carved diorama layers in TX_<realm>_h space.

    Returns:
      - albedo_u8 (size, size, 3): painted biome + real TX_woodbase / TX_slab / TX_wood_cell_edge + decals
      - norm_sh_u8 (size, size, 4): RGB = world-space 2K normal (BC6H + wood chisel + paint + frost), A = raymarched sun shadow * AO
      - water_mask_u8 (size, size, 3): R = water/glossy ice reflectivity, G = lava/emissive glow, B = surface smoothness
    """
    style = SURFACE_STYLES.get(realm, SURFACE_STYLES['midgard'])
    elev = 1.0 - h_raw.astype(np.float32)
    q0, q1 = np.quantile(elev, [0.005, 0.995])
    en = np.clip((elev - q0) / max(float(q1 - q0), 1e-6), 0.0, 1.0).astype(np.float32)

    if en.shape[0] != size:
        en = np.asarray(Image.fromarray(en, 'F').resize((size, size), Image.BILINEAR), dtype=np.float32)

    # 1. Exact world-space height gradients & 2K surface normals from full BC6H precision
    M_inv = np.linalg.inv(M)
    dh_dty, dh_dtx = np.gradient(en * float(height_amp))
    dh_dwx = (M_inv[0, 0] * dh_dtx + M_inv[1, 0] * dh_dty).astype(np.float32)
    dh_dwz = (M_inv[0, 1] * dh_dtx + M_inv[1, 1] * dh_dty).astype(np.float32)
    grad_mag = np.hypot(dh_dwx, dh_dwz)
    slope = np.clip(grad_mag / 1.45, 0.0, 1.0).astype(np.float32)

    # Multi-scale local cavity AO & crisp carved ridge highlights
    en_blur_s = _blur_f32(en, 2.5)
    en_blur_m = _blur_f32(en, 14.0)
    cavity_ao = np.clip(1.0 + (en - en_blur_s) * 3.4 + (en - en_blur_m) * 1.4, 0.62, 1.08)
    ridge = np.clip((en - en_blur_s) * 8.0, 0.0, 1.0)

    # 36-step raymarched directional cliff self-shadow directly on the 2K BC6H heightmap!
    ray_shadow = compute_raymarched_terrain_shadow(en, M, height_amp)

    # 2. Load REAL game carved-wood, chisel-gouge, stone-slab, frost, and oil-paint textures
    mat_got = arc.extract_textures(list(TERRAIN_MATERIAL_TEXTURES.values()))

    def _mat_tile(key: str, tile_px: int, rot90: bool = False) -> np.ndarray | None:
        g = mat_got.get(TERRAIN_MATERIAL_TEXTURES[key])
        if g is None:
            return None
        return _tile_to_size(g[1], tile_px, size, rot90=rot90)

    wood_d = _mat_tile('wood_d', 256, rot90=True)
    wood_n = _mat_tile('wood_n', 256, rot90=True)
    wood_ao = _mat_tile('wood_ao', 256, rot90=True)
    wood_rough_d = _mat_tile('wood_rough_d', 160, rot90=True)
    wood_rough_n = _mat_tile('wood_rough_n', 160, rot90=True)
    cell_n = _mat_tile('cell_n', 176, rot90=False)
    cell_edge = _mat_tile('cell_edge', 176, rot90=False)
    slab_d = _mat_tile('slab_d', 384, rot90=False)
    slab_n = _mat_tile('slab_n', 384, rot90=False)
    frost_a = _mat_tile('frost_a', 224, rot90=False)
    frost_n = _mat_tile('frost_n', 224, rot90=False)
    paint_n = _mat_tile('paint_n', 256, rot90=False)

    # 3. Compose authentic carved-wood + painted-diorama albedo (NO double-darkened hillshade!)
    c_lo = np.array(style['low'], dtype=np.float32)
    c_mi = np.array(style['mid'], dtype=np.float32)
    c_hi = np.array(style['high'], dtype=np.float32)
    c_cl = np.array(style['cliff'], dtype=np.float32)
    t_mid = np.clip(en * 1.45, 0.0, 1.0)[..., None]
    t_hi = np.clip((en - 0.52) / 0.48, 0.0, 1.0)[..., None]
    paint_rgb = c_lo + (c_mi - c_lo) * t_mid
    paint_rgb = paint_rgb + (c_hi - paint_rgb) * (t_hi * 0.72)

    # Real carved base material (TX_slab_d for Helheim stone, TX_woodbase_d + TX_wood_rough_04_d_grey for wood realms)
    if realm == 'helheim' and slab_d is not None:
        base_mat = slab_d * 255.0
        grain_luma = (base_mat.mean(axis=2, keepdims=True) / 160.0)
    elif wood_d is not None:
        base_mat = wood_d * 255.0
        if wood_rough_d is not None:
            rough_luma = wood_rough_d.mean(axis=2, keepdims=True) / 0.635
            grain_luma = (base_mat.mean(axis=2, keepdims=True) / 156.0) * 0.50 + rough_luma * 0.50
            base_mat = base_mat * 0.68 + (wood_rough_d * 225.0) * 0.32
        else:
            grain_luma = (base_mat.mean(axis=2, keepdims=True) / 156.0)
    else:
        base_mat = np.full((size, size, 3), 160.0, dtype=np.float32)
        grain_luma = np.ones((size, size, 1), dtype=np.float32)

    # Crisp fine vertical wood-grain showing through the matte top paint coat (signature GoWR diorama look!)
    rgb = paint_rgb * (0.82 + 0.18 * grain_luma)
    if wood_ao is not None and realm != 'helheim':
        rgb *= (0.88 + 0.12 * wood_ao[..., None])

    # Crystalline snow frost texture on icy realms (Midgard, Niflheim, Helheim)
    if frost_a is not None and realm in ('midgard', 'niflheim', 'helheim'):
        fr_v = frost_a.mean(axis=2, keepdims=True)
        flat_m = np.clip(1.0 - slope * 2.4, 0.0, 1.0)[..., None]
        rgb += (fr_v - 0.54) * (18.0 * flat_m)

    # Steep chiseled cliffs strip away paint to expose real carved wood/stone + sharp gouged chisel facet rims!
    cliff_w = np.clip((slope - 0.085) / 0.28, 0.0, 1.0)[..., None]
    carved_cliff = (c_cl * 0.54 + base_mat * 0.46) * (0.80 + 0.26 * grain_luma)
    if cell_edge is not None:
        ce_gray = cell_edge.mean(axis=2, keepdims=True) if cell_edge.ndim == 3 else cell_edge[..., None]
        edge_hi = np.clip((ce_gray - 0.22) * 1.45, 0.0, 1.0)
        carved_cliff = carved_cliff + edge_hi * np.array([26.0, 27.0, 29.0], dtype=np.float32)
    rgb = rgb * (1.0 - cliff_w * 0.84) + carved_cliff * (cliff_w * 0.84)

    # Crisp painted snow/stone highlight along carved cliff rims & mountain crests
    rgb += ridge[..., None] * np.array([22.0, 23.0, 26.0], dtype=np.float32)

    # 4. Real game texture masks (water, ice cracks, lava, navpaths, underground paths)
    masks_cfg = REALM_MASKS.get(map_id, {})
    all_tx = [t for lst in masks_cfg.values() for t in lst]
    got_masks = arc.extract_textures(all_tx) if all_tx else {}

    def _mask_2d(key: str) -> np.ndarray | None:
        acc = None
        for t in masks_cfg.get(key, []):
            got = got_masks.get(t)
            if got is None:
                continue
            arr = got[1]
            ch = arr[..., 0] if arr.ndim == 3 else arr
            m = np.asarray(Image.fromarray(ch.astype(np.uint8), 'L').resize((size, size), Image.BILINEAR), dtype=np.float32) / 255.0
            acc = m if acc is None else np.maximum(acc, m)
        return acc

    def _stamp_decal_mask(mask_tx_list: list[str], decal_substr: str) -> np.ndarray | None:
        if not decals or map_id not in QUAD_FOOTPRINTS or not mask_tx_list:
            return None
        d_hits = [d for d in decals if decal_substr in d['mat']]
        if not d_hits:
            return None
        cx_q, cz_q, hx_q, hz_q = QUAD_FOOTPRINTS[map_id]
        canvas = np.zeros((size, size), dtype=np.float32)
        for idx_t, t in enumerate(mask_tx_list):
            got = got_masks.get(t)
            if got is None:
                continue
            arr = got[1]
            ch = (arr[..., 0] if arr.ndim == 3 else arr).astype(np.uint8)
            d = d_hits[min(idx_t, len(d_hits) - 1)]
            ux = (d['x'] - cx_q) / (2.0 * hx_q) + 0.5
            uz = (d['z'] - cz_q) / (2.0 * hz_q) + 0.5
            w_px = max(8, int(round((d['sx'] / (2.0 * hx_q)) * size)))
            h_px = max(8, int(round((d['sz'] / (2.0 * hz_q)) * size)))
            x0 = int(round(ux * size - w_px * 0.5))
            y0 = int(round(uz * size - h_px * 0.5))
            patch = np.asarray(Image.fromarray(ch, 'L').resize((w_px, h_px), Image.BILINEAR), dtype=np.float32) / 255.0
            sx0, sy0 = max(0, -x0), max(0, -y0)
            dx0, dy0 = max(0, x0), max(0, y0)
            cw = min(w_px - sx0, size - dx0)
            ch_h = min(h_px - sy0, size - dy0)
            if cw > 0 and ch_h > 0:
                canvas[dy0:dy0 + ch_h, dx0:dx0 + cw] = np.maximum(
                    canvas[dy0:dy0 + ch_h, dx0:dx0 + cw],
                    patch[sy0:sy0 + ch_h, sx0:sx0 + cw],
                )
        return canvas

    # Dynamic WebGL2 shader surface mask channels: R=water/ice reflect, G=lava/emissive, B=gloss
    wm_water = np.zeros((size, size), dtype=np.float32)
    wm_glow = np.zeros((size, size), dtype=np.float32)
    wm_gloss = np.full((size, size), 0.14, dtype=np.float32)

    # Midgard frozen Lake of Nine: crisp snow-dusted wood-grain ice + localized luminous cyan channels + deep sapphire pools
    if style.get('is_ice_lake'):
        lo_b, hi_b = style['lake_h_band']
        flat_lake = ((en >= lo_b) & (en <= hi_b) & (slope < 0.085)).astype(np.float32)
        flat_lake = _blur_f32(flat_lake, 2.0)
        lake_m = _stamp_decal_mask(masks_cfg.get('lake', []), 'lake')
        ice_w = flat_lake * 0.12
        if lake_m is not None:
            ice_w = np.clip(ice_w + lake_m * flat_lake * 0.76, 0.0, 0.88)
        ice_col = np.array(style['water'], dtype=np.float32)
        foam_col = np.array(style['foam'], dtype=np.float32)
        cracks_m = _mask_2d('ice_cracks')
        if cracks_m is not None:
            cr_small = np.asarray(Image.fromarray((cracks_m * 255).astype(np.uint8), 'L').resize((256, 256), Image.BILINEAR), dtype=np.float32) / 255.0
            tiled = np.tile(cr_small, (size // 256, size // 256))
            ice_surface = ice_col * (0.90 + 0.16 * tiled[..., None]) + foam_col * (np.clip(tiled - 0.44, 0.0, 1.0)[..., None] * 0.68)
            wm_glow = np.maximum(wm_glow, np.clip(tiled - 0.52, 0.0, 1.0) * ice_w * 0.40)
        else:
            ice_surface = ice_col
        snow_ice = rgb * 0.34 + ice_surface * 0.66
        rgb = rgb * (1.0 - ice_w[..., None]) + snow_ice * ice_w[..., None]
        wm_water = np.maximum(wm_water, ice_w * 0.52)
        wm_gloss = np.maximum(wm_gloss, ice_w * 0.68)

        # Deep crystalline sapphire-blue pools inside crater depressions (Raider Keep / King's Grave / Oarsmen)
        if 'deep_ice' in style:
            deep_m = ((en >= 0.03) & (en < lo_b) & (slope < 0.16)).astype(np.float32)
            deep_m = _blur_f32(deep_m, 2.0)
            dcol = np.array(style['deep_ice'], dtype=np.float32)
            dw = np.clip(deep_m * 0.90, 0.0, 0.92)[..., None]
            rgb = rgb * (1.0 - dw) + dcol * dw
            wm_water = np.maximum(wm_water, deep_m * 0.94)
            wm_gloss = np.maximum(wm_gloss, deep_m * 0.94)

    # Liquid water masks (Svartalfheim, Vanaheim, Alfheim, Asgard, Jotunheim)
    water_m = _mask_2d('water')
    if water_m is not None:
        if float(water_m.mean()) > 0.65:
            water_m = 1.0 - water_m
        wcol = np.array(style['water'], dtype=np.float32)
        ww = np.clip(water_m * 1.18, 0.0, 0.94)[..., None]
        rgb = rgb * (1.0 - ww) + wcol * ww
        wm_water = np.maximum(wm_water, np.clip(water_m * 1.2, 0.0, 1.0))
        wm_gloss = np.maximum(wm_gloss, np.clip(water_m * 1.1, 0.0, 0.95))
        edge_m = _mask_2d('wateredge')
        if edge_m is not None:
            if float(edge_m.mean()) > 0.5:
                edge_m = 1.0 - edge_m
            fcol = np.array(style['foam'], dtype=np.float32)
            ew = np.clip(edge_m * 0.85, 0.0, 0.85)[..., None]
            rgb = rgb * (1.0 - ew) + fcol * ew

    # Molten incandescent lava (Muspelheim)
    lava_m = _mask_2d('lava')
    if lava_m is not None:
        lcol = np.array(style['water'], dtype=np.float32)
        fcol = np.array(style['foam'], dtype=np.float32)
        lw = np.clip(lava_m * 1.25, 0.0, 0.96)[..., None]
        core = np.clip((lava_m - 0.50) / 0.50, 0.0, 1.0)[..., None]
        rgb = rgb * (1.0 - lw) + (lcol * (1.0 - core) + fcol * core) * lw
        wm_glow = np.maximum(wm_glow, np.clip(lava_m * 1.35, 0.0, 1.0))
        wm_gloss = np.maximum(wm_gloss, np.clip(lava_m * 0.8, 0.0, 0.85))

    # Carved wooden trails & footpaths: expose raw grained oak wood along navpath!
    nav_m = _mask_2d('navpath')
    if nav_m is not None:
        pcol = np.array(style['path'], dtype=np.float32)
        wood_path = pcol * 0.58 + base_mat * 0.42
        pw = np.clip(nav_m * 0.72, 0.0, 0.76)[..., None]
        rgb = rgb * (1.0 - pw) + wood_path * pw

    # Subtle glowing underground tunnel paths stamped strictly inside their decal footprint
    ug_m = _stamp_decal_mask(masks_cfg.get('underground', []), 'underground')
    if ug_m is not None:
        ucol = np.array([124.0, 188.0, 228.0], dtype=np.float32)
        uw = np.clip(ug_m * 0.34, 0.0, 0.40)[..., None]
        rgb = rgb * (1.0 - uw) + ucol * uw
        wm_glow = np.maximum(wm_glow, ug_m * 0.30)

    # 5. Stamp REAL in-game carved tree & paint brushstroke DCL_* decals at exact (pos, scale, rot)
    if decals and map_id in QUAD_FOOTPRINTS:
        cx_q, cz_q, hx_q, hz_q = QUAD_FOOTPRINTS[map_id]
        d_tx_need = [t for pair in DECAL_GAME_TEXTURES.values() for t in pair if t]
        d_got = arc.extract_textures(d_tx_need)

        def _make_sprite(key: str, tint: tuple[int, int, int] | None = None) -> Image.Image | None:
            tx_d, tx_m = DECAL_GAME_TEXTURES[key]
            gm = d_got.get(tx_m) if tx_m else None
            if gm is None:
                return None
            ma = gm[1]
            alpha = (ma[..., 0] if ma.ndim == 3 else ma).astype(np.uint8)
            gd = d_got.get(tx_d) if tx_d else None
            if gd is not None and gd[1].ndim == 3:
                col_rgb = gd[1][..., :3].astype(np.uint8)
                if col_rgb.shape[:2] != alpha.shape[:2]:
                    col_rgb = np.asarray(
                        Image.fromarray(col_rgb, 'RGB').resize((alpha.shape[1], alpha.shape[0]), Image.BILINEAR),
                        dtype=np.uint8,
                    )
            else:
                tr, tg, tb = tint or (255, 255, 255)
                col_rgb = np.empty((alpha.shape[0], alpha.shape[1], 3), dtype=np.uint8)
                col_rgb[..., 0] = tr
                col_rgb[..., 1] = tg
                col_rgb[..., 2] = tb
            return Image.fromarray(np.dstack([col_rgb, alpha]), 'RGBA')

        sp_tree_mid_1 = _make_sprite('tree_mid_1')
        sp_tree_mid_2 = _make_sprite('tree_mid_2')
        sp_tree_sva = _make_sprite('tree_sva', (68, 78, 62))
        sp_tree_nif = _make_sprite('tree_nif')

        def _tint_tree_sprite(base_sp: Image.Image | None, lo_rgb: tuple[int, int, int], hi_rgb: tuple[int, int, int]) -> Image.Image | None:
            if base_sp is None:
                return None
            arr = np.asarray(base_sp, dtype=np.float32)
            lum = (arr[..., 0] * 0.299 + arr[..., 1] * 0.587 + arr[..., 2] * 0.114) / 255.0
            t = np.clip((lum - 0.18) / 0.72, 0.0, 1.0)[..., None]
            lo_v = np.array(lo_rgb, dtype=np.float32)
            hi_v = np.array(hi_rgb, dtype=np.float32)
            out_rgb = lo_v + (hi_v - lo_v) * t
            return Image.fromarray(np.dstack([np.clip(out_rgb, 0, 255), arr[..., 3]]).astype(np.uint8), 'RGBA')

        sp_tree_van_1 = _tint_tree_sprite(sp_tree_mid_1, (38, 68, 42), (92, 128, 72)) if realm == 'vanaheim' else None
        sp_tree_van_2 = _tint_tree_sprite(sp_tree_mid_2, (34, 62, 38), (86, 122, 68)) if realm == 'vanaheim' else None

        gm_brush = d_got.get(DECAL_GAME_TEXTURES['paint_brush'][1])
        brush_mask = None
        if gm_brush is not None:
            ba = gm_brush[1]
            raw_bm = (ba[..., 0] if ba.ndim == 3 else ba).astype(np.float32)
            bh_m, bw_m = raw_bm.shape[:2]
            yy_m, xx_m = np.mgrid[0:bh_m, 0:bw_m].astype(np.float32)
            nx_m = (xx_m / max(bw_m - 1, 1) - 0.5) * 2.0
            ny_m = (yy_m / max(bh_m - 1, 1) - 0.5) * 2.0
            r2 = nx_m * nx_m + ny_m * ny_m
            # Radial ellipse falloff prevents rotated paint decals from stamping sharp rectangular quad borders
            rad_vig = np.clip(1.0 - r2 / 0.92, 0.0, 1.0) ** 2.0
            brush_mask = np.clip(raw_bm * rad_vig, 0, 255).astype(np.uint8)

        paint_layer = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        tree_layer = Image.new('RGBA', (size, size), (0, 0, 0, 0))

        for d_idx, d in enumerate(decals):
            ux = (d['x'] - cx_q) / (2.0 * hx_q) + 0.5
            uz = (d['z'] - cz_q) / (2.0 * hz_q) + 0.5
            if not (-0.1 <= ux <= 1.1 and -0.1 <= uz <= 1.1):
                continue
            px = ux * size
            py = uz * size
            w_px = max(10, int(round((d['sx'] / (2.0 * hx_q)) * size)))
            h_px = max(10, int(round((d['sz'] / (2.0 * hz_q)) * size)))
            ang = -math.degrees(d['rot'])
            ml = d['mat']

            if 'tree' in ml:
                if realm == 'svartalfheim' and sp_tree_sva is not None:
                    sp = sp_tree_sva
                elif realm == 'niflheim' and sp_tree_nif is not None:
                    sp = sp_tree_nif
                elif realm == 'vanaheim' and sp_tree_van_1 is not None:
                    sp = sp_tree_van_2 if (('02' in ml or d_idx % 3 == 0) and sp_tree_van_2 is not None) else sp_tree_van_1
                else:
                    sp = sp_tree_mid_2 if (('02' in ml or d_idx % 3 == 0) and sp_tree_mid_2 is not None) else sp_tree_mid_1
                if sp is None:
                    continue
                tw = max(12, min(160, int(round(w_px * 0.92))))
                th = max(12, min(160, int(round(h_px * 0.92))))
                stamp = sp.resize((tw, th), Image.LANCZOS)
                if abs(ang) > 0.5:
                    stamp = stamp.rotate(ang, resample=Image.BICUBIC, expand=True)
                st_arr = np.asarray(stamp, dtype=np.float32).copy()
                st_arr[..., 3] *= 0.84
                stamp = Image.fromarray(np.clip(st_arr, 0, 255).astype(np.uint8), 'RGBA')
                tree_layer.alpha_composite(stamp, (int(round(px - stamp.width * 0.5)), int(round(py - stamp.height * 0.5))))
                continue

            if 'snow' in ml or 'white' in ml:
                pcol_rgba = (244, 249, 254, 44)
            elif 'green' in ml:
                pcol_rgba = (96, 134, 94, 34)
            elif 'yellow' in ml or 'orange' in ml:
                pcol_rgba = (196, 170, 120, 32)
            elif 'red' in ml:
                pcol_rgba = (150, 124, 108, 24)
            elif 'path' in ml or 'road' in ml or 'dirt' in ml:
                pcol_rgba = (156, 140, 122, 46)
            else:
                continue

            if brush_mask is not None:
                bw = max(14, min(640, w_px))
                bh = max(14, min(640, h_px))
                bm = Image.fromarray(brush_mask, 'L').resize((bw, bh), Image.BILINEAR)
                ba_arr = (np.asarray(bm, dtype=np.float32) * (pcol_rgba[3] / 255.0)).astype(np.uint8)
                patch = np.empty((bh, bw, 4), dtype=np.uint8)
                patch[..., 0] = pcol_rgba[0]
                patch[..., 1] = pcol_rgba[1]
                patch[..., 2] = pcol_rgba[2]
                patch[..., 3] = ba_arr
                stamp = Image.fromarray(patch, 'RGBA')
                if abs(ang) > 0.5:
                    stamp = stamp.rotate(ang, resample=Image.BILINEAR, expand=True)
                paint_layer.alpha_composite(stamp, (int(round(px - stamp.width * 0.5)), int(round(py - stamp.height * 0.5))))
            else:
                draw_p = ImageDraw.Draw(paint_layer, 'RGBA')
                rx, ry = w_px * 0.44, h_px * 0.44
                draw_p.ellipse([px - rx, py - ry, px + rx, py + ry], fill=pcol_rgba)

        p_arr = np.asarray(paint_layer, dtype=np.float32)
        pa = p_arr[..., 3:4] / 255.0
        rgb = rgb * (1.0 - pa) + p_arr[..., :3] * pa

        t_arr = np.asarray(tree_layer, dtype=np.float32)
        ta = t_arr[..., 3:4] / 255.0
        rgb = rgb * (1.0 - ta) + t_arr[..., :3] * ta

    # Outer void fade
    flat_void = (en < 0.015).astype(np.float32)
    flat_void = _blur_f32(flat_void, 12.0)
    vcol = np.array(style['void'], dtype=np.float32)
    rgb = rgb * (1.0 - flat_void[..., None] * 0.92) + vcol * (flat_void[..., None] * 0.92)
    wm_water *= (1.0 - flat_void)
    wm_glow *= (1.0 - flat_void)

    # 6. Combine 2K BC6H geometric normal with REAL carved wood-chisel + paint + frost normals!
    # Keep liquid water flat so animated flowmap ripples control its normal in WebGL2
    dry_m = np.clip(1.0 - wm_water * 0.92, 0.0, 1.0)
    nx_w = -dh_dwx * dry_m
    nz_w = -dh_dwz * dry_m
    ny_w = np.ones((size, size), dtype=np.float32)

    # Hand-gouged chisel scallops strongly on carved cliffs, fine wood grain & oil-paint strokes on flats
    cw2d = cliff_w[..., 0] * dry_m
    fl2d = (1.0 - cliff_w[..., 0]) * dry_m
    if realm == 'helheim' and slab_n is not None:
        nx_w += (slab_n[..., 0] * 2.0 - 1.0) * (0.42 * dry_m)
        nz_w += (slab_n[..., 1] * 2.0 - 1.0) * (0.42 * dry_m)
    else:
        if cell_n is not None:
            nx_w += (cell_n[..., 0] * 2.0 - 1.0) * (0.14 * fl2d + 0.72 * cw2d)
            nz_w += (cell_n[..., 1] * 2.0 - 1.0) * (0.14 * fl2d + 0.72 * cw2d)
        if wood_n is not None:
            nx_w += (wood_n[..., 0] * 2.0 - 1.0) * (0.24 * dry_m)
            nz_w += (wood_n[..., 1] * 2.0 - 1.0) * (0.24 * dry_m)
        if wood_rough_n is not None:
            nx_w += (wood_rough_n[..., 0] * 2.0 - 1.0) * (0.28 * dry_m)
            nz_w += (wood_rough_n[..., 1] * 2.0 - 1.0) * (0.28 * dry_m)
    if paint_n is not None:
        nx_w += (paint_n[..., 0] * 2.0 - 1.0) * (0.22 * fl2d)
        nz_w += (paint_n[..., 1] * 2.0 - 1.0) * (0.22 * fl2d)
    if frost_n is not None and realm in ('midgard', 'niflheim', 'helheim'):
        nx_w += (frost_n[..., 0] * 2.0 - 1.0) * (0.20 * fl2d)
        nz_w += (frost_n[..., 1] * 2.0 - 1.0) * (0.20 * fl2d)

    nlen = np.sqrt(nx_w * nx_w + ny_w * ny_w + nz_w * nz_w)
    nx_w /= np.maximum(nlen, 1e-6)
    ny_w /= np.maximum(nlen, 1e-6)
    nz_w /= np.maximum(nlen, 1e-6)

    # Combined raymarched directional cliff shadow * crevice AO stored in terrain_n Alpha channel!
    sh_ao = np.clip(ray_shadow * cavity_ao, 0.16, 1.0)
    norm_sh = np.empty((size, size, 4), dtype=np.uint8)
    norm_sh[..., 0] = np.clip((nx_w * 0.5 + 0.5) * 255.0, 0, 255).astype(np.uint8)
    norm_sh[..., 1] = np.clip((ny_w * 0.5 + 0.5) * 255.0, 0, 255).astype(np.uint8)
    norm_sh[..., 2] = np.clip((nz_w * 0.5 + 0.5) * 255.0, 0, 255).astype(np.uint8)
    norm_sh[..., 3] = np.clip(sh_ao * 255.0, 0, 255).astype(np.uint8)

    wmask = np.empty((size, size, 3), dtype=np.uint8)
    wmask[..., 0] = np.clip(wm_water * 255.0, 0, 255).astype(np.uint8)
    wmask[..., 1] = np.clip(wm_glow * 255.0, 0, 255).astype(np.uint8)
    wmask[..., 2] = np.clip(wm_gloss * 255.0, 0, 255).astype(np.uint8)

    return np.clip(rgb, 0, 255).astype(np.uint8), norm_sh, wmask


def bake_prop_shadows_on_surface(
    surf_rgb: np.ndarray,
    vertices: np.ndarray,
    indices: np.ndarray,
    world_w: float,
    world_h: float,
    sample_ground_y,
    shadow_tint: tuple[float, float, float] = (0.60, 0.67, 0.78),
) -> np.ndarray:
    """Bake crisp directional sun shadows + soft contact AO from 3D landmark meshes onto surface.png.

    Sun comes from upper-left (-0.48, +0.80, -0.38), casting grounded shadows toward lower-right (+X, +Z).
    """
    if len(vertices) == 0 or len(indices) < 3 or world_w <= 0 or world_h <= 0:
        return surf_rgb
    sh_h, sh_w = surf_rgb.shape[:2]
    mask_n = min(1024, sh_w)
    sx = (mask_n - 1) / float(world_w)
    sz = (mask_n - 1) / float(world_h)

    wx = vertices[:, 0].astype(np.float64)
    wy = vertices[:, 1].astype(np.float64)
    wz = vertices[:, 2].astype(np.float64)
    y_g = sample_ground_y(wx, wz).astype(np.float64)
    h_above = np.clip(wy - y_g, 0.0, 260.0)

    # Projected shadow coordinates along -Lkey (+0.58, +0.48 per unit height)
    px_base = wx * sx
    py_base = wz * sz
    px_sh = (wx + h_above * 0.58) * sx
    py_sh = (wz + h_above * 0.48) * sz

    tris = indices.reshape(-1, 3)
    sh_img = Image.new('L', (mask_n, mask_n), 0)
    ao_img = Image.new('L', (mask_n, mask_n), 0)
    draw_sh = ImageDraw.Draw(sh_img)
    draw_ao = ImageDraw.Draw(ao_img)

    # Filter triangles within canvas and rasterize cast shadow + base contact AO
    for a, b, c in tris:
        ha = max(float(h_above[a]), float(h_above[b]), float(h_above[c]))
        if ha > 2.5:
            x0, y0 = float(px_sh[a]), float(py_sh[a])
            x1, y1 = float(px_sh[b]), float(py_sh[b])
            x2, y2 = float(px_sh[c]), float(py_sh[c])
            if max(x0, x1, x2) >= 0 and min(x0, x1, x2) < mask_n and max(y0, y1, y2) >= 0 and min(y0, y1, y2) < mask_n:
                draw_sh.polygon([(x0, y0), (x1, y1), (x2, y2)], fill=255)
        if min(float(h_above[a]), float(h_above[b]), float(h_above[c])) < 32.0:
            bx0, by0 = float(px_base[a]), float(py_base[a])
            bx1, by1 = float(px_base[b]), float(py_base[b])
            bx2, by2 = float(px_base[c]), float(py_base[c])
            if max(bx0, bx1, bx2) >= 0 and min(bx0, bx1, bx2) < mask_n and max(by0, by1, by2) >= 0 and min(by0, by1, by2) < mask_n:
                draw_ao.polygon([(bx0, by0), (bx1, by1), (bx2, by2)], fill=255)

    sh_f = _blur_f32(np.asarray(sh_img, dtype=np.float32) / 255.0, 2.6)
    ao_f = _blur_f32(np.asarray(ao_img, dtype=np.float32) / 255.0, 5.0)
    if mask_n != sh_w or mask_n != sh_h:
        sh_f = np.asarray(Image.fromarray(sh_f, 'F').resize((sh_w, sh_h), Image.BILINEAR), dtype=np.float32)
        ao_f = np.asarray(Image.fromarray(ao_f, 'F').resize((sh_w, sh_h), Image.BILINEAR), dtype=np.float32)

    tint = np.array(shadow_tint, dtype=np.float32)
    out = surf_rgb.astype(np.float32)
    # Apply subtle dark contact AO around building bases, then crisp cool directional sun shadow
    ao_w = np.clip(ao_f * 0.30, 0.0, 0.34)[..., None]
    out = out * (1.0 - ao_w + tint * ao_w)
    sh_w_arr = np.clip(sh_f * 0.56, 0.0, 0.60)[..., None]
    out = out * (1.0 - sh_w_arr + tint * sh_w_arr)
    return np.clip(out, 0, 255).astype(np.float32)


def _split_spatial_clusters(pos: np.ndarray, tris: np.ndarray, margin: float = 0.015) -> list[tuple[np.ndarray, np.ndarray]]:
    """Split a submesh into rigid physical landmarks (connected components merged by overlapping XZ footprint).

    Keeps multi-piece landmarks (tree trunks + leaf cards, temples + roofs + banners, houses + chimneys)
    locked together rigidly while separating independent buildings/pillars across a realm submesh.
    """
    nv = len(pos)
    if nv == 0 or len(tris) == 0:
        return []
    parent = np.arange(nv, dtype=np.int32)

    def _find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = int(parent[x])
        return x

    for a, b, c in tris:
        ra, rb, rc = _find(int(a)), _find(int(b)), _find(int(c))
        m = ra if ra < rb else rb
        if rc < m:
            m = rc
        parent[ra] = m
        parent[rb] = m
        parent[rc] = m

    roots = np.array([_find(i) for i in range(nv)], dtype=np.int32)
    tri_roots = roots[tris[:, 0]]
    uniq_roots = np.unique(tri_roots)
    nc = len(uniq_roots)
    if nc <= 1:
        return [(np.unique(tris.ravel()), tris)]

    # Compute XZ bounding box per connected component and merge strictly XZ-overlapping pieces
    r_to_ci = {int(r): ci for ci, r in enumerate(uniq_roots)}
    boxes = np.empty((nc, 4), dtype=np.float32)  # xmin, xmax, zmin, zmax
    for ci, r in enumerate(uniq_roots):
        vm = roots == r
        boxes[ci, 0] = pos[vm, 0].min()
        boxes[ci, 1] = pos[vm, 0].max()
        boxes[ci, 2] = pos[vm, 2].min()
        boxes[ci, 3] = pos[vm, 2].max()

    c_parent = np.arange(nc, dtype=np.int32)

    def _cfind(x: int) -> int:
        while c_parent[x] != x:
            c_parent[x] = c_parent[c_parent[x]]
            x = int(c_parent[x])
        return x

    # Sort-and-sweep on xmin for fast O(N log N) overlap merging
    order = np.argsort(boxes[:, 0])
    for oi in range(nc):
        i = int(order[oi])
        xi1 = float(boxes[i, 1]) + margin
        zi0, zi1 = float(boxes[i, 2]) - margin, float(boxes[i, 3]) + margin
        for oj in range(oi + 1, nc):
            j = int(order[oj])
            if float(boxes[j, 0]) > xi1:
                break
            if float(boxes[j, 2]) <= zi1 and float(boxes[j, 3]) >= zi0:
                ri, rj = _cfind(i), _cfind(j)
                if ri != rj:
                    if ri < rj:
                        c_parent[rj] = ri
                    else:
                        c_parent[ri] = rj

    # Group triangles & vertex masks by merged cluster root
    v_cid = np.full(nv, -1, dtype=np.int32)
    for r, ci in r_to_ci.items():
        v_cid[roots == r] = _cfind(ci)
    t_cid = v_cid[tris[:, 0]]
    clusters: list[tuple[np.ndarray, np.ndarray]] = []
    for cid in np.unique(t_cid):
        if cid < 0:
            continue
        tmask = t_cid == cid
        ct = tris[tmask]
        used_v = np.unique(ct.ravel())
        clusters.append((used_v, ct))
    return clusters


def build_realm_native_3d(
    realm: str,
    arc: _GameMapArchive | None = None,
    out_base: Path | None = None,
    maps_dir: Path | None = None,
    surface_size: int = 2048,
) -> dict[str, Any] | None:
    """Build props.bin, atlas.png, surface.png, and meta.json for one realm."""
    if realm not in NATIVE_REALMS:
        return None
    if arc is None:
        arc = _GameMapArchive()
    georef = _load_georef()
    frame = _realm_world_frame(realm)
    out_dir = (Path(out_base) if out_base else OUT_BASE) / realm
    out_dir.mkdir(parents=True, exist_ok=True)
    h16_dir = Path(maps_dir) if maps_dir else (paths.CACHE / 'gow_game_maps')

    # Ensure inverted 1024x1024 h16 heightmap exists and load its float grid for exact building grounding
    h16_path = build_realm_h16(realm, out_dir=h16_dir, maps_dir=h16_dir, georef=georef, size=1024)
    if h16_path is None or not h16_path.is_file():
        return None
    h16_rgb = np.asarray(Image.open(h16_path).convert('RGB'), dtype=np.float32)
    h16_grid = (h16_rgb[..., 0] * 256.0 + h16_rgb[..., 1]) / 65535.0
    h16_n = h16_grid.shape[0]

    def sample_h16_world(wx: np.ndarray, wz: np.ndarray) -> np.ndarray:
        u = np.clip(wx / frame['world_w'], 0.0, 1.0) * (h16_n - 1)
        v = np.clip(wz / frame['world_h'], 0.0, 1.0) * (h16_n - 1)
        x0 = np.floor(u).astype(np.int64)
        y0 = np.floor(v).astype(np.int64)
        x1 = np.minimum(h16_n - 1, x0 + 1)
        y1 = np.minimum(h16_n - 1, y0 + 1)
        fx = (u - x0).astype(np.float32)
        fy = (v - y0).astype(np.float32)
        val = (
            h16_grid[y0, x0] * (1.0 - fx) * (1.0 - fy)
            + h16_grid[y0, x1] * fx * (1.0 - fy)
            + h16_grid[y1, x0] * (1.0 - fx) * fy
            + h16_grid[y1, x1] * fx * fy
        )
        return val * frame['height_amp']

    # 1. Extract raw heightmaps for this realm (Vanaheim has 2: crater + jungle)
    map_ids = [mid for mid, (r, _) in GAME_MAPS.items() if r == realm and mid in georef and georef[mid].get('accepted')]
    raw_hs: dict[str, np.ndarray] = {}
    for mid in map_ids:
        _, tx_name = GAME_MAPS[mid]
        got = arc.extract_textures([tx_name]).get(tx_name)
        if got is not None:
            arr = got[1]
            raw_hs[mid] = arr[..., 0].astype(np.float32) if arr.ndim == 3 else arr.astype(np.float32)

    # 2. Locate MESH_<realm>_0, materials, inline GPU buffer, and decals
    me_list = [e for e in arc.entries if e['name'] == f'MESH_{realm}_0' and e['pool'] == 0]
    if not me_list:
        return None
    me = me_list[0]
    moff = arc.find_mesh_offset(me)
    if moff is None:
        return None
    p0_base = moff - me['doff']
    mdata = arc.raw[moff:moff + me['size']]
    nparts = struct.unpack_from('<I', mdata, 0x10)[0]
    offs = [0x40 + i * 4 + struct.unpack_from('<I', mdata, 0x40 + i * 4)[0] for i in range(nparts)]
    mats = arc.find_mat_table(arc.entries[me['idx'] + 1])
    gpu_e = [e for e in arc.entries if e['name'] == f'MG_{realm}_0_gpu'][0]
    g_start = arc.find_inline_gpu(gpu_e, mdata, offs)
    decals = arc.extract_realm_decals(realm, me['idx'], p0_base)

    # 3. Render 2048x2048 wood-carved diorama surface.png, 2K terrain_n.png (normal + raymarched shadow), and water_mask.png!
    m0 = frame['merc0']
    xs = np.linspace(m0['x_min'], m0['x_max'], surface_size, dtype=np.float64)
    ys = np.linspace(m0['y_min'], m0['y_max'], surface_size, dtype=np.float64)
    gx_g, gy_g = np.meshgrid(xs, ys)

    surf_frags: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    norm_frags: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    wmask_frags: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    for mid, h_arr in raw_hs.items():
        M_mid, _ = _tex_to_world_fn(mid, georef, frame)
        albedo, norm_sh, wmask = _render_map_id_layers(
            arc, realm, mid, h_arr, decals, M_mid, frame['height_amp'], size=2048,
        )
        G = np.asarray(georef[mid]['merc0_to_texture'], dtype=np.float64)
        tx = G[0, 0] * gx_g + G[0, 1] * gy_g + G[0, 2]
        ty = G[1, 0] * gx_g + G[1, 1] * gy_g + G[1, 2]
        dx = np.minimum(tx, 2047.0 - tx)
        dy = np.minimum(ty, 2047.0 - ty)
        w = np.clip(np.minimum(dx, dy) / 24.0, 0.0, 1.0).astype(np.float32)
        w = w * w * (3.0 - 2.0 * w)
        surf_frags[mid] = (_bilinear_sample_2d(albedo, tx, ty), w)
        norm_frags[mid] = (_bilinear_sample_2d(norm_sh, tx, ty), w)
        wmask_frags[mid] = (_bilinear_sample_2d(wmask, tx, ty), w)

    def _merge_frags(frags: dict[str, tuple[np.ndarray, np.ndarray]], default_val: tuple[float, ...]) -> np.ndarray:
        ch = len(default_val)
        if realm == 'vanaheim' and 'vanaheim_crater' in frags and 'vanaheim_jungle' in frags:
            lat_grid = np.degrees(np.arctan(np.sinh(np.pi * (1.0 - 2.0 * gy_g / 256.0))))
            t = np.clip((lat_grid - 0.660) / (0.710 - 0.660), 0.0, 1.0).astype(np.float32)[..., None]
            s = t * t * (3.0 - 2.0 * t)
            return frags['vanaheim_crater'][0] * s + frags['vanaheim_jungle'][0] * (1.0 - s)
        if frags:
            num = np.zeros((surface_size, surface_size, ch), dtype=np.float32)
            den = np.zeros((surface_size, surface_size, 1), dtype=np.float32)
            for vals, weights in frags.values():
                w3 = weights[..., None]
                num += vals * w3
                den += w3
            def_arr = np.array(default_val, dtype=np.float32).reshape(1, 1, ch)
            cov = np.clip(den, 0.0, 1.0)
            avg = np.where(den > 1e-4, num / np.maximum(den, 1e-6), def_arr)
            return avg * cov + def_arr * (1.0 - cov)
        out_arr = np.empty((surface_size, surface_size, ch), dtype=np.float32)
        for ci, dv in enumerate(default_val):
            out_arr[..., ci] = dv
        return out_arr

    void_rgb = tuple(float(c) for c in SURFACE_STYLES.get(realm, SURFACE_STYLES['midgard'])['void'])
    surf_rgb = _merge_frags(surf_frags, void_rgb)
    terr_norm_rgba = _merge_frags(norm_frags, (128.0, 255.0, 128.0, 255.0))
    water_mask_rgb = _merge_frags(wmask_frags, (0.0, 0.0, 36.0))

    # 4. Extract ALL 3D landmark sub-meshes & their PBR diffuse (RGBA)/normal/gloss/AO textures
    raw_parts: list[dict[str, Any]] = []
    tex_images: dict[str, np.ndarray] = {}
    tex_alpha_frac: dict[str, float] = {}
    norm_images: dict[str, np.ndarray] = {}
    gloss_images: dict[str, np.ndarray] = {}
    tex_weights: dict[str, int] = {}

    for pi in range(nparts):
        pe = offs[pi + 1] if pi + 1 < nparts else len(mdata)
        c = mdata[offs[pi]:pe]
        if len(c) < 0x90:
            continue
        u = struct.unpack_from('<16I', c, 0x28)
        mat_idx, ib_off, vb_off, nv, ntri, nidx = u[0], u[2], u[5], u[7], u[8], u[13]
        if nv <= 8 or ntri <= 2 or nidx != ntri * 3:
            continue
        if mat_idx >= len(mats):
            continue
        tx_names = arc.resolve_mat_textures(mats[mat_idx])
        picked = arc.pick_diffuse_texture(tx_names)
        if picked is None:
            continue
        tx_key, tx_rgba = picked
        if tx_key not in tex_images:
            norm_arr, gloss_arr, ao_arr = arc.pick_pbr_maps(tx_names, tx_key)
            if ao_arr is not None:
                ao_f = np.asarray(
                    Image.fromarray(ao_arr.astype(np.uint8), 'L').resize((tx_rgba.shape[1], tx_rgba.shape[0]), Image.BILINEAR),
                    dtype=np.float32,
                ) / 255.0
                tx_rgba = tx_rgba.copy()
                tx_rgba[..., :3] = np.clip(tx_rgba[..., :3].astype(np.float32) * (0.64 + 0.36 * ao_f[..., None]), 0, 255).astype(np.uint8)
            tex_images[tx_key] = tx_rgba
            tex_alpha_frac[tx_key] = float(np.mean(tx_rgba[..., 3] < 128)) if tx_rgba.shape[2] >= 4 else 0.0
            if norm_arr is not None:
                norm_images[tx_key] = norm_arr
            if gloss_arr is not None:
                gloss_images[tx_key] = gloss_arr

        lh = struct.unpack_from('<Q', c, 0x68)[0] if len(c) >= 0x70 else 0
        buf = arc.read_lod(lh) if lh in arc.lod_subs else (
            arc.raw[g_start:g_start + gpu_e['size']] if g_start is not None else None
        )
        if buf is None or ib_off + nidx * 2 > len(buf):
            continue
        idxs = np.frombuffer(buf[ib_off:ib_off + nidx * 2], '<u2')
        if len(idxs) != nidx or int(idxs.max()) >= nv:
            continue

        # Stream offsets live in the last 16 bytes of the 0x100/0xf0 part descriptor
        so_pos = len(c) - 16
        s0, s1, s2, s3 = struct.unpack_from('<4I', c, so_pos)
        if s0 != vb_off:
            s0 = vb_off
            s1 = s0 + nv * 12
            s2 = s1 + nv * 4
            s3 = s2 + nv * 4
        if s0 + nv * 12 > len(buf):
            continue

        pos = np.frombuffer(buf[s0:s0 + nv * 12], '<f4').reshape(nv, 3).copy()
        if not np.isfinite(pos).all():
            continue

        # Flip triangle winding from GoWR CW (a,b,c) -> WebGL2 CCW (a,c,b)
        tris = idxs.reshape(-1, 3)[:, [0, 2, 1]].astype(np.uint32)

        # Decode normals (s1) or fallback to smooth geometric normals
        if s1 + nv * 4 <= len(buf) and s2 > s1:
            nrm = decode_r10g10b10a2_unorm_normals(np.frombuffer(buf[s1:s1 + nv * 4], '<u4'))
            gn = compute_smooth_normals(pos, tris)
            if float(np.mean(np.sum(nrm * gn, axis=1))) < 0.2:
                nrm = gn
        else:
            nrm = compute_smooth_normals(pos, tris)

        # Decode UV0 (s2: UNORM16 x 2; handle 8B dual-UV streams by taking first 4B per vertex)
        s2_stride = (s3 - s2) // nv if (s3 > s2 and (s3 - s2) % nv == 0) else 4
        if s2 + nv * max(4, s2_stride) <= len(buf) and s2_stride in (4, 8):
            if s2_stride == 4:
                uv = np.frombuffer(buf[s2:s2 + nv * 4], '<u2').reshape(nv, 2).astype(np.float32) / 65535.0
            else:
                raw_uv = np.frombuffer(buf[s2:s2 + nv * 8], '<u2').reshape(nv, 4)
                uv = raw_uv[:, :2].astype(np.float32) / 65535.0
        else:
            span_x = max(1e-4, float(pos[:, 0].max() - pos[:, 0].min()))
            span_z = max(1e-4, float(pos[:, 2].max() - pos[:, 2].min()))
            uv = np.stack([(pos[:, 0] - pos[:, 0].min()) / span_x, (pos[:, 2] - pos[:, 2].min()) / span_z], axis=1)

        tex_weights[tx_key] = tex_weights.get(tx_key, 0) + ntri
        raw_parts.append({
            'pi': pi, 'tx_key': tx_key, 'pos': pos, 'nrm': nrm, 'uv': uv, 'tris': tris,
        })

    # 5. Transform all extracted 3D landmarks into exact WebGL2 world space using rigid spatial clusters!
    # Never warp vertices per-vertex against local terrain elevation (which shears bridges/arches over chasms).
    map_world_xforms = {mid: _tex_to_world_fn(mid, georef, frame) for mid in raw_hs}

    def map_xz_to_world(x: np.ndarray, z: np.ndarray):
        if realm == 'vanaheim' and 'vanaheim_crater' in raw_hs and 'vanaheim_jungle' in raw_hs:
            is_crat = z < -0.29
            wx = np.empty_like(x, dtype=np.float64)
            wz = np.empty_like(z, dtype=np.float64)
            jac_list = {}
            for mid, mask in (('vanaheim_crater', is_crat), ('vanaheim_jungle', ~is_crat)):
                if not np.any(mask):
                    continue
                cx_q, cz_q, hx_q, hz_q = QUAD_FOOTPRINTS[mid]
                tx = ((x[mask] - cx_q) / (2.0 * hx_q) + 0.5) * 2048.0
                ty = ((z[mask] - cz_q) / (2.0 * hz_q) + 0.5) * 2048.0
                M, t_vec = map_world_xforms[mid]
                wx[mask] = M[0, 0] * tx + M[0, 1] * ty + t_vec[0]
                wz[mask] = M[1, 0] * tx + M[1, 1] * ty + t_vec[1]
                J = M @ np.diag([2048.0 / (2.0 * hx_q), 2048.0 / (2.0 * hz_q)])
                jac_list[mid] = (mask, J)
            return wx, wz, jac_list
        mid = map_ids[0]
        cx_q, cz_q, hx_q, hz_q = QUAD_FOOTPRINTS[mid]
        tx = ((x - cx_q) / (2.0 * hx_q) + 0.5) * 2048.0
        ty = ((z - cz_q) / (2.0 * hz_q) + 0.5) * 2048.0
        M, t_vec = map_world_xforms[mid]
        wx = M[0, 0] * tx + M[0, 1] * ty + t_vec[0]
        wz = M[1, 0] * tx + M[1, 1] * ty + t_vec[1]
        J = M @ np.diag([2048.0 / (2.0 * hx_q), 2048.0 / (2.0 * hz_q)])
        return wx, wz, {mid: (np.ones(len(x), dtype=bool), J)}

    horiz_scales = []
    for mid, (M, _) in map_world_xforms.items():
        _, _, hx_q, hz_q = QUAD_FOOTPRINTS[mid]
        J = M @ np.diag([2048.0 / (2.0 * hx_q), 2048.0 / (2.0 * hz_q)])
        horiz_scales.append(math.sqrt(abs(float(np.linalg.det(J)))))
    world_per_3d = float(np.mean(horiz_scales)) if horiz_scales else 160.0

    # Split each submesh into rigid physical landmark clusters and cull far out-of-bounds clusters per cluster
    kept_clusters: list[dict[str, Any]] = []
    fit_py: list[float] = []
    fit_yt: list[float] = []
    for part in raw_parts:
        pos_full = part['pos']
        nrm_full = part['nrm']
        uv_full = part['uv']
        tris_full = part['tris']
        tx_key = part['tx_key']

        wx_all, wz_all, jac_all = map_xz_to_world(pos_full[:, 0], pos_full[:, 2])
        # Transform normals once per submesh using inverse-transpose Jacobian
        nrm_all = nrm_full.copy()
        det_sign = 1.0
        for _, (mask, J) in jac_all.items():
            J_it = np.linalg.inv(J).T
            j_norm = math.sqrt(abs(float(np.linalg.det(J_it)))) or 1.0
            J_unit = J_it / j_norm
            nxz = nrm_full[mask][:, [0, 2]] @ J_unit.T
            nrm_all[mask, 0] = nxz[:, 0]
            nrm_all[mask, 2] = nxz[:, 1]
            if float(np.linalg.det(J)) < 0:
                det_sign = -1.0
        nl = np.linalg.norm(nrm_all, axis=1, keepdims=True)
        nrm_all = np.where(nl > 1e-5, nrm_all / np.maximum(nl, 1e-5), np.array([0.0, 1.0, 0.0], np.float32))
        if det_sign < 0:
            tris_full = tris_full[:, [0, 2, 1]]

        # Special case: continuous terrain-following landmarks stay as a single rigid cluster
        if 'worldsnakebody' in tx_key.lower():
            cl_list = [(np.arange(len(pos_full), dtype=np.int32), tris_full)]
        else:
            cl_list = _split_spatial_clusters(pos_full, tris_full, margin=0.015)

        for used_v, ct in cl_list:
            if len(used_v) < 3 or len(ct) == 0:
                continue
            c_wx = wx_all[used_v]
            c_wz = wz_all[used_v]
            in_x = (c_wx >= -frame['world_w'] * 0.12) & (c_wx <= frame['world_w'] * 1.12)
            in_z = (c_wz >= -frame['world_h'] * 0.12) & (c_wz <= frame['world_h'] * 1.12)
            if float(np.mean(in_x & in_z)) < 0.25:
                continue
            # Remap local vertex indices 0..len(used_v)-1 cleanly
            remap = np.empty(len(pos_full), dtype=np.uint32)
            remap[used_v] = np.arange(len(used_v), dtype=np.uint32)
            local_tris = remap[ct]
            c_py = pos_full[used_v, 1]
            c_yt = sample_h16_world(c_wx, c_wz)
            py_base = float(np.percentile(c_py, 10))
            base_m = c_py <= py_base + 0.025
            yt_b = c_yt[base_m]
            if float(yt_b.max() - yt_b.min()) > 35.0 and np.any(yt_b > 25.0):
                y_anchor = float(np.median(yt_b[yt_b > 25.0]))
            else:
                y_anchor = float(np.median(yt_b))
            if y_anchor > 10.0:
                fit_py.append(float(np.median(c_py[base_m])))
                fit_yt.append(y_anchor)
            kept_clusters.append({
                'pi': part['pi'],
                'tx_key': tx_key,
                'wx': c_wx,
                'wz': c_wz,
                'py': c_py,
                'yt': c_yt,
                'py_base': py_base,
                'y_anchor': y_anchor,
                'nrm': nrm_all[used_v],
                'uv': uv_full[used_v],
                'tris': local_tris,
            })

    # Robust Theil-Sen realm linear elevation fit yt = A_fit * py + B_fit (for giant terrain-spanning walls/serpents)
    if len(fit_py) >= 4:
        py_arr = np.asarray(fit_py, dtype=np.float64)
        yt_arr = np.asarray(fit_yt, dtype=np.float64)
        idx_sub = np.linspace(0, len(py_arr) - 1, min(len(py_arr), 160)).astype(int)
        slopes = []
        for ii in range(len(idx_sub)):
            i = idx_sub[ii]
            for jj in range(ii + 1, len(idx_sub)):
                j = idx_sub[jj]
                if abs(py_arr[j] - py_arr[i]) > 0.12:
                    s = (yt_arr[j] - yt_arr[i]) / (py_arr[j] - py_arr[i])
                    if 25.0 < s < 520.0:
                        slopes.append(s)
        a_lin = float(np.median(slopes)) if slopes else min(world_per_3d, frame['height_amp'])
        b_lin = float(np.median(yt_arr - a_lin * py_arr))
    else:
        a_lin = min(world_per_3d, frame['height_amp'])
        b_lin = float(np.median(fit_yt) - a_lin * np.median(fit_py)) if fit_py else 0.0

    # Architectural vertical scale per realm (prevents zoomed realms like Helheim/Muspelheim/Niflheim from stretching)
    if realm == 'asgard':
        scale_y = float(np.clip(a_lin, 95.0, 125.0))
    else:
        scale_y = float(min(world_per_3d, frame['height_amp'] * 1.08))

    # Keep only textures actually referenced by kept clusters so atlas space is maximized
    used_tx_keys = {cl['tx_key'] for cl in kept_clusters}
    used_tex_images = {k: v for k, v in tex_images.items() if k in used_tx_keys}
    used_norm_images = {k: v for k, v in norm_images.items() if k in used_tx_keys}
    used_gloss_images = {k: v for k, v in gloss_images.items() if k in used_tx_keys}
    used_tex_weights = {k: v for k, v in tex_weights.items() if k in used_tx_keys}

    # Pack synchronized RGBA diffuse + tangent-normal/gloss atlases
    atlas_img, atlas_n_img, uv_map = pack_pbr_atlases(
        used_tex_images, normal_maps=used_norm_images, gloss_maps=used_gloss_images, weights=used_tex_weights,
    )
    atlas_path = out_dir / 'atlas.png'
    tmp_atlas = atlas_path.with_suffix('.tmp')
    atlas_img.save(tmp_atlas, 'PNG', compress_level=6)
    tmp_atlas.replace(atlas_path)

    atlas_n_path = out_dir / 'atlas_n.png'
    tmp_atlas_n = atlas_n_path.with_suffix('.tmp')
    atlas_n_img.save(tmp_atlas_n, 'PNG', compress_level=6)
    tmp_atlas_n.replace(atlas_n_path)

    # Assemble single merged WebGL2 vertex + index buffer
    all_verts: list[np.ndarray] = []
    all_idxs: list[np.ndarray] = []
    shadow_idxs: list[np.ndarray] = []
    v_offset = 0
    seen_pis: set[int] = set()

    for cl in kept_clusters:
        tx_key = cl['tx_key']
        if tx_key not in uv_map:
            continue
        c_wx = cl['wx']
        c_wz = cl['wz']
        c_py = cl['py']
        c_yt = cl['yt']
        sxz = max(float(c_wx.max() - c_wx.min()), float(c_wz.max() - c_wz.min()))
        dh_terr = float(c_yt.max() - c_yt.min())

        # Pure rigid vertical placement (ZERO per-vertex y_terr shearing!)
        if 'worldsnakebody' in tx_key.lower() or (sxz > 260.0 and dh_terr > 35.0):
            wy = a_lin * c_py + b_lin
        else:
            wy = (cl['y_anchor'] - 1.5) + (c_py - cl['py_base']) * scale_y

        u0, v0, us, vs = uv_map[tx_key]
        uv = cl['uv']
        u_a = u0 + np.clip(uv[:, 0], 0.0, 1.0) * us
        v_a = v0 + np.clip(uv[:, 1], 0.0, 1.0) * vs

        nrm_w = cl['nrm']
        v_block = np.empty((len(c_py), 8), dtype='<f4')
        v_block[:, 0] = c_wx
        v_block[:, 1] = wy
        v_block[:, 2] = c_wz
        v_block[:, 3] = nrm_w[:, 0]
        v_block[:, 4] = nrm_w[:, 1]
        v_block[:, 5] = nrm_w[:, 2]
        v_block[:, 6] = u_a
        v_block[:, 7] = v_a

        tri_shifted = cl['tris'].ravel() + np.uint32(v_offset)
        all_verts.append(v_block)
        all_idxs.append(tri_shifted)
        # Exclude highly transparent alpha-cutout cards from opaque 2D surface shadow bake
        # (real-time WebGL2 alpha-tested shadow map handles leaf-shaped shadows cleanly!)
        if tex_alpha_frac.get(tx_key, 0.0) <= 0.12:
            shadow_idxs.append(tri_shifted)
        v_offset += len(c_py)
        seen_pis.add(cl['pi'])

    submesh_count = len(seen_pis)
    if all_verts:
        merged_v = np.vstack(all_verts)
        merged_i = np.concatenate(all_idxs)
        merged_sh_i = np.concatenate(shadow_idxs) if shadow_idxs else np.zeros((0,), dtype='<u4')
    else:
        merged_v = np.zeros((0, 8), dtype='<f4')
        merged_i = np.zeros((0,), dtype='<u4')
        merged_sh_i = np.zeros((0,), dtype='<u4')

    # Bake soft contact AO (and light 2D-fallback shadow) from opaque 3D landmarks onto surface.png
    style = SURFACE_STYLES.get(realm, SURFACE_STYLES['midgard'])
    if len(merged_v) > 0 and len(merged_sh_i) >= 3:
        surf_rgb = bake_prop_shadows_on_surface(
            surf_rgb,
            merged_v,
            merged_sh_i,
            frame['world_w'],
            frame['world_h'],
            sample_h16_world,
            shadow_tint=style.get('shadow_tint', (0.68, 0.74, 0.84)),
        )

    surface_path = out_dir / 'surface.png'
    tmp_surf = surface_path.with_suffix('.tmp')
    Image.fromarray(np.clip(surf_rgb, 0, 255).astype(np.uint8), 'RGB').save(tmp_surf, 'PNG', compress_level=6)
    tmp_surf.replace(surface_path)

    # Re-normalize resampled 2K world-space terrain normals and save terrain_n.png (RGBA)
    tn_vec = terr_norm_rgba[..., :3] / 127.5 - 1.0
    tn_len = np.linalg.norm(tn_vec, axis=2, keepdims=True)
    tn_vec = np.where(tn_len > 1e-5, tn_vec / np.maximum(tn_len, 1e-5), np.array([0.0, 1.0, 0.0], np.float32))
    terr_norm_out = np.empty((surface_size, surface_size, 4), dtype=np.uint8)
    terr_norm_out[..., :3] = np.clip((tn_vec * 0.5 + 0.5) * 255.0, 0, 255).astype(np.uint8)
    terr_norm_out[..., 3] = np.clip(terr_norm_rgba[..., 3], 0, 255).astype(np.uint8)
    terrain_n_path = out_dir / 'terrain_n.png'
    tmp_tn = terrain_n_path.with_suffix('.tmp')
    Image.fromarray(terr_norm_out, 'RGBA').save(tmp_tn, 'PNG', compress_level=6)
    tmp_tn.replace(terrain_n_path)

    # Save 1024x1024 water/lava/gloss dynamic surface mask
    water_mask_path = out_dir / 'water_mask.png'
    tmp_wm = water_mask_path.with_suffix('.tmp')
    wm_img = Image.fromarray(np.clip(water_mask_rgb, 0, 255).astype(np.uint8), 'RGB')
    if wm_img.width > 1024:
        wm_img = wm_img.resize((1024, 1024), Image.BILINEAR)
    wm_img.save(tmp_wm, 'PNG', compress_level=6)
    tmp_wm.replace(water_mask_path)

    props_path = out_dir / 'props.bin'
    tmp_props = props_path.with_suffix('.tmp')
    tmp_props.write_bytes(pack_gowm_binary(merged_v, merged_i))
    tmp_props.replace(props_path)

    meta_out = {
        'realm': realm,
        'schema_version': SCHEMA_VERSION,
        'has_native_3d': True,
        'has_surface': surface_path.is_file(),
        'has_props': bool(len(merged_v) > 0),
        'has_normal_atlas': atlas_n_path.is_file(),
        'has_terrain_normal': terrain_n_path.is_file(),
        'has_water_mask': water_mask_path.is_file(),
        'vertex_count': int(len(merged_v)),
        'index_count': int(len(merged_i)),
        'tri_count': int(len(merged_i) // 3),
        'submesh_count': submesh_count,
        'texture_count': len(uv_map),
        'normal_count': len(norm_images),
        'gloss_count': len(gloss_images),
        'atlas_size': [atlas_img.width, atlas_img.height],
        'surface_size': [surface_size, surface_size],
        'decal_count': len(decals),
    }
    meta_path = out_dir / 'meta.json'
    tmp_meta = meta_path.with_suffix('.tmp')
    tmp_meta.write_text(json.dumps(meta_out, indent=2), encoding='utf-8')
    tmp_meta.replace(meta_path)
    return meta_out


def main() -> None:
    ap = argparse.ArgumentParser(description='Extract native GoWR 3D map scenes into local user cache.')
    ap.add_argument('realms', nargs='*', help='Realm keys to build (default: all 9 realms)')
    ap.add_argument('--surface-size', type=int, default=2048)
    ap.add_argument('--out', type=Path, default=OUT_BASE)
    ap.add_argument('--game-dir', type=Path)
    args = ap.parse_args()
    if args.game_dir:
        paths.GAME_DIR = paths.find_game_dir(args.game_dir)
    targets = args.realms or list(NATIVE_REALMS)
    arc = _GameMapArchive()
    for r in targets:
        if r not in NATIVE_REALMS:
            print(f'Skipping unknown realm: {r}', file=sys.stderr)
            continue
        info = build_realm_native_3d(r, arc=arc, out_base=args.out, surface_size=args.surface_size)
        if info:
            print(
                f"{r:13s}: {info['submesh_count']:2d} submeshes, {info['vertex_count']:6,d} verts, "
                f"{info['tri_count']:6,d} tris, {info['texture_count']:2d} PBR textures "
                f"(atlas {info['atlas_size'][0]}x{info['atlas_size'][1]}), {info['decal_count']:3d} decals",
                flush=True,
            )


if __name__ == '__main__':
    main()
