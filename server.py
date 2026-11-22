"""A local, stdlib HTTP server for the standalone companion map."""
from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import socket
import threading
from urllib.parse import parse_qs, urlsplit
import webbrowser

import paths
from i18n import language, t
from saves import SaveReader
import gow_memory
import gow_pins
import gow_favors

VERSION = '0.2.0'
REALMS = ('midgard', 'vanaheim', 'svartalfheim', 'alfheim', 'jotunheim', 'asgard',
          'helheim', 'niflheim', 'muspelheim', 'sindris-house')


class App:
    def __init__(self, save_reader=None, telemetry_reader=None):
        self.save_reader = save_reader or SaveReader().read
        self.telemetry_reader = telemetry_reader or gow_memory.read_live_telemetry
        self.lock = threading.Lock()

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
            if save.get('ok') and save.get('difficulty_id') in range(5):
                public_save['difficulty'] = t('difficulty_' + str(save['difficulty_id']), lang)
            missing = [key for key in REALMS if not (gow_pins.PINS / (key + '.json')).is_file()]
            notices = ([t('save_missing', lang)] if not save.get('ok') else [])
            if missing:
                notices.append(t('pins_missing', lang))
            lt = {k: v for k, v in lt.items() if k != 'pid'}
            return {'ok': True, 'version': VERSION, 'lang': lang, 'realms_map': rm,
                    'save': public_save, 'live_telemetry': lt, 'notices': notices}


def make_server(host='127.0.0.1', port=8790, app=None, offline=False):
    app = app or App()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass  # The console contains startup information, never personal file paths.

        def reply(self, status, data, content_type='application/json; charset=utf-8', cache=False):
            if not isinstance(data, bytes):
                data = json.dumps(data, ensure_ascii=False).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(data)))
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Cache-Control', 'public, max-age=86400' if cache else 'no-store')
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            url = urlsplit(self.path)
            query = parse_qs(url.query)
            lang = language(query.get('lang', [self.headers.get('Accept-Language', 'en')])[0])
            try:
                if url.path in ('/', '/gow-map'):
                    self.reply(200, (paths.ROOT / 'web/index.html').read_bytes(), 'text/html; charset=utf-8')
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
            except (OSError, ValueError, KeyError, RuntimeError):
                self.reply(500, {'ok': False, 'error': t('internal_error', lang)})

    return ThreadingHTTPServer((host, port), Handler)


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
