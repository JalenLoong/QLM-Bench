"""Offline Push-only admission audit, unchanged-video merge and review sheets.

Run this file directly with the data Python and QLM src on PYTHONPATH. It does
not import the simulator/RAMBO package or modify any input demonstration.
"""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path

from qlm_bench.compatibility.dataset_v2.validation import file_hash, inventory, validate_canonical
from qlm_bench.compatibility.dataset_v2.media import MediaTools
from qlm_bench.data.tools import build_replay, merge_episodes
from qlm_bench.scaleup import check_slots


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')


def previews(accepted, output):
    """Actual initial frame pairs; scene statistics are not visibility labels."""
    import av
    import numpy as np
    from PIL import Image, ImageDraw
    if output.exists():
        raise ValueError('Refuse existing review directory')
    output.mkdir(parents=True)
    rows=[];tiles=[]
    for row in sorted(accepted, key=lambda r:r['episode_uid']):
        if row['source']!='new':continue
        root=Path(row['canonical']);contract=json.loads((root/'meta/contract.json').read_text())
        ep=contract['episodes'][0]
        tile=Image.new('RGB',(640,206),'white');draw=ImageDraw.Draw(tile)
        draw.text((4,4),row['episode_uid']+' | '+row['metadata']['trajectory_type']+' | '+row['metadata']['asset_id'],fill='black')
        stats={}
        for index,key in enumerate(('observation.images.ego','observation.images.task_centric')):
            path=root/ep['videos'][key]['path']
            with av.open(str(path)) as stream:
                frame=next(stream.decode(video=0)).to_ndarray(format='rgb24')
            stats[key]={'rgb_std':float(np.std(frame)), 'video_sha256':ep['videos'][key]['sha256']}
            tile.paste(Image.fromarray(frame).resize((320,180)),(index*320,26))
        tiles.append(tile);rows.append({'episode_uid':row['episode_uid'],'initial_frames':stats,'object_visibility':'requires visual review; either camera is sufficient'})
    pages=[]
    for start in range(0,len(tiles),10):
        page=Image.new('RGB',(1280,1030),'white')
        for index,tile in enumerate(tiles[start:start+10]):page.paste(tile,((index%2)*640,(index//2)*206))
        path=output/f'initial-pairs-{start//10+1:02d}.png';page.save(path);pages.append(str(path))
    result={'new_episodes':len(rows),'pairs':rows,'pages':pages,'frame_index':0,'view_order':['ego','task_centric'],'human_visibility_review':'pending'}
    write(output/'index.json',result)
    return result


def audit(root, accepted):
    plan=json.loads((root/'plan-v1/slot-plan.json').read_text())
    quota=check_slots(plan,accepted=accepted)
    historical=[];new=[];recovery=[]
    for row in accepted:
        evidence=None
        canonical=Path(row['canonical']);contract=json.loads((canonical/'meta/contract.json').read_text())
        ep=contract['episodes'][0]
        assert not contract['diagnostic_only'] and ep['status']=='success'
        assert ep['episode_uid']==row['episode_uid'] and ep['raw_manifest_sha256']==row['source_identity_sha256']
        assert file_hash(Path(row['raw'])/'manifest.json')==row['source_identity_sha256']
        if row['source']=='historical':
            ext=contract['extensions']['scaleup'];source=Path(ext['historical_source_root'])
            assert file_hash(source/'meta/checksums.json')==ext['historical_inventory_sha256']
            inventory(source)
            historical.append({'episode_uid':row['episode_uid'],'historical_episode_uid':ext['historical_episode_uid'],
                'source_inventory_sha256':ext['historical_inventory_sha256'],'original_inventory_and_payloads':'unchanged'})
        else:
            result=json.loads((Path(row['raw']).parents[1]/'result.json').read_text())
            assert result['outcome']=='success' and result['passed'] and result['terminal_before_reset'] and result['recovery_verified']
            assert result['n_boundaries']==result['n_actions']+1
            capture=json.loads((Path(row['raw'])/'capture.json').read_text())
            assert capture['profile']['scaleup_metadata']==row['metadata']
            if row['metadata']['trajectory_type']=='recovery':
                events=[cmd['extensions']['expert'].get('recovery_evidence') for cmd in capture['commands'] if cmd['extensions']['expert'].get('recovery_evidence')]
                assert events
                resumed=[event for command in capture['commands']
                    if (event:=command['extensions']['expert'].get('recovery_evidence'))
                    and command['start_tick']/500-event['start']>=2.2]
                assert resumed
                evidence={'progress_before_m':max(e['progress_before'] for e in events),
                    'maximum_separation_m':max(e['max_separation'] for e in events),
                    'minimum_separation_after_correction_m':min(e['current_separation_m'] for e in resumed),
                    'final_progress_m':events[-1]['progress_m'],
                    'correction_recorded':any(e['corrected'] for e in events),
                    'contact_pair_measurement':'unknown; geometric separation evidence only'}
                assert evidence['progress_before_m']>=.10 and evidence['maximum_separation_m']>=.045 and evidence['correction_recorded']
                assert evidence['minimum_separation_after_correction_m']<evidence['maximum_separation_m'] and evidence['final_progress_m']>evidence['progress_before_m']
            new.append({'episode_uid':row['episode_uid'],'attempt':row['accepted_attempt'],
                'source_identity':result['source'],'realized_retry_condition':capture['profile'].get('retry_realized_condition')})
        if row['metadata']['trajectory_type']=='recovery':
            recovery.append({'episode_uid':row['episode_uid'],'source':row['source'],
                'evidence':'historical full-trajectory audited recovery' if row['source']=='historical' else 'actual progress, foot withdrawal, separation, corrective recontact, successful terminal',
                'measured_geometry':evidence})
    return {'work_id':'QLM-DATA-001','quota_validation':quota,'historical':historical,'new':new,'recovery':recovery,
        'counts':{key:dict(Counter(row['metadata'][key] for row in accepted)) for key in ('split','difficulty','trajectory_type','asset_id','appearance_preset')},
        'accepted_episodes':len(accepted),'historical_episodes':len(historical),'new_episodes':len(new),
        'policy_evaluation':'not_run','published':False,'wam_changed':False}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--ffmpeg',required=True);p.add_argument('--ffprobe',required=True)
    p.add_argument('--preview-only',action='store_true')
    p.add_argument('--review-directory',type=Path)
    args=p.parse_args(argv);root=args.root.resolve()
    accepted=json.loads((root/'accepted.json').read_text())
    if args.preview_only:
        result=previews(accepted,args.review_directory or root/f'visual-review-{len(accepted):03d}')
        print(json.dumps({'new_episodes':result['new_episodes'],'pages':result['pages']}),flush=True);return
    report=audit(root,accepted);write(root/'admission-audit.json',report)
    order={'train':0,'validation':1,'test':2}
    entries=[{'canonical':row['canonical'],'split':row['metadata']['split']} for row in sorted(accepted,key=lambda r:(order[r['metadata']['split']],r['episode_uid']))]
    write(root/'merge-entries.json',entries)
    destination=root/'canonical-100-v1'
    print('PUSH_FINAL_MERGE_BEGIN',flush=True)
    result=merge_episodes(entries,destination,ffmpeg=args.ffmpeg,ffprobe=args.ffprobe,work_id='QLM-DATA-001')
    # Add the frozen task metadata to this new collection only. Source media,
    # trajectories and original releases remain unchanged.
    write(destination/'meta/scaleup.json',{'schema':'qlm-push-scaleup-accepted-v1','work_id':'QLM-DATA-001',
        'slots':accepted,'plan_sha256':file_hash(root/'plan-v1/slot-plan.json'),
        'raw_storage':'original historical Raw roots and accepted task attempts; no failure artifacts in collection'})
    contract_path=destination/'meta/contract.json';contract=json.loads(contract_path.read_text())
    contract['extensions']['scaleup_manifest']={'path':'meta/scaleup.json','sha256':file_hash(destination/'meta/scaleup.json')}
    write(contract_path,contract)
    write(destination/'meta/checksums.json',{str(path.relative_to(destination)):file_hash(path) for path in sorted(destination.rglob('*')) if path.is_file() and path!=destination/'meta/checksums.json'})
    structure=validate_canonical(destination,tools=MediaTools(args.ffmpeg,args.ffprobe),check_media=False)
    replay=build_replay(destination,root/'replay-100-v1.html')
    review=previews(accepted,args.review_directory or root/'visual-review-100')
    write(root/'final-validation.json',{'admission':report,'merged_validation':result,'post_metadata_structure_validation':structure,
        'replay':replay,'initial_frame_review':{'index':str(root/'visual-review-100/index.json'),'status':'pending'},
        'canonical':str(destination),'task_complete':False,'remaining_gate':'human initial-frame visibility review and WAM/source preservation readback'})
    print(json.dumps({'accepted':100,'merged':str(destination),'media_validation':result['video_validation'],'preview_pages':review['pages']}),flush=True)


if __name__=='__main__':main()
