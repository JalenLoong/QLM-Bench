"""Freeze ten retained physical demos and a separate new360p recording identity."""
import argparse,copy,json,subprocess
from pathlib import Path
from qlm_bench.backends.mujoco.rendition import audit_trace,validate_slot_inputs
from qlm_bench.backends.mujoco.trace import verify_trace,sha,write_json
from qlm_bench.compatibility.dataset_v2.validation import digest
from qlm_bench.compatibility.dataset_v2.pilot_rendition import load_profile

p=argparse.ArgumentParser();p.add_argument('--physical-profile',required=True);p.add_argument('--historical-queue',required=True)
p.add_argument('--output',required=True);p.add_argument('--work-id',default='QLM-DATA-014');a=p.parse_args()
out=Path(a.output)
if out.exists():raise FileExistsError(out)
old=json.loads(Path(a.physical_profile).read_text());queue=json.loads(Path(a.historical_queue).read_text())
repo=Path(__file__).resolve().parents[3]
source={'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip(),
 'source_tree_status':'local_uncommitted_recording_implementation; per-file hashes authoritative',
 'implementation':{str(f.relative_to(repo)):sha(f) for folder in ('src/qlm_bench','scripts/mujoco/synthesis')
                   for f in (repo/folder).rglob('*') if f.suffix in ('.py','.json')},'work_id':a.work_id}
profile={'schema':'qlm-push-pilot-rendition-v1','profile_id':'push-box-360p-pilot-reconstruction-20261014-v1',
 'work_id':a.work_id,'task_id':'push_box','rgb_profile':'dual-rgb-360p-v1','maximum_render_attempts':3,
 'template_root':old['template_root'],'template_sha256':old['template_sha256'],'template_id':old['source']['template_id'],
 'recording_source':source,'python':old['python'],'render_script':str(repo/'scripts/mujoco/synthesis/render_trace.py'),
 'ffmpeg':old['ffmpeg'],'ffprobe':old['ffprobe'],'render_environment':copy.deepcopy(old['render_environment']),
 'historical_physical_profile_sha256':sha(a.physical_profile),'historical_queue_sha256':sha(a.historical_queue),
 'counting':'Same ten physical trajectories, new recording rendition; no new physics/demo count','slots':[]}
for declared in old['slots']:
 uid=declared['episode_uid'];row=queue['slots'][uid];trace=Path(row['trace']);audit=audit_trace(trace);m=verify_trace(trace)[0]
 slot={k:declared[k] for k in ('episode_uid','task_id','difficulty','split')}
 slot.update(trace=str(trace.resolve()),model=m['scene']['model'],model_identity=m['model_identity'],
  physical_source_sha256=audit['source_identity_sha256'],trace_manifest_sha256=audit['manifest_sha256'],
  physical_trajectory_sha256=audit['trajectory_sha256'],quality=audit['quality'],n_actions=m['n_actions'],
  rendition_id=uid+'@dual-rgb-360p-v1-reconstruction-v1',candidate_id=m['scene']['candidate_id'],
  asset_id=m['profile']['asset_id'],appearance_preset=m['scene']['appearance_preset'],seed=m['scene']['seed'])
 profile['slots'].append(slot)
profile['profile_sha256']=digest(profile);write_json(out,profile);profile=load_profile(out)
for s in profile['slots']:validate_slot_inputs(profile,s['episode_uid'])
print(json.dumps({'passed':True,'slots':len(profile['slots']),'actions':sum(s['n_actions'] for s in profile['slots']),
 'profile_sha256':profile['profile_sha256'],'physical_executions':0,'physical_sources_preserved':True}),flush=True)
