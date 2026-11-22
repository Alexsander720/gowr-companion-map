"""Optional, locally authored guides; all fixtures are synthetic and offline."""
import json
import os
import io
import threading
from pathlib import Path

import pytest
import gow_pins as pins
import gow_favors as favors
from tools.check_clean import inspect_file


@pytest.fixture
def guide_data(monkeypatch, tmp_path, synthetic_map):
    data = tmp_path / 'data'
    data.mkdir()
    for name, obj in {
        'category_ids.json': {'7100': 'nornir_chest', '7107': 'legendary_chest'},
        'pin_mapping.json': {'1': {'t2_hash': '0x11'}}, 'region_sids.json': {},
    }.items():
        (data / name).write_text(json.dumps(obj), encoding='utf-8')
    monkeypatch.setattr(pins, 'DATA', data)
    monkeypatch.setattr(favors, 'DATA', data)
    pins._load_categories_map.cache_clear()
    pins._load_pin_mapping.cache_clear()
    (pins.PINS / 'midgard.json').write_text(json.dumps(synthetic_map), encoding='utf-8')
    quest = {'id': 'Favor_Test', 'name': 'Synthetic favor', 'hash': '0x22',
             'region': 'Synthetic region', 'realm': 'midgard', 'pin_ids': [], 'pin_realms': {},
             'step_locations_unknown': True, 'steps': [
                 {'id': 'Goal_Test', 'hash': '0x33', 'name': 'Synthetic goal', 'counter': None, 'steps': []}]}
    monkeypatch.setattr(favors, '_base_catalog', lambda: {'favors': [quest]})
    monkeypatch.setattr(favors, 'load_catalog', lambda lang='en': {'favors': [quest]})
    yield data
    pins._load_categories_map.cache_clear()
    pins._load_pin_mapping.cache_clear()


def write_guides(data, obj):
    path = data / 'guides.json'
    path.write_text(json.dumps(obj, ensure_ascii=False), encoding='utf-8')
    # Force distinct mtimes even on filesystems with coarse clock resolution.
    stamp = path.stat().st_mtime_ns + 1000000
    os.utime(path, ns=(stamp, stamp))


@pytest.mark.parametrize('content', [None, '{broken', '[]', 'null', '{"version":2}', '{"version":1,"pins":[]}'])
def test_missing_or_invalid_guides_are_optional(guide_data, content):
    if content is not None:
        (guide_data / 'guides.json').write_text(content, encoding='utf-8')
    assert pins._load_guides().get('pins', {}) == {}
    assert all('guide' not in p for p in pins.get_realm_pois('midgard'))
    assert 'guide' not in favors.read_favors(None)[0]


def test_guides_language_links_and_mtime(guide_data):
    write_guides(guide_data, {'version': 1, 'pins': {'1': {
        'ru': '**Печати**: [Тайник](https://mapgenie.io/test?locationIds=2)',
        'en': '**Seals**', 'sources': ['https://example.invalid/guide']}}})
    ru = pins.get_realm_pois('midgard', lang='ru')[0]['guide']
    assert ru == {'text': '**Печати**: [Synthetic cache](pin:midgard:2)', 'lang': 'ru',
                  'sources': ['https://example.invalid/guide']}
    assert pins.get_realm_pois('midgard', lang='fr')[0]['guide']['text'] == '**Seals**'
    write_guides(guide_data, {'version': 1, 'pins': {'1': {'en': 'Changed'}}})
    assert pins.get_realm_pois('midgard', lang='ru')[0]['guide'] == {
        'text': 'Changed', 'lang': 'en', 'sources': []}
    write_guides(guide_data, {'version': 1, 'pins': {'1': {'ru': 'Только русский'}}})
    assert pins.get_realm_pois('midgard', lang='en')[0]['guide']['lang'] == 'ru'
    (guide_data / 'guides.json').write_text('{broken', encoding='utf-8')
    assert 'guide' not in pins.get_realm_pois('midgard')[0]


def test_favor_points_use_anchor_coordinates_and_objective_ids(guide_data):
    write_guides(guide_data, {'version': 1, 'favors': {'Favor_Test': {
        'ru': 'Найти печать', 'en': 'Find the seal', 'points': [
            {'step': 'Goal_Test', 'anchor_pin': '2', 'realm': 'midgard', 'label_ru': 'У тайника', 'label_en': 'At cache'},
            {'step': None, 'anchor_pin': '9999', 'realm': 'midgard'},
            {'step': None, 'anchor_pin': '2', 'realm': 'alfheim'},
        ]}}})
    save = {'progression_tables': {'table2_stage': {'0x22': 2, '0x33': 2}}}
    q = favors.read_favors(save, 'ru')[0]
    assert q['guide']['text'] == 'Найти печать'
    assert q['objectives'][0]['id'] == 'Goal_Test'
    assert q['step_ids'] == ['Goal_Test']
    assert q['points'] == [{'step': 'Goal_Test', 'realm': 'midgard', 'lat': .71, 'lng': -.69,
                            'label': 'У тайника', 'anchor_pin': '2', 'anchor_name': 'Synthetic cache'}]
    assert favors.read_favors(save, 'en')[0]['points'][0]['label'] == 'At cache'


def test_guides_scanner_exception_is_narrow():
    assert inspect_file('data/guides.json', b'{"version":1,"pins":{"1":{"en":"Our prose","description":"Our note"}}}') == []
    assert inspect_file('data/other.json', b'{"description":"Borrowed text"}')
    assert inspect_file('data/guides.json', ('{"en":"Q' + ':/private"}').encode())
    assert inspect_file('cache/guides.json', b'{}')


def test_chromium_guides_targets_and_proximity(guide_data, monkeypatch, tmp_path):
    """Real HTTP payload + Chromium; no game, remote pages or network assets."""
    playwright = pytest.importorskip('playwright.sync_api')
    import server
    from PIL import Image
    (guide_data / 'ru_descriptions.json').write_text(json.dumps({'1': {'ru': 'Перевод описания'}}), encoding='utf-8')
    write_guides(guide_data, {'version': 1, 'pins': {'1': {
        'en': '**Break the seals**\n1. Look left\n\n2. Strike the second seal\n- Look up', 'ru': '**Разбейте печати**',
        'sources': ['https://example.invalid/guide', 'javascript:alert(1)']},
        '2': {'en': '**Only a guide**', 'ru': '**Только гайд**'}},
        'favors': {'Favor_Test': {'en': '**Find the cache**', 'ru': '**Найдите тайник**', 'points': [
            {'step': 'Goal_Test', 'anchor_pin': '2', 'realm': 'midgard', 'label_en': 'Reach the cache', 'label_ru': 'К тайнику'},
            {'step': None, 'anchor_pin': '2', 'realm': 'midgard', 'label_en': 'Inspect the cache', 'label_ru': 'Осмотрите тайник'},
            {'step': None, 'anchor_pin': '3', 'realm': 'alfheim', 'label_en': 'Other realm', 'label_ru': 'Другой мир'}]}}})
    (pins.PINS / 'alfheim.json').write_text(json.dumps({'locations': [
        {'id': 3, 'title': 'Other cache', 'category_id': 7107, 'latitude': '.8', 'longitude': '-.8'}]}))
    runtime = {'available': False}
    stages = {'0x11': 0, '0x22': 2, '0x33': 2}
    app = server.App(save_reader=lambda: {'progression_tables': {'table2_stage': dict(stages)}},
                     telemetry_reader=lambda **kwargs: dict(runtime))
    httpd = server.make_server(port=0, app=app, offline=True)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    output = Path(os.environ.get('GOWR_UI_ARTIFACTS', str(tmp_path / 'screenshots')))
    output.mkdir(parents=True, exist_ok=True)
    tile = io.BytesIO()
    Image.new('RGB', (256, 256), (28, 41, 49)).save(tile, 'PNG')
    try:
        with playwright.sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
            except playwright.Error as exc:
                pytest.skip('Chromium unavailable: ' + str(exc).splitlines()[0])
            context = browser.new_context(viewport={'width': 1920, 'height': 1080}, locale='en-US')
            context.route('**/gow-tiles/**', lambda route: route.fulfill(content_type='image/png', body=tile.getvalue()))
            page = context.new_page()
            errors = []
            page.on('pageerror', lambda err: errors.append(str(err)))
            url = f'http://127.0.0.1:{httpd.server_port}/'
            page.goto(url)
            page.wait_for_selector('.leaflet-marker-icon')
            assert page.locator('.gow-fs-guide-toast:visible').count() == 0
            page.locator('.leaflet-marker-icon').first.click()
            page.wait_for_selector('.gow-fs-guide')
            assert page.locator('.gow-fs-guide h3').inner_text() == 'How to solve'
            assert page.locator('.gow-fs-guide strong').inner_text() == 'Break the seals'
            assert page.locator('.gow-fs-guide ol li').first.inner_text() == 'Look left'
            assert page.locator('.gow-fs-guide ol').nth(1).get_attribute('start') == '2'
            sources = page.locator('.gow-fs-guide details')
            assert sources.get_attribute('open') is None
            assert sources.locator('a').count() == 1
            assert sources.locator('a').get_attribute('rel') == 'noopener'
            assert sources.locator('a').get_attribute('target') == '_blank'
            page.locator('[data-desc-lang="ru"]').click()
            assert page.locator('#gowFsDrawerDesc').inner_text() == 'Перевод описания'
            assert page.locator('.gow-fs-guide strong').inner_text() == 'Break the seals'
            page.screenshot(path=str(output / 'guide-card-en.png'), animations='disabled')
            # A live marker alone is insufficient without a metres scale.
            runtime.update(available=True, process_running=True, radar={
                'realm_key': 'midgard', 'map_lat': .7, 'map_lng': -.7,
                'projection_confidence': 'proven'})
            page.reload()
            page.wait_for_selector('.gow-kratos')
            assert page.locator('.gow-fs-guide-toast:visible').count() == 0
            runtime['radar']['map_scale_per_metre'] = .00001
            page.reload()
            page.wait_for_selector('.gow-fs-guide-toast:visible')
            runtime['radar']['map_lat'] = .70035
            page.wait_for_function("document.getElementById('gowFsStatusText').textContent.includes('35')")
            assert page.locator('.gow-fs-guide-toast').is_visible()
            runtime['radar']['map_lat'] = .7
            page.locator('.gow-fs-guide-toast [data-guide-open]').click()
            assert page.locator('.gow-fs-guide').is_visible()
            page.locator('.gow-fs-guide-toast [data-guide-dismiss]').click()
            # Coordinate jitter must not reshow the dismissed pin.
            runtime['radar']['map_lat'] = .70029
            page.wait_for_function("document.getElementById('gowFsStatusText').textContent.includes('29')")
            assert page.locator('.gow-fs-guide-toast:visible').count() == 0
            page.locator('#gowFsDrawerClose').click()
            page.locator('#gowFsModeBtn').click()
            page.locator('[data-mode="favors"]').click()
            assert page.locator('.gow-favor-target').count() == 2
            assert page.locator('[data-guide-point="0"]').inner_text() == 'Reach the cache'
            assert page.locator('[data-current-point]').inner_text() == 'Guide point'
            # Same coordinates have different screen offsets.
            transforms = page.locator('.gow-favor-target').evaluate_all('(xs) => xs.map(x => [x.style.left, x.style.top].join())')
            assert transforms[0] != transforms[1]
            page.locator('[data-favor-guide]').click()
            assert page.locator('.gow-fs-favor-guide strong').inner_text() == 'Find the cache'
            # With no matching current objective, count all available guide points.
            stages['0x33'] = 4
            page.wait_for_function("document.querySelector('.gow-fs-favor-help').textContent.includes('Guide points: 3')")
            stages['0x33'] = 2
            page.wait_for_selector('[data-current-point]')
            runtime['radar'].update(map_lat=.71, map_lng=-.69)
            page.wait_for_selector('.gow-fs-guide-toast [data-guide-open]')
            page.wait_for_function("document.querySelector('.gow-fs-guide-toast').textContent.includes('Synthetic favor')")
            # A guide hot-reload can reorder points while this toast stays open.
            guides = json.loads((guide_data / 'guides.json').read_text(encoding='utf-8'))
            points = guides['favors']['Favor_Test']['points']
            guides['favors']['Favor_Test']['points'] = [points[2], points[0], points[1]]
            write_guides(guide_data, guides)
            page.wait_for_function("document.querySelector('[data-guide-point=\"0\"]').textContent.includes('Other realm')")
            page.screenshot(path=str(output / 'favors-target-toast-en.png'), animations='disabled')
            page.locator('.gow-fs-guide-toast [data-guide-open]').click()
            assert page.locator('#gowFsWorldName').text_content() == 'Midgard'
            assert page.locator('.gow-fs-favor-guide').is_visible()
            # Crossing 45 m hides the toast; a shown point is not repeated.
            runtime['radar']['map_lat'] = .7105
            page.wait_for_function("!document.querySelector('.gow-fs-guide-toast') || document.querySelector('.gow-fs-guide-toast').hidden")
            runtime['radar']['map_lat'] = .71
            # Cross-realm point navigation and pending focus after refresh.
            page.locator('[data-guide-point="0"]').click()
            page.wait_for_function("document.getElementById('gowFsWorldName').textContent === 'Alfheim'")
            page.wait_for_selector('.gow-favor-target')
            assert page.locator('.gow-favor-target').count() == 1
            # Completed favors lose targets and panel guide controls.
            stages['0x22'] = 4
            page.wait_for_function("document.querySelectorAll('.gow-favor-target').length === 0")
            assert page.locator('[data-favor-guide]').count() == 0
            stages['0x22'] = 0
            page.wait_for_function("document.querySelectorAll('.gow-favor-target').length === 0")
            # Language switches preserve interface-specific guide language.
            stages['0x22'] = 2
            runtime.clear(); runtime.update(available=False)
            page.locator('#gowLanguage').click()
            page.wait_for_function("document.documentElement.lang === 'ru'")
            page.wait_for_selector('[data-favor-guide]')
            page.locator('[data-favor-guide]').click()
            assert page.locator('.gow-fs-favor-guide strong').inner_text() == 'Найдите тайник'
            # A fresh tab session captures the RU favor target and toast too.
            runtime.update(available=True, process_running=True, radar={'realm_key': 'alfheim',
                'map_lat': .8, 'map_lng': -.8, 'map_scale_per_metre': .00001, 'projection_confidence': 'proven'})
            page.evaluate("sessionStorage.removeItem('gowGuideSeen')")
            page.reload()
            page.wait_for_selector('.gow-fs-guide-toast:visible')
            page.locator('[data-favor-guide]').click()
            page.screenshot(path=str(output / 'favors-target-toast-ru.png'), animations='disabled')
            runtime.clear(); runtime.update(available=False, process_running=True)
            page.wait_for_function("!document.querySelector('.gow-kratos') && document.querySelector('.gow-fs-guide-toast').hidden")
            # Guide remains accessible when no realm, anchor, or legacy pin is known.
            quest = favors._base_catalog()['favors'][0]
            quest['realm'] = None
            guides = json.loads((guide_data / 'guides.json').read_text(encoding='utf-8'))
            guides['favors']['Favor_Test'] = {'ru': '**Без якоря**'}
            write_guides(guide_data, guides)
            page.wait_for_function("document.querySelector('.gow-fs-favor-guide') && document.querySelector('.gow-fs-favor-guide').textContent.includes('Без якоря')")
            page.locator('#gowFsModeBtn').click()
            page.locator('[data-mode="remaining"]').click()
            page.locator('[data-realm="midgard"]').first.click()
            page.wait_for_selector('.leaflet-marker-icon[aria-label="Synthetic cache"]')
            page.locator('.leaflet-marker-icon[aria-label="Synthetic cache"]').click()
            assert page.locator('.gow-fs-guide h3').inner_text() == 'Как открыть'
            assert page.locator('.gow-fs-guide strong').inner_text() == 'Только гайд'
            assert page.locator('.gow-fs-drawer-desc.is-empty').count() == 0
            page.screenshot(path=str(output / 'guide-card-ru.png'), animations='disabled')
            page.locator('#gowFsDrawerClose').click()
            # Collected and unknown guided pins must never produce a hint.
            runtime.update(available=True, process_running=True, radar={'realm_key': 'midgard',
                'map_lat': .7, 'map_lng': -.7, 'map_scale_per_metre': .00001, 'projection_confidence': 'proven'})
            for stage in (4, None):
                if stage is None:
                    stages.pop('0x11', None)
                    (guide_data / 'pin_mapping.json').write_text('{}')
                    pins._load_pin_mapping.cache_clear()
                else:
                    stages['0x11'] = stage
                page.evaluate("sessionStorage.removeItem('gowGuideSeen')")
                page.reload()
                page.wait_for_selector('.gow-kratos')
                assert page.locator('.gow-fs-guide-toast:visible').count() == 0
            page.set_viewport_size({'width': 390, 'height': 844})
            assert page.evaluate('document.documentElement.scrollWidth') == 390
            assert not errors, errors
            browser.close()
    finally:
        httpd.shutdown(); httpd.server_close(); thread.join()
