"""Read localization from the user-installed game; never bundle extracted strings."""
from pathlib import Path
from typing import Optional, Union, Dict
import re
from paths import wad_dir
try:
    import lz4.frame
except ImportError:
    lz4 = None

def read_language_strings(lang_wad_path: Optional[Union[str, Path]] = None) -> Dict[int, str]:
    """
    Распаковывает LZ4-архив локализации (по умолчанию r_lang_ru.wad)
    и извлекает все 48 800+ строк словаря игры в формате {str_id: text}.
    """
    if lang_wad_path is None:
        lang_wad_path = wad_dir() / 'r_lang_ru.wad'

    p = Path(lang_wad_path)
    if not p.is_file():
        return {}

    if lz4 is None:
        raise RuntimeError("Модуль lz4 не установлен")

    raw_comp = p.read_bytes()
    data = lz4.frame.decompress(raw_comp)

    # В r_lang_*.wad после заголовка WTOC лежат блоки *<ID>*\n<Text>\n
    pattern = re.compile(rb'\*(\d+)\*\r?\n(.*?)(?=\*\d+\*|\Z)', re.DOTALL)
    matches = pattern.findall(data)

    string_dict: Dict[int, str] = {}
    for str_id_bytes, text_bytes in matches:
        try:
            s_id = int(str_id_bytes)
            text = text_bytes.decode('utf-8', errors='ignore').strip()
            string_dict[s_id] = text
        except Exception:
            continue

    return string_dict

