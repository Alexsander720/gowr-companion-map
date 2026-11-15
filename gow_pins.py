"""Normalize user-downloaded pins and correlate them with read-only save tables."""
from __future__ import annotations
import json
import re
from pathlib import Path
from typing import Any
from paths import DATA, PINS
from tools.fetch_mapgenie import MAP_IDS
from functools import lru_cache
from i18n import category
ALL_REALM_KEYS = tuple(MAP_IDS)
MINOR_UNTRACKED_CATS = frozenset({'hacksilver','other_loot','wood_chest','red_coffin','miscellaneous','shop','entrance','realm_tower','7096','7113','boat_dock','yggdrasils_dew'})
CATEGORY_ICONS = {'odins_raven': '🦅', 'legendary_chest': '📦', 'nornir_chest': '🗝️', 'hel_tear': '🌀', 'nine_realms_in_bloom': '🌸', 'mystic_gateway': '🚪', 'lore': '📜', 'artifact': '🏺', 'kvasirs_poem': '📖', 'berserker_gravestone': '⚔️', 'remnant_of_asgard': '☄️', 'kol_raider_camp': '⛺', 'shield': '🛡️', 'relic': '🔮', 'buried_treasure': '💰', 'treasure_map': '🗺️', 'red_coffin': '🧰', 'wood_chest': '🪵', 'hacksilver': '🪙', 'other_loot': '🎒', 'miscellaneous': '🧭', 'entrance': '🕳️', 'draugr_hole': '💀', 'yggdrasil_rift': '🌌', 'shop': '⚒️', 'jewel_of_yggdrasil': '💎', 'favor': '⭐', 'boss': '👑', 'sleeping_troll': '🗿', 'ingredient': '🍲', 'armor_set': '🥋', '7096': '⛵', '7113': '💧', '7121': '🪽', '7125': '🔑', '7132': '🔥', '7134': '🐉', '7136': '✨', '7176': '🌙', '7177': '🦌', '7179': '⛲'}

def normalize_realm_key(realm_key: str | None) -> str:
    """Приведение русскоязычного или английского названия мира к каноническому slug."""
    clean_key = (realm_key or "midgard").lower().strip()
    if clean_key in ALL_REALM_KEYS:
        return clean_key
    if "синдри" in clean_key or "sindri" in clean_key or "межмирь" in clean_key:
        return "sindris-house"
    if "хель" in clean_key or "hel" in clean_key:
        return "helheim"
    if "мид" in clean_key or "mid" in clean_key:
        return "midgard"
    if "ван" in clean_key or "van" in clean_key:
        return "vanaheim"
    if "сварт" in clean_key or "sva" in clean_key:
        return "svartalfheim"
    if "альв" in clean_key or "alf" in clean_key:
        return "alfheim"
    if "асг" in clean_key or "asg" in clean_key:
        return "asgard"
    if "йот" in clean_key or "jot" in clean_key:
        return "jotunheim"
    if "ниф" in clean_key or "nif" in clean_key:
        return "niflheim"
    if "мус" in clean_key or "mus" in clean_key:
        return "muspelheim"
    return clean_key

def _prepare_fast_pt(save_data: dict | None) -> dict[str, Any] | None:
    """Индексирует progression_tables сохранения в множества O(1) для мгновенной сверки всех меток."""
    if not save_data or not isinstance(save_data, dict):
        return None
    prog = save_data.get("progress") if isinstance(save_data.get("progress"), dict) else save_data
    pt = prog.get("progression_tables") or save_data.get("progression_tables")
    if not pt or not isinstance(pt, dict):
        return None
    visited_raw = pt.get("visited_wads") or []
    unvisited_raw = pt.get("unvisited_wads") or []
    return {
        "table1_bool": {str(h).lower() for h in (pt.get("table1_bool") or ())},
        "table1_int": {str(k).lower(): int(v) for k, v in (pt.get("table1_int") or {}).items()},
        "table2_stage": {str(k).lower(): int(v) for k, v in (pt.get("table2_stage") or {}).items()},
        "hero_items": {str(k).lower(): int(v) for k, v in (pt.get("hero_items") or {}).items()},
        "equip_owned": {str(h).lower() for h in (pt.get("equip_owned") or ())},
        "visited_wads": set(visited_raw),
        "has_wads": bool(visited_raw or unvisited_raw),
        "ft_claimed": {str(k): bool(v) for k, v in (pt.get("ft_claimed") or {}).items()},
        "wad_ent_states": {str(k): bool(v) for k, v in (pt.get("wad_ent_states") or {}).items()},
    }

def _check_is_collected(
    loc: dict,
    cat_slug: str,
    save_data: dict | None,
    realm_key: str = "",
    pin_map: dict[str, dict[str, Any]] | None = None,
    manual_ids: set[str] | None = None,
    pt_fast: dict[str, Any] | None = None,
) -> bool | None:
    """Определяет, найден/открыт ли данный тайник по данным из сохранения или ручной отметки.

    Возвращает:
      True  — подтверждено собрано (collected)
      False — подтверждено осталось зачистить (not_collected)
      None  — неизвестно (unknown: мелкий лут без флага в сохранении или нет сейва)
    """
    pid = str(loc.get("id", ""))
    if manual_ids and pid in manual_ids:
        return True

    if not save_data:
        return None

    if pt_fast is None:
        pt_fast = _prepare_fast_pt(save_data)

    # 1. Точная бинарная сверка по 5 таблицам сохранения (Table 1/2, HERO, Equipment Pool, WAD)
    if pt_fast is not None:
        p_map = pin_map if pin_map is not None else _load_pin_mapping()
        m = p_map.get(pid) or {}

        if cat_slug in MINOR_UNTRACKED_CATS:
            # Для мелкого нетрекаемого лута никогда не выдумываем статус: только None
            return None

        status: bool | None = None
        if "ft_wad" in m and "ft_item_hash" in m:
            ft_key = f"{m['ft_wad']}:{str(m['ft_item_hash']).lower()}"
            if ft_key in pt_fast["ft_claimed"]:
                status = pt_fast["ft_claimed"][ft_key]
            elif pt_fast["has_wads"] and m["ft_wad"] not in pt_fast["visited_wads"]:
                status = False
        elif "wad_ent_hash" in m and "wad_name" in m:
            ent_key = f"{m['wad_name']}:{str(m['wad_ent_hash']).lower()}"
            if ent_key in pt_fast["wad_ent_states"]:
                status = pt_fast["wad_ent_states"][ent_key]
            elif pt_fast["has_wads"] and m["wad_name"] not in pt_fast["visited_wads"]:
                status = False
        elif "equip_any" in m:
            status = any(str(eh).lower() in pt_fast["equip_owned"] for eh in m["equip_any"])
        elif "t1_bool" in m and str(m["t1_bool"]).lower() in pt_fast["table1_bool"]:
            status = True
        elif "hero_hash" in m:
            hh = str(m["hero_hash"]).lower()
            if pt_fast["hero_items"].get(hh, 0) > 0:
                status = True
            elif "t2_hash" not in m:
                status = False

        if status is None and "t2_hash" in m:
            th = str(m["t2_hash"]).lower()
            min_stg = int(m.get("t2_min_stage", 4))
            if th in pt_fast["table2_stage"]:
                status = pt_fast["table2_stage"][th] >= min_stg
            elif th in pt_fast["table1_bool"]:
                status = True
            else:
                status = False

        if status is None and "t1_bool" in m:
            status = str(m["t1_bool"]).lower() in pt_fast["table1_bool"]

        if status is None and "rs_hash" in m:
            rsh = str(m["rs_hash"]).lower()
            stg = pt_fast["table2_stage"].get(rsh, 0)
            if stg >= 4:
                status = True
            elif stg == 0:
                status = False

        if status is None and "primary_wad" in m and pt_fast["has_wads"]:
            if m["primary_wad"] not in pt_fast["visited_wads"]:
                status = False

        return status

    # 2. Резервная сверка для синтетических/упрощённых структур без progression_tables
    prog = save_data.get("progress") or save_data
    coll = prog.get("collectibles") or {}
    by_realm = coll.get("by_realm") or {}
    realm_info = by_realm.get(realm_key) or {}
    title = (loc.get("title") or "").lower()

    if cat_slug == "odins_raven":
        ravens_info = coll.get("ravens") or {}
        if ravens_info.get("collected", 0) == 0:
            return False
        if realm_info.get("ravens_total") == 0:
            return False
        return None

    if cat_slug == "nornir_chest":
        if realm_info.get("nornir_chests_total") == 0:
            return False
        apples = coll.get("idunn_apples", 0)
        horns = coll.get("blood_mead_horns", 0)
        if apples == 0 and horns == 0 and not coll.get("stat_boosts"):
            return False
        return None

    if cat_slug == "hel_tear":
        if realm_key == "alfheim":
            return True if realm_info.get("hel_tears_completed") == 1 else False
        return None

    if cat_slug == "draugr_hole":
        if realm_key == "alfheim":
            return True if realm_info.get("draugr_holes_completed") == 1 else False
        return None

    if cat_slug == "berserker_gravestone":
        bers = coll.get("berserkers") or {}
        if bers.get("gravestones_cleared", 0) == 0:
            return False
        if "hrolf" in title and bers.get("king_hrolf_defeated"):
            return True
        return None

    if cat_slug in ("yggdrasil_rift", "draugr_hole"):
        lw = coll.get("lindwyrms") or {}
        if lw.get("captured", 0) == 0:
            return False
        if lw.get("captured") == 6 and cat_slug == "yggdrasil_rift":
            return True
        return None

    return None

def summarize_pois_completion(pois: list[dict[str, Any]]) -> dict[str, Any]:
    """Сводка зачистки мира по коллекционным/квестовым точкам (без мелкого нетрекаемого лута)."""
    total = 0
    collected = 0
    remaining = 0
    unknown = 0
    by_cat: dict[str, dict[str, Any]] = {}

    for p in pois:
        if not p.get("is_completionist"):
            continue
        total += 1
        st = p.get("status")
        ckey = p.get("category_key") or "poi"
        cat_entry = by_cat.get(ckey)
        if cat_entry is None:
            cat_entry = {
                "key": ckey,
                "name": p.get("category") or ckey,
                "icon": p.get("icon") or "📍",
                "total": 0,
                "collected": 0,
                "remaining": 0,
                "unknown": 0,
            }
            by_cat[ckey] = cat_entry

        cat_entry["total"] += 1
        if st == "collected":
            collected += 1
            cat_entry["collected"] += 1
        elif st == "not_collected":
            remaining += 1
            cat_entry["remaining"] += 1
        else:
            unknown += 1
            cat_entry["unknown"] += 1

    percent = round((collected / total) * 100.0, 1) if total > 0 else 0.0
    sorted_cats = sorted(
        by_cat.values(),
        key=lambda c: (-c["remaining"], -c["total"], c["name"]),
    )
    return {
        "total": total,
        "collected": collected,
        "remaining": remaining,
        "unknown": unknown,
        "percent": percent,
        "by_category": sorted_cats,
    }

def get_all_realms_completion(
    save_data: dict | None = None,
    manual_ids: set[str] | None = None,
    lang: str = 'en',
) -> dict[str, Any]:
    """Считает точную сводку зачистки сразу по всем 9 мирам + Дому Синдри."""
    effective_manual = manual_ids if manual_ids is not None else _load_default_manual_ids()
    by_realm: dict[str, dict[str, Any]] = {}
    g_total = 0
    g_collected = 0
    g_remaining = 0
    g_unknown = 0

    for rkey in ALL_REALM_KEYS:
        r_pois = get_realm_pois(rkey, limit=1000, save_data=save_data, manual_ids=effective_manual, lang=lang)
        comp = summarize_pois_completion(r_pois)
        by_realm[rkey] = comp
        g_total += comp["total"]
        g_collected += comp["collected"]
        g_remaining += comp["remaining"]
        g_unknown += comp["unknown"]

    g_percent = round((g_collected / g_total) * 100.0, 1) if g_total > 0 else 0.0
    return {
        "total": g_total,
        "collected": g_collected,
        "remaining": g_remaining,
        "unknown": g_unknown,
        "percent": g_percent,
        "by_realm": by_realm,
    }


@lru_cache(maxsize=1)
def _load_pin_mapping():
    return json.loads((DATA / 'pin_mapping.json').read_text(encoding='utf-8'))


@lru_cache(maxsize=1)
def _load_categories_map():
    return json.loads((DATA / 'category_ids.json').read_text(encoding='utf-8'))


def _load_default_manual_ids():
    return set()  # Browser-local marks are deliberately separate from save evidence.


@lru_cache(maxsize=32)
def _read_cached(path, stamp):
    try:
        return json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}


def _cached(path):
    try:
        return _read_cached(str(path), path.stat().st_mtime_ns)
    except OSError:
        return {}


def _load_realm_locations(clean_key):
    return _cached(PINS / (clean_key + '.json')).get('locations', [])


def _localize_links(text, names):
    if not text:
        return text
    def repl(m):
        pid = re.search(r'(?:[?&])locationIds=(\d+)', m[2])
        if not pid:
            return m[1]
        entry = names.get(pid[1], {})
        return f"[{entry.get('name') or m[1]}](pin:{entry.get('realm', '')}:{pid[1]})"
    return re.sub(r'\[((?:[^\[\]]|\[[^\[\]]*\])+)\]\(([^)\s]+)\)', repl, text)


def _descriptions(pid, original, names, lang, ru_desc):
    """Original (EN) description plus our optional Russian translation (data/ru_descriptions.json)."""
    en = _localize_links(original, names)
    ru = (ru_desc.get(pid) or {}).get('ru') if original else None
    ru = _localize_links(ru, names) if ru else None
    use_ru = lang == 'ru' and bool(ru)
    return {'description': ru if use_ru else en, 'description_lang': 'ru' if use_ru else 'en',
            'description_en': en, 'description_ru': ru}


def location_names(lang='en'):
    ru = _cached(PINS / 'ru_names.json') if lang == 'ru' else {}
    # Our own translations for pins whose names are not game strings (shipped in data/).
    pending = _cached(DATA / 'ru_names_pending.json') if lang == 'ru' else {}
    # Generic titles shared by many pins (Wood Chest, Odin's Raven...) translated once by title.
    titles = _cached(DATA / 'ru_titles.json') if lang == 'ru' else {}
    names = {}
    for realm in ALL_REALM_KEYS:
        for loc in _load_realm_locations(realm):
            pid = str(loc['id'])
            names[pid] = {'name': (ru.get(pid) or {}).get('ru') or (pending.get(pid) or {}).get('ru')
                          or titles.get(loc.get('title') or '') or loc.get('title') or '', 'realm': realm}
    return names


def get_realm_pois(realm_key, limit=1000, save_data=None, manual_ids=None, lang='en'):
    key = normalize_realm_key(realm_key)
    if key not in ALL_REALM_KEYS:
        return []
    locations = _load_realm_locations(key)
    if not locations:
        return []
    lats = [float(p['latitude']) for p in locations]
    lngs = [float(p['longitude']) for p in locations]
    min_lat, max_lat, min_lng, max_lng = min(lats), max(lats), min(lngs), max(lngs)
    ids, mapping = _load_categories_map(), _load_pin_mapping()
    names = location_names(lang)
    from gow_story import load_story_strings
    strings = load_story_strings(lang)
    english_strings = load_story_strings('en') if lang != 'en' else strings
    region_sids = json.loads((DATA / 'region_sids.json').read_text(encoding='utf-8'))
    map_regions = {r['id']: r.get('title', '') for r in _cached(PINS / (key + '.json')).get('regions', [])
                   if isinstance(r, dict) and 'id' in r}
    fast = _prepare_fast_pt(save_data)
    from gow_favors import pin_favor_ids, read_favors
    favor_ids = pin_favor_ids()
    # Journal rules override conflicting legacy reward hashes.
    reward_ids = {'219969','219970','219960','219964','219961'}
    reward_state = {}
    if save_data and any(str(p['id']) in reward_ids for p in locations):
        for favor in read_favors(save_data, lang):
            for pid in favor['pin_ids']:
                if pid in reward_ids and favor['state'] != 'unknown':
                    reward_state[pid] = favor['state'] == 'completed'
    ru_desc = _cached(DATA / 'ru_descriptions.json')
    result = []
    for loc in locations[:limit]:
        pid, cid = str(loc['id']), str(loc.get('category_id', ''))
        cat = ids.get(cid) or cid
        label = category(cat, lang)
        state = _check_is_collected(loc, cat, save_data, realm_key=key, pin_map=mapping,
                                   manual_ids=manual_ids or set(), pt_fast=fast)
        if pid in reward_state:
            state = reward_state[pid]
        lat, lng = float(loc['latitude']), float(loc['longitude'])
        region_key = mapping.get(pid, {}).get('region_key', '')
        region_sid = region_sids.get(region_key)
        region_name = (strings.get(region_sid) or english_strings.get(region_sid) or
                       map_regions.get(loc.get('region_id')) or re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', region_key))
        result.append({'id': pid, 'name': names.get(pid, {}).get('name') or label,
                       'name_en': loc.get('title') or '', 'category': label, 'category_key': cat,
                       'icon': CATEGORY_ICONS.get(cat, '◇'), 'region': region_name,
                       'region_key': mapping.get(pid, {}).get('region_key', ''), 'is_completionist': cat not in MINOR_UNTRACKED_CATS,
                       'is_manual': pid in (manual_ids or set()), 'is_collected': state,
                       'status': 'collected' if state is True else 'not_collected' if state is False else 'unknown',
                       'pct_x': round(6 + (lng-min_lng)/(max_lng-min_lng or 1)*88, 2),
                       'pct_y': round(6 + (1-(lat-min_lat)/(max_lat-min_lat or 1))*88, 2), 'lat': lat, 'lng': lng,
                       **_descriptions(pid, loc.get('description'), names, lang, ru_desc), 'media': [], 'favor_ids': favor_ids.get(pid, []),
                       'artifact': names.get(pid, {}).get('name') if pid in reward_ids else None})
    return result
