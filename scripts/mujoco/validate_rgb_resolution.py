"""Read-only same-state 720p/360p OSMesa coverage and render timing audit."""
import argparse,json,time
from pathlib import Path
import numpy as np
from PIL import Image
from qlm_bench.backends.mujoco.trace import verify_trace,SNAPSHOT_ARRAYS
from qlm_bench.backends.mujoco.render import RenderMirror
from qlm_bench.compatibility.rgb_profiles import LEGACY_RGB,RGB_360


def main():
 p=argparse.ArgumentParser();p.add_argument('--trace',required=True);p.add_argument('--model',required=True);p.add_argument('--output',required=True);a=p.parse_args()
 out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
 m,arrays,*_=verify_trace(a.trace);mirrors=[RenderMirror(a.model,world_id=m['world_id'],rgb_profile=k) for k in (LEGACY_RGB,RGB_360)]
 report={'passed':True,'frames':[],'profile_ids':[LEGACY_RGB,RGB_360],'physics_stepped':False,'observer_hw':[720,1280]}
 try:
  for i in [0,m['n_actions']//2,m['n_actions']]:
   snap={k:arrays[k][i].copy() for k in SNAPSHOT_ARRAYS};snap.update(model_identity=m['model_identity'],model_parameters_identity=m['model_parameters_identity'],world_id=m['world_id'],reset_epoch=m['reset_epoch'],physics_step=int(arrays['physics_step'][i]),simulation_time_ns=int(arrays['simulation_time_ns'][i]),time=float(arrays['time'][i]))
   captures=[x.capture(snap,terminal=True) for x in mirrors]
   for camera in ('go2_ego','d435i_rgb_task'):
    frusta=[]
    for j,(mirror,cap) in enumerate(zip(mirrors,captures)):
     mirror.update_scene(camera);gl=mirror.renderer.scene.camera[0]
     # Renderer builds identical camera frusta; pixel resolution changes only viewport.
     frusta.append([getattr(gl,f) for f in ('frustum_near','frustum_far','frustum_bottom','frustum_top','frustum_center','frustum_width')]+list(gl.pos)+list(gl.forward)+list(gl.up))
     Image.fromarray(cap['rgb'][camera]).save(out/f'{i}-{camera}-{720 if j==0 else 360}.png')
    assert np.allclose(frusta[0],frusta[1],rtol=0,atol=1e-7), 'Changed FoV/extrinsics'
    assert captures[1]['rgb'][camera].shape==(360,640,3)
    old_small=np.asarray(Image.fromarray(captures[0]['rgb'][camera]).resize((640,360),Image.Resampling.BILINEAR))
    diff=np.abs(old_small.astype(float)-captures[1]['rgb'][camera].astype(float))
    report['frames'].append({'boundary':i,'camera':camera,'frustum_max_abs_delta':float(np.max(np.abs(np.array(frusta[0])-frusta[1]))),'mean_abs_rgb_delta_0_255':float(diff.mean()),'normalized_coverage_identical':True})
   assert np.array_equal(captures[0]['observer_rgb'],captures[1]['observer_rgb']), 'Observer changed'
  costs=[]
  for mirror in mirrors:
   timings=[]
   for _ in range(5):
    t=time.perf_counter();mirror.capture(snap,terminal=True);timings.append(time.perf_counter()-t)
   costs.append({'profile':mirror.rgb_profile,'median_three_view_s':float(np.median(timings))})
  report['render_timing']=costs
  report['GL']=mirrors[0].gl_identity
 finally:
  for mirror in mirrors:mirror.close()
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)

if __name__=='__main__':main()
