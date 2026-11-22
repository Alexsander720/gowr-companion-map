"""UI labels written for this companion. Game localization is loaded separately."""
STRINGS = {
    'en': {
        'guide_solve': 'How to solve', 'guide_sources': 'Sources', 'guide_button': 'Guide',
        'guide_point': 'Guide point', 'guide_points': 'Guide points: ', 'guide_dismiss': 'Dismiss hint',
        'guide_near_nornir': 'Nornir chest nearby — how to solve',
        'guide_near_pin': 'Nearby: {name} — how to solve', 'guide_near_favor': 'Favor point nearby: “{name}”',
        'title': 'God of War Ragnarök — Companion Map', 'unknown': 'Unknown',
        'save_missing': 'No saves found; the map is still available',
        'pins_missing': 'Some pins could not be downloaded. See the terminal; the map remains available.',
        'unsupported_build': 'Memory offsets are not for this version of the game',
        'build_unverified': 'Game build could not be verified; live marker hidden',
        'game_closed': 'Game is not running', 'memory_unavailable': 'Live position is unavailable',
        'save_updates': 'Updates after each autosave', 'bad_request': 'Invalid request',
        'not_found': 'Not found', 'internal_error': 'Unable to read local data',
        'ready': 'Map ready', 'download': 'Preparing map data (first launch only)',
        'offline': 'Offline mode: cached data only', 'autocalib_missing': 'Install requirements-optional.txt for automatic calibration',
        'autocalib_templates': 'Automatic calibration needs your local templates. Run tools/gow_auto_calibrate.py --learn-templates first.',
        'nine_realms': 'Nine Realms', 'step_unknown': 'Current objective is unknown',
        'midgard': 'Midgard', 'vanaheim': 'Vanaheim', 'svartalfheim': 'Svartalfheim',
        'alfheim': 'Alfheim', 'jotunheim': 'Jötunheim', 'asgard': 'Asgard',
        'helheim': 'Helheim', 'niflheim': 'Niflheim', 'muspelheim': 'Muspelheim',
        'sindris-house': "Sindri's House", 'poi': 'Location',
        'difficulty_0': 'Story', 'difficulty_1': 'Grace', 'difficulty_2': 'Balance',
        'difficulty_3': 'No Mercy', 'difficulty_4': 'God of War',
    },
    'ru': {
        'guide_solve': 'Как открыть', 'guide_sources': 'Источники', 'guide_button': 'Гайд',
        'guide_point': 'Точка по гайду', 'guide_points': 'Точки по гайду: ', 'guide_dismiss': 'Закрыть подсказку',
        'guide_near_nornir': 'Рядом сундук Норн — как открыть',
        'guide_near_pin': 'Рядом: {name} — как открыть', 'guide_near_favor': 'Рядом точка просьбы «{name}»',
        'title': 'God of War Ragnarök — Карта-компаньон', 'unknown': 'Неизвестно',
        'save_missing': 'Сохранения не найдены; карта доступна',
        'pins_missing': 'Часть меток не загрузилась. Подробности в терминале; карта доступна.',
        'unsupported_build': 'Смещения памяти не для этой версии игры',
        'build_unverified': 'Версию игры проверить не удалось; живой маркер скрыт',
        'game_closed': 'Игра не запущена', 'memory_unavailable': 'Живые координаты недоступны',
        'save_updates': 'Обновляется после каждого автосохранения', 'bad_request': 'Некорректный запрос',
        'not_found': 'Не найдено', 'internal_error': 'Не удалось прочитать локальные данные',
        'ready': 'Карта готова', 'download': 'Подготовка данных карты (при первом запуске)',
        'offline': 'Автономный режим: только данные из кэша', 'autocalib_missing': 'Для автокалибровки установите requirements-optional.txt',
        'autocalib_templates': 'Автокалибровке нужны ваши локальные шаблоны. Сначала запустите tools/gow_auto_calibrate.py --learn-templates.',
        'nine_realms': 'Девять миров', 'step_unknown': 'Текущая цель неизвестна',
        'midgard': 'Мидгард', 'vanaheim': 'Ванахейм', 'svartalfheim': 'Свартальвхейм',
        'alfheim': 'Альвхейм', 'jotunheim': 'Йотунхейм', 'asgard': 'Асгард',
        'helheim': 'Хельхейм', 'niflheim': 'Нифльхейм', 'muspelheim': 'Муспельхейм',
        'sindris-house': 'Дом Синдри', 'poi': 'Метка',
        'difficulty_0': 'Сюжет', 'difficulty_1': 'Пощада', 'difficulty_2': 'Баланс',
        'difficulty_3': 'Без пощады', 'difficulty_4': 'Бог войны',
    },
}

# These category captions are our UI labels, not an upstream category dump.
CATEGORIES = {
    'odins_raven': ('Ravens', 'Вороны'), 'legendary_chest': ('Legendary chests', 'Легендарные сундуки'),
    'nornir_chest': ('Nornir chests', 'Сундуки Норн'), 'hel_tear': ('Hel tears', 'Разрывы Хель'),
    'nine_realms_in_bloom': ('Flowers', 'Цветы'), 'mystic_gateway': ('Gateways', 'Врата'),
    'lore': ('Lore', 'Знания'), 'artifact': ('Artifacts', 'Артефакты'),
    'kvasirs_poem': ('Poems', 'Стихи'), 'berserker_gravestone': ('Berserker graves', 'Могилы берсерков'),
    'remnant_of_asgard': ('Asgard remnants', 'Остатки Асгарда'), 'kol_raider_camp': ('Raider camps', 'Лагеря налётчиков'),
    'shield': ('Shields', 'Щиты'), 'relic': ('Relics', 'Реликвии'),
    'buried_treasure': ('Buried treasure', 'Клады'), 'treasure_map': ('Treasure maps', 'Карты сокровищ'),
    'red_coffin': ('Red coffins', 'Красные гробы'), 'wood_chest': ('Wood chests', 'Деревянные сундуки'),
    'hacksilver': ('Hacksilver', 'Серебро'), 'other_loot': ('Other loot', 'Другая добыча'),
    'miscellaneous': ('Other', 'Прочее'), 'entrance': ('Entrances', 'Проходы'),
    'draugr_hole': ('Draugr holes', 'Драугрские ямы'), 'yggdrasil_rift': ('Rifts', 'Разрывы'),
    'shop': ('Shops', 'Лавки'), 'jewel_of_yggdrasil': ('Jewels', 'Жемчужины'),
    'favor': ('Favors', 'Просьбы'), 'boss': ('Bosses', 'Боссы'),
    'sleeping_troll': ('Sleeping trolls', 'Спящие тролли'), 'ingredient': ('Ingredients', 'Ингредиенты'),
    'armor_set': ('Armor sets', 'Комплекты брони'), 'boat_dock': ('Boat docks', 'Причалы'),
    'yggdrasils_dew': ('Dew', 'Роса'), 'lost_lindwyrm': ('Lindwyrms', 'Линдвурмы'),
    'seasonal_stag': ('Stags', 'Олени'), 'celestial_altar': ('Altars', 'Алтари'),
    'wishing_well': ('Wishing wells', 'Колодцы желаний'), 'amulet_enhancement': ('Enchantments', 'Чары'),
    'key_item': ('Key items', 'Ключевые предметы'), 'muspelheim_trial': ('Trials', 'Испытания'),
}


def language(value):
    return 'ru' if str(value or '').lower().startswith('ru') else 'en'


def t(key, lang='en'):
    return STRINGS[language(lang)].get(key, key)


def category(key, lang='en'):
    value = CATEGORIES.get(key)
    return value[language(lang) == 'ru'] if value else t('poi', lang)
