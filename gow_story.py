"""Resolve journal string identifiers from the installed game, without bundled prose."""
from functools import lru_cache
import hashlib
import json
import paths


def load_story_strings(lang='ru'):
    source = paths.wad_dir() / f'r_lang_{lang}.wad'
    if not source.is_file():
        return {}
    info = source.stat()
    return _load_strings(lang, str(source), info.st_size, info.st_mtime_ns, str(paths.CACHE))


@lru_cache(maxsize=8)
def _load_strings(lang, source_path, size, mtime, cache_root):
    from pathlib import Path
    source = Path(source_path)
    stamp = f'{size}:{mtime}'
    key = hashlib.sha256(str(source).encode()).hexdigest()[:16]
    target = Path(cache_root) / f'localization-{lang}-{key}.json'
    if target.is_file():
        try:
            doc = json.loads(target.read_text(encoding='utf-8'))
            if doc['stamp'] == stamp:
                return {int(k): v for k, v in doc['strings'].items()}
        except (OSError, ValueError, KeyError):
            pass
    from gowassets import read_language_strings
    strings = read_language_strings(source)
    paths.atomic_json(target, {'stamp': stamp, 'strings': strings})
    return strings


load_story_strings.cache_clear = _load_strings.cache_clear


def get_story_progress(stats_counter, place='', lang='ru'):
    strings = load_story_strings(lang)
    return {'objective_string_id': stats_counter, 'objective_title': strings.get(stats_counter),
            'objective_desc': strings.get(stats_counter + 1) if isinstance(stats_counter, int) else None,
            'chapter_title': None, 'story_percent': None}
