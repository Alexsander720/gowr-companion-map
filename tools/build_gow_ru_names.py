"""Match English pin titles to Russian strings by shared game localization IDs."""
from __future__ import annotations

import collections
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import gowassets  # noqa: E402

from paths import PINS as DATA, wad_dir
REALMS = ("midgard", "vanaheim", "svartalfheim", "alfheim", "helheim", "jotunheim",
          "asgard", "niflheim", "muspelheim", "sindris-house")

# Имена, которых нет среди строк игры (у сундуков/горшков нет подписи в UI).
GLOSSARY = {}


# MapGenie и игра иногда расходятся в числе: «Casualty of War: The Toy» у MapGenie,
# «Casualties of War: The Toy» в строках игры (у брошки/кружки/свитка — единственное).
ALT_FORMS = (("casualty of war", "casualties of war"),)


def norm(text: str) -> str:
    text = text.replace("’", "'").replace("‘", "'").replace("`", "'").replace("–", "-").replace("—", "-")
    text = "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", text).strip().lower()


def load_localization():
    base = wad_dir()
    ru = gowassets.read_language_strings(base / 'r_lang_ru.wad')
    en = gowassets.read_language_strings(base / "r_lang_en.wad")
    if not ru or not en:
        return {}, {}
    exact, loose = collections.defaultdict(set), collections.defaultdict(set)
    for sid, text in en.items():
        t = text.strip()
        r = (ru.get(sid) or "").strip()
        if not t or not r or len(t) > 120 or "\n" in t:
            continue
        exact[t].add(r)
        loose[norm(t)].add(r)
    return exact, loose


def pick(values):
    """Одно значение или None, если строки игры расходятся."""
    values = {v for v in values if v}
    return next(iter(values)) if len(values) == 1 else None


def translate(title: str, exact, loose):
    t = title.strip()
    if t in exact and pick(exact[t]):
        return pick(exact[t]), "game_loc"
    if norm(t) in loose and pick(loose[norm(t)]):
        return pick(loose[norm(t)]), "normalized"
    for a, b in ALT_FORMS:
        for x, y in ((a, b), (b, a)):
            alt = norm(t).replace(x, y)
            if alt != norm(t) and alt in loose and pick(loose[alt]):
                return pick(loose[alt]), "normalized"
    m = re.match(r"^(.*?)\s*\[(\d+)\]$", t)
    if m:
        ru, src = translate(m.group(1), exact, loose)
        if ru:
            return f"{ru} [{m.group(2)}]", "pattern" if src != "pending" else src
    m = re.match(r"^(.*?)\s+x(\d+)$", t)
    if m:
        ru, src = translate(m.group(1), exact, loose)
        if ru:
            return f"{ru} ×{m.group(2)}", "pattern"
    m = re.match(r"^(.*?) Set \((\w+)\)$", t)
    if m:
        for cand in (f"{m.group(1)} Armor Set", f"{m.group(1)} Set", m.group(1)):
            if norm(cand) in loose and pick(loose[norm(cand)]):
                return pick(loose[norm(cand)]), "pattern"
    m = re.match(r"^(.*?) \((Kratos|Atreus|Freya)\)$", t)
    if m:
        ru, src = translate(m.group(1), exact, loose)
        if ru:
            return ru, "pattern"
    if " - " in t:
        head, tail = t.split(" - ", 1)
        ru_head, s1 = translate(head, exact, loose)
        ru_tail, s2 = translate(tail, exact, loose)
        if ru_head and ru_tail:
            return f"{ru_head}: {ru_tail}", "pattern"
    if norm(t) in GLOSSARY:
        return GLOSSARY[norm(t)], "glossary"
    return None, "pending"


def build_names():
    from paths import atomic_json
    base = wad_dir()
    files = [base / 'r_lang_en.wad', base / 'r_lang_ru.wad']
    if not all(f.is_file() for f in files):
        return {}
    stamp = [(f.stat().st_size, f.stat().st_mtime_ns) for f in files]
    stamp += [(str(p.name), p.stat().st_size, p.stat().st_mtime_ns) for p in sorted(DATA.glob('*.json'))
              if p.stem in REALMS]
    key = json.dumps(stamp)
    target = DATA / 'ru_names.json'
    status = DATA / 'localization.status.json'
    if target.is_file() and status.is_file():
        try:
            if json.loads(status.read_text(encoding='utf-8')).get('stamp') == key:
                return json.loads(target.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            pass
    exact, loose = load_localization()
    out = {}
    for realm in REALMS:
        path = DATA / f'{realm}.json'
        if not path.is_file():
            continue
        for loc in json.loads(path.read_text(encoding='utf-8')).get('locations', []):
            title = (loc.get('title') or '').strip()
            if not title:
                continue
            ru, source = translate(title, exact, loose)
            out[str(loc['id'])] = {'ru': ru, 'en': title, 'source': source, 'realm': realm}
    atomic_json(target, out)
    atomic_json(status, {'stamp': key})
    return out


def main():
    import argparse
    import paths
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-dir', type=Path)
    args = parser.parse_args()
    if args.game_dir:
        paths.GAME_DIR = paths.find_game_dir(args.game_dir)
    result = build_names()
    print('Localized pins:', sum(bool(v.get('ru')) for v in result.values()), '/', len(result))


if __name__ == '__main__':
    main()
