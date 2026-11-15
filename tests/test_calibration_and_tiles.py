import copy
import io
import json
import numpy as np
from PIL import Image
import pytest
import gow_tiles
import gow_game_tiles
from tools import gow_auto_calibrate as auto
from paths import DATA


def test_calibration_is_off_and_writes_only_user_refs(monkeypatch,tmp_path):
    monkeypatch.delenv('GOWR_AUTOCALIB',raising=False)
    assert auto.start_background() is None
    baseline=(DATA/'live_realm_refs.json').read_bytes()
    target=tmp_path/'user/refs.json'
    point={'world':[800,10,400],'lat':.65,'lng':-.7,'source':'auto_map_sift'}
    assert auto.append_reference(target,'muspelheim',point)
    assert not auto.append_reference(target,'muspelheim',point)
    doc=json.loads(target.read_text(encoding='utf-8'))
    assert len(doc['realms']['muspelheim']['refs']) == 3
    assert (DATA/'live_realm_refs.json').read_bytes() == baseline


def test_calibration_rejects_movement_and_process_changes():
    before={'available':True,'pid':11,'radar':{'realm_key':'midgard'},'position':{'x':10,'y':0,'z':20}}
    assert auto.stable_samples(before,copy.deepcopy(before))
    after=copy.deepcopy(before);after['position']['x']+=1
    assert not auto.stable_samples(before,after)
    after=copy.deepcopy(before);after['pid']=12
    assert not auto.stable_samples(before,after)


def test_tile_keyout_cache_and_request_validation(tmp_path):
    rgb=np.zeros((8,8,3),np.uint8);rgb[:]=gow_tiles.TILE_BG['midgard'];rgb[2:6,2:6]=[255,220,100]
    buf=io.BytesIO();Image.fromarray(rgb).save(buf,'PNG')
    calls=[]
    def fetch(*args):calls.append(args);return buf.getvalue()
    png=gow_tiles.get_tile('midgard',11,1020,1019,cache_dir=tmp_path,fetch=fetch)
    assert gow_tiles.get_tile('midgard',11,1020,1019,cache_dir=tmp_path,fetch=fetch) == png
    assert len(calls)==1
    alpha=np.asarray(Image.open(io.BytesIO(png)))[:,:,3]
    assert alpha[0,0] == 0 and alpha[4,4] == 255
    assert gow_tiles.parse_path('/gow-tiles/midgard/11/1020/1019.png') == ('midgard',11,1020,1019)
    assert gow_tiles.parse_path('/gow-tiles/../11/1020/1019.png') is None
    assert gow_tiles.parse_path('/gow-tiles/midgard/30/1/1.png') is None


def test_native_relief_unavailable_without_local_assets(monkeypatch,tmp_path):
    monkeypatch.setattr(gow_game_tiles,'MAPS_DIR',tmp_path)
    assert gow_game_tiles.realms_available() == []


def test_calibration_requires_private_templates(monkeypatch,tmp_path):
    monkeypatch.setenv('GOWR_AUTOCALIB','1')
    monkeypatch.setattr(auto,'FIX',tmp_path/'templates')
    with pytest.raises(RuntimeError,match='learn-templates'):
        auto.start_background()


def test_template_setup_uses_synthetic_capture_only(monkeypatch,tmp_path):
    pytest.importorskip('cv2')
    monkeypatch.setattr(auto,'FIX',tmp_path/'templates')
    frame=np.zeros((837,1488,3),np.uint8)
    rois=iter([(400,780,80,30),(500,400,29,29)])
    result=auto.learn_templates(capture=lambda pid:frame,process_finder=lambda:(12,None),
                                selector=lambda title,pixels:next(rois),wait=lambda seconds:None)
    assert result == tmp_path/'templates'
    assert auto.templates_ready()
    assert Image.open(result/'map_tab_template.png').size == (80,30)
    assert Image.open(result/'kratos_template.png').size == (29,29)


def test_collector_understands_russian_save_realm(monkeypatch):
    import gowsave
    import gow_memory
    monkeypatch.setattr(gowsave,'read',lambda:{'ok':True,'realm':'Муспельхейм - synthetic'})
    monkeypatch.setattr(gow_memory,'read_live_telemetry',lambda **kw:kw)
    assert auto.current_telemetry() == {'active_realm':'muspelheim'}
