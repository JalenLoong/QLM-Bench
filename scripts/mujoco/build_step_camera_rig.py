"""Portable STEP support visual meshes, preserving original camera/robot physics."""
import argparse,copy,hashlib,json,subprocess,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
import mujoco
from qlm_bench.backends.mujoco.resources import resource_closure

TASKS=('push_box','press_button','lift_basket')

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def dump(p,v):Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def manifest(folder,entry):
 files={str(p.relative_to(folder)):{'sha256':sha(p),'size_bytes':p.stat().st_size} for p in sorted(folder.rglob('*')) if p.is_file() and not (p.parent==folder and p.name in ('resource-manifest.json','attempt.json','result.json'))}
 dump(folder/'resource-manifest.json',{'schema':'qlm-portable-mujoco-resource-v1','entrypoint':entry,'files':files})

def main():
 p=argparse.ArgumentParser()
 for name in ('assembly','mesh','colors','registration','model-root','rig-output','output'):p.add_argument('--'+name,required=True)
 a=p.parse_args();out=Path(a.output);out.mkdir(parents=True,exist_ok=False);core=Path(a.rig_output);core.mkdir(parents=True,exist_ok=False)
 assembly=json.loads((Path(a.assembly)/'result.json').read_text());meshes=json.loads((Path(a.mesh)/'result.json').read_text());colors=json.loads((Path(a.colors)/'result.json').read_text());reg=json.loads((Path(a.registration)/'result.json').read_text())
 if not assembly['passed'] or not meshes['passed'] or not colors['passed']:raise ValueError('Input gate failed')
 if sha(assembly['source'])!=assembly['source_sha256'] or colors['STEP_sha256']!=assembly['source_sha256']:raise ValueError('STEP source mismatch')
 best=reg['chosen'];quality=best['target_to_CAD_distance_m']
 if quality['median']>.001 or best['rotation_correction_deg']>.1:raise ValueError('CAD registration candidate is not sufficiently constrained')
 if min(t['target_to_CAD_distance_m']['median'] for t in reg['candidates'] if t is not best and t!=best)<quality['median']*3:raise ValueError('CAD axis ambiguity')
 T=np.asarray(reg['T_base_from_CAD_world_m']);parts=[];core.joinpath('meshes').mkdir()
 for row in meshes['components']:
  if row['name'] not in ('基础框架最终版1-6','单支架'):continue
  if row['missing_face_indices']:raise ValueError('Missing selected support faces')
  file=Path(a.mesh)/row['mesh']
  if sha(file)!=row['mesh_sha256']:raise ValueError('CAD mesh changed')
  z=np.load(file);v=z['vertices_mm']/1000@T[:3,:3].T+T[:3,3];n=z['normals']@T[:3,:3].T;faces=z['faces'];source_face=z['source_face']
  face_colors=colors['components'][row['name']]['face_RGB']
  if len(face_colors)!=row['source_faces']:raise ValueError('Face/color ordering mismatch')
  groups={}
  for i,f in enumerate(source_face):
   # STEP may omit presentation color. A named neutral material is explicit;
   # no material density, optical calibration or physical load is inferred.
   color=tuple(face_colors[int(f)] or [.65,.65,.65]);groups.setdefault(color,[]).append(i)
  for color,indices in groups.items():
   selected=faces[indices];used,new=np.unique(selected.reshape(-1),return_inverse=True)
   name='step_support_'+str(len(parts));dest=core/'meshes'/(name+'.obj')
   with dest.open('x') as f:
    f.write('# STEP triangulation in Go2 base frame; metres; no decimation\n')
    np.savetxt(f,v[used],fmt='v %.17g %.17g %.17g');np.savetxt(f,n[used],fmt='vn %.17g %.17g %.17g')
    for tri in new.reshape(-1,3)+1:f.write('f '+' '.join(str(int(i))+'//'+str(int(i)) for i in tri)+'\n')
   parts.append({'name':name,'file':'meshes/'+dest.name,'component':row['name'],'color_RGB':list(color),
    'source_color':'STEP' if face_colors[int(source_face[indices[0]])] else 'explicit neutral fallback for absent presentation color',
    'triangles':len(indices),'vertices':len(used),'sha256':sha(dest),
    'bounds_base_m':[v[used].min(0).tolist(),v[used].max(0).tolist()]})
 if sum(x['triangles'] for x in parts)!=sum(x['triangles'] for x in meshes['components'] if x['name'] in ('基础框架最终版1-6','单支架')):raise ValueError('Not all support triangles exported')
 source={'STEP_sha256':assembly['source_sha256'],'STEP_original':assembly['source'],'assembly_components':['基础框架最终版1-6','单支架'],
  'CAD_units':'mm','mesh_units':'m','T_base_from_CAD_world_m':T.tolist(),'registration':reg,
  'registration_scope':'visual body-frame fit; CAD/Isaac robot surfaces are not identical; not device/extrinsic metrology',
  'linear_deflection_mm':.2,'angular_deflection_rad':.15,'mesh_decimation':False,'mass_modeled':False,'collision':False,
  'optical_camera':'original mounted camera retained; STEP supplies no optical center/axis/FoV calibration',
  'STEP_mass_density_material_metadata':'not found','source_face_coverage':'all selected support/frame faces tessellated',
  'zero_area_triangles_removed':sum(x['zero_area_triangles_removed'] for x in meshes['components'] if x['name'] in ('基础框架最终版1-6','单支架'))}
 dump(core/'step-rig.profile.json',{'schema':'qlm-step-camera-rig-v1','work_id':'QLM-SIM-007','source':source,'parts':parts})
 for filename,src in [('assembly.json',Path(a.assembly)/'result.json'),('tessellation.json',Path(a.mesh)/'result.json'),('face-colors.json',Path(a.colors)/'result.json'),('registration-validation.json',Path(a.registration)/'surface-validation.json')]:
  (core/filename).write_bytes(src.read_bytes())
 dump(core/'source-identity.json',source);dump(out/'rig-result.json',{'passed':True,'core':str(core),'parts':parts,'source':source})
 models={}
 for task in TASKS:
  before=Path(a.model_root)/f'original-{task}-v1-ethan-rig-a01';after=Path(a.model_root)/f'original-{task}-v1-step-rig-a01'
  parent=resource_closure(before/'scene.xml',require_portable=True)
  if after.exists():raise FileExistsError(after)
  subprocess.run(['cp','--reflink=auto','-a',str(before),str(after)],check=True)
  for name in ('attempt.json','result.json','resource-manifest.json'): (after/name).unlink(missing_ok=True)
  tree=ET.parse(after/'scene.xml');root=tree.getroot();base=root.find("worldbody/body[@name='base']");asset=root.find('asset')
  previous=mujoco.MjModel.from_xml_path(str(before/'scene.xml'))
  # Visual mesh bounds must not silently change clipping/statistical scale.
  statistic=root.find('statistic')
  if statistic is None:statistic=ET.SubElement(root,'statistic')
  for key in ('extent','meansize','meanmass','meaninertia'):statistic.set(key,format(float(getattr(previous.stat,key)),'.17g'))
  statistic.set('center',' '.join(format(float(v),'.17g') for v in previous.stat.center))
  cameras=[ET.tostring(c) for c in base.findall('camera')];removed=[]
  for geom in list(base.findall('geom')):
   if geom.get('name','').startswith('original_camera_rig_'):removed.append(geom.get('name'));base.remove(geom)
  if len(removed)!=5:raise ValueError('Current rig definition differs')
  for part in parts:
   (after/part['file']).write_bytes((core/part['file']).read_bytes())
   ET.SubElement(asset,'mesh',name=part['name'],file=part['file'],inertia='shell',maxhullvert='64')
   ET.SubElement(base,'geom',name=part['name'],type='mesh',mesh=part['name'],mass='0',rgba=' '.join(map(str,[*part['color_RGB'],1.])),contype='0',conaffinity='0',group='2')
  if [ET.tostring(c) for c in base.findall('camera')]!=cameras:raise ValueError('Optical camera changed')
  ET.indent(tree);tree.write(after/'scene.xml',encoding='unicode')
  profile=json.loads((after/'scene.task.json').read_text());profile['asset_profile']=profile['asset_profile'].replace('-ethan-rig-v1','')+'-step-rig-v1'
  profile['camera_rig']={'version':'STEP-new-support-v1','geometries':len(parts),'source':source,'mass_modeled':False,'collision':False,'source_profile':'step-rig.profile.json'}
  dump(after/'scene.task.json',profile)
  for name in ('step-rig.profile.json','source-identity.json','assembly.json','tessellation.json','face-colors.json','registration-validation.json'):(after/name).write_bytes((core/name).read_bytes())
  historical=after/'source/previous-programmatic-rig';historical.mkdir()
  for name in ('camera-rig-definition.json','camera-rig-derivation.json'):
   if (after/name).exists():(after/name).rename(historical/name)
  dump(after/'attempt.json',{'work_id':'QLM-SIM-007','parent_resource_identity':parent['identity'],'kind':'STEP-support-visual-derivative','builder_sha256':sha(__file__)})
  manifest(after,'scene.xml');model=mujoco.MjModel.from_xml_path(str(after/'scene.xml'));closure=resource_closure(after/'scene.xml',require_portable=True)
  models[task]={'passed':True,'model':str(after/'scene.xml'),'parent_model':str(before/'scene.xml'),'resource_identity':closure['identity'],'parent_resource_identity':parent['identity'],'ngeom':model.ngeom,'ncam':model.ncam}
  dump(after/'result.json',models[task]);print('Compiled STEP support scene',task,flush=True)
 dump(out/'result.json',{'passed':True,'work_id':'QLM-SIM-007','source_STEP_sha256':assembly['source_sha256'],'models':models,'parts':parts})

if __name__=='__main__':main()
