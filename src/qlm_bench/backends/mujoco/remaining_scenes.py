"""Pose-only production scenes over the six approved supports; zero physics."""
import copy
import itertools
import json
import math
import os
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

import numpy as np

from .remaining_tasks import binding
from .resources import resource_closure
from .trace import sha, write_json

SUPPORT = {
    'sweep_block_to_zone': ([-.02,-.02,-5,-4,.205], [.02,.02,5,4,.245], [0,0,0,0,.225]),
    'close_fridge_door': ([-.02,-.02,-5,45], [.02,.02,5,55], [0,0,0,50]),
    'close_oven_door': ([-.02,-.02,-5,25], [.02,.02,5,35], [0,0,0,35]),
    'turn_valve': ([-.02,-.02,-5,0], [.02,.02,5,5], [0,0,0,0]),
    'pull_open_drawer': ([-.02,-.02,-5,0], [.02,.02,5,.02], [0,0,0,.008]),
    'open_room_door': ([-.02,-.02,-5], [.02,.02,5], [0,0,0]),
}


def create_scene(task, parameters, destination, background):
    import mujoco
    source = Path(binding(task)['primary_model'])
    dest = Path(destination)
    p = np.asarray(parameters, float)
    lo, hi, _ = map(np.asarray, SUPPORT[task])
    if p.shape != lo.shape or np.any(p < lo) or np.any(p > hi):
        raise ValueError('Candidate outside approved support')
    if dest.exists():
        proof = json.loads((dest/'production-scene.json').read_text())
        if proof['parameters'] != parameters or proof['background'] != background:
            raise ValueError('Existing model belongs to another candidate')
        return dest/'scene.xml'
    dest.parent.mkdir(parents=True, exist_ok=True)
    partial = dest.with_name(dest.name+'.writing')
    if partial.exists():
        # Only incomplete model construction; never a trajectory or accepted data.
        partial.rename(partial.with_name(partial.name+'-interrupted-'+str(__import__('time').time_ns())))
    shutil.copytree(source.parent, partial, copy_function=os.link)
    for name in ('scene.xml','asset-only.xml','scene.task.json','resource-manifest.json'):
        (partial/name).unlink()
    tree = ET.parse(source)
    asset = ET.parse(source.parent/'asset-only.xml')
    world = tree.getroot().find('worldbody')
    profile = json.loads(source.with_suffix('.task.json').read_text())
    old = mujoco.MjModel.from_xml_path(str(source)); data = mujoco.MjData(old)
    mujoco.mj_forward(old, data)
    origin = data.xpos[old.body('primary').id].copy()
    angle = math.radians(p[2]); c, s = math.cos(angle), math.sin(angle)
    rot = np.array([[c,-s,0],[s,c,0],[0,0,1.]])
    turn = np.array([math.cos(angle/2),0,0,math.sin(angle/2)])
    delta = np.array([p[0],p[1],0.])
    def pose(v): return origin + rot @ (np.asarray(v)-origin) + delta
    def vector(node,key,value): node.set(key,' '.join(f'{v:.17g}' for v in value))
    if task == 'sweep_block_to_zone':
        block = world.find("body[@name='primary']")
        vector(block,'pos',origin+delta); vector(block,'quat',turn)
        direction = math.radians(p[3]); toward = np.array([math.sin(direction),-math.cos(direction)])
        center = (origin+delta)[:2]+p[4]*toward
        vector(world.find("body[@name='sw_zone']"),'pos',[*center,0.])
        profile.update(initial_center_y=float(origin[1]+delta[1]),initial_center_xy=(origin+delta)[:2].tolist(),
                       sweep_direction_xy=toward.tolist(),goal_x=[float(center[0]-.13),float(center[0]+.13)],
                       goal_y=[float(center[1]-.10),float(center[1]+.10)],canonical_goal_position=[*center.tolist(),0.])
    else:
        for node in asset.getroot().find('worldbody'):
            target=world.find(f"{node.tag}[@name='{node.get('name')}']")
            vector(target,'pos',pose(np.fromstring(target.get('pos','0 0 0'),sep=' ')))
            q=np.zeros(4);mujoco.mju_mulQuat(q,turn,np.fromstring(target.get('quat','1 0 0 0'),sep=' '))
            vector(target,'quat',q)
        profile['canonical_goal_position']=pose(profile['canonical_goal_position']).tolist()
        if task != 'open_room_door':
            value = -math.radians(p[3]) if task.startswith('close_') else math.radians(p[3]) if task=='turn_valve' else p[3]
            profile['initial_joint_positions'][profile['primary_joint']]=float(value)
    for node in asset.getroot().find('worldbody'):
        target=world.find(f"{node.tag}[@name='{node.get('name')}']")
        if target is not None:
            for key in ('pos','quat'):
                if target.get(key) is not None: node.set(key,target.get(key))
    if background == 'ap_01':
        assets=tree.getroot().find('asset')
        ET.SubElement(assets,'texture',name='qlm_ap01_floor_texture',type='2d',builtin='checker',width='256',height='256',rgb1='.48 .42 .32',rgb2='.40 .34 .25')
        ET.SubElement(assets,'material',name='qlm_ap01_floor_material',texture='qlm_ap01_floor_texture',texrepeat='2 2',texuniform='true',reflectance='0',specular='0',shininess='0')
        floor=world.find("geom[@name='floor']");floor.set('material','qlm_ap01_floor_material');floor.set('rgba','1 1 1 1')
    elif background != 'ap_00': raise ValueError('Only approved two backgrounds')
    profile.update(appearance_preset=background,production_parameters=p.tolist(),
                   production_source_model=str(source),production_work_id='QLM-DATA-040')
    tree.write(partial/'scene.xml',encoding='unicode');asset.write(partial/'asset-only.xml',encoding='unicode')
    write_json(partial/'scene.task.json',profile)
    new=mujoco.MjModel.from_xml_path(str(partial/'scene.xml'));nd=mujoco.MjData(new);mujoco.mj_forward(new,nd)
    protected=('body_mass','body_inertia','geom_size','geom_friction','geom_solref','geom_solimp','geom_condim',
               'jnt_range','jnt_stiffness','dof_damping','dof_frictionloss','cam_pos','cam_quat','cam_fovy',
               'actuator_gainprm','actuator_biasprm','eq_data')
    for key in protected:np.testing.assert_array_equal(getattr(old,key),getattr(new,key))
    for key in ('body_ipos','body_iquat'):
        np.testing.assert_allclose(getattr(old,key)[old.body_mass>0],getattr(new,key)[old.body_mass>0],rtol=0,atol=1e-12)
    for key in ('gravity','timestep','iterations','ls_iterations','tolerance'):
        np.testing.assert_array_equal(getattr(old.opt,key),getattr(new.opt,key))
    robot={old.body('base').id}
    for body in range(old.nbody):
        if int(old.body_parentid[body]) in robot:robot.add(body)
    for body in robot:
        for key in ('body_pos','body_quat'):np.testing.assert_array_equal(getattr(old,key)[body],getattr(new,key)[body])
    for key in ('cam_xpos','cam_xmat'):np.testing.assert_allclose(getattr(data,key),getattr(nd,key),rtol=0,atol=1e-12)
    proof=dict(task_id=task,parameters=parameters,background=background,source_model=str(source),
               source_identity=resource_closure(source)['identity'],protected_arrays=list(protected),physics_steps=0,
               robot_camera_unchanged=True,work_id='QLM-DATA-040')
    write_json(partial/'production-scene.json',proof)
    write_json(partial/'resource-manifest.json',dict(schema='qlm-portable-mujoco-resource-v1',entrypoint='scene.xml',
        files={str(f.relative_to(partial)):dict(sha256=sha(f),size_bytes=f.stat().st_size) for f in partial.rglob('*') if f.is_file() and f.name!='resource-manifest.json'}))
    resource_closure(partial/'scene.xml',require_portable=True);partial.rename(dest)
    return dest/'scene.xml'


def initial_state(task, model_path):
    import mujoco
    b=binding(task);ref=Path(b['reference']);snap=ref/'review50/snapshots.npz'
    if snap.exists():
        with np.load(snap) as z:state={k:z[k][0].tolist() for k in ('qpos','qvel')}
    else:state=copy.deepcopy(json.loads((ref/'trace/manifest.json').read_text())['scene']['initial_state'])
    model=mujoco.MjModel.from_xml_path(str(model_path));profile=json.loads(Path(model_path).with_suffix('.task.json').read_text())
    if task=='sweep_block_to_zone':state['qpos'][19:]=model.qpos0[19:].tolist()
    else:
        for name,value in profile['initial_joint_positions'].items():state['qpos'][int(model.joint(name).qposadr[0])]=value
    state.update(schema='qlm-mujoco-initial-state-v1',model_identity=resource_closure(model_path)['identity'])
    return state
