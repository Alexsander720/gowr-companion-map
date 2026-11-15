"""Optional Chromium smoke test with synthetic pins and locally generated tiles."""
import io
import json
import threading
import pytest
import gow_pins
import server


def test_chromium_synthetic_map_i18n_and_interaction(synthetic_map,tmp_path):
    playwright=pytest.importorskip('playwright.sync_api')
    synthetic_map['regions']=[{'id':7,'title':'Synthetic region'}]
    for loc in synthetic_map['locations']: loc['region_id']=7
    from PIL import Image
    tile=io.BytesIO();Image.new('RGB',(256,256),(22,36,44)).save(tile,'PNG')
    (gow_pins.PINS/'midgard.json').write_text(json.dumps(synthetic_map))
    app=server.App(save_reader=lambda:{},telemetry_reader=lambda **kwargs:{'available':False})
    httpd=server.make_server(port=0,app=app,offline=True)
    thread=threading.Thread(target=httpd.serve_forever,daemon=True);thread.start()
    try:
        with playwright.sync_playwright() as p:
            try:browser=p.chromium.launch(headless=True)
            except playwright.Error as exc:pytest.skip('Chromium unavailable: '+str(exc).splitlines()[0])
            context=browser.new_context(viewport={'width':1920,'height':1080},locale='en-US')
            context.route('**/gow-tiles/**',lambda route:route.fulfill(status=200,content_type='image/png',body=tile.getvalue()))
            page=context.new_page();errors=[];page.on('pageerror',lambda err:errors.append(str(err)))
            page.goto(f'http://127.0.0.1:{httpd.server_port}/')
            page.wait_for_selector('.leaflet-marker-icon')
            assert page.locator('#gowFsWorldName').text_content() == 'Midgard'
            assert page.locator('.gow-kratos').count() == 0
            page.locator('#gowFsRegionSelect').select_option('Synthetic region')
            page.locator('#gowFsSearch').focus();page.keyboard.press('ArrowDown')
            assert page.locator('#gowFsSearch').evaluate('(el) => el === document.activeElement')
            page.evaluate('document.activeElement.blur()');page.keyboard.press('ArrowRight')
            assert page.evaluate("document.activeElement.getAttribute('role')") == 'button'
            page.locator('.leaflet-marker-icon').first.click()
            assert 'Synthetic' in page.locator('#gowFsDrawerTitle').inner_text()
            before=page.evaluate('window.gowLeafletMap.getZoom()')
            page.locator('#gowFsZoomIn').click()
            assert page.evaluate('window.gowLeafletMap.getZoom()') > before
            page.locator('#gowLanguage').click();page.wait_for_load_state('load')
            page.wait_for_function("document.documentElement.lang === 'ru'")
            page.wait_for_function("document.getElementById('gowFsWorldName').textContent.length > 1")
            assert page.locator('#gowFsWorldName').text_content() == 'Мидгард'
            page.reload();page.wait_for_function("document.documentElement.lang === 'ru'")
            page.set_viewport_size({'width':390,'height':844})
            assert page.evaluate('document.documentElement.scrollWidth') == 390
            assert not errors, errors
            browser.close()
    finally:
        httpd.shutdown();httpd.server_close();thread.join()
