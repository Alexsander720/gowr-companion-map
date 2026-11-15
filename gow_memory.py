"""Живой трекер Кратоса из памяти God of War Ragnarök (задача 166).

🔴 КРИТИЧЕСКИЕ ПРАВИЛА БЕЗОПАСНОСТИ:
1. ТОЛЬКО ЧТЕНИЕ: использует исключительно PROCESS_VM_READ | PROCESS_QUERY_INFORMATION.
   Ни при каких условиях не запрашивает права на запись и не вызывает WriteProcessMemory.
2. ПРИВЯЗКА К ОТПЕЧАТКУ СБОРКИ: цепочки указателей привязаны к точному отпечатку
   исполняемого файла GoWR.exe (размер файла, PE TimeDateStamp и SHA-256 заголовка).
   При любом обновлении игры модуль честно рапортует "данные устарели".
3. НИКАКИХ ЗАСТЫВШИХ ТОЧЕК: если процесс закрыт, цепочка указателей вернула невалидный
   адрес или сборка не совпала — модуль возвращает available: False с ясной причиной.
   Замерший Кратос на карте планшета недопустим.
4. ПРОВЕРКА ПОВЕДЕНИЕМ: сырые значения проверяются на допустимые диапазоны
   (здоровье 0..max_hp, координаты внутри реалистичных границ мира, ярость 0..max_rage).
"""
from __future__ import annotations

import ctypes
from paths import DATA, LIVE_REFS
import ctypes.wintypes
import hashlib
import json
import math
import os
import struct
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Константы Win32 API
PROCESS_VM_READ = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400
SAFE_ACCESS_MASK = PROCESS_VM_READ | PROCESS_QUERY_INFORMATION


def _configure_winapi():
    """Declare pointer-sized handles explicitly on 64-bit Python."""
    w = ctypes.wintypes
    k = ctypes.windll.kernel32
    k.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]
    k.OpenProcess.restype = w.HANDLE
    k.CloseHandle.argtypes = [w.HANDLE]
    k.CloseHandle.restype = w.BOOL
    k.CreateToolhelp32Snapshot.argtypes = [w.DWORD, w.DWORD]
    k.CreateToolhelp32Snapshot.restype = w.HANDLE
    for name in ('Process32FirstW', 'Process32NextW'):
        getattr(k, name).argtypes = [w.HANDLE, ctypes.c_void_p]
        getattr(k, name).restype = w.BOOL
    k.QueryFullProcessImageNameW.argtypes = [w.HANDLE, w.DWORD, w.LPWSTR, ctypes.POINTER(w.DWORD)]
    k.QueryFullProcessImageNameW.restype = w.BOOL
    k.ReadProcessMemory.argtypes = [w.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t,
                                   ctypes.POINTER(ctypes.c_size_t)]
    k.ReadProcessMemory.restype = w.BOOL
    p = ctypes.windll.psapi
    p.EnumProcessModules.argtypes = [w.HANDLE, ctypes.c_void_p, w.DWORD, ctypes.POINTER(w.DWORD)]
    p.EnumProcessModules.restype = w.BOOL

# Отпечаток текущей установленной Steam-сборки God of War Ragnarök
KNOWN_BUILDS: Dict[Tuple[int, int], Dict[str, Any]] = {
    # (file_size, pe_timestamp)
    (46685144, 1750707527): {'version': 'owner-calibrated XYZ/Yaw only',
 'header_sha256': 'b192cfbdf42e805fde8ef47aa725ffb4cfb622bca92ae58c83dbabe7dc27c32c',
 'loaded_header_key': '44e3d6df92dbd19e64d497a4e2a7530ec513c4cad0d0199e64106ee2dc2041ef',
 'module_name': 'GoWR.exe',
 'kratos_anchor_offset': 96019504,
 'kratos_chain': [8, 0],
 'offsets': {},
 'position_source': {'rva': 96019504,
                     'chain': [8, 0],
                     'role': 'player_world_via_frame',
                     'frame_chain': [8, 8, 160],
                     'frame_matrix_offset': 80,
                     'frame_stamp_offset': 64,
                     'frame_kind_offset': 168,
                     'frame_parent_offset': 160,
                     'frame_other_parent_offset': 192,
                     'frame_other_flag_offset': 184,
                     'frame_lock_offset': 144,
                     'ancestor_stamp_offset': 224,
                     'ancestor_next_offset': 320,
                     'ancestor_flags_offset': 488,
                     'ancestor_byte_flags_offset': 480,
                     'ancestor_lock_offset': 304,
                     'offset': 80,
                     'kind': 'player_position'},
 'yaw_source': {'rva': 67262760,
                'chain': [3840],
                'offset': 32,
                'kind': 'forward_neg',
                'role': 'camera_not_kratos'},
 'yaw_convention': '+Z=0,+X=90,Y-up',
 'integration_ready': True,
 'integration_note': 'Apply the generated consumer patch after reviewing this live '
                     'calibration; no consumer file was modified.',
 'probe_sources': True,
 'calibration_status': 'owner_confirmed_behavioral_chain',
 'integration_requires_patch': True}
}

# Координатные границы и ключевые POI 9 королевств God of War Ragnarök (Задача 182)
REALM_BOUNDING_BOXES = {'midgard': {'name': 'midgard', 'slug': 'midgard', 'min_x': -100000.0, 'max_x': 100000.0, 'min_y': -100000.0, 'max_y': 100000.0, 'map_lat_min': 0.506, 'map_lat_max': 0.9097, 'map_lng_min': -0.9851, 'map_lng_max': -0.3888, 'center_lat': 0.7373, 'center_lng': -0.5846, 'min_zoom': 9, 'max_zoom': 14, 'initial_zoom': 11, 'tile_pattern': 'https://tiles.mapgenie.io/games/god-of-war-ragnarok/midgard/default-v1/{z}/{x}/{y}.jpg', 'pois': []}, 'vanaheim': {'name': 'vanaheim', 'slug': 'vanaheim', 'min_x': -60000.0, 'max_x': 60000.0, 'min_y': -60000.0, 'max_y': 60000.0, 'map_lat_min': 0.3498, 'map_lat_max': 0.9545, 'map_lng_min': -0.8318, 'map_lng_max': -0.6088, 'center_lat': 0.75, 'center_lng': -0.72, 'min_zoom': 9, 'max_zoom': 15, 'initial_zoom': 11, 'tile_pattern': 'https://tiles.mapgenie.io/games/god-of-war-ragnarok/vanaheim/default-v1/{z}/{x}/{y}.jpg', 'pois': []}, 'helheim': {'name': 'helheim', 'slug': 'helheim', 'min_x': -40000.0, 'max_x': 40000.0, 'min_y': -80000.0, 'max_y': 80000.0, 'map_lat_min': 0.5076, 'map_lat_max': 0.7576, 'map_lng_min': -0.9067, 'map_lng_max': -0.5208, 'center_lat': 0.63, 'center_lng': -0.71, 'min_zoom': 9, 'max_zoom': 14, 'initial_zoom': 11, 'tile_pattern': 'https://tiles.mapgenie.io/games/god-of-war-ragnarok/helheim/default-v1/{z}/{x}/{y}.jpg', 'pois': []}, 'svartalfheim': {'name': 'svartalfheim', 'slug': 'svartalfheim', 'min_x': -80000.0, 'max_x': 80000.0, 'min_y': -80000.0, 'max_y': 80000.0, 'map_lat_min': 0.4566, 'map_lat_max': 0.9504, 'map_lng_min': -0.88, 'map_lng_max': -0.5301, 'center_lat': 0.7, 'center_lng': -0.7, 'min_zoom': 9, 'max_zoom': 14, 'initial_zoom': 11, 'tile_pattern': 'https://tiles.mapgenie.io/games/god-of-war-ragnarok/svartalfheim/default-v1/{z}/{x}/{y}.jpg', 'pois': []}, 'alfheim': {'name': 'alfheim', 'slug': 'alfheim', 'min_x': -70000.0, 'max_x': 70000.0, 'min_y': -70000.0, 'max_y': 70000.0, 'map_lat_min': 0.4064, 'map_lat_max': 0.9388, 'map_lng_min': -0.9294, 'map_lng_max': -0.5033, 'center_lat': 0.7, 'center_lng': -0.72, 'min_zoom': 9, 'max_zoom': 15, 'initial_zoom': 11, 'tile_pattern': 'https://tiles.mapgenie.io/games/god-of-war-ragnarok/alfheim/default-v1/{z}/{x}/{y}.jpg', 'pois': []}, 'asgard': {'name': 'asgard', 'slug': 'asgard', 'min_x': -50000.0, 'max_x': 50000.0, 'min_y': -50000.0, 'max_y': 50000.0, 'map_lat_min': 0.5, 'map_lat_max': 0.85, 'map_lng_min': -0.85, 'map_lng_max': -0.55, 'center_lat': 0.68, 'center_lng': -0.7, 'min_zoom': 9, 'max_zoom': 13, 'initial_zoom': 11, 'tile_pattern': 'https://tiles.mapgenie.io/games/god-of-war-ragnarok/asgard/default-v1/{z}/{x}/{y}.jpg', 'pois': []}, 'jotunheim': {'name': 'jotunheim', 'slug': 'jotunheim', 'min_x': -50000.0, 'max_x': 50000.0, 'min_y': -50000.0, 'max_y': 50000.0, 'map_lat_min': 0.4, 'map_lat_max': 0.9, 'map_lng_min': -0.9, 'map_lng_max': -0.5, 'center_lat': 0.65, 'center_lng': -0.7, 'min_zoom': 9, 'max_zoom': 15, 'initial_zoom': 11, 'tile_pattern': 'https://tiles.mapgenie.io/games/god-of-war-ragnarok/jotunheim/default-v1/{z}/{x}/{y}.jpg', 'pois': []}, 'niflheim': {'name': 'niflheim', 'slug': 'niflheim', 'min_x': -30000.0, 'max_x': 30000.0, 'min_y': -30000.0, 'max_y': 30000.0, 'map_lat_min': 0.6077, 'map_lat_max': 0.7929, 'map_lng_min': -0.9228, 'map_lng_max': -0.6032, 'center_lat': 0.7, 'center_lng': -0.76, 'min_zoom': 9, 'max_zoom': 14, 'initial_zoom': 11, 'tile_pattern': 'https://tiles.mapgenie.io/games/god-of-war-ragnarok/niflheim/default-v1/{z}/{x}/{y}.jpg', 'pois': []}, 'muspelheim': {'name': 'muspelheim', 'slug': 'muspelheim', 'min_x': -30000.0, 'max_x': 30000.0, 'min_y': -30000.0, 'max_y': 30000.0, 'map_lat_min': 0.5575, 'map_lat_max': 0.8475, 'map_lng_min': -0.868, 'map_lng_max': -0.5609, 'center_lat': 0.7, 'center_lng': -0.71, 'min_zoom': 9, 'max_zoom': 13, 'initial_zoom': 11, 'tile_pattern': 'https://tiles.mapgenie.io/games/god-of-war-ragnarok/muspelheim/default-v1/{z}/{x}/{y}.jpg', 'pois': []}, 'sindris-house': {'name': 'sindris-house', 'slug': 'sindris-house', 'min_x': -20000.0, 'max_x': 20000.0, 'min_y': -20000.0, 'max_y': 20000.0, 'map_lat_min': 0.6, 'map_lat_max': 0.8, 'map_lng_min': -0.8, 'map_lng_max': -0.6, 'center_lat': 0.7, 'center_lng': -0.7, 'min_zoom': 9, 'max_zoom': 11, 'initial_zoom': 10, 'tile_pattern': 'https://tiles.mapgenie.io/games/god-of-war-ragnarok/sindris-house/default-v1/{z}/{x}/{y}.jpg', 'pois': []}}


def load_realm_affine_transforms(path: Path | str | None = None) -> Dict[str, Any]:
    """Read optional offline calibration. Invalid entries fail back to the bbox.

    No WAD reads or numpy dependency in telemetry. Restart the server after
    regenerating the calibration; the module loads the small JSON once.
    """
    if path is None:
        path = DATA / 'realm_affine_transforms.json'
    try:
        document = json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}
    if not isinstance(document, dict) or document.get('schema_version') != 1:
        return {}
    records = document.get('realms')
    if not isinstance(records, dict):
        return {}

    def finite(value):
        return type(value) in (int, float) and math.isfinite(value)

    def measured_hull(points):
        points = sorted(set(points))
        def half(sequence):
            result = []
            for p in sequence:
                while len(result) >= 2:
                    a, b = result[-2:]
                    if (b[0]-a[0])*(p[1]-a[1]) - (b[1]-a[1])*(p[0]-a[0]) > 0:
                        break
                    result.pop()
                result.append(p)
            return result
        return half(points)[:-1] + half(reversed(points))[:-1]

    def valid(record, zone=False):
        if not isinstance(record, dict):
            return False
        if zone:
            bounds = record.get('world_bounds')
            if not isinstance(bounds, dict) or not bounds:
                return False
            for axis, extent in bounds.items():
                if axis not in ('x', 'y', 'z') or not isinstance(extent, list) or len(extent) != 2:
                    return False
                if any(v is not None and not finite(v) for v in extent):
                    return False
                if all(v is not None for v in extent) and extent[0] >= extent[1]:
                    return False
        if record.get('status') == 'proven_wad' and record.get('method') == 'piecewise_affine':
            zones = record.get('zones')
            if (zone or record.get('matrix') is not None or not isinstance(zones, list) or len(zones) < 2
                    or not all(valid(z, zone=True) for z in zones)):
                return False
            # A complete partition has no gap, overlap, or uncovered end.
            if any(len(z['world_bounds']) != 1 for z in zones):
                return False
            axis = next(iter(zones[0]['world_bounds']))
            if any(axis not in z['world_bounds'] for z in zones):
                return False
            ranges = sorted((z['world_bounds'][axis] for z in zones),
                            key=lambda extent: float('-inf') if extent[0] is None else extent[0])
            return (ranges[0][0] is None and ranges[-1][1] is None
                    and all(a[1] is not None and b[0] is not None and a[1] == b[0]
                            for a, b in zip(ranges, ranges[1:])))
        if record.get('status') == 'proven_wad':
            if record.get('method') != 'affine_ransac_lstsq':
                return False
            axes, matrix = record.get('axes'), record.get('matrix')
            if (not isinstance(axes, list) or len(axes) != 2
                    or any(type(a) is not int or a not in (0, 1, 2) for a in axes)
                    or axes[0] == axes[1]):
                return False
            if (not isinstance(matrix, list) or len(matrix) != 2
                    or any(not isinstance(row, list) or len(row) != 3
                           or not all(finite(v) for v in row) for row in matrix)):
                return False
            if abs(matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]) < 1e-20:
                return False
            bounds = record.get('map_bounds', {})
            if (not isinstance(bounds, dict) or not all(finite(bounds.get(k)) for k in
                    ('lat_min', 'lat_max', 'lng_min', 'lng_max'))
                    or bounds['lat_min'] >= bounds['lat_max'] or bounds['lng_min'] >= bounds['lng_max']):
                return False
            refs, inliers = record.get('references'), record.get('inliers')
            minimum = 4
            if (not isinstance(refs, list) or not isinstance(inliers, list) or len(set(inliers)) < minimum
                    or any(type(i) is not int or not 0 <= i < len(refs) for i in inliers)):
                return False
            for p in refs:
                if (not isinstance(p, dict) or not all(k in p for k in ('pin_id', 'world', 'lat', 'lng'))
                        or not isinstance(p['world'], list) or len(p['world']) != 3
                        or not all(finite(v) for v in p['world'])
                        or not finite(p['lat']) or not finite(p['lng'])):
                    return False
            accepted = {tuple(refs[i]['world'][a] for a in axes) for i in inliers}
            if len(accepted) < minimum or record.get('threshold') != .003:
                return False
            domain = record.get('domain', {})
            if (not isinstance(domain, dict) or domain.get('kind') != 'interpolation_hull_with_negative_controls'
                    or domain.get('boundary_tolerance') != 0.0):
                return False
            hull, excluded = domain.get('hull'), domain.get('excluded')
            if (not isinstance(hull, list) or len(hull) < 3 or not isinstance(excluded, list)
                    or any(not isinstance(p, list) or len(p) != 2 or not all(finite(v) for v in p) for p in hull)):
                return False
            if any(not isinstance(p, dict) or not isinstance(p.get('world'), list) or len(p['world']) != 3
                   or not all(finite(v) for v in p['world']) for p in excluded):
                return False
            # Reconstruct from measured positive controls, including compatible
            # f16 native anchors of f32 inlier origins. Never accept padding.
            positive_controls = set(accepted)
            negative = {tuple(p['world'][a] for a in axes) for p in excluded}
            for i, p in enumerate(refs):
                samples = [p['world']]
                if p.get('icon') == 'goMapIconFastTravel':
                    samples.append(p['marker_world'])
                    if p.get('wad_gateway_candidates'):
                        samples.append(p['wad_gateway_candidates'][0]['world'])
                for xyz in samples:
                    if (not isinstance(xyz, list) or len(xyz) != 3
                            or not all(finite(v) for v in xyz)):
                        return False
                    uv = tuple(xyz[a] for a in axes)
                    error = math.hypot(*(sum(row[j]*uv[j] for j in (0, 1)) + row[2] - target
                                         for row, target in zip(matrix, (p['lat'], p['lng']))))
                    if xyz is p['world'] and i in inliers and error > .003:
                        return False
                    if i in inliers and error <= .003:
                        positive_controls.add(uv)
                    if (i not in inliers or error > .003) and uv not in negative:
                        return False
            if [tuple(p) for p in hull] != measured_hull(positive_controls):
                return False
        elif record.get('status') != 'fallback_bbox':
            return False
        zones = record.get('zones', [])
        return isinstance(zones, list) and all(valid(z, zone=True) for z in zones)

    result = {}
    for key, record in records.items():
        try:
            if key in REALM_BOUNDING_BOXES and valid(record):
                result[key] = record
        except (TypeError, ValueError, KeyError, RecursionError):
            continue
    return result


REALM_AFFINE_TRANSFORMS = load_realm_affine_transforms()


def load_realm_similarity_transforms(path: Path | str | None = None) -> Dict[str, Any]:
    """Подобие по двум реперам для миров без доказанной аффинной матрицы.

    Бриф Шага 1: «similarity transform 4 DOF требует всего 2 реперные точки —
    честная пометка similarity_2pt». Строгий загрузчик выше оставляет такие
    миры fallback_bbox; здесь из тех же реперов строится приближение без
    отражения (у всех доказанных миров det > 0). Опора — пара с самой длинной
    базой. Независимой проверки у такой пары нет, поэтому статус отдельный.
    """
    if path is None:
        path = DATA / 'realm_affine_transforms.json'
    try:
        document = json.loads(Path(path).read_text(encoding='utf-8'))
        records = document['realms'] if document.get('schema_version') == 1 else {}
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        return {}
    result = {}
    for key, record in (records.items() if isinstance(records, dict) else ()):
        try:
            if key not in REALM_BOUNDING_BOXES or record.get('status') != 'fallback_bbox':
                continue
            axes = record.get('axes') or [0, 2]
            bounds = record['map_bounds']
            if not all(math.isfinite(bounds[k]) for k in ('lat_min', 'lat_max', 'lng_min', 'lng_max')):
                continue
            refs = [r for r in record.get('references') or []
                    if len(r['world']) == 3 and all(math.isfinite(v) for v in (*r['world'], r['lat'], r['lng']))]
            best = None
            for i, a in enumerate(refs):
                for b in refs[i + 1:]:
                    du = complex(b['world'][axes[0]] - a['world'][axes[0]], b['world'][axes[1]] - a['world'][axes[1]])
                    dp = complex(b['lat'] - a['lat'], b['lng'] - a['lng'])
                    if abs(du) >= 10.0 and abs(dp) > 1e-6 and (best is None or abs(du) > abs(best[2])):
                        best = (a, b, du, dp)
            if not best:
                continue
            a, b, du, dp = best
            s = dp / du
            ua = complex(a['world'][axes[0]], a['world'][axes[1]])
            t = complex(a['lat'], a['lng']) - s * ua
            result[key] = {
                'id': None, 'method': 'similarity_2pt', 'axes': list(axes), 'map_bounds': dict(bounds),
                'matrix': [[s.real, -s.imag, t.real], [s.imag, s.real, t.imag]],
                'references': [a, b], 'inliers': [0, 1],
                'scale': abs(s), 'rotation_deg': math.degrees(math.atan2(s.imag, s.real)),
            }
        except (TypeError, ValueError, KeyError, AttributeError, ZeroDivisionError):
            continue
    return result


REALM_SIMILARITY_TRANSFORMS = load_realm_similarity_transforms()


def _fit_live_similarity(refs, threshold=.003):
    """Bounded deterministic RANSAC, followed by complex least squares (4 DOF).

    For 3+ refs require >=3 inliers and a strict majority. A split model is
    ambiguous; a single rejected reference cannot prove a new translation zone.
    """
    import random
    n = len(refs)
    if n < 2:
        return None
    u = [complex(r['world'][0], r['world'][2]) for r in refs]
    v = [complex(r['lat'], r['lng']) for r in refs]
    if n <= 32:
        pairs = [(i,j) for i in range(n) for j in range(i+1,n)]
    else:
        rng = random.Random(0)
        pairs = sorted(set(tuple(sorted(rng.sample(range(n), 2))) for _ in range(512)))
    best = None
    for i,j in pairs:
        if abs(u[j]-u[i]) < 10 or abs(v[j]-v[i]) < 1e-6:
            continue
        scale = (v[j]-v[i])/(u[j]-u[i]); offset = v[i]-scale*u[i]
        residuals = [abs(scale*x+offset-y) for x,y in zip(u,v)]
        inliers = [k for k,e in enumerate(residuals) if e <= threshold]
        score = (len(inliers), -sum(min(e,threshold)**2 for e in residuals))
        if best is None or score > best[0]:
            best = score, scale, offset, inliers
    if best is None:
        return None
    _, scale, offset, inliers = best
    required = 2 if n == 2 else max(3,n//2+1)
    if len(inliers) < required:
        return None
    for _ in range(5):
        mean_u = sum(u[i] for i in inliers)/len(inliers)
        mean_v = sum(v[i] for i in inliers)/len(inliers)
        denom = sum(abs(u[i]-mean_u)**2 for i in inliers)
        if denom <= 0:
            return None
        scale = sum((u[i]-mean_u).conjugate()*(v[i]-mean_v) for i in inliers)/denom
        offset = mean_v-scale*mean_u
        residuals = [abs(scale*x+offset-y) for x,y in zip(u,v)]
        new_inliers = [i for i,e in enumerate(residuals) if e <= threshold]
        if new_inliers == inliers:
            break
        if len(new_inliers) < required:
            return None
        inliers = new_inliers
    return scale, offset, inliers, residuals


def _live_wad_conflicts(key, refs):
    record = REALM_AFFINE_TRANSFORMS.get(key, {})
    conflicts = []
    for i,ref in enumerate(refs):
        xyz = ref['world']
        candidates = [z for z in record.get('zones', []) if z.get('status') == 'proven_wad'
                      and all((lo is None or xyz['xyz'.index(axis)] >= lo)
                              and (hi is None or xyz['xyz'.index(axis)] < hi)
                              for axis,(lo,hi) in z.get('world_bounds',{}).items())]
        if not candidates and record.get('status') == 'proven_wad' and record.get('matrix'):
            candidates = [record]
        for model in candidates:
            u,v = (xyz[j] for j in model['axes'])
            lat,lng = (r[0]*u+r[1]*v+r[2] for r in model['matrix'])
            error = math.hypot(lat-ref['lat'],lng-ref['lng'])
            if error > .01:
                conflicts.append(dict(ref_index=i, zone=model.get('id'), error=error,
                                      wad_lat=lat, wad_lng=lng,
                                      inside_proven_domain=(not _affine_domain_reason(model,xyz)
                                                            if model.get('domain') else False)))
    return conflicts


def load_live_realm_transforms(path: Path | str | None = None) -> Dict[str, Any]:
    """Проекции по реперам, проверенным на живой игре (data/gow_pins/live_realm_refs.json).

    Два репера → подобие без отражения (как similarity_2pt), но обе точки взяты
    из памяти игры и положения на её собственной карте, а не из меток .wad.
    Зоны — места мира, нарисованные на карте не там, где лежат (арена Горнила):
    тот же масштаб и поворот, сдвиг по метке зоны. Возвращает {мир: [модели]}.
    """
    if path is None:
        path = LIVE_REFS if LIVE_REFS.is_file() else DATA / 'live_realm_refs.json'
    try:
        document = json.loads(Path(path).read_text(encoding='utf-8'))
        records = document['realms'] if document.get('schema_version') == 1 else {}
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        return {}
    result = {}
    for key,record in (records.items() if isinstance(records,dict) else ()):
        if key not in REALM_BOUNDING_BOXES or not isinstance(record,dict):
            continue
        refs, original_indices = [], []
        for i,r in enumerate(record.get('refs') or []):
            try:
                if len(r['world']) == 3 and all(type(v) in (int,float) and math.isfinite(v)
                                               for v in (*r['world'],r['lat'],r['lng'])):
                    refs.append(dict(r, pin_id=r.get('pin_id', f'live:{i}')))
                    original_indices.append(i)
            except (KeyError,TypeError,ValueError):
                continue
        fit = _fit_live_similarity(refs)
        seeded = False
        if not fit:
            # Preserve measured owner anchors when a third point first visits
            # an inset: two-vs-one cannot be resolved from geometry alone.
            trusted = [i for i,r in enumerate(refs) if isinstance(r.get('source'), str) and r['source']
                       and not r['source'].startswith('auto_')]
            seed = _fit_live_similarity([refs[i] for i in trusted])
            if seed:
                s,t,_,_ = seed
                residuals = [abs(s*complex(r['world'][0],r['world'][2])+t-complex(r['lat'],r['lng'])) for r in refs]
                fit = s,t,[i for i,e in enumerate(residuals) if e <= .003],residuals
                seeded = True
        if not fit:
            continue
        scale,offset,inliers,residuals = fit
        meta = REALM_BOUNDING_BOXES[key]
        bounds = (REALM_AFFINE_TRANSFORMS.get(key) or {}).get('map_bounds') or {
            k:meta['map_'+k] for k in ('lat_min','lat_max','lng_min','lng_max')}
        conflicts = _live_wad_conflicts(key,refs)
        for conflict in conflicts:
            conflict['ref_index'] = original_indices[conflict['ref_index']]
        report = dict(threshold=.003, method='similarity_2pt' if len(refs)==2 else 'ransac_similarity',
                      inliers=[original_indices[i] for i in inliers],
                      outliers=[original_indices[i] for i in range(len(refs)) if i not in inliers],
                      residuals=residuals, residual_ref_indices=original_indices,
                      rmse=math.sqrt(sum(residuals[i]**2 for i in inliers)/len(inliers)),
                      wad_conflicts=conflicts)
        if seeded:
            report['method'] = 'manual_seed_ambiguous_consensus'
        def model(identifier, translation, indices, method='live_similarity'):
            return dict(id=identifier, method=method, axes=[0,2], map_bounds=dict(bounds),
                        matrix=[[scale.real,-scale.imag,translation.real],
                                [scale.imag,scale.real,translation.imag]],
                        references=[],inliers=[],calibration_refs=[refs[i] for i in indices],
                        scale=abs(scale), rotation_deg=math.degrees(math.atan2(scale.imag,scale.real)),
                        fit_report=dict(report, inliers=[original_indices[i] for i in indices]))
        models = [model('live',offset,inliers)]
        rejected = [i for i in range(len(refs)) if i not in inliers]
        translations = {i:complex(refs[i]['lat'],refs[i]['lng'])-
                          scale*complex(refs[i]['world'][0],refs[i]['world'][2]) for i in rejected}
        while rejected:
            clusters = [[j for j in rejected if abs(translations[j]-translations[i]) <= .003] for i in rejected]
            group = max(clusters,key=len)
            if len(group) < 2:
                break
            center = sum(translations[i] for i in group)/len(group)
            group = [i for i in group if abs(translations[i]-center) <= .003]
            if len(group) < 2:
                break
            span = max(math.hypot(refs[i]['world'][0]-refs[j]['world'][0],
                                  refs[i]['world'][2]-refs[j]['world'][2]) for i in group for j in group)
            if span >= 15:
                zone = model(f'live:auto:{original_indices[group[0]]}', center, group, 'live_similarity_zone')
                zone['zone_radius_m'] = max(30.,span*1.5)
                zone['fit_report'] = dict(zone['fit_report'],
                                         method='shared_similarity_translation_cluster', outliers=[],
                                         residuals=[abs(translations[i]-center) for i in group],
                                         residual_ref_indices=[original_indices[i] for i in group],
                                         rmse=math.sqrt(sum(abs(translations[i]-center)**2 for i in group)/len(group)))
                models.append(zone)
            rejected = [i for i in rejected if i not in group]
        for zone in record.get('zones') or []:
            try:
                anchor = zone['anchor_world']
                if len(anchor) != 3 or not all(math.isfinite(v) for v in (*anchor,zone['anchor_lat'],zone['anchor_lng'])):
                    continue
                translation = complex(zone['anchor_lat'],zone['anchor_lng'])-scale*complex(anchor[0],anchor[2])
                m = model(f"live:{zone['id']}",translation,[], 'live_similarity_zone')
                m['calibration_refs'] = [dict(world=anchor,lat=zone['anchor_lat'],lng=zone['anchor_lng'])]
                m['fit_report'] = dict(report, method='manual_anchor_shared_similarity', inliers=[],
                                       outliers=[],residuals=[],residual_ref_indices=[],rmse=None)
                models.append(m)
            except (KeyError,TypeError,ValueError):
                continue
        result[key] = models
    return result


REALM_LIVE_TRANSFORMS = {}  # initialized after the WAD domain helper below
_LIVE_REFS_PATH = LIVE_REFS if LIVE_REFS.is_file() else DATA / 'live_realm_refs.json'
_LIVE_REFS_STAMP = None


def refresh_live_realm_transforms(path=None):
    """Atomic model swap on reference-file change; strict WAD is independent."""
    global REALM_LIVE_TRANSFORMS, _LIVE_REFS_STAMP
    target = Path(path) if path is not None else (LIVE_REFS if LIVE_REFS.is_file() else DATA / 'live_realm_refs.json')
    try:
        stat = target.stat()
        stamp = (str(target), stat.st_mtime_ns, stat.st_size)
    except OSError:
        stamp = None
    if stamp != _LIVE_REFS_STAMP:
        REALM_LIVE_TRANSFORMS = load_live_realm_transforms(target)
        _LIVE_REFS_STAMP = stamp
    return REALM_LIVE_TRANSFORMS
# Насколько приближённая проекция может выйти за рамку карты мира, прежде чем
# точку признают чужой (не этот мир, мусор памяти). Доли lat/lng MapGenie.
APPROX_MAP_MARGIN = 0.03


def _affine_domain_reason(model, xyz):
    axes = model['axes']
    u, v = (xyz[a] for a in axes)
    domain = model['domain']
    hull = domain['hull']
    # The tiny relative tolerance is floating-point roundoff, not a spatial
    # extension of the measured hull.
    for a, b in zip(hull, hull[1:] + hull[:1]):
        cross = (b[0]-a[0])*(v-a[1]) - (b[1]-a[1])*(u-a[0])
        scale = max(1., abs((b[0]-a[0])*(v-a[1])), abs((b[1]-a[1])*(u-a[0])))
        if cross < -1e-12 * scale:
            return 'outside_calibrated_domain'
    accepted_distance = min(math.hypot(u-model['references'][i]['world'][axes[0]],
                                       v-model['references'][i]['world'][axes[1]]) for i in model['inliers'])
    for point in domain['excluded']:
        if math.hypot(u-point['world'][axes[0]], v-point['world'][axes[1]]) <= accepted_distance:
            return 'near_contradictory_reference'
    return None


REALM_LIVE_TRANSFORMS = load_live_realm_transforms()


def _select_realm_affine(realm_key: str, xyz: Tuple[float, float, float]):
    record = REALM_AFFINE_TRANSFORMS.get(realm_key, {})
    for zone in record.get('zones', []):
        if zone.get('status') != 'proven_wad':
            continue
        if all((extent[0] is None or xyz['xyz'.index(axis)] >= extent[0])
               and (extent[1] is None or xyz['xyz'.index(axis)] < extent[1])
               for axis, extent in zone['world_bounds'].items()):
            reason = _affine_domain_reason(zone, xyz)
            return (None, reason) if reason else (zone, None)
    if record.get('status') == 'proven_wad' and record.get('matrix'):
        reason = _affine_domain_reason(record, xyz)
        return (None, reason) if reason else (record, None)
    return None, record.get('reason', 'calibration_unavailable')


def _approximate_realm_model(realm_key: str, xyz: Tuple[float, float, float]):
    """Лучшая недоказанная проекция: (модель, статус) или (None, None).

    extrapolated_wad — доказанная матрица мира (или зона Ванахейма по высоте)
    за пределами измеренной области. На реперах, не вошедших в область,
    ошибка ≤0.02 у 21/24 Мидгарда, 11/12 Альфхейма, 21/21 Свартальфхейма —
    против 0.13–0.29 у рамки. similarity_2pt — подобие по двум реперам.
    Точка, проецирующаяся дальше APPROX_MAP_MARGIN за рамку карты, отвергается.
    """
    record = REALM_AFFINE_TRANSFORMS.get(realm_key, {})
    model, status = None, None
    for zone in record.get('zones', []):
        if zone.get('status') == 'proven_wad' and all(
                (extent[0] is None or xyz['xyz'.index(axis)] >= extent[0])
                and (extent[1] is None or xyz['xyz'.index(axis)] < extent[1])
                for axis, extent in zone['world_bounds'].items()):
            model, status = zone, 'extrapolated_wad'
            break
    if model is None and record.get('status') == 'proven_wad' and record.get('matrix'):
        model, status = record, 'extrapolated_wad'
    def distance(m):
        return min((math.dist(xyz,r['world']) for r in m['calibration_refs']), default=float('inf'))
    live = sorted(REALM_LIVE_TRANSFORMS.get(realm_key, []), key=distance)
    candidates = [(m, 'live_similarity') for m in live
                  if not m.get('zone_radius_m') or distance(m) <= m['zone_radius_m']]
    if model is not None:
        candidates.append((model,status))
    if realm_key in REALM_SIMILARITY_TRANSFORMS:
        candidates.append((REALM_SIMILARITY_TRANSFORMS[realm_key], 'similarity_2pt'))
    for model, status in candidates:
        u, v = (xyz[i] for i in model['axes'])
        lat_row, lng_row = model['matrix']
        lat = lat_row[0] * u + lat_row[1] * v + lat_row[2]
        lng = lng_row[0] * u + lng_row[1] * v + lng_row[2]
        b = model['map_bounds']
        m = APPROX_MAP_MARGIN
        if b['lat_min'] - m <= lat <= b['lat_max'] + m and b['lng_min'] - m <= lng <= b['lng_max'] + m:
            return model, status
    return None, None


def normalize_coordinates(
    realm_key: str,
    x: float,
    y: float,
    z: float = 0.0,
    strict: bool = False,
) -> Dict[str, Any]:
    """Нормализация мировых координат Кратоса в процентный диапазон 0..100% и координаты Leaflet (Задача 166, 174, 182)."""
    r_key = (realm_key or "midgard").lower().strip()
    meta = REALM_BOUNDING_BOXES.get(r_key)
    if not meta:
        for k, v in REALM_BOUNDING_BOXES.items():
            # Сейв называет мир «Муспельхейм - …», справочник — «Муспельхейм (Горнило)»:
            # сравниваем по названию до скобки, иначе живой Кратос уезжал в Мидгард.
            if (k in r_key or r_key in k or v["name"].lower() in r_key
                    or v["name"].split(" (")[0].lower() in r_key):
                meta = v
                r_key = k
                break
    if not meta:
        meta = REALM_BOUNDING_BOXES["midgard"]
        r_key = "midgard"

    if not all(math.isfinite(v) for v in (x, y, z)):
        raise ValueError('World coordinates must be finite')
    affine, projection_reason = _select_realm_affine(r_key, (x, y, z))
    projection_status = 'proven_wad' if affine else 'fallback_bbox'
    if not affine and not strict:
        approx, approx_status = _approximate_realm_model(r_key, (x, y, z))
        if approx:
            affine, projection_status = approx, approx_status

    min_x = meta["min_x"]
    max_x = meta["max_x"]
    min_y = meta["min_y"]
    max_y = meta["max_y"]

    width = max_x - min_x
    height = max_y - min_y

    in_bounds = (min_x <= x <= max_x) and (min_y <= y <= max_y)
    if not affine and r_key in REALM_AFFINE_TRANSFORMS:
        # A bbox coordinate is retained for old consumers, but does not certify
        # a position rejected by the measured projection's applicability guard.
        in_bounds = False

    norm_x = (x - min_x) / width * 100.0 if width > 0 else 50.0
    norm_y = (y - min_y) / height * 100.0 if height > 0 else 50.0

    pct_x = round(max(0.0, min(100.0, norm_x)), 2)
    # Инвертируем Y для отрисовки на экране (+Y на север = вверх)
    pct_y = round(max(0.0, min(100.0, 100.0 - norm_y)), 2)

    # Leaflet-координаты (lat, lng) на тайловой карте
    map_lat_min = meta.get("map_lat_min", 0.5060)
    map_lat_max = meta.get("map_lat_max", 0.9097)
    map_lng_min = meta.get("map_lng_min", -0.9851)
    map_lng_max = meta.get("map_lng_max", -0.3888)

    norm_x_ratio = max(0.0, min(1.0, norm_x / 100.0))
    norm_y_ratio = max(0.0, min(1.0, norm_y / 100.0))
    map_lat = round(map_lat_min + norm_y_ratio * (map_lat_max - map_lat_min), 6)
    map_lng = round(map_lng_min + norm_x_ratio * (map_lng_max - map_lng_min), 6)

    poi_source = meta.get('pois', [])
    if affine:
        bounds = affine['map_bounds']
        map_lat_min, map_lat_max = bounds['lat_min'], bounds['lat_max']
        map_lng_min, map_lng_max = bounds['lng_min'], bounds['lng_max']
        xyz = (x, y, z)
        u, v = (xyz[i] for i in affine['axes'])
        lat_row, lng_row = affine['matrix']
        lat = lat_row[0] * u + lat_row[1] * v + lat_row[2]
        lng = lng_row[0] * u + lng_row[1] * v + lng_row[2]
        in_bounds = map_lat_min <= lat <= map_lat_max and map_lng_min <= lng <= map_lng_max
        map_lat = max(map_lat_min, min(map_lat_max, round(lat, 6)))
        map_lng = max(map_lng_min, min(map_lng_max, round(lng, 6)))
        pct_x = round(max(0., min(100., (lng - map_lng_min) / (map_lng_max - map_lng_min) * 100)), 2)
        pct_y = round(max(0., min(100., (map_lat_max - lat) / (map_lat_max - map_lat_min) * 100)), 2)
        # Only measured inlier POIs have trustworthy world positions. Legacy
        # hand-written POIs belong to the fallback square and cannot be mixed.
        poi_source = [dict(id=p['pin_id'], name=p['pin_id'], x=p['world'][0], y=p['world'][1],
                           z=p['world'][2], lat=p['lat'], lng=p['lng'])
                      for i in affine['inliers'] for p in [affine['references'][i]]]

    pois_out = []
    closest_poi = None
    min_dist = float("inf")

    for p in poi_source:
        p_x = p["x"]
        p_y = p["y"]
        p_norm_x = round(max(0.0, min(100.0, (p_x - min_x) / width * 100.0)), 2) if width > 0 else 50.0
        p_norm_y = round(max(0.0, min(100.0, 100.0 - (p_y - min_y) / height * 100.0)), 2) if height > 0 else 50.0
        p_lat = p.get("lat") or round(map_lat_min + (p_norm_x / 100.0) * (map_lat_max - map_lat_min), 6)
        p_lng = p.get("lng") or round(map_lng_min + (p_norm_x / 100.0) * (map_lng_max - map_lng_min), 6)
        dist = math.hypot(x - p_x, y - p_y)
        if affine:
            p_norm_x = round(max(0., min(100., (p['lng'] - map_lng_min) / (map_lng_max - map_lng_min) * 100)), 2)
            p_norm_y = round(max(0., min(100., (map_lat_max - p['lat']) / (map_lat_max - map_lat_min) * 100)), 2)
            point = (p_x, p_y, p['z'])
            dist = math.hypot(*(a - b for a, b in
                               ((xyz[i], point[i]) for i in affine['axes'])))
        poi_info = {
            "id": p["id"],
            "name": p["name"],
            "x": p_x,
            "y": p_y,
            "lat": p_lat,
            "lng": p_lng,
            "pct_x": p_norm_x,
            "pct_y": p_norm_y,
            "distance_units": round(dist, 1),
            # WAD-реперы в метрах (мир Муспельхейма ~800 ед. поперёк);
            # рукописные метки старой рамки — в сантиметрах.
            "distance_meters": round(dist if affine else dist / 100.0, 1),
        }
        pois_out.append(poi_info)
        if dist < min_dist:
            min_dist = dist
            closest_poi = poi_info

    return {
        "realm_key": r_key,
        "realm_name": meta["name"],
        "slug": meta.get("slug", r_key),
        "raw_x": round(x, 2),
        "raw_y": round(y, 2),
        "raw_z": round(z, 2),
        "pct_x": pct_x,
        "pct_y": pct_y,
        "map_lat": map_lat,
        "map_lng": map_lng,
        "center_lat": meta.get("center_lat", map_lat),
        "center_lng": meta.get("center_lng", map_lng),
        "min_zoom": meta.get("min_zoom", 9),
        "max_zoom": meta.get("max_zoom", 14),
        "initial_zoom": meta.get("initial_zoom", 11),
        "tile_pattern": meta.get("tile_pattern", f"https://tiles.mapgenie.io/games/god-of-war-ragnarok/{r_key}/default-v1/{{z}}/{{x}}/{{y}}.jpg"),
        "in_bounds": in_bounds,
        "closest_poi": closest_poi,
        "pois": pois_out,
        # Доля lat/lng карты на метр мира: карта переводит расстояние до пина в метры.
        "map_scale_per_metre": (math.sqrt(abs(affine['matrix'][0][0] * affine['matrix'][1][1]
                                              - affine['matrix'][0][1] * affine['matrix'][1][0])) if affine else None),
        "projection_status": projection_status,
        # proven — внутри измеренной области; approximate — честное приближение
        # (extrapolated_wad / similarity_2pt); none — рамка, точке верить нельзя.
        "projection_confidence": ('proven' if projection_status == 'proven_wad'
                                  else 'none' if projection_status == 'fallback_bbox' else 'approximate'),
        "projection_method": affine['method'] if affine else 'fallback_bbox',
        "projection_axes": affine['axes'] if affine else [0, 1],
        "projection_zone": affine.get('id') if affine else None,
        "projection_reason": projection_reason,
        "projection_report": affine.get('fit_report') if affine else None,
    }


def map_heading_deg(realm_key: str, x: float, y: float, z: float, world_yaw_deg: float) -> Optional[float]:
    """Направление взгляда на карте: 0 — вверх (север, +lat), 90 — вправо (+lng).

    Мировой угол: +Z = 0°, +X = 90°, Y вверх (живая калибровка 14.11.2026).
    Считается через ту же проекцию, что и позиция: шаг 5 м по направлению
    взгляда и пеленг между двумя точками карты. Рамка (confidence none) — None.
    """
    try:
        yaw = math.radians(float(world_yaw_deg))
    except (TypeError, ValueError):
        return None
    if not math.isfinite(yaw):
        return None
    a = normalize_coordinates(realm_key, x, y, z)
    if a.get('projection_confidence') == 'none':
        return None
    b = normalize_coordinates(realm_key, x + 5.0 * math.sin(yaw), y, z + 5.0 * math.cos(yaw))
    if b.get('projection_status') != a.get('projection_status') or b.get('projection_zone') != a.get('projection_zone'):
        return None
    d_lat, d_lng = b['map_lat'] - a['map_lat'], b['map_lng'] - a['map_lng']
    if abs(d_lat) + abs(d_lng) < 1e-9:
        return None
    return round(math.degrees(math.atan2(d_lng, d_lat)) % 360.0, 1)


@dataclass(frozen=True)
class BuildFingerprint:
    file_size: int
    pe_timestamp: int
    header_sha256: str

    def matches(self, known: Dict[str, Any]) -> bool:
        if self.header_sha256 and known.get("header_sha256"):
            return self.header_sha256.lower() == known["header_sha256"].lower()
        return True


def get_exe_fingerprint(exe_path: Path | str) -> Optional[BuildFingerprint]:
    """Извлекает отпечаток исполняемого файла GoWR.exe."""
    p = Path(exe_path)
    if not p.is_file():
        return None

    try:
        size = p.stat().st_size
        with open(p, "rb") as f:
            header_4k = f.read(4096)
            if len(header_4k) < 0x100:
                return None
            e_lfanew = struct.unpack_from("<I", header_4k, 0x3C)[0]
            if e_lfanew + 24 > len(header_4k):
                f.seek(e_lfanew)
                pe_block = f.read(24)
            else:
                pe_block = header_4k[e_lfanew:e_lfanew + 24]

            if not pe_block.startswith(b"PE\x00\x00"):
                return None
            timestamp = struct.unpack_from("<I", pe_block, 8)[0]
            h_sha256 = hashlib.sha256(header_4k).hexdigest()

        return BuildFingerprint(
            file_size=size,
            pe_timestamp=timestamp,
            header_sha256=h_sha256,
        )
    except (OSError, struct.error):
        return None


def validate_behavior(
    x: float, y: float, z: float,
    hp: float, max_hp: float,
    rage: float, max_rage: float,
) -> bool:
    """Строгая проверка правдоподобия поведения метрик Кратоса.

    Поле без подтверждения не публикуется.
    """
    # 1. Проверка на нечисловые значения (NaN, Inf)
    for val in (x, y, z, hp, max_hp, rage, max_rage):
        if math.isnan(val) or math.isinf(val):
            return False

    # 2. Координаты игрового мира (не улетели в бесконечность)
    if abs(x) > 200000.0 or abs(y) > 200000.0 or abs(z) > 100000.0:
        return False

    # 3. Здоровье: от 0 до max_hp (max_hp обычно 100..2000)
    if max_hp <= 0.0 or max_hp > 50000.0:
        return False
    if hp < 0.0 or hp > max_hp * 1.05:  # небольшой допуск на оверхп
        return False

    # 4. Ярость: от 0 до max_rage (max_rage обычно 100..500)
    if max_rage <= 0.0 or max_rage > 5000.0:
        return False
    if rage < 0.0 or rage > max_rage * 1.05:
        return False

    return True


# Маппинг элементов урона босса
BOSS_ELEMENT_MAP: Dict[int, str] = {
    0: "none",
    1: "fire",
    2: "frost",
    3: "sonic",  # Бифрёст / звук
}


def validate_boss_behavior(
    hp: float, max_hp: float,
    shield_hp: Optional[float] = None,
    shield_max: Optional[float] = None,
    phase: Optional[int] = None,
) -> bool:
    """Валидация метрик босса. Если значения невалидны — не публикуем."""
    for val in (hp, max_hp):
        if val is None or math.isnan(val) or math.isinf(val):
            return False

    if max_hp <= 0.0 or max_hp > 200000.0:
        return False
    if hp < 0.0 or hp > max_hp * 1.05:
        return False

    if shield_hp is not None and shield_max is not None:
        if math.isnan(shield_hp) or math.isnan(shield_max):
            return False
        if shield_max < 0 or shield_hp < 0:
            return False

    if phase is not None and (phase < 0 or phase > 20):
        return False

    return True


def validate_cooldowns(cooldowns: Dict[str, Optional[float]]) -> Dict[str, float]:
    """Фильтрует и нормализует кулдауны. Возвращает только валидные (0..300 сек)."""
    valid: Dict[str, float] = {}
    for name, val in cooldowns.items():
        if val is None:
            continue
        if math.isnan(val) or math.isinf(val):
            continue
        # Кулдаун 0 = готов, >0 = отсчёт в секундах, <0 игнорируем
        if 0.0 <= val <= 300.0:
            valid[name] = round(val, 1)
    return valid


class SafeProcessMemory:
    """Безопасная обёртка вокруг ReadProcessMemory с гарантией READ-ONLY."""

    def __init__(self, pid: int, h_process: int, base_address: int):
        self.pid = pid
        self.h_process = h_process
        self.base_address = base_address

    @classmethod
    def open(cls, pid: int) -> Optional[SafeProcessMemory]:
        """Открывает процесс строго с правами на чтение."""
        _configure_winapi()
        k32 = ctypes.windll.kernel32
        h_proc = k32.OpenProcess(SAFE_ACCESS_MASK, False, pid)
        if not h_proc:
            return None

        # Определение базового адреса модуля через EnumProcessModules
        base_addr = 0
        try:
            psapi = ctypes.windll.psapi
            h_mods = (ctypes.wintypes.HMODULE * 1)()
            cb_needed = ctypes.wintypes.DWORD()
            if psapi.EnumProcessModules(h_proc, h_mods, ctypes.sizeof(h_mods), ctypes.byref(cb_needed)):
                base_addr = h_mods[0]
        except Exception:
            pass

        if not base_addr:
            k32.CloseHandle(h_proc)
            return None

        return cls(pid, h_proc, base_addr)

    def close(self) -> None:
        if self.h_process:
            ctypes.windll.kernel32.CloseHandle(self.h_process)
            self.h_process = 0

    def __enter__(self) -> SafeProcessMemory:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

    def read_raw(self, address: int, size: int) -> Optional[bytes]:
        """Читает произвольный блок байтов из памяти процесса."""
        if not self.h_process or address < 0x10000 or address > 0x7FFFFFFFFFFF:
            return None
        buf = ctypes.create_string_buffer(size)
        bytes_read = ctypes.c_size_t(0)
        res = ctypes.windll.kernel32.ReadProcessMemory(
            self.h_process,
            ctypes.c_void_p(address),
            buf,
            size,
            ctypes.byref(bytes_read),
        )
        if res and bytes_read.value == size:
            return buf.raw
        return None

    def read_uint64(self, address: int) -> Optional[int]:
        raw = self.read_raw(address, 8)
        if raw and len(raw) == 8:
            return struct.unpack("<Q", raw)[0]
        return None

    def read_float(self, address: int) -> Optional[float]:
        raw = self.read_raw(address, 4)
        if raw and len(raw) == 4:
            return struct.unpack("<f", raw)[0]
        return None

    def read_int32(self, address: int) -> Optional[int]:
        raw = self.read_raw(address, 4)
        if raw and len(raw) == 4:
            return struct.unpack("<i", raw)[0]
        return None

    def resolve_chain(self, start_addr: int, offsets: List[int]) -> Optional[int]:
        """Разрешает цепочку указателей pointer -> offset1 -> offset2."""
        cur = start_addr
        for off in offsets:
            ptr = self.read_uint64(cur)
            if not ptr or ptr < 0x10000 or ptr > 0x7FFFFFFFFFFF:
                return None
            cur = ptr + off
        return cur


def find_gowr_process() -> Optional[Tuple[int, Optional[Path]]]:
    """Ищет активный процесс GoWR.exe."""
    if os.name != 'nt':
        return None
    _configure_winapi()
    # Быстрый поиск через ctypes CreateToolhelp32Snapshot
    TH32CS_SNAPPROCESS = 0x00000002

    class PROCESSENTRY32W(ctypes.Structure):
        _fields_ = [
            ("dwSize", ctypes.wintypes.DWORD),
            ("cntUsage", ctypes.wintypes.DWORD),
            ("th32ProcessID", ctypes.wintypes.DWORD),
            ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
            ("th32ModuleID", ctypes.wintypes.DWORD),
            ("cntThreads", ctypes.wintypes.DWORD),
            ("th32ParentProcessID", ctypes.wintypes.DWORD),
            ("pcPriClassBase", ctypes.c_long),
            ("dwFlags", ctypes.wintypes.DWORD),
            ("szExeFile", ctypes.c_wchar * 260),
        ]

    k32 = ctypes.windll.kernel32
    h_snap = k32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if h_snap == ctypes.c_void_p(-1).value:
        return None

    try:
        pe = PROCESSENTRY32W()
        pe.dwSize = ctypes.sizeof(PROCESSENTRY32W)
        if k32.Process32FirstW(h_snap, ctypes.byref(pe)):
            while True:
                if pe.szExeFile.lower() == "gowr.exe":
                    pid = pe.th32ProcessID
                    # Попытка узнать полный путь к exe
                    exe_path: Optional[Path] = None
                    h_proc = k32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
                    if h_proc:
                        try:
                            buf = ctypes.create_unicode_buffer(1024)
                            size = ctypes.wintypes.DWORD(1024)
                            if k32.QueryFullProcessImageNameW(h_proc, 0, buf, ctypes.byref(size)):
                                exe_path = Path(buf.value)
                        finally:
                            k32.CloseHandle(h_proc)
                    return pid, exe_path
                if not k32.Process32NextW(h_snap, ctypes.byref(pe)):
                    break
    finally:
        k32.CloseHandle(h_snap)

    return None


def read_live_telemetry(custom_reader: Any = None, active_realm: str = "midgard") -> Dict[str, Any]:
    """Главная точка входа живой телеметрии Кратоса из памяти игры.

    Возвращает актуальные координаты (X, Y, Z), здоровье, ярость и нормализованный радар,
    если игра запущена и отпечаток сборки подтверждён.
    При любом сбое честно возвращает available: False с описанием причины.
    """
    if isinstance(custom_reader, str):
        active_realm = custom_reader
        custom_reader = None

    res: Dict[str, Any] = {
        "available": False,
        "process_running": False,
        "pid": None,
        "source": "memory_live",
        "reason": "игра не запущена",
        "timestamp": time.time(),
        "build_fingerprint": None,
        "kratos": None,
        "position": None,
        "combat": None,
        "radar": None,
        "boss": None,
        "cooldowns": {},
    }

    refresh_live_realm_transforms()
    reader = custom_reader
    managed_reader = False
    exe_path = None

    if reader is not None:
        res["process_running"] = True
        res["pid"] = getattr(reader, "pid", None)
    else:
        proc_info = find_gowr_process()
        if not proc_info:
            return res

        pid, exe_path = proc_info
        res["process_running"] = True
        res["pid"] = pid
        reader = SafeProcessMemory.open(pid)
        if not reader:
            res["reason"] = f"процесс GoWR.exe обнаружен (PID {pid}), но не удалось открыть память (ограничение прав)"
            return res
        managed_reader = True

    try:
        # Проверка отпечатка исполняемого файла игры
        fingerprint: Optional[BuildFingerprint] = None
        if exe_path and exe_path.is_file():
            fingerprint = get_exe_fingerprint(exe_path)

        build_cfg = None
        if fingerprint:
            key = (fingerprint.file_size, fingerprint.pe_timestamp)
            build_cfg = KNOWN_BUILDS.get(key)
            res["build_fingerprint"] = {
                "file_size": fingerprint.file_size,
                "pe_timestamp": fingerprint.pe_timestamp,
                "version": build_cfg.get("version") if build_cfg else "неизвестная сборка",
                "matched": build_cfg is not None,
            }

        # Если файл не нашли через процесс, ищем первый известный конфиг по умолчанию
        if not build_cfg:
            if fingerprint:
                res["reason"] = "unsupported_build"
                return res
            if custom_reader is None:
                res["reason"] = "build_unverified"
                return res
            build_cfg = next(iter(KNOWN_BUILDS.values()))

        # Чтение структуры Кратоса по цепочке указателей
        if build_cfg.get("probe_sources"):
            from tools.gow_live_pointer_probe import read_configured_sample
            sample = read_configured_sample(reader, reader.base_address, build_cfg)
            if not sample["available"]:
                res["reason"] = ('unsupported_build' if 'fingerprint differs' in sample['reason']
                                 else sample["reason"])
                return res
            x, y, z = sample["xyz"]
            radar = normalize_coordinates(active_realm, x, y, z)
            # Угол камеры в мире (+Z=0, +X=90) → направление на карте мира:
            # у каждой карты свой поворот (Муспельхейм ~161°, Нифльхейм ~180°).
            heading = map_heading_deg(active_realm, x, y, z, sample["yaw_deg"])
            radar["world_yaw_deg"] = round(sample["yaw_deg"], 1)
            radar["yaw_deg"] = heading
            point = {"x": x, "y": y, "z": z, "yaw_deg": heading,
                     "world_yaw_deg": round(sample["yaw_deg"], 1),
                     "pct_x": radar.get("pct_x"), "pct_y": radar.get("pct_y")}
            res.update(available=True, reason="ok", radar=radar,
                       position=dict(point), kratos=dict(point), combat=None,
                       boss=None, cooldowns={}, source_guards=sample["guards"])
            return res

        anchor = reader.base_address + build_cfg["kratos_anchor_offset"]
        actor_addr = reader.resolve_chain(anchor, build_cfg["kratos_chain"])

        if not actor_addr:
            pid_label = f" (PID {res['pid']})" if res.get("pid") else ""
            res["reason"] = f"процесс GoWR.exe активен{pid_label}, но цепочка указателей Кратоса не активна (меню, пауза или загрузка мира)"
            return res

        offs = build_cfg["offsets"]
        x = reader.read_float(actor_addr + offs["pos_x"])
        y = reader.read_float(actor_addr + offs["pos_y"])
        z = reader.read_float(actor_addr + offs["pos_z"])
        hp = reader.read_float(actor_addr + offs["hp"])
        max_hp = reader.read_float(actor_addr + offs["max_hp"])
        rage = reader.read_float(actor_addr + offs["rage"])
        max_rage = reader.read_float(actor_addr + offs["max_rage"])

        if None in (x, y, z, hp, max_hp, rage, max_rage):
            res["reason"] = "ошибка чтения полей актора"
            return res

        # Строгая проверка поведением
        if not validate_behavior(x, y, z, hp, max_hp, rage, max_rage):
            res["reason"] = "значения памяти не прошли проверку поведением"
            return res

        radar = normalize_coordinates(active_realm, x, y, z)

        res["available"] = True
        res["reason"] = "ok"
        res["radar"] = radar
        res["kratos"] = {
            "x": round(x, 2),
            "y": round(y, 2),
            "z": round(z, 2),
            "pct_x": radar["pct_x"],
            "pct_y": radar["pct_y"],
            "hp": round(hp, 1),
            "max_hp": round(max_hp, 1),
            "hp_percent": round((hp / max_hp) * 100, 1) if max_hp > 0 else 0.0,
            "rage": round(rage, 1),
            "max_rage": round(max_rage, 1),
            "rage_percent": round((rage / max_rage) * 100, 1) if max_rage > 0 else 0.0,
        }
        res["position"] = {
            "x": round(x, 2),
            "y": round(y, 2),
            "z": round(z, 2),
            "pct_x": radar["pct_x"],
            "pct_y": radar["pct_y"],
            "closest_poi": radar["closest_poi"]["name"] if radar.get("closest_poi") else None,
            "closest_poi_dist_m": radar["closest_poi"]["distance_meters"] if radar.get("closest_poi") else None,
        }
        res["combat"] = {
            "health": round(hp, 1),
            "max_health": round(max_hp, 1),
            "health_pct": round((hp / max_hp) * 100, 1) if max_hp > 0 else 0.0,
            "rage": round(rage, 1),
            "max_rage": round(max_rage, 1),
            "rage_pct": round((rage / max_rage) * 100, 1) if max_rage > 0 else 0.0,
        }

        # Чтение босса (если есть) — Задача 183
        boss_anchor = reader.base_address + build_cfg["boss_anchor_offset"]
        boss_addr = reader.resolve_chain(boss_anchor, build_cfg["boss_chain"])
        if boss_addr:
            b_offs = build_cfg["boss_offsets"]
            b_hp = reader.read_float(boss_addr + b_offs["hp"])
            b_max = reader.read_float(boss_addr + b_offs["max_hp"])
            b_shield = reader.read_float(boss_addr + b_offs["shield_hp"])
            b_shield_max = reader.read_float(boss_addr + b_offs["shield_max_hp"])
            b_phase = reader.read_int32(boss_addr + b_offs["phase_index"])
            b_element_raw = reader.read_int32(boss_addr + b_offs["element"])

            if validate_boss_behavior(b_hp, b_max, b_shield, b_shield_max, b_phase):
                element_name = BOSS_ELEMENT_MAP.get(b_element_raw, "unknown") if b_element_raw is not None else "none"
                boss_data: Dict[str, Any] = {
                    "active": True,
                    "hp": round(b_hp, 1),
                    "max_hp": round(b_max, 1),
                    "hp_percent": round((b_hp / b_max) * 100, 1) if b_max > 0 else 0.0,
                    "phase": b_phase if b_phase is not None else 0,
                    "element": element_name,
                }
                # Щит (может быть 0 или не существовать)
                if b_shield is not None and b_shield_max is not None and b_shield_max > 0:
                    boss_data["shield_hp"] = round(b_shield, 1)
                    boss_data["shield_max_hp"] = round(b_shield_max, 1)
                    boss_data["shield_percent"] = round((b_shield / b_shield_max) * 100, 1)
                    boss_data["has_shield"] = b_shield > 0
                else:
                    boss_data["has_shield"] = False

                res["boss"] = boss_data

        if res["boss"] is None:
            res["boss"] = {"active": False}

        # Чтение кулдаунов рунических атак Кратоса — Задача 183
        if "cooldown_offsets" in build_cfg:
            cd_anchor = reader.base_address + build_cfg["cooldown_anchor_offset"]
            cd_addr = reader.resolve_chain(cd_anchor, build_cfg["cooldown_chain"])
            if cd_addr:
                cd_offs = build_cfg["cooldown_offsets"]
                raw_cds: Dict[str, Optional[float]] = {}
                for cd_name, cd_off in cd_offs.items():
                    raw_cds[cd_name] = reader.read_float(cd_addr + cd_off)
                valid_cds = validate_cooldowns(raw_cds)
                res["cooldowns"] = valid_cds
            else:
                res["cooldowns"] = {}
        else:
            res["cooldowns"] = {}

        return res
    finally:
        if managed_reader and reader:
            reader.close()
