"""Runtime Codex reader (Bestiary, Lore, Skill Labors, Hero Loadout & Materials).

Reads structured journal definitions strictly from the user's local game files
(`exec/dc/pc_le/quests_main.dcb`, `r_lang_*.wad`, `r_ui.wad` + `root.texpack`),
joins them read-only against save progression tables (`table1_int`, `table2_stage`),
and caches rendered monochrome-gold ink portraits strictly in user cache
(`%LOCALAPPDATA%\\gowr-companion-map\\cache\\codex_icons\\`).
No extracted game prose or textures are ever stored in the repository.
"""
from __future__ import annotations

import io
import re
import struct
import threading
import time
from functools import lru_cache
from pathlib import Path
from typing import Any

import gow_favors
import gow_story
import gowsave
import paths

ICON_CACHE_DIR = paths.CACHE / 'codex_icons'
ICON_KEY_RE = re.compile(r'^[a-z0-9_-]{1,64}$')
BOOK_ASSETS = {
    'page': 'TX_sonjournal00_page_base_gen_0d_1D85FF6FD0E44A3C',
    'flap': 'TX_pagesolo_d_094752992F00A7A0',
    'cover': 'TX_sonjournal00_kratos_cover_gen_0d_8F2268E70F22CC5C',
    'cover_frame': 'TX_sonjournalui00_cover_gen_0d_914F9F0C5D75D2AF',
    'header_brush': 'TX_headerpaint_m_434426C1A3B9B132',
    'row_brush': 'TX_headerpaint_small_m_4C72B1FB954E52E1',
    'wm_lore': 'TX_journal_design_5079E16CA1FCD7B8',
    'wm_bestiary': 'TX_codex_design_CB33037DEF23F5BF',
}
_BOOK_FLAP_MASK = 'TX_pagesolo_m_676F818AD992E735'
_ICON_LOCK = threading.Lock()

# Fallback portrait stem overrides for the 18 entries whose h58 uses an internal
# alias that differs slightly from the TX_<stem>_01_<hash> filename in r_ui.wad.
_PORTRAIT_FALLBACK_BY_PREFIX = (
    ('Bestiary_GolemSoulEater', 'golem_souleater01'),
    ('Bestiary_Golem', 'golem_01'),
    ('Bestiary_DarkOneElite', 'darkoneelite_01'),
    ('Bestiary_DarkOneSummoner', 'darkone_summoner01'),
    ('Bestiary_DarkOneWarrior', 'darkone_blaster_01'),
    ('Bestiary_DarkOne', 'darkone_blaster_01'),
    ('Bestiary_DraugrChest', 'draugr_chest_01'),
    ('Bestiary_DraugrLegs', 'draugr_leg_01'),
    ('Bestiary_DraugrWeapon', 'draugr_powerweapon_01'),
    ('Bestiary_DraugrArm', 'draugr_skinny_arm_01'),
    ('Bestiary_DraugrDual', 'draugr_skinny_dual_wield_01'),
    ('Bestiary_DraugrShield', 'draugr_01_shield'),
    ('Bestiary_DraugrHeavy', 'draugr_heavy_01'),
    ('Bestiary_Draugr', 'draugr_01'),
    ('Bestiary_LightOneElite', 'lightone_elite_01'),
    ('Bestiary_LightOneWarrior', 'lightone_samurai_01'),
    ('Bestiary_LightOneMythic', 'lightone_mystic_01'),
    ('Bestiary_LightOne', 'lightone_01'),
    ('Bestiary_ProjectionBrood', 'projection_01'),
    ('Bestiary_TravelerChampion', 'traveler_02'),
    ('Bestiary_Traveler', 'traveler_01'),
)

# Family tokens linking Bestiary entries to Labor_*Kills counters from quests_main.dcb.
_KILL_FAMILY_PATTERNS = (
    ('draugr', ('draugr',)),
    ('bandit', ('bandit', 'reaver')),
    ('berserker', ('berserker', 'raider')),
    ('helwalker', ('helwalker', 'hel_', 'helreaver', 'helviken', 'helshadow')),
    ('seidr', ('seidr', 'viken', 'shadow', 'revenant')),
    ('darkone', ('darkone',)),
    ('lightone', ('lightone',)),
    ('einherjar', ('einherjar',)),
    ('grim', ('grim', 'bergsra')),
    ('wretch', ('wretch',)),
    ('nightmare', ('nightmare', 'flyer')),
    ('wisp', ('wisp',)),
    ('wulver', ('wulver',)),
    ('ogre', ('ogre',)),
    ('troll', ('troll',)),
    ('golem', ('golem', 'souleater')),
    ('wyvern', ('wyvern', 'dreki', 'drake', 'dragon')),
    ('stalker', ('stalker', 'stagtaur')),
    ('traveler', ('traveler',)),
)

# English names for KNOWN_RESOURCE_HASHES keys so both RU and EN UI show clean material labels.
_MATERIAL_EN = {
    'hacksilver': 'Hacksilver',
    'divine_ashes': 'Divine Ashes',
    'forged_iron': 'Forged Iron',
    'dwarven_steel': 'Dwarven Steel',
    'asgardian_ingot': 'Asgardian Ingot',
    'luminous_alloy': 'Luminous Alloy',
    'petrified_bone': 'Petrified Bone',
    'stonewood': 'Stonewood',
    'ydalir_timber': 'Ydalir Timber',
    'honed_metal': 'Honed Metal',
    'slag_deposits': 'Slag Deposits',
    'rawhide': 'Rawhide',
    'bonded_leather': 'Bonded Leather',
    'beast_scraps': 'Beast Scraps',
    'beast_bones': 'Beast Bones',
    'dragon_teeth': 'Dragon Tooth',
    'dust_of_realms': 'Dust of Realms',
    'whispering_slab': 'Whispering Slab',
    'shattered_runes': 'Shattered Runes',
    'nidavellir_core': 'Nidavellir Ore',
    'tempered_remnants': 'Tempered Remnants',
    'hardened_remnants': 'Hardened Remnants',
    'hunters_brand': "Hunter's Brand",
    'essence_of_hel': 'Essence of Hel',
    'svefnthorn': 'Svefnthorn',
    'crackle_of_bilskirnir': 'Crackle of Bilskirnir',
    'nars_cup': "Nar's Cup",
    'frozen_flame': 'Frozen Flame',
    'chaos_flame': 'Chaos Flame',
    'gale_flame': 'Gale Flame',
    'frozen_spark': 'Frozen Spark',
    'chaos_spark_alt': 'Chaos Spark',
    'jewel_of_yggdrasil': 'Jewel of Yggdrasil',
    'lindwyrm_scales': 'Lindwyrm Scales',
    'folkvangr_whetstone': 'Folkvangr Whetstone',
    'skirnir_gambanteinn': 'Skirnir Gambanteinn',
    'resurrection_stone': 'Resurrection Stone',
    'dew_strength': "Yggdrasil's Dew of Strength",
    'dew_runic': "Yggdrasil's Dew of Runic Power",
    'dew_defense': "Yggdrasil's Dew of Defense",
    'dew_cooldown': "Yggdrasil's Dew of Cooldown",
    'dew_vitality': "Yggdrasil's Dew of Vitality",
    'dew_luck': "Yggdrasil's Dew of Luck",
}

_MATERIAL_CATEGORIES = {'материал', 'улучшение', 'улучшение топора', 'улучшение клинков', 'улучшение копья', 'амулет', 'усиление', 'квест/материал', 'расходник'}

_WEAPON_LABELS = {
    'en': {'axe': 'Leviathan Axe', 'blades': 'Blades of Chaos', 'spear': 'Draupnir Spear', 'other': 'Combat'},
    'ru': {'axe': 'Топор Левиафан', 'blades': 'Клинки Хаоса', 'spear': 'Копьё Драупнир', 'other': 'Бой'},
}

_SLOT_LABELS = {
    'en': {
        'axe': 'Leviathan Axe', 'axe_pommel': 'Axe Attachment',
        'blades': 'Blades of Chaos', 'blades_handles': 'Blades Attachment',
        'spear': 'Draupnir Spear', 'spear_sauroter': 'Spear Hind',
        'chest': 'Chest Armor', 'wrist': 'Wrist Armor', 'waist': 'Waist Armor',
        'shield': 'Shield', 'rond': 'Shield Rönd',
    },
    'ru': {
        'axe': 'Топор Левиафан', 'axe_pommel': 'Рукоять топора',
        'blades': 'Клинки Хаоса', 'blades_handles': 'Рукояти клинков',
        'spear': 'Копьё Драупнир', 'spear_sauroter': 'Тыльник копья',
        'chest': 'Нагрудник', 'wrist': 'Наручи', 'waist': 'Пояс',
        'shield': 'Щит', 'rond': 'Ронд щита',
    },
}

_GEAR_EN_NAMES = {
    'Топор Левиафан': 'Leviathan Axe',
    'Клинки Хаоса': 'Blades of Chaos',
    'Копьё Драупнир': 'Draupnir Spear',
    'Щит': 'Shield',
    'Ронд щита': 'Shield Rönd',
    'Кираса Лунды (нагрудник)': "Lunda's Lost Cuirass",
    'Браслеты Лунды': "Lunda's Lost Bracers",
    'Пояс Лунды': "Lunda's Lost Belt",
}

_TIER_LABELS = {
    'en': {'bronze': 'Bronze', 'silver': 'Silver', 'gold': 'Gold', 'platinum': 'Platinum'},
    'ru': {'bronze': 'Бронза', 'silver': 'Серебро', 'gold': 'Золото', 'platinum': 'Платина'},
}


def _is_valhalla_id(rid: str) -> bool:
    return rid.endswith('_Val') or rid.startswith('Val_') or '_Val_' in rid


def _extract_skill_name_sid(qraw: bytes, first_step_off: int) -> int:
    """Follow Bronze step's completion notification pointer chain (+0x10 -> +0x30 -> +0x08) for official skill SID."""
    n = len(qraw)
    try:
        if not (0 <= first_step_off + 0x18 <= n):
            return 0
        rel_arr = struct.unpack_from('<q', qraw, first_step_off + 0x10)[0]
        p_arr = first_step_off + 0x10 + rel_arr
        if not (0 <= p_arr + 8 <= n):
            return 0
        p_item = p_arr + struct.unpack_from('<q', qraw, p_arr)[0]
        if not (0 <= p_item + 0x38 <= n):
            return 0
        p_sub_arr = p_item + 0x30 + struct.unpack_from('<q', qraw, p_item + 0x30)[0]
        if not (0 <= p_sub_arr + 8 <= n):
            return 0
        p_sub = p_sub_arr + struct.unpack_from('<q', qraw, p_sub_arr)[0]
        if not (0 <= p_sub + 12 <= n):
            return 0
        return int(struct.unpack_from('<I', qraw, p_sub + 8)[0])
    except (struct.error, ValueError):
        return 0


@lru_cache(maxsize=2)
def _ru_to_en_strings_cached(game_dir_str: str) -> dict[str, str]:
    """Map Russian game string -> English game string via shared string IDs from local WADs."""
    en = gow_story.load_story_strings('en')
    ru = gow_story.load_story_strings('ru')
    out: dict[str, str] = {}
    for sid, rtxt in ru.items():
        if rtxt and sid in en and en[sid]:
            out.setdefault(rtxt.strip().lower(), en[sid].strip())
    return out


def _translate_gear_to_en(raw_name: str, fallback: str) -> str:
    if not raw_name:
        return fallback
    if raw_name in _GEAR_EN_NAMES:
        return _GEAR_EN_NAMES[raw_name]
    if not any('\u0400' <= ch <= '\u04ff' for ch in raw_name):
        return raw_name
    gd = paths.find_game_dir()
    if gd:
        lookup = _ru_to_en_strings_cached(str(gd))
        clean = re.sub(r'\s*\([^)]*\)\s*$', '', raw_name).strip()
        hit = lookup.get(raw_name.strip().lower()) or lookup.get(clean.lower())
        if hit:
            return hit
    return fallback


def clean_game_text(text: str | None) -> str:
    """Convert GoWR journal markup (`\\n\\p`, `[i]`, `[style=...]`) to clean readable prose."""
    if not text:
        return ''
    s = str(text)
    s = re.sub(r'^\[\[[^\]]*\]\]\s*', '', s)
    s = s.replace('\\n\\p', '\n\n').replace('\\p', '\n\n').replace('\\n', '\n')
    s = re.sub(r'\[style=[^\]]+\]', '**', s)
    s = s.replace('[/style]', '**')
    s = re.sub(r'\[/?i\]', '_', s, flags=re.I)
    s = re.sub(r'\[/?b\]', '**', s, flags=re.I)
    s = re.sub(r'\[Icons:[^\]]+\]', '', s)
    s = re.sub(r'\[[A-Za-z0-9_]+Button\]', '', s)
    s = re.sub(r'\n{3,}', '\n\n', s)
    return s.strip()


def _humanize_skill_id(skill_id: str) -> tuple[str, str]:
    """Derive weapon group and readable label from a `Labor_Skill_*` identifier."""
    raw = skill_id.removeprefix('Labor_Skill_')
    low = raw.lower()
    if low.startswith('axe'):
        weapon = 'axe'
        body = raw[3:]
    elif low.startswith(('blades', 'blade')):
        weapon = 'blades'
        body = raw[6:] if low.startswith('blades') else raw[5:]
    elif low.startswith('spear'):
        weapon = 'spear'
        body = raw[5:]
    else:
        weapon = 'other'
        body = raw
    words = re.sub(r'([a-z])([A-Z])', r'\1 \2', body).replace('_', ' ').strip()
    words = re.sub(r'\bEvade F\b', 'Evade Forward', words)
    words = re.sub(r'\bEvade B\b', 'Evade Back', words)
    return weapon, words or raw


def _dc_quests_path() -> Path | None:
    gd = paths.find_game_dir()
    if not gd:
        return None
    p = gd / 'exec' / 'dc' / 'pc_le' / 'quests_main.dcb'
    return p if p.is_file() else None


def _ui_wad_path() -> Path | None:
    wd = paths.wad_dir()
    p = wd / 'r_ui.wad'
    return p if p.is_file() else None


@lru_cache(maxsize=2)
def _load_ui_tx_index(wad_path_str: str, size: int, mtime: int) -> tuple[dict[int, str], dict[str, str]]:
    """Scan `r_ui.wad` once per file stamp to map portrait hashes and stems -> TX names."""
    import lz4.frame
    from tools import gow_texpack
    raw = lz4.frame.decompress(Path(wad_path_str).read_bytes())
    tp_dir = Path(wad_path_str).parent
    packs = sorted(tp_dir.glob('*.texpack'), key=lambda p: (p.name != 'root.texpack', p.name))
    tp_index = (
        gow_texpack._texpack_toc_index(
            str(tp_dir), tuple((p.name, p.stat().st_size, p.stat().st_mtime_ns) for p in packs)
        )
        if packs else {}
    )
    by_hash: dict[int, str] = {}
    by_stem: dict[str, str] = {}
    for m in re.finditer(rb'(TX_[A-Za-z0-9_]{3,64})', raw):
        tn = m.group(1).decode('ascii', 'ignore')
        if len(tn) <= 20 or tn[-17] != '_':
            continue
        if tp_index:
            try:
                if gow_texpack.texture_hash(tn) not in tp_index:
                    continue
            except ValueError:
                continue
        stem = tn[3:-17]
        low = stem.lower()
        by_stem.setdefault(low, tn)
        variants = {
            stem,
            re.sub(r'_?0\d$', '', stem),
            stem.replace('_01', ''),
            stem.replace('01', ''),
            stem.replace('_', ''),
            re.sub(r'_?0\d$', '', stem).replace('_', ''),
        }
        for v in list(variants):
            variants.add(v.replace('skinny_', ''))
            variants.add(v.replace('_01_', '_'))
        for v in variants:
            if v:
                by_hash.setdefault(gowsave.sms_std_name_hash(v), tn)
    return by_hash, by_stem


def _ui_tx_index() -> tuple[dict[int, str], dict[str, str]]:
    p = _ui_wad_path()
    if not p:
        return {}, {}
    try:
        st = p.stat()
        return _load_ui_tx_index(str(p), st.st_size, st.st_mtime_ns)
    except (OSError, ValueError, RuntimeError, ImportError):
        return {}, {}


def _safe_icon_key(tx_name: str) -> str:
    stem = tx_name.removeprefix('TX_')
    if len(stem) > 17 and stem[-17] == '_':
        stem = stem[:-17]
    key = re.sub(r'[^a-z0-9_-]+', '_', stem.lower()).strip('_')
    return key[:64]


def _resolve_portrait_tx(entry_id: str, h58: int, by_hash: dict[int, str], by_stem: dict[str, str]) -> str | None:
    if h58 and h58 in by_hash:
        return by_hash[h58]
    for pref, stem in _PORTRAIT_FALLBACK_BY_PREFIX:
        if entry_id.startswith(pref):
            tx = by_stem.get(stem.lower())
            if tx:
                return tx
    # Generic normalized fallback against stem table
    norm = re.sub(r'^(Bestiary_|Lore_People_|Lore_Enemies_)', '', entry_id)
    norm = re.sub(r'(_Entry|_Val|_Atreus|_Preload)$', '', norm)
    low = re.sub(r'[^a-z0-9]+', '', norm.lower())
    if low:
        for stem_k, tx in by_stem.items():
            s_clean = re.sub(r'(_?0\d)$', '', stem_k).replace('_', '')
            if s_clean == low:
                return tx
    return None


def _parse_categories(qraw: bytes) -> tuple[dict[int, tuple[int, int]], dict[int, tuple[int, int, int]]]:
    """Read official journal categories & subcategories from header table @0x3b0."""
    rel, cnt = struct.unpack_from('<qI', qraw, 0x3b0)
    arr = 0x3b0 + rel
    hash_to_cat: dict[int, tuple[int, int]] = {}
    hash_to_sub: dict[int, tuple[int, int, int]] = {}
    for i in range(min(cnt, 32)):
        p = arr + i * 8
        t = p + struct.unpack_from('<q', qraw, p)[0]
        sub_rel, sub_cnt, name_sid = struct.unpack_from('<qII', qraw, t)
        h_rel, h_cnt = struct.unpack_from('<qI', qraw, t + 32)
        if h_rel and h_cnt and name_sid:
            tp = t + 32 + h_rel
            for k in range(min(h_cnt, 4)):
                h = struct.unpack_from('<Q', qraw, tp + k * 8)[0]
                if h:
                    hash_to_cat[h] = (i, name_sid)
        if sub_cnt and sub_rel:
            sarr = t + sub_rel
            for j in range(min(sub_cnt, 64)):
                sp = sarr + j * 8
                st = sp + struct.unpack_from('<q', qraw, sp)[0]
                s_sid = struct.unpack_from('<I', qraw, st + 12)[0]
                sh_rel, _ = struct.unpack_from('<qI', qraw, st + 32)
                if sh_rel:
                    sh = struct.unpack_from('<Q', qraw, st + 32 + sh_rel)[0]
                    if sh:
                        hash_to_sub[sh] = (i, j, s_sid)
    return hash_to_cat, hash_to_sub


@lru_cache(maxsize=2)
def _load_dc_catalog(dcb_path_str: str, size: int, mtime: int) -> dict[str, Any]:
    """Parse `quests_main.dcb` into language-agnostic numeric SIDs, hashes & icon keys."""
    import lz4.frame
    qraw = lz4.frame.decompress(Path(dcb_path_str).read_bytes())
    # Verify WTOC magic and DC section payload @0x3a0 (size stored in WTOC[1] @0xd4)
    if qraw[:4] != b'WTOC':
        raise ValueError('Unexpected quests_main.dcb header')
    dc_size = struct.unpack_from('<I', qraw, 0xd4)[0]
    dc_start = 0x3a0
    dc_end = min(len(qraw), dc_start + dc_size)

    hash_to_cat, hash_to_sub = _parse_categories(qraw)
    en_strings = gow_story.load_story_strings('en')
    ru_strings = gow_story.load_story_strings('ru')
    recs = gow_favors.parse_quest_database(qraw, dc_start, dc_end, ru_strings, en_strings)
    by_hash, by_stem = _ui_tx_index()

    bestiary: list[dict[str, Any]] = []
    lore: list[dict[str, Any]] = []
    treasures: list[dict[str, Any]] = []
    skills: list[dict[str, Any]] = []
    labors: list[dict[str, Any]] = []
    kill_counters: dict[str, str] = {}  # family -> table1_int hash
    icon_to_tx: dict[str, str] = {}

    def record_cat_sub(off: int):
        p0_rel, c0 = struct.unpack_from('<qI', qraw, off)
        if not c0 or not p0_rel:
            return None, None
        hs = [struct.unpack_from('<Q', qraw, off + p0_rel + k * 8)[0] for k in range(min(c0, 4))]
        cat = next((hash_to_cat[h] for h in hs if h in hash_to_cat), None)
        sub = next((hash_to_sub[h] for h in hs if h in hash_to_sub), None)
        return cat, sub

    def extract_best_counter(node: dict[str, Any]) -> dict[str, Any] | None:
        if node.get('counter'):
            return node['counter']
        for step in node.get('steps') or []:
            c = extract_best_counter(step)
            if c:
                return c
        return None

    for r in recs:
        rid = r['id']
        off = r['offset']
        cat, sub = record_cat_sub(off)
        cat_idx = cat[0] if cat else -1
        sub_sid = sub[2] if sub else 0
        h58 = struct.unpack_from('<Q', qraw, off + 0x58)[0]

        # Track family kill counters from Labor_*Kills
        if rid.startswith('Labor_') and 'Kills' in rid and 'NGP' not in rid:
            c = extract_best_counter(r)
            if c and c.get('hash'):
                low = rid.lower()
                for fam, toks in _KILL_FAMILY_PATTERNS:
                    if any(t in low for t in toks):
                        kill_counters.setdefault(fam, c['hash'].lower())

        # 1. Bestiary (category 6)
        if cat_idx == 6 or rid.startswith('Bestiary_'):
            tx = _resolve_portrait_tx(rid, h58, by_hash, by_stem)
            icon_key = None
            if tx:
                icon_key = _safe_icon_key(tx)
                if icon_key:
                    icon_to_tx.setdefault(icon_key, tx)
            tips = []
            for s in r.get('steps') or []:
                tips.append({
                    'id': s['id'],
                    'hash': s['hash'].lower(),
                    'name_sid': s['name_sid'],
                    'desc_sid': s['description_sid'],
                })
            low_id = rid.lower()
            family = next((fam for fam, toks in _KILL_FAMILY_PATTERNS if any(t in low_id for t in toks)), None)
            bestiary.append({
                'id': rid,
                'hash': r['hash'].lower(),
                'name_sid': r['name_sid'],
                'desc_sid': r['description_sid'],
                'sub_sid': sub_sid,
                'is_valhalla': _is_valhalla_id(rid),
                'icon_key': icon_key,
                'family': family,
                'tips': tips,
            })
            continue

        # 2. Lore (category 5: Friends, Foes, Friends & Foes, Lore Markers, Rune Reads, Scrolls)
        if cat_idx == 5:
            tx = _resolve_portrait_tx(rid, h58, by_hash, by_stem)
            icon_key = None
            if tx:
                icon_key = _safe_icon_key(tx)
                if icon_key:
                    icon_to_tx.setdefault(icon_key, tx)
            updates = []
            for s in r.get('steps') or []:
                if s.get('description_sid') or s.get('name_sid'):
                    updates.append({
                        'id': s['id'],
                        'hash': s['hash'].lower(),
                        'name_sid': s['name_sid'],
                        'desc_sid': s['description_sid'],
                    })
            lore.append({
                'id': rid,
                'hash': r['hash'].lower(),
                'name_sid': r['name_sid'],
                'desc_sid': r['description_sid'],
                'sub_sid': sub_sid,
                'is_valhalla': _is_valhalla_id(rid),
                'icon_key': icon_key,
                'updates': updates,
            })
            continue

        # 2b. Treasure Maps (10 TreasureMap_*_Parent records with clue art + riddle text)
        if rid.startswith('TreasureMap_') and rid.endswith('_Parent') and 'Trophy' not in rid and r.get('name_sid'):
            tx = by_stem.get(rid.lower())
            icon_key = None
            if tx:
                icon_key = _safe_icon_key(tx)
                if icon_key:
                    icon_to_tx.setdefault(icon_key, tx)
            steps = r.get('steps') or []
            treasures.append({
                'id': rid,
                'hash': r['hash'].lower(),
                'step_hash': steps[0]['hash'].lower() if steps else None,
                'name_sid': r['name_sid'],
                'desc_sid': r['description_sid'],
                'icon_key': icon_key,
            })
            continue

        # 3. Skill Labors (49 weapon skill tiers)
        if rid.startswith('Labor_Skill_'):
            weapon, fallback_label = _humanize_skill_id(rid)
            steps_list = r.get('steps') or []
            skill_name_sid = _extract_skill_name_sid(qraw, steps_list[0]['offset']) if steps_list else 0
            tiers = []
            for s in steps_list:
                c = s.get('counter')
                tier_key = s['id'].rsplit('_', 1)[-1].lower()
                if tier_key not in ('bronze', 'silver', 'gold', 'platinum'):
                    continue
                tiers.append({
                    'tier': tier_key,
                    'hash': s['hash'].lower(),
                    'name_sid': s['name_sid'],
                    'counter_hash': c['hash'].lower() if c else None,
                    'total': c['total'] if c else None,
                })
            if tiers:
                tiers.sort(key=lambda t: t['total'] or 0)
                skills.append({
                    'id': rid,
                    'hash': r['hash'].lower(),
                    'weapon': weapon,
                    'name_sid': skill_name_sid,
                    'label': fallback_label,
                    'tiers': tiers,
                })
            continue

        # 4. General Labors (cat 4 or 9, non-Skill)
        if (cat_idx in (4, 9) or rid.startswith('Labor_')) and r.get('name_sid'):
            tiers = []
            for s in r.get('steps') or []:
                c = s.get('counter')
                if c:
                    tiers.append({
                        'id': s['id'],
                        'hash': s['hash'].lower(),
                        'name_sid': s['name_sid'],
                        'desc_sid': s['description_sid'],
                        'counter_hash': c['hash'].lower(),
                        'total': c['total'],
                    })
            if not tiers and r.get('counter'):
                c = r['counter']
                tiers.append({
                    'id': rid,
                    'hash': r['hash'].lower(),
                    'name_sid': r['name_sid'],
                    'desc_sid': r['description_sid'],
                    'counter_hash': c['hash'].lower(),
                    'total': c['total'],
                })
            if tiers:
                tiers.sort(key=lambda t: t['total'] or 0)
                labors.append({
                    'id': rid,
                    'hash': r['hash'].lower(),
                    'name_sid': r['name_sid'],
                    'desc_sid': r['description_sid'],
                    'sub_sid': sub_sid,
                    'is_ngp': '_NGP_' in rid,
                    'is_valhalla': cat_idx == 9 or _is_valhalla_id(rid),
                    'tiers': tiers,
                })

    return {
        'bestiary': bestiary,
        'lore': lore,
        'treasures': treasures,
        'skills': skills,
        'labors': labors,
        'kill_counters': kill_counters,
        'icon_to_tx': icon_to_tx,
    }


def _base_dc_catalog() -> dict[str, Any] | None:
    p = _dc_quests_path()
    if not p:
        return None
    try:
        st = p.stat()
        return _load_dc_catalog(str(p), st.st_size, st.st_mtime_ns)
    except (OSError, ValueError, RuntimeError, ImportError):
        return None


def _build_hero_summary(save: dict[str, Any], lang: str) -> dict[str, Any]:
    """Build clean hero loadout, amulet, currency, collectibles & materials from save data."""
    if not save or not save.get('ok'):
        return {
            'ok': False,
            'power_level': None,
            'gear_level': None,
            'loadout': {},
            'amulet': {},
            'wallet': {},
            'collectibles': {},
            'materials': [],
        }
    wallet = save.get('wallet') or {}
    pt = save.get('progression_tables') or {}
    hero_items = {str(k).lower(): v for k, v in (pt.get('hero_items') or {}).items()}

    # Build clean material list from KNOWN_RESOURCE_HASHES + wallet
    materials: list[dict[str, Any]] = []
    seen_keys: set[str] = set()
    for h_int, (key, ru_name, cat) in gowsave.KNOWN_RESOURCE_HASHES.items():
        if cat not in _MATERIAL_CATEGORIES or key in seen_keys:
            continue
        hk = f'0x{h_int:016x}'
        qty = hero_items.get(hk)
        if qty is None:
            qty = wallet.get(key)
        if isinstance(qty, (int, float)) and qty > 0:
            seen_keys.add(key)
            materials.append({
                'key': key,
                'name': ru_name if lang == 'ru' else _MATERIAL_EN.get(key, key.replace('_', ' ').title()),
                'category': cat,
                'qty': int(qty),
            })
    materials.sort(key=lambda m: (-m['qty'], m['name']))

    unused_flames = sum(
        int(wallet.get(k) or 0)
        for k in ('frozen_flame', 'chaos_flame', 'gale_flame')
        if isinstance(wallet.get(k), (int, float))
    )

    slot_labels = _SLOT_LABELS[lang]
    raw_loadout = save.get('loadout') or {}

    def clean_gear_group(group: dict[str, Any] | None) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        if not isinstance(group, dict):
            return out
        for slot_key, rec in group.items():
            if not isinstance(rec, dict):
                continue
            raw_name = rec.get('name_guess') or rec.get('name') or ''
            slot_lbl = slot_labels.get(slot_key, slot_key.replace('_', ' ').title())
            if lang == 'en':
                disp = _translate_gear_to_en(str(raw_name), slot_lbl)
            else:
                disp = raw_name or slot_lbl
            lvl = rec.get('level')
            out.append({
                'slot': slot_key,
                'label': slot_lbl,
                'name': disp,
                'level': int(lvl) if isinstance(lvl, (int, float)) and lvl > 0 else None,
            })
        return out

    raw_amulet = save.get('amulet') or {}
    clean_amulet = {
        'sockets_unlocked': raw_amulet.get('sockets_unlocked'),
        'sockets_total': raw_amulet.get('sockets_total', 9),
        'jewels_found': raw_amulet.get('jewels_found', 0),
    }

    raw_coll = save.get('collectibles') or {}
    ravens = raw_coll.get('ravens') or {}
    nornir = raw_coll.get('nornir_progress') or {}
    poems = raw_coll.get('kvasir_poems') or {}
    rtree = raw_coll.get('raven_tree') or {}
    stree = raw_coll.get('skill_tree') or {}
    clean_coll = {
        'ravens': {'collected': ravens.get('collected'), 'total': ravens.get('total', 48)},
        'nornir': {
            'opened': nornir.get('nornir_chests_opened'),
            'idunn_apples': nornir.get('idunn_apples_total', raw_coll.get('idunn_apples')),
            'blood_mead_horns': nornir.get('blood_mead_horns_total', raw_coll.get('blood_mead_horns')),
            'health_tier': nornir.get('health_tier'),
            'rage_tier': nornir.get('rage_tier'),
        },
        'kvasir_poems': {'collected': poems.get('collected'), 'total': poems.get('total', 14)},
        'raven_tree': {'opened': rtree.get('chests_opened'), 'total': rtree.get('chests_total', 6)},
        'skill_tree': {
            'unlocked': stree.get('unlocked_skills'),
            'total': stree.get('total_skills'),
            'percent': stree.get('progress_percent'),
        },
    }

    return {
        'ok': True,
        'power_level': save.get('power_level'),
        'gear_level': save.get('gear_level'),
        'gear_levels': [g for g in (save.get('gear_levels') or []) if isinstance(g, int) and g > 0],
        'loadout': {
            'weapons': clean_gear_group(raw_loadout.get('weapons')),
            'armor': clean_gear_group(raw_loadout.get('armor')),
            'shields': clean_gear_group(raw_loadout.get('shields')),
        },
        'amulet': clean_amulet,
        'wallet': {
            'hacksilver': wallet.get('wallet_hacksilver', save.get('hacksilver')),
            'divine_ashes': wallet.get('divine_ashes'),
            'kratos_xp': wallet.get('kratos_xp', save.get('xp')),
            'atreus_xp': wallet.get('atreus_xp'),
            'freya_xp': wallet.get('freya_xp'),
            'skills_count': wallet.get('skills_count', save.get('skills_count')),
            'unused_flames': unused_flames,
        },
        'collectibles': clean_coll,
        'materials': materials,
    }


def build_codex(save_data: dict[str, Any] | None = None, lang: str = 'en',
                catalog: dict[str, Any] | None = None,
                strings_primary: dict[int, str] | None = None,
                strings_fallback: dict[int, str] | None = None) -> dict[str, Any]:
    """Hydrate Bestiary, Lore, Skill Labors, Labors & Hero inventory for the requested language."""
    save = save_data or {}
    lang = 'ru' if str(lang).lower().startswith('ru') else 'en'
    pt = save.get('progression_tables') or (save.get('progress') or {}).get('progression_tables') or {}
    t2 = {str(k).lower(): v for k, v in (pt.get('table2_stage') or {}).items()}
    t1i = {str(k).lower(): v for k, v in (pt.get('table1_int') or {}).items()}
    has_save = bool(save.get('ok') or t2 or t1i)

    cat_data = catalog if catalog is not None else _base_dc_catalog()
    hero = _build_hero_summary(save, lang)

    if cat_data is None:
        return {
            'ok': True,
            'lang': lang,
            'game_data_available': False,
            'has_save': has_save,
            'bestiary': [],
            'bestiary_categories': [],
            'lore': [],
            'lore_categories': [],
            'treasures': [],
            'skills': [],
            'labors': [],
            'near_completion': [],
            'hero': hero,
            'summary': {
                'bestiary_unlocked': 0, 'bestiary_total': 0,
                'bestiary_main_unlocked': 0, 'bestiary_main_total': 0,
                'lore_unlocked': 0, 'lore_total': 0,
                'lore_main_unlocked': 0, 'lore_main_total': 0,
                'treasures_found': 0, 'treasures_dug': 0, 'treasures_total': 0,
                'skills_gold': 0, 'skills_total': 0,
                'labors_completed': 0, 'labors_total': 0,
            },
        }

    s_pri = strings_primary if strings_primary is not None else gow_story.load_story_strings(lang)
    s_fb = strings_fallback if strings_fallback is not None else (gow_story.load_story_strings('en') if lang != 'en' else s_pri)

    def txt(sid: int) -> str:
        if not sid:
            return ''
        return clean_game_text(s_pri.get(sid) or s_fb.get(sid) or '')

    kill_map = cat_data.get('kill_counters') or {}

    # 1. Bestiary
    bestiary_out: list[dict[str, Any]] = []
    b_cats_seen: dict[str, int] = {}
    for entry in cat_data.get('bestiary') or []:
        name = txt(entry['name_sid'])
        if not name or '*TEMP*' in name:
            continue
        desc = txt(entry['desc_sid'])
        cat_name = txt(entry['sub_sid']) or ('Прочие' if lang == 'ru' else 'Other')
        stage = t2.get(entry['hash'])
        unlocked = stage in (2, 4)
        tips_out = []
        for tip in entry.get('tips') or []:
            t_text = txt(tip['name_sid']) or txt(tip['desc_sid'])
            if not t_text or '*TEMP*' in t_text:
                continue
            tips_out.append({
                'id': tip['id'],
                'text': t_text,
                'unlocked': t2.get(tip['hash']) in (2, 4),
            })
        fam = entry.get('family')
        kills = t1i.get(kill_map[fam]) if fam and fam in kill_map else None
        b_cats_seen[cat_name] = b_cats_seen.get(cat_name, 0) + 1
        bestiary_out.append({
            'id': entry['id'],
            'name': name,
            'category': cat_name,
            'description': desc,
            'unlocked': unlocked,
            'stage': stage,
            'is_valhalla': bool(entry.get('is_valhalla')),
            'icon': f"/api/codex/icon/{entry['icon_key']}.png" if entry.get('icon_key') else None,
            'family': fam,
            'family_kills': int(kills) if isinstance(kills, (int, float)) else None,
            'tips': tips_out,
            'tips_unlocked': sum(1 for t in tips_out if t['unlocked']),
        })

    # 2. Lore
    lore_out: list[dict[str, Any]] = []
    l_cats_seen: dict[str, int] = {}
    for entry in cat_data.get('lore') or []:
        name = txt(entry['name_sid'])
        desc = txt(entry['desc_sid'])
        if not name or '*TEMP*' in name or '*TEMP*' in desc:
            continue
        cat_name = txt(entry['sub_sid']) or ('Легенды' if lang == 'ru' else 'Lore')
        stage = t2.get(entry['hash'])
        unlocked = stage in (2, 4)
        updates_out = []
        for up in entry.get('updates') or []:
            u_text = txt(up['desc_sid']) or txt(up['name_sid'])
            if not u_text or '*TEMP*' in u_text or u_text == desc:
                continue
            updates_out.append({
                'id': up['id'],
                'text': u_text,
                'unlocked': t2.get(up['hash']) in (2, 4),
            })
        l_cats_seen[cat_name] = l_cats_seen.get(cat_name, 0) + 1
        lore_out.append({
            'id': entry['id'],
            'name': name,
            'category': cat_name,
            'description': desc,
            'unlocked': unlocked,
            'is_valhalla': bool(entry.get('is_valhalla')),
            'icon': f"/api/codex/icon/{entry['icon_key']}.png" if entry.get('icon_key') else None,
            'updates': updates_out,
        })

    # 2b. Treasure Maps & Buried Treasures
    treasures_out: list[dict[str, Any]] = []
    for entry in cat_data.get('treasures') or []:
        name = txt(entry['name_sid'])
        if not name or '*TEMP*' in name:
            continue
        desc = txt(entry['desc_sid'])
        st = t2.get(entry['hash'])
        if st is None and entry.get('step_hash'):
            st = t2.get(entry['step_hash'])
        if st == 4:
            status = 'dug'
        elif st == 2:
            status = 'active'
        else:
            status = 'unfound'
        treasures_out.append({
            'id': entry['id'],
            'name': name,
            'description': desc,
            'status': status,
            'unlocked': status in ('active', 'dug'),
            'dug': status == 'dug',
            'icon': f"/api/codex/icon/{entry['icon_key']}.png" if entry.get('icon_key') else None,
        })

    # 3. Skill Labors (49 weapon skills)
    skills_out: list[dict[str, Any]] = []
    near_completion: list[dict[str, Any]] = []
    w_labels = _WEAPON_LABELS[lang]
    t_labels = _TIER_LABELS[lang]
    for entry in cat_data.get('skills') or []:
        tiers_out = []
        best_done = 0
        next_tier = None
        completed_tiers = 0
        for t_rec in entry.get('tiers') or []:
            st = t2.get(t_rec['hash'])
            done_flag = st == 4
            val = t1i.get(t_rec['counter_hash']) if t_rec.get('counter_hash') else None
            tot = int(t_rec['total']) if t_rec.get('total') else 0
            cur = int(val) if isinstance(val, (int, float)) else (tot if done_flag else 0)
            best_done = max(best_done, cur)
            if done_flag or (tot > 0 and cur >= tot):
                completed_tiers += 1
            elif next_tier is None and tot > 0:
                next_tier = {
                    'tier': t_rec['tier'],
                    'tier_label': txt(t_rec['name_sid']) or t_labels.get(t_rec['tier'], t_rec['tier']),
                    'done': min(cur, tot),
                    'total': tot,
                    'remaining': max(0, tot - cur),
                }
            tiers_out.append({
                'tier': t_rec['tier'],
                'tier_label': txt(t_rec['name_sid']) or t_labels.get(t_rec['tier'], t_rec['tier']),
                'done': min(cur, tot) if tot else cur,
                'total': tot,
                'completed': done_flag or (tot > 0 and cur >= tot),
            })
        max_tot = max((t['total'] for t in tiers_out), default=0)
        is_gold = completed_tiers >= len(tiers_out) and len(tiers_out) > 0
        skill_name = txt(entry.get('name_sid') or 0) or entry['label']
        skill_obj = {
            'id': entry['id'],
            'name': skill_name,
            'weapon': entry['weapon'],
            'weapon_label': w_labels.get(entry['weapon'], entry['weapon']),
            'done': best_done,
            'max_total': max_tot,
            'completed': is_gold,
            'next_tier': next_tier,
            'tiers': tiers_out,
        }
        skills_out.append(skill_obj)
        if next_tier and next_tier['done'] > 0 and next_tier['remaining'] > 0:
            near_completion.append({
                'kind': 'skill',
                'id': entry['id'],
                'name': f"{w_labels.get(entry['weapon'], '')}: {skill_name}".strip(': '),
                'tier_label': next_tier['tier_label'],
                'done': next_tier['done'],
                'total': next_tier['total'],
                'remaining': next_tier['remaining'],
                'ratio': next_tier['done'] / max(1, next_tier['total']),
            })

    # 4. General Labors (Kills, Trials, Crafting, Ratatoskr)
    labors_out: list[dict[str, Any]] = []
    for entry in cat_data.get('labors') or []:
        name = txt(entry['name_sid'])
        if not name or '*TEMP*' in name:
            continue
        cat_name = txt(entry['sub_sid']) or ('Труды' if lang == 'ru' else 'Labors')
        tiers_out = []
        next_tier = None
        completed_tiers = 0
        for t_rec in entry.get('tiers') or []:
            st = t2.get(t_rec['hash'])
            done_flag = st == 4
            val = t1i.get(t_rec['counter_hash']) if t_rec.get('counter_hash') else None
            tot = int(t_rec['total']) if t_rec.get('total') else 0
            cur = int(val) if isinstance(val, (int, float)) else (tot if done_flag else 0)
            t_label = txt(t_rec['name_sid']) or ''
            t_desc = txt(t_rec['desc_sid'])
            if '%d' in t_desc and tot:
                try:
                    t_desc = t_desc.replace('%d', str(min(cur, tot)), 1).replace('%d', str(tot), 1)
                except ValueError:
                    pass
            if done_flag or (tot > 0 and cur >= tot):
                completed_tiers += 1
            elif next_tier is None and tot > 0:
                next_tier = {
                    'tier_label': t_label,
                    'desc': t_desc,
                    'done': min(cur, tot),
                    'total': tot,
                    'remaining': max(0, tot - cur),
                }
            tiers_out.append({
                'id': t_rec['id'],
                'tier_label': t_label,
                'desc': t_desc,
                'done': min(cur, tot) if tot else cur,
                'total': tot,
                'completed': done_flag or (tot > 0 and cur >= tot),
            })
        is_done = completed_tiers >= len(tiers_out) and len(tiers_out) > 0
        labors_out.append({
            'id': entry['id'],
            'name': name,
            'category': cat_name,
            'is_ngp': bool(entry.get('is_ngp')),
            'is_valhalla': bool(entry.get('is_valhalla')),
            'completed': is_done,
            'next_tier': next_tier,
            'tiers': tiers_out,
        })
        if next_tier and not entry.get('is_ngp') and next_tier['done'] > 0 and next_tier['remaining'] > 0:
            near_completion.append({
                'kind': 'labor',
                'id': entry['id'],
                'name': name,
                'tier_label': next_tier['tier_label'],
                'done': next_tier['done'],
                'total': next_tier['total'],
                'remaining': next_tier['remaining'],
                'ratio': next_tier['done'] / max(1, next_tier['total']),
            })

    near_completion.sort(key=lambda x: (-x['ratio'], x['remaining'], x['name']))

    main_b = [b for b in bestiary_out if not b['is_valhalla']]
    main_l = [l for l in lore_out if not l['is_valhalla']]
    summary = {
        'bestiary_unlocked': sum(1 for b in bestiary_out if b['unlocked']),
        'bestiary_total': len(bestiary_out),
        'bestiary_main_unlocked': sum(1 for b in main_b if b['unlocked']),
        'bestiary_main_total': len(main_b),
        'lore_unlocked': sum(1 for l in lore_out if l['unlocked']),
        'lore_total': len(lore_out),
        'lore_main_unlocked': sum(1 for l in main_l if l['unlocked']),
        'lore_main_total': len(main_l),
        'treasures_found': sum(1 for tr in treasures_out if tr['unlocked']),
        'treasures_dug': sum(1 for tr in treasures_out if tr['dug']),
        'treasures_total': len(treasures_out),
        'skills_gold': sum(1 for s in skills_out if s['completed']),
        'skills_total': len(skills_out),
        'labors_completed': sum(1 for l in labors_out if l['completed']),
        'labors_total': len(labors_out),
    }

    return {
        'ok': True,
        'lang': lang,
        'game_data_available': True,
        'has_save': has_save,
        'bestiary': bestiary_out,
        'bestiary_categories': sorted(b_cats_seen.keys()),
        'lore': lore_out,
        'lore_categories': sorted(l_cats_seen.keys()),
        'treasures': treasures_out,
        'skills': skills_out,
        'labors': labors_out,
        'near_completion': near_completion[:10],
        'hero': hero,
        'summary': summary,
        'updated_at': int(time.time()),
    }


_HERO_CAT_ORDER = (
    'odins_raven', 'nornir_chest', 'legendary_chest', 'lore', 'artifact',
    'favor', 'boss', 'berserker_gravestone', 'yggdrasil_rift', 'hel_tear',
    'remnant_of_asgard', 'draugr_hole', 'buried_treasure', 'nine_realms_in_bloom', 'kvasirs_poem',
)
_ENEMY_PIN_CATS = {'boss', 'berserker_gravestone', 'sleeping_troll', 'draugr_hole', 'kol_raider_camp'}


def attach_map_links(codex: dict[str, Any], save_data: dict[str, Any] | None, lang: str,
                     realms: tuple[str, ...]) -> dict[str, Any]:
    """Attach proven 9-realm category totals to hero and cross-link boss/enemy pins into Bestiary & Lore."""
    import gow_pins
    from i18n import t as tr_srv

    cat_totals: dict[str, dict[str, Any]] = {}
    enemy_pins: list[tuple[str, str, dict[str, Any], str]] = []
    tmap_pins: list[tuple[str, str, dict[str, Any], str]] = []
    tdig_pins: list[tuple[str, str, dict[str, Any], str]] = []
    norm = lambda s: re.sub(r'[^a-z0-9\u0400-\u04ff]+', ' ', str(s or '').lower()).strip()

    for realm in realms:
        pois = gow_pins.get_realm_pois(realm, save_data=save_data, lang=lang)
        r_name = tr_srv(realm, lang)
        for p in pois:
            ck = p.get('category_key')
            if p.get('is_completionist') and ck:
                rec = cat_totals.setdefault(ck, {'key': ck, 'name': p.get('category') or ck, 'collected': 0, 'total': 0})
                rec['total'] += 1
                if p.get('status') == 'collected' or p.get('is_collected'):
                    rec['collected'] += 1
            if ck in _ENEMY_PIN_CATS and p.get('name'):
                pn = norm(p['name'])
                if len(pn) >= 3:
                    enemy_pins.append((realm, r_name, p, pn))
            elif ck == 'treasure_map' and p.get('name'):
                tmap_pins.append((realm, r_name, p, norm(p['name'])))
            elif ck == 'buried_treasure' and p.get('name'):
                tdig_pins.append((realm, r_name, p, norm(p['name'])))

    hero = codex.get('hero')
    if isinstance(hero, dict):
        ordered = [cat_totals[k] for k in _HERO_CAT_ORDER if k in cat_totals]
        hero['realm_categories'] = ordered

    # Pair all 10 Treasure Maps with their exact map-scroll pickup pin & buried-treasure dig pin
    def _pin_ref(realm: str, r_name: str, p: dict[str, Any]) -> dict[str, Any]:
        return {
            'realm': realm,
            'realm_name': r_name,
            'id': p['id'],
            'name': p['name'],
            'region': p.get('region') or '',
            'collected': bool(p.get('status') == 'collected' or p.get('is_collected')),
        }

    for tr_entry in codex.get('treasures') or []:
        tn = norm(tr_entry.get('name'))
        if not tn:
            continue
        mp = next(((rl, rn, p) for rl, rn, p, pn in tmap_pins if tn == pn or tn in pn), None)
        dp = next(((rl, rn, p) for rl, rn, p, pn in tdig_pins if tn == pn or tn in pn), None)
        if mp:
            tr_entry['map_pin'] = _pin_ref(*mp)
        if dp:
            tr_entry['dig_pin'] = _pin_ref(*dp)

    def _word_match(short: str, long: str) -> bool:
        if len(short) < 4:
            return False
        return bool(re.search(rf'(?:^|\s){re.escape(short)}(?:$|\s)', long))

    if enemy_pins:
        for sec in ('bestiary', 'lore'):
            for entry in codex.get(sec) or []:
                if entry.get('is_valhalla'):
                    continue
                en_norm = norm(entry.get('name'))
                if len(en_norm) < 3:
                    continue
                exact = []
                partial = []
                seen_ids: set[str] = set()
                for realm, r_name, p, pn in enemy_pins:
                    pid = f"{realm}:{p['id']}"
                    if pid in seen_ids:
                        continue
                    hit = None
                    if pn == en_norm:
                        hit = exact
                    elif _word_match(en_norm, pn) or _word_match(pn, en_norm):
                        hit = partial
                    if hit is not None:
                        seen_ids.add(pid)
                        hit.append({
                            'realm': realm,
                            'realm_name': r_name,
                            'id': p['id'],
                            'name': p['name'],
                            'collected': bool(p.get('status') == 'collected' or p.get('is_collected')),
                        })
                links = (exact or partial)[:4]
                if links:
                    entry['map_pins'] = links
    return codex


def codex_snapshot(codex: dict[str, Any]) -> dict[str, Any]:
    """Extract a lightweight diffable snapshot of unlocked entries & counts."""
    return {
        'bestiary': {b['id']: b['name'] for b in codex.get('bestiary') or [] if b.get('unlocked')},
        'tips': {
            f"{b['id']}:{t['id']}": {'entry_id': b['id'], 'entry_name': b['name'], 'text': t['text']}
            for b in codex.get('bestiary') or []
            for t in b.get('tips') or []
            if t.get('unlocked')
        },
        'lore': {l['id']: {'name': l['name'], 'category': l['category']} for l in codex.get('lore') or [] if l.get('unlocked')},
        'treasures': {tr['id']: {'name': tr['name'], 'status': tr['status']} for tr in codex.get('treasures') or [] if tr.get('unlocked')},
        'skills': {s['id']: {'name': s['name'], 'done': s['done'], 'completed': s['completed']} for s in codex.get('skills') or []},
    }


def compute_codex_diff(prev: dict[str, Any] | None, curr: dict[str, Any]) -> dict[str, Any]:
    """Compute newly unlocked Bestiary entries, combat tips, Lore, Treasures & skill rank ups."""
    if not prev:
        return {'has_changes': False, 'new_bestiary': [], 'new_tips': [], 'new_lore': [], 'new_treasures': [], 'skill_updates': []}
    prev_b = prev.get('bestiary') or {}
    curr_b = curr.get('bestiary') or {}
    new_b = [{'id': k, 'name': v} for k, v in curr_b.items() if k not in prev_b]

    prev_t = prev.get('tips') or {}
    curr_t = curr.get('tips') or {}
    new_t = [v for k, v in curr_t.items() if k not in prev_t]

    prev_l = prev.get('lore') or {}
    curr_l = curr.get('lore') or {}
    new_l = [{'id': k, 'name': v['name'], 'category': v['category']} for k, v in curr_l.items() if k not in prev_l]

    prev_tr = prev.get('treasures') or {}
    curr_tr = curr.get('treasures') or {}
    new_tr = [
        {'id': k, 'name': v['name'], 'status': v['status']}
        for k, v in curr_tr.items()
        if k not in prev_tr or prev_tr[k].get('status') != v.get('status')
    ]

    prev_s = prev.get('skills') or {}
    curr_s = curr.get('skills') or {}
    skill_up = []
    for k, v in curr_s.items():
        old = prev_s.get(k)
        if old and (v['done'] > old['done'] or (v['completed'] and not old['completed'])):
            skill_up.append({'id': k, 'name': v['name'], 'done': v['done'], 'completed': v['completed']})

    has_changes = bool(new_b or new_t or new_l or new_tr or skill_up)
    return {
        'has_changes': has_changes,
        'new_bestiary': new_b[:8],
        'new_tips': new_t[:8],
        'new_lore': new_l[:8],
        'new_treasures': new_tr[:6],
        'skill_updates': skill_up[:6],
    }


def get_codex_icon_png(icon_key: str, cache_dir: Path | None = None,
                       catalog: dict[str, Any] | None = None,
                       ink: str = 'gold') -> bytes | None:
    """Return cached portrait/clue PNG for a Codex entry (`ink='dark'` charcoal for book, `'gold'` for dark UI)."""
    if not ICON_KEY_RE.match(icon_key):
        return None
    ink = 'dark' if ink == 'dark' else 'gold'
    is_clue = icon_key.startswith('treasuremap_')
    out_dir = Path(cache_dir) if cache_dir is not None else ICON_CACHE_DIR
    suffix = '' if (ink == 'gold' or is_clue) else '_dark'
    target = out_dir / f'{icon_key}{suffix}.png'
    if target.is_file():
        cached = target.read_bytes()
        if cached.startswith(b'\x89PNG\r\n\x1a\n') and len(cached) > 32:
            return cached
    miss = out_dir / f'{icon_key}.none'
    if miss.is_file():
        return None
    if not paths.find_game_dir():
        return None

    cat_data = catalog if catalog is not None else _base_dc_catalog()
    if not cat_data:
        return None
    tx_name = (cat_data.get('icon_to_tx') or {}).get(icon_key)
    if not tx_name:
        return None

    with _ICON_LOCK:
        if target.is_file():
            cached = target.read_bytes()
            if cached.startswith(b'\x89PNG\r\n\x1a\n') and len(cached) > 32:
                return cached
        try:
            import numpy as np
            from PIL import Image
            from tools import gow_texpack

            extracted = gow_texpack.extract([tx_name]).get(tx_name)
            out_dir.mkdir(parents=True, exist_ok=True)
            if not extracted:
                miss.write_bytes(b'')
                return None
            _, arr = extracted
            if is_clue and arr.ndim == 2:
                # Treasure map clue painting: map luminance into rich charcoal-to-parchment sepia tones
                t = np.clip(arr.astype(np.float32) / 255.0, 0.0, 1.0) ** 0.92
                rgb = np.empty((arr.shape[0], arr.shape[1], 3), dtype=np.uint8)
                rgb[..., 0] = np.clip(28 + t * 204, 0, 255).astype(np.uint8)
                rgb[..., 1] = np.clip(24 + t * 192, 0, 255).astype(np.uint8)
                rgb[..., 2] = np.clip(20 + t * 166, 0, 255).astype(np.uint8)
                img = Image.fromarray(rgb, 'RGB')
                img.thumbnail((640, 360), Image.LANCZOS)
            elif arr.ndim == 2:
                # Monochrome BC4 sketch from Kratos/Atreus journal -> dark charcoal ink (book) or gilded ink (dark UI)
                gamma = 0.62 if ink == 'dark' else 0.68
                a = np.clip((arr.astype(np.float32) / 255.0) ** gamma * 255.0, 0, 255).astype(np.uint8)
                rgba = np.empty((arr.shape[0], arr.shape[1], 4), dtype=np.uint8)
                if ink == 'dark':
                    rgba[..., 0] = 28
                    rgba[..., 1] = 25
                    rgba[..., 2] = 21
                else:
                    rgba[..., 0] = 232
                    rgba[..., 1] = 198
                    rgba[..., 2] = 126
                rgba[..., 3] = a
                img = Image.fromarray(rgba, 'RGBA')
                bbox = img.getbbox()
                if bbox:
                    w, h = img.size
                    pad = max(12, int(min(w, h) * 0.04))
                    img = img.crop((max(0, bbox[0] - pad), max(0, bbox[1] - pad),
                                    min(w, bbox[2] + pad), min(h, bbox[3] + pad)))
                img.thumbnail((512 if ink == 'dark' else 384, 512 if ink == 'dark' else 384), Image.LANCZOS)
            else:
                img = Image.fromarray(arr.astype(np.uint8), 'RGBA' if arr.shape[2] == 4 else 'RGB').convert('RGBA')
                bbox = img.getbbox()
                if bbox:
                    w, h = img.size
                    pad = max(12, int(min(w, h) * 0.04))
                    img = img.crop((max(0, bbox[0] - pad), max(0, bbox[1] - pad),
                                    min(w, bbox[2] + pad), min(h, bbox[3] + pad)))
                img.thumbnail((420, 420), Image.LANCZOS)

            buf = io.BytesIO()
            img.save(buf, 'PNG', optimize=True)
            data = buf.getvalue()
            tmp = target.with_suffix('.tmp')
            tmp.write_bytes(data)
            tmp.replace(target)
            return data
        except (ImportError, OSError, ValueError, RuntimeError):
            return None


def get_codex_book_asset_png(asset: str, cache_dir: Path | None = None) -> bytes | None:
    """Return cached journal book parchment/flap/cover/watermark PNG extracted from local game files."""
    tx_name = BOOK_ASSETS.get(asset)
    if not tx_name:
        return None
    out_dir = Path(cache_dir) if cache_dir is not None else ICON_CACHE_DIR
    target = out_dir / f'_book_{asset}.png'
    if target.is_file():
        cached = target.read_bytes()
        if cached.startswith(b'\x89PNG\r\n\x1a\n') and len(cached) > 32:
            return cached
    if not paths.find_game_dir():
        return None

    with _ICON_LOCK:
        if target.is_file():
            cached = target.read_bytes()
            if cached.startswith(b'\x89PNG\r\n\x1a\n') and len(cached) > 32:
                return cached
        try:
            import numpy as np
            from PIL import Image
            from tools import gow_texpack

            need = [tx_name, _BOOK_FLAP_MASK] if asset == 'flap' else [tx_name]
            res = gow_texpack.extract(need)
            got = res.get(tx_name)
            if not got:
                return None
            out_dir.mkdir(parents=True, exist_ok=True)
            _, arr = got
            if asset == 'flap':
                rgb = arr[..., :3].astype(np.float32)
                # Match the game's cool weathered linen parchment lighting
                rgb[..., 0] = np.clip(rgb[..., 0] * 0.935, 0, 255)
                rgb[..., 1] = np.clip(rgb[..., 1] * 0.960, 0, 255)
                rgb[..., 2] = np.clip(rgb[..., 2] * 1.000, 0, 255)
                mask_got = res.get(_BOOK_FLAP_MASK)
                if mask_got is not None and mask_got[1].ndim == 2:
                    alpha = mask_got[1].astype(np.uint8)
                else:
                    alpha = np.where(rgb.max(axis=2) > 16, 255, 0).astype(np.uint8)
                # Subtle binding overlap shadow on the left edge where the flap tucks under the right page
                fw = rgb.shape[1]
                lx = np.linspace(0.0, 1.0, fw, dtype=np.float32)[None, :, None]
                shadow = 0.62 + 0.38 * np.clip(lx / 0.14, 0.0, 1.0)
                rgb = np.clip(rgb * shadow, 0, 255)
                rgba = np.dstack([rgb.astype(np.uint8), alpha])
                img = Image.fromarray(rgba, 'RGBA')
                bbox = img.getbbox()
                if bbox:
                    img = img.crop(bbox)
                img.thumbnail((880, 1040), Image.LANCZOS)
            elif asset == 'page':
                out_arr = arr.astype(np.float32)
                out_arr[..., 0] = np.clip(out_arr[..., 0] * 0.940, 0, 255)
                out_arr[..., 1] = np.clip(out_arr[..., 1] * 0.962, 0, 255)
                out_arr[..., 2] = np.clip(out_arr[..., 2] * 1.005, 0, 255)
                # Deepen natural page-crease shading along the inner binding edge (left side of texture)
                pw = out_arr.shape[1]
                gx = np.linspace(0.0, 1.0, pw, dtype=np.float32)[None, :, None]
                crease = 0.56 + 0.44 * np.clip(gx / 0.11, 0.0, 1.0) ** 0.72
                out_arr[..., :3] = np.clip(out_arr[..., :3] * crease, 0, 255)
                img = Image.fromarray(out_arr.astype(np.uint8), 'RGBA' if arr.shape[2] == 4 else 'RGB')
                bbox = img.getbbox()
                if bbox:
                    img = img.crop(bbox)
                img.thumbnail((1152, 1152), Image.LANCZOS)
            elif asset == 'cover_frame':
                # Build an open two-page dark braided-leather cover + top spine clasp from sonjournalui00_cover
                h_c, w_c = arr.shape[:2]
                y0, y1 = int(h_c * 0.175), int(h_c * 0.985)
                x0, x1 = int(w_c * 0.312), int(w_c * 0.988)
                panel = arr[y0:y1, x0:x1, :3].astype(np.float32)
                ph, pw = panel.shape[:2]
                # Mask out flat tan UV background around outer-right rounded corners
                alpha_p = np.full((ph, pw), 255.0, dtype=np.float32)
                corner_r = max(32, int(min(ph, pw) * 0.135))
                for cy_c, cx_c in ((corner_r, pw - 1 - corner_r), (ph - 1 - corner_r, pw - 1 - corner_r)):
                    ys_b = slice(0, corner_r) if cy_c == corner_r else slice(ph - corner_r, ph)
                    xs_b = slice(pw - corner_r, pw)
                    gy, gx = np.mgrid[ys_b, xs_b]
                    dist = np.hypot(gy - cy_c, gx - cx_c)
                    fade = np.clip((corner_r - 1.5 - dist) / 3.0, 0.0, 1.0)
                    alpha_p[ys_b, xs_b] *= fade
                # Rich dark-leather tone so the thin braided rim matches the in-game book
                yy, xx = np.mgrid[0:ph, 0:pw]
                in_y = (yy > int(ph * 0.075)) & (yy < int(ph * 0.925))
                in_x = (xx > int(pw * 0.095)) & (xx < int(pw * 0.905))
                inner = in_y & in_x
                panel[inner] *= 0.16
                panel[~inner] *= 0.64
                rgba_p = np.dstack([np.clip(panel, 0, 255), alpha_p])
                right_half = rgba_p[:, int(pw * 0.04):, :]
                left_half = right_half[:, ::-1, :]
                spine_w = max(14, int(pw * 0.03))
                spine = np.empty((ph, spine_w, 4), dtype=np.float32)
                spine[..., :3] = [18, 13, 10]
                spine[..., 3] = 255.0
                spread = np.concatenate([left_half, spine, right_half], axis=1)
                # Composite the blue-grey leather spine clasp from the top-left of sonjournalui00_cover
                clasp_src = arr[int(h_c * 0.01):int(h_c * 0.165), int(w_c * 0.015):int(w_c * 0.315), :3].astype(np.float32)
                clasp_im = Image.fromarray(np.clip(clasp_src * 0.85, 0, 255).astype(np.uint8), 'RGB')
                cw = max(48, int(spread.shape[1] * 0.095))
                ch = max(24, int(spread.shape[0] * 0.048))
                clasp_im = clasp_im.resize((cw, ch), Image.LANCZOS)
                cx0 = (spread.shape[1] - cw) // 2
                ca = np.array(clasp_im, dtype=np.float32)
                # Taper clasp slightly toward the bottom
                cy_g, cx_g = np.mgrid[0:ch, 0:cw]
                edge_m = np.clip((cw * 0.5 - np.abs(cx_g - cw * 0.5) - cy_g * 0.18) / 3.0, 0.0, 1.0)
                for c_idx in range(3):
                    spread[:ch, cx0:cx0 + cw, c_idx] = (
                        spread[:ch, cx0:cx0 + cw, c_idx] * (1.0 - edge_m) + ca[..., c_idx] * edge_m
                    )
                spread[:ch, cx0:cx0 + cw, 3] = np.maximum(spread[:ch, cx0:cx0 + cw, 3], edge_m * 255.0)
                img = Image.fromarray(np.clip(spread, 0, 255).astype(np.uint8), 'RGBA')
                img.thumbnail((1400, 1040), Image.LANCZOS)
            elif asset == 'header_brush':
                a = np.clip((arr.astype(np.float32) / 255.0) ** 0.72 * 246.0, 0, 255).astype(np.uint8)
                rgba = np.empty((arr.shape[0], arr.shape[1], 4), dtype=np.uint8)
                rgba[..., 0] = 26
                rgba[..., 1] = 25
                rgba[..., 2] = 23
                rgba[..., 3] = a
                img = Image.fromarray(rgba, 'RGBA')
                bbox = img.getbbox()
                if bbox:
                    img = img.crop(bbox)
                img.thumbnail((768, 192), Image.LANCZOS)
            elif asset == 'row_brush':
                af = (arr.astype(np.float32) / 255.0) ** 0.70
                # Smooth dry-brush fade on the right third, matching the active entry highlight in-game
                fade = np.linspace(1.0, 0.0, arr.shape[1], dtype=np.float32)
                fade = np.clip((fade - 0.02) / 0.36, 0.0, 1.0)[None, :]
                a = np.clip(af * fade * 248.0, 0, 255).astype(np.uint8)
                rgba = np.empty((arr.shape[0], arr.shape[1], 4), dtype=np.uint8)
                rgba[..., 0] = 21
                rgba[..., 1] = 20
                rgba[..., 2] = 18
                rgba[..., 3] = a
                img = Image.fromarray(rgba, 'RGBA')
                bbox = img.getbbox()
                if bbox:
                    img = img.crop(bbox)
                img.thumbnail((768, 160), Image.LANCZOS)
            elif asset == 'cover':
                img = Image.fromarray(arr[..., :3].astype(np.uint8), 'RGB')
                img.thumbnail((768, 768), Image.LANCZOS)
            else:
                # Re-center wrapped BC4 emblem texture (half-width shifted in WAD) for subtle parchment watermark
                centered = np.roll(arr, arr.shape[1] // 2, axis=1)
                a = np.clip((centered.astype(np.float32) / 255.0) * 76.0, 0, 255).astype(np.uint8)
                rgba = np.empty((centered.shape[0], centered.shape[1], 4), dtype=np.uint8)
                rgba[..., 0] = 56
                rgba[..., 1] = 52
                rgba[..., 2] = 46
                rgba[..., 3] = a
                img = Image.fromarray(rgba, 'RGBA')

            buf = io.BytesIO()
            img.save(buf, 'PNG', optimize=True)
            data = buf.getvalue()
            tmp = target.with_suffix('.tmp')
            tmp.write_bytes(data)
            tmp.replace(target)
            return data
        except (ImportError, OSError, ValueError, RuntimeError):
            return None
