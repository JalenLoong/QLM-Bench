"""Independent CAD rendering-LOD resource packs; protected camera/physics are copied."""
import argparse,copy,json,subprocess,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np,mujoco
from build_step_camera_rig import sha,dump,manifest
from qlm_bench.backends.mujoco.resources import resource_closure

TASKS=('push_box','press_button','lift_basket')

def main():
 p=argparse.ArgumentParser();p.add_argument('--mesh',required=True);p.add_argument('--model-root',required=True);p.add_argument('--rig-output',required=True);p.add_argument('--output',required=True);p.add_argument('--lod-revision',default='a02',choices=('a01','a02'))
 a=p.parse_args();out=Path(a.output);out.mkdir(parents=True,exist_ok=False);core=Path(a.rig_output);core.mkdir(parents=True,exist_ok=False);(core/'meshes').mkdir()
 root=Path(a.model_root);full=root/'ethan-step-camera-rig-v1-a01';master=json.loads((full/'step-rig.profile.json').read_text());tess=json.loads((Path(a.mesh)/'result.json').read_text());colors=json.loads((full/'face-colors.json').read_text());T=np.asarray(master['source']['T_base_from_CAD_world_m']);parts=[]
 if not tess['passed'] or tess['source_STEP_sha256']!=master['source']['STEP_sha256']:raise ValueError('CAD source mismatch')
 if tess['total_triangles']>sum(p['triangles'] for p in master['parts'])*.4:raise ValueError('LOD polygon reduction below60percent')
 for row in tess['components']:
  path=Path(a.mesh)/row['mesh'];assert sha(path)==row['mesh_sha256'];z=np.load(path)
  v=z['vertices_mm']/1000@T[:3,:3].T+T[:3,3];n=z['normals']@T[:3,:3].T;faces=z['faces'];source=z['source_face'];face_colors=colors['components'][row['name']]['face_RGB'];assert len(face_colors)==row['source_faces'] and not row['missing_face_indices']
  groups={}
  for i,f in enumerate(source):groups.setdefault(tuple(face_colors[int(f)] or [.65,.65,.65]),[]).append(i)
  for color,indices in groups.items():
   used,new=np.unique(faces[indices].reshape(-1),return_inverse=True);name='step_support_'+str(len(parts));dest=core/'meshes'/(name+'.obj')
   with dest.open('x') as f:
    f.write('# CAD rendering LOD; all source features retained; same base frame/metres\n');np.savetxt(f,v[used],fmt='v %.17g %.17g %.17g');np.savetxt(f,n[used],fmt='vn %.17g %.17g %.17g')
    for tri in new.reshape(-1,3)+1:f.write('f '+' '.join(str(int(i))+'//'+str(int(i)) for i in tri)+'\n')
   parts.append({'name':name,'file':'meshes/'+dest.name,'component':row['name'],'color_RGB':list(color),'triangles':len(indices),'vertices':len(used),'sha256':sha(dest),'bounds_base_m':[v[used].min(0).tolist(),v[used].max(0).tolist()]})
 profile=copy.deepcopy(master);profile['work_id']='QLM-SIM-009';profile['version']='rendering-lod-v1';profile['parts']=parts
 profile['source'].update(linear_deflection_mm=tess['components'][0]['linear_deflection_mm'],angular_deflection_rad=tess['components'][0]['angular_deflection_rad'],parent_full_profile_sha256=sha(full/'step-rig.profile.json'),lod_method=tess['method'],all_original_CAD_faces_retained=True,acceptance='candidate pending surface/RGB gates')
 profile['source']['protected_source_faces']=tess.get('protected_source_faces',{})
 dump(core/'step-rig.profile.json',profile);dump(core/'tessellation.json',tess)
 for name in ('source-identity.json','face-colors.json','assembly.json','registration-validation.json'):
  (core/name).write_bytes((full/name).read_bytes())
 dump(core/'source-identity.json',profile['source']);models={}
 for task in TASKS:
  before=root/f'original-{task}-v1-step-rig-a01';after=root/f'original-{task}-v1-step-rig-lod-{a.lod_revision}';assert not after.exists();parent=resource_closure(before/'scene.xml',require_portable=True)
  subprocess.run(['cp','--reflink=auto','-a',str(before),str(after)],check=True)
  for name in ('attempt.json','result.json','resource-manifest.json'):(after/name).unlink(missing_ok=True)
  history=after/'source/full-step-rig';history.mkdir()
  for name in ('step-rig.profile.json','source-identity.json','tessellation.json'):(history/name).write_bytes((after/name).read_bytes())
  # Existing geom/actuator/camera attributes remain exactly unchanged. Only mesh bytes differ.
  for part in parts:(after/part['file']).write_bytes((core/part['file']).read_bytes())
  for name in ('step-rig.profile.json','source-identity.json','tessellation.json'):(after/name).write_bytes((core/name).read_bytes())
  task_profile=json.loads((after/'scene.task.json').read_text());task_profile['asset_profile']+='-rendering-lod-v1';task_profile['camera_rig']['version']='STEP-new-support-rendering-LOD-v1';task_profile['camera_rig']['source']=profile['source'];dump(after/'scene.task.json',task_profile)
  dump(after/'attempt.json',{'work_id':'QLM-SIM-009','parent_resource_identity':parent['identity'],'builder_sha256':sha(__file__),'kind':'CAD rendering LOD; no camera/physics/quality settings changed'})
  manifest(after,'scene.xml');model=mujoco.MjModel.from_xml_path(str(after/'scene.xml'));identity=resource_closure(after/'scene.xml',require_portable=True)
  models[task]={'passed':True,'model':str(after/'scene.xml'),'parent':str(before/'scene.xml'),'resource_identity':identity['identity'],'parent_resource_identity':parent['identity'],'model_triangles':int(model.nmeshface),'support_triangles':sum(p['triangles'] for p in parts),'MJCF_xml_bytes_identical_to_full':sha(after/'scene.xml')==sha(before/'scene.xml')}
  assert models[task]['MJCF_xml_bytes_identical_to_full'];dump(after/'result.json',models[task]);print(task,'compiled independent LOD',models[task]['support_triangles'],flush=True)
 dump(out/'result.json',{'passed':True,'work_id':'QLM-SIM-009','full_triangles':sum(p['triangles'] for p in master['parts']),'LOD_triangles':sum(p['triangles'] for p in parts),'reduction_fraction':1-sum(p['triangles'] for p in parts)/sum(p['triangles'] for p in master['parts']),'models':models,'core':str(core)})

if __name__=='__main__':main()
