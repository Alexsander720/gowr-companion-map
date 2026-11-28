"""Offline synthetic tests for Codex (Bestiary, Lore, Skills, Hero) and real-time SSE stream."""
from __future__ import annotations

import http.client
import json
import threading
import time

import pytest

import gow_codex
import gow_pins
import server


def _synthetic_catalog():
    return {
        'bestiary': [
            {
                'id': 'Bestiary_Draugr_Entry',
                'hash': '0x0001',
                'name_sid': 101,
                'desc_sid': 102,
                'sub_sid': 201,
                'is_valhalla': False,
                'icon_key': 'draugr_01',
                'family': 'draugr',
                'tips': [
                    {'id': 'Bestiary_Draugr_Tip01', 'hash': '0x0011', 'name_sid': 103, 'desc_sid': 0},
                    {'id': 'Bestiary_Draugr_Tip02', 'hash': '0x0012', 'name_sid': 104, 'desc_sid': 0},
                ],
            },
            {
                'id': 'Bestiary_Troll_Entry',
                'hash': '0x0002',
                'name_sid': 105,
                'desc_sid': 106,
                'sub_sid': 202,
                'is_valhalla': False,
                'icon_key': 'troll_01',
                'family': 'troll',
                'tips': [],
            },
            {
                'id': 'Bestiary_Val_Entry_Val',
                'hash': '0x0003',
                'name_sid': 107,
                'desc_sid': 108,
                'sub_sid': 201,
                'is_valhalla': True,
                'icon_key': None,
                'family': None,
                'tips': [],
            },
        ],
        'lore': [
            {
                'id': 'Lore_People_Ally',
                'hash': '0x0101',
                'name_sid': 301,
                'desc_sid': 302,
                'sub_sid': 203,
                'is_valhalla': False,
                'icon_key': 'ally_01',
                'updates': [
                    {'id': 'Lore_People_Ally_Up1', 'hash': '0x0111', 'name_sid': 0, 'desc_sid': 303},
                ],
            },
            {
                'id': 'Lore_Temp_Entry',
                'hash': '0x0102',
                'name_sid': 304,
                'desc_sid': 305,
                'sub_sid': 203,
                'is_valhalla': False,
                'icon_key': None,
                'updates': [],
            },
        ],
        'treasures': [
            {
                'id': 'TreasureMap_Synth_Parent',
                'hash': '0x0601',
                'step_hash': '0x0602',
                'name_sid': 501,
                'desc_sid': 502,
                'icon_key': 'treasuremap_synth_parent',
            },
        ],
        'skills': [
            {
                'id': 'Labor_Skill_AxeThrowLight',
                'hash': '0x0201',
                'weapon': 'axe',
                'label': 'Throw Light',
                'tiers': [
                    {'tier': 'bronze', 'hash': '0x0211', 'name_sid': 401, 'counter_hash': '0x0301', 'total': 25},
                    {'tier': 'silver', 'hash': '0x0212', 'name_sid': 402, 'counter_hash': '0x0301', 'total': 50},
                    {'tier': 'gold', 'hash': '0x0213', 'name_sid': 403, 'counter_hash': '0x0301', 'total': 100},
                ],
            },
        ],
        'labors': [
            {
                'id': 'Labor_DraugrKills',
                'hash': '0x0401',
                'name_sid': 404,
                'desc_sid': 0,
                'sub_sid': 204,
                'is_ngp': False,
                'is_valhalla': False,
                'tiers': [
                    {'id': 'Labor_DraugrKills_Gold', 'hash': '0x0411', 'name_sid': 403, 'desc_sid': 405, 'counter_hash': '0x0501', 'total': 20},
                ],
            },
        ],
        'kill_counters': {'draugr': '0x0501'},
        'icon_to_tx': {'draugr_01': 'TX_draugr_01_0000000000000001'},
    }


def _synthetic_strings(lang='en'):
    if lang == 'ru':
        return {
            101: 'Драугр', 102: 'Описание [style=Highlight]драугра[/style]\\n\\pАбзац 2.',
            103: 'Бей щитом [Icons:Shield]', 104: 'Уклоняйся от огня',
            105: 'Лесной тролль', 106: 'Каменный великан',
            107: 'Эхо Вальхаллы', 108: 'Испытание DLC',
            201: 'Монстры', 202: 'Звери', 203: 'Друзья', 204: 'Убийства',
            301: 'Союзник', 302: 'История союзника', 303: 'Продолжение истории',
            304: '*TEMP* Черновик', 305: '*TEMP* текст',
            401: 'Бронза', 402: 'Серебро', 403: 'Золото',
            404: 'Гроза драугров', 405: 'Побеждено: %d/%d',
            501: 'Забытый тайник', 502: 'Ищи у замёрзшего берега.',
        }
    return {
        101: 'Draugr', 102: 'Synthetic [style=Highlight]draugr[/style]\\n\\pParagraph 2.',
        103: 'Use shield [Icons:Shield]', 104: 'Dodge fire attacks',
        105: 'Forest Troll', 106: 'Stone giant',
        107: 'Valhalla Echo', 108: 'DLC foe',
        201: 'Monsters', 202: 'Beasts', 203: 'Friends', 204: 'Kills',
        301: 'Ally', 302: 'Ally story', 303: 'Story continuation',
        304: '*TEMP* Draft', 305: '*TEMP* body',
        401: 'Bronze', 402: 'Silver', 403: 'Gold',
        404: 'Draugr Bane', 405: 'Defeated: %d/%d',
        501: 'Forgotten Cache', 502: 'Look by the frozen shore.',
    }


def _synthetic_save(troll_unlocked=False, tip2_unlocked=False, draugr_kills=19, treasure_stage=2):
    t2 = {'0x0001': 2, '0x0011': 2, '0x0101': 2, '0x0211': 4}
    if treasure_stage is not None:
        t2['0x0601'] = treasure_stage
    if troll_unlocked:
        t2['0x0002'] = 2
    if tip2_unlocked:
        t2['0x0012'] = 2
    return {
        'ok': True,
        'realm': 'midgard',
        'place': 'Midgard',
        'objective': 'Synthetic objective',
        'play_time': '41 ч 45 мин 55 с',
        'difficulty_id': 2,
        'power_level': 4,
        'gear_level': 5,
        'gear_levels': [4, 5, 3],
        'loadout': {
            'weapons': {'axe': {'name_guess': 'Топор Левиафан', 'level': 5}},
            'armor': {'chest': {'name_guess': 'Кираса Лунды (нагрудник)', 'level': 4}},
            'shields': {'shield': {'name_guess': 'Щит', 'level': 3}},
        },
        'amulet': {'sockets_unlocked': 4, 'sockets_total': 9, 'jewels_found': 2},
        'wallet': {'wallet_hacksilver': 42000, 'divine_ashes': 150, 'kratos_xp': 9500, 'skills_count': 18, 'frozen_flame': 1},
        'collectibles': {
            'ravens': {'collected': 12, 'total': 48},
            'nornir_progress': {'nornir_chests_opened': 7},
            'lindwyrms': {'captured': 2, 'total': 6},
        },
        'progression_tables': {
            'table2_stage': t2,
            'table1_int': {'0x0301': 46, '0x0501': draugr_kills},
            'hero_items': {'0x2d004f87802835e2': 250},
        },
    }


def test_clean_game_text_strips_markup():
    raw = '[[NOTE]] Hello [style=Gold]World[/style]\\n\\p[i]Italic[/i] [Icons:L1Button] [TriangleButton]'
    out = gow_codex.clean_game_text(raw)
    assert '[[NOTE]]' not in out
    assert '[Icons:' not in out
    assert '[TriangleButton]' not in out
    assert '**World**' in out
    assert '_Italic_' in out
    assert '\n\n' in out


def test_build_codex_filters_temp_and_computes_progress_and_diff():
    cat = _synthetic_catalog()
    save1 = _synthetic_save(troll_unlocked=False, tip2_unlocked=False, draugr_kills=19)
    en1 = gow_codex.build_codex(save1, 'en', catalog=cat, strings_primary=_synthetic_strings('en'), strings_fallback=_synthetic_strings('en'))
    ru1 = gow_codex.build_codex(save1, 'ru', catalog=cat, strings_primary=_synthetic_strings('ru'), strings_fallback=_synthetic_strings('en'))

    assert en1['game_data_available'] is True
    assert en1['summary']['bestiary_total'] == 3
    assert en1['summary']['bestiary_main_total'] == 2
    assert en1['summary']['bestiary_main_unlocked'] == 1
    # *TEMP* lore entry must be excluded
    assert len(en1['lore']) == 1 and en1['lore'][0]['name'] == 'Ally'
    assert ru1['lore'][0]['name'] == 'Союзник'
    assert en1['bestiary'][0]['family_kills'] == 19
    assert en1['bestiary'][0]['tips_unlocked'] == 1
    assert en1['bestiary'][0]['icon'] == '/api/codex/icon/draugr_01.png'
    # Near completion should surface Draugr Bane (19/20, 1 left) and Axe Throw Light (46/50, 4 left)
    near_ids = [n['id'] for n in en1['near_completion']]
    assert 'Labor_DraugrKills' in near_ids and 'Labor_Skill_AxeThrowLight' in near_ids
    assert en1['near_completion'][0]['remaining'] == 1
    # Hero loadout in EN should translate known Russian weapon/armor names cleanly
    assert en1['hero']['loadout']['weapons'][0]['name'] == 'Leviathan Axe'
    assert en1['hero']['wallet']['hacksilver'] == 42000
    assert en1['hero']['wallet']['unused_flames'] == 1
    assert en1['summary']['treasures_total'] == 1
    assert en1['summary']['treasures_found'] == 1
    assert en1['summary']['treasures_dug'] == 0
    assert en1['treasures'][0]['status'] == 'active'
    assert ru1['treasures'][0]['name'] == 'Забытый тайник'

    # Simulate live save progression -> diff detects new bestiary, new tip & dug treasure
    save2 = _synthetic_save(troll_unlocked=True, tip2_unlocked=True, draugr_kills=20, treasure_stage=4)
    en2 = gow_codex.build_codex(save2, 'en', catalog=cat, strings_primary=_synthetic_strings('en'), strings_fallback=_synthetic_strings('en'))
    assert en2['summary']['treasures_dug'] == 1
    assert en2['treasures'][0]['status'] == 'dug'
    diff = gow_codex.compute_codex_diff(gow_codex.codex_snapshot(en1), gow_codex.codex_snapshot(en2))
    assert diff['has_changes'] is True
    assert [x['id'] for x in diff['new_bestiary']] == ['Bestiary_Troll_Entry']
    assert [x['entry_id'] for x in diff['new_tips']] == ['Bestiary_Draugr_Entry']
    assert [x['id'] for x in diff['new_treasures']] == ['TreasureMap_Synth_Parent']
    assert diff['new_treasures'][0]['status'] == 'dug'


def test_attach_map_links_uses_word_boundaries_and_valhalla_id_helper(synthetic_map):
    assert gow_codex._is_valhalla_id('Val_Lore_People_Mimir') is True
    assert gow_codex._is_valhalla_id('Bestiary_Thor_Entry_Val') is True
    assert gow_codex._is_valhalla_id('Lore_Enemies_Thor') is False

    # Add two boss pins ("Forest Troll", "Gna") and paired treasure scroll + dig pins
    cats_map = gow_pins._load_categories_map()
    boss_cid = int(next(k for k, v in cats_map.items() if v == 'boss'))
    tmap_cid = int(next(k for k, v in cats_map.items() if v == 'treasure_map'))
    tdig_cid = int(next(k for k, v in cats_map.items() if v == 'buried_treasure'))
    synthetic_map['locations'].extend([
        {'id': 50, 'category_id': boss_cid, 'title': 'Forest Troll', 'latitude': '0.72', 'longitude': '-0.72', 'description': '', 'media': []},
        {'id': 51, 'category_id': boss_cid, 'title': 'Gna', 'latitude': '0.73', 'longitude': '-0.73', 'description': '', 'media': []},
        {'id': 52, 'category_id': tmap_cid, 'title': 'Forgotten Cache Treasure Map', 'latitude': '0.74', 'longitude': '-0.74', 'description': '', 'media': []},
        {'id': 53, 'category_id': tdig_cid, 'title': 'Forgotten Cache', 'latitude': '0.75', 'longitude': '-0.75', 'description': '', 'media': []},
    ])
    (gow_pins.PINS / 'midgard.json').write_text(json.dumps(synthetic_map))
    codex = {
        'ok': True,
        'bestiary': [
            {'id': 'B1', 'name': 'Forest Troll', 'is_valhalla': False},
            {'id': 'B2', 'name': 'Ragnarok', 'is_valhalla': False},  # contains "gna" inside word — must NOT match Gna!
        ],
        'lore': [{'id': 'L1', 'name': 'Gna', 'is_valhalla': False}],
        'treasures': [{'id': 'T1', 'name': 'Forgotten Cache', 'status': 'active', 'unlocked': True, 'dug': False}],
        'hero': {'ok': True},
    }
    gow_codex.attach_map_links(codex, {}, 'en', ('midgard',))
    assert codex['bestiary'][0]['map_pins'][0]['id'] == '50'
    assert 'map_pins' not in codex['bestiary'][1]
    assert codex['lore'][0]['map_pins'][0]['id'] == '51'
    assert codex['treasures'][0]['map_pin']['id'] == '52'
    assert codex['treasures'][0]['dig_pin']['id'] == '53'
    assert any(rc['key'] == 'odins_raven' and rc['total'] == 1 for rc in codex['hero']['realm_categories'])


def test_codex_endpoints_icon_cache_and_sse_stream(synthetic_map, monkeypatch, tmp_path):
    (gow_pins.PINS / 'midgard.json').write_text(json.dumps(synthetic_map))
    cat = _synthetic_catalog()
    state = {'save': _synthetic_save(troll_unlocked=False, tip2_unlocked=False)}

    def builder(save, lang):
        return gow_codex.build_codex(
            save, lang, catalog=cat,
            strings_primary=_synthetic_strings(lang),
            strings_fallback=_synthetic_strings('en'),
        )

    icon_cache = tmp_path / 'codex_icons'
    icon_cache.mkdir()
    sample_png = b'\x89PNG\r\n\x1a\n' + b'\x00' * 32
    dark_png = b'\x89PNG\r\n\x1a\n' + b'\x01' * 32
    page_png = b'\x89PNG\r\n\x1a\n' + b'\x02' * 32
    (icon_cache / 'draugr_01.png').write_bytes(sample_png)
    (icon_cache / 'draugr_01_dark.png').write_bytes(dark_png)
    (icon_cache / '_book_page.png').write_bytes(page_png)
    monkeypatch.setattr(gow_codex, 'ICON_CACHE_DIR', icon_cache)

    app = server.App(
        save_reader=lambda: state['save'],
        telemetry_reader=lambda **kw: {'available': False, 'process_running': False},
        codex_builder=builder,
    )
    httpd = server.make_server(port=0, app=app, offline=True)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        con = http.client.HTTPConnection('127.0.0.1', httpd.server_port, timeout=10)
        # /api/codex
        con.request('GET', '/api/codex?lang=ru')
        res = con.getresponse()
        body = json.loads(res.read())
        assert res.status == 200 and body['ok'] is True
        assert body['bestiary'][0]['name'] == 'Драугр'

        # /api/map exposes codex_summary + hero
        con.request('GET', '/api/map?lang=en&realm=midgard')
        res = con.getresponse()
        mp = json.loads(res.read())
        assert res.status == 200
        assert mp['codex_summary']['bestiary_main_unlocked'] == 1
        assert mp['hero']['power_level'] == 4
        assert mp['save']['play_time'] == '41h 45m 55s'

        # /api/codex/icon/<key>.png (cached 200, dark ink 200, missing 204, traversal 404)
        con.request('GET', '/api/codex/icon/draugr_01.png')
        res = con.getresponse(); raw_icon = res.read()
        assert res.status == 200 and raw_icon == sample_png
        assert 'max-age=86400' in (res.getheader('Cache-Control') or '')

        con.request('GET', '/api/codex/icon/draugr_01.png?ink=dark')
        res = con.getresponse(); raw_dark = res.read()
        assert res.status == 200 and raw_dark == dark_png

        con.request('GET', '/api/codex/icon/missing_icon.png')
        res = con.getresponse(); res.read()
        assert res.status == 204
        assert res.getheader('Cache-Control') == 'no-store'

        con.request('GET', '/api/codex/icon/../secret.png')
        res = con.getresponse(); res.read()
        assert res.status == 404

        # /api/codex/book/<asset>.png (cached 200, missing 204, unknown/traversal 404)
        con.request('GET', '/api/codex/book/page.png')
        res = con.getresponse(); raw_page = res.read()
        assert res.status == 200 and raw_page == page_png
        assert 'max-age=86400' in (res.getheader('Cache-Control') or '')

        con.request('GET', '/api/codex/book/flap.png')
        res = con.getresponse(); res.read()
        assert res.status == 204
        assert res.getheader('Cache-Control') == 'no-store'

        con.request('GET', '/api/codex/book/unknown_asset.png')
        res = con.getresponse(); res.read()
        assert res.status == 404
        con.close()

        # /api/stream?once=1 emits initial hello event and closes cleanly
        con = http.client.HTTPConnection('127.0.0.1', httpd.server_port, timeout=5)
        con.request('GET', '/api/stream?lang=en&once=1')
        res = con.getresponse()
        text = res.read().decode('utf-8')
        con.close()
        assert res.status == 200
        assert 'event: hello' in text
        assert '"bestiary_main_unlocked": 1' in text

        # Live SSE delta when save changes
        events = []
        def reader():
            c2 = http.client.HTTPConnection('127.0.0.1', httpd.server_port, timeout=5)
            try:
                c2.request('GET', '/api/stream?lang=en&interval=0.08')
                resp = c2.getresponse()
                cur_ev = None
                while True:
                    raw_line = resp.readline()
                    if not raw_line:
                        break
                    line = raw_line.decode('utf-8').strip()
                    if line.startswith('event:'):
                        cur_ev = line.split(':', 1)[1].strip()
                    elif line.startswith('data:'):
                        events.append((cur_ev, json.loads(line.split(':', 1)[1].strip())))
                        if cur_ev == 'codex_delta':
                            break
            finally:
                c2.close()
        rt = threading.Thread(target=reader, daemon=True)
        rt.start()
        deadline = time.monotonic() + 3.0
        while not events and time.monotonic() < deadline:
            time.sleep(0.05)
        state['save'] = _synthetic_save(troll_unlocked=True, tip2_unlocked=True, draugr_kills=20)
        rt.join(timeout=3.0)
        ev_names = [e[0] for e in events]
        assert 'hello' in ev_names
        assert 'save_updated' in ev_names
        assert 'codex_delta' in ev_names
        delta_ev = next(p for name, p in events if name == 'codex_delta')
        assert delta_ev['new_bestiary'][0]['id'] == 'Bestiary_Troll_Entry'
    finally:
        # Must shut down promptly even if an SSE handler was active
        t0 = time.monotonic()
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=3.0)
        assert time.monotonic() - t0 < 2.5
