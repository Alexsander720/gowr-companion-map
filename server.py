"""A local, stdlib HTTP server for the standalone companion map."""
from __future__ import annotations

import argparse
import gzip
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
import os
from pathlib import Path
import re
import socket
import threading
import time
from urllib.parse import parse_qs, urlsplit
import webbrowser

import paths
from i18n import language, t
from saves import SaveReader
import gow_memory
import gow_pins
import gow_favors
import gow_codex

VERSION = '0.4.0'
REALMS = ('midgard', 'vanaheim', 'svartalfheim', 'alfheim', 'jotunheim', 'asgard',
          'helheim', 'niflheim', 'muspelheim', 'sindris-house')


def _icon_svg() -> bytes:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128">'
        '<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0" stop-color="#0b151f"/><stop offset="1" stop-color="#060b10"/>'
        '</linearGradient></defs>'
        '<rect width="128" height="128" rx="26" fill="url(#bg)" stroke="#c8a258" stroke-width="3"/>'
        '<circle cx="64" cy="64" r="42" fill="none" stroke="#c8a258" stroke-width="2.5" stroke-opacity="0.5"/>'
        '<path d="M44 90h16V78c-10-5-16-14-16-24 0-12 9-22 20-22s20 10 20 22c0 10-6 19-16 24v12h16v8H68V83'
        'c11-5 19-16 19-29 0-16-10-29-23-29S41 38 41 54c0 13 8 24 19 29v15H44z" fill="#e5c378"/>'
        '</svg>'
    ).encode('utf-8')


_ICON_PNG_CACHE: dict[int, bytes] = {}


def _icon_png(size: int) -> bytes:
    cached = _ICON_PNG_CACHE.get(size)
    if cached is not None:
        return cached
    from PIL import Image, ImageDraw
    s = size
    im = Image.new('RGBA', (s, s), (6, 11, 16, 255))
    d = ImageDraw.Draw(im)
    pad = max(2, round(s * 0.04))
    rad = max(6, round(s * 0.20))
    d.rounded_rectangle([pad, pad, s - pad - 1, s - pad - 1], radius=rad,
                        fill=(11, 21, 31, 255), outline=(200, 162, 88, 255), width=max(2, round(s * 0.025)))
    rp = round(s * 0.16)
    d.ellipse([rp, rp, s - rp, s - rp], outline=(200, 162, 88, 128), width=max(1, round(s * 0.018)))
    # Crisp stylized gold Omega arc + pedestal bars
    r0 = round(s * 0.24)
    w_arc = max(3, round(s * 0.075))
    d.arc([r0, round(s * 0.20), s - r0, round(s * 0.72)], start=132, end=48, fill=(229, 195, 120, 255), width=w_arc)
    y_foot = round(s * 0.72)
    h_foot = max(2, round(s * 0.07))
    d.rectangle([round(s * 0.28), y_foot, round(s * 0.44), y_foot + h_foot], fill=(229, 195, 120, 255))
    d.rectangle([round(s * 0.56), y_foot, round(s * 0.72), y_foot + h_foot], fill=(229, 195, 120, 255))
    buf = io.BytesIO()
    im.save(buf, 'PNG', optimize=True)
    out = buf.getvalue()
    _ICON_PNG_CACHE[size] = out
    return out


def _realm_scale_per_metre(realm: str) -> float | None:
    rec = (gow_memory.REALM_AFFINE_TRANSFORMS.get(realm)
           or gow_memory.REALM_SIMILARITY_TRANSFORMS.get(realm) or {})
    mat = rec.get('matrix')
    if not mat and rec.get('zones'):
        mat = next((z.get('matrix') for z in rec['zones'] if z.get('matrix')), None)
    if not mat:
        return None
    det = abs(mat[0][0] * mat[1][1] - mat[0][1] * mat[1][0])
    return (det ** 0.5) if det > 0 else None


def _save_fingerprint(save: dict | None) -> tuple:
    """Fast, privacy-free fingerprint of save state for caching and SSE change detection."""
    if not save:
        return (False,)
    pt = save.get('progression_tables') or (save.get('progress') or {}).get('progression_tables') or {}
    t2 = pt.get('table2_stage') or {}
    t1i = pt.get('table1_int') or {}
    t1b = pt.get('table1_bool') or ()
    wallet = save.get('wallet') or {}
    t2_sig = (len(t2), sum(v for v in t2.values() if isinstance(v, int)))
    t1i_sig = (len(t1i), sum(v for v in t1i.values() if isinstance(v, int)))
    t1b_sig = len(t1b) if isinstance(t1b, (list, tuple, set, dict)) else 0
    return (
        bool(save.get('ok')),
        Path(str((save.get('source') or {}).get('slot') or '')).name,
        save.get('realm'),
        save.get('play_time'),
        save.get('objective'),
        save.get('power_level'),
        wallet.get('wallet_hacksilver', save.get('hacksilver')),
        wallet.get('kratos_xp', save.get('xp')),
        t2_sig,
        t1i_sig,
        t1b_sig,
    )


class _CompanionHTTPServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, server_address, RequestHandlerClass):
        self.stop_event = threading.Event()
        super().__init__(server_address, RequestHandlerClass)

    def handle_error(self, request, client_address):
        import sys
        exc = sys.exc_info()[1]
        if isinstance(exc, (ConnectionAbortedError, ConnectionResetError, BrokenPipeError)):
            return
        super().handle_error(request, client_address)

    def shutdown(self):
        self.stop_event.set()
        super().shutdown()


class App:
    def __init__(self, save_reader=None, telemetry_reader=None, codex_builder=None):
        self.save_reader = save_reader or SaveReader().read
        self.telemetry_reader = telemetry_reader or gow_memory.read_live_telemetry
        self.codex_builder = codex_builder or gow_codex.build_codex
        self.lock = threading.Lock()
        self._codex_cache: dict[tuple, dict] = {}

    def _read_codex_locked(self, save: dict, lang: str) -> dict:
        fp = _save_fingerprint(save)
        key = (fp, lang)
        cached = self._codex_cache.get(key)
        if cached is not None:
            return cached
        built = self.codex_builder(save, lang)
        if built and built.get('ok'):
            gow_codex.attach_map_links(built, save, lang, REALMS)
        if len(self._codex_cache) >= 6:
            self._codex_cache.clear()
        self._codex_cache[key] = built
        return built

    def codex_payload(self, lang='en') -> dict:
        lang = language(lang)
        with self.lock:
            save = self.save_reader() or {}
            return self._read_codex_locked(save, lang)

    def stream_tick(self, lang='en') -> tuple[tuple, dict, dict]:
        """Return (save_fingerprint, live_telemetry, codex_dict) for one SSE tick."""
        lang = language(lang)
        with self.lock:
            save = self.save_reader() or {}
            prog = save.get('progress') or save
            current = gow_pins.normalize_realm_key(save.get('realm') or prog.get('realm'))
            if current not in REALMS:
                current = 'midgard'
            try:
                lt = self.telemetry_reader(active_realm=current) or {'available': False}
            except (OSError, ValueError, RuntimeError, AttributeError):
                lt = {'available': False, 'reason': 'memory_unavailable'}
            if (lt.get('build_fingerprint') or {}).get('matched') is False:
                lt = dict(lt, available=False, radar=None, position=None, kratos=None,
                          reason_code='unsupported_build', reason=t('unsupported_build', lang))
            lt_pub = {k: v for k, v in lt.items() if k != 'pid'}
            fp = _save_fingerprint(save)
            codex = self._read_codex_locked(save, lang)
            return fp, lt_pub, codex

    def payload(self, realm=None, lang='en', manual_ids=None):
        lang = language(lang)
        with self.lock:
            save = self.save_reader() or {}
            prog = save.get('progress') or save
            current = gow_pins.normalize_realm_key(save.get('realm') or prog.get('realm'))
            if current not in REALMS:
                current = 'midgard'
            selected = realm if realm in REALMS else current
            try:
                lt = self.telemetry_reader(active_realm=current) or {'available': False}
            except (OSError, ValueError, RuntimeError, AttributeError):
                lt = {'available': False, 'reason': 'memory_unavailable'}
            reason = lt.get('reason', '')
            if not lt.get('available'):
                code = reason if reason in ('unsupported_build', 'build_unverified', 'memory_unavailable') else (
                    'memory_unavailable' if lt.get('process_running') else 'game_closed')
                lt = dict(lt, reason_code=code, reason=t(code, lang))
            # A different patch may provide a running process, but never a live marker.
            if (lt.get('build_fingerprint') or {}).get('matched') is False:
                lt = dict(lt, available=False, radar=None, position=None, kratos=None,
                          reason_code='unsupported_build', reason=t('unsupported_build', lang))
            all_comp = gow_pins.get_all_realms_completion(save_data=save, lang=lang, manual_ids=manual_ids)
            pins = gow_pins.get_realm_pois(selected, save_data=save, lang=lang, manual_ids=manual_ids)
            bounds = gow_memory.REALM_BOUNDING_BOXES[selected]
            meta = []
            for key in REALMS:
                b = gow_memory.REALM_BOUNDING_BOXES[key]
                meta.append(dict(key=key, name=t(key, lang), name_en=t(key), is_current=bool(save.get('ok')) and key == current,
                                 completion=all_comp['by_realm'].get(key),
                                 **{k: b[k] for k in ('center_lat', 'center_lng', 'min_zoom', 'max_zoom', 'initial_zoom')}))
            rm = dict(favors=gow_favors.read_favors(save, lang), active_realm=t(current, lang),
                      active_realm_key=current, selected_realm_key=selected,
                      realm_name=t(selected, lang), slug=selected, realm_pois=pins,
                      realms=meta, realm_completion=gow_pins.summarize_pois_completion(pins),
                      global_completion={k: all_comp[k] for k in ('total', 'collected', 'remaining', 'unknown', 'percent')},
                      sindris_house_completion=all_comp['by_realm'].get('sindris-house'),
                      update_policy=t('save_updates', lang), collectibles=prog.get('collectibles') or {},
                      is_hub=current == 'sindris-house',
                      map_scale_per_metre=_realm_scale_per_metre(selected),
                      **{k: bounds[k] for k in ('center_lat', 'center_lng', 'min_zoom', 'max_zoom', 'initial_zoom')})
            # Expose no save path, account folder, raw save bytes, PID or RAM address.
            public_save = {k: save.get(k) for k in ('ok', 'place', 'objective', 'play_time', 'difficulty')}
            public_save['source'] = {'slot': Path(str((save.get('source') or {}).get('slot') or '')).name}
            if lang == 'en' and save.get('ok'):
                # Save header strings reflect the game's language. Prefer installed EN strings.
                from gow_story import get_story_progress
                story = get_story_progress(save.get('objective_string_id'), lang='en')
                public_save['objective'] = story.get('objective_title') or save.get('objective')
                public_save['place'] = t(current, lang)
                pt_str = public_save.get('play_time')
                if isinstance(pt_str, str) and pt_str:
                    pt_en = re.sub(r'\s*ч(?=\s|$)', 'h', pt_str)
                    pt_en = re.sub(r'\s*мин(?=\s|$)', 'm', pt_en)
                    pt_en = re.sub(r'\s*с(?=\s|$)', 's', pt_en)
                    public_save['play_time'] = pt_en
            if save.get('ok') and save.get('difficulty_id') in range(5):
                public_save['difficulty'] = t('difficulty_' + str(save['difficulty_id']), lang)
            missing = [key for key in REALMS if not (gow_pins.PINS / (key + '.json')).is_file()]
            notices = ([t('save_missing', lang)] if not save.get('ok') else [])
            if missing:
                notices.append(t('pins_missing', lang))
            lt = {k: v for k, v in lt.items() if k != 'pid'}
            codex = self._read_codex_locked(save, lang)
            return {'ok': True, 'version': VERSION, 'lang': lang, 'realms_map': rm,
                    'save': public_save, 'live_telemetry': lt, 'notices': notices,
                    'codex_summary': codex.get('summary') or {}, 'hero': codex.get('hero') or {}}


def make_server(host='127.0.0.1', port=8790, app=None, offline=False):
    app = app or App()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass  # The console contains startup information, never personal file paths.

        def reply(self, status, data, content_type='application/json; charset=utf-8', cache=False):
            if not isinstance(data, bytes):
                data = json.dumps(data, ensure_ascii=False).encode('utf-8')
            use_gzip = (
                len(data) >= 1024
                and not content_type.startswith('image/')
                and 'gzip' in (self.headers.get('Accept-Encoding') or '').lower()
            )
            if use_gzip:
                data = gzip.compress(data, compresslevel=5)
            try:
                self.send_response(status)
                self.send_header('Content-Type', content_type)
                if use_gzip:
                    self.send_header('Content-Encoding', 'gzip')
                self.send_header('Vary', 'Accept, Accept-Encoding')
                self.send_header('Content-Length', str(len(data)))
                self.send_header('X-Content-Type-Options', 'nosniff')
                self.send_header('Cache-Control', 'public, max-age=86400' if cache else 'no-store')
                self.end_headers()
                if data:
                    self.wfile.write(data)
            except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
                return

        def do_GET(self):
            url = urlsplit(self.path)
            query = parse_qs(url.query)
            lang = language(query.get('lang', [self.headers.get('Accept-Language', 'en')])[0])
            try:
                if url.path in ('/', '/gow-map'):
                    self.reply(200, (paths.ROOT / 'web/index.html').read_bytes(), 'text/html; charset=utf-8')
                elif url.path == '/manifest.webmanifest':
                    manifest = {
                        'name': 'God of War Ragnarök — Companion Map',
                        'short_name': 'GoWR 3D Map',
                        'start_url': '/',
                        'display': 'standalone',
                        'orientation': 'landscape',
                        'background_color': '#060b10',
                        'theme_color': '#0b151f',
                        'icons': [
                            {'src': '/icon.svg', 'sizes': 'any', 'type': 'image/svg+xml', 'purpose': 'any maskable'},
                            {'src': '/icon-192.png', 'sizes': '192x192', 'type': 'image/png', 'purpose': 'any'},
                            {'src': '/icon-512.png', 'sizes': '512x512', 'type': 'image/png', 'purpose': 'any'},
                        ],
                    }
                    self.reply(200, manifest, 'application/manifest+json; charset=utf-8')
                elif url.path == '/icon.svg':
                    self.reply(200, _icon_svg(), 'image/svg+xml', cache=True)
                elif url.path in ('/icon-192.png', '/icon-512.png'):
                    sz = 192 if url.path == '/icon-192.png' else 512
                    self.reply(200, _icon_png(sz), 'image/png', cache=True)
                elif url.path.startswith('/api/realm-height/'):
                    import gow_game_tiles
                    rest = url.path.removeprefix('/api/realm-height/')
                    if rest.endswith('/meta.json'):
                        realm = rest[:-len('/meta.json')]
                        if realm not in REALMS:
                            self.reply(404, {'error': t('not_found', lang)})
                            return
                        meta = gow_game_tiles.get_realm_height_meta(realm)
                        if meta is None:
                            self.reply(404, {'error': t('not_found', lang)})
                            return
                        self.reply(200, meta)
                    elif '/' not in rest and rest in REALMS:
                        data = gow_game_tiles.get_realm_height_png(rest)
                        self.reply(200 if data else 204, data or b'', 'image/png', cache=bool(data))
                    else:
                        self.reply(404, {'error': t('not_found', lang)})
                elif url.path.startswith('/api/realm-3d/'):
                    import gow_game_tiles
                    rest = url.path.removeprefix('/api/realm-3d/')
                    parts = rest.split('/')
                    if len(parts) != 2 or parts[0] not in REALMS:
                        self.reply(404, {'error': t('not_found', lang)})
                        return
                    realm_key, fname = parts[0], parts[1]
                    if fname == 'meta.json':
                        self.reply(200, gow_game_tiles.get_realm_native_3d_meta(realm_key))
                    elif fname in gow_game_tiles.NATIVE_3D_FILES:
                        accept_webp = 'image/webp' in (self.headers.get('Accept') or '').lower()
                        got = gow_game_tiles.get_realm_native_3d_file(realm_key, fname, prefer_webp=accept_webp)
                        if not got:
                            self.reply(204, b'', gow_game_tiles.NATIVE_3D_FILES[fname])
                        else:
                            self.reply(200, got[0], got[1], cache=True)
                    else:
                        self.reply(404, {'error': t('not_found', lang)})
                elif url.path.startswith('/api/map-detail/'):
                    import gow_game_tiles
                    rest = url.path.removeprefix('/api/map-detail/')
                    if not rest.endswith('.png') or '/' in rest:
                        self.reply(404, {'error': t('not_found', lang)})
                        return
                    name = rest[:-4]
                    if name not in gow_game_tiles.MAP_DETAIL_ASSETS:
                        self.reply(404, {'error': t('not_found', lang)})
                        return
                    data = gow_game_tiles.get_map_detail_png(name)
                    self.reply(200 if data else 204, data or b'', 'image/png', cache=bool(data))
                elif url.path.startswith('/api/map-icon/'):
                    import gow_game_tiles
                    rest = url.path.removeprefix('/api/map-icon/')
                    if not rest.endswith('.png') or '/' in rest:
                        self.reply(404, {'error': t('not_found', lang)})
                        return
                    key = rest[:-4]
                    if key not in gow_game_tiles.MAP_ICON_ASSETS:
                        self.reply(404, {'error': t('not_found', lang)})
                        return
                    data = gow_game_tiles.get_map_icon_png(key)
                    self.reply(200 if data else 204, data or b'', 'image/png', cache=bool(data))
                elif url.path == '/api/codex':
                    self.reply(200, app.codex_payload(lang))
                elif url.path.startswith('/api/codex/book/'):
                    rest = url.path.removeprefix('/api/codex/book/')
                    if not rest.endswith('.png') or '/' in rest:
                        self.reply(404, {'error': t('not_found', lang)})
                        return
                    asset = rest[:-4]
                    if asset not in gow_codex.BOOK_ASSETS:
                        self.reply(404, {'error': t('not_found', lang)})
                        return
                    data = gow_codex.get_codex_book_asset_png(asset)
                    self.reply(200 if data else 204, data or b'', 'image/png', cache=bool(data))
                elif url.path.startswith('/api/codex/icon/'):
                    rest = url.path.removeprefix('/api/codex/icon/')
                    if not rest.endswith('.png') or '/' in rest:
                        self.reply(404, {'error': t('not_found', lang)})
                        return
                    key = rest[:-4]
                    if not gow_codex.ICON_KEY_RE.match(key):
                        self.reply(404, {'error': t('not_found', lang)})
                        return
                    ink = 'dark' if query.get('ink', ['gold'])[0] == 'dark' else 'gold'
                    data = gow_codex.get_codex_icon_png(key, ink=ink)
                    self.reply(200 if data else 204, data or b'', 'image/png', cache=bool(data))
                elif url.path == '/api/stream':
                    once = query.get('once', ['0'])[0] == '1'
                    try:
                        interval = max(0.05, min(2.0, float(query.get('interval', ['0.4'])[0])))
                    except ValueError:
                        interval = 0.4
                    self._handle_sse(lang, once=once, interval=interval)
                elif url.path in ('/api/map', '/api/companion'):
                    realm = query.get('realm', [None])[0]
                    if realm and realm not in REALMS:
                        self.reply(400, {'ok': False, 'error': t('bad_request', lang)})
                    else:
                        marked = query.get('marked', [''])[0]
                        ids = marked.split(',') if marked else []
                        if len(marked) > 20000 or any(not (p.isascii() and p.isdigit() and len(p) <= 10) for p in ids):
                            self.reply(400, {'ok': False, 'error': t('bad_request', lang)})
                        else:
                            self.reply(200, app.payload(realm, lang, set(ids)))
                elif url.path == '/gow-game-tiles/available.json':
                    import gow_game_tiles
                    self.reply(200, {'realms': gow_game_tiles.realms_available()})
                elif url.path.startswith('/gow-tiles/') or url.path.startswith('/gow-game-tiles/'):
                    import gow_tiles
                    import gow_game_tiles
                    native = url.path.startswith('/gow-game-tiles/')
                    module = gow_game_tiles if native else gow_tiles
                    parsed = module.parse_path(url.path)
                    if not parsed:
                        self.reply(404, {'error': t('not_found', lang)})
                        return
                    if offline and not native:
                        realm, z, x, y = parsed
                        target = gow_tiles.CACHE_DIR / realm / str(z) / str(x) / f'{y}.png'
                        data = target.read_bytes() if target.is_file() else None
                    else:
                        data = module.get_tile(*parsed)
                    self.reply(200 if data else 204, data or b'', 'image/png', cache=bool(data))
                elif url.path.startswith('/web/'):
                    name = url.path.removeprefix('/web/')
                    allowed = {'map_engine.js': 'text/javascript', 'map_engine.css': 'text/css',
                               'i18n.js': 'text/javascript', 'companion_gow_map.js': 'text/javascript',
                               'companion_gow_map.css': 'text/css'}
                    if name not in allowed:
                        self.reply(404, {'error': t('not_found', lang)})
                        return
                    self.reply(200, (paths.ROOT / 'web' / name).read_bytes(), allowed[name] + '; charset=utf-8')
                else:
                    self.reply(404, {'error': t('not_found', lang)})
            except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
                return
            except (OSError, ValueError, KeyError, RuntimeError):
                self.reply(500, {'ok': False, 'error': t('internal_error', lang)})

        def _send_sse_event(self, event: str, payload: dict) -> bool:
            raw = f'event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n'.encode('utf-8')
            try:
                self.wfile.write(raw)
                self.wfile.flush()
                return True
            except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError, OSError):
                return False

        def _handle_sse(self, lang: str, once: bool = False, interval: float = 0.4):
            stop_ev = getattr(self.server, 'stop_event', None)
            self.close_connection = True
            try:
                self.send_response(200)
                self.send_header('Content-Type', 'text/event-stream; charset=utf-8')
                self.send_header('Cache-Control', 'no-cache, no-transform')
                self.send_header('Connection', 'close' if once else 'keep-alive')
                self.send_header('X-Accel-Buffering', 'no')
                self.end_headers()
            except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError, OSError):
                return

            fp, lt, codex = app.stream_tick(lang)
            prev_snap = gow_codex.codex_snapshot(codex)
            prev_fp = fp

            def tel_sig(t_obj: dict):
                r = t_obj.get('radar') or {}
                lat = r.get('map_lat')
                lng = r.get('map_lng')
                yaw = r.get('yaw_deg')
                return (
                    bool(t_obj.get('available')),
                    bool(t_obj.get('process_running')),
                    r.get('realm_key'),
                    round(lat, 5) if isinstance(lat, (int, float)) else None,
                    round(lng, 5) if isinstance(lng, (int, float)) else None,
                    round(yaw, 1) if isinstance(yaw, (int, float)) else None,
                )

            prev_tel = tel_sig(lt)
            if not self._send_sse_event('hello', {
                'version': VERSION,
                'codex_summary': codex.get('summary') or {},
                'live_telemetry': lt,
            }):
                return
            if once:
                return

            last_ping = time.monotonic()
            while not (stop_ev and stop_ev.is_set()):
                if stop_ev:
                    if stop_ev.wait(interval):
                        break
                else:
                    time.sleep(interval)
                try:
                    fp, lt, codex = app.stream_tick(lang)
                except (OSError, ValueError, KeyError, RuntimeError):
                    continue
                cur_tel = tel_sig(lt)
                if cur_tel != prev_tel:
                    prev_tel = cur_tel
                    if not self._send_sse_event('telemetry', {'live_telemetry': lt}):
                        return
                    last_ping = time.monotonic()
                if fp != prev_fp:
                    prev_fp = fp
                    curr_snap = gow_codex.codex_snapshot(codex)
                    delta = gow_codex.compute_codex_diff(prev_snap, curr_snap)
                    prev_snap = curr_snap
                    if not self._send_sse_event('save_updated', {
                        'codex_summary': codex.get('summary') or {},
                        'delta': delta,
                    }):
                        return
                    if delta.get('has_changes'):
                        if not self._send_sse_event('codex_delta', {
                            **delta,
                            'summary': codex.get('summary') or {},
                        }):
                            return
                    last_ping = time.monotonic()
                elif time.monotonic() - last_ping >= 15.0:
                    try:
                        self.wfile.write(b': ping\n\n')
                        self.wfile.flush()
                    except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError, OSError):
                        return
                    last_ping = time.monotonic()

    return _CompanionHTTPServer((host, port), Handler)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--port', type=int, default=8790)
    p.add_argument('--lan', action='store_true', help='Listen on the local network')
    p.add_argument('--game-dir', type=Path)
    p.add_argument('--save-dir', type=Path)
    p.add_argument('--autocalib', action='store_true', help='Opt in to automatic screen calibration')
    p.add_argument('--offline', action='store_true', help='Use cached data; never fetch tiles')
    p.add_argument('--no-browser', action='store_true')
    p.add_argument('--lang', choices=['ru', 'en'], default='en', help='Terminal language (browser chooses UI language)')
    args = p.parse_args(argv)
    if args.game_dir:
        paths.GAME_DIR = paths.find_game_dir(args.game_dir)
    if args.offline:
        print(t('offline', args.lang))
    else:
        from tools.fetch_mapgenie import prepare
        print(t('download', args.lang))
        prepare(notify=print)
    if paths.find_game_dir():
        from tools.build_gow_ru_names import build_names
        try:
            build_names()
        except (OSError, ValueError, RuntimeError):
            print(t('internal_error', args.lang))
    if args.autocalib:
        try:
            from tools.gow_auto_calibrate import _vision, start_background
            _vision()
            os.environ['GOWR_AUTOCALIB'] = '1'
            start_background()
        except ImportError:
            print(t('autocalib_missing', args.lang))
        except RuntimeError:
            print(t('autocalib_templates', args.lang))
    app = App(save_reader=SaveReader(args.save_dir).read)
    with make_server('0.0.0.0' if args.lan else '127.0.0.1', args.port, app, args.offline) as httpd:
        url = f'http://127.0.0.1:{httpd.server_port}/'
        print(t('ready', args.lang) + ': ' + url)
        if args.lan:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                try:
                    # Local route lookup only; no packet is transmitted.
                    s.connect(('192.0.2.1', 9))
                    print(f'LAN: http://{s.getsockname()[0]}:{httpd.server_port}/')
                except OSError:
                    print(f'LAN: http://<LAN-IP>:{httpd.server_port}/')
        if not args.no_browser:
            webbrowser.open(url)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
