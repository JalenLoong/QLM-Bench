"""Push-only bounded attempts, CPU packaging and local admission ledger."""
from __future__ import annotations
import argparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from qlm_bench.scaleup import SlotAttempts, check_slots
from rambo.tasks.common.push_box_retry import PushSlotAttempts, attempt_limit


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_suffix('.tmp.json');temporary.write_text(json.dumps(value,indent=2)+'\n');temporary.replace(path)


def metadata_hash(metadata):
    return hashlib.sha256(json.dumps(metadata,sort_keys=True).encode()).hexdigest()


def inspect_normal_failure(attempt,uid):
    """Report measured major lateral overflow while the expert keeps advancing."""
    import numpy as np
    raw=attempt/'raw'/uid;capture_path=raw/'capture.json'
    if not capture_path.exists():return {'checked':False,'reason':'capture unavailable'}
    data=json.loads(capture_path.read_text());profile=data['profile'];gx,gy=profile['goal_x'],profile['goal_y'];hits=[];reached_goal_x=False
    for command,boundary in zip(data['commands'],data['boundaries']):
        review=boundary['task_review'];pts=np.asarray(review['footprint_xy']);lo=pts.min(0);hi=pts.max(0)
        x=max(0.,min(hi[0],gx[1])-max(lo[0],gx[0]))/(hi[0]-lo[0])
        y=max(0.,min(hi[1],gy[1])-max(lo[1],gy[0]))/(hi[1]-lo[1])
        velocity=command['extensions']['expert'].get('commanded_world_base_velocity',[0.,0.,0.])
        reached_goal_x=reached_goal_x or x>=.7
        if reached_goal_x and y<=.65 and velocity[0]>=.035:
            hits.append({'simulation_seconds':boundary['simulation_time_ns']/1e9,'inside_x_ratio':float(x),'inside_y_ratio':float(y),
                'world_forward_command_m_s':float(velocity[0]),'footprint_xy':review['footprint_xy'],'goal_x':gx,'goal_y':gy})
    return {'checked':True,'matches_user_major_overflow_case':len(hits)>=10,'matching_policy_frames':len(hits),
        'first_matching_state':hits[0] if hits else None,'largest_outside_y_fraction':max([1-h['inside_y_ratio'] for h in hits] or [0.]),
        'criterion':'after reaching >=70% X overlap at least once, at least0.2s with >=35% Y footprint outside and continued forward command>=0.035m/s; may subsequently overshoot X; videos retained for human confirmation'}


def finish_external(log,metadata,index,outcome,valid,reason):
    """Finish the specifically recorded attempt, without treating it as a restart."""
    rows=[json.loads(line) for line in log.read_text().splitlines() if line]
    latest=next(row for row in reversed(rows) if row['episode_slot']==metadata['episode_uid'])
    if latest['status']!='running' or latest['attempt_index']!=index or latest['slot_metadata_sha256']!=metadata_hash(metadata):
        raise ValueError('No matching pending external attempt')
    attempt=object.__new__(PushSlotAttempts)
    attempt.limit=attempt_limit(log.parent,metadata)
    attempt.metadata=metadata;attempt.log_path=log;attempt.index=index;attempt.pending=True;attempt.accepted=False;attempt.identity=metadata_hash(metadata)
    return attempt.finish(outcome,validation_passed=valid,reason=reason)


def package(repository,root,uid,index,data_python,ffmpeg,ffprobe):
    attempt=root/'attempts'/f'{uid}__a{index:02d}'
    env=os.environ.copy();env['PYTHONPATH']=str(repository/'src')
    command=[data_python,'-m','qlm_bench.cli','data','convert','--raw',str(attempt/'raw'/uid),
        '--canonical',str(attempt/'canonical'),'--ffmpeg',ffmpeg,'--ffprobe',ffprobe]
    if (attempt/'canonical').exists():
        # Completed conversion may precede a deliberate manager restart. Reuse
        # only after fresh complete validation; never overwrite the payload.
        code='import sys,json; from qlm_bench.compatibility.dataset_v2.validation import validate_raw,validate_canonical; from qlm_bench.compatibility.dataset_v2.media import MediaTools; t=MediaTools(sys.argv[3],sys.argv[4]); print(json.dumps({"raw":validate_raw(sys.argv[1],tools=t),"canonical":validate_canonical(sys.argv[2],tools=t)}))'
        command=[data_python,'-c',code,str(attempt/'raw'/uid),str(attempt/'canonical'),ffmpeg,ffprobe]
    with (attempt/'packaging.log').open('a') as stream:
        result=subprocess.run(command,env=env,stdout=stream,stderr=subprocess.STDOUT)
    return result.returncode==0


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--data-python',required=True)
    p.add_argument('--ffmpeg',required=True);p.add_argument('--ffprobe',required=True)
    p.add_argument('--resource-root',type=Path,required=True)
    p.add_argument('--batch-size',type=int,default=10)
    p.add_argument('--packaging-workers',type=int,default=2)
    p.add_argument('--pilot-only',action='store_true')
    p.add_argument('--normal-only',action='store_true')
    p.add_argument('--skip-historical-admission',action='store_true')
    p.add_argument('--defer-exhausted',action='store_true')
    p.add_argument('--admit-existing-attempt',action='store_true')
    args=p.parse_args(argv);root=args.root.resolve()
    if not 1<=args.batch_size<=10:
        p.error('Current user-authorized lane limit is10')
    if not 1<=args.packaging_workers<=2:
        p.error('CPU packaging uses at most2 independent workers')
    repository=Path(__file__).resolve().parents[5]
    slots=json.loads((root/'plan-v1/conditions.json').read_text())['slots']
    plan=json.loads((root/'plan-v1/slot-plan.json').read_text());check_slots(plan)
    accepted_path=root/'accepted.json';accepted=json.loads(accepted_path.read_text()) if accepted_path.exists() else []
    byuid={row['episode_uid']:row for row in accepted}
    for slot in slots:
        metadata=slot['metadata'];uid=metadata['episode_uid']
        if not args.skip_historical_admission and slot['source']=='historical' and uid not in byuid:
            old=slot['historical'];canonical=root/'historical-derived'/uid
            byuid[uid]=dict(episode_uid=uid,metadata=metadata,status='success',validation_passed=True,
                source_identity_sha256=old['raw_manifest_sha256'],canonical=str(canonical),source='historical',historical_episode_uid=old['historical_episode_uid'],raw=old['raw_path'])
    accepted=list(byuid.values());write(accepted_path,accepted)
    pending=[slot for slot in slots if slot['source']=='new' and slot['metadata']['episode_uid'] not in byuid and
             (not args.normal_only or slot['metadata']['trajectory_type']=='normal') and
             (not args.pilot_only or int(slot['metadata']['episode_uid'].split('__ep')[1])<=10)]
    log=root/'collection-log.jsonl'
    if args.defer_exhausted and log.exists():
        rows=[json.loads(line) for line in log.read_text().splitlines() if line]
        latest={row['episode_slot']:row for row in rows}
        exhausted={s['metadata']['episode_uid'] for s in pending
                   if latest.get(s['metadata']['episode_uid'],{}).get('status')=='exhausted'
                   and latest[s['metadata']['episode_uid']]['attempt_index']>=attempt_limit(root,s['metadata'])}
        pending=[s for s in pending if s['metadata']['episode_uid'] not in exhausted]
    # Verify all selected resources before consuming any attempt budget.
    from qlm_bench.assets import resolve_asset
    for asset_id in sorted({s['metadata']['asset_id'] for s in pending} | {'rambo-go2-controller'}):
        resolve_asset(asset_id,args.resource_root)
    def process(slot,index,packaged=None):
        metadata=slot['metadata'];uid=metadata['episode_uid'];attempt=root/'attempts'/f'{uid}__a{index:02d}'
        if not (attempt/'result.json').exists():return 'runtime_error',False,'runtime startup/capture error'
        result=json.loads((attempt/'result.json').read_text())
        outcome=result['outcome']
        if outcome!='success':return outcome,False,result.get('status',outcome)
        if not result.get('recovery_verified'):
            return 'task_failure',False,'successful task lacks required actual recovery evidence'
        if result.get('approach_continuity_verified') is False:
            return 'task_failure',False,'new demonstration contains unacceptable early FL target discontinuity'
        valid=package(repository,root,uid,index,args.data_python,args.ffmpeg,args.ffprobe) if packaged is None else packaged
        if valid:
            raw=attempt/'raw'/uid
            source_hash=hashlib.sha256((raw/'manifest.json').read_bytes()).hexdigest()
            byuid[uid]=dict(episode_uid=uid,metadata=metadata,status='success',validation_passed=True,source_identity_sha256=source_hash,
                canonical=str(attempt/'canonical'),raw=str(raw),source='new',accepted_attempt=index)
            write(accepted_path,list(byuid.values()))
        return 'success' if valid else 'runtime_error',valid,'' if valid else 'Raw/Canonical validation failed'
    if args.admit_existing_attempt:
        for slot in pending[:]:
            uid=slot['metadata']['episode_uid']
            entries=[json.loads(line) for line in log.read_text().splitlines() if line]
            entries=[row for row in entries if row['episode_slot']==uid]
            if not entries or entries[-1]['status']!='running':continue
            number=entries[-1]['attempt_index'];attempt=root/'attempts'/f'{uid}__a{number:02d}'
            if not (attempt/'result.json').exists():continue
            outcome,valid,reason=process(slot,number)
            finish_external(log,slot['metadata'],number,outcome,valid,reason)
            if not valid and outcome in ('timeout','fall','task_failure'):
                failure=repository.parents[1]/'runs/audit/qlm-scaleup-push-box-20261007/failures'/uid/f'a{number:02d}'
                failure.parent.mkdir(parents=True,exist_ok=True);shutil.move(str(attempt),str(failure))
            if valid:pending.remove(slot)
    groups=defaultdict(list)
    for slot in pending:
        groups[(slot['metadata']['asset_id'],slot['metadata']['appearance_preset'])].append(slot)
    for group,remaining in groups.items():
        while remaining:
            control=root/'collection-control.json'
            lane_limit=json.loads(control.read_text()).get('user_parallel_limit',10) if control.exists() else 10
            if type(lane_limit) is not int or not 1<=lane_limit<=10:
                raise ValueError('Explicit collection lane limit must be1..10')
            entries=[json.loads(line) for line in log.read_text().splitlines() if line] if log.exists() else []
            count=lambda s:max([row['attempt_index'] for row in entries if row['episode_slot']==s['metadata']['episode_uid']] or [0])
            target_count=count(remaining[0]);wave=[s for s in remaining if count(s)==target_count][:min(args.batch_size,lane_limit)]
            selected_ids={s['metadata']['episode_uid'] for s in wave};remaining=[s for s in remaining if s['metadata']['episode_uid'] not in selected_ids]
            managers={};indices={}
            for slot in wave:
                uid=slot['metadata']['episode_uid'];manager=PushSlotAttempts(slot['metadata'],log,limit=attempt_limit(root,slot['metadata']))
                if manager.index>=manager.limit:raise RuntimeError('Exhausted slot requires user report: '+uid)
                manager.begin();managers[uid]=manager;indices[uid]=manager.index
            # A wave requires equal attempt index; split retries in subsequent passes.
            if len(set(indices.values()))!=1:raise RuntimeError('Group retry attempts separately')
            number=next(iter(indices.values()))
            command=[str(repository/'scripts/rambo/run_scaleup.sh'),'-m','rambo.tasks.common.push_box_scaleup_collect',
                '--conditions',str(root/'plan-v1/conditions.json'),'--output-root',str(root),'--attempt',str(number),
                '--resource-root',str(args.resource_root),'--ffmpeg',args.ffmpeg,'--horizon','24','--viz','none']
            for slot in wave:command.extend(['--uid',slot['metadata']['episode_uid']])
            wave_log=root/'local-logs'/f'{wave[0]["metadata"]["episode_uid"]}-a{number:02d}.log';wave_log.parent.mkdir(exist_ok=True)
            env=os.environ.copy();env.update(OMNI_KIT_ACCEPT_EULA='Y',WORKSPACE_ROOT=str(repository.parents[1]),RAMBO_PYCACHE_PREFIX='/tmp/qlm-push-scaleup-pycache')
            with wave_log.open('w') as stream:subprocess.run(command,cwd=repository,env=env,stdout=stream,stderr=subprocess.STDOUT)
            eligible=[]
            for slot in wave:
                uid=slot['metadata']['episode_uid'];result_path=root/'attempts'/f'{uid}__a{number:02d}'/'result.json'
                if result_path.exists():
                    result=json.loads(result_path.read_text())
                    if result['outcome']=='success' and result.get('recovery_verified'):eligible.append(uid)
            with ThreadPoolExecutor(max_workers=args.packaging_workers) as pool:
                futures={uid:pool.submit(package,repository,root,uid,number,args.data_python,args.ffmpeg,args.ffprobe) for uid in eligible}
                packaged={uid:future.result() for uid,future in futures.items()}
            retries=[]
            for slot in wave:
                uid=slot['metadata']['episode_uid'];index=indices[uid]
                outcome,valid,reason=process(slot,index,packaged.get(uid))
                policy=managers[uid].finish(outcome,validation_passed=valid,reason=reason)
                print(json.dumps({'uid':uid,'attempt':index,'status':policy['status'],'outcome':outcome,'accepted_total':len(byuid)}),flush=True)
                attempt=root/'attempts'/f'{uid}__a{index:02d}'
                if not valid:
                    if outcome in ('timeout','fall','task_failure') and args.normal_only and attempt.exists():
                        diagnosis=inspect_normal_failure(attempt,uid)
                        write(attempt/'failure-diagnosis.json',diagnosis)
                        report={'uid':uid,'attempt':index,'outcome':outcome,'diagnosis':diagnosis}
                        with (root/'normal-failure-reports.jsonl').open('a') as stream:stream.write(json.dumps(report)+'\n')
                        print('NORMAL_FAILURE_REPORT='+json.dumps(report),flush=True)
                    failure_root=repository.parents[1]/'runs/audit/qlm-scaleup-push-box-20261007/failures'/uid/f'a{index:02d}'
                    failure_root.parent.mkdir(parents=True,exist_ok=True)
                    if policy['archive']=='local_full_failure' or policy['report_to_user']:
                        if attempt.exists():shutil.move(str(attempt),str(failure_root))
                    elif attempt.exists():
                        # Preserve only available videos temporarily until slot resolves.
                        temporary=root/'retry-videos'/uid/f'a{index:02d}';temporary.mkdir(parents=True,exist_ok=True)
                        for video in attempt.rglob('*.mp4'):shutil.copy2(video,temporary/(video.parent.name+'-'+video.name))
                        shutil.rmtree(attempt)
                    if policy['report_to_user']:raise RuntimeError(f'All{managers[uid].limit} attempts exhausted; available failure video preserved: '+uid)
                    retries.append(slot)
                else:
                    temporary=root/'retry-videos'/uid
                    if temporary.exists():shutil.rmtree(temporary)
            if retries:
                # Keep retries at equal attempt indices in smaller waves.
                for slot in reversed(retries):remaining.insert(0,slot)
                args.batch_size=min(args.batch_size,6)
    selected=[byuid[s['metadata']['episode_uid']] for s in slots if s['metadata']['episode_uid'] in byuid]
    write(accepted_path,selected)
    if len(selected)==100:check_slots(plan,accepted=selected)
    print(json.dumps({'accepted_total':len(selected),'pilot_complete':all(s['metadata']['episode_uid'] in byuid for s in slots[:10]),'task_complete':len(selected)==100}),flush=True)
    return 0


if __name__=='__main__':raise SystemExit(main())
