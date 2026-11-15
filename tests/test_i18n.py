from pathlib import Path
import json
import re
from i18n import STRINGS, language


def test_no_russian_text_outside_js_dictionary():
    for p in (Path(__file__).resolve().parents[1]/'web').glob('*.js'):
        if p.name != 'i18n.js':
            assert not re.search(r'[\u0400-\u04ff]',p.read_text(encoding='utf-8')), p.name


def test_dictionaries_have_matching_keys_and_english_fallback():
    assert set(STRINGS['en']) == set(STRINGS['ru'])
    assert language('ru-RU') == 'ru'
    assert language('fr-FR') == 'en'
    s=(Path(__file__).resolve().parents[1]/'web/i18n.js').read_text(encoding='utf-8')
    d=json.JSONDecoder().raw_decode(s[s.index('var strings = ')+len('var strings = '):])[0]
    assert set(d['en']) == set(d['ru'])
    source=(Path(__file__).resolve().parents[1]/'web/companion_gow_map.js').read_text(encoding='utf-8')
    assert set(re.findall(r"tr\('([^']+)'\)",source)) <= set(d['en'])
