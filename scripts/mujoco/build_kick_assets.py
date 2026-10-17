"""Portable approved Kick assets with the retained Go2/controller camera model."""
import argparse,copy,json,os
from pathlib import Path
import xml.etree.ElementTree as ET
import mujoco
import numpy as np
from qlm_bench.backends.mujoco.resources import resource_closure,file_hash


def numbers(v):return ' '.join(f'{float(x):.16g}' for x in v)
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')

def build(parent,review,label,output):
    parent=Path(parent).resolve();review=Path(review);output=Path(output)
    if output.exists():raise FileExistsError(output)
    identity=resource_closure(parent,require_portable=True)
    candidate=json.loads((review/label/'candidate.json').read_text());source=Path(candidate['model'])
    if file_hash(source)!=candidate['model_sha256']:raise ValueError('Approved candidate changed')
    old=mujoco.MjModel.from_xml_path(str(parent));xml=ET.parse(parent).getroot();world=xml.find('worldbody')
    for node in list(world):
        if node.tag=='body' and node.get('name') in ('primary','task_static') or node.get('name','').startswith('original_Goal_'):
            world.remove(node)
    source_xml=ET.parse(source).getroot();source_world=source_xml.find('worldbody')
    ball=copy.deepcopy(source_world.find("body[@name='primary']"));ball.set('pos','.62 .18 .10')
    # Retain the approved .6 coefficient against the unchanged robot floor1.
    ball.find("geom[@name='ball_collision']").set('priority','1')
    goal=copy.deepcopy(source_world.find("body[@name='goal']"));goal.set('pos','1.62 .18 0')
    world.extend([ball,goal])
    marker=copy.deepcopy(source_world.find("geom[@name='goal_line_visual']"));marker.set('pos','1.62 .18 .0008');world.append(marker)
    # Preserve physical clipping/calibration despite different task bounds.
    stat=xml.find('statistic')
    if stat is None:stat=ET.SubElement(xml,'statistic')
    stat.set('extent',str(float(old.stat.extent)));stat.set('center',numbers(old.stat.center))
    assets=xml.find('asset')
    for node in source_xml.find('asset'):
        node=copy.deepcopy(node)
        if node.get('file'):node.set('file',str((source.parent/node.get('file')).resolve()))
        assets.append(node)
    refs={k:set() for k in ('mesh','material','texture')}
    for geom in world.iter('geom'):
        for key in ('mesh','material'):
            if geom.get(key):refs[key].add(geom.get(key))
    for node in assets:
        if node.tag=='material' and node.get('name') in refs['material']:
            if node.get('texture'):refs['texture'].add(node.get('texture'))
            for layer in node.iter():
                if layer.get('texture'):refs['texture'].add(layer.get('texture'))
    output.mkdir(parents=True)
    for node in list(assets):
        if node.tag in refs and node.get('name') not in refs[node.tag]:assets.remove(node);continue
        if not node.get('file'):continue
        f=Path(node.get('file'));src=f if f.is_absolute() else parent.parent/f
        relative=(Path('task_meshes')/(file_hash(src)[:16]+'-'+src.name)) if f.is_absolute() else f
        dest=output/relative;dest.parent.mkdir(parents=True,exist_ok=True)
        if not dest.exists():os.link(src,dest)
        node.set('file',str(relative))
    ET.indent(xml);ET.ElementTree(xml).write(output/'scene.xml',encoding='unicode')
    p=json.loads(parent.with_suffix('.task.json').read_text())
    profile={'schema':'qlm-mujoco-task-candidate-v1','task_id':'kick_ball_to_goal','instruction':'Kick the ball into the goal.',
        'asset_id':candidate['asset_id'],'asset_profile':'kick-goal-'+label.lower()+'-v1','status':'approved_asset_reference_stage_not_pilot',
        'source_asset':candidate,'robot_parent_resource_identity':identity['identity'],
        'ball_radius_m':.1,'mass_kg':.4,'floor_z_m':0.,'success_hold_commands':3,'horizon_s':24.,'force_zero':True,
        'canonical_goal_position':[1.82,.18,.1],
        'goal_geometry':{'front_center_xyz_m':[1.62,.18,0.],'yaw_rad':0.,'width_m':.8,'height_m':.45,'depth_m':.4,'floor_tolerance_m':.003},
        'success':'Measured whole sphere inside physical goal after a valid forward mouth crossing; notfallen; three50Hz ticks. No initial-inside/side/back/above-crossbar score.',
        'progress':'Measured ball center worldX displacement from the reset center, metres; distinct from success',
        'interaction':'Actual FL impulse then free ball motion; sustained body push is a separate quality rejection, not a task predicate change',
        'fall':{'base_height_lt':.1,'projected_gravity_error_gt':.75},
        'observer':copy.deepcopy(p['observer']),'camera_rig':copy.deepcopy(p['camera_rig']),
        'mjwarp_capacity':{'nconmax':1024,'njmax':8192},
        'source_profile':{'task_profile_version':'kick-ball-goal-mujoco-v1','asset_id':candidate['asset_id'],
            'canonical_goal_position':[1.82,.18,.1],'policy_rgb_fps':50,'policy_fps':50,'controller_fps':100,'physics_fps':500,
            'contact':{'role':'diagnostic_only','unavailable':'unknown'},'force_zero':True},
        'work_id':'QLM-SIM-019','physics_qualification':'pending'}
    write(output/'scene.task.json',profile)
    model=mujoco.MjModel.from_xml_path(str(output/'scene.xml'))
    for name in ('cam_pos','cam_quat','cam_fovy'):np.testing.assert_array_equal(getattr(model,name),getattr(old,name))
    robot=xml.find("worldbody/body[@name='base']")
    for node in robot.iter('body'):
        name=node.get('name')
        if not name:continue
        for field in ('mass','inertia','ipos','iquat'):
            np.testing.assert_array_equal(getattr(model.body(name),field),getattr(old.body(name),field))
    for name in ('FL','FR','RL','RR'):
        for key in ('size','friction','condim','contype','conaffinity'):
            np.testing.assert_array_equal(getattr(model.geom(name),key),getattr(old.geom(name),key))
    assert model.neq==0 and model.nq==old.nq and model.nv==old.nv
    np.testing.assert_allclose(model.vis.map.znear*model.stat.extent,old.vis.map.znear*old.stat.extent,atol=0)
    files={str(f.relative_to(output)):{'sha256':file_hash(f),'size_bytes':f.stat().st_size} for f in sorted(output.rglob('*')) if f.is_file()}
    write(output/'resource-manifest.json',{'schema':'qlm-portable-mujoco-resource-v1','entrypoint':'scene.xml','files':files})
    closure=resource_closure(output/'scene.xml',require_portable=True)
    assert resource_closure(parent,require_portable=True)['identity']==identity['identity']
    return {'label':label,'model':str(output/'scene.xml'),'resource_identity':closure['identity'],'robot_camera_solver_unchanged':True,'physics_qualification':'pending'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--parent',required=True);p.add_argument('--review',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    out=Path(a.output);out.mkdir(exist_ok=False,parents=True)
    rows=[build(a.parent,a.review,label,out/label) for label in ('A','B','C')];write(out/'packs.json',rows);print(json.dumps(rows),flush=True)
