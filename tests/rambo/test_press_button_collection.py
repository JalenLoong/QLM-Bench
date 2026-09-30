from pathlib import Path
from collections import Counter
import json


def test_ten_slot_balance_and_retry_bounds():
    cfg=json.loads((Path(__file__).parents[2]/'configs/press_button_collection_v1.json').read_text())
    slots=cfg['slots'];assert len({x['id'] for x in slots})==10
    assert Counter(x['asset'] for x in slots)=={'industrial':5,'emergency':5}
    assert Counter(x['motion'] for x in slots)=={'baseline':5,'early_stop':5}
    assert Counter(x['color'] for x in slots)=={'red':3,'blue':3,'green':2,'orange':2}
    assert Counter(x['split'] for x in slots)=={'train':8,'validation':1,'test':1}
    assert Counter(x['asset'] for x in slots if x['split']=='train')=={'industrial':4,'emergency':4}
    for slot in slots:
        x,y,z=slot['front_xyz'];assert x==.56 and .08<=y<=.12 and .285<=z<=.315
        assert [a['attempt'] for a in slot['attempts']]==[1,2,3]
        assert [a['standoff_m'] for a in slot['attempts']]==([.075,.070,.065] if slot['motion']=='early_stop' else [.055]*3)
    assert cfg['wall']['size']==[.025,1.,.6] and cfg['wall']['center'][2]==.3
    assert cfg['local_only'] and cfg['max_actions']==1000 and cfg['max_attempts_per_slot']==3
