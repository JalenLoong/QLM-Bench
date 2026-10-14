"""Independent ten-pilot render-only queue; no physical execution callback."""
import argparse,json,os,subprocess
from pathlib import Path
from qlm_bench.backends.mujoco.rendition import RenditionQueue,RecordingIntegrityError
from qlm_bench.backends.mujoco.trace import write_json

p=argparse.ArgumentParser();p.add_argument('--profile',required=True);p.add_argument('--output',required=True)
p.add_argument('--episodes',nargs='+',help='Optional admitted representative subset; membership remains ten')
a=p.parse_args();root=Path(a.output)
with RenditionQueue(root,a.profile) as queue:
 def worker(slot,output,attempt):
  metadata={k:slot[k] for k in ('episode_uid','task_id','difficulty','split')}
  metadata.update(asset_id=slot['asset_id'],appearance_preset=slot['appearance_preset'],environment_seed=slot['seed'],
                  initial_condition_id=slot['candidate_id'],goal_condition_id=slot['candidate_id'])
  meta=root/'render-inputs'/(slot['episode_uid']+'.json');write_json(meta,metadata)
  env=dict(os.environ);env['MUJOCO_GL']='osmesa';env.update(queue.profile['render_environment'])
  command=[queue.profile['python'],'-u',queue.profile['render_script'],'--trace',slot['trace'],'--model',slot['model'],
           '--output',str(output),'--episode-uid',slot['episode_uid'],'--ffmpeg',queue.tools.ffmpeg,'--ffprobe',queue.tools.ffprobe,
           '--formal-pilot','--metadata',str(meta),'--recording-profile',str(Path(a.profile).resolve())]
  log=root/(slot['episode_uid']+f'-render-{attempt:02d}.log')
  with log.open('x') as f:result=subprocess.run(command,env=env,stdout=f,stderr=subprocess.STDOUT)
  if result.returncode:
   text=log.read_text()
   if 'RecordingIntegrityError' in text or 'identity mismatch' in text or 'Frozen ' in text:
    raise RecordingIntegrityError('Fatal source/trace/scene conflict; see '+str(log))
   raise RuntimeError(f'Render worker exit{result.returncode}; see {log}')
 queue.run(worker,uids=a.episodes)
 print(json.dumps({'accepted':queue.accepted(),'physical_executions':queue.state['physical_executions'],
                   'profile_sha256':queue.profile['profile_sha256']}),flush=True)
