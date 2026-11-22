"""Favor journal: code-owned hash joins, runtime localization, read-only save state."""
from __future__ import annotations
import json
import math
import re
import struct
from functools import lru_cache
from paths import DATA
import gowsave

def parse_quest_database(raw: bytes, start: int, end: int, ru: dict, en: dict) -> list[dict]:
    """Parse the DC payload (also accepts synthetic bytes with the same layout)."""
    def check(off, size):
        if not start <= off <= off + size <= end <= len(raw):
            raise ValueError('Truncated quest database')

    def u32(off):
        check(off, 4)
        return struct.unpack_from('<I', raw, off)[0]

    def ptr(off):
        check(off, 8)
        target = off + struct.unpack_from('<q', raw, off)[0]
        check(target, 1)
        return target

    def array(off, count):
        if not 0 <= count <= 20000:
            raise ValueError('Invalid quest array count')
        if not count:
            return []
        p = ptr(off)
        check(p, count * 8)
        return [ptr(p + i * 8) for i in range(count)]

    def record(off, ancestors=()):
        check(off, 120)
        if off in ancestors or len(ancestors) > 16:
            raise ValueError('Cyclic quest tree')
        p = ptr(off + 80)
        stop = raw.find(b'\0', p, end)
        if stop < 0 or stop - p > 256:
            raise ValueError('Invalid quest name')
        name = raw[p:stop].decode('ascii')
        if not re.fullmatch(r'[A-Za-z0-9_]+', name):
            raise ValueError('Invalid quest name')
        sid, descid = u32(off + 12), u32(off + 28)
        counter = None
        description = ru.get(descid) or en.get(descid, '')
        # A visible counted objective has a localized %d/%d description and a
        # completion condition: type 0x10000/0x10500, Table 1 key +8, f32 total +16.
        # Example: XPL_Draugr_Holes_Objective @0x2a760, condition @0x2a8f0,
        # key 0x3464c4e41540373b, total 6; live Table 1 =4, journal fixture =4/6.
        if '%d' in description:
            candidates = []
            for q in array(off + 64, u32(off + 72)):
                check(q, 20)
                kind, key, total = struct.unpack_from('<QQf', raw, q)
                if kind in (0x10000, 0x10500) and math.isfinite(total) and total > 1 and total.is_integer():
                    candidates.append({'hash': f'0x{key:016x}', 'total': int(total), 'offset': q})
            if len(candidates) == 1:
                counter = candidates[0]
        children = [record(q, ancestors + (off,)) for q in array(off + 32, u32(off + 40))]
        return {'id': name, 'hash': f'0x{gowsave.sms_std_name_hash(name):016x}',
                'offset': off, 'name_sid': sid, 'name': ru.get(sid), 'name_en': en.get(sid),
                'description_sid': descid, 'description': description, 'counter': counter,
                'kind': u32(off + 44), 'steps': children}

    return [record(off) for off in array(start, u32(start + 8))]

def _flatten(records):
    for q in records:
        yield q
        yield from _flatten(q['steps'])

def read_favors(save_data: dict | None, lang='en') -> list[dict]:
    """All known favors; absent/unrecognized Table 2 entries remain unknown."""
    save_data = save_data or {}
    pt = save_data.get('progression_tables') or (save_data.get('progress') or {}).get('progression_tables') or {}
    stages = {str(k).lower(): v for k, v in (pt.get('table2_stage') or {}).items()}
    counters = {str(k).lower(): v for k, v in (pt.get('table1_int') or {}).items()}
    import gow_pins
    fast = gow_pins._prepare_fast_pt(save_data)
    guides = gow_pins._load_guides().get('favors', {})
    names = gow_pins.location_names(lang) if guides else {}
    anchors = {(realm, str(loc['id'])): loc for realm in gow_pins.ALL_REALM_KEYS
               for loc in gow_pins._load_realm_locations(realm)} if guides else {}
    result = []
    for q in load_catalog(lang)['favors']:
        stage = stages.get(q['hash'])
        # 0/2/4 corroborated against the owner's journal and completed favor pins.
        # Stage 5 exists for unrelated quests; it is deliberately NOT completed.
        state = {0: 'not_started', 2: 'active', 4: 'completed'}.get(stage, 'unknown')
        active = [s for s in _flatten(q['steps']) if stages.get(s['hash']) == 2 and s['name']]
        counted = [s for s in active if s['counter']]
        visible = counted + [s for s in active if not s['counter']]
        step = '; '.join(dict.fromkeys(s['name'] for s in visible)) if state == 'active' else None
        objectives = []
        for s in visible if state == 'active' else []:
            counter = None
            c = s['counter']
            done = counters.get(c['hash']) if c else None
            if c and isinstance(done, int) and 0 <= done <= c['total']:
                counter = {'done': done, 'total': c['total']}
            objectives.append({'id': s.get('id'), 'name': s['name'], 'counter': counter,
                               'counter_unknown': bool(c and counter is None)})
        counter = next((o['counter'] for o in objectives if o['counter'] is not None), None)
        pin_states = {}
        for pid in q['pin_ids']:
            m = q.get('pin_rules', {}).get(pid) or {}
            # Use only save evidence here: manual map marks are not journal
            # completion. An absent Table 2 key is unknown, not a completed site.
            collected = None
            key = m.get('t2_hash')
            known_stage = not key or stages.get(key) in (0, 2, 4)
            summary_key = m.get('rs_hash')
            known_summary = not summary_key or summary_key not in stages or stages[summary_key] in (0, 2, 4)
            if fast and m and known_stage and known_summary:
                collected = gow_pins._check_is_collected({'id': pid}, '', save_data,
                    pin_map={pid: m}, manual_ids=set(), pt_fast=fast)
            pin_states[pid] = {True: 'collected', False: 'not_collected', None: 'unknown'}[collected]
        result.append({'id': q['id'], 'name': q['name'], 'region': q['region'], 'realm': q['realm'],
                       'state': state, 'step': step, 'counter': counter, 'pin_ids': q['pin_ids'],
                       'pin_realms': q['pin_realms'], 'pin_states': pin_states,
                       'step_locations_unknown': q.get('step_locations_unknown', False),
                       'stage': stage, 'objectives': objectives,
                       'step_ids': [s['id'] for s in visible if state == 'active' and s.get('id')]})
        entry = guides.get(q['id'])
        if isinstance(entry, dict):
            guide = gow_pins._guide(entry, lang, names)
            if guide:
                result[-1]['guide'] = guide
            points = []
            raw_points = entry.get('points')
            for point in raw_points if isinstance(raw_points, list) else []:
                if not isinstance(point, dict):
                    continue
                pid, realm = str(point.get('anchor_pin', '')), point.get('realm')
                if not isinstance(realm, str):
                    continue
                anchor = anchors.get((realm, pid))
                if not anchor:
                    continue
                try:
                    lat, lng = float(anchor['latitude']), float(anchor['longitude'])
                except (KeyError, TypeError, ValueError):
                    continue
                if not (math.isfinite(lat) and math.isfinite(lng)):
                    continue
                preferred = 'label_ru' if lang == 'ru' else 'label_en'
                fallback = 'label_en' if preferred == 'label_ru' else 'label_ru'
                label = next((point[k] for k in (preferred, fallback)
                              if isinstance(point.get(k), str) and point[k].strip()), '')
                name = names.get(pid, {}).get('name') or anchor.get('title') or ''
                points.append({'step': point.get('step'), 'realm': realm, 'lat': lat, 'lng': lng,
                               'label': label or name, 'anchor_pin': pid, 'anchor_name': name})
            result[-1]['points'] = points
    return result


@lru_cache(maxsize=1)
def _base_catalog():
    return json.loads((DATA / 'favors_map.json').read_text(encoding='utf-8'))


def pin_favor_ids():
    result = {}
    for q in _base_catalog()['favors']:
        for pid in q['pin_ids']:
            result.setdefault(pid, []).append(q['id'])
    return result


def load_catalog(lang='en'):
    from gow_story import load_story_strings
    from gow_pins import location_names, _load_realm_locations
    from i18n import t
    strings = load_story_strings(lang)
    english = load_story_strings('en') if lang != 'en' else strings
    names = location_names(lang)
    anchor_ids = {str(loc['id']) for realm in __import__('gow_pins').ALL_REALM_KEYS
                  for loc in _load_realm_locations(realm) if loc.get('category_id') == 7115}
    def hydrate(q):
        out = dict(q)
        sid = q.get('name_sid')
        fallback = next((names[pid]['name'] for pid in q.get('pin_ids', []) if pid in anchor_ids and pid in names), None)
        out['name'] = strings.get(sid) or english.get(sid) or fallback or (t('step_unknown', lang) if sid else None)
        out['counter'] = q.get('counter')
        out['steps'] = [hydrate(s) for s in q.get('steps', [])]
        if q.get('pin_ids') is not None:
            out['name'] = out['name'] or q['id']
            out['region'] = t(q.get('realm') or 'nine_realms', lang)
        return out
    return {'favors': [hydrate(q) for q in _base_catalog()['favors']]}
