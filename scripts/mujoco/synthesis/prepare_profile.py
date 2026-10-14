"""Freeze ten pilot slots and three small appearance presets from retained LOD only."""
import argparse,copy,hashlib,json,math,os,shutil,subprocess,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
from qlm_bench.backends.mujoco.trace import sha,write_json
from qlm_bench.backends.mujoco.resources import resource_closure

p=argparse.ArgumentParser();p.add_argument('--source-model',required=True);p.add_argument('--template',required=True)
p.add_argument('--resources',required=True);p.add_argument('--output',required=True);p.add_argument('--workspace',required=True)
a=p.parse_args();w=Path(a.workspace);source=Path(a.source_model).parent;destination=Path(a.resources)
if destination.exists():raise FileExistsError(destination)
model_set=[];template=json.loads((Path(a.template)/'template.json').read_text());original=template['source_scene']
original_identity=resource_closure(a.source_model)
for i,color in enumerate(['.35 .4 .45 1','.37 .4 .43 1','.33 .39 .46 1']):
 root=destination/f'ap_0{i}';shutil.copytree(source,root,copy_function=os.link)
 # Break links only for newly written derived files. Source assets are immutable.
 for name in ['scene.xml','scene.task.json','resource-manifest.json']:(root/name).unlink()
 tree=ET.parse(source/'scene.xml');tree.getroot().find("worldbody/geom[@name='floor']").set('rgba',color)
 tree.write(root/'scene.xml',encoding='unicode')
 task=json.loads((source/'scene.task.json').read_text());task.update(appearance_preset=f'ap_0{i}',
  synthesis_profile='push-box-automated-pilot-v1',source_resource_identity=original_identity['identity'])
 write_json(root/'scene.task.json',task)
 manifest=json.loads((source/'resource-manifest.json').read_text())
 for name in ['scene.xml','scene.task.json']:
  manifest['files'][name]={'sha256':sha(root/name),'size_bytes':(root/name).stat().st_size}
 write_json(root/'resource-manifest.json',manifest);identity=resource_closure(root/'scene.xml',require_portable=True)['identity']
 model_set.append({'model':str(root/'scene.xml'),'identity':identity,'preset':f'ap_0{i}'})
# Object freejoint is last in the retained Go2+Box model. Resolve by name from MuJoCo.
import mujoco
m=mujoco.MjModel.from_xml_path(a.source_model);j=mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_JOINT,'object_free');adr=int(m.jnt_qposadr[j])
bins=[(0,0,0,0,0),(0,0,0,0,0),(-.035,-.016,-.025,-.025,-.015),(-.025,.016,.025,-.015,.015),
 (.035,-.016,.02,.025,-.015),(.025,.016,-.02,.015,.015),(-.018,-.012,.015,.025,.015),
 (-.018,.012,-.015,-.025,-.015),(.018,-.012,-.025,-.025,.015),(.018,.012,.025,.025,-.015)]
slots=[]
for i,(dx,dy,yaw,gx,gy) in enumerate(bins):
 uid=f'push_box__ep{i+1:04}';candidates=[]
 for attempt in range(5):
  preset=0 if i<2 else 1+i%2;resource=model_set[preset]
  scene=copy.deepcopy(original);q=np.array(scene['initial_state']['qpos']);q[adr:adr+2]+=[dx,dy]
  # Prespecified retry jitter stays in the same geometry bin, never collapses to nominal.
  if i>=2 and attempt:q[adr]+=(attempt%2*2-1)*.0015;q[adr+1]+=(attempt//2%2*2-1)*.001
  q[adr+3:adr+7]=[math.cos(yaw/2),0,0,math.sin(yaw/2)]
  scene.update(candidate_id=f'{uid}__a{attempt+1:02}',seed=1001+i*31+attempt,model=resource['model'],
   appearance_preset=resource['preset'],difficulty='clean' if i<2 else 'randomized',
   goal_x=[v+gx for v in original['goal_x']],goal_y=[v+gy for v in original['goal_y']])
  if i==0:scene['seed']=42+attempt
  scene['canonical_goal_position']=[np.mean(scene['goal_x']),np.mean(scene['goal_y']),0.]
  # Freeze the visible contact-free goal outline with the numerical goal.
  if i>=2:
   goal_root=destination/f'slot-{i+1:04}'
   if attempt==0:
    shutil.copytree(Path(resource['model']).parent,goal_root,copy_function=os.link)
    for name in ['scene.xml','scene.task.json','resource-manifest.json']:(goal_root/name).unlink()
    xml=ET.parse(resource['model'])
    for geom in xml.getroot().iter('geom'):
     if geom.get('name','').startswith('original_Goal_'):
      assert geom.get('contype')=='0' and geom.get('conaffinity')=='0'
      pos=np.array([float(v) for v in geom.get('pos').split()]);pos[:2]+=[gx,gy]
      geom.set('pos',' '.join(map(str,pos)))
    xml.write(goal_root/'scene.xml',encoding='unicode')
    task=json.loads(Path(resource['model']).with_suffix('.task.json').read_text())
    task.update(goal_x=scene['goal_x'],goal_y=scene['goal_y'],canonical_goal_position=scene['canonical_goal_position'])
    task['source_profile'].update(goal_x=scene['goal_x'],goal_y=scene['goal_y'])
    write_json(goal_root/'scene.task.json',task)
    declared=json.loads((Path(resource['model']).parent/'resource-manifest.json').read_text())
    for name in ['scene.xml','scene.task.json']:
     declared['files'][name]={'sha256':sha(goal_root/name),'size_bytes':(goal_root/name).stat().st_size}
    write_json(goal_root/'resource-manifest.json',declared)
   scene['model']=str(goal_root/'scene.xml')
   scene['initial_state']['model_identity']=resource_closure(goal_root/'scene.xml',require_portable=True)['identity']

  scene['initial_state'].update(model_identity=resource_closure(scene['model'],require_portable=True)['identity'],qpos=q.tolist())
  scene['variation']={'object_dx_m':dx,'object_dy_m':dy,'object_yaw_rad':yaw,'goal_dx_m':gx,'goal_dy_m':gy}
  candidates.append(scene)
 slots.append({'episode_uid':uid,'task_id':'push_box','difficulty':'clean' if i<2 else 'randomized','split':'train','candidates':candidates})
repo=Path(__file__).resolve().parents[3]
implementation={str(f.relative_to(repo)):sha(f) for directory in ('src/qlm_bench','scripts/mujoco/synthesis')
 for f in (repo/directory).rglob('*') if f.suffix in ('.py','.json')}
profile={'schema':'qlm-automated-push-pilot-v1','task_id':'push_box','work_id':'QLM-DATA-011','slots':slots,
 'template_root':str(Path(a.template).resolve()),'template_sha256':sha(Path(a.template)/'template.json'),
 'resources':model_set,'source_resource':original_identity,'horizon_s':24.,'bounds':template['bounds'],
 'python':str(w/'envs/qlm-mujoco-py312-v1/bin/python'),'render_script':str(repo/'scripts/mujoco/synthesis/render_trace.py'),
 'ffmpeg':str(w/'cache/tools/bin/ffmpeg'),'ffprobe':str(w/'cache/tools/bin/ffprobe'),
 'render_environment':{'LD_LIBRARY_PATH':str(w/'assets/mujoco/p0-v1/osmesa/root/usr/lib/x86_64-linux-gnu'),
 'MESA_SHADER_CACHE_DIR':str(w/'cache/mesa'),'OMP_NUM_THREADS':'4'},
 'source':{'source_commit':subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip(),
 'implementation':implementation,'template_id':template['template_id'],'template_sha256':sha(Path(a.template)/'template.json'),
 'work_id':'QLM-DATA-011'},'quotas':{'clean':2,'randomized':8,'train':10},'batch_GPT_calls':0,
 'physics_candidate_limits':{'per_slot':5,'total':30,'consecutive_failure':10},'render_retries':2}
profile['profile_sha256']=hashlib.sha256(json.dumps(profile,sort_keys=True,separators=(',',':')).encode()).hexdigest()
write_json(a.output,profile);print('Frozen ten slots,three appearance presets',profile['profile_sha256'])
