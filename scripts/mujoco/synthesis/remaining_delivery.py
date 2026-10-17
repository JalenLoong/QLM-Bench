"""Task-once consumer admission, whole-task audit/merge, and final random review."""
import argparse
import html
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from qlm_bench.backends.mujoco.remaining_tasks import WORKSPACE as W, TASKS, binding
from qlm_bench.backends.mujoco.trace import sha,write_json

AUDIT=W/'runs/audit/remaining-six-production-20261016-v1'


def prompts():
    import torch
    from transformers import T5TokenizerFast,UMT5EncoderModel
    from wam_policy.v3.text import encode_prompts
    source=W/'models/lingbot-va-base-source-68b7bc1'
    prior=W/'runs/audit/mujoco-alignment-repair-v1/verified-prompts-a01/acceptance.json'
    record=json.loads(prior.read_text());assert record['passed']
    inventory={k:v for k,v in record['verified_frozen_files'].items() if k.startswith(('tokenizer/','text_encoder/'))}
    for name,value in inventory.items():assert sha(source/name)==value,name
    missing=[]
    for task in TASKS:
        out=AUDIT/'prompts'/task
        if (out/'reference.json').exists():
            ref=json.loads((out/'reference.json').read_text());assert sha(ref['path'])==ref['sha256']
        else:missing.append(task)
    if not missing:return
    torch.set_num_threads(4)
    tokenizer=T5TokenizerFast.from_pretrained(source/'tokenizer',local_files_only=True)
    encoder=UMT5EncoderModel.from_pretrained(source/'text_encoder',torch_dtype=torch.bfloat16,local_files_only=True).to('cuda')
    for task in missing:
        instruction=json.loads(Path(binding(task)['primary_model']).with_suffix('.task.json').read_text())['instruction']
        out=AUDIT/'prompts'/task;out.mkdir(parents=True,exist_ok=False)
        value=encode_prompts([instruction],tokenizer,encoder).cpu();assert list(value.shape)==[1,512,4096]
        path=out/'embedding.pt';torch.save(value,path)
        ref=dict(path=str(path),sha256=sha(path),instruction=instruction,source_revision=record['source_revision'],
                 text_config_sha256=inventory['text_encoder/config.json'],padding='max_length_512_attention_mask_zeroed')
        write_json(out/'reference.json',ref)
        write_json(out/'acceptance.json',dict(passed=True,task_id=task,source_inventory=inventory,
            prior_verified_inventory_sha256=sha(prior),shape=list(value.shape),training=False,normalizer_refit=False))
        print('PROMPT',task,'passed',flush=True)


def consumers(root):
    root=Path(root);c=json.loads((root/'campaign.json').read_text());q=json.loads((root/'queue.json').read_text())
    task=c['task_id'];prompt=json.loads((AUDIT/'prompts'/task/'reference.json').read_text())
    assert sha(prompt['path'])==prompt['sha256']
    passed=root/'dual-wam-compatibility.json'
    if passed.exists():
        prior=json.loads(passed.read_text());assert prior['passed'] and prior['task_id']==task and prior['campaign_sha256']==c['profile_sha256']
        print('TASK-ONCE receipt reused',task,flush=True);return
    assert all(q['slots'][s['episode_uid']]['status']=='accepted' for s in c['slots'][:2])
    records=[]
    for variant in ('v2','v3'):
        config=json.loads((W/f'runs/audit/rgb-resolution-360p-20261014-v1/{variant}-inference.json').read_text())
        config.get('resources',config)['prompt_embedding']=prompt
        config_path=root/(variant+'-inference.json');write_json(config_path,config)
        repo=W/('repos/WAM-Policy-v2-mujoco' if variant=='v2' else 'repos/WAM-Policy-mujoco')
        source=repo/('src/wam_policy/pilot_readback.py' if variant=='v2' else 'src/wam_policy/v3/pilot_readback.py')
        env=dict(os.environ,PYTHONPATH=str(repo/'src')+':'+str(root/'frozen-source/src'),OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
        for slot in c['slots'][:2]:
            uid=slot['episode_uid'];out=root/'readbacks'/(variant+'-'+slot['difficulty'])
            if (out/'result.json').exists():
                result=json.loads((out/'result.json').read_text())
                assert result['passed'] and result['episode_uid']==uid and result['actual_instruction']==prompt['instruction']
            else:
                assert not out.exists(),'Incomplete model attempt retained; inspect before retry'
                out.parent.mkdir(exist_ok=True);start=time.time()
                cmd=[str(W/'envs/lingbot-va-9d-py310/bin/python'),'-u','-m',
                    'wam_policy.pilot_readback' if variant=='v2' else 'wam_policy.v3.pilot_readback',
                    '--canonical',str(Path(c['data_root'])/'new'/uid/'episodes'/uid/'canonical'),
                    '--recording-profile',str(root/'profiles'/(uid+'.json')),'--frozen',str(W/'models/lingbot-va-base-source-68b7bc1'),
                    '--output',str(out),'--inference-config',str(config_path),'--ffmpeg',c['ffmpeg'],'--ffprobe',c['ffprobe']]
                with (root/(variant+'-'+slot['difficulty']+'-readback.log')).open('x') as log:
                    p=subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT)
                write_json(root/(variant+'-'+slot['difficulty']+'-attempt.json'),dict(exit_code=p.returncode,started_unix_s=start,
                    wall_s=time.time()-start,source_entry_sha256=sha(source),task_id=task,episode_uid=uid,training=False,
                    work_id='DATA-020' if variant=='v2' else 'v3/DATA-010'))
                if p.returncode:raise RuntimeError('Actual consumer failed: '+variant+'/'+slot['difficulty'])
                result=json.loads((out/'result.json').read_text())
                assert result['passed'] and result['actual_instruction']==prompt['instruction']
            records.append(dict(variant=variant,difficulty=slot['difficulty'],episode_uid=uid,result=str(out/'result.json'),sha256=sha(out/'result.json')))
            print('CONSUMER',task,variant,slot['difficulty'],'passed',flush=True)
    write_json(passed,dict(passed=True,task_id=task,campaign_sha256=c['profile_sha256'],checks=records,
        normalizer_fitted=False,training=False,optimizer_steps=0,model_weights_changed=False,per_task_once=True))


def telemetry_audit(out,trace):
    import numpy as np
    import pyarrow as pa
    import pyarrow.parquet as pq
    from qlm_bench.backends.mujoco.trace import verify_trace
    uid=out.name;raw=out/'raw'/uid
    _,arrays,telemetry,commands,terminal=verify_trace(trace);results={}
    for source,filename in [('controller','controller_100hz'),('physics','physics_500hz'),('contact_sensor','contact_sensor')]:
        table=pq.read_table(raw/'streams'/(filename+'.parquet'));original=telemetry[source]
        assert table.num_rows==len(original)
        for key in original[0]:
            expected=pa.array([row[key] for row in original],type=table.schema.field(key).type)
            assert table[key].combine_chunks().equals(expected),(uid,source,key)
        results[source]=dict(rows=len(original),all_original_columns_exact_at_schema_dtype=True)
    policy=pq.read_table(raw/'streams/policy_50hz.parquet')
    for key,field in [('action.executed','executed'),('action.requested','requested')]:
        expected=pa.array([c[field] for c in commands],type=policy.schema.field(key).type)
        assert policy[key].combine_chunks().equals(expected)
    np.testing.assert_array_equal(policy['simulation_time_ns'].to_numpy(),arrays['simulation_time_ns'][:-1])
    np.testing.assert_array_equal(policy['physics_step'].to_numpy(),arrays['physics_step'][:-1])
    assert json.loads((raw/'manifest.json').read_text())['terminal']['state']==terminal['state']
    return dict(passed=True,streams=results,actions_timestamps_terminal_exact=True)


def admission(root):
    from qlm_bench.backends.mujoco.remaining_production import load_campaign
    from qlm_bench.backends.mujoco.rendition import validate_output
    from qlm_bench.compatibility.dataset_v2.media import MediaTools
    root=Path(root);c=load_campaign(root/'campaign.json',root/'frozen-source');q=json.loads((root/'queue.json').read_text())
    consumer=json.loads((root/'dual-wam-compatibility.json').read_text());assert consumer['passed']
    checks=[]
    for slot in c['slots'][:2]:
        uid=slot['episode_uid'];assert q['slots'][uid]['status']=='accepted'
        out=Path(c['data_root'])/'new'/uid/'episodes'/uid
        checks.append(dict(episode_uid=uid,output=validate_output(out,profile_path=root/'profiles'/(uid+'.json'),
            tools=MediaTools(c['ffmpeg'],c['ffprobe']),check_media=False),telemetry=telemetry_audit(out,q['slots'][uid]['trace'])))
    write_json(root/'production-admission.json',dict(passed=True,task_id=c['task_id'],campaign_sha256=c['profile_sha256'],
        checks=checks,consumer_receipt_sha256=sha(root/'dual-wam-compatibility.json'),samples_count_in100=True,
        human_pilot_gate=False,physics_backend='NativeCPU',render_backend='NativeEGL'))
    print('END-TO-END ADMISSION',c['task_id'],'passed;2count in100',flush=True)


def finalize(root):
    import numpy as np
    from qlm_bench.backends.mujoco.remaining_production import load_campaign,QUOTAS
    from qlm_bench.backends.mujoco.remaining_scenes import SUPPORT
    from qlm_bench.backends.mujoco.rendition import validate_output,audit_trace
    from qlm_bench.compatibility.dataset_v2.media import MediaTools
    from qlm_bench.compatibility.dataset_v2.merge import merge
    root=Path(root);c=load_campaign(root/'campaign.json',root/'frozen-source');q=json.loads((root/'queue.json').read_text())
    assert q['status']=='production_complete' and sum(r['status']=='accepted' for r in q['slots'].values())==100
    dest=Path(c['data_root']);tools=MediaTools(c['ffmpeg'],c['ffprobe']);seen=set();prior=[];records=[];entries=[];checks=[]
    lo,hi,_=map(np.asarray,SUPPORT[c['task_id']]);counts={s:{d:0 for d in ('clean','randomized')} for s in QUOTAS}
    for slot in sorted(c['slots'],key=lambda s:({'train':0,'validation':1,'test':2}[s['split']],s['episode_uid'])):
        uid=slot['episode_uid'];row=q['slots'][uid];out=dest/'new'/uid/'episodes'/uid
        profile=root/'profiles'/(uid+'.json');member=json.loads(profile.read_text())['slots'][0]
        check=validate_output(out,profile_path=profile,tools=tools,check_media=False)
        actual=audit_trace(row['trace']);assert actual['trajectory_sha256'] not in seen;seen.add(actual['trajectory_sha256'])
        point=np.array(actual['scene']['configuration_parameters'])
        assert all(not np.array_equal(point,p) and (split==slot['split'] or not np.all(abs(point-p)<=(hi-lo)*.005)) for p,split in prior)
        prior.append((point,slot['split']));counts[slot['split']][slot['difficulty']]+=1
        for folder,target in [('episodes',out),('raw',out/'raw'/uid)]:
            view=dest/folder;view.mkdir(exist_ok=True);link=view/uid
            if not link.is_symlink():link.symlink_to(os.path.relpath(target,view),target_is_directory=True)
            assert link.resolve()==target.resolve()
        streams=telemetry_audit(out,row['trace']);render=json.loads((out/'result.json').read_text())
        assert render['GL']['vendor']=='NVIDIA Corporation' and render['mirror_physics_advanced'] is False
        assert render['controller_loaded'] is False and render['physics_reexecuted'] is False
        records.append(dict(**{k:slot[k] for k in ('episode_uid','task_id','split','difficulty','appearance_preset')},
            trace=row['trace'],output=str(out),recording_profile=str(profile),configuration_parameters=point.tolist(),
            physical_trajectory_sha256=actual['trajectory_sha256'],n_actions=member['n_actions']))
        checks.append(dict(episode_uid=uid,output=check,telemetry=streams))
        entries.append(dict(canonical=str(out/'canonical'),split=slot['split']))
        print('FULL AUDIT',c['task_id'],len(records),'/100',flush=True)
    assert counts==QUOTAS
    write_json(root/'full-artifact-checks.json',dict(passed=True,checks=checks))
    merged=dest/'canonical'
    if merged.exists():
        from qlm_bench.compatibility.dataset_v2.validation import validate_canonical
        merge_result=validate_canonical(merged,tools=tools)
    else:merge_result=merge(entries,merged,tools,'QLM-DATA-040')
    write_json(root/'accepted100.json',records)
    write_json(root/'completion.json',dict(passed=True,task_id=c['task_id'],episodes=100,
        actions=sum(r['n_actions'] for r in records),boundaries=sum(r['n_actions']+1 for r in records),
        quotas=counts,unique_physical_traces=len(seen),cross_split_near_duplicates=0,canonical=merge_result,
        new_physics_attempts=sum(r['physical_attempts'] for r in q['slots'].values()),
        task_once_consumer_receipt_sha256=sha(root/'dual-wam-compatibility.json'),human_final_review='pending_all_six',
        training_AMD_git_HF=False))
    print('TASK100 ENGINEERING COMPLETE',c['task_id'],flush=True)


def review():
    import numpy as np
    rows=[]
    roots=json.loads((AUDIT/'active-task-roots.json').read_text()) if (AUDIT/'active-task-roots.json').exists() else {}
    for task in TASKS:
        root=Path(roots.get(task,str(AUDIT/task)));completion=json.loads((root/'completion.json').read_text());assert completion['passed']
        records=json.loads((root/'accepted100.json').read_text());assert len(records)==100
        seed=202610164000+TASKS.index(task);indices=np.random.default_rng(seed).choice(100,10,replace=False)
        selected=[records[int(i)] for i in indices]
        write_json(root/'random10-selection.json',dict(task_id=task,seed=seed,population=100,sampling='uniform_without_replacement_no_quality_or_split_filter',episodes=selected))
        c=json.loads((root/'campaign.json').read_text());media=root/'random10';media.mkdir(exist_ok=True)
        clips=[]
        for r in selected:
            raw=Path(r['output'])/'raw'/r['episode_uid'];clip=media/(r['episode_uid']+'.mp4')
            if not clip.exists():
                cmd=[c['ffmpeg'],'-nostdin','-v','error','-threads','2','-filter_complex_threads','2']
                for role in ('ego','task_centric','observer'):cmd+=['-i',str(raw/'cameras'/(role+'.mp4'))]
                cmd+=['-filter_complex','[0:v]fps=25[a];[1:v]fps=25[b];[2:v]scale=640:360[c];[c][a][b]hstack=inputs=3[v]',
                    '-map','[v]','-an','-c:v','libx264','-preset','fast','-crf','22','-pix_fmt','yuv420p','-movflags','+faststart',str(clip)]
                subprocess.run(cmd,check=True)
            clips.append(dict(episode_uid=r['episode_uid'],path=str(clip),sha256=sha(clip),display_only=True,source_policy_fps=50,display_fps=25))
            rows.append(f'<h3>{html.escape(task)} / {html.escape(r["episode_uid"])}</h3><video controls preload="none" width="100%" src="{html.escape(os.path.relpath(clip,AUDIT))}"></video>')
        write_json(root/'random10-media.json',clips)
    (AUDIT/'review.html').write_text('<!doctype html><meta charset="utf-8"><title>六task最终随机审核</title><style>body{max-width:1500px;margin:30px auto;background:#111;color:#eee;font-family:sans-serif}video{margin-bottom:30px}</style><h1>六task各100条；各均匀无放回随机10条</h1><p>Observer | Ego | Task；原速25FPS展示，正式双RGB50FPS保持。工程验收完成；用户最终动作审核待定。</p>'+''.join(rows))
    write_json(AUDIT/'completion.json',dict(engineering_complete=True,new_episodes=600,total_with_prior400=1000,
        final_user_review='pending',review=str(AUDIT/'review.html'),HF_publication=False,training_AMD_git=False))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['prompts','consumers','admission','finalize','review']);p.add_argument('--root',type=Path)
    a=p.parse_args()
    if a.mode=='prompts':prompts()
    elif a.mode=='consumers':consumers(a.root)
    elif a.mode=='admission':admission(a.root)
    elif a.mode=='finalize':finalize(a.root)
    else:review()
