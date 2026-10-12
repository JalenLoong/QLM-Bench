"""Frozen Push-specific conditions and historical metadata mapping; CPU only."""
from __future__ import annotations
from collections import Counter
from pathlib import Path
import copy
import hashlib
import json
import math
import random
import numpy as np
from .push_box_geometry import source_geometry,world_geometry,rotation_xyzw

ASSETS={'box05':'cardboard-box-05','box01':'cardboard-box-01','box04':'cardboard-box-04'}
PRESETS={'ap_00':{'intensity':2000.,'color':[.75,.75,.75]},
         'ap_01':{'intensity':2000.,'color':[.80,.74,.67]},
         'ap_02':{'intensity':1700.,'color':[.72,.75,.80]},
         'ap_03':{'intensity':2200.,'color':[.78,.78,.74]}}


def resolve_case(base, *, low, high, seed, clean, recovery, yaw_deg=0):
    rng=random.Random(seed)
    angle=math.radians(yaw_deg);q=[0.,0.,math.sin(angle/2),math.cos(angle/2)];R=rotation_xyzw(q)
    face=min([('local_x_min',[-1.,0.,0.]),('local_x_max',[1.,0.,0.]),('local_y_min',[0.,-1.,0.]),('local_y_max',[0.,1.,0.])],key=lambda x:float((R@x[1])[0]))[0]
    geometry=source_geometry(low,high,face=face);vertices=np.asarray(geometry['corners'])@R.T
    face_x=.54+rng.uniform(-.006,.006) if clean else rng.uniform(.525,.555)
    center_y=.142+rng.uniform(-.004,.004) if clean else rng.uniform(.134,.151)
    position=[face_x-float(vertices[:,0].min()),center_y-float((R@geometry['center'])[1]),base['initial_floor_clearance']-float(vertices[:,2].min())]
    width_x=float(np.ptp(vertices[:,0]));width_y=float(np.ptp(vertices[:,1]))
    goal_x=.95+(rng.uniform(-.008,.008) if clean else rng.uniform(-.015,.020))
    goal_y=.15+(rng.uniform(-.005,.005) if clean else rng.uniform(-.012,.012))
    gx=max(.4,width_x+(.15 if clean else rng.uniform(.13,.18)))
    gy=max(.5,width_y+(.15 if clean else rng.uniform(.13,.18)))
    p=copy.deepcopy(base)
    p.update(goal_x=[goal_x,goal_x+gx],goal_y=[goal_y-gy/2,goal_y+gy/2],goal_color=[.05,.8,.15],
             scaleup_recovery=recovery,recovery_progress_m=.12,
             episode_scenario={'work_id':'QLM-DATA-001','authorization':'qlm-scaleup-push-v1','selected_face':face},
             instruction='Push the box into the target area.')
    p['expert'].update(motion='coordinated',transition_s=.45,push_base_speed=.12,
                       push_foot_x=.38,leg_finish_max_x=.40,lateral_tracking_gain=2.,
                       lateral_tracking_limit_m=.015,corner_recovery=False)
    return {'position':position,'orientation':q,'selected_face':face,'profile':p,'seed':seed}


def generate(workspace, repository, output):
    workspace,repository,output=map(Path,(workspace,repository,output))
    audit=json.loads((workspace/'data/qlm_bench/scaleup_v1/reuse-audit-20261007-v1/reuse-manifest.json').read_text())
    old=[r for r in audit['episodes'] if r['task_id']=='push_box'];assert len(old)==50
    bounds={}
    for alias,asset in ASSETS.items():
        row=next(r for r in old if r['scenario'].get('asset','box05')==alias)
        summary=json.loads((Path(row['raw_path'])/'summary.json').read_text())
        geometry=summary['initial_geometry']['source']
        bounds[asset]={'low':geometry['low'],'high':geometry['high'],'sha256':row['asset_hashes'][0]}
    # Explicit pilot4/3/3 covers all source assets, including one new clean recovery.
    chosen=[]
    chosen.append(next(r for r in old if r['historical_episode_uid']=='demo_00'))
    chosen.append(None)
    chosen += [r for r in old if r['scenario'].get('asset')=='box01'][:3]
    chosen += [r for r in old if r['scenario'].get('asset')=='box04'][:3]
    chosen.append(next(r for r in old if r['historical_episode_uid']=='demo_10-a4'))
    chosen.append(next(r for r in old if r['historical_episode_uid']=='demo_13-a4'))
    seen={r['historical_episode_uid'] for r in chosen if r}
    remaining=[r for r in old if r['historical_episode_uid'] not in seen]
    slots=[];new_counter=0
    def old_slot(row,number):
        uid=row['historical_episode_uid'];scenario=row['scenario'];alias=scenario.get('asset','box05')
        clean=uid.startswith('demo_') and '-a' not in uid and int(uid.split('_')[1])<10
        metadata=dict(episode_uid=f'push_box__ep{number:04d}',task_id='push_box',split='train',
            difficulty='clean' if clean else 'randomized',trajectory_type=row['trajectory_type'],
            recovery_type='lateral_deviation' if row['trajectory_type']=='recovery' else None,
            appearance_preset='ap_00',asset_id=ASSETS[alias],initial_condition_id=f'ic_{number:04d}',goal_condition_id=f'gc_{number:04d}',
            environment_seed=scenario.get('parameters',{}).get('seed',scenario.get('seed',42)))
        return {'metadata':metadata,'source':'historical','historical':row}
    base=json.loads((repository/'configs/collection/push_box.json').read_text())
    def new_slot(number,asset,clean,recovery,preset):
        nonlocal new_counter
        seed=202610070000+number;bound=bounds[asset];p=copy.deepcopy(base)
        p.update(asset_id=asset,asset_sha256=bound['sha256'])
        yaw=0 if clean else [0,90,180,270][number%4]
        case=resolve_case(p,low=bound['low'],high=bound['high'],seed=seed,clean=clean,recovery=recovery,yaw_deg=yaw)
        metadata=dict(episode_uid=f'push_box__ep{number:04d}',task_id='push_box',split='train',difficulty='clean' if clean else 'randomized',
            trajectory_type='recovery' if recovery else 'normal',recovery_type='contact_loss' if recovery else None,
            appearance_preset=preset,asset_id=asset,initial_condition_id=f'ic_{number:04d}',goal_condition_id=f'gc_{number:04d}',environment_seed=seed)
        case['metadata']=metadata;case['profile']['scaleup_metadata']=metadata;new_counter+=1
        return {'metadata':metadata,'source':'new','case':case}
    for number,row in enumerate(chosen,1):
        slots.append(old_slot(row,number) if row else new_slot(number,ASSETS['box05'],True,True,'ap_00'))
    for row in remaining:slots.append(old_slot(row,len(slots)+1))
    # Remaining9 clean and40 randomized new slots; pilot already contributes1 clean recovery.
    labels=[(ASSETS['box05'],True,False,'ap_00')]*6+[(ASSETS['box05'],True,True,'ap_00')]*3
    labels += [(ASSETS['box05'],False,False,'ap_01')]*4+[(ASSETS['box05'],False,True,'ap_01')]*8
    labels += [(ASSETS['box05'],False,False,'ap_02')]*2+[(ASSETS['box05'],False,True,'ap_02')]*6
    labels += [(ASSETS['box01'],False,False,'ap_03')]*10+[(ASSETS['box04'],False,False,'ap_03')]*10
    for asset,clean,recovery,preset in labels:slots.append(new_slot(len(slots)+1,asset,clean,recovery,preset))
    assert len(slots)==100 and new_counter==50
    # Keep all pilot slots in train, then allocate stratified val/test from remaining slots.
    used=set()
    for split in ('validation','test'):
        needs={('clean','normal'):1,('clean','recovery'):1,('randomized','normal'):7,('randomized','recovery'):1}
        for key,count in needs.items():
            rows=[s for s in slots[10:] if s['metadata']['episode_uid'] not in used and (s['metadata']['difficulty'],s['metadata']['trajectory_type'])==key]
            for row in rows[:count]:
                row['metadata']['split']=split;used.add(row['metadata']['episode_uid'])
    plan={'schema':'qlm-scaleup-slot-plan-v1','task_id':'push_box','seed':20261007,'asset_pool':list(bounds),
          'recovery_types':['contact_loss','lateral_deviation'],'status':'planned','slots':[s['metadata'] for s in slots]}
    from qlm_bench.scaleup import check_slots
    check_slots(plan)
    output.mkdir(parents=True,exist_ok=True)
    for name,value in [('slot-plan.json',plan),('conditions.json',{'slots':slots}),('asset-pool.json',{'assets':bounds,'physics':'original fixed source; no modifications'}),('appearance-presets.json',PRESETS)]:
        target=output/name
        if target.exists():raise ValueError('Refuse frozen plan overwrite')
        target.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')
    return {'slots':100,'historical':50,'new':50,'pilot_new':1,'new_normal':32,'new_recovery':18}
