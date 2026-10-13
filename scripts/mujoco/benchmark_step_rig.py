"""Bounded counterbalanced performance assessment, immutable old/new resource packs."""
import argparse,gc,hashlib,json,os,subprocess,sys,time
from pathlib import Path
import numpy as np
import psutil
import torch
import mujoco
from qlm_bench.backends.mujoco.physics import MuJoCoPhysics
from qlm_bench.backends.mujoco.render import RenderMirror

VARIANTS={'old':'ethan-rig-a01','new':'step-rig-a01'}
W=Path(__file__).resolve().parents[4]


def write(path,value):Path(path).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
def med(values):return float(np.median(values))
def model_path(task,variant):return W/'assets/mujoco'/f'original-{task}-v1-{VARIANTS[variant]}/scene.xml'
def stats(model):
 return {'ngeom':int(model.ngeom),'nmesh':int(model.nmesh),'mesh_vertices':int(model.nmeshvert),'mesh_triangles':int(model.nmeshface),
  'exposed_model_array_bytes':sum(v.nbytes for n in dir(model) if not n.startswith('_') and isinstance((v:=getattr(model,n)),np.ndarray))}


def render_unit(a,out):
 start=time.perf_counter();physics=MuJoCoPhysics(model_path(a.task,a.variant));mirror=RenderMirror(model_path(a.task,a.variant))
 initialized=time.perf_counter()-start;rss=psutil.Process().memory_info().rss
 try:
  snapshot=physics.snapshot()
  for _ in range(3):mirror.capture(snapshot)
  rows=[]
  for iteration in range(10):
   t=time.perf_counter();capture=mirror.capture(snapshot);full=time.perf_counter()-t
   t=time.perf_counter()
   for name in ('go2_ego','d435i_rgb_task'):mirror.update_scene(name);mirror.renderer.render()
   dual=time.perf_counter()-t
   t=time.perf_counter();mirror.update_scene('observer');mirror.renderer.render();observer=time.perf_counter()-t
   rows.append({'full_three_view_s':full,'dual_render_readback_s':dual,'observer_render_readback_s':observer,**capture['timing_s']})
  assert int(physics.ticks[0])==0
  rgb_std={k:float(v.std()) for k,v in capture['rgb'].items()};assert min(rgb_std.values())>1
  from PIL import Image
  Image.fromarray(capture['rgb']['d435i_rgb_task']).save(out/'task_camera.png')
  result={'passed':True,'phase':'render','task':a.task,'variant':a.variant,'round':a.round,
   'initialization_s':initialized,'RSS_after_init_bytes':rss,'model':stats(physics.model),'rows':rows,
   'dual_render_readback_median_s':med([r['dual_render_readback_s'] for r in rows]),
   'observer_render_readback_median_s':med([r['observer_render_readback_s'] for r in rows]),
   'mirror_refresh_median_s':med([r['mirror_refresh'] for r in rows]),'GL':mirror.gl_identity,
   'RGB_std':rgb_std,'resource_identity':physics.model_identity,'physics_advanced':False,
   'note':'Actual same-state rendering microbenchmark, not50Hz temporal data; nominal cadence cost is an estimate'}
  result['nominal_50Hz_dual_25Hz_observer_render_wall_s_per_sim_s']=50*(result['dual_render_readback_median_s']+result['mirror_refresh_median_s'])+25*result['observer_render_readback_median_s']
  return result
 finally:mirror.close();physics.close()


def physics_unit(a,out):
 start=time.perf_counter();physics=MuJoCoPhysics(model_path(a.task,a.variant),count=a.worlds,backend='mjwarp',device='cuda:0');initialized=time.perf_counter()-start
 try:
  effort=np.zeros((a.worlds,12),np.float32)
  # Compile all early contact kernels before timed reset; no actor or success claim.
  for _ in range(120):physics.step(effort)
  physics.reset();transfer_start=dict(physics.transfer_metrics);samples=[]
  for _ in range(100):
   t=time.perf_counter();physics.step(effort);samples.append(time.perf_counter()-t)
  s=physics.snapshot();np.savez_compressed(out/'terminal.npz',qpos=s['qpos'],qvel=s['qvel'])
  free,total=torch.cuda.mem_get_info()
  return {'passed':True,'phase':'physics','task':a.task,'variant':a.variant,'round':a.round,'worlds':a.worlds,
   'initialization_s':initialized,'steps':100,'wall_s':sum(samples),'step_median_s':med(samples),
   'samples_s':samples,'state_transfer':{k:physics.transfer_metrics[k]-transfer_start[k] for k in transfer_start},
   'resource_identity':physics.model_identity,'model':stats(physics.model),'backend':physics.backend_options,
   'process_RSS_bytes':psutil.Process().memory_info().rss,'device_used_bytes_after':total-free,
   'note':'Direct zero-effort stepping fixture including synchronized host readback; not actor/controller rollout or production batch'}
 finally:physics.close()


def capture_unit(a,out):
 from qlm_bench.backends.mujoco.runtime import MuJoCoRuntime
 from qlm_bench.backends.mujoco.recording import record_engineering
 root=Path(__file__).resolve().parents[2]
 initialized=time.perf_counter();r=MuJoCoRuntime(model_path(a.task,a.variant),W/'checkpoints/rambo/go2/quadruped/model_2000.pt',backend='mjwarp',seed=42)
 init=time.perf_counter()-initialized
 try:
  commit=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
  result=record_engineering(r,out/'capture',ffmpeg=str(W/'cache/tools/bin/ffmpeg'),ffprobe=str(W/'cache/tools/bin/ffprobe'),commands=64,source_commit=commit)
  if not result['passed']:raise ValueError('Actual full capture/validation failed')
  performance=json.loads((out/'capture/performance.json').read_text())
  timing=performance['timing_s'];running=timing['total_s']-timing['packaging_s']-timing['encoder_close_s']
  return {'passed':True,'phase':'capture','task':a.task,'variant':a.variant,'round':a.round,'initialization_s':init,
   'commands':64,'simulation_s':1.28,'result':result,'performance':performance,
   'rollout_capture_s':running,'total_pipeline_s':timing['total_s'],'model':stats(r.physics.model),
   'resource_identity':r.physics.model_identity,'artifact_bytes':sum(p.stat().st_size for p in (out/'capture').rglob('*') if p.is_file()),
   'process_RSS_bytes':psutil.Process().memory_info().rss,'note':'actual bounded engineering capture/Raw/Canonical,not a demonstration; short fixed packaging cost included'}
 finally:r.close()


def main():
 p=argparse.ArgumentParser();p.add_argument('--phase',choices=('render','physics','capture','all'),required=True);p.add_argument('--output',required=True)
 p.add_argument('--unit',action='store_true');p.add_argument('--task',default='push_box');p.add_argument('--variant',choices=('old','new'),default='old');p.add_argument('--round',type=int,default=0);p.add_argument('--worlds',type=int,default=1)
 a=p.parse_args();out=Path(a.output);out.mkdir(parents=True,exist_ok=False);torch.set_num_threads(1);torch.manual_seed(42)
 if a.unit:
  write(out/'attempt.json',{'work_id':'QLM-SIM-008','args':vars(a),'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'model':str(model_path(a.task,a.variant)),'started_unix':time.time()})
  result={'render':render_unit,'physics':physics_unit,'capture':capture_unit}[a.phase](a,out)
  write(out/'result.json',result);print(json.dumps({k:v for k,v in result.items() if k not in ('rows','samples_s','performance','result')}),flush=True);return
 phases=('render','physics','capture') if a.phase=='all' else (a.phase,);results=[]
 for phase in phases:
  if phase=='render':cases=[(task,1,round,variant) for task in ('push_box','press_button','lift_basket') for round in range(2) for variant in (('old','new') if round==0 else ('new','old'))]
  elif phase=='physics':cases=[('push_box',worlds,round,variant) for worlds in (1,2) for round in range(2) for variant in (('old','new') if round==0 else ('new','old'))]
  else:cases=[(task,1,0,variant) for task in ('push_box','lift_basket') for variant in (('old','new') if task=='push_box' else ('new','old'))]
  for task,worlds,round,variant in cases:
   unit=out/f'{phase}-{task}-w{worlds}-r{round}-{variant}'
   with (out/(unit.name+'.log')).open('x') as log:
    cmd=[sys.executable,str(Path(__file__).resolve()),'--phase',phase,'--unit','--task',task,'--variant',variant,'--round',str(round),'--worlds',str(worlds),'--output',str(unit)]
    subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=240)
   r=json.loads((unit/'result.json').read_text());results.append(r)
   print('Completed',phase,task,worlds,round,variant,flush=True)
 write(out/'result.json',{'passed':True,'work_id':'QLM-SIM-008','order':'counterbalanced/fresh process per unit','units':results})

if __name__=='__main__':main()
