"""Read-only GoWR map calibration. Vision/capture dependencies load only in a game.

Run via hub.py serve, or: python tools/gow_auto_calibrate.py [--debug].
No input injection, process writes, screenshots on disk (unless --debug), or AI APIs.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import io
import json
import logging
import math
import os
from pathlib import Path
import sys
import tempfile
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from paths import CACHE as USER_CACHE, LIVE_REFS, DATA
FIX = USER_CACHE / 'calibration-fixtures'
CACHE = USER_CACHE / 'gow_calib'
REFS = LIVE_REFS
LOG = logging.getLogger('gow_auto_calibrate')
_write_lock = threading.Lock()
_start_lock = threading.Lock()
_thread = None
_stop = threading.Event()


def _vision():
    import cv2
    import numpy as np
    return cv2, np


def _gray(rgb):
    cv, _ = _vision()
    return cv.cvtColor(rgb, cv.COLOR_RGB2GRAY)


def map_mask(frame):
    """Exclude realm panel, legend and bottom controls; dimensions in UI height."""
    _, np = _vision()
    h, w = frame.shape[:2]
    mask = np.zeros((h, w), 'uint8')
    mask[int(.04*h):int(.79*h), int(.81*h):w-int(.24*h)] = 255
    return mask


def is_map_screen(frame):
    """Cheap highlighted Russian КАРТА tab check, on a 480 px tall frame.

    Uses the text AND its selected light background, not generic dark menu edges.
    Fails closed if the tab is hidden, locale/UI scale is unsupported, or crop is bad.
    """
    cv, np = _vision()
    if frame is None or frame.ndim != 3 or min(frame.shape[:2]) < 200:
        return False
    h, w = frame.shape[:2]
    small = cv.resize(_gray(frame), (round(w*480/h), 480), interpolation=cv.INTER_AREA)
    tab = cv.imread(str(FIX / 'map_tab_template.png'), cv.IMREAD_GRAYSCALE)
    if tab is None:
        return False
    strip = small[round(.925*480):]
    for scale in (.9, 1., 1.1):
        t = cv.resize(tab, (round(tab.shape[1]*480/837*scale), round(tab.shape[0]*480/837*scale)),
                      interpolation=cv.INTER_AREA)
        if t.shape[0] > strip.shape[0] or t.shape[1] > strip.shape[1]:
            continue
        scores = cv.matchTemplate(strip, t, cv.TM_CCOEFF_NORMED)
        _, score, _, loc = cv.minMaxLoc(scores)
        crop = strip[loc[1]:loc[1]+t.shape[0], loc[0]:loc[0]+t.shape[1]]
        if score >= .84 and float(np.mean(crop)) >= 130:
            return True
    return False


def find_kratos(frame):
    """Circular Omega template, multiscale, spatial NMS; legend is masked out."""
    cv, np = _vision()
    template = cv.imread(str(FIX / 'kratos_template.png'))
    if template is None:
        return dict(accepted=False, reason='icon_template_missing')
    template = cv.cvtColor(template, cv.COLOR_BGR2RGB)
    h, w = frame.shape[:2]
    # Normalize UI size independently of the map zoom.
    factor = 837/h
    image = cv.resize(frame, (round(w*factor), 837), interpolation=cv.INTER_AREA)
    mask = map_mask(image)
    hits = []
    for scale in (.85, .925, 1., 1.075, 1.15):
        n = round(29*scale)
        t = cv.resize(template, (n, n))
        circle = np.zeros((n, n), 'uint8')
        cv.circle(circle, (n//2, n//2), round(n*.44), 255, -1)
        score = cv.matchTemplate(image, t, cv.TM_CCOEFF_NORMED, mask=circle)
        score[~np.isfinite(score)] = -1
        score[mask[:score.shape[0], :score.shape[1]] == 0] = -1
        # Bounded peaks per scale. Reject multiple distinct candidates.
        for _ in range(5):
            _, confidence, _, (x, y) = cv.minMaxLoc(score)
            if confidence < .8:
                break
            cx, cy = x+(n-1)/2, y+(n-1)/2
            # Colour check rejects grey/gold circular POIs with similar shapes.
            patch = image[y:y+n, x:x+n].astype(float)
            red = (patch[:,:,0] > patch[:,:,1]*1.4) & (patch[:,:,0] > patch[:,:,2]*1.4)
            if red.mean() >= .08:
                hits.append((confidence, cx, cy, n))
            cv.rectangle(score, (max(0, x-n), max(0, y-n)), (x+n, y+n), -1, -1)
    unique = []
    for hit in sorted(hits, reverse=True):
        if all(math.hypot(hit[1]-a[1], hit[2]-a[2]) > max(hit[3], a[3])*.75 for a in unique):
            unique.append(hit)
    if len(unique) != 1:
        return dict(accepted=False, reason='icon_missing' if not unique else 'icon_ambiguous', count=len(unique))
    confidence, x, y, n = unique[0]
    # Direction wedge is optional: no angle is invented when insufficient pixels.
    angle = _wedge_angle(image, x, y, n)
    return dict(accepted=True, center=(x/factor, y/factor), confidence=confidence,
                wedge_deg=angle, wedge_reason='measured' if angle is not None else 'wedge_unresolved')


def _wedge_angle(image, x, y, diameter):
    cv, np = _vision()
    r = round(diameter*1.1)
    cx, cy = round(x), round(y)
    if min(cx-r, cy-r) < 0 or cx+r >= image.shape[1] or cy+r >= image.shape[0]:
        return None
    patch = image[cy-r:cy+r+1, cx-r:cx+r+1]
    hsv = cv.cvtColor(patch, cv.COLOR_RGB2HSV)
    yy, xx = np.indices(hsv.shape[:2]); dx, dy = xx-r, yy-r
    radius = np.hypot(dx, dy)
    # Pale gold triangle outside the circular rim. Saturated orange quest
    # diamonds/lava and the desaturated ground-position circle are excluded.
    gold = ((hsv[:,:,0] >= 18) & (hsv[:,:,0] <= 35)
            & (hsv[:,:,1] >= 110) & (hsv[:,:,1] <= 175) & (hsv[:,:,2] > 160)
            & (radius > diameter*.46) & (radius < diameter*.75))
    count, labels = cv.connectedComponents(gold.astype('uint8'))
    candidates = []
    for label in range(1,count):
        pixels = labels == label
        if pixels.sum() < 6:
            continue
        unit_x, unit_y = dx[pixels]/radius[pixels], dy[pixels]/radius[pixels]
        vx,vy = float(unit_x.mean()),float(unit_y.mean())
        if math.hypot(vx,vy) >= .985:
            candidates.append(math.degrees(math.atan2(vx,-vy)) % 360)
    return candidates[0] if len(candidates) == 1 else None


def image_features(rgb, mask=None):
    cv, _ = _vision()
    return cv.SIFT_create(nfeatures=8000).detectAndCompute(_gray(rgb), mask)


def register_map(frame, mosaic, meta, mosaic_features=None):
    """Screen -> mosaic partial affine. Residuals are in original screen pixels."""
    cv, np = _vision()
    h, w = frame.shape[:2]
    factor = min(1., 2000/w, 1080/h)
    small = cv.resize(frame, (round(w*factor), round(h*factor)), interpolation=cv.INTER_AREA) if factor < 1 else frame
    ka, da = image_features(small, map_mask(small))
    kb, db = mosaic_features if mosaic_features is not None else image_features(mosaic)
    reject = dict(accepted=False, reason='registration_insufficient', inliers=0, meta=dict(meta))
    if da is None or db is None or len(da) < 60 or len(db) < 60:
        return reject
    pairs = cv.BFMatcher().knnMatch(da, db, k=2)
    matches = [p[0] for p in pairs if len(p)==2 and p[0].distance < .75*p[1].distance]
    if len(matches) < 60:
        return dict(reject, matches=len(matches))
    src = np.float32([ka[m.queryIdx].pt for m in matches])
    dst = np.float32([kb[m.trainIdx].pt for m in matches])
    A, inliers = cv.estimateAffinePartial2D(src, dst, method=cv.RANSAC,
                                            ransacReprojThreshold=4., maxIters=3000, confidence=.999)
    if A is None or inliers is None:
        return reject
    good = inliers.ravel().astype(bool)
    scale = math.hypot(A[0,0], A[1,0])
    if not math.isfinite(scale) or scale < .15 or scale > 8:
        return dict(reject, reason='registration_scale')
    rotation = math.degrees(math.atan2(A[1,0], A[0,0]))
    residual = np.linalg.norm(src[good] @ A[:,:2].T + A[:,2] - dst[good], axis=1) / scale / factor
    median = float(np.median(residual))
    count = int(good.sum())
    # Require spatial support: many copies of one POI cannot calibrate a frame.
    support = cv.convexHull(src[good]) if count >= 3 else None
    area = cv.contourArea(support) if support is not None else 0
    accepted = count >= 60 and median <= 2.5 and abs(rotation) <= 2 and area >= 2500*factor*factor
    # Convert back to original screenshot coordinates.
    A[:,:2] *= factor
    return dict(accepted=accepted, reason='registered' if accepted else 'registration_quality',
                matrix=A.tolist(), meta=dict(meta), inliers=count, median_px=median,
                rotation_deg=rotation, scale=scale*factor, matches=len(matches), support_px=area/(factor*factor))


def map_point(registration, point):
    A, meta = registration['matrix'], registration['meta']
    x = A[0][0]*point[0] + A[0][1]*point[1] + A[0][2] + meta['x0']*256
    y = A[1][0]*point[0] + A[1][1]*point[1] + A[1][2] + meta['y0']*256
    n = 256 * 2**meta['z']
    return math.degrees(math.atan(math.sinh(math.pi*(1-2*y/n)))), x/n*360-180


def stable_samples(before, after):
    try:
        if not before['available'] or not after['available'] or before['pid'] != after['pid']:
            return False
        if before['radar']['realm_key'] != after['radar']['realm_key']:
            return False
        a, b = before['position'], after['position']
        values = [a[k] for k in 'xyz'] + [b[k] for k in 'xyz']
        return all(math.isfinite(v) for v in values) and math.dist(values[:3], values[3:]) <= .5
    except (KeyError, TypeError, ValueError):
        return False


def _atomic_json(path, document):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    name = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf8', dir=path.parent,
                                         suffix='.tmp', delete=False) as f:
            name = f.name
            json.dump(document, f, ensure_ascii=False, indent=2, allow_nan=False)
            f.write('\n'); f.flush(); os.fsync(f.fileno())
        os.replace(name, path)
    finally:
        if name and os.path.exists(name):
            os.unlink(name)


def append_reference(path, realm, ref):
    """Append only; preserve all unknown fields/manual refs/zones. Fail on corrupt input.

    In-process lock plus OS advisory lock serializes hub/standalone collectors.
    Lock file remains intentionally; it never contains a screenshot or game data.
    """
    import gow_memory as gm
    if realm not in gm.REALM_BOUNDING_BOXES or len(ref['world']) != 3:
        raise ValueError('unknown realm or invalid world')
    if not all(math.isfinite(v) for v in (*ref['world'], ref['lat'], ref['lng'])):
        raise ValueError('nonfinite reference')
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    with _write_lock, open(str(path)+'.lock', 'a+b') as lock:
        if lock.seek(0,2) == 0:
            lock.write(b'0'); lock.flush()
        lock.seek(0)
        if sys.platform == 'win32':
            import msvcrt
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            source = path if path.exists() else DATA / 'live_realm_refs.json'
            doc = json.loads(source.read_text(encoding='utf8'))
            if doc.get('schema_version') != 1 or not isinstance(doc.get('realms'), dict):
                raise ValueError('invalid reference schema; file preserved')
            record = doc['realms'].setdefault(realm, {})
            refs = record.setdefault('refs', [])
            if any(math.dist(r['world'], ref['world']) <= 15 for r in refs):
                return False
            refs.append(ref)
            _atomic_json(path, doc)
            return True
        finally:
            lock.seek(0)
            if sys.platform == 'win32':
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(lock, fcntl.LOCK_UN)


class MosaicCache:
    """Realm bounded mosaics: transparent gow_tiles composited onto black."""
    def __init__(self, cache_dir=CACHE):
        self.root = Path(cache_dir)
        self.features = {}

    def __call__(self, realm):
        import gow_memory as gm
        b = gm.REALM_AFFINE_TRANSFORMS.get(realm, {}).get('map_bounds')
        if not b:
            r = gm.REALM_BOUNDING_BOXES[realm]
            b = {k:r['map_'+k] for k in ('lat_min','lat_max','lng_min','lng_max')}
        span = max(b['lat_max']-b['lat_min'], b['lng_max']-b['lng_min'])
        r = gm.REALM_BOUNDING_BOXES[realm]
        base = max(r['min_zoom'], min(r['max_zoom'], math.floor(math.log2(1400*360/(256*span)))))
        for z in (base, base+1, base-1):
            if r['min_zoom'] <= z <= r['max_zoom']:
                yield self.build(realm, b, z)

    def build(self, realm, bounds, z):
        _, np = _vision()
        from PIL import Image
        import gow_tiles
        def merc(lat, lng):
            n = 256*2**z
            return (lng+180)/360*n, (1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*n
        # Include border art outside the pin extrema.
        pad = .03
        a = merc(bounds['lat_max']+pad, bounds['lng_min']-pad)
        b = merc(bounds['lat_min']-pad, bounds['lng_max']+pad)
        x0, y0 = int(a[0]//256), int(a[1]//256)
        x1, y1 = int(b[0]//256), int(b[1]//256)
        if (x1-x0+1)*(y1-y0+1) > 400:
            raise ValueError('mosaic tile budget exceeded')
        meta = dict(z=z, x0=x0, y0=y0)
        target = self.root / f'{realm}_z{z}_{x0}_{y0}_{x1}_{y1}.png'
        if target.exists():
            with Image.open(target) as im:
                return np.asarray(im.convert('RGB')), meta
        out = Image.new('RGB', ((x1-x0+1)*256, (y1-y0+1)*256))
        for y in range(y0, y1+1):
            for x in range(x0, x1+1):
                if _stop.is_set():
                    raise RuntimeError('collector_stopping')
                raw = gow_tiles.get_tile(realm, z, x, y)
                if raw:
                    with Image.open(io.BytesIO(raw)) as tile:
                        tile = tile.convert('RGBA')
                        out.paste(tile, ((x-x0)*256, (y-y0)*256), tile)
        self.root.mkdir(parents=True, exist_ok=True)
        name = None
        try:
            with tempfile.NamedTemporaryFile(dir=self.root, suffix='.tmp', delete=False) as f:
                name = f.name
                out.save(f, format='PNG')
            os.replace(name, target)
        finally:
            if name and os.path.exists(name):
                os.unlink(name)
        return np.asarray(out), meta

    def describe(self, realm, mosaic, meta):
        key = (realm, meta['z'], meta['x0'], meta['y0'])
        if key not in self.features:
            if len(self.features) >= 3:
                self.features.pop(next(iter(self.features)))
            self.features[key] = image_features(mosaic)
        return self.features[key]


class WindowCapture:
    """Read the foreground GoWR client, using DXGI on its exact monitor.

    Does not activate, resize, move or send input to windows. No recorder thread.
    mss is a fallback for unavailable DXGI; never reuse a cached frame.
    """
    def __init__(self):
        self.camera = None
        self.device_key = None

    def close(self):
        if self.camera is not None:
            self.camera.release()
            self.camera = None
            self.device_key = None

    def __call__(self, pid):
        import ctypes as c
        from ctypes import wintypes as w
        if sys.platform != 'win32':
            return None
        u = c.WinDLL('user32', use_last_error=True)
        u.GetForegroundWindow.restype = w.HWND
        u.GetWindowThreadProcessId.argtypes = [w.HWND, c.POINTER(w.DWORD)]
        u.GetClientRect.argtypes = [w.HWND, c.POINTER(w.RECT)]
        u.ClientToScreen.argtypes = [w.HWND, c.POINTER(w.POINT)]
        u.IsIconic.argtypes = [w.HWND]
        u.MonitorFromWindow.argtypes = [w.HWND, w.DWORD]; u.MonitorFromWindow.restype = w.HMONITOR
        u.SetThreadDpiAwarenessContext.argtypes = [c.c_void_p]
        u.SetThreadDpiAwarenessContext.restype = c.c_void_p
        previous = u.SetThreadDpiAwarenessContext(c.c_void_p(-4))
        try:
            hwnd = u.GetForegroundWindow(); owner = w.DWORD()
            u.GetWindowThreadProcessId(hwnd, c.byref(owner))
            if owner.value != pid or u.IsIconic(hwnd):
                return None
            rect, origin = w.RECT(), w.POINT()
            if not u.GetClientRect(hwnd, c.byref(rect)) or not u.ClientToScreen(hwnd, c.byref(origin)):
                return None
            width, height = rect.right, rect.bottom
            if min(width, height) < 200:
                return None
            class MI(c.Structure):
                _fields_ = [('cbSize',w.DWORD), ('rcMonitor',w.RECT), ('rcWork',w.RECT),
                            ('dwFlags',w.DWORD), ('szDevice',w.WCHAR*32)]
            mi = MI(); mi.cbSize = c.sizeof(mi)
            u.GetMonitorInfoW.argtypes = [w.HMONITOR,c.POINTER(MI)]
            if not u.GetMonitorInfoW(u.MonitorFromWindow(hwnd, 2), c.byref(mi)):
                return None
            bounds = mi.rcMonitor
            region = (origin.x-bounds.left, origin.y-bounds.top,
                      origin.x-bounds.left+width, origin.y-bounds.top+height)
            if region[0] < 0 or region[1] < 0 or region[2] > bounds.right-bounds.left or region[3] > bounds.bottom-bounds.top:
                return None
            frame = None
            try:
                import dxcam
                # Installed DXcam exposes monitor names only in its factory inventory.
                # Verify the exact device name; never guess by output index/resolution.
                factory = getattr(dxcam, '__factory', None)
                key = next(((di,oi) for di,outputs in enumerate(factory.outputs)
                            for oi,o in enumerate(outputs) if o.devicename == mi.szDevice), None) if factory else None
                if key is not None:
                    if key != self.device_key:
                        self.close()
                        self.camera = dxcam.create(device_idx=key[0], output_idx=key[1], output_color='RGB')
                        self.device_key = key
                    frame = self.camera.grab(region=region, new_frame_only=True)
                    if frame is None:
                        return None  # no new DXGI frame; no last-good fallback
            except Exception:
                self.close()
            if frame is None:
                import mss
                _, np = _vision()
                with mss.mss() as screen:
                    shot = screen.grab(dict(left=origin.x, top=origin.y, width=width, height=height))
                    frame = np.asarray(shot)[:,:,:3][:,:,::-1].copy()
            # Foreground/geometry must still match after the capture.
            check, offset = w.RECT(), w.POINT()
            if (u.GetForegroundWindow() != hwnd or not u.GetClientRect(hwnd,c.byref(check))
                    or not u.ClientToScreen(hwnd,c.byref(offset))
                    or (check.right,check.bottom,offset.x,offset.y) != (width,height,origin.x,origin.y)):
                return None
            return frame
        finally:
            if previous:
                u.SetThreadDpiAwarenessContext(previous)


def current_telemetry():
    """Same save realm source as companion; unknown realm fails closed, no Midgard default."""
    import gow_memory as gm
    import gowsave
    save = gowsave.read()
    realm = save.get('realm') or (save.get('progress') or {}).get('realm')
    if not save.get('ok') or not realm:
        return dict(available=False, reason='save_realm_unavailable')
    from gow_pins import normalize_realm_key
    key = normalize_realm_key(realm)
    if key not in gm.REALM_BOUNDING_BOXES:
        return dict(available=False, reason='save_realm_unknown')
    return gm.read_live_telemetry(active_realm=key)


def foreground_gowr_process():
    """Cheap idle gate: exact executable of foreground window, no process scan.

    Background/minimized games cannot supply an unobscured desktop-duplication
    frame anyway. Full memory checks remain in read_live_telemetry after this gate.
    """
    if sys.platform != 'win32':
        return None
    import ctypes as c
    from ctypes import wintypes as w
    u = c.WinDLL('user32', use_last_error=True)
    k = c.WinDLL('kernel32', use_last_error=True)
    u.GetForegroundWindow.restype = w.HWND
    u.GetWindowThreadProcessId.argtypes = [w.HWND,c.POINTER(w.DWORD)]
    k.OpenProcess.argtypes = [w.DWORD,w.BOOL,w.DWORD]; k.OpenProcess.restype = w.HANDLE
    k.QueryFullProcessImageNameW.argtypes = [w.HANDLE,w.DWORD,w.LPWSTR,c.POINTER(w.DWORD)]
    k.CloseHandle.argtypes = [w.HANDLE]
    pid = w.DWORD()
    u.GetWindowThreadProcessId(u.GetForegroundWindow(), c.byref(pid))
    handle = k.OpenProcess(0x1000, False, pid.value)  # query limited information only
    if not handle:
        return None
    try:
        name = c.create_unicode_buffer(32768); size = w.DWORD(len(name))
        if k.QueryFullProcessImageNameW(handle,0,name,c.byref(size)) and Path(name.value).name.lower() == 'gowr.exe':
            return pid.value,Path(name.value)
    finally:
        k.CloseHandle(handle)
    return None


class Collector:
    def __init__(self, process_finder=None, capture=None, telemetry=None, refs_path=REFS,
                 mosaics=None, debug=False):
        self.process_finder = process_finder
        self.capture = capture
        self.telemetry = telemetry or current_telemetry
        self.refs_path = Path(refs_path)
        self.mosaics = mosaics
        self.debug = debug
        self.counts = Counter()
        self.last_result = {}

    def poll(self):
        result = self._poll()
        self.counts[result['reason']] += 1
        if result['reason'] != self.last_result.get('reason'):
            LOG.info('GoW calibration: %s', result)
        self.last_result = result
        return result

    def _poll(self):
        proc = (self.process_finder or foreground_gowr_process)()
        if not proc:
            if isinstance(self.capture, WindowCapture):
                self.capture.close()
            return dict(reason='game_absent')
        import gow_memory as gm
        before = self.telemetry()
        if not before.get('available') or before.get('pid') != proc[0]:
            return dict(reason='memory_unavailable', detail=before.get('reason'))
        if self.capture is None:
            self.capture = WindowCapture()
        frame = self.capture(proc[0])
        captured = datetime.now(timezone.utc).isoformat()
        after = self.telemetry()
        if not stable_samples(before, after):
            return dict(reason='memory_unstable')
        if frame is None:
            return dict(reason='capture_unavailable')
        if self.debug:
            self._debug_frame(frame)
        if not is_map_screen(frame):
            return dict(reason='not_map')
        icon = find_kratos(frame)
        if not icon['accepted']:
            return dict(reason=icon['reason'])
        realm = before['radar']['realm_key']
        if realm not in gm.REALM_BOUNDING_BOXES:
            return dict(reason='realm_unknown')
        if self.mosaics is None:
            self.mosaics = MosaicCache()
        accepted = None
        for mosaic, meta in self.mosaics(realm):
            features = self.mosaics.describe(realm, mosaic, meta) if isinstance(self.mosaics, MosaicCache) else None
            registration = register_map(frame, mosaic, meta, features)
            if registration['accepted']:
                accepted = registration
                break
        if accepted is None:
            return dict(reason='registration_rejected', realm=realm)
        lat, lng = map_point(accepted, icon['center'])
        bounds = gm.REALM_AFFINE_TRANSFORMS.get(realm, {}).get('map_bounds')
        if bounds and not (bounds['lat_min']-.03 <= lat <= bounds['lat_max']+.03
                           and bounds['lng_min']-.03 <= lng <= bounds['lng_max']+.03):
            return dict(reason='icon_outside_realm_bounds', realm=realm)
        p = before['position']
        ref = dict(world=[p[k] for k in 'xyz'], lat=lat, lng=lng, source='auto_map_sift',
                   captured=captured, inliers=accepted['inliers'],
                   median_px=accepted['median_px'], icon_confidence=icon['confidence'],
                   wedge_deg=icon['wedge_deg'], wedge_reason=icon['wedge_reason'],
                   world_yaw_deg=p.get('world_yaw_deg'), map_yaw_deg=p.get('yaw_deg'),
                   registration=dict(z=accepted['meta']['z'], rotation_deg=accepted['rotation_deg'],
                                     scale=accepted['scale']))
        added = append_reference(self.refs_path, realm, ref)
        if added:
            models = gm.refresh_live_realm_transforms(self.refs_path)
            if self.refs_path == REFS:
                reports = {k:[dict(id=m['id'], **m['fit_report']) for m in v] for k,v in models.items()}
                _atomic_json(CACHE / 'fit_report.json', reports)
                for report in reports.get(realm, []):
                    if report['wad_conflicts']:
                        LOG.warning('Live/WAD calibration conflicts: %s', report['wad_conflicts'])
        return dict(reason='reference_added' if added else 'duplicate', realm=realm,
                    lat=lat, lng=lng, inliers=accepted['inliers'], median_px=accepted['median_px'])

    def _debug_frame(self, frame):
        from PIL import Image
        folder = CACHE / 'frames'; folder.mkdir(parents=True, exist_ok=True)
        # Ring overwrites only collector-owned debug slots; at most 20 frames.
        slot = sum(self.counts.values()) % 20
        Image.fromarray(frame).save(folder / f'frame_{slot:02}.webp')

    def run(self, stop):
        try:
            while not stop.is_set():
                try:
                    self.poll()
                except Exception:
                    LOG.exception('GoW calibration poll failed; retry in 2 s')
                stop.wait(2.)
        finally:
            if isinstance(self.capture, WindowCapture):
                self.capture.close()


def templates_ready():
    return all((FIX / name).is_file() for name in ('map_tab_template.png', 'kratos_template.png'))


def learn_templates(capture=None, process_finder=None, selector=None, wait=None):
    """User-invoked local setup; no reference images are distributed with the app.

    Capture one user game window, let the user select the highlighted MAP tab and
    the circular Kratos icon, and retain only those two crops in the user cache.
    The template dimensions are normalized to the collector's 837px UI model.
    """
    cv, np = _vision()
    import gow_memory as gm
    proc = (process_finder or gm.find_gowr_process)()
    if not proc:
        raise RuntimeError('Open the game and its map before learning templates')
    print('Switch to the game map now. Capturing the game window in 5 seconds.')
    (wait or time.sleep)(5)
    source = capture or WindowCapture()
    try:
        frame = source(proc[0])
    finally:
        if capture is None:
            source.close()
    if frame is None:
        raise RuntimeError('Game-window capture failed; no templates were saved')
    h, w = frame.shape[:2]
    image = cv.resize(frame, (round(w * 837 / h), 837), interpolation=cv.INTER_AREA)
    bgr = cv.cvtColor(image, cv.COLOR_RGB2BGR)
    choose = selector or (lambda title, pixels: cv.selectROI(title, pixels, showCrosshair=True, fromCenter=False))
    crops = []
    try:
        for title in ('Select only the highlighted MAP tab; Enter confirms',
                      'Select a square around the circular Kratos icon; Enter confirms'):
            x, y, cw, ch = map(int, choose(title, bgr))
            if cw < 8 or ch < 8 or x < 0 or y < 0 or x+cw > image.shape[1] or y+ch > image.shape[0]:
                raise RuntimeError('Selection cancelled or invalid; no templates were saved')
            crops.append(bgr[y:y+ch, x:x+cw].copy())
    finally:
        if selector is None:
            cv.destroyAllWindows()
    FIX.mkdir(parents=True, exist_ok=True)
    for name, crop in zip(('map_tab_template.png', 'kratos_template.png'), crops):
        if not cv.imwrite(str(FIX / name), crop):
            raise OSError('Could not save a user template')
    print('Saved two user-local templates. Start the companion with --autocalib.')
    return FIX


def start_background():
    global _thread
    if os.environ.get('GOWR_AUTOCALIB', '0').strip() == '0':
        return None
    if not templates_ready():
        raise RuntimeError('Run tools/gow_auto_calibrate.py --learn-templates first')
    with _start_lock:
        if _thread is None or not _thread.is_alive():
            _stop.clear()
            _thread = threading.Thread(target=Collector().run, args=(_stop,), daemon=True, name='gow-auto-calibration')
            _thread.start()
        return _thread


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--debug', action='store_true', help='keep a ring of at most 20 frames in cache/gow_calib/frames')
    parser.add_argument('--learn-templates', action='store_true', help='Capture your game map once and select two private templates')
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    if args.learn_templates:
        learn_templates()
        raise SystemExit(0)
    if os.environ.get('GOWR_AUTOCALIB', '0').strip() != '0':
        try:
            Collector(debug=args.debug).run(_stop)
        except KeyboardInterrupt:
            _stop.set()
