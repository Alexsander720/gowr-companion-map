import copy
import json
import math
import pytest
import gow_memory as g
from paths import DATA


def test_all_code_owned_models_survive_text_removal():
    doc = json.loads((DATA / 'realm_affine_transforms.json').read_text(encoding='utf-8'))
    assert set(g.load_realm_affine_transforms()) == set(doc['realms'])
    assert len(g.load_realm_affine_transforms()) == 10


def test_measured_live_references_and_zone():
    doc = json.loads((DATA / 'live_realm_refs.json').read_text(encoding='utf-8'))['realms']['muspelheim']
    for ref in doc['refs']:
        p = g.normalize_coordinates('muspelheim', *ref['world'])
        assert p['projection_status'] == 'live_similarity'
        assert math.hypot(p['map_lat']-ref['lat'], p['map_lng']-ref['lng']) < 1e-5
        assert p['projection_confidence'] == 'approximate'
        strict = g.normalize_coordinates('muspelheim', *ref['world'], strict=True)
        assert strict['projection_status'] == 'fallback_bbox'
    zone = doc['zones'][0]
    p = g.normalize_coordinates('muspelheim', *zone['anchor_world'])
    assert p['projection_zone'] == 'live:crucible'
    assert p['map_scale_per_metre'] > 0


@pytest.mark.parametrize('realm,xyz', [('midgard',(1e6,0,1e6)), ('svartalfheim',(1e8,0,-1e8)),
                                    ('muspelheim',(50000,0,50000)), ('vanaheim',(-9e5,-500,9e5))])
def test_outside_calibration_is_hidden(realm, xyz):
    p = g.normalize_coordinates(realm, *xyz)
    assert p['projection_confidence'] == 'none'


def test_axis_selection_uses_y_not_z(monkeypatch):
    record = copy.deepcopy(g.load_realm_affine_transforms()['svartalfheim'])
    record['axes'] = [0,1]
    record['matrix'] = [[.0001,.0002,.7],[.0002,-.0001,-.7]]
    record['domain'] = dict(kind='interpolation_hull_with_negative_controls', excluded=[],
                            hull=[[-100,-100],[100,-100],[100,100],[-100,100]], boundary_tolerance=0.)
    monkeypatch.setattr(g, 'REALM_AFFINE_TRANSFORMS', {'svartalfheim':record})
    p = g.normalize_coordinates('svartalfheim',10,20,-1e6,strict=True)
    assert p['map_lat'] == pytest.approx(.705)
    assert p['map_lng'] == pytest.approx(-.7)


def test_strict_domain_and_negative_controls():
    r = g.load_realm_affine_transforms()['midgard']
    ref = next(p for p in r['references'] if p['pin_id'] == '219051')
    p = g.normalize_coordinates('midgard',*ref['world'],strict=True)
    assert p['projection_reason'] == 'near_contradictory_reference'
    assert p['projection_confidence'] == 'none'


@pytest.mark.parametrize('mutation', ['missing','expanded','threshold','two_point','bad_matrix'])
def test_weak_geometric_proof_is_rejected(tmp_path, mutation):
    r = copy.deepcopy(g.load_realm_affine_transforms()['midgard'])
    if mutation == 'missing': r.pop('domain')
    elif mutation == 'expanded': r['domain']['hull']=[[-1e8,-1e8],[1e8,-1e8],[1e8,1e8],[-1e8,1e8]]
    elif mutation == 'threshold': r['threshold']=.1
    elif mutation == 'two_point': r['inliers']=r['inliers'][:2]
    else: r['matrix'][0][2]+=.05
    p=tmp_path/'model.json';p.write_text(json.dumps({'schema_version':1,'realms':{'midgard':r}}))
    assert g.load_realm_affine_transforms(p) == {}


def test_synthetic_live_ransac_rejects_outlier(tmp_path):
    refs=[dict(world=[x,10,z],lat=.65+x*.0002-z*.0001+shift,lng=-.7+x*.0001+z*.0002)
          for x,z,shift in [(0,0,0),(100,0,0),(0,100,0),(100,100,0),(50,50,.08)]]
    p=tmp_path/'refs.json';p.write_text(json.dumps({'schema_version':1,'realms':{'muspelheim':{'refs':refs}}}))
    model=g.load_live_realm_transforms(p)['muspelheim'][0]
    assert model['fit_report']['outliers'] == [4]
    assert model['matrix'][0] == pytest.approx([.0002,-.0001,.65])


def test_unknown_build_never_reads_offsets(monkeypatch, tmp_path):
    exe = tmp_path/'new.exe'; exe.write_bytes(b'changed')
    calls=[]
    class Reader:
        def close(self): calls.append('closed')
        def read_raw(self,*args): raise AssertionError('Offsets read for unknown build')
    monkeypatch.setattr(g,'find_gowr_process',lambda:(12,exe))
    monkeypatch.setattr(g.SafeProcessMemory,'open',lambda pid:Reader())
    monkeypatch.setattr(g,'get_exe_fingerprint',lambda path:g.BuildFingerprint(123,456,'changed'))
    result=g.read_live_telemetry()
    assert result['available'] is False
    assert result['reason'] == 'unsupported_build'
    assert result['radar'] is None
    assert calls == ['closed']


def test_no_fingerprint_has_no_default_profile(monkeypatch):
    class Reader:
        def close(self): pass
        def read_raw(self,*args): raise AssertionError('Unverified build must not read offsets')
    monkeypatch.setattr(g,'find_gowr_process',lambda:(12,None))
    monkeypatch.setattr(g.SafeProcessMemory,'open',lambda pid:Reader())
    result=g.read_live_telemetry()
    assert result['reason'] == 'build_unverified'
    assert result['available'] is False


def test_access_mask_has_read_and_query_only():
    assert g.SAFE_ACCESS_MASK == 0x0410
    from tools.gow_live_pointer_probe import open_readonly
    calls=[]
    class API:
        def OpenProcess(self,*args): calls.append(args);return 101
    assert open_readonly(API(),23) == 101
    assert calls == [(0x0410,False,23)]
