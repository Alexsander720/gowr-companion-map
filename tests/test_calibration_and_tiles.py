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


def test_h16_heightmap_pipeline_single_and_vanaheim(tmp_path):
    from tools.gow_game_map import build_realm_h16, realm_height_meta

    for name, val in (('midgard', 0.25), ('vanaheim_crater', 0.7), ('vanaheim_jungle', 0.3)):
        arr = np.linspace(0.0, 1.0, 64 * 64, dtype=np.float32).reshape(64, 64) * 0.8 + val * 0.1
        np.save(tmp_path / f'{name}_h.npy', arr)

    georef = {
        'midgard': {'realm': 'midgard', 'accepted': True, 'texture_px': 64,
                    'merc0_to_texture': [[100.0, 0.0, -12700.0], [0.0, 100.0, -12700.0]]},
        'vanaheim_crater': {'realm': 'vanaheim', 'accepted': True, 'texture_px': 64,
                            'merc0_to_texture': [[100.0, 0.0, -12700.0], [0.0, 100.0, -12700.0]]},
        'vanaheim_jungle': {'realm': 'vanaheim', 'accepted': True, 'texture_px': 64,
                            'merc0_to_texture': [[100.0, 0.0, -12700.0], [0.0, 100.0, -12700.0]]},
    }
    mid_png = build_realm_h16('midgard', out_dir=tmp_path, maps_dir=tmp_path, georef=georef, size=64)
    van_png = build_realm_h16('vanaheim', out_dir=tmp_path, maps_dir=tmp_path, georef=georef, size=64)
    assert mid_png is not None and mid_png.is_file()
    assert van_png is not None and van_png.is_file()
    arr = np.asarray(Image.open(mid_png))
    assert arr.shape == (64, 64, 3) and arr.dtype == np.uint8
    assert realm_height_meta('midgard', maps_dir=tmp_path)['has_heightmap'] is True
    assert realm_height_meta('sindris-house', maps_dir=tmp_path)['has_heightmap'] is False


def test_native_3d_gowm_pack_atlas_and_endpoints(monkeypatch, tmp_path):
    from tools.gow_native_map_3d import (
        bake_prop_shadows_on_surface,
        compute_raymarched_terrain_shadow,
        decode_r10g10b10a2_unorm_normals,
        pack_gowm_binary,
        pack_pbr_atlases,
        pack_texture_atlas,
        unpack_gowm_binary,
    )

    # 1. R10G10B10A2_UNORM normal decoding -> unit length
    up_packed = np.array([(512) | (1023 << 10) | (512 << 20)], dtype='<u4')
    nrm = decode_r10g10b10a2_unorm_normals(up_packed)
    assert nrm.shape == (1, 3)
    assert abs(float(nrm[0, 1]) - 1.0) < 0.01

    # 2. GOWM v1 binary roundtrip
    verts = np.array([
        [10.0, 20.0, 30.0, 0.0, 1.0, 0.0, 0.1, 0.2],
        [40.0, 20.0, 30.0, 0.0, 1.0, 0.0, 0.9, 0.2],
        [25.0, 50.0, 60.0, 0.0, 1.0, 0.0, 0.5, 0.8],
    ], dtype='<f4')
    idxs = np.array([0, 1, 2], dtype='<u4')
    blob = pack_gowm_binary(verts, idxs)
    assert blob[:4] == b'GOWM'
    verts2, idxs2 = unpack_gowm_binary(blob)
    assert np.allclose(verts, verts2)
    assert np.array_equal(idxs, idxs2)

    # 3. Texture atlas packing (diffuse + synchronized PBR normal/gloss atlas)
    t1 = np.full((32, 32, 3), (200, 40, 30), dtype=np.uint8)
    t2 = np.full((32, 32, 4), (30, 140, 220, 255), dtype=np.uint8)
    t2[:8, :8, 3] = 0
    n1 = np.full((32, 32, 3), (128, 128, 255), dtype=np.uint8)
    g1 = np.full((32, 32), 200, dtype=np.uint8)
    atlas, uv_map = pack_texture_atlas({'tex_a': t1, 'tex_b': t2[..., :3]}, weights={'tex_a': 500, 'tex_b': 100})
    assert atlas.mode == 'RGB' and atlas.width >= 512
    assert set(uv_map.keys()) == {'tex_a', 'tex_b'}
    atlas_d, atlas_n, uv_pbr = pack_pbr_atlases(
        {'tex_a': t1, 'tex_b': t2},
        normal_maps={'tex_a': n1},
        gloss_maps={'tex_a': g1},
        weights={'tex_a': 500, 'tex_b': 100},
    )
    assert atlas_d.mode == 'RGBA' and atlas_n.mode == 'RGBA'
    assert atlas_d.size == atlas_n.size
    assert int(np.asarray(atlas_d)[..., 3].min()) == 0
    assert uv_pbr == uv_map
    for u0, v0, us, vs in uv_pbr.values():
        assert 0.0 <= u0 < 1.0 and 0.0 <= v0 < 1.0 and us > 0.0 and vs > 0.0

    # 4. Baked directional sun shadows darken snow surface southeast of elevated 3D geometry
    surf = np.full((128, 128, 3), 230.0, dtype=np.float32)
    sh_verts = np.array([
        [40.0, 35.0, 40.0, 0.0, 1.0, 0.0, 0.0, 0.0],
        [70.0, 35.0, 40.0, 0.0, 1.0, 0.0, 1.0, 0.0],
        [55.0, 35.0, 70.0, 0.0, 1.0, 0.0, 0.5, 1.0],
    ], dtype='<f4')
    sh_out = bake_prop_shadows_on_surface(
        surf, sh_verts, np.array([0, 1, 2], dtype='<u4'), 128.0, 128.0,
        lambda wx, wz: np.zeros_like(wx, dtype=np.float32),
    )
    assert sh_out.shape == surf.shape
    assert float(sh_out.mean()) < float(surf.mean())

    # 4b. Raymarched directional terrain cliff self-shadowing casts shadow southeast of a ridge
    en_ridge = np.zeros((128, 128), dtype=np.float32)
    en_ridge[24:56, 24:56] = 1.0
    M_ident = np.array([[2.0, 0.0], [0.0, 2.0]], dtype=np.float64)
    sh_ray = compute_raymarched_terrain_shadow(en_ridge, M_ident, height_amp=200.0, steps=16)
    assert sh_ray.shape == (128, 128) and sh_ray.dtype == np.float32
    assert float(sh_ray[60, 60]) < float(sh_ray[10, 10])  # southeast lee shadowed vs northwest lit

    # 5. Cached native 3D getters (strictly offline, no game dir required)
    assert gow_game_tiles.get_realm_native_3d_meta('midgard', native_dir=tmp_path, allow_extract=False)['has_native_3d'] is False
    rdir = tmp_path / 'midgard'
    rdir.mkdir(parents=True)
    (rdir / 'props.bin').write_bytes(blob)
    atlas_d.save(rdir / 'atlas.png', 'PNG')
    atlas_n.save(rdir / 'atlas_n.png', 'PNG')
    Image.new('RGB', (64, 64), (100, 140, 180)).save(rdir / 'surface.png', 'PNG')
    Image.new('RGBA', (64, 64), (128, 255, 128, 240)).save(rdir / 'terrain_n.png', 'PNG')
    Image.new('RGB', (64, 64), (180, 0, 120)).save(rdir / 'water_mask.png', 'PNG')
    (rdir / 'meta.json').write_text(json.dumps({
        'realm': 'midgard', 'has_native_3d': True, 'has_surface': True,
        'has_terrain_normal': True, 'has_water_mask': True,
        'has_props': True, 'has_normal_atlas': True, 'tri_count': 1,
    }), encoding='utf-8')
    meta = gow_game_tiles.get_realm_native_3d_meta('midgard', native_dir=tmp_path, allow_extract=False)
    assert meta['has_native_3d'] is True and meta['has_normal_atlas'] is True and meta['has_terrain_normal'] is True and meta['has_water_mask'] is True and meta['tri_count'] == 1
    assert isinstance(meta.get('rev'), int) and meta['rev'] > 0
    got_props = gow_game_tiles.get_realm_native_3d_file('midgard', 'props.bin', native_dir=tmp_path, allow_extract=False)
    assert got_props is not None and got_props[0] == blob and got_props[1] == 'application/octet-stream'
    got_norm = gow_game_tiles.get_realm_native_3d_file('midgard', 'atlas_n.png', native_dir=tmp_path, allow_extract=False)
    assert got_norm is not None and got_norm[0].startswith(b'\x89PNG') and got_norm[1] == 'image/png'
    got_tn = gow_game_tiles.get_realm_native_3d_file('midgard', 'terrain_n.png', native_dir=tmp_path, allow_extract=False)
    assert got_tn is not None and got_tn[0].startswith(b'\x89PNG') and got_tn[1] == 'image/png'
    got_wm = gow_game_tiles.get_realm_native_3d_file('midgard', 'water_mask.png', native_dir=tmp_path, allow_extract=False)
    assert got_wm is not None and got_wm[0].startswith(b'\x89PNG') and got_wm[1] == 'image/png'
    got_webp = gow_game_tiles.get_realm_native_3d_file('midgard', 'surface.png', native_dir=tmp_path, allow_extract=False, prefer_webp=True)
    assert got_webp is not None and got_webp[1] == 'image/webp' and got_webp[0][:4] == b'RIFF' and got_webp[0][8:12] == b'WEBP'
    assert (rdir / 'surface.webp').is_file()
    got_wm_webp = gow_game_tiles.get_realm_native_3d_file('midgard', 'water_mask.png', native_dir=tmp_path, allow_extract=False, prefer_webp=True)
    assert got_wm_webp is not None and got_wm_webp[1] == 'image/webp'
    assert gow_game_tiles.get_realm_native_3d_file('midgard', '../secret', native_dir=tmp_path, allow_extract=False) is None
