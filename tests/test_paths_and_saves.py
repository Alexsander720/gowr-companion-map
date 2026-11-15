from pathlib import Path
import json
import paths
import gowsave
from saves import SaveReader


def test_steam_library_discovery_uses_manifest(monkeypatch,tmp_path):
    steam=tmp_path/'steam';lib=tmp_path/'second-library';(steam/'steamapps').mkdir(parents=True)
    app=lib/'steamapps/common/Synthetic Game';app.mkdir(parents=True);(app/'GoWR.exe').write_bytes(b'synthetic')
    (steam/'steamapps/libraryfolders.vdf').write_text('"libraryfolders" { "1" { "path" "'+lib.as_posix()+'" } }')
    (lib/'steamapps/appmanifest_2322010.acf').write_text('"AppState" { "installdir" "Synthetic Game" }')
    monkeypatch.setattr(paths,'GAME_DIR',None);monkeypatch.setattr(paths,'steam_roots',lambda:[steam])
    assert paths.find_game_dir() == app


def test_save_discovery_does_not_assume_account_id(tmp_path):
    root=tmp_path/'Saved Games';game=root/'God of War Ragnarok'
    for account in ['user-one','user-two']:
        folder=game/account;folder.mkdir(parents=True);(folder/'GOWRSAVE0').write_bytes(b'synthetic')
    assert set(gowsave.find_save_dirs([root])) == {game/'user-one',game/'user-two'}


def test_save_reader_caches_by_file_metadata(monkeypatch,tmp_path):
    save=tmp_path/'GOWRSAVE0';save.write_bytes(b'synthetic')
    calls=[]
    monkeypatch.setattr(gowsave,'read',lambda d:calls.append(d) or {'ok':True})
    reader=SaveReader(tmp_path)
    assert reader.read()['ok'];assert reader.read()['ok'];assert len(calls)==1
    save.write_bytes(b'synthetic updated')
    assert reader.read()['ok'];assert len(calls)==2


def test_localization_uses_shared_ids_only(monkeypatch,tmp_path):
    from tools import build_gow_ru_names as tool
    from gowassets import read_language_strings
    import lz4.frame
    game=tmp_path/'game';wad=game/'exec/wad/pc_le';wad.mkdir(parents=True)
    (wad/'r_lang_en.wad').write_bytes(lz4.frame.compress(b'*11*\nSynthetic bird\n'))
    (wad/'r_lang_ru.wad').write_bytes(lz4.frame.compress('*11*\nСинтетическая птица\n'.encode()))
    assert read_language_strings(wad/'r_lang_ru.wad')[11] == 'Синтетическая птица'
    monkeypatch.setattr(paths,'GAME_DIR',game);monkeypatch.setattr(tool,'DATA',tmp_path/'pins')
    tool.DATA.mkdir(exist_ok=True);(tool.DATA/'midgard.json').write_text(json.dumps({'locations':[{'id':1,'title':'Synthetic bird'}]}))
    assert tool.build_names()['1']['ru'] == 'Синтетическая птица'


def test_story_cache_follows_game_directory(monkeypatch,tmp_path):
    import lz4.frame
    from gow_story import load_story_strings
    for directory,text in [('one','First synthetic'),('two','Second synthetic')]:
        game=tmp_path/directory;wad=game/'exec/wad/pc_le';wad.mkdir(parents=True)
        (wad/'r_lang_en.wad').write_bytes(lz4.frame.compress(('*11*\n'+text+'\n').encode()))
        monkeypatch.setattr(paths,'GAME_DIR',game)
        assert load_story_strings('en')[11] == text
