"""STEP support actual before/after RGB and protected optical/physical comparison."""
import argparse,json
from pathlib import Path
import numpy as np,mujoco
from PIL import Image,ImageDraw
from scipy.spatial.transform import Rotation
from qlm_bench.backends.mujoco.physics import MuJoCoPhysics
from qlm_bench.backends.mujoco.render import RenderMirror
from compare_camera_rig import camera_state

TASKS=('push_box','press_button','lift_basket')

def protected(a,b):
 fields=['body_mass','body_inertia','body_ipos','body_iquat','body_pos','body_quat','body_parentid','body_jntadr','body_jntnum','body_dofadr','body_dofnum','qpos0','qpos_spring']
 fields.extend(n for n in dir(a) if n.startswith(('jnt_','dof_','actuator_','eq_','tendon_','cam_','light_','mat_')) and n!='dof_length' and isinstance(getattr(a,n),np.ndarray))
 for n in fields:np.testing.assert_array_equal(getattr(a,n),getattr(b,n),err_msg='Protected field:'+n)
 # Geometry membership changes; compare unchanged geometry by stable names.
 count=0
 for i in range(a.ngeom):
  name=mujoco.mj_id2name(a,mujoco.mjtObj.mjOBJ_GEOM,i)
  if name.startswith('original_camera_rig_'):continue
  j=mujoco.mj_name2id(b,mujoco.mjtObj.mjOBJ_GEOM,name)
  if j<0:raise ValueError('Non-rig geometry missing:'+name)
  for field in ('type','pos','quat','size','bodyid','contype','conaffinity','condim','friction','solref','solimp','margin','gap','priority','rgba','dataid','matid'):
   np.testing.assert_array_equal(getattr(a,'geom_'+field)[i],getattr(b,'geom_'+field)[j],err_msg=name+':'+field)
  count+=1
 rig=[i for i in range(b.ngeom) if (mujoco.mj_id2name(b,mujoco.mjtObj.mjOBJ_GEOM,i) or '').startswith('step_support_')]
 if not rig or any(b.geom_contype[i] or b.geom_conaffinity[i] for i in rig):raise ValueError('STEP visual support collision enabled')
 for field in ('extent','meansize','meanmass','meaninertia','center'):np.testing.assert_array_equal(getattr(a.stat,field),getattr(b.stat,field))
 # Direct same-input dynamics check; no actor, frame invention or resource fallback.
 x,y=mujoco.MjData(a),mujoco.MjData(b)
 for iteration in range(100):
  control=np.sin(np.arange(a.nu)+iteration*.05)*.3;x.ctrl[:]=control;y.ctrl[:]=control
  mujoco.mj_step(a,x);mujoco.mj_step(b,y)
 np.testing.assert_array_equal(x.qpos,y.qpos);np.testing.assert_array_equal(x.qvel,y.qvel)
 return {'passed':True,'protected_fields':fields,'unchanged_nonrig_geoms':count,'visual_support_geoms':len(rig),
  'mass_before_kg':float(a.body_mass.sum()),'mass_after_kg':float(b.body_mass.sum()),'robot_inertia_identical':True,
  'support_collision':False,'support_mass_modeled':False,'same_control_Native_100steps_qpos_qvel_identical':True,
  'dof_length_derived_geometry_delta':float(np.max(np.abs(a.dof_length-b.dof_length))),
  'stats_preserved_explicitly':'original extent/meansize/meanmass/meaninertia/center; clipping preserved'}

def main():
 p=argparse.ArgumentParser();p.add_argument('--model-root',required=True);p.add_argument('--output',required=True);a=p.parse_args();out=Path(a.output);out.mkdir(parents=True,exist_ok=False);reports={}
 for task in TASKS:
  current=out/task;current.mkdir();paths=[Path(a.model_root)/f'original-{task}-v1-{suffix}/scene.xml' for suffix in ('ethan-rig-a01','step-rig-a01')]
  owners=[MuJoCoPhysics(path) for path in paths];mirrors=[]
  try:
   mirrors=[RenderMirror(path) for path in paths];invariants=protected(owners[0].model,owners[1].model);states=[]
   for fixture in ('reset','translated_yaw_roll_pitch'):
    for owner in owners:
     owner.reset()
     if fixture!='reset':
      d=owner.data[0];d.qpos[:3]=[.25,-.1,.45];q=Rotation.from_euler('xyz',[8.,-5.,30.],degrees=True).as_quat();d.qpos[3:7]=q[[3,0,1,2]];d.qpos[owner.qadr[0]]=.12;mujoco.mj_forward(owner.model,d)
     owner._host_valid=False;owner._read_cache={}
    captures=[];metrics=[]
    for label,owner,mirror in zip(('before','after'),owners,mirrors):
     q=owner.data[0].qpos.copy();clock=owner.data[0].time;capture=mirror.capture(owner.snapshot(),terminal=True)
     np.testing.assert_array_equal(q,owner.data[0].qpos);assert owner.data[0].time==clock
     captures.append(capture);metrics.append(camera_state(owner.model,owner.data[0]))
     for view,rgb in [*capture['rgb'].items(),('observer',capture['observer_rgb'])]:Image.fromarray(rgb).save(current/f'{fixture}-{label}-{view}.png')
    old,new=metrics;position=float(np.linalg.norm(np.asarray(old['position_world_m'])-new['position_world_m']));angle=float(np.degrees(Rotation.from_matrix(np.asarray(old['world_rotation_matrix']).T@new['world_rotation_matrix']).magnitude()))
    for key in ('mount_position_base_m','mount_rotation_base_matrix','horizontal_fov_deg','vertical_fov_deg','intrinsics_pixels','clipping_m'):np.testing.assert_array_equal(old[key],new[key],err_msg='Frozen camera:'+key)
    if position>1e-12 or angle>1e-10:raise ValueError('World camera pose changed')
    rgb_metrics={};canvas=Image.new('RGB',(1200,500),(20,24,30));draw=ImageDraw.Draw(canvas)
    draw.text((8,5),task+' / '+fixture+' / BEFORE above, STEP support below',fill='white')
    for col,view in enumerate(('go2_ego','d435i_rgb_task','observer')):
     draw.text((col*400+8,24),view,fill='white')
     images=[c['observer_rgb'] if view=='observer' else c['rgb'][view] for c in captures]
     for row,(label,im) in enumerate(zip(('before','after'),images)):
      if im.std()<1:raise ValueError('Uniform invalid RGB:'+view)
      canvas.paste(Image.fromarray(im).resize((400,225)),(col*400,45+row*230))
     delta=np.abs(images[0].astype(np.int16)-images[1].astype(np.int16));rgb_metrics[view]={'MAE_255':float(delta.mean()),'max_abs_255':int(delta.max()),'changed_pixel_fraction':float(np.any(delta!=0,axis=2).mean()),'after_std':float(images[1].std())}
    canvas.save(current/f'{fixture}-comparison.png')
    states.append({'fixture':fixture,'before':old,'after':new,'world_position_delta_m':position,'world_rotation_delta_deg':angle,'FoV_delta_deg':0.,'RGB':rgb_metrics,'physics_advanced_by_render':False})
   reports[task]={'passed':True,'models':[str(path) for path in paths],'invariants':invariants,'states':states,'GL':mirrors[0].gl_identity};(current/'result.json').write_text(json.dumps(reports[task],indent=2)+'\n');print(task,'STEP actual rendering and camera/physics gates pass',flush=True)
  finally:
   for mirror in mirrors:mirror.close()
   for owner in owners:owner.close()
 result={'passed':True,'work_id':'QLM-SIM-007','tasks':reports,'kind':'actual same-state Native OSMesa RGB; no learned-model rollout','optical_calibration':'retained original; STEP lacks optical calibration'}
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
 cards=[]
 for task in TASKS:
  for fixture in ('reset','translated_yaw_roll_pitch'):cards.append(f'<h2>{task} / {fixture}</h2><img src="{task}/{fixture}-comparison.png">')
 (out/'review.html').write_text('<!doctype html><meta charset="utf-8"><title>STEP 支架迁移对比</title><style>body{background:#15191f;color:#eee;font:16px sans-serif;max-width:1250px;margin:24px auto}img{width:100%}h2{font-size:20px}</style><h1>STEP 新支架：MuJoCo 实际画面对比</h1><p>上方：旧程序化支架；下方：STEP 新支架。同一物理状态的实际 OSMesa 渲染。光学相机校准保持原配置；CAD 支架无质量贡献、无碰撞。</p>'+''.join(cards))

if __name__=='__main__':main()
