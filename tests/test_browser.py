"""Chromium smoke + WebGL2 3D terrain & 0-drift multitouch verification."""
import io
import json
import threading
import numpy as np
import pytest
import gow_codex
import gow_game_tiles
import gow_pins
import server


def test_chromium_synthetic_map_i18n_and_interaction(synthetic_map, monkeypatch, tmp_path):
    playwright = pytest.importorskip('playwright.sync_api')
    from tests.test_codex import _synthetic_catalog, _synthetic_save, _synthetic_strings
    synthetic_map['regions'] = [{'id': 7, 'title': 'Synthetic region'}]
    for loc in synthetic_map['locations']:
        loc['region_id'] = 7
    from PIL import Image
    from tools.gow_game_map import encode_h16_png

    tile = io.BytesIO()
    Image.new('RGB', (256, 256), (22, 36, 44)).save(tile, 'PNG')
    maps_dir = tmp_path / 'maps'
    maps_dir.mkdir()
    h = np.linspace(0.0, 1.0, 64 * 64, dtype=np.float32).reshape(64, 64)
    (maps_dir / 'midgard_h16.png').write_bytes(encode_h16_png(h))
    monkeypatch.setattr(gow_game_tiles, 'MAPS_DIR', maps_dir)

    cats_map = gow_pins._load_categories_map()
    gw_cid = int(next(k for k, v in cats_map.items() if v == 'mystic_gateway'))
    tmap_cid = int(next(k for k, v in cats_map.items() if v == 'treasure_map'))
    tdig_cid = int(next(k for k, v in cats_map.items() if v == 'buried_treasure'))
    synthetic_map['locations'].extend([
        {'id': 60, 'category_id': gw_cid, 'title': 'Lake Gateway', 'region_id': 7, 'latitude': '0.68', 'longitude': '-0.68', 'description': '', 'media': []},
        {'id': 61, 'category_id': tmap_cid, 'title': 'Forgotten Cache Treasure Map', 'region_id': 7, 'latitude': '0.73', 'longitude': '-0.73', 'description': '', 'media': []},
    ])
    (gow_pins.PINS / 'midgard.json').write_text(json.dumps(synthetic_map))
    (gow_pins.PINS / 'alfheim.json').write_text(json.dumps({
        'maps': [{'id': 475, 'slug': 'alfheim'}], 'map': {'id': 475, 'slug': 'alfheim'},
        'regions': [{'id': 9, 'title': 'Alfheim desert'}],
        'locations': [
            {'id': 70, 'category_id': gw_cid, 'title': 'Desert Gateway', 'region_id': 9, 'latitude': '0.72', 'longitude': '-0.72', 'description': '', 'media': []},
            {'id': 71, 'category_id': tdig_cid, 'title': 'Forgotten Cache', 'region_id': 9, 'latitude': '0.76', 'longitude': '-0.76', 'description': '', 'media': []},
        ],
    }))
    cat = _synthetic_catalog()
    syn_save = _synthetic_save()
    def _build_linked_codex(save, lang):
        cx = gow_codex.build_codex(
            save, lang, catalog=cat,
            strings_primary=_synthetic_strings(lang),
            strings_fallback=_synthetic_strings('en'),
        )
        return gow_codex.attach_map_links(cx, save, lang, ('midgard', 'alfheim'))
    app = server.App(
        save_reader=lambda: syn_save,
        telemetry_reader=lambda **kwargs: {'available': False},
        codex_builder=_build_linked_codex,
    )
    httpd = server.make_server(port=0, app=app, offline=True)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        with playwright.sync_playwright() as p:
            try:
                browser = p.chromium.launch(
                    headless=True,
                    args=['--use-gl=angle', '--use-angle=d3d11', '--ignore-gpu-blocklist'],
                )
            except playwright.Error as exc:
                pytest.skip('Chromium unavailable: ' + str(exc).splitlines()[0])
            context = browser.new_context(viewport={'width': 1920, 'height': 1080}, locale='en-US')
            context.route('**/gow-tiles/**', lambda route: route.fulfill(status=200, content_type='image/png', body=tile.getvalue()))
            page = context.new_page()
            errors = []
            page.on('console', lambda m: errors.append(f'CONSOLE {m.type}: {m.text}') if m.type == 'error' else None)
            page.on('pageerror', lambda err: errors.append(str(err)))

            page.goto(f'http://127.0.0.1:{httpd.server_port}/')
            page.wait_for_selector('.leaflet-marker-icon')
            assert page.locator('#gowFsWorldName').text_content() == 'Midgard'
            assert page.locator('.gow-kratos').count() == 0
            assert page.evaluate('document.documentElement.scrollWidth') == 1920

            # 3D mode, rotate, compass & nearest beacon UX
            has_gl = page.evaluate('Boolean(window.gowLeafletMap && window.gowLeafletMap.hasWebGL2)')
            if has_gl:
                page.wait_for_function('window.gowLeafletMap.hasHeightmap === true', timeout=5000)
                assert page.evaluate('window.gowLeafletMap.mode3D') is True
                page.locator('#gowFs3D').click()
                page.wait_for_timeout(150)
                assert page.evaluate('window.gowLeafletMap.mode3D') is False
                page.locator('#gowFs3D').click()
                page.wait_for_timeout(150)
                assert page.evaluate('window.gowLeafletMap.mode3D') is True

                # 0-drift Google Maps multitouch verification (pan, pinch+twist, 2-finger tilt)
                touch = page.evaluate('''() => {
                    const el = document.getElementById('gowInteractiveMap');
                    const m = window.gowLeafletMap;
                    m.setView([0.70, -0.70], 11, { animate: false });
                    m.pitchDeg = 42; m.yawDeg = 45; m._apply();
                    const b1 = m.unprojectGround(960, 540);
                    el.dispatchEvent(new PointerEvent('pointerdown', { pointerId: 1, clientX: 960, clientY: 540, button: 0, bubbles: true }));
                    el.dispatchEvent(new PointerEvent('pointermove', { pointerId: 1, clientX: 1060, clientY: 600, button: 0, bubbles: true }));
                    const a1 = m.unprojectGround(1060, 600);
                    el.dispatchEvent(new PointerEvent('pointerup', { pointerId: 1, clientX: 1060, clientY: 600, button: 0, bubbles: true }));
                    const panErr = Math.hypot(b1[0] - a1[0], b1[1] - a1[1]);

                    m.setView([0.70, -0.70], 11, { animate: false });
                    m.pitchDeg = 42; m.yawDeg = 0; m._apply();
                    const midBefore = m.unprojectGround(960, 540);
                    el.dispatchEvent(new PointerEvent('pointerdown', { pointerId: 10, clientX: 860, clientY: 540, bubbles: true }));
                    el.dispatchEvent(new PointerEvent('pointerdown', { pointerId: 11, clientX: 1060, clientY: 540, bubbles: true }));
                    for (const deg of [10, 25]) {
                        const rad = deg * Math.PI / 180;
                        el.dispatchEvent(new PointerEvent('pointermove', { pointerId: 10, clientX: 960 - Math.cos(rad) * 115, clientY: 540 - Math.sin(rad) * 115, bubbles: true }));
                        el.dispatchEvent(new PointerEvent('pointermove', { pointerId: 11, clientX: 960 + Math.cos(rad) * 115, clientY: 540 + Math.sin(rad) * 115, bubbles: true }));
                    }
                    const midAfter = m.unprojectGround(960, 540);
                    const yawAfterTwist = m.yawDeg;
                    el.dispatchEvent(new PointerEvent('pointerup', { pointerId: 10, clientX: 850, clientY: 500, bubbles: true }));
                    el.dispatchEvent(new PointerEvent('pointerup', { pointerId: 11, clientX: 1070, clientY: 580, bubbles: true }));
                    const pivotErr = Math.hypot(midBefore[0] - midAfter[0], midBefore[1] - midAfter[1]);

                    m.pitchDeg = 28; m._apply();
                    el.dispatchEvent(new PointerEvent('pointerdown', { pointerId: 20, clientX: 880, clientY: 540, bubbles: true }));
                    el.dispatchEvent(new PointerEvent('pointerdown', { pointerId: 21, clientX: 1040, clientY: 540, bubbles: true }));
                    el.dispatchEvent(new PointerEvent('pointermove', { pointerId: 20, clientX: 880, clientY: 460, bubbles: true }));
                    el.dispatchEvent(new PointerEvent('pointermove', { pointerId: 21, clientX: 1040, clientY: 460, bubbles: true }));
                    const pitchAfterTilt = m.pitchDeg;
                    el.dispatchEvent(new PointerEvent('pointerup', { pointerId: 20, clientX: 880, clientY: 460, bubbles: true }));
                    el.dispatchEvent(new PointerEvent('pointerup', { pointerId: 21, clientX: 1040, clientY: 460, bubbles: true }));
                    m.resetNorth();
                    return { panErr, pivotErr, yawAfterTwist, pitchAfterTilt };
                }''')
                assert touch['panErr'] < 1.0, touch
                assert touch['pivotErr'] < 1.0, touch
                assert touch['yawAfterTwist'] > 10.0, touch
                assert touch['pitchAfterTilt'] > 40.0, touch

            # Nearest collectible button, 3D clearing route, weather toggle & universal drawer routing
            assert page.locator('#gowFsWeather').is_visible()
            if has_gl:
                assert page.evaluate('window.gowLeafletMap.weatherEnabled') is True
                page.locator('#gowFsWeather').click()
                assert page.evaluate('window.gowLeafletMap.weatherEnabled') is False
                page.locator('#gowFsWeather').click()
                assert page.evaluate('window.gowLeafletMap.weatherEnabled') is True

            page.locator('#gowFsRoute').click()
            page.wait_for_selector('#gowFsRoutePill:not([hidden])')
            assert page.evaluate('window.gowLeafletMap.routePoints.length') >= 2
            page.locator('#gowFsRouteClear').click()
            assert not page.locator('#gowFsRoutePill').is_visible()
            assert page.locator('#gowFsWake').is_visible()
            page.locator('#gowFsWake').click()

            page.locator('#gowFsNearest').click()
            page.wait_for_selector('#gowFsRightDrawer.open')
            assert page.locator('#gowFsBeaconPill').is_visible()
            # Plot single-target 3D route from pin drawer (uses nearest Mystic Gateway offline)
            page.locator('#gowFsRouteHere').click()
            page.wait_for_selector('#gowFsRoutePill:not([hidden])')
            assert 'Lake Gateway' in page.locator('#gowFsRoutePill').inner_text()
            assert page.evaluate('window.gowLeafletMap.routePoints.length') == 2
            page.locator('#gowFsRouteClear').click()
            page.locator('#gowFsDrawerClose').click()
            assert not page.locator('#gowFsRightDrawer.open').count()
            page.locator('#gowFsNearest').click()
            page.wait_for_selector('#gowFsRightDrawer.open')
            page.locator('#gowFsDrawerClose').click()
            page.locator('#gowFsBeaconPill').click()
            page.wait_for_selector('#gowFsRightDrawer.open')
            page.locator('#gowFsBeaconClear').click()
            assert not page.locator('#gowFsBeaconPill').is_visible()
            page.locator('#gowFsDrawerClose').click()

            # Open Book Codex (5 tabs: Bestiary, Lore, Treasures, Skills, Hero) + Dark view toggle + Cross-realm Treasure routing
            page.keyboard.press('k')
            page.wait_for_selector('#gowFsCodexModal.open')
            page.wait_for_selector('#gowFsCodexBody.is-book-mode')
            page.wait_for_selector('.gow-cx-item')
            page.wait_for_selector('#gowCodexLivePill.is-live', timeout=4000)
            assert 'draugr' in page.locator('#gowCxDetail').inner_text().lower()
            # Locked Troll is spoiler-hidden until revealed
            page.locator('[data-cx-select="Bestiary_Troll_Entry"]').click()
            assert '???' in page.locator('#gowCxDetail').inner_text()
            page.locator('[data-cx-reveal="Bestiary_Troll_Entry"]').click()
            assert 'forest troll' in page.locator('#gowCxDetail').inner_text().lower()
            # Toggle Book <-> Dark view and back
            page.locator('[data-cx-book-mode="1"]').click()
            assert not page.locator('#gowFsCodexBody.is-book-mode').count()
            page.locator('[data-cx-book-mode="1"]').click()
            page.wait_for_selector('#gowFsCodexBody.is-book-mode')
            # Switch through Lore, Skills & Labors, Hero & Materials, and Treasures
            page.locator('[data-cx-tab="lore"]').click()
            assert 'ally' in page.locator('#gowFsCodexBody').inner_text().lower()
            page.locator('[data-cx-tab="skills"]').click()
            assert 'Draugr Bane' in page.locator('#gowFsCodexBody').inner_text()
            page.locator('[data-cx-tab="hero"]').click()
            assert 'Leviathan Axe' in page.locator('#gowFsCodexBody').inner_text()
            page.locator('[data-cx-tab="treasures"]').click()
            page.wait_for_selector('#gowFsCodexBody.is-book-mode')
            assert 'forgotten cache' in page.locator('#gowCxDetail').inner_text().lower()
            # Click "Route to buried treasure" -> closes book, switches realm to Alfheim & plots 3D route from Desert Gateway!
            page.locator('[data-cx-route-pin="71"]').click()
            assert not page.locator('#gowFsCodexModal.open').count()
            page.wait_for_function("document.getElementById('gowFsWorldName').textContent === 'Alfheim'")
            page.wait_for_selector('#gowFsRoutePill:not([hidden])')
            assert 'Desert Gateway' in page.locator('#gowFsRoutePill').inner_text()
            assert page.evaluate('window.gowLeafletMap.routePoints.length') == 2
            page.locator('#gowFsRouteClear').click()
            page.locator('#gowFsDrawerClose').click()
            # Switch back to Midgard for remaining map checks
            page.locator('[data-realm="midgard"]').click()
            page.wait_for_function("document.getElementById('gowFsWorldName').textContent === 'Midgard'")
            page.wait_for_selector('.leaflet-marker-icon')

            page.locator('#gowFsSearch').fill('Synthetic')
            assert page.locator('#gowFsSearchClear').is_visible()
            page.locator('#gowFsSearchClear').click()
            assert page.locator('#gowFsSearch').input_value() == ''
            page.locator('.leaflet-marker-icon').first.hover()
            assert page.locator('.leaflet-tooltip.gow-fs-tip').is_visible()

            page.locator('#gowFsRegionSelect').select_option('Synthetic region')
            page.locator('#gowFsSearch').focus()
            page.keyboard.press('ArrowDown')
            assert page.locator('#gowFsSearch').evaluate('(el) => el === document.activeElement')
            page.evaluate('document.activeElement.blur()')
            page.keyboard.press('ArrowRight')
            assert page.evaluate("document.activeElement.getAttribute('role')") == 'button'
            page.locator('.leaflet-marker-icon').first.click()
            assert 'Synthetic' in page.locator('#gowFsDrawerTitle').inner_text()
            before = page.evaluate('window.gowLeafletMap.getZoom()')
            page.locator('#gowFsZoomIn').click()
            assert page.evaluate('window.gowLeafletMap.getZoom()') > before
            page.locator('#gowLanguage').click()
            page.wait_for_load_state('load')
            page.wait_for_function("document.documentElement.lang === 'ru'")
            page.wait_for_function("document.getElementById('gowFsWorldName').textContent.length > 1")
            assert page.locator('#gowFsWorldName').text_content() == 'Мидгард'
            page.reload()
            page.wait_for_function("document.documentElement.lang === 'ru'")
            page.set_viewport_size({'width': 390, 'height': 844})
            assert page.evaluate('document.documentElement.scrollWidth') == 390
            assert not errors, errors
            browser.close()
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join()
