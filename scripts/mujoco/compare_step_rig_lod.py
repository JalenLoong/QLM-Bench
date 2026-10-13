"""Three actual Observer views plus protected-camera/physics/LOD visual gates."""
import argparse,json
from pathlib import Path
import numpy as np,mujoco
from PIL import Image,ImageDraw
from scipy.ndimage import binary_dilation
from scipy.spatial.transform import Rotation
from qlm_bench.backends.mujoco.physics import MuJoCoPhysics
from qlm_bench.backends.mujoco.render import RenderMirror
from compare_camera_rig import camera_state

VARIANTS=[('original','a03'),('STEP_full','step-rig-a01'),('STEP_LOD','step-rig-lod-a02')]
TASKS=('push_box','press_button','lift_basket')

def invariant(a,b):
 names=['body_mass','body_inertia','body_ipos','body_iquat','body_pos','body_quat','body_parentid','qpos0']
 names+=[n for n in dir(a) if n.startswith(('jnt_','dof_','actuator_','cam_','light_','mat_')) and n!='dof_length' and isinstance(getattr(a,n),np.ndarray)]
 for n in names:np.testing.assert_array_equal(getattr(a,n),getattr(b,n),err_msg=n)
 for section in ('global_','quality','headlight','map','scale','rgba'):
  x=getattr(a.vis,section);y=getattr(b.vis,section)
  for n in dir(x):
   if n.startswith('_'):continue
   p,q=getattr(x,n),getattr(y,n)
   if isinstance(p,(np.ndarray,int,float)):np.testing.assert_array_equal(p,q,err_msg='vis.'+section+'.'+n)
 for key in ('extent','meansize','meaninertia','meanmass','center'):np.testing.assert_array_equal(getattr(a.stat,key),getattr(b.stat,key))
 for i in range(a.ngeom):
  name=mujoco.mj_id2name(a,mujoco.mjtObj.mjOBJ_GEOM,i)
  if name.startswith('step_support_'):continue
  j=mujoco.mj_name2id(b,mujoco.mjtObj.mjOBJ_GEOM,name)
  for attr in ('type','pos','quat','size','bodyid','contype','conaffinity','friction','condim','rgba','matid'):
   np.testing.assert_array_equal(getattr(a,'geom_'+attr)[i],getattr(b,'geom_'+attr)[j],err_msg=name+':'+attr)
 x,y=mujoco.MjData(a),mujoco.MjData(b)
 for k in range(100):
  x.ctrl[:]=y.ctrl[:]=np.sin(np.arange(a.nu)+k*.05)*.3;mujoco.mj_step(a,x);mujoco.mj_step(b,y)
 np.testing.assert_array_equal(x.qpos,y.qpos);np.testing.assert_array_equal(x.qvel,y.qvel)
 return {'passed':True,'camera_quality_mass_inertia_collision_light_identical':True,'same_control_Native100step_identical':True,'dof_length_geometry_delta':float(np.max(np.abs(a.dof_length-b.dof_length)))}

def observer_mask(mirror):
 mirror.geometry_masks() # Initialize separate audit-only no-MSAA segmentation context.
 r=mirror.audit_renderer;r.enable_segmentation_rendering()
 try:
  r.update_scene(mirror.data,camera='observer')
  for camera in r.scene.camera:
   ratio=mirror.observer_clip[0]/camera.frustum_near
   for attr in ('frustum_bottom','frustum_top','frustum_center','frustum_width'):setattr(camera,attr,getattr(camera,attr)*ratio)
   camera.frustum_near,camera.frustum_far=mirror.observer_clip
  ids=r.render().copy();geoms=[i for i in range(mirror.model.ngeom) if (mujoco.mj_id2name(mirror.model,mujoco.mjtObj.mjOBJ_GEOM,i) or '').startswith(('original_camera_rig_','step_support_'))]
  return np.isin(ids[:,:,0],geoms)&(ids[:,:,1]==int(mujoco.mjtObj.mjOBJ_GEOM))
 finally:r.disable_segmentation_rendering()


def main():
 p=argparse.ArgumentParser();p.add_argument('--model-root',required=True);p.add_argument('--output',required=True);a=p.parse_args();out=Path(a.output);out.mkdir(parents=True,exist_ok=False);reports={};cards=[]
 for task in TASKS:
  folder=out/task;folder.mkdir();paths=[Path(a.model_root)/f'original-{task}-v1-{suffix}/scene.xml' for _,suffix in VARIANTS]
  owners=[MuJoCoPhysics(path) for path in paths];mirrors=[]
  try:
   mirrors=[RenderMirror(path) for path in paths];physics=invariant(owners[1].model,owners[2].model);states=[]
   for fixture in ('reset','translated_yaw_roll_pitch'):
    captures=[];camera=[];masks=[]
    for (label,_),owner,mirror in zip(VARIANTS,owners,mirrors):
     owner.reset()
     if fixture!='reset':
      d=owner.data[0];d.qpos[:3]=[.25,-.1,.45];q=Rotation.from_euler('xyz',[8.,-5.,30.],degrees=True).as_quat();d.qpos[3:7]=q[[3,0,1,2]];d.qpos[owner.qadr[0]]=.12;mujoco.mj_forward(owner.model,d)
     owner._host_valid=False;owner._read_cache={};before=owner.data[0].qpos.copy();clock=owner.data[0].time
     c=mirror.capture(owner.snapshot(),terminal=True);captures.append(c);camera.append(camera_state(owner.model,owner.data[0]));mask=observer_mask(mirror);masks.append(mask)
     np.testing.assert_array_equal(before,owner.data[0].qpos);assert owner.data[0].time==clock
     for view,rgb in [('observer',c['observer_rgb']),*c['rgb'].items()]:Image.fromarray(rgb).save(folder/f'{fixture}-{label}-{view}.png')
     np.save(folder/f'{fixture}-{label}-rig-mask.npy',mask)
    for pose in camera[1:]:
     for field in ('mount_position_base_m','mount_rotation_base_matrix','horizontal_fov_deg','vertical_fov_deg','position_world_m','world_rotation_matrix','intrinsics_pixels','clipping_m'):np.testing.assert_allclose(camera[0][field],pose[field],atol=1e-12,rtol=0)
    intersection=(masks[1]&masks[2]).sum();union=(masks[1]|masks[2]).sum();iou=float(intersection/union);assert iou>=.995,'Observer outline IoU gate failed'
    roi=binary_dilation(masks[1]|masks[2],iterations=4);delta=np.abs(captures[1]['observer_rgb'].astype(np.int16)-captures[2]['observer_rgb'].astype(np.int16));roi_mae=float(delta[roi].mean());assert roi_mae<=2.,'Observer ROI color gate failed'
    rgb={}
    for name in ('go2_ego','d435i_rgb_task'):
     d=np.abs(captures[1]['rgb'][name].astype(np.int16)-captures[2]['rgb'][name].astype(np.int16));rgb[name]={'MAE_255':float(d.mean()),'max_abs_255':int(d.max())};assert d.mean()<=.1 and d.max()<=2,'Policy RGB gate failed'
    # Actual original Observer, same full resolution in each panel.
    canvas=Image.new('RGB',(3840,760),(20,24,30));draw=ImageDraw.Draw(canvas)
    for i,(label,_) in enumerate(VARIANTS):draw.text((i*1280+12,8),label+' / '+task+' / '+fixture,fill='white');canvas.paste(Image.fromarray(captures[i]['observer_rgb']),(i*1280,40))
    canvas.save(folder/f'{fixture}-observer-three.png')
    ys,xs=np.nonzero(masks[0]|masks[1]|masks[2]);bounds=(max(0,int(xs.min())-14),max(0,int(ys.min())-14),min(1280,int(xs.max())+15),min(720,int(ys.max())+15))
    # Same pixel ROI enlarged; no camera/FoV change and no image-generation edits.
    crops=[Image.fromarray(c['observer_rgb']).crop(bounds) for c in captures];ratio=min(560/crops[0].width,420/crops[0].height);size=(round(crops[0].width*ratio),round(crops[0].height*ratio));detail=Image.new('RGB',(1680,size[1]+40),(20,24,30));draw=ImageDraw.Draw(detail)
    for i,((label,_),crop) in enumerate(zip(VARIANTS,crops)):draw.text((i*560+12,8),label+' / same Observer ROI magnified',fill='white');detail.paste(crop.resize(size),(i*560,40))
    detail.save(folder/f'{fixture}-observer-detail-three.png')
    states.append({'fixture':fixture,'cameras':dict(zip([v[0] for v in VARIANTS],camera)),'Observer_LOD_vs_full_rig_silhouette_IoU':iou,'Observer_LOD_vs_full_ROI_MAE_255':roi_mae,'policy_RGB_LOD_vs_full':rgb,'Observer_crop_pixels':bounds,'render_advanced_physics':False})
    cards.append(f'<h2>{task} / {fixture}</h2><p>原 Observer 的相同像素区域放大，不改变 FoV。</p><img src="{task}/{fixture}-observer-detail-three.png"><p>原始 Observer 全画面（各1280×720）：</p><img src="{task}/{fixture}-observer-three.png">')
   reports[task]={'passed':True,'models':[str(x) for x in paths],'physics_invariants':physics,'states':states,'GL':mirrors[0].gl_identity};print(task,'three-way Observer/LOD gates passed',flush=True)
  finally:
   for m in mirrors:m.close()
   for o in owners:o.close()
 result={'passed':True,'work_id':'QLM-SIM-009','variants':VARIANTS,'gates':{'Observer_silhouette_IoU_min':.995,'Observer_ROI_MAE_max_255':2.,'policy_RGB_MAE_max_255':.1,'policy_RGB_max_abs_255':2},'tasks':reports}
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
 (out/'review.html').write_text('<!doctype html><meta charset="utf-8"><title>三版支架 Observer 对比</title><style>body{background:#15191f;color:#eee;font:16px sans-serif;max-width:1700px;margin:24px auto}img{max-width:100%}h2{font-size:20px}</style><h1>MuJoCo Observer：最初支架 / 完整 STEP 新支架 / rendering LOD</h1><p>从左至右分别为三版。同一物理状态、同一原 Observer camera；图片来自实际 Native OSMesa 渲染。STEP 原文件通过完整精度 mesh 显示，原 STEP 保留。下面放大图仅裁剪同一原始 RGB 区域。</p>'+''.join(cards))

if __name__=='__main__':main()
