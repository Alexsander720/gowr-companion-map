import struct
import pytest
import gow_favors as favors
import gowsave


def save_bytes(stages, counters=()):
    t1=[(0x123,0)]+list(counters)
    buf=bytearray(0x8844+len(t1)*24+16+len(stages)*24)
    struct.pack_into('<I',buf,0x8840,len(t1))
    for i,(h,v) in enumerate(t1):struct.pack_into('<QQII',buf,0x8844+i*24,h,v<<11,0,0)
    off=0x8844+len(t1)*24
    struct.pack_into('<IIII',buf,off,0,2,len(stages),len(stages))
    for i,(h,stage) in enumerate(stages):struct.pack_into('<QIIII',buf,off+16+i*24,h,0,0,stage,0)
    return bytes(buf)


def catalog():
    return {'favors':[{'id':'Synthetic_Quest','name':'Synthetic favor','hash':'0x0000000000000011',
                       'realm':'midgard','region':'Synthetic region','steps':[
                           {'hash':'0x0000000000000022','name':'Synthetic objective',
                            'counter':{'hash':'0x0000000000000033','total':6},'steps':[]}],
                       'pin_ids':['1','2'],'pin_realms':{'1':'midgard','2':'alfheim'},
                       'pin_rules':{'1':{'t2_hash':'0x0000000000000044'}}}]}


@pytest.mark.parametrize('stage,state',[(0,'not_started'),(2,'active'),(4,'completed'),(5,'unknown')])
def test_synthetic_journal_bytes_and_counter(monkeypatch,stage,state):
    monkeypatch.setattr(favors,'load_catalog',lambda lang='en':catalog())
    pt=gowsave.parse_progression_tables(save_bytes([(0x11,stage),(0x22,2),(0x44,0)],[(0x33,4)]))
    q=favors.read_favors({'progression_tables':pt})[0]
    assert q['state'] == state
    if state == 'active':
        assert q['counter'] == {'done':4,'total':6}
        assert q['step'] == 'Synthetic objective'
    assert q['pin_states']['1'] == 'not_collected'
    assert q['pin_states']['2'] == 'unknown'


def test_absent_save_and_missing_counter_remain_unknown(monkeypatch):
    monkeypatch.setattr(favors,'load_catalog',lambda lang='en':catalog())
    assert favors.read_favors(None)[0]['state'] == 'unknown'
    pt=gowsave.parse_progression_tables(save_bytes([(0x11,2),(0x22,2)]))
    q=favors.read_favors({'progression_tables':pt})[0]
    assert q['objectives'][0]['counter'] is None
    assert q['objectives'][0]['counter_unknown'] is True


def test_synthetic_quest_database_and_bounds():
    buf=bytearray(1600)
    def rel(off,target):struct.pack_into('<q',buf,off,target-off)
    rel(0,64);struct.pack_into('<I',buf,8,1);rel(64,128)
    for off,name,sid in [(128,b'Favor_Test',11),(320,b'Favor_Test_Step',12)]:
        rel(off+80,1000+off);buf[1000+off:1000+off+len(name)+1]=name+b'\0'
        struct.pack_into('<I',buf,off+12,sid)
    rel(160,80);struct.pack_into('<I',buf,168,1);rel(80,320)
    struct.pack_into('<I',buf,348,22);rel(384,600);struct.pack_into('<I',buf,392,1);rel(600,640)
    struct.pack_into('<QQf',buf,640,0x10500,0x456,6.)
    records=favors.parse_quest_database(bytes(buf),0,len(buf),{11:'Synthetic favor',12:'Goal',22:'%d of %d'}, {})
    assert records[0]['hash'] == f'0x{gowsave.sms_std_name_hash("Favor_Test"):016x}'
    assert records[0]['steps'][0]['counter']['total'] == 6
    english=favors.parse_quest_database(bytes(buf),0,len(buf),{}, {11:'Synthetic favor',12:'Goal',22:'%d of %d'})
    assert english[0]['steps'][0]['counter']['total'] == 6
    with pytest.raises(ValueError):favors.parse_quest_database(bytes(buf[:500]),0,500,{}, {})


def test_no_wads_preserves_active_counter(monkeypatch):
    base=catalog();q=base['favors'][0];q['name_sid']=11;q['steps'][0]['name_sid']=12
    monkeypatch.setattr(favors,'_base_catalog',lambda:base)
    pt=gowsave.parse_progression_tables(save_bytes([(0x11,2),(0x22,2)],[(0x33,4)]))
    result=favors.read_favors({'progression_tables':pt})[0]
    assert result['counter'] == {'done':4,'total':6}
    assert result['objectives'][0]['name'] == 'Current objective is unknown'
