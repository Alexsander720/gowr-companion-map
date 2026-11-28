def test_standalone_import():
    import server
    assert callable(server.make_server)


import http.client
import json
import threading
import pytest
import gow_pins
import server


@pytest.fixture
def running_server(synthetic_map):
    (gow_pins.PINS/'midgard.json').write_text(json.dumps(synthetic_map))
    app=server.App(save_reader=lambda:{},telemetry_reader=lambda **kwargs:{'available':False,'process_running':False})
    httpd=server.make_server(port=0,app=app,offline=True)
    thread=threading.Thread(target=httpd.serve_forever,daemon=True);thread.start()
    yield httpd
    httpd.shutdown();httpd.server_close();thread.join()


def get(httpd,path):
    con=http.client.HTTPConnection('127.0.0.1',httpd.server_port,timeout=10)
    con.request('GET',path);res=con.getresponse();data=res.read();status=res.status
    con.close();return status,data


def test_api_synthetic_contract_and_languages(running_server):
    status,raw=get(running_server,'/api/map?lang=en&realm=midgard');d=json.loads(raw)
    assert status == 200 and d['ok']
    assert len(d['realms_map']['realms']) == 10
    assert len(d['realms_map']['realm_pois']) == 2
    assert d['realms_map']['realm_name'] == 'Midgard'
    status,raw=get(running_server,'/api/map?lang=ru');ru=json.loads(raw)
    assert ru['realms_map']['realm_name'] == 'Мидгард'
    assert not d['live_telemetry'].get('available')
    assert d['live_telemetry'].get('radar') is None
    assert 'path' not in d['save'].get('source',{})


def test_invalid_routes_are_bounded(running_server):
    for path in ['/api/map?realm=../escape','/web/../../server.py','/gow-tiles/unknown/11/1/1.png','/api/companion/check_poi']:
        assert get(running_server,path)[0] in (400,404)
    assert get(running_server,'/')[0] == 200


def test_new_build_keeps_map_but_hides_marker():
    app=server.App(save_reader=lambda:{},telemetry_reader=lambda **kwargs:{
        'available':True,'process_running':True,'radar':{'map_lat':.7,'map_lng':-.7},
        'build_fingerprint':{'matched':False}})
    d=app.payload(lang='en')
    assert d['ok']
    assert d['live_telemetry']['available'] is False
    assert d['live_telemetry']['radar'] is None
    assert d['live_telemetry']['reason_code'] == 'unsupported_build'


def test_memory_failure_does_not_break_the_map():
    def denied(**kwargs): raise OSError('Synthetic process permission error')
    d=server.App(save_reader=lambda:{},telemetry_reader=denied).payload()
    assert d['ok']
    assert d['live_telemetry']['available'] is False
    assert d['live_telemetry']['reason_code'] == 'memory_unavailable'


def test_browser_marks_update_every_completion_summary(running_server):
    status,raw=get(running_server,'/api/map?marked=1');d=json.loads(raw);rm=d['realms_map']
    assert status == 200
    assert rm['realm_completion']['collected'] == 1
    assert rm['global_completion']['collected'] == 1
    assert next(r for r in rm['realms'] if r['key']=='midgard')['completion']['collected'] == 1
    _,raw=get(running_server,'/api/map');assert json.loads(raw)['realms_map']['global_completion']['collected'] == 0
    assert get(running_server,'/api/map?marked=not-an-id')[0] == 400


def test_offline_miss_is_not_http_cached(running_server):
    con=http.client.HTTPConnection('127.0.0.1',running_server.server_port,timeout=5)
    con.request('GET','/gow-tiles/midgard/1/0/0.png');r=con.getresponse();r.read()
    assert r.status == 204
    assert r.getheader('Cache-Control') == 'no-store'
    con.close()


def test_english_save_fallback_and_difficulty():
    save={'ok':True,'realm':'midgard','objective':'Synthetic objective','difficulty_id':2}
    d=server.App(save_reader=lambda:save,telemetry_reader=lambda **kw:{'available':False}).payload(lang='en')
    assert d['save']['objective'] == 'Synthetic objective'
    assert d['save']['difficulty'] == 'Balance'
    d=server.App(save_reader=lambda:{'ok':False},telemetry_reader=lambda **kw:{'available':False}).payload(lang='en')
    assert d['save']['place'] is None


def test_realm_height_endpoints_and_pwa_manifest(running_server, monkeypatch, tmp_path):
    import gow_game_tiles
    from tools.gow_game_map import encode_h16_png
    import numpy as np

    maps_dir = tmp_path / 'maps'
    maps_dir.mkdir()
    monkeypatch.setattr(gow_game_tiles, 'MAPS_DIR', maps_dir)

    con = http.client.HTTPConnection('127.0.0.1', running_server.server_port, timeout=5)
    con.request('GET', '/api/realm-height/midgard')
    r = con.getresponse(); r.read()
    assert r.status == 204
    assert r.getheader('Cache-Control') == 'no-store'

    status, raw = get(running_server, '/api/realm-height/midgard/meta.json')
    meta = json.loads(raw)
    assert status == 200 and meta['realm'] == 'midgard' and meta['has_heightmap'] is False
    assert {'lat_min', 'lat_max', 'lng_min', 'lng_max'} <= meta['bounds'].keys()
    assert 'key_light' in meta['palette']

    (maps_dir / 'midgard_h16.png').write_bytes(encode_h16_png(np.linspace(0, 1, 64 * 64, dtype=np.float32).reshape(64, 64)))
    con.request('GET', '/api/realm-height/midgard')
    r = con.getresponse(); body = r.read()
    assert r.status == 200
    assert r.getheader('Content-Type') == 'image/png'
    assert 'max-age=86400' in (r.getheader('Cache-Control') or '')
    assert body.startswith(b'\x89PNG')
    con.close()

    status, raw = get(running_server, '/api/realm-height/midgard/meta.json')
    assert status == 200 and json.loads(raw)['has_heightmap'] is True
    assert get(running_server, '/api/realm-height/../secret')[0] == 404
    assert get(running_server, '/api/realm-height/unknown/meta.json')[0] == 404

    status, raw = get(running_server, '/manifest.webmanifest')
    manifest = json.loads(raw)
    assert status == 200 and manifest['display'] == 'standalone' and manifest['orientation'] == 'landscape'
    assert {ic['src'] for ic in manifest['icons']} >= {'/icon.svg', '/icon-192.png', '/icon-512.png'}
    status, raw = get(running_server, '/icon.svg')
    assert status == 200 and b'<svg' in raw
    for icon_path in ('/icon-192.png', '/icon-512.png'):
        st, raw_png = get(running_server, icon_path)
        assert st == 200 and raw_png.startswith(b'\x89PNG')
    import gzip
    con = http.client.HTTPConnection('127.0.0.1', running_server.server_port, timeout=5)
    con.request('GET', '/api/map?lang=en&realm=midgard', headers={'Accept-Encoding': 'gzip'})
    gr = con.getresponse(); gbody = gr.read()
    assert gr.status == 200 and gr.getheader('Content-Encoding') == 'gzip'
    assert json.loads(gzip.decompress(gbody))['ok'] is True
    con.close()
