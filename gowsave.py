"""Разбор формата сохранения God of War Ragnarök (задача 149).

Сейвы лежат в `Saved Games/God of War Ragnarök/<id>/GOWRSAVE*` (2.1–2.6 МБ).
Файл не зашифрован и не сжат (энтропия 4.43 бит/байт, ~49% нулей).

🔴 Почему стандартные утилиты поиска строк потерпели неудачу:
Они искали 7-битный ASCII (`strings -n 6`). Локализованные строки сохранения
(«Хельхейм - Пристань Вадгельмира - Хельская задача», «Вернуться к дому Синдри»)
записаны в UTF-8 (байты `\xd0`, `\xd1`), поэтому классический ascii-grep
принял их за случайный шум.

Структура заголовка (первые 0x440 = 1088 байт):
  0x00..0x08:  uint64 время сохранения (Unix epoch time в секундах)
  0x08..0x0c:  uint32 тип файла / заголовочный тег (0x08)
  0x0c..0x10:  uint32 версия формата (0x00660404 = 6685700)
  0x10..0x14:  uint32 размер настроек (696 байт = размер userpreferences)
  0x18..0x1c:  uint32 размер основного блока данных
  0x40..0x48:  uint64 время сохранения (повторная копия)
  0x48..0x4c:  uint32 тег (0x23 = 35)
  0x4c..0x50:  uint32 версия формата (0x00660404)
  0x50..0x190: фиксированный буфер 320 байт (0x140): UTF-8 строка места и цели:
               «Мир - Локация - Активная цель / квест»
  0x190..0x194: uint32 время прохождения в секундах (play_seconds)
  0x194..0x198: uint32 время сохранения (32-битный unix timestamp)
  0x198..0x19c: uint32 суммарно заработанное рубленое серебро
  0x19c..0x1a0: uint32 суммарно заработанный опыт (XP)
  0x1a0..0x1a4: uint32 ID локации / карты (0x805d..0x8575)
  0x1bc..0x1c0: uint32 порядковый номер сохранения (save_counter: 1182, 1183...)
  0x440:       начало полезной нагрузки сейва (uncompressed raw struct state)

Блок инвентаря и кошелька героя (HERO Wallet, ~0x2279a):
  Заголовок: 0x00004895C643225F (WalletHash "HERO")
  Количество записей: uint32 (158 ресурсов)
  Каждая запись: [uint64 Hash] [uint32 Quantity] [uint32 ID/Flags] (16 байт)
"""
from __future__ import annotations

import datetime
from paths import DATA, saved_games_roots
import json
import os
import re
import struct
import sys
from pathlib import Path

MAGIC_VERSION = 0x00660404
HEADER_SIZE = 0x440
STRING_OFFSET = 0x50
STRING_MAX_LEN = 0x140  # 320 байт: 0x50..0x190
HERO_WALLET_HASH = 0x00004895C643225F

DEFAULT_SAVE_ROOTS = saved_games_roots()

DIFFICULTY_LEVELS = {
    0: 'Сюжет (Give Me Story)',
    1: 'Пощада (Give Me Grace)',
    2: 'Баланс (Give Me Balance)',
    3: 'Без пощады (Give Me No Mercy)',
    4: 'Бог войны (Give Me God of War)',
}

REALM_NAMES_BY_ID = {
    0: 'Мидгард',
    1: 'Муспельхейм',
    2: 'Нифльхейм',
    3: 'Асгард',
    5: 'Хельхейм',
    6: 'Альвхейм',
    9: 'Ванахейм',
    10: 'Дом Синдри (Межмирье)',
}

ZONE_NAMES_BY_ID = {
    490: 'Мидгард',
    491: 'Альвхейм',
    492: 'Хельхейм',
    494: 'Нифльхейм',
    495: 'Муспельхейм',
    497: 'Ванахейм',
    498: 'Асгард',
    7262: 'Дом Синдри (Межмирье)',
}

CHAR_ACTORS = {
    'Char_HeroA00': ('Кратос (Главный герой)', 'главный герой'),
    'Char_Atreus00': ('Атрей (Сын / Локи)', 'главный герой / спутник'),
    'Char_FreyaValkyrie00': ('Фрейя (Королева Валькирий)', 'союзник / спутник'),
    'Char_Thor00': ('Тор (Бог грома)', 'асы'),
    'Char_Odin00': ('Один (Всеотец)', 'асы'),
    'Char_Heimdall00': ('Хеймдалль', 'асы'),
    'Char_Sif00': ('Сиф', 'асы'),
    'Char_Thrud00': ('Труд', 'асы'),
    'Char_Huginn00': ('Хугин (Ворон Всеотца)', 'асы'),
    'Char_Brok00': ('Брок', 'хульдры'),
    'Char_Sindri00': ('Синдри', 'хульдры'),
    'Char_Tyr00': ('Тюр (Скандинавский бог войны)', 'союзник'),
    'Char_Angrboda00': ('Ангрбода', 'союзник'),
    'Char_Freyr00': ('Фрейр', 'союзник'),
    'Char_Durlin00': ('Дурлин', 'союзник'),
    'Char_Faye00': ('Фэй (Лаувейя)', 'семья'),
    'Char_Skjoldr00': ('Скьёльд', 'житель Мидгарда'),
    'Char_IngridSword00': ('Летающий меч Ингрид', 'оружие / спутник'),
    'Char_DwarfDog00': ('Фенрир / Пес гномов', 'союзник'),
    'Char_AngrbodaYak00': ('Ялль (Як Ангрбоды)', 'существо'),
    'Char_FreyaFalcon00': ('Сокол Фрейи', 'существо'),
    'Char_Fox00': ('Лисица', 'существо'),
    'Char_Dwarf10_F5': ('Гном-страж', 'персонаж'),
    'Char_DarkOne00_F5': ('Тёмный эльф', 'архетип'),
    'Char_LightOne00_F5': ('Светлый эльф', 'архетип'),
    'Char_Traveler00_F5': ('Путник', 'архетип'),
}


def sms_std_name_hash(name: str | bytes) -> int:
    """Оригинальный 64-битный алгоритм хеширования имен движка Santa Monica Studio.

    Дизассемблирован из GoWR.exe (смещение 0x66EB70, StdNameHash).
    Регистронезависимый (uppercase): 'hero' == 'HERO' -> 0x00004895C643225F.
    'hacksilver' == 'Hacksilver' -> 0x5AE80674D240529E.
    """
    if isinstance(name, str):
        b = name.encode('ascii', errors='ignore')
    else:
        b = name
    rax = 0
    MASK64 = 0xFFFFFFFFFFFFFFFF
    for byte in b:
        c = byte
        if 0x61 <= c <= 0x7A:
            c -= 0x20
        rcx = (c + rax) & MASK64
        rax = (rcx * 0x401) & MASK64
        rcx = (rax >> 6) & MASK64
        rax = (rax ^ rcx) & MASK64
    return rax


# Известные 64-битные хеши ресурсов и прокачки (Santa Monica Engine / GoWR)
KNOWN_RESOURCE_HASHES = {
    # Валюта и очки опыта
    0x5AE80674D240529E: ('hacksilver', 'Рубленое серебро', 'валюта'),
    0x1E62B3ECB450EE3B: ('divine_ashes', 'Божественный пепел', 'валюта'),
    0x9C7CF61C839B9A8A: ('kratos_xp', 'Опыт Кратоса', 'опыт'),
    0xA1D028F9B467E25C: ('atreus_xp', 'Опыт Атрея', 'опыт'),
    0xAC98E8B5155F2C73: ('atreus_xp_alt', 'Опыт Атрея (альт)', 'опыт'),
    0xE577D004DA4F5243: ('freya_xp', 'Опыт Фрейи', 'опыт'),

    # Постоянные усиления характеристик (Роса Иггдрасиля)
    0xB34288875C3E1BCC: ('dew_strength', 'Роса силы Иггдрасиля', 'усиление'),
    0x3A7AB925F3863462: ('dew_runic', 'Роса рунической силы Иггдрасиля', 'усиление'),
    0x9C6B2C793C908F41: ('dew_defense', 'Роса защиты Иггдрасиля', 'усиление'),
    0x2D953C161CDB136A: ('dew_cooldown', 'Роса восстановления Иггдрасиля', 'усиление'),

    # Улучшения оружия и амулета
    0x0B6552BEE68874FA: ('chaos_flame', 'Пламя Хаоса', 'улучшение клинков'),
    0x6DBF14545BF30691: ('chaos_flame_alt', 'Пламя Хаоса (альт)', 'улучшение клинков'),
    0x27678319710C9A2F: ('gale_flame', 'Штормовое пламя', 'улучшение копья'),
    0x29EA3915152A4E92: ('gale_flame_alt', 'Штормовое пламя (альт)', 'улучшение копья'),
    0xEB1FE5F962F01FA6: ('frozen_flame', 'Замерзшее пламя', 'улучшение топора'),
    0x3102377B5A1DF473: ('frozen_flame_alt', 'Замерзшее пламя (альт)', 'улучшение топора'),
    0xFE5EABE1F74A6D4A: ('jewel_of_yggdrasil', 'Жемчужина Иггдрасиля', 'амулет'),
    0x5993A40733A11F58: ('amulet_jewels_alt', 'Жемчужина Иггдрасиля (альт)', 'амулет'),

    # Сундуки Норн: Яблоки Идунн (MaxHealthUpgradePiece) — непотраченные части текущего тира
    0x638E76C7E822F035: ('idunn_apples_t1', 'Яблоки Идунн (тир 1)', 'здоровье'),
    0x638E76C7E822F424: ('idunn_apples_t2', 'Яблоки Идунн (тир 2)', 'здоровье'),
    0x638E76C7E8220BD3: ('idunn_apples_t3', 'Яблоки Идунн (тир 3)', 'здоровье'),
    0x638E76C7E8220FC2: ('idunn_apples_t4', 'Яблоки Идунн (тир 4)', 'здоровье'),
    0x638E76C7E82203F1: ('idunn_apples_t5', 'Яблоки Идунн (тир 5)', 'здоровье'),
    # Сундуки Норн: Рога медовой крови (MaxRageUpgradePiece) — непотраченные части текущего тира
    0x6CF01AFB41A1421E: ('blood_mead_horns_t1', 'Рога медовой крови (тир 1)', 'ярость'),
    0x6CF01AFB41A15E6F: ('blood_mead_horns_t2', 'Рога медовой крови (тир 2)', 'ярость'),
    0x6CF01AFB41A15A78: ('blood_mead_horns_t3', 'Рога медовой крови (тир 3)', 'ярость'),
    0x6CF01AFB41A15649: ('blood_mead_horns_t4', 'Рога медовой крови (тир 4)', 'ярость'),
    0x6CF01AFB41A1525A: ('blood_mead_horns_t5', 'Рога медовой крови (тир 5)', 'ярость'),
    # Глобальный счётчик открытых сундуков Норн (рога + яблоки)
    0x554185F25EFB1F0A: ('nornir_chests_opened', 'Всего открыто сундуков Норн', 'прогресс'),
    0x534685FF86561129: ('idunn_apples_alt', 'Яблоки Идунн (альт)', 'здоровье'),
    0xB3C3330664D5C90B: ('blood_mead_horns_alt', 'Рога медовой крови (альт)', 'ярость'),
    0x482780EFF18ED57E: ('the_eyes_of_odin', 'Глаза Одина (вороны)', 'коллекционное'),
    0x28FB73555D08478B: ('odin_raven_chests', 'Сундуки Древа Воронов', 'коллекционное'),
    0x39A3F2B4507119F4: ('odin_ravens_alt', 'Глаза Одина (альт)', 'коллекционное'),
    0x1BAB03B171A4D93A: ('lore_marker', 'Святилище знаний', 'коллекционное'),

    # Квестовые предметы и реликвии
    0x7B0502D7C5B3D928: ('inert_hilt_skofnung', 'Рукоять Скофнунга (неактивная)', 'реликвия'),
    0x6E2831056991BE78: ('hilt_skofnung', 'Рукоять Скофнунга', 'реликвия'),
    0x5A13392A861AFD71: ('hammer_revolution', 'Молот революции', 'квест'),
    0xC102E8E1D36FDFB0: ('lindwyrm_trap', 'Ловушка для линдвурмов', 'квест'),
    0xC87E473C9761A378: ('lindwyrm_scales', 'Чешуя линдвурма', 'квест/материал'),
    0xD5D2CA705C3D43BF: ('jotunheim_fruit', 'Йотунхеймский плод', 'квест'),
    0x4B618A4A0B900ADA: ('resurrection_stone', 'Камень воскрешения', 'расходник'),

    # Просьбы и броня (Лунда, Скирнир, Фрейя)
    0x233B569A68CD2AD7: ('mysterious_orb', 'Таинственная сфера Лунды', 'просьба'),
    0xA840E2A18262AF54: ('lunda_cuirass', 'Кираса Лунды', 'броня'),
    0xFAAC474DF3F70C20: ('lunda_belt', 'Пояс Лунды', 'броня'),
    0xB0C5E31BF288DEE4: ('lunda_bracers', 'Браслеты Лунды', 'броня'),
    0xBB2168B7BCDAABFE: ('folkvangr_whetstone', 'Фольквангский точильный камень', 'улучшение'),
    0xA3990A964C1021CB: ('skirnir_gambanteinn', 'Гамбантейн Скирнира', 'материал'),

    # Материалы для крафта
    0x8012CD8607AFCAB3: ('forged_iron', 'Кованое железо', 'материал'),
    0x2D218DADA5D3E28F: ('dwarven_steel', 'Гномья сталь', 'материал'),
    0x2D219821A6CB84B2: ('asgardian_ingot', 'Асгардский слиток', 'материал'),
    0x56CABA257449EEB0: ('luminous_alloy', 'Светящийся сплав', 'материал'),
    0xD37CC9F00CC092C3: ('petrified_bone', 'Окаменелая кость', 'материал'),
    0xD37DF96D85271A34: ('stonewood', 'Окаменелое дерево', 'материал'),
    0x57366132328A1215: ('ydalir_timber', 'Идалирская древесина', 'материал'),
    0x56CB1102C2C9DA7B: ('honed_metal', 'Заточенный металл', 'материал'),
    0xDBC322506D89B008: ('slag_deposits', 'Шлак', 'материал'),
    0x4FB167B13EBE3F7E: ('rawhide', 'Сыромятная кожа', 'материал'),
    0x4F5B100295A64536: ('bonded_leather', 'Плотная кожа', 'материал'),
    0x1EA4F1B430F75E47: ('beast_scraps', 'Звериные ошметки', 'материал'),
    0xA2486AA082C30D97: ('beast_bones', 'Звериные кости', 'материал'),
    0xF9A3AF92681E695E: ('dragon_teeth', 'Зуб дракона', 'материал'),
    0xCA34EC49A6E8F225: ('dust_of_realms', 'Пыль миров', 'материал'),
    0x7433123E219F06C3: ('whispering_slab', 'Шепчущая плита', 'материал'),
    0xBCADF49D2EEEDC44: ('shattered_runes', 'Разбитые руны', 'материал'),
    0x64E4C212F24E07C7: ('nidavellir_core', 'Ядро Нидавеллира', 'материал'),
    0x27A4C43D2BA1926D: ('dew_vitality', 'Роса живучести Иггдрасиля', 'усиление'),
    0x5DB3BF85D2C3CBF3: ('dew_luck', 'Роса удачи Иггдрасиля', 'усиление'),
    0x7F8323FC15C33E3B: ('tempered_remnants', 'Закаленные обломки', 'материал'),
    0x6E71A12DA8C86401: ('hardened_remnants', 'Укрепленные обломки', 'материал'),
    0x9BAAA724E1465DC6: ('hunters_brand', 'Клеймо охотника', 'материал'),
    0xCA32D6528EBCE496: ('essence_of_hel', 'Сущность Хель', 'материал'),
    0x600DFFF47F2AC8BA: ('svefnthorn', 'Свефнторн', 'материал'),
    0x5602C80740A65E0F: ('crackle_of_bilskirnir', 'Гул Бильскирнира', 'материал'),
    0x086B670820E0482A: ('nars_cup', 'Чаша Нара', 'материал'),
    0xB7F497AD9D6D81E6: ('muspelheim_seed_half', 'Половина семени Муспельхейма', 'квест'),
    0x3363EA24D97F3F10: ('jotunheim_fruit_alt', 'Йотунхеймский плод (альт)', 'квест'),
    0x0F293CEC4D3EDEEE: ('consuls_journal', 'Журнал консула', 'артефакт'),
    0x8030774CEFD65A11: ('meal_of_comfort', 'Трапеза утешения', 'расходник'),
    0xD6833365C3296802: ('max_health_increased', 'Увеличение макс. здоровья', 'улучшение'),
    0x1AEEE86352596537: ('max_rage_increased', 'Увеличение макс. ярости', 'улучшение'),
    0xFA7488E6BE52650B: ('chaos_spark_alt', 'Искра Хаоса (альт)', 'материал'),
    0xA61FF062F9E51FEB: ('frozen_spark', 'Ледяная искра', 'материал'),
    0x2C22FF2C43DDDA89: ('blood_mead_horns_total', 'Всего собрано Рогов медовой крови', 'прогресс'),

    # Доказанные артефакты и квестовые предметы (Задача 202)
    0xF7661514835F29C0: ('draugr_empress_loot', 'Добыча нор Драугров (Императрица)', 'квест/материал'),
    0x4E4EDEA1196B39A6: ('muspelheim_seed_piece', 'Половина семени Муспельхейма (деталь)', 'квест'),
    0x0F5EA64007C80256: ('tome_ridill_upgrade', 'Зуб Тора (том улучшения Ридилль)', 'реликвия/улучшение'),
    0x9DA65BD12638D6EE: ('anv_dark_odyssey_gear', 'Броня Тёмной Одиссеи', 'броня'),
    0x719917E3CA5A4240: ('muspelheim_seed_tracker', 'Прогресс семян Муспельхейма', 'прогресс'),
    0xB86D84824DDC0CDF: ('angurvadal_resource_tracker', 'Рукоять Ангрваделя', 'реликвия/квест'),
    0xD651D39A97F7C57B: ('lindwyrm_hilt_tracker', 'Ловля линдвурмов (прогресс рукояти)', 'просьба'),
    0x735330EA42E2B405: ('freya_party_tracker', 'Фрейя в отряде', 'сюжет'),
    0xC35C73716E47B4ED: ('axe_reinforcement', 'Улучшение топора Левиафан', 'улучшение'),
    0xDCCFA60D1AE18D88: ('blades_reinforcement', 'Улучшение Клинков Хаоса', 'улучшение'),

    # Украденные сокровища Мидгарда (StolenTreasure01..06)
    0xE724D1990BE437FE: ('stolen_treasure_01', 'Украденное сокровище #1', 'артефакт'),
    0xE724D1990BE43BD1: ('stolen_treasure_02', 'Украденное сокровище #2', 'артефакт'),
    0xE724D1990BE43FC0: ('stolen_treasure_03', 'Украденное сокровище #3', 'артефакт'),
    0xE724D1990BE423B3: ('stolen_treasure_04', 'Украденное сокровище #4', 'артефакт'),
    0xE724D1990BE427A2: ('stolen_treasure_05', 'Украденное сокровище #5', 'артефакт'),
    0xE724D1990BE42B95: ('stolen_treasure_06', 'Украденное сокровище #6', 'артефакт'),

    # Семейные гербы Ванахейма (FamilyCrests01..06)
    0xBB10065F6DF7B8C6: ('family_crest_01', 'Семейный герб #1', 'артефакт'),
    0xBB10065F6DF7BCD7: ('family_crest_02', 'Семейный герб #2', 'артефакт'),
    0xBB10065F6DF78024: ('family_crest_03', 'Семейный герб #3', 'артефакт'),
    0xBB10065F6DF78435: ('family_crest_04', 'Семейный герб #4', 'артефакт'),
    0xBB10065F6DF78802: ('family_crest_05', 'Семейный герб #5', 'артефакт'),
    0xBB10065F6DF78C13: ('family_crest_06', 'Семейный герб #6', 'артефакт'),

    # Оставленные вещи Свартальвхейма (ThingsLeftBehind01..06)
    0xA4CAAA0EF85AE94B: ('things_left_behind_01', 'Оставленная вещь #1', 'артефакт'),
    0xA4CAAA0EF85AED5A: ('things_left_behind_02', 'Оставленная вещь #2', 'артефакт'),
    0xA4CAAA0EF85AE169: ('things_left_behind_03', 'Оставленная вещь #3', 'артефакт'),
    0xA4CAAA0EF85AE578: ('things_left_behind_04', 'Оставленная вещь #4', 'артефакт'),
    0xA4CAAA0EF85AF917: ('things_left_behind_05', 'Оставленная вещь #5', 'артефакт'),
    0xA4CAAA0EF85AFD06: ('things_left_behind_06', 'Оставленная вещь #6', 'артефакт'),

    # Подношения Фрейру Альвхейма (TributesToFreyr01..06)
    0x7B32ED8F4BF7D053: ('tributes_to_freyr_01', 'Подношение Фрейру #1', 'артефакт'),
    0x7B32ED8F4BF7D442: ('tributes_to_freyr_02', 'Подношение Фрейру #2', 'артефакт'),
    0x7B32ED8F4BF7D84D: ('tributes_to_freyr_03', 'Подношение Фрейру #3', 'артефакт'),
    0x7B32ED8F4BF7DC5C: ('tributes_to_freyr_04', 'Подношение Фрейру #4', 'артефакт'),
    0x7B32ED8F4BF7C02F: ('tributes_to_freyr_05', 'Подношение Фрейру #5', 'артефакт'),
    0x7B32ED8F4BF7C43E: ('tributes_to_freyr_06', 'Подношение Фрейру #6', 'артефакт'),

    # Мастер-трекеры коллекций артефактов (доказаны из GoWR.exe)
    0x2E44032F3C79A93B: ('stolen_treasure_tracker', 'Коллекция: Украденные сокровища (Мидгард)', 'коллекция'),
    0x532912274F0537DB: ('things_left_behind_tracker', 'Коллекция: Оставленные вещи (Свартальвхейм)', 'коллекция'),
    0xCA9531AA5ED2D969: ('family_crests_tracker', 'Коллекция: Семейные гербы (Ванахейм)', 'коллекция'),
    0xD9C5D7E417939EC6: ('tributes_to_freyr_tracker', 'Коллекция: Подношения Фрейру (Альвхейм)', 'коллекция'),
    0x0B439056E3853C5D: ('mimir_books_tracker', 'Коллекция: Стихи Квасира / Книги Мимира', 'коллекция'),
}

# Ключевые сюжетные катсцены
MILESTONE_CUTSCENES = [
    ('C_113_SonicArrows', 'sonic_arrows', 'Получены звуковые стрелы Атрея'),
    ('C_120_TyrIntro', 'tyr_rescued', 'Тюр найден в Свартальвхейме'),
    ('C_170_GroaRevealed', 'groa_secret', 'Тайна Гроа в Альвхейме'),
    ('C_177_RatatoskrIntro', 'ratatoskr', 'Знакомство с Рататоском'),
    ('C_190_IronwoodArrival', 'ironwood', 'Атрей прибыл в Железный лес'),
    ('C_240_GrylaIntro', 'gryla_defeated', 'Победа над Грилой в Йотунхейме'),
    ('C_330_OldWoundsRevisited', 'freya_allied', 'Фрейя освобождена от проклятия'),
    ('C_350_AsgardCalls', 'asgard_visited', 'Атрей посетил Асгард'),
    ('C_400_IngridIntro', 'ingrid_sword', 'Атрей получил летающий меч Ингрид'),
    ('C_430_TheNorns', 'norns_visited', 'Норны у Озера Девяти («Слово судьбы»)'),
    ('C_450_DraupnirSpear', 'draupnir_spear', 'Выковано копьё Драупнир'),
    ('C_483_AtreusMissesHome', 'hel_completed', 'Возвращение из Хельхейма («Хельская задача»)'),
]

# Ключевые боссы и сюжетные чекпоинты (Actor / Encounter checkpoints)
BOSS_ENCOUNTER_MARKERS = [
    ('Mid_Cal100_ThorFightMaster', 'thor_fight', 'Битва с Тором у хижины (Мидгард)'),
    ('Mid_For210_BossFreya', 'freya_valkyrie', 'Схватка с валькирией Фрейей'),
    ('Van_VanVil500_FreyaHouse', 'freya_curse_lifted', 'Освобождение Фрейи в Ванахейме'),
    ('Jot_Iron025_Utangard', 'ironwood_arrival', 'Атрей прибыл в Железный лес к Ангрбоде'),
    ('Jot_Iron125_WolfEscort', 'jotunheim_wolf', 'Сопровождение волка в Йотунхейме'),
    ('Asg_Fort100_Main', 'asgard_great_lodge', 'Крепость Одина в Асгарде (Великая ложа)'),
    ('Asg_MidCity250_HeimFightMaster', 'heimdall_encounter', 'Схватка с Хеймдаллем'),
    ('Van_CratPlain100_Entrance', 'vanaheim_crater', 'Исследование Кратера в Ванахейме'),
    ('Hel_Garm500_Docks', 'garm_docks_chase', 'Погоня за Гармом по верфям Хельхейма'),
    ('Hel_Garm520_GarmsPen', 'garm_defeated', 'Победа над Гармом в его логове'),
]

# Спутники в странствиях
COMPANION_MARKERS = [
    ('Add_AtreusCompanion00', 'atreus', 'Атрей'),
    ('Add_BrokCompanion00', 'brok', 'Брок'),
    ('Add_FreyaCompanion00', 'freya', 'Фрейя'),
    ('Char_IngridSword00', 'ingrid_sword', 'Летающий меч Ингрид'),
]

# Префиксы локаций и скриптов 9 миров
REALM_CHECKPOINT_PREFIXES = {
    'midgard': rb'Mid_[A-Za-z0-9_]+',
    'svartalfheim': rb'Sva_[A-Za-z0-9_]+',
    'vanaheim': rb'Van_[A-Za-z0-9_]+',
    'alfheim': rb'Alf_[A-Za-z0-9_]+',
    'jotunheim': rb'Jot_[A-Za-z0-9_]+',
    'asgard': rb'Asg_[A-Za-z0-9_]+',
    'helheim': rb'Hel_[A-Za-z0-9_]+',
    'niflheim': rb'Nif_[A-Za-z0-9_]+',
    'muspelheim': rb'(?:Msp|Mus)_[A-Za-z0-9_]+',
}

# Ключевые слоты снаряжения героя (Char_HeroA00 loadout)
# Точные названия рукоятей и тыльников доказаны скриншотами сессии из живой игры (Задача 191)
KEY_EQUIPMENT_MAP = {
    0x083E95365CC16313: ('weapon_primary', 'Топор Левиафан'),
    0x5EDA95A2FC221AEE: ('weapon_secondary', 'Клинки Хаоса'),
    0xA1E318FD889AD3BA: ('weapon_spear', 'Копьё Драупнир'),
    0x176AAA6E0D2E9792: ('armor_chest', 'Кираса Лунды (нагрудник)'),
    0x143EEED4BCEE1352: ('armor_wrist', 'Браслеты Лунды'),
    0x735D31B293869CC0: ('armor_waist', 'Пояс Лунды'),
    0x2586D16A9CC81C97: ('shield', 'Щит'),
    0x40D1EB70CBD41D34: ('shield_rond', 'Ронд щита'),
    0x3788835BFB348C9E: ('weapon_pommel', 'Топорище каменотёса'),
    0xAEB7801850BA7596: ('blades_handles', 'Рукояти лёгкого обмана'),
    0x8694E35BE525EFCC: ('spear_sauroter', 'Тыльник стремительного натиска'),
}

# Доказанные рунические атаки (Задача 191, верифицировано скриншотами сессии и слотами Char_HeroA00)
PROVEN_RUNIC_ATTACKS = {
    # Топор Левиафан
    0x25AA7D624507EBF2: {
        'name': 'Укус зимы',
        'name_en': "Winter's Bite",
        'type': 'light',
        'weapon': 'axe',
        'cooldown_sec': 59,
        'proven': True,
        'basis': 'скриншот Левиафана из живой игры и слот +0x0C8B в Char_HeroA00',
    },
    0x4E069A72D687E6EF: {
        'name': 'Наковальня Ивальди',
        'name_en': "Ivaldi's Anvil",
        'type': 'heavy',
        'weapon': 'axe',
        'cooldown_sec': 118,
        'proven': True,
        'basis': 'скриншот Левиафана из живой игры и слот +0x0C95 в Char_HeroA00',
    },
    0x33EC5039DD344198: {
        'name': 'Туман Фимбулвинтера',
        'name_en': "Fog of Fimbulwinter",
        'type': 'heavy',
        'weapon': 'axe',
        'cooldown_sec': 196,
        'proven': True,
        'basis': 'скриншот Левиафана из живой игры и слот +0x0C9F в Char_HeroA00',
    },
    # Клинки Хаоса
    0xD5A29A532902503E: {
        'name': 'Буйство фурий',
        'name_en': "Rampage of the Furies",
        'type': 'light',
        'weapon': 'blades',
        'cooldown_sec': 79,
        'proven': True,
        'basis': 'скриншот Клинков Хаоса из живой игры и слот +0x0F3E в Char_HeroA00',
    },
    0xB18BF327A00513DB: {
        'name': 'Укрощение зверя',
        'name_en': "Tame the Beast",
        'type': 'heavy',
        'weapon': 'blades',
        'cooldown_sec': 118,
        'proven': True,
        'basis': 'скриншот Клинков Хаоса из живой игры и слот +0x0F48 в Char_HeroA00',
    },
    0x0433DAEFFED3DE8D: {
        'name': 'Пламя боли',
        'name_en': "Flames of Anguish",
        'type': 'light',
        'weapon': 'blades',
        'cooldown_sec': 79,
        'proven': True,
        'basis': 'скриншот Клинков Хаоса из живой игры и слот +0x0F52 в Char_HeroA00',
    },
    0x6651D43034D6F8A7: {
        'name': 'Вулкан Атласа',
        'name_en': "Atlas Eruption",
        'type': 'heavy',
        'weapon': 'blades',
        'cooldown_sec': 255,
        'proven': True,
        'basis': 'скриншот Клинков Хаоса из живой игры и слот +0x0F5C в Char_HeroA00',
    },
    # Копьё Драупнир
    0x4EFC1EAA8A45A505: {
        'name': 'Крушитель гор',
        'name_en': "Mountain Splitter",
        'type': 'light',
        'weapon': 'spear',
        'cooldown_sec': 118,
        'proven': True,
        'basis': 'скриншот Драупнира из живой игры и слот +0x124F в Char_HeroA00',
    },
}

# Доказанные чары Амулета Иггдрасиля (Задача 191, верифицировано скриншотами Амулета)
PROVEN_AMULET_ENCHANTMENTS = {
    0x8F90325A60120F00: {
        'name': 'Мощь Ванахейма',
        'name_en': "Vanaheim's Power",
        'set': 'Vanaheim',
        'proven': True,
        'basis': 'скриншот Амулета Иггдрасиля слот 1 и Char_HeroA00',
    },
    0xB11C545428053F87: {
        'name': 'Удача Ванахейма',
        'name_en': "Vanaheim's Fortitude",
        'set': 'Vanaheim',
        'proven': True,
        'basis': 'скриншот Амулета Иггдрасиля слот 2 и Char_HeroA00',
    },
    0x0F9812A58492CE73: {
        'name': 'Защита Муспельхейма',
        'name_en': "Muspelheim's Protection",
        'set': 'Muspelheim',
        'proven': True,
        'basis': 'скриншот Амулета Иггдрасиля слот 3 и Char_HeroA00',
    },
    0x3EDAAC1A7D93EDD5: {
        'name': 'Дар гнева',
        'name_en': 'Boon of Wrath',
        'set': None,
        'proven': True,
        'basis': 'скриншот Амулета Иггдрасиля слот 4 (до замены) и Char_HeroA00',
    },
    0x3405CFBB2B83374F: {
        'name': 'Честь Ванахейма',
        'name_en': "Vanaheim's Honor",
        'set': 'Vanaheim',
        'proven': True,
        'basis': 'скриншот Амулета Иггдрасиля слот 5 и Char_HeroA00',
    },
    0x9A83391826086423: {
        'name': 'Знак стихийного уклонения',
        'name_en': 'Emblem of Elusive Elements',
        'set': None,
        'proven': True,
        'basis': 'скриншот Амулета Иггдрасиля слот 6 (до замены) и Char_HeroA00',
    },
}

WORLD_FLAGS_START = 0x2600
WORLD_FLAGS_END = 0x36C0
WORLD_FLAG_ACTIVE_VAL = 0x00020000

# Доказанные соответствия битовых флагов мира конкретным мирам (Задача 188)
# Доказано не менее чем 2 переходами между хронологическими слотами сохранений.
PROVEN_REALM_FLAGS = {
    # Мидгард: монотонно зажигаются в слотах 13->14 (Озеро Девяти -> Берега Девяти, Слово судьбы)
    0x79E7867D999084F6: {
        'realm': 'midgard',
        'offset': 0x2E88,
        'index': 546,
        'name_guess': 'Объект/веха исследования Мидгарда #1',
        'proven': True,
        'basis': 'монотонная активация в слотах 13->14 внутри Мидгарда, сохраняется во всех последующих слотах',
    },
    0x8CC2C9B716802B7B: {
        'realm': 'midgard',
        'offset': 0x3200,
        'index': 768,
        'name_guess': 'Объект/веха исследования Мидгарда #2',
        'proven': True,
        'basis': 'монотонная активация в слотах 13->14 внутри Мидгарда, сохраняется во всех последующих слотах',
    },
    0xC0E4CE7614AD3E5D: {
        'realm': 'midgard',
        'offset': 0x32A4,
        'index': 809,
        'name_guess': 'Объект/веха исследования Мидгарда #3',
        'proven': True,
        'basis': 'монотонная активация в слотах 13->14 внутри Мидгарда, сохраняется во всех последующих слотах',
    },
    # Хельхейм: локальный флаг зоны (активен только внутри Хельхейма, сбрасывается в 0 при выходе)
    0x91F601FEA768905A: {
        'realm': 'helheim',
        'offset': 0x2634,
        'index': 13,
        'name_guess': 'Объект/веха исследования Хельхейма',
        'proven': False,
        'basis': 'локальный флаг зоны Хельхейма (сбрасывается в 0 при выходе в другие миры, не является глобально персистентным)',
    },
}


def get_proven_realm_flags_summary(data: bytes) -> dict:
    """Сводка доказанных соответствий флагов мира (Задача 188)."""
    if len(data) < WORLD_FLAGS_END:
        return {}
    res = {
        'midgard': {'active_count': 0, 'total_tracked': 3, 'flags': []},
        'helheim': {'active_count': 0, 'total_tracked': 1, 'flags': []},
    }
    for h, meta in PROVEN_REALM_FLAGS.items():
        off = meta['offset']
        is_active = (struct.unpack_from('<I', data, off)[0] == WORLD_FLAG_ACTIVE_VAL)
        realm = meta['realm']
        if realm in res:
            res[realm]['flags'].append({
                'hash': hex(h),
                'offset': hex(off),
                'index': meta['index'],
                'active': is_active,
                'name_guess': meta['name_guess'],
                'proven': meta['proven'],
                'basis': meta['basis'],
            })
            if is_active:
                res[realm]['active_count'] += 1
    return res


# Битовые маски этапов прохождения квестов в 0x36C0..0x4000 (Задача 181)
QUEST_STAGE_MASKS = {
    0x3BE4: {
        'id': 'asgard_into_the_fire',
        'title': 'Заблудшее дитя (Асгард)',
        'max_steps': 4,
        'description': 'Побег Атрея в Асгард и аудиенция у Одина',
    },
    0x3D14: {
        'id': 'word_of_fate',
        'title': 'Слово судьбы (Норны)',
        'max_steps': 5,
        'description': 'Поиски Норн у Озера Девяти в Мидгарде',
    },
    0x3B84: {
        'id': 'hel_task_garm',
        'title': 'Хельская задача (Гарм)',
        'max_steps': 3,
        'description': 'Освобождение и усмирение Гарма в Хельхейме',
    },
    0x3B80: {
        'id': 'hel_exploration',
        'title': 'Исследование Хельхейма',
        'max_steps': 6,
        'description': 'Продвижение по локациям Хельхейма (Пристань, Берег Гнипахеллира)',
    },
    0x3C88: {
        'id': 'storyline_milestones',
        'title': 'Сюжетные вехи Саги',
        'max_steps': 8,
        'description': 'Ключевые поворотные этапы основного сюжета',
    },
    0x3D88: {
        'id': 'norns_trail',
        'title': 'Следы Норн у Озера Девяти',
        'max_steps': 3,
        'description': 'Исследование следов Норн и поездка на келпи',
    },
    0x3D7C: {
        'id': 'norns_sanctuary',
        'title': 'Святилище Норн (Судьба)',
        'max_steps': 4,
        'description': 'Преодоление иллюзий Норн и вход в Святилище',
    },
    0x3BE0: {
        'id': 'ingrid_arrival',
        'title': 'Меч Ингрид и Асгард',
        'max_steps': 3,
        'description': 'Обретение меча Ингрид и переход в Асгард',
    },
    0x3BD0: {
        'id': 'garm_pursuit',
        'title': 'Погоня за Гармом',
        'max_steps': 3,
        'description': 'Преследование Гарма по разломам Хельхейма',
    },
    0x3D00: {
        'id': 'helheim_reunion',
        'title': 'Воссоединение (Хельхейм)',
        'max_steps': 4,
        'description': 'Поиски и воссоединение Кратоса и Атрея в Хельхейме',
    },
    0x3D30: {
        'id': 'helheim_trials',
        'title': 'Испытания Хельхейма',
        'max_steps': 6,
        'description': 'Битвы у ледяных врат и прорыв через царство мёртвых',
    },
    0x3D50: {
        'id': 'saga_major_acts',
        'title': 'Глобальные акты Саги',
        'max_steps': 7,
        'description': 'Основные сюжетные кульминации и союзы Девяти миров',
    },
    0x3D78: {
        'id': 'helheim_escape',
        'title': 'Врата спасения из Хельхейма',
        'max_steps': 4,
        'description': 'Закрытие разломов и эвакуация из Хельхейма',
    },
}


def parse_quest_stages(data: bytes) -> dict[str, dict]:
    """Извлечение доказанных битовых масок этапов квестов в секторе 0x3700..0x4000 (Задача 181)."""
    stages = {}
    for off, meta in QUEST_STAGE_MASKS.items():
        if off + 4 <= len(data):
            raw_val = struct.unpack_from('<I', data, off)[0]
            mask_hi = raw_val >> 16
            completed = bin(mask_hi).count('1')
            max_s = meta['max_steps']
            pct = round((completed / max_s) * 100, 1) if max_s > 0 else 0.0
            stages[meta['id']] = {
                'offset': hex(off),
                'id': meta['id'],
                'title': meta['title'],
                'name_guess': meta['title'],
                'proven': False,
                'basis': 'корреляция с катсценами Саги',
                'completed_steps': completed,
                'max_steps': max_s,
                'percent': min(100.0, pct),
                'is_completed': completed >= max_s,
                'raw_mask': f'0x{mask_hi:04X}',
                'raw_uint32': f'0x{raw_val:08X}',
                'description': meta['description'],
            }
    return stages


PROVEN_MONOTONIC_OFFSETS = {
    0x0000: {
        'name': 'save_timestamp_epoch',
        'type': 'uint32 (low 32b of uint64)',
        'description': 'Unix epoch время создания сохранения (совпадает с заголовком)',
    },
    0x0040: {
        'name': 'save_timestamp_epoch_dup',
        'type': 'uint32 (low 32b of uint64)',
        'description': 'Дубликат Unix epoch времени создания сохранения',
    },
    0x0190: {
        'name': 'play_seconds',
        'type': 'uint32',
        'description': 'Время прохождения игры в секундах',
    },
    0x0194: {
        'name': 'save_timestamp_copy',
        'type': 'uint32',
        'description': '32-битная копия Unix epoch времени сохранения',
    },
    0x01AC: {
        'name': 'session_event_sequence',
        'type': 'uint32',
        'description': 'Глобальный порядковый номер игровых событий и сессий (22174 -> 50313)',
    },
    0x01B0: {
        'name': 'stats_counter',
        'alias': 'objective_string_id',
        'type': 'uint32',
        'description': 'ID строки активного шага цели в таблице локализации r_lang_ru.wad (13466, 14493, 22958, 19608), подтверждено строкой 0x50',
    },
    0x01B4: {
        'name': 'action_trigger_sequence',
        'type': 'uint32',
        'description': 'Счётчик триггеров действий и интеракций мира (13467 -> 22951)',
    },
    0x01BC: {
        'name': 'save_counter',
        'type': 'uint32',
        'description': 'Порядковый номер слота автосохранения (773 -> 1213)',
    },
    0x3B80: {
        'name': 'hel_exploration_mask',
        'type': 'uint32 (hi 16b bitmask)',
        'description': 'Битовая маска этапов исследования Хельхейма (0x001F0000 -> 0x003F0000, 5 -> 6 бит)',
    },
    0x3B84: {
        'name': 'hel_task_garm_mask',
        'type': 'uint32 (hi 16b bitmask)',
        'description': 'Битовая маска этапов квеста «Хельская задача / Гарм» (0 -> 0x00070000, 3 бита)',
    },
    0x3BD0: {
        'name': 'garm_pursuit_mask',
        'type': 'uint32 (hi 16b bitmask)',
        'description': 'Битовая маска погони за Гармом по разломам Хельхейма (0 -> 0x00070000, 3 бита)',
    },
    0x3BE0: {
        'name': 'ingrid_arrival_mask',
        'type': 'uint32 (hi 16b bitmask)',
        'description': 'Битовая маска получения меча Ингрид и пути в Асгард (0 -> 0x00070000, 3 бита)',
    },
    0x3BE4: {
        'name': 'asgard_into_the_fire_mask',
        'type': 'uint32 (hi 16b bitmask)',
        'description': 'Битовая маска этапов квеста «Заблудшее дитя (Асгард)» (0 -> 0x000F0000, 4 бита)',
    },
    0x3C88: {
        'name': 'storyline_milestones_mask',
        'type': 'uint32 (hi 16b bitmask)',
        'description': 'Битовая маска сюжетных вех Саги (0 -> 0x030F0000 -> 0x036F0000, 6 -> 8 бит)',
    },
    0x3D00: {
        'name': 'helheim_reunion_mask',
        'type': 'uint32 (hi 16b bitmask)',
        'description': 'Битовая маска этапов квеста «Воссоединение (Хельхейм)» (0x000B0000 -> 0x000F0000, 3 -> 4 бита)',
    },
    0x3D14: {
        'name': 'word_of_fate_mask',
        'type': 'uint32 (hi 16b bitmask)',
        'description': 'Битовая маска этапов квеста «Слово судьбы» (0 -> 0x001F0000, 5 бит)',
    },
    0x3D30: {
        'name': 'helheim_trials_mask',
        'type': 'uint32 (hi 16b bitmask)',
        'description': 'Битовая маска испытаний и битв у ледяных врат Хельхейма (0x000F0000 -> 0x006F0000, 4 -> 6 бит)',
    },
    0x3D50: {
        'name': 'saga_major_acts_mask',
        'type': 'uint32 (hi 16b bitmask)',
        'description': 'Битовая маска глобальных актов и союзов Саги (0x022F0000 -> 0x02AF0000, 6 -> 7 бит)',
    },
    0x3D78: {
        'name': 'helheim_escape_mask',
        'type': 'uint32 (hi 16b bitmask)',
        'description': 'Битовая маска закрытия разломов и эвакуации из Хельхейма (0 -> 0x000F0000, 4 бита)',
    },
    0x3D7C: {
        'name': 'norns_sanctuary_mask',
        'type': 'uint32 (hi 16b bitmask)',
        'description': 'Битовая маска преодоления иллюзий Норн и входа в Святилище (0 -> 0x000E0000 -> 0x000F0000, 3 -> 4 бита)',
    },
    0x3D88: {
        'name': 'norns_trail_mask',
        'type': 'uint32 (hi 16b bitmask)',
        'description': 'Битовая маска следов Норн (0x00010000 -> 0x00070000, 1 -> 3 бита)',
    },
    0x8840: {
        'name': 'tracked_entities_count',
        'type': 'uint32',
        'description': 'Количество записей в реестре отслеживаемых сущностей (523 -> 721)',
    },
    0x8864: {
        'name': 'tracked_entities_capacity',
        'type': 'uint32',
        'description': 'Выделенная ёмкость буфера реестра сущностей (2048 -> 4096)',
    },
    0x080444: {
        'name': 'resource_transaction_sequence',
        'type': 'uint32',
        'description': 'Глобальный порядковый номер ресурсных транзакций и событий кошелька (723339 -> 788939)',
    },
}


def get_monotonic_offsets_catalog(save_dir: Path | str | None = None, scan_limit: int = 0x90000) -> dict:
    """Каталогизация монотонно растущих uint32 смещений по всем слотам сохранения (Задача 170).

    Сопоставляет каждое смещение с известными доказанными полями, а остальные
    выписывает со статусом «растёт, назначение неизвестно» без ложных домыслов.
    """
    dirs = [Path(save_dir)] if save_dir else find_save_dirs()
    slots_data: list[bytes] = []
    for d in dirs:
        try:
            for p in sorted(d.glob('GOWRSAVE*')):
                data = p.read_bytes()
                if len(data) >= scan_limit:
                    slots_data.append(data[:scan_limit])
        except OSError:
            continue

    if len(slots_data) < 2:
        return {
            'ok': False,
            'reason': 'недостаточно слотов для сравнительного анализа',
            'proven_offsets': {},
            'unassigned_offsets': [],
            'total_monotonic_count': 0,
        }

    # Сортируем хронологически по порядковому номеру сохранения (0x1BC)
    slots_data.sort(key=lambda b: struct.unpack_from('<I', b, 0x1BC)[0])

    proven_found: dict = {}
    for off, meta in PROVEN_MONOTONIC_OFFSETS.items():
        if off + 4 <= scan_limit:
            vals = [struct.unpack_from('<I', b, off)[0] for b in slots_data]
            proven_found[hex(off)] = {
                'offset': off,
                'name': meta['name'],
                'type': meta['type'],
                'description': meta['description'],
                'initial_value': vals[0],
                'final_value': vals[-1],
                'is_strictly_non_decreasing': all(vals[i] <= vals[i+1] for i in range(len(vals)-1)),
            }

    unassigned: list[dict] = []
    for off in range(0, scan_limit, 4):
        if off in PROVEN_MONOTONIC_OFFSETS:
            continue
        vals = [struct.unpack_from('<I', b, off)[0] for b in slots_data]
        if vals[-1] > vals[0] and all(vals[i] <= vals[i+1] for i in range(len(vals)-1)):
            unassigned.append({
                'offset': off,
                'hex_offset': hex(off),
                'initial_value': vals[0],
                'final_value': vals[-1],
                'status': 'растёт, назначение неизвестно',
            })

    return {
        'ok': True,
        'slots_analyzed': len(slots_data),
        'scan_limit_bytes': scan_limit,
        'proven_offsets': proven_found,
        'unassigned_offsets': unassigned,
        'proven_count': len(proven_found),
        'unassigned_count': len(unassigned),
        'total_monotonic_count': len(proven_found) + len(unassigned),
    }


def count_world_flags(data: bytes) -> int:
    """Подсчёт активных битовых флагов мира (0x00020000 = 1 << 17) в 0x2600..0x36c0.

    Каждое 4-байтовое слово соответствует отдельному объекту/событию мира
    из таблицы 1072 хешей на 0x448..0x25c8. Флаг зажигается монотонно.
    """
    if len(data) < WORLD_FLAGS_END:
        return 0
    cnt = 0
    for off in range(WORLD_FLAGS_START, WORLD_FLAGS_END, 4):
        if struct.unpack_from('<I', data, off)[0] == WORLD_FLAG_ACTIVE_VAL:
            cnt += 1
    return cnt


def format_play_time(seconds: int) -> str:
    """Человеческое время прохождения: '28 ч 21 мин 27 с'."""
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f'{h} ч {m:02d} мин {s:02d} с' if s else f'{h} ч {m:02d} мин'
    if m > 0:
        return f'{m} мин {s:02d} с' if s else f'{m} мин'
    return f'{s} с'


def split_place(place_text: str) -> dict[str, str | None]:
    """Разбивка строки места на компоненты."""
    clean = (place_text or '').strip()
    if not clean:
        return {'realm': None, 'area': None, 'objective': None}
    parts = [p.strip() for p in clean.split(' - ') if p.strip()]
    if len(parts) >= 3:
        return {'realm': parts[0], 'area': parts[1], 'objective': parts[-1]}
    if len(parts) == 2:
        return {'realm': parts[0], 'area': None, 'objective': parts[1]}
    return {'realm': parts[0], 'area': None, 'objective': parts[0]}


def parse_gowr_header(buf: bytes) -> dict | None:
    """Быстрый разбор бинарного заголовка God of War Ragnarök (первые 1088 байт)."""
    if len(buf) < 0x1c0:
        return None

    ver1 = struct.unpack('<I', buf[0x0c:0x10])[0]
    ver2 = struct.unpack('<I', buf[0x4c:0x50])[0]
    if ver1 != MAGIC_VERSION or ver2 != MAGIC_VERSION:
        return None

    ts_raw = struct.unpack('<Q', buf[0:8])[0]
    try:
        save_time = datetime.datetime.fromtimestamp(ts_raw, datetime.timezone.utc)
        save_time_iso = save_time.isoformat()
    except (OSError, OverflowError, ValueError):
        save_time_iso = None

    raw_str = buf[STRING_OFFSET:STRING_OFFSET + STRING_MAX_LEN].split(b'\x00')[0]
    place = raw_str.decode('utf-8', errors='replace').strip() or None
    split_info = split_place(place or '')

    play_seconds = struct.unpack('<I', buf[0x190:0x194])[0]
    ts_32 = struct.unpack('<I', buf[0x194:0x198])[0]
    hacksilver_total = struct.unpack('<I', buf[0x198:0x19c])[0]
    xp_total = struct.unpack('<I', buf[0x19c:0x1a0])[0]
    location_id = struct.unpack('<I', buf[0x1a0:0x1a4])[0]
    zone_id = struct.unpack('<I', buf[0x1a8:0x1ac])[0] if len(buf) >= 0x1ac else None
    stats_counter = struct.unpack('<I', buf[0x1b0:0x1b4])[0] if len(buf) >= 0x1b4 else None
    realm_id = struct.unpack('<I', buf[0x1b8:0x1bc])[0] if len(buf) >= 0x1bc else None
    realm_by_id = REALM_NAMES_BY_ID.get(realm_id) if realm_id is not None else None
    save_counter = struct.unpack('<I', buf[0x1bc:0x1c0])[0]
    diff_byte = buf[0x1c0] if len(buf) > 0x1c0 else 0
    difficulty = DIFFICULTY_LEVELS.get(diff_byte, f'Уровень {diff_byte}')

    raw_prefs = list(buf[0x1c0:0x1e4]) if len(buf) >= 0x1e4 else []
    user_preferences = {
        'difficulty_id': diff_byte,
        'puzzle_timing': buf[0x1c7] if len(buf) > 0x1c7 else None,
        'aim_assist': buf[0x1d0] if len(buf) > 0x1d0 else None,
        'subtitle_size': buf[0x1d7] if len(buf) > 0x1d7 else None,
        'raw_preferences': raw_prefs,
    }

    try:
        import gow_story
        story_info = gow_story.get_story_progress(stats_counter, place)
    except Exception:
        story_info = {}

    ch_title = story_info.get('chapter_title')
    final_objective = split_info['objective']
    final_objective_desc = story_info.get('objective_desc')

    # Задача 195: устранение дублирования названия главы на экране «Данные игры».
    # Когда в строке сохранения (place) и в stats_counter стоит заголовок квеста/главы (например, 19607: «Твари пророчества»),
    # сам шаг цели (19608: «Пройти в лагерь Фрейра») ошибочно уходит в objective_desc.
    # В этом случае истинная цель — это шаг цели, а описание цели — следующий текст из дневника/лора.
    if ch_title and final_objective == ch_title:
        step_candidate = story_info.get('objective_desc')
        if step_candidate:
            final_objective = step_candidate
            lore_desc = None
            try:
                import gowassets
                wad_strings = gowassets.read_language_strings()
                if wad_strings and stats_counter and (stats_counter + 2) in wad_strings:
                    lore_desc = wad_strings[stats_counter + 2]
            except Exception:
                pass
            final_objective_desc = lore_desc

    return {
        'format': 'gowr',
        'place': place,
        'realm': split_info['realm'] or realm_by_id,
        'realm_id': realm_id,
        'zone_id': zone_id,
        'realm_by_id': realm_by_id,
        'area': split_info['area'],
        'objective': final_objective,
        'difficulty': difficulty,
        'difficulty_id': diff_byte,
        'play_seconds': play_seconds,
        'play_time': format_play_time(play_seconds),
        'save_timestamp': ts_raw if ts_raw else ts_32,
        'save_time_utc': save_time_iso,
        'hacksilver_total': hacksilver_total,
        'xp_total': xp_total,
        'location_id': location_id,
        'stats_counter': stats_counter,
        'objective_string_id': stats_counter,
        'stats_counter_status': f'подтверждён ID строки цели, значение {stats_counter}',
        'stats_counter_basis': 'ID строки активного шага цели в r_lang_ru.wad (13466, 14493, 22958, 19608), подтверждено бинарно со строкой 0x50; монотонный счётчик сохранений находится по смещению 0x1BC (save_counter: 773 -> 1305)',
        'save_counter': save_counter,
        'user_preferences': user_preferences,
        'story_progress': story_info,
        'story_percent': story_info.get('story_percent'),
        'chapter': story_info.get('chapter'),
        'chapter_index': story_info.get('chapter_index'),
        'chapters_total': story_info.get('chapters_total'),
        'chapter_title': ch_title,
        'objective_desc': final_objective_desc,
        'remaining_chapters': story_info.get('remaining_chapters'),
        'next_chapter': story_info.get('next_chapter'),
    }


def parse_wallet_resources(data: bytes) -> dict:
    """Разбор кошелька ресурсов, прокачки, реликвий и материалов (HERO Wallet)."""
    needle = struct.pack('<Q', HERO_WALLET_HASH)
    w_off = data.find(needle)
    if w_off == -1:
        return {}

    try:
        count = struct.unpack_from('<I', data, w_off + 8)[0]
    except struct.error:
        return {}

    cur = w_off + 20
    wallet_raw: dict[int, int] = {}
    for _ in range(count):
        if cur + 16 > len(data):
            break
        rh, rq = struct.unpack_from('<QI', data, cur)
        wallet_raw[rh] = rq
        cur += 16

    # Постоянные прибавки к характеристикам (роса Иггдрасиля: +2 к параметру)
    stat_boosts = {
        'strength': wallet_raw.get(0xB34288875C3E1BCC, 0),
        'runic': wallet_raw.get(0x3A7AB925F3863462, 0),
        'defense': wallet_raw.get(0x9C6B2C793C908F41, 0),
        'cooldown': wallet_raw.get(0x2D953C161CDB136A, 0),
    }

    # Улучшения вооружения
    weapon_upgrades = {
        'chaos_flame': wallet_raw.get(0x0B6552BEE68874FA, wallet_raw.get(0x6DBF14545BF30691, 0)),
        'gale_flame': wallet_raw.get(0x27678319710C9A2F, wallet_raw.get(0x29EA3915152A4E92, 0)),
        'frozen_flame': wallet_raw.get(0xEB1FE5F962F01FA6, wallet_raw.get(0x3102377B5A1DF473, 0)),
        'jewel_of_yggdrasil': wallet_raw.get(0xFE5EABE1F74A6D4A, wallet_raw.get(0x5993A40733A11F58, 0)),
    }

    # Квестовые предметы и реликвии
    key_items = {
        'inert_hilt_skofnung': wallet_raw.get(0x7B0502D7C5B3D928, 0),
        'hammer_revolution': wallet_raw.get(0x5A13392A861AFD71, 0),
        'lindwyrm_trap': wallet_raw.get(0xC102E8E1D36FDFB0, 0),
        'lindwyrm_scales': wallet_raw.get(0xC87E473C9761A378, 0),
        'jotunheim_fruit': wallet_raw.get(0xD5D2CA705C3D43BF, 0),
        'resurrection_stone': wallet_raw.get(0x4B618A4A0B900ADA, 0),
    }

    # Выполненные просьбы и выкованная броня
    favors = {
        'lunda_cuirass_crafted': 0xA840E2A18262AF54 in wallet_raw,
        'lunda_belt_crafted': 0xFAAC474DF3F70C20 in wallet_raw,
        'lunda_bracers_crafted': 0xB0C5E31BF288DEE4 in wallet_raw,
        'mysterious_orb_completed': 0x233B569A68CD2AD7 in wallet_raw,
        'skirnir_gambanteinn_found': 0xA3990A964C1021CB in wallet_raw,
    }

    # ──────────────────────────────────────────────────────────────────────
    # Сундуки Норн — тиры, части и перекрёстная сверка (Задача 198)
    # ──────────────────────────────────────────────────────────────────────
    _RAGE_TIER_HASHES = [
        0x6CF01AFB41A1421E,  # T1
        0x6CF01AFB41A15E6F,  # T2
        0x6CF01AFB41A15A78,  # T3
        0x6CF01AFB41A15649,  # T4
        0x6CF01AFB41A1525A,  # T5
    ]
    _HEALTH_TIER_HASHES = [
        0x638E76C7E822F035,  # T1
        0x638E76C7E822F424,  # T2
        0x638E76C7E8220BD3,  # T3
        0x638E76C7E8220FC2,  # T4
        0x638E76C7E82203F1,  # T5
    ]

    blood_mead_horns_total = wallet_raw.get(0x2C22FF2C43DDDA89, 0)
    nornir_chests_opened = wallet_raw.get(0x554185F25EFB1F0A, 0)
    idunn_apples_total = max(0, nornir_chests_opened - blood_mead_horns_total)

    def _find_tier_pieces(tier_hashes: list[int]) -> tuple[int, int]:
        for idx, h in enumerate(tier_hashes):
            qty = wallet_raw.get(h, 0)
            if qty > 0:
                return (idx + 1, qty)
        return (0, 0)

    def _compute_tier_from_total(total: int) -> tuple[int, int]:
        if total <= 0:
            return (0, 0)
        t = 1
        while (t + 1) * t // 2 <= total:
            t += 1
        q = total - t * (t - 1) // 2
        return (t, q)

    rage_wallet_tier, rage_wallet_pieces = _find_tier_pieces(_RAGE_TIER_HASHES)
    health_wallet_tier, health_wallet_pieces = _find_tier_pieces(_HEALTH_TIER_HASHES)

    rage_total_tier, rage_total_pieces = _compute_tier_from_total(blood_mead_horns_total)
    health_total_tier, health_total_pieces = _compute_tier_from_total(idunn_apples_total)

    rage_cross_ok = (
        (rage_total_pieces == 0 and rage_wallet_pieces == 0) or
        (rage_wallet_tier == rage_total_tier and rage_wallet_pieces == rage_total_pieces)
    )
    health_cross_ok = (
        (health_total_pieces == 0 and health_wallet_pieces == 0) or
        (health_wallet_tier == health_total_tier and health_wallet_pieces == health_total_pieces)
    )

    nornir_progress = {
        'nornir_chests_opened': nornir_chests_opened,
        'blood_mead_horns_total': blood_mead_horns_total,
        'idunn_apples_total': idunn_apples_total,
        'rage_tier': rage_total_tier,
        'rage_tier_pieces': rage_total_pieces,
        'health_tier': health_total_tier,
        'health_tier_pieces': health_total_pieces,
        'rage_cross_verified': rage_cross_ok,
        'health_cross_verified': health_cross_ok,
        'proven': rage_cross_ok and health_cross_ok,
        'basis': (
            'sms_std_name_hash(MaxRageUpgradePieceT1..T5), '
            'sms_std_name_hash(MaxHealthUpgradePieceT1..T5), '
            '0x2C22FF2C43DDDA89 = blood_mead_horns_total, '
            '0x554185F25EFB1F0A = nornir_chests_opened, '
            'перекрёстная сверка wallet_tier == computed_tier'
        ),
        '_debug': {
            'rage_wallet_tier': rage_wallet_tier,
            'rage_wallet_pieces': rage_wallet_pieces,
            'health_wallet_tier': health_wallet_tier,
            'health_wallet_pieces': health_wallet_pieces,
        },
    }
    # 03.10.2026: предмет 0x482780EF… — не «убито воронов», а их остаток: игра показывает больше ровно на 3 за
    # каждый открытый дар Древа воронов (0x28FB7355…). Сверено с экраном просьбы «Глаза Одина» дважды:
    # 21.09 экран 16 при предмете 10 и 2 дарах; 02.10 экран 28 при предмете 22 и 2 дарах (GOWRSAVE21).
    odin_ravens_item = wallet_raw.get(0x482780EFF18ED57E, 0)
    odin_raven_chests = wallet_raw.get(0x28FB73555D08478B, 0)
    odin_ravens = odin_ravens_item + 3 * odin_raven_chests

    materials: dict[str, int] = {}
    for rh, qty in wallet_raw.items():
        if qty > 0 and rh in KNOWN_RESOURCE_HASHES:
            key, name, cat = KNOWN_RESOURCE_HASHES[rh]
            if cat in ('материал', 'квест/материал'):
                materials[name] = qty

    # Коллекционные наборы и фрагменты по совпадению старших 32 бит хешей
    guiding_light_hashes = [
        0xF250F487E81B4DA1, 0xF250F487E81B714E, 0xF250F487E81B755F, 0xF250F487E81B796C
    ]
    guiding_light_pieces = sum(1 for h in guiding_light_hashes if wallet_raw.get(h, 0) > 0)

    # 10 доказанных наборов артефактов / коллекционок
    artifact_sets = {
        'guiding_light': {
            'name': 'Путеводный свет (Фрагменты брони Тюра)',
            'pieces_found': guiding_light_pieces,
            'total': 4,
            'completed': guiding_light_pieces == 4,
            'proven': True,
            'basis': 'группа хешей 0xF250F487, монотонный рост 0->3->3->4 по слотам',
        },
        'group_bb10065f': {
            'name': 'Семейные эмблемы (Family Crests)',
            'name_guess': 'Семейные эмблемы (Family Crests)',
            'tag': 'Family',
            'realm': 'Ванахейм',
            'items_found': sum(1 for h in [0xBB10065F6DF7B8C6, 0xBB10065F6DF7BCD7, 0xBB10065F6DF78024, 0xBB10065F6DF78435, 0xBB10065F6DF78802, 0xBB10065F6DF78C13] if wallet_raw.get(h, 0) > 0),
            'total': 6,
            'proven': True,
            'basis': 'r_ui.wad 0x4B23718 tag Family (6 предметов), монотонный рост по слотам',
        },
        'group_d07d480b': {
            'name_guess': 'Набор артефактов (группа D07D480B)',
            'items_found': sum(1 for h in [0xD07D480BB9F9AE6C, 0xD07D480BB9F9B211, 0xD07D480BB9F9BA33, 0xD07D480BB9F9BE20] if wallet_raw.get(h, 0) > 0),
            'total': 4,
            'proven': False,
            'basis': 'группа хешей 0xD07D480B',
        },
        'group_a4caaa0e': {
            'name': 'Оставленные вещи (Things Left Behind)',
            'name_guess': 'Оставленные вещи (Things Left Behind)',
            'tag': 'Things',
            'realm': 'Свартальвхейм',
            'items_found': sum(1 for h in [0xA4CAAA0EF85AE94B, 0xA4CAAA0EF85AED5A, 0xA4CAAA0EF85AE169, 0xA4CAAA0EF85AE578, 0xA4CAAA0EF85AF917, 0xA4CAAA0EF85AFD06] if wallet_raw.get(h, 0) > 0),
            'total': 6,
            'proven': True,
            'basis': 'r_ui.wad 0x4B23778 tag Things (6 предметов), монотонный рост по слотам',
        },
        'group_9e433831': {
            'name': "Стихи Квасира: Свартальвхейм (Kvasir's Poems: Svartalfheim)",
            'name_guess': "Стихи Квасира: Свартальвхейм (Kvasir's Poems: Svartalfheim)",
            'tag': 'Svarta',
            'realm': 'Свартальвхейм',
            'items_found': sum(1 for h in [0x9E43383176B3FB8B, 0x9E43383176B3E7FC, 0x9E43383176B3E3ED, 0x9E43383176B3EFDE, 0x9E43383176B3EBCF] if wallet_raw.get(h, 0) > 0),
            'total': 5,
            'proven': True,
            'basis': "r_ui.wad 0x4B23678 tag Svarta (5 поэм Квасира)",
        },
        'group_8e39a7ad': {
            'name_guess': 'Набор артефактов (группа 8E39A7AD)',
            'items_found': sum(1 for h in [0x8E39A7ADFF2A4061, 0x8E39A7ADFF2A4476, 0x8E39A7ADFF2A5803] if wallet_raw.get(h, 0) > 0),
            'total': 3,
            'proven': False,
            'basis': 'группа хешей 0x8E39A7AD',
        },
        'group_7b32ed8f': {
            'name': 'Подношения Фрейру (Tributes to Freyr)',
            'name_guess': 'Подношения Фрейру (Tributes to Freyr)',
            'tag': 'Tribut',
            'realm': 'Альвхейм',
            'items_found': sum(1 for h in [0x7B32ED8F4BF7D053, 0x7B32ED8F4BF7D442, 0x7B32ED8F4BF7D84D, 0x7B32ED8F4BF7DC5C, 0x7B32ED8F4BF7C02F, 0x7B32ED8F4BF7C43E] if wallet_raw.get(h, 0) > 0),
            'total': 6,
            'proven': True,
            'basis': 'r_ui.wad 0x4B235E8 tag Tribut (6 предметов), alf_bluff300_outerwell.wad',
        },
        'group_36218493': {
            'name_guess': 'Набор артефактов (группа 36218493)',
            'items_found': sum(1 for h in [0x3621849355F013B6, 0x3621849355F0E06A, 0x3621849355F0E848] if wallet_raw.get(h, 0) > 0),
            'total': 3,
            'proven': False,
            'basis': 'группа хешей 0x36218493',
        },
        'group_12bca41f': {
            'name': "Стихи Квасира: Альвхейм (Kvasir's Poems: Alfheim)",
            'name_guess': "Стихи Квасира: Альвхейм (Kvasir's Poems: Alfheim)",
            'tag': 'Alfhei',
            'realm': 'Альвхейм',
            'items_found': sum(1 for h in [0x12BCA41F6E79CE9A, 0x12BCA41F6E79D2EB, 0x12BCA41F6E79D6E4, 0x12BCA41F6E79DAD5, 0x12BCA41F6E79DEC6] if wallet_raw.get(h, 0) > 0),
            'total': 5,
            'proven': True,
            'basis': "r_ui.wad 0x4B236C8 tag Alfhei (5 поэм Квасира)",
        },
        'group_5dde0b39': {
            'name_guess': 'Набор артефактов (группа 5DDE0B39)',
            'items_found': sum(1 for h in [0x5DDE0B394906F3B6, 0x5DDE0B394906FB98, 0x5DDE0B394906FF89] if wallet_raw.get(h, 0) > 0),
            'total': 3,
            'proven': False,
            'basis': 'группа хешей 0x5DDE0B39',
        },
    }

    # Задача 198: 0x2C22FF2C43DDDA89 — это blood_mead_horns_total, а НЕ норы драугров.
    # Счётчик уже вычислен выше в nornir_progress.

    stolen_hashes = [
        0xE724D1990BE437FE, 0xE724D1990BE43BD1, 0xE724D1990BE43FC0,
        0xE724D1990BE423B3, 0xE724D1990BE427A2, 0xE724D1990BE42B95
    ]
    stolen_treasures_count = sum(1 for h in stolen_hashes if wallet_raw.get(h, 0) > 0)

    kvasir_svartalfheim = sum(1 for h in [0x9E43383176B3FB8B, 0x9E43383176B3E7FC, 0x9E43383176B3E3ED, 0x9E43383176B3EFDE, 0x9E43383176B3EBCF] if wallet_raw.get(h, 0) > 0)
    kvasir_alfheim = sum(1 for h in [0x12BCA41F6E79CE9A, 0x12BCA41F6E79D2EB, 0x12BCA41F6E79D6E4, 0x12BCA41F6E79DAD5, 0x12BCA41F6E79DEC6] if wallet_raw.get(h, 0) > 0)
    kvasir_vanaheim = sum(1 for h in [0xF2B5C1532D9454D1, 0xF2B5C1532D9450C0, 0xF2B5C1532D945CFF] if wallet_raw.get(h, 0) > 0)
    kvasir_midgard = 1 if wallet_raw.get(0x5AB11479E4B19F47, 0) > 0 else 0
    kvasir_total = kvasir_svartalfheim + kvasir_alfheim + kvasir_vanaheim + kvasir_midgard

    # Количество разблокированных навыков в дереве способностей
    skills_count = 0
    after_w = w_off + 12 + count * 16
    if after_w + 8 <= len(data):
        v1, s_cnt = struct.unpack_from('<II', data, after_w)
        if v1 == 1 and 0 < s_cnt < 1000:
            skills_count = s_cnt

    return {
        'wallet_hacksilver': wallet_raw.get(0x5AE80674D240529E, 0),
        'divine_ashes': wallet_raw.get(0x1E62B3ECB450EE3B, 0),
        'kratos_xp': wallet_raw.get(0x9C7CF61C839B9A8A, 0),
        'atreus_xp': wallet_raw.get(0xA1D028F9B467E25C, wallet_raw.get(0xAC98E8B5155F2C73, 0)),
        'freya_xp': wallet_raw.get(0xE577D004DA4F5243, 0),
        'blood_mead_horns': nornir_progress['rage_tier_pieces'],
        'idunn_apples': nornir_progress['health_tier_pieces'],
        'nornir_progress': nornir_progress,
        'amulet_jewels': weapon_upgrades['jewel_of_yggdrasil'],
        'gale_flame': weapon_upgrades['gale_flame'],
        'chaos_flame': weapon_upgrades['chaos_flame'],
        'frozen_flame': weapon_upgrades['frozen_flame'],
        'odin_ravens': odin_ravens,
        'odin_raven_chests': odin_raven_chests,
        'skills_count': skills_count,
        'stat_boosts': stat_boosts,
        'weapon_upgrades': weapon_upgrades,
        'key_items': key_items,
        'favors': favors,
        'materials': materials,
        'guiding_light': artifact_sets['guiding_light'],
        'artifact_sets': artifact_sets,
        'draugr_holes': nornir_progress['blood_mead_horns_total'],  # обратная совместимость (ошибочное имя задачи 191)
        'stolen_treasures': stolen_treasures_count,
        'kvasir_poems': {
            'collected': kvasir_total,
            'total': 14,
            'by_realm': {
                'svartalfheim': kvasir_svartalfheim,
                'alfheim': kvasir_alfheim,
                'vanaheim': kvasir_vanaheim,
                'midgard': kvasir_midgard,
            },
            'proven': True,
            'basis': 'r_ui.wad 0x4B23648..0x4B23718 (14 поэм по 4 мирам)',
        },
    }


def parse_story_milestones(data: bytes) -> dict:
    """Извлечение пройденных сюжетных вех, боссов, спутников и исследования миров."""
    cutscenes = re.findall(b'C_\\d{3}_[A-Za-z0-9_]+', data)
    unique_cuts = sorted(set(c.decode('ascii') for c in cutscenes))

    milestones = {}
    for marker, key, desc in MILESTONE_CUTSCENES:
        milestones[key] = {
            'achieved': marker.encode('ascii') in data,
            'description': desc,
        }

    bosses = {}
    for marker, key, desc in BOSS_ENCOUNTER_MARKERS:
        bosses[key] = {
            'achieved': marker.encode('ascii') in data,
            'description': desc,
        }

    companions = {}
    for marker, key, name in COMPANION_MARKERS:
        companions[key] = {
            'present': marker.encode('ascii') in data,
            'name': name,
        }

    realms_exploration = {}
    for realm_name, pattern in REALM_CHECKPOINT_PREFIXES.items():
        found = set(re.findall(pattern, data))
        realms_exploration[realm_name] = len(found)

    # Визиты в убежища / базы (Дом Синдри, Чертог Одина и Лагерь Фрейра)
    sindri_visits = sorted(set(s.decode('ascii') for s in re.findall(rb'Base_SindriHouse_Visit\d+[A-Za-z]?', data)))
    odin_visits = sorted(set(s.decode('ascii') for s in re.findall(rb'Base_OdinHouse_Visit\d+[A-Za-z]?', data)))
    freyr_visits = sorted(set(s.decode('ascii') for s in re.findall(rb'Base_FreyrCamp_Visit\d+[A-Za-z]?', data)))

    base_visits = {
        'sindri_sanctuary': {
            'visits_count': len(sindri_visits),
            'max_visits': 8,
            'visits': sindri_visits,
            'latest_visit': sindri_visits[-1] if sindri_visits else None,
        },
        'odin_great_lodge': {
            'visits_count': len(odin_visits),
            'max_visits': 4,
            'visits': odin_visits,
            'latest_visit': odin_visits[-1] if odin_visits else None,
        },
        'freyr_camp': {
            'visits_count': len(freyr_visits),
            'max_visits': 7,
            'visits': freyr_visits,
            'latest_visit': freyr_visits[-1] if freyr_visits else None,
        },
    }

    # Поиск присутствующих акторов персонажей из 26 структур Santa Monica Engine
    present_actors = {}
    for act_tag, (act_title, act_category) in CHAR_ACTORS.items():
        if act_tag.encode('ascii') in data:
            present_actors[act_tag] = {
                'name': act_title,
                'category': act_category,
            }

    # Определение активного управляемого героя (Кратос vs Атрей)
    realm_id_val = struct.unpack_from('<I', data, 0x1b8)[0] if len(data) >= 0x1bc else None
    is_atreus_player = (b'PLYR_Nav_Base_Idle_Atr' in data) and (realm_id_val == 3)
    active_hero = 'Атрей' if is_atreus_player else 'Кратос'

    return {
        'cutscenes_count': len(unique_cuts),
        'latest_cutscene': unique_cuts[-1] if unique_cuts else None,
        'cutscenes': unique_cuts,
        'milestones': milestones,
        'bosses': bosses,
        'companions': companions,
        'realms_exploration': realms_exploration,
        'base_visits': base_visits,
        'actors_catalog': present_actors,
        'active_hero': active_hero,
    }


def parse_save_file(path: Path | str, detailed: bool = True) -> dict | None:
    """Чтение одного файла сохранения с опциональным глубоким разбором."""
    p = Path(path)
    if not p.is_file():
        return None
    try:
        if detailed:
            data = p.read_bytes()
            buf = data[:HEADER_SIZE]
        else:
            with open(p, 'rb') as f:
                buf = f.read(HEADER_SIZE)
            data = None
        stat = p.stat()
    except OSError:
        return None

    parsed = parse_gowr_header(buf)
    if not parsed:
        return None

    parsed.update({
        'path': str(p.resolve()),
        'slot': p.name,
        'file_size': stat.st_size,
        'mtime': stat.st_mtime,
    })

    if detailed and data:
        wallet = parse_wallet_resources(data)
        if wallet:
            parsed['wallet'] = wallet
            # Подставляем актуальное серебро из кошелька
            if 'wallet_hacksilver' in wallet:
                parsed['hacksilver'] = wallet['wallet_hacksilver']
        story = parse_story_milestones(data)
        if story:
            parsed['story'] = story

        # Уровни надетых предметов экипировки (крафтовые ранги 1..9) и активные слоты
        gear_levels = []
        leveled_items = []
        equipped_gear = {}
        equipped_hashes = []
        relic = None
        slotted_enchantments = []
        hero_pos = data.find(b'Char_HeroA00')
        if hero_pos != -1:
            start = hero_pos
            end = min(len(data), start + 0x2000)
            cur = start
            while cur < end:
                if cur + 13 <= end and data[cur + 8] == 3:
                    lvl = struct.unpack_from('<i', data, cur + 9)[0]
                    h = struct.unpack_from('<Q', data, cur)[0]
                    if 0 <= lvl <= 9 and h != 0:
                        gear_levels.append(lvl)
                        item_dict = {
                            'hash': hex(h),
                            'upgrade_tier': lvl,
                            'level': lvl + 1,
                            'tag': 3,
                        }
                        if h in KEY_EQUIPMENT_MAP:
                            slot_id, slot_title = KEY_EQUIPMENT_MAP[h]
                            item_dict['slot'] = slot_id
                            item_dict['name'] = slot_title
                            equipped_gear[slot_id] = item_dict
                        leveled_items.append(item_dict)
                        cur += 13
                        continue
                if cur + 10 <= end and data[cur + 8] == 1 and data[cur + 9] == 1:
                    h = struct.unpack_from('<Q', data, cur)[0]
                    if h != 0 and h != 0x83c00000000:
                        equipped_hashes.append(hex(h))
                        cur += 10
                        continue
                cur += 1

        parsed['gear_levels'] = gear_levels
        parsed['max_gear_level'] = max(gear_levels) if gear_levels else None

        # Общий уровень силы Кратоса (Power Level на базе надетой экипировки)
        if equipped_gear:
            avg_lvl = sum(g['level'] for g in equipped_gear.values()) / len(equipped_gear)
            power_level = round(avg_lvl)
        else:
            power_level = parsed['max_gear_level']
        parsed['power_level'] = power_level

        # Индивидуальное структурирование оружия, брони и щитов (задача 168)
        weapons = {}
        if 'weapon_primary' in equipped_gear:
            weapons['axe'] = {
                'name_guess': 'Топор Левиафан',
                'level': equipped_gear['weapon_primary']['level'],
                'tier': equipped_gear['weapon_primary']['upgrade_tier'],
                'hash': equipped_gear['weapon_primary']['hash'],
                'proven': False,
                'basis': 'порядок слотов в блоке Char_HeroA00',
            }
        if 'weapon_pommel' in equipped_gear:
            weapons['axe_pommel'] = {
                'name_guess': equipped_gear['weapon_pommel']['name'],
                'level': equipped_gear['weapon_pommel']['level'],
                'tier': equipped_gear['weapon_pommel']['upgrade_tier'],
                'hash': equipped_gear['weapon_pommel']['hash'],
                'proven': False,
                'basis': 'порядок слотов в блоке Char_HeroA00',
            }
        if 'weapon_secondary' in equipped_gear:
            weapons['blades'] = {
                'name_guess': 'Клинки Хаоса',
                'level': equipped_gear['weapon_secondary']['level'],
                'tier': equipped_gear['weapon_secondary']['upgrade_tier'],
                'hash': equipped_gear['weapon_secondary']['hash'],
                'proven': False,
                'basis': 'порядок слотов в блоке Char_HeroA00',
            }
        if 'blades_handles' in equipped_gear:
            weapons['blades_handles'] = {
                'name_guess': equipped_gear['blades_handles']['name'],
                'level': equipped_gear['blades_handles']['level'],
                'tier': equipped_gear['blades_handles']['upgrade_tier'],
                'hash': equipped_gear['blades_handles']['hash'],
                'proven': False,
                'basis': 'порядок слотов в блоке Char_HeroA00',
            }
        if 'weapon_spear' in equipped_gear:
            weapons['spear'] = {
                'name_guess': 'Копьё Драупнир',
                'level': equipped_gear['weapon_spear']['level'],
                'tier': equipped_gear['weapon_spear']['upgrade_tier'],
                'hash': equipped_gear['weapon_spear']['hash'],
                'proven': False,
                'basis': 'порядок слотов в блоке Char_HeroA00',
            }
        if 'spear_sauroter' in equipped_gear:
            weapons['spear_sauroter'] = {
                'name_guess': equipped_gear['spear_sauroter']['name'],
                'level': equipped_gear['spear_sauroter']['level'],
                'tier': equipped_gear['spear_sauroter']['upgrade_tier'],
                'hash': equipped_gear['spear_sauroter']['hash'],
                'proven': False,
                'basis': 'порядок слотов в блоке Char_HeroA00',
            }

        armor = {}
        if 'armor_chest' in equipped_gear:
            armor['chest'] = {
                'name_guess': equipped_gear['armor_chest']['name'],
                'level': equipped_gear['armor_chest']['level'],
                'tier': equipped_gear['armor_chest']['upgrade_tier'],
                'hash': equipped_gear['armor_chest']['hash'],
                'proven': False,
                'basis': 'порядок слотов в блоке Char_HeroA00',
            }
        if 'armor_wrist' in equipped_gear:
            armor['wrist'] = {
                'name_guess': equipped_gear['armor_wrist']['name'],
                'level': equipped_gear['armor_wrist']['level'],
                'tier': equipped_gear['armor_wrist']['upgrade_tier'],
                'hash': equipped_gear['armor_wrist']['hash'],
                'proven': False,
                'basis': 'порядок слотов в блоке Char_HeroA00',
            }
        if 'armor_waist' in equipped_gear:
            armor['waist'] = {
                'name_guess': equipped_gear['armor_waist']['name'],
                'level': equipped_gear['armor_waist']['level'],
                'tier': equipped_gear['armor_waist']['upgrade_tier'],
                'hash': equipped_gear['armor_waist']['hash'],
                'proven': False,
                'basis': 'порядок слотов в блоке Char_HeroA00',
            }

        shields = {}
        if 'shield' in equipped_gear:
            shields['shield'] = {
                'name_guess': 'Щит',
                'level': equipped_gear['shield']['level'],
                'tier': equipped_gear['shield']['upgrade_tier'],
                'hash': equipped_gear['shield']['hash'],
                'proven': False,
                'basis': 'порядок слотов в блоке Char_HeroA00',
            }
        if 'shield_rond' in equipped_gear:
            shields['rond'] = {
                'name_guess': 'Ронд щита',
                'level': equipped_gear['shield_rond']['level'],
                'tier': equipped_gear['shield_rond']['upgrade_tier'],
                'hash': equipped_gear['shield_rond']['hash'],
                'proven': False,
                'basis': 'порядок слотов в блоке Char_HeroA00',
            }

        # Индивидуальное снаряжение спутника (Атрея) в блоке Char_Atreus00
        companion_loadout = []
        atreus_pos = data.find(b'Char_Atreus00')
        if atreus_pos != -1:
            sub = data[atreus_pos:atreus_pos + 0x1500]
            for cur in range(len(sub) - 13):
                if sub[cur + 8] == 3:
                    lvl = struct.unpack_from('<i', sub, cur + 9)[0]
                    h = struct.unpack_from('<Q', sub, cur)[0]
                    if 0 <= lvl <= 9 and h > 0x1000:
                        companion_loadout.append({
                            'hash': hex(h),
                            'upgrade_tier': lvl,
                            'level': lvl + 1,
                        })

        # Рунические атаки оружия (быстрая и мощная) в слотах Char_HeroA00
        runic_attacks = {}
        if hero_pos != -1:
            hero_sub = data[hero_pos:hero_pos + 0x2000]

            def extract_weapon_runics(w_hash: int) -> dict:
                w_idx = hero_sub.find(struct.pack('<Q', w_hash))
                if w_idx == -1:
                    return {'light': False, 'heavy': False, 'light_hash': None, 'heavy_hash': None}
                cur_w = w_idx + 13
                slots_w = []
                while cur_w < w_idx + 70 and len(slots_w) < 2:
                    if cur_w + 10 <= len(hero_sub) and hero_sub[cur_w + 8] == 1:
                        h = struct.unpack_from('<Q', hero_sub, cur_w)[0]
                        eq = bool(hero_sub[cur_w + 9])
                        slots_w.append((eq, hex(h) if eq else None))
                        cur_w += 10
                    else:
                        cur_w += 1
                return {
                    'light': slots_w[0][0] if len(slots_w) > 0 else False,
                    'heavy': slots_w[1][0] if len(slots_w) > 1 else False,
                    'light_hash': slots_w[0][1] if len(slots_w) > 0 else None,
                    'heavy_hash': slots_w[1][1] if len(slots_w) > 1 else None,
                }

            def enrich_runic_attack(h_hex: str | None) -> dict | None:
                if not h_hex:
                    return None
                try:
                    h_int = int(h_hex, 16)
                except ValueError:
                    return None
                meta = PROVEN_RUNIC_ATTACKS.get(h_int)
                if meta:
                    return {
                        'hash': h_hex,
                        'name': meta['name'],
                        'name_en': meta['name_en'],
                        'cooldown_sec': meta.get('cooldown_sec'),
                        'proven': True,
                    }
                return {
                    'hash': h_hex,
                    'name': None,
                    'name_en': None,
                    'cooldown_sec': None,
                    'proven': False,
                }

            axe_r = extract_weapon_runics(0x083E95365CC16313)
            blades_r = extract_weapon_runics(0x5EDA95A2FC221AEE)
            spear_r = extract_weapon_runics(0xA1E318FD889AD3BA)
            total_r = sum([axe_r['light'], axe_r['heavy'], blades_r['light'], blades_r['heavy'], spear_r['light'], spear_r['heavy']])
            runic_attacks = {
                'axe': {
                    'name_guess': 'Топор Левиафан',
                    'light': axe_r['light'],
                    'heavy': axe_r['heavy'],
                    'light_hash': axe_r['light_hash'],
                    'heavy_hash': axe_r['heavy_hash'],
                    'light_attack': enrich_runic_attack(axe_r['light_hash']),
                    'heavy_attack': enrich_runic_attack(axe_r['heavy_hash']),
                    'equipped_count': int(axe_r['light']) + int(axe_r['heavy']),
                    'proven': True,
                    'basis': 'порядок слотов в блоке Char_HeroA00',
                },
                'blades': {
                    'name_guess': 'Клинки Хаоса',
                    'light': blades_r['light'],
                    'heavy': blades_r['heavy'],
                    'light_hash': blades_r['light_hash'],
                    'heavy_hash': blades_r['heavy_hash'],
                    'light_attack': enrich_runic_attack(blades_r['light_hash']),
                    'heavy_attack': enrich_runic_attack(blades_r['heavy_hash']),
                    'equipped_count': int(blades_r['light']) + int(blades_r['heavy']),
                    'proven': True,
                    'basis': 'порядок слотов в блоке Char_HeroA00',
                },
                'spear': {
                    'name_guess': 'Копьё Драупнир',
                    'light': spear_r['light'],
                    'heavy': spear_r['heavy'],
                    'light_hash': spear_r['light_hash'],
                    'heavy_hash': spear_r['heavy_hash'],
                    'light_attack': enrich_runic_attack(spear_r['light_hash']),
                    'heavy_attack': enrich_runic_attack(spear_r['heavy_hash']),
                    'equipped_count': int(spear_r['light']) + int(spear_r['heavy']),
                    'proven': True,
                    'basis': 'порядок слотов в блоке Char_HeroA00',
                },
                'total_equipped': total_r,
                'slots_total': 6,
                'proven': True,
                'basis': 'слоты рунических атак в блоках оружия Char_HeroA00, монотонный рост 0->2->3->4 по 15 слотам',
            }

            # Активная реликвия (рукоять / талисман) и чары Амулета в блоке Char_HeroA00
            relic = None
            slotted_enchantments = []
            waist_idx = hero_sub.find(struct.pack('<Q', 0x735D31B293869CC0))
            blades_idx = hero_sub.find(struct.pack('<Q', 0x5EDA95A2FC221AEE))
            if waist_idx != -1:
                cur_rel = waist_idx + 13
                for _ in range(6):
                    if cur_rel + 10 <= len(hero_sub) and hero_sub[cur_rel + 8] == 1:
                        if hero_sub[cur_rel + 9] == 1:
                            r_hash = struct.unpack_from('<Q', hero_sub, cur_rel)[0]
                            relic = {
                                'hash': hex(r_hash),
                                'equipped': True,
                                'proven': True,
                                'basis': 'активный слот талисмана/реликвии в Char_HeroA00 (смещение 0xd1a92)',
                            }
                            break
                        cur_rel += 10
            if waist_idx != -1 and blades_idx != -1 and blades_idx > waist_idx:
                ench_sub = hero_sub[waist_idx + 13 + 60:blades_idx]
                c_e = 0
                while c_e <= len(ench_sub) - 10:
                    if ench_sub[c_e + 8] == 1 and ench_sub[c_e + 9] == 1:
                        eh = struct.unpack_from('<Q', ench_sub, c_e)[0]
                        if eh > 0x1000:
                            slotted_enchantments.append(hex(eh))
                        c_e += 10
                    elif ench_sub[c_e + 8] == 3:
                        c_e += 13
                    else:
                        c_e += 1

        # Детализированное описание чар Амулета Иггдрасиля (Задача 191)
        enchantments_detailed = []
        for eh_hex in slotted_enchantments:
            try:
                eh_int = int(eh_hex, 16)
            except ValueError:
                continue
            meta_ench = PROVEN_AMULET_ENCHANTMENTS.get(eh_int)
            if meta_ench:
                enchantments_detailed.append({
                    'hash': eh_hex,
                    'name': meta_ench['name'],
                    'name_en': meta_ench['name_en'],
                    'set': meta_ench['set'],
                    'proven': True,
                    'basis': meta_ench['basis'],
                })
            else:
                enchantments_detailed.append({
                    'hash': eh_hex,
                    'name': None,
                    'name_en': None,
                    'set': None,
                    'proven': False,
                    'basis': 'слот в блоке Char_HeroA00',
                })

        # Недоказанные/безымянные слоты остаются номерами (без ложных догадок)
        unassigned_items = [it for it in leveled_items if 'slot' not in it]

        parsed['loadout'] = {
            'power_level': power_level,
            'max_gear_level': parsed['max_gear_level'],
            'weapons': weapons,
            'armor': armor,
            'shields': shields,
            'equipped_gear': equipped_gear,
            'runic_attacks': runic_attacks,
            'relic': relic,
            'slotted_enchantments': slotted_enchantments,
            'enchantments_detailed': enchantments_detailed,
            'gear_levels': [it['level'] for it in leveled_items],
            'leveled_items': leveled_items,
            'unassigned_items': unassigned_items,
            'companion_loadout': companion_loadout,
            'equipped_hashes_count': len(equipped_hashes),
            'equipped_hashes': equipped_hashes[:30],
        }
        parsed['active_hero'] = story.get('active_hero', 'Кратос') if story else 'Кратос'

        # Прогресс Амулета Иггдрасиля
        amulet_jewels = (wallet or {}).get('amulet_jewels', 0)
        parsed['amulet'] = {
            'jewels_found': amulet_jewels,
            'sockets_unlocked': min(9, 2 + amulet_jewels),
            'sockets_total': 9,
            'proven': True,
            'basis': 'кошелёк jewel_of_yggdrasil и базовые 2 слота амулета',
        }

        # Чеклист коллекционок и квестов (для компаньона и аналитики)
        w = wallet or {}
        key_items = w.get('key_items') or {}
        favors = w.get('favors') or {}
        ravens_cnt = w.get('odin_ravens', 0)
        lindwyrms_cnt = key_items.get('lindwyrm_scales', 0)
        lunda_cuirass = favors.get('lunda_cuirass_crafted', False)
        lunda_bracers = favors.get('lunda_bracers_crafted', False)
        lunda_belt = favors.get('lunda_belt_crafted', False)
        lunda_complete = bool(lunda_cuirass and lunda_bracers and lunda_belt)
        skills_count = w.get('skills_count', 0)

        # Реестр отслеживаемых динамических сущностей (смещение 0x8840, задача 170)
        tracked_entities = None
        if len(data) >= 0x886C:
            te_cnt = struct.unpack_from('<I', data, 0x8840)[0]
            te_cap = struct.unpack_from('<I', data, 0x8864)[0]
            if 0 < te_cnt <= te_cap and te_cap <= 65536:
                archetype_counts: dict[str, int] = {}
                records_start = 0x886C
                records_end = records_start + te_cnt * 24
                if records_end <= len(data):
                    for idx in range(te_cnt):
                        off = records_start + idx * 24
                        _tag, _eid, arch = struct.unpack_from('<QQQ', data, off)
                        arch_key = f"0x{arch:X}"
                        archetype_counts[arch_key] = archetype_counts.get(arch_key, 0) + 1

                top_archetypes = dict(sorted(archetype_counts.items(), key=lambda x: x[1], reverse=True)[:5])

                tracked_entities = {
                    'count': te_cnt,
                    'capacity': te_cap,
                    'record_size': 24,
                    'array_offset_start': records_start,
                    'array_offset_end': records_end,
                    'unique_archetypes_count': len(archetype_counts),
                    'top_archetypes': top_archetypes,
                }
                parsed['tracked_entities'] = tracked_entities

        # Реестр инвентарных ресурсов и материалов (смещение 0x080440..0x0889A2, доказана монотонность транзакций)
        inventory_summary = None
        res_seq = None
        if len(data) >= 0x080450:
            res_seq = struct.unpack_from('<I', data, 0x080444)[0]
            parsed['resource_transaction_sequence'] = res_seq
            seg_len = min(len(data), 0x0889A2) - 0x080450
            rec_cnt = 0
            for i_off in range(0x080450, 0x080450 + seg_len, 16):
                rec = data[i_off:i_off+16]
                if any(rec):
                    rec_cnt += 1
            inventory_summary = {
                'transaction_sequence': res_seq,
                'item_records_count': rec_cnt,
                'record_size': 16,
                'array_offset_start': 0x080450,
                'array_offset_end': 0x0889A2,
                'proven': True,
                'basis': 'монотонный рост транзакций 723339 -> 788939 по 15 слотам',
            }
            parsed['inventory_summary'] = inventory_summary

        world_flags_cnt = count_world_flags(data)
        endgame = {
            'berserkers': {
                'quest_unlocked': bool(key_items.get('inert_hilt_skofnung', 0)),
                'kings_grave_visited': b'Mid_Cal700_KingsArena' in data,
                'total_gravestones': 12,
                'gravestones_cleared': 0,
                'king_hrolf_defeated': bool(key_items.get('hilt_skofnung', 0)),
                'unproven': ['gravestones_cleared', 'king_hrolf_defeated'],
            },
            'valkyrie_queen_gna': {
                'arena_unlocked': b'Msp_Mount400_UpperArena' in data,
                'council_visited': b'Mid_Cal385_ValkyrieCouncil' in data,
                'defeated': False,
                'unproven': ['defeated'],
            },
        }

        quest_stages = parse_quest_stages(data)
        parsed['quest_stages'] = quest_stages

        if story:
            story['quest_stages'] = quest_stages
            story['endgame'] = endgame
            story['world_flags_active'] = world_flags_cnt

        parsed['collectibles'] = {
            'ravens': {
                'collected': ravens_cnt,
                'total': 48,
                'remaining': max(0, 48 - ravens_cnt),
                'asgard_outskirts': b'Asg_OutSkrt090_Raven' in data,
                'tree_visited': b'Nif_RavenTree100_Main' in data,
            },
            'idunn_apples': w.get('idunn_apples', 0),
            'blood_mead_horns': w.get('blood_mead_horns', 0),
            'nornir_progress': w.get('nornir_progress'),
            'lindwyrms': {
                'captured': lindwyrms_cnt,
                'total': 6,
                'remaining': max(0, 6 - lindwyrms_cnt),
            },
            'lunda_armor_set': {
                'cuirass': lunda_cuirass,
                'bracers': lunda_bracers,
                'belt': lunda_belt,
                'complete': lunda_complete,
            },
            'berserkers': endgame['berserkers'],
            'valkyrie_queen': endgame['valkyrie_queen_gna'],
            'endgame': endgame,
            'raven_tree': {
                'visited': b'Nif_RavenTree100_Main' in data,
                'chests_opened': w.get('odin_raven_chests', 0),
                'chests_total': 6,
                'chests_remaining': max(0, 6 - w.get('odin_raven_chests', 0)),
            },
            'skill_tree': {
                'unlocked_skills': skills_count,
                'total_skills': 160,
                'progress_percent': round((skills_count / 160) * 100, 1) if skills_count else 0.0,
            },
            'world_flags_active': world_flags_cnt,
            'tracked_entities': tracked_entities,
            'inventory_summary': inventory_summary,
            'resource_transaction_sequence': res_seq,
            'guiding_light': w.get('guiding_light'),
            'artifact_sets': w.get('artifact_sets'),
            # Задача 198: 0x2C22FF2C43DDDA89 = blood_mead_horns_total, а не норы драугров
            'draugr_holes': {
                'completed': w.get('draugr_holes', 0),
                'total': None,
                'favor_completed': False,
                'proven': False,
                'basis': 'ОШИБКА задачи 191 исправлена задачей 198: 0x2C22FF2C43DDDA89 = blood_mead_horns_total, а не норы драугров',
            },
            'stolen_treasures': {
                'collected': w.get('stolen_treasures', 0),
                'total': 6,
                'realm': 'Мидгард',
                'proven': True,
                'basis': 'r_ui.wad 0x4B237D8 tag Stolen (6 предметов)',
            },
            'kvasir_poems': w.get('kvasir_poems'),
            'update_policy': 'обновляется при каждом автосохранении',
            'key_items': key_items,
            'favors': favors,
            'by_realm': {
                'vanaheim': {
                    'name': 'Ванахейм',
                    'ravens_total': 15,
                    'ravens_collected': None,
                    'ravens_remaining': None,
                    'nornir_chests_total': 11,
                    'nornir_chests_remaining': None,
                    'status': 'unknown',
                    'proven': False,
                    'note': 'Помировые счетчики воронов и сундуков Норн в теле сохранения не хранятся отдельными числами (хранятся глобально в HERO Wallet)',
                },
                'svartalfheim': {
                    'name': 'Свартальвхейм',
                    'ravens_total': 13,
                    'ravens_collected': None,
                    'ravens_remaining': None,
                    'nornir_chests_total': 10,
                    'nornir_chests_remaining': None,
                    'status': 'unknown',
                    'proven': False,
                    'note': 'Помировые счетчики воронов и сундуков Норн в теле сохранения не хранятся отдельными числами (хранятся глобально в HERO Wallet)',
                },
                'midgard': {
                    'name': 'Мидгард',
                    'ravens_total': 6,
                    'ravens_collected': None,
                    'ravens_remaining': None,
                    'nornir_chests_total': 4,
                    'nornir_chests_remaining': None,
                    'status': 'unknown',
                    'proven': False,
                    'note': 'Помировые счетчики воронов и сундуков Норн в теле сохранения не хранятся отдельными числами (хранятся глобально в HERO Wallet)',
                },
                'alfheim': {
                    'name': 'Альвхейм',
                    'ravens_total': 10,
                    'ravens_collected': None,
                    'ravens_remaining': None,
                    'nornir_chests_total': 7,
                    'nornir_chests_remaining': None,
                    'hel_tears_completed': 1 if (b'Alf_Trench200_AI_HelTear' in data) else 0,
                    'draugr_holes_completed': 1 if (b'Alf_DWest200_AI_DraugrHole' in data) else 0,
                    'status': 'unknown',
                    'proven': False,
                    'note': 'Помировые счетчики воронов и сундуков Норн в теле сохранения не хранятся отдельными числами (хранятся глобально в HERO Wallet)',
                },
                'asgard': {
                    'name': 'Асгард',
                    'ravens_total': 2,
                    'ravens_collected': None,
                    'ravens_remaining': None,
                    'asgard_outskirts_raven_encountered': b'Asg_OutSkrt090_Raven' in data,
                    'nornir_chests_total': 0,
                    'nornir_chests_remaining': 0,
                    'status': 'unknown',
                    'proven': False,
                    'note': 'Строка Asg_OutSkrt090_Raven подтверждает присутствие записи ворона, но флаг сбития требует дальнейшей привязки',
                },
                'helheim': {
                    'name': 'Хельхейм',
                    'ravens_total': 2,
                    'ravens_collected': None,
                    'ravens_remaining': None,
                    'nornir_chests_total': 0,
                    'nornir_chests_remaining': 0,
                    'status': 'unknown',
                    'proven': False,
                    'note': 'Помировые счетчики воронов и сундуков Норн в теле сохранения не хранятся отдельными числами (хранятся глобально в HERO Wallet)',
                },
                'muspelheim': {
                    'name': 'Муспельхейм',
                    'ravens_total': 2,
                    'ravens_collected': None,
                    'ravens_remaining': None,
                    'nornir_chests_total': 1,
                    'nornir_chests_remaining': None,
                    'upper_arena_unlocked': b'Msp_Mount400_UpperArena' in data,
                    'status': 'unknown',
                    'proven': False,
                    'note': 'Помировые счетчики воронов и сундуков Норн в теле сохранения не хранятся отдельными числами (хранятся глобально в HERO Wallet)',
                },
                'niflheim': {
                    'name': 'Нифльхейм',
                    'ravens_total': 0,
                    'ravens_collected': 0,
                    'ravens_remaining': 0,
                    'nornir_chests_total': 0,
                    'nornir_chests_remaining': 0,
                    'raven_tree_visited': b'Nif_RavenTree100_Main' in data,
                    'status': 'confirmed',
                    'proven': True,
                    'note': 'В Нифльхейме нет воронов и сундуков Норн (Древо воронов — прием наград)',
                },
                'jotunheim': {
                    'name': 'Йотунхейм',
                    'ravens_total': 0,
                    'ravens_collected': 0,
                    'ravens_remaining': 0,
                    'nornir_chests_total': 0,
                    'nornir_chests_remaining': 0,
                    'status': 'confirmed',
                    'proven': True,
                    'note': 'В сюжетном Йотунхейме нет воронов Одина и сундуков Норн',
                },
            },
            'proven_realm_flags': get_proven_realm_flags_summary(data),
        }

        if story and 'realms_exploration' in story:
            parsed['realms_exploration'] = story['realms_exploration']

        parsed['progression_tables'] = parse_progression_tables(data)
        _apply_raven_journal_counters(parsed)

    return parsed


# Счётчики просьбы «Глаза Одина» из журнала самой игры (Table 1, целые): шаг «Убивать воронов Одина»
# и шаг «Открыть дары воронов» (хеши счётчиков — из quests_main.dcb, см. gow_favors.load_catalog()).
_RAVENS_KILLED_COUNTER = '0x105a6147d2e88ae8'   # из 48
_RAVEN_GIFTS_COUNTER = '0x5828350b43a63bc4'     # из 6


def _apply_raven_journal_counters(parsed: dict) -> None:
    """Вороны и дары Древа — по счётчику журнала, а не по формуле из кошелька.

    14.11.2026: формула «предмет 0x482780EF… + 3 × дары» совпадала с экраном просьбы только в двух точках
    калибровки (21.09, 02.10). По 22 слотам сейва она расходится со счётчиком журнала в обе стороны
    (GOWRSAVE17: 27 против 21, GOWRSAVE4: 29 против 31) и стоит на месте, пока счётчик растёт
    (GOWRSAVE19→21: 28/28/28 против 25/28/28). Счётчик — то самое число, что игра пишет в просьбе
    «Глаза Одина»; формула остаётся запасной для сейвов, где счётчика ещё нет (до начала просьбы).
    """
    counters = (parsed.get('progression_tables') or {}).get('table1_int') or {}
    colls = parsed.get('collectibles') or {}
    wallet = parsed.get('wallet')
    killed = counters.get(_RAVENS_KILLED_COUNTER)
    if isinstance(killed, int) and 0 <= killed <= 48 and isinstance(colls.get('ravens'), dict):
        colls['ravens'].update(collected=killed, remaining=48 - killed, source='journal_counter')
        if isinstance(wallet, dict):
            wallet['odin_ravens_wallet_formula'] = wallet.get('odin_ravens')
            wallet['odin_ravens'] = killed
    gifts = counters.get(_RAVEN_GIFTS_COUNTER)
    if isinstance(gifts, int) and 0 <= gifts <= 6 and isinstance(colls.get('raven_tree'), dict):
        colls['raven_tree'].update(chests_opened=gifts, chests_remaining=6 - gifts, source='journal_counter')


_U4_MAGIC = b'U4SLBKRB'
_FT_CLAIMED_SIG = b'\x0b' + struct.pack('<Q', 0xF413C5F24D2A8807)
_T1_BOOL_TRUE_VAL = 0x0000A8CE0F4DDD8B
_PIN_MAPPING_TARGETS_CACHE: dict | None = None


def _get_pin_mapping_targets() -> dict:
    """Единоразовая загрузка целевых WAD и хешей экипировки из data/gow_pins/pin_mapping.json."""
    global _PIN_MAPPING_TARGETS_CACHE
    if _PIN_MAPPING_TARGETS_CACHE is not None:
        return _PIN_MAPPING_TARGETS_CACHE

    mapping_path = DATA / 'pin_mapping.json'
    equip_seen: dict[int, str] = {}
    ft_seen: dict[str, tuple[str, int, str]] = {}
    wad_ent_seen: dict[str, tuple[str, int, str | None, str]] = {}
    needed_wads: set[str] = set()

    if mapping_path.is_file():
        try:
            raw_map = json.loads(mapping_path.read_text(encoding='utf-8'))
            for m in raw_map.values():
                if not isinstance(m, dict):
                    continue
                for eh in m.get('equip_any') or ():
                    eh_norm = str(eh).lower()
                    eh_int = int(eh_norm, 16)
                    equip_seen[eh_int] = eh_norm
                if 'ft_wad' in m and 'ft_item_hash' in m:
                    wname = str(m['ft_wad'])
                    ih_norm = str(m['ft_item_hash']).lower()
                    key = f'{wname}:{ih_norm}'
                    ft_seen[key] = (wname, int(ih_norm, 16), key)
                    needed_wads.add(wname)
                if 'wad_name' in m and 'wad_ent_hash' in m:
                    wname = str(m['wad_name'])
                    wh_norm = str(m['wad_ent_hash']).lower()
                    pref = m.get('wad_ent_prefix')
                    key = f'{wname}:{wh_norm}:{pref or ""}'
                    wad_ent_seen[key] = (wname, int(wh_norm, 16), pref, f'{wname}:{wh_norm}')
                    needed_wads.add(wname)
        except Exception:
            pass

    _PIN_MAPPING_TARGETS_CACHE = {
        'equip_hashes': list(equip_seen.items()),
        'ft_targets': list(ft_seen.values()),
        'wad_ent_targets': list(wad_ent_seen.values()),
        'needed_wads': needed_wads,
    }
    return _PIN_MAPPING_TARGETS_CACHE


def _unpack_wad_payload_fast(p: bytes) -> dict | None:
    """Быстрое битовое выравнивание блока состояния WAD по маркеру U4SLBKRB."""
    if not p or len(p) < 12:
        return None
    big = int.from_bytes(p, 'big')
    plen = len(p)
    for rshift in range(8):
        aligned = (big >> rshift).to_bytes(plen, 'big')
        u4_pos = aligned.find(_U4_MAGIC)
        if u4_pos >= 8:
            sa, sb = struct.unpack_from('<II', aligned, u4_pos - 8)
            tlv_start = u4_pos - 8 - sb
            if tlv_start >= 0:
                return {
                    'u4_pos': u4_pos,
                    'sa': sa,
                    'sb': sb,
                    'tlv_start': tlv_start,
                    'tlv': aligned[tlv_start:u4_pos - 8],
                }
    return None


def _check_wad_ent_pre_tlv(p: bytes, u: dict | None, ent_h_int: int, prefix: str | None = None) -> bool:
    """Проверка битового состояния сущности строго в Pre-TLV области WAD (до U4SLBKRB)."""
    if not p or len(p) < 17 or not u:
        return False
    pre_len = (u['u4_pos'] - u['sb']) + 2
    if pre_len < 17:
        return False
    p_slice = p[:min(len(p), pre_len)]
    slen = len(p_slice)
    if slen < 17:
        return False
    big = int.from_bytes(p_slice, 'big')
    pat = struct.pack('<Q', ent_h_int)
    for rshift in range(8):
        b = (big >> rshift).to_bytes(slen, 'big')
        idx = b.find(pat)
        if idx >= 0 and idx + 17 <= slen:
            if not prefix:
                return True
            val66 = int.from_bytes(b[idx + 8:idx + 17], 'big') >> 6
            return f'{val66:066b}'.startswith(prefix)
    return False


def parse_progression_tables(data: bytes) -> dict:
    """Полный бинарный разбор 5 структур прогрессии GOWRSAVE без внешних .wad файлов игры.

    Извлекает:
      1. Table 1 (0x08840): булевы флаги мира (0xA8CE0F4DDD8B) и целочисленные счётчики (val >> 11)
      2. Table 2 (0x08844 + t1_cnt*24): этапы квестов, просьб, артефактов, лора и RegionSummary
      3. Table 3 (HERO Wallet): точные количества предметов инвентаря (hero_pos + 20)
      4. Equipment Pool: открытые комплекты брони Кратоса, Атрея и Фрейи
      5. Table 4 (WAD State DB): посещённые/непосещённые WAD, врата (TLV) и Pre-TLV сущности
    """
    n = len(data)
    table1_bool: list[str] = []
    table1_int: dict[str, int] = {}
    table2_stage: dict[str, int] = {}
    hero_items: dict[str, int] = {}
    equip_owned: list[str] = []
    visited_wads: list[str] = []
    unvisited_wads: list[str] = []
    ft_claimed: dict[str, bool] = {}
    wad_ent_states: dict[str, bool] = {}

    # 1 & 2. Table 1 и Table 2
    if n >= 0x08848:
        t1_cnt = struct.unpack_from('<I', data, 0x08840)[0]
        t1_end = 0x08844 + t1_cnt * 24
        if 0 < t1_cnt < 20000 and t1_end <= n:
            for h, val, _u1, _u2 in struct.iter_unpack('<QQII', data[0x08844:t1_end]):
                if val == _T1_BOOL_TRUE_VAL:
                    table1_bool.append(f'0x{h:016x}')
                elif val < (1 << 32):
                    table1_int[f'0x{h:016x}'] = val >> 11

            t2_off = t1_end
            if t2_off + 16 <= n:
                _bsize, ver, _cap, t2_cnt = struct.unpack_from('<IIII', data, t2_off)
                t2_end = t2_off + 16 + t2_cnt * 24
                if ver == 2 and 0 < t2_cnt < 20000 and t2_end <= n:
                    for h, _sts, _ets, stg, _unk in struct.iter_unpack('<QIIII', data[t2_off + 16:t2_end]):
                        table2_stage[f'0x{h:016x}'] = stg

    targets = _get_pin_mapping_targets()

    # 3 & 4. HERO Inventory (w_off + 20) и пул открытой экипировки
    hero_pos = data.find(struct.pack('<Q', HERO_WALLET_HASH))
    if hero_pos != -1 and hero_pos + 20 <= n:
        n_items = struct.unpack_from('<I', data, hero_pos + 8)[0]
        if 0 < n_items < 10000:
            items_start = hero_pos + 20
            items_end = min(n, items_start + n_items * 16)
            items_end -= (items_end - items_start) % 16
            for rh, rq, _slot in struct.iter_unpack('<QII', data[items_start:items_end]):
                hero_items[f'0x{rh:016x}'] = rq

        equip_slice = data[max(0, hero_pos - 0x3000):min(n, hero_pos + 0x2000)]
        for eh_int, eh_hex in targets['equip_hashes']:
            if struct.pack('<Q', eh_int) in equip_slice:
                equip_owned.append(eh_hex)

    # 5. WAD State Database (начинается с Mid_Chase100_Intro - 48)
    first_wad = data.find(b'Mid_Chase100_Intro\x00')
    wad_payloads: dict[str, bytes] = {}
    needed_wads = targets['needed_wads']
    if first_wad >= 48:
        pos = first_wad - 48
        while pos + 208 <= n:
            name_raw = data[pos + 48:pos + 100]
            nul = name_raw.find(b'\x00')
            if nul <= 0:
                break
            try:
                wname = name_raw[:nul].decode('ascii')
            except UnicodeDecodeError:
                break
            if not all(32 <= ord(c) < 127 for c in wname):
                break
            payload_size = struct.unpack_from('<I', data, pos + 4)[0]
            if pos + 208 + payload_size > n:
                break
            if payload_size > 0:
                visited_wads.append(wname)
                if wname in needed_wads:
                    wad_payloads[wname] = data[pos + 116:pos + 116 + payload_size]
            else:
                unvisited_wads.append(wname)
            pos += 208 + payload_size

        unpacked_cache: dict[str, dict | None] = {}
        for wname in wad_payloads:
            unpacked_cache[wname] = _unpack_wad_payload_fast(wad_payloads[wname])

        for wname, ih_int, ft_key in targets['ft_targets']:
            u = unpacked_cache.get(wname)
            if u:
                ft_claimed[ft_key] = (struct.pack('<Q', ih_int) + _FT_CLAIMED_SIG) in u['tlv']
            else:
                ft_claimed[ft_key] = False

        for wname, eh_int, pref, ent_key in targets['wad_ent_targets']:
            p = wad_payloads.get(wname, b'')
            u = unpacked_cache.get(wname)
            wad_ent_states[ent_key] = _check_wad_ent_pre_tlv(p, u, eh_int, pref)

    if not (table1_bool or table1_int or table2_stage or hero_items or visited_wads):
        return {}

    return {
        'table1_bool': table1_bool,
        'table1_int': table1_int,
        'table2_stage': table2_stage,
        'hero_items': hero_items,
        'equip_owned': equip_owned,
        'visited_wads': visited_wads,
        'unvisited_wads': unvisited_wads,
        'ft_claimed': ft_claimed,
        'wad_ent_states': wad_ent_states,
    }


def find_save_dirs(roots: list[Path | str] | None = None) -> list[Path]:
    """Поиск каталогов сохранений God of War Ragnarök."""
    out: list[Path] = []
    search_roots = [Path(r) for r in (roots if roots is not None else DEFAULT_SAVE_ROOTS)]
    for root in search_roots:
        if not root.exists():
            continue
        if root.is_dir() and any(root.glob('GOWRSAVE*')):
            if root not in out:
                out.append(root)
            continue
        for candidate in [root / 'God of War Ragnarök', root / 'God of War Ragnarok']:
            if candidate.is_dir():
                for sub in candidate.iterdir():
                    if sub.is_dir() and any(sub.glob('GOWRSAVE*')) and sub not in out:
                        out.append(sub)
    return out


def read_all_slots(save_dir: Path | str | None = None, detailed: bool = False) -> list[dict]:
    """Чтение всех слотов с сортировкой от самого свежего к старым."""
    dirs = [Path(save_dir)] if save_dir else find_save_dirs()
    slots: list[dict] = []
    for d in dirs:
        try:
            entries = list(d.glob('GOWRSAVE*'))
        except OSError:
            continue
        for p in entries:
            parsed = parse_save_file(p, detailed=detailed)
            if parsed:
                slots.append(parsed)

    slots.sort(key=lambda s: (s.get('save_counter') or 0, s.get('save_timestamp') or 0), reverse=True)
    return slots


def read(save_dir: Path | str | None = None) -> dict:
    """Единый фасад прогресса для the companion (контракт gamesave.py)."""
    answer: dict = {
        'ok': False,
        'appid': 2322010,
        'game': 'God of War Ragnarök',
        'format': 'not_found',
        'place': None,
        'realm': None,
        'area': None,
        'objective': None,
        'play_seconds': None,
        'play_time': None,
        'gear_level': None,
        'skills_count': None,
        'difficulty': None,
        'collected': None,
        'hacksilver': None,
        'xp': None,
        'slots': [],
        'source': None,
        'reason': 'сохранения God of War Ragnarök не найдены',
    }

    # Читаем слоты (быстро без detailed)
    slots = read_all_slots(save_dir, detailed=False)
    if not slots:
        return answer

    # Для самого свежего слота делаем полный разбор кошелька и сюжета
    best = parse_save_file(slots[0]['path'], detailed=True) or slots[0]

    answer.update({
        'ok': True,
        'format': 'gowr',
        'place': best.get('place'),
        'realm': best.get('realm'),
        'area': best.get('area'),
        'objective': best.get('objective'),
        'difficulty': best.get('difficulty'),
        'difficulty_id': best.get('difficulty_id'),
        'play_seconds': best.get('play_seconds'),
        'play_time': best.get('play_time'),
        'power_level': best.get('power_level'),
        'gear_level': best.get('max_gear_level'),
        'gear_levels': best.get('gear_levels', []),
        'loadout': best.get('loadout'),
        'amulet': best.get('amulet'),
        'collectibles': best.get('collectibles'),
        'odin_ravens': best.get('wallet', {}).get('odin_ravens', (best.get('collectibles') or {}).get('ravens', {}).get('collected', 0)),
        'ravens': (best.get('collectibles') or {}).get('ravens'),
        'skills_count': best.get('wallet', {}).get('skills_count'),
        'hacksilver': best.get('hacksilver', best.get('hacksilver_total')),
        'xp': best.get('wallet', {}).get('kratos_xp', best.get('xp_total')),
        'wallet': best.get('wallet'),
        'story': best.get('story'),
        'realms_exploration': best.get('realms_exploration'),
        'stats_counter': best.get('stats_counter'),
        'objective_string_id': best.get('objective_string_id', best.get('stats_counter')),
        'stats_counter_status': best.get('stats_counter_status'),
        'stats_counter_basis': best.get('stats_counter_basis'),
        'proven_realm_flags': best.get('collectibles', {}).get('proven_realm_flags'),
        'user_preferences': best.get('user_preferences'),
        'world_flags_active': best.get('collectibles', {}).get('world_flags_active'),
        'tracked_entities': best.get('tracked_entities'),
        'realm_id': best.get('realm_id'),
        'zone_id': best.get('zone_id'),
        'realm_by_id': best.get('realm_by_id'),
        'active_hero': best.get('active_hero', best.get('story', {}).get('active_hero', 'Кратос')),
        'base_visits': best.get('story', {}).get('base_visits'),
        'actors_catalog': best.get('story', {}).get('actors_catalog'),
        'quest_stages': best.get('quest_stages', best.get('story', {}).get('quest_stages')),
        'story_progress': best.get('story_progress'),
        'story_percent': best.get('story_percent'),
        'chapter': best.get('chapter'),
        'chapter_index': best.get('chapter_index'),
        'chapters_total': best.get('chapters_total'),
        'chapter_title': best.get('chapter_title'),
        'objective_desc': best.get('objective_desc'),
        'remaining_chapters': best.get('remaining_chapters'),
        'next_chapter': best.get('next_chapter'),
        'progression_tables': best.get('progression_tables'),
        'update_policy': 'обновляется при каждом автосохранении',
        'source': {
            'path': best['path'],
            'mtime': best.get('mtime'),
            'slot': best.get('slot'),
            'save_counter': best.get('save_counter'),
            'save_time_utc': best.get('save_time_utc'),
        },
        'reason': 'ok',
        'slots': slots,
    })
    return answer


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding='utf-8', errors='replace')
        except (AttributeError, OSError):
            pass

    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dir', help='Каталог с сохранениями GOWRSAVE')
    parser.add_argument('--slot', help='Путь к конкретному файлу GOWRSAVE')
    parser.add_argument('--all', action='store_true', help='Вывести все слоты')
    parser.add_argument('--details', action='store_true', help='Полные данные кошелька и сюжета')
    args = parser.parse_args()

    if args.slot:
        res = parse_save_file(args.slot, detailed=True)
        print(json.dumps(res, ensure_ascii=False, indent=2, default=str))
        return 0 if res else 1

    if args.all:
        slots = read_all_slots(args.dir, detailed=args.details)
        print(f'Найдено валидных слотов GOWR: {len(slots)}')
        for s in slots:
            print(f"  {s['slot']:12} #{s['save_counter']:4} | {s['save_time_utc'][:16]} | "
                  f"{s['play_time']:14} | HS={s.get('hacksilver_total', 0):7} | {s['place']}")
        return 0 if slots else 1

    got = read(args.dir)
    print(json.dumps(got, ensure_ascii=False, indent=2, default=str))
    return 0 if got['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
