import json
import pytest
import gow_pins as pins


def test_synthetic_map_data_localization_links_and_status(monkeypatch, synthetic_map):
    (pins.PINS/'midgard.json').write_text(json.dumps(synthetic_map))
    (pins.PINS/'ru_names.json').write_text(json.dumps({'1':{'ru':'Синтетическая птица'}}),encoding='utf-8')
    monkeypatch.setattr(pins,'_load_pin_mapping',lambda:{'1':{'t2_hash':'0x123'}})
    en=pins.get_realm_pois('midgard',save_data={'progression_tables':{'table2_stage':{'0x123':4}}},lang='en')
    ru=pins.get_realm_pois('midgard',lang='ru')
    assert en[0]['name'] == 'Synthetic bird'
    assert en[0]['is_collected'] is True
    assert en[1]['is_collected'] is None
    assert en[0]['pct_x'] < en[1]['pct_x']
    assert en[0]['pct_y'] > en[1]['pct_y']
    assert ru[0]['name'] == 'Синтетическая птица'
    assert ru[1]['name'] == 'Synthetic cache'
    assert ru[0]['description_lang'] == 'en'
    assert '(pin:midgard:2)' in ru[0]['description']
    assert ru[0]['description'].startswith('See ')


@pytest.mark.parametrize('field,value,expected',[
    ('t1_bool','0x01',True),('hero_hash','0x02',True),('t2_hash','0x03',True),
    ('equip_any',['0x04'],True),('rs_hash','0x05',False),
])
def test_synthetic_save_joins(field,value,expected):
    save={'progression_tables':{'table1_bool':['0x01'],'hero_items':{'0x02':1},
                                'table2_stage':{'0x03':4},'equip_owned':['0x04']}}
    assert pins._check_is_collected({'id':'1'},'artifact',save,pin_map={'1':{field:value}}) is expected


def test_unknown_mapping_and_resource_loot_do_not_invent_completion():
    save={'progression_tables':{'table2_stage':{'0x123':4}}}
    assert pins._check_is_collected({'id':'1'},'lore',save,pin_map={}) is None
    assert pins._check_is_collected({'id':'1'},'wood_chest',save,pin_map={'1':{'t2_hash':'0x123'}}) is None
    assert pins._check_is_collected({'id':'1'},'wood_chest',save,manual_ids={'1'}) is True


def test_summary_preserves_unknowns():
    rows=[{'id':str(i),'is_completionist':True,'status':s,'category_key':'artifact'}
          for i,s in enumerate(['collected','not_collected','unknown'])]
    result=pins.summarize_pois_completion(rows)
    assert (result['collected'],result['remaining'],result['unknown'],result['total']) == (1,1,1,3)
    assert pins.summarize_pois_completion([])['percent'] == 0


def test_nested_brackets_and_external_links_are_safe():
    text='[Thing [1]](https://mapgenie.io/test?locationIds=2) [outside](https://example.invalid/)'
    result=pins._localize_links(text,{'2':{'name':'Local','realm':'alfheim'}})
    assert result == '[Local](pin:alfheim:2) outside'
