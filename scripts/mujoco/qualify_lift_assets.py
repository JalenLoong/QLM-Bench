"""Passive asset diagnostics; initial velocities only, never demonstration success."""
import argparse
import copy
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

import mujoco
import numpy as np

from qlm_bench.backends.mujoco.physics import MuJoCoPhysics
from qlm_bench.backends.mujoco.resources import resource_closure
from qlm_bench.backends.mujoco.trace import sha, write_json


def numbers(values):
    return ' '.join(f'{float(x):.17g}' for x in values)


def prepare(original, candidate_root, output, label):
    original = Path(original)
    target = Path(output)
    target.mkdir(parents=True, exist_ok=False)
    root = ET.parse(original).getroot()
    world = root.find('worldbody')
    profile = json.loads(original.with_suffix('.task.json').read_text())
    parent = resource_closure(original, require_portable=True)
    if label != 'A':
        candidate = Path(candidate_root)/label/'review-only.xml'
        cr = ET.parse(candidate).getroot()
        cm = mujoco.MjModel.from_xml_path(str(candidate))
        body = copy.deepcopy(cr.find('.//body[@name="primary"]'))
        old = world.find('body[@name="primary"]')
        body.set('pos', old.get('pos'))
        ET.SubElement(body, 'inertial', pos=numbers(cm.body('primary').ipos),
            mass=numbers(cm.body('primary').mass), diaginertia=numbers(cm.body('primary').inertia),
            quat=numbers(cm.body('primary').iquat))
        world.remove(old)
        world.append(body)
        for material in cr.find('asset').findall('material'):
            if material.get('name') != 'review_floor':
                root.find('asset').append(copy.deepcopy(material))
        rec = json.loads(candidate.with_name('candidate.json').read_text())
        profile.update(asset_id=rec['asset_id'], candidate_model_sha256=sha(candidate),
            candidate_inertia_derivation=rec['inertia_status'])
    # Keep only assets actually referenced by the unchanged robot/rig and this basket.
    refs = {k:set() for k in ('mesh','material','texture')}
    for g in world.iter('geom'):
        for k in ('mesh','material'):
            if g.get(k):
                refs[k].add(g.get(k))
    assets = root.find('asset')
    for element in assets:
        if element.tag == 'material' and element.get('name') in refs['material']:
            for layer in element.iter():
                if layer.get('texture'):
                    refs['texture'].add(layer.get('texture'))
    for element in list(assets):
        if element.tag in refs and element.get('name') not in refs[element.tag]:
            assets.remove(element)
        elif element.get('file'):
            source = original.parent/element.get('file')
            dest = target/element.get('file')
            dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(source,dest)
    m = mujoco.MjModel.from_xml_path(str(original))
    radius = float(m.geom('FL').size[0])
    probe = ET.SubElement(world,'body',name='diagnostic_probe',pos='-2 3 .4')
    ET.SubElement(probe,'freejoint',name='diagnostic_probe_free')
    mass = .15
    ET.SubElement(probe,'inertial',pos='0 0 0',mass=str(mass),
        diaginertia=numbers([2/5*mass*radius**2]*3))
    ET.SubElement(probe,'geom',name='diagnostic_probe_geom',type='sphere',size=str(radius),
        contype='1',conaffinity='6',friction='1 0 0',rgba='.2 .7 .9 1')
    profile.update(work_id='QLM-SIM-017',kind='passive_asset_diagnostic_not_task_or_demonstration',
        qualification_parent_identity=parent['identity'],asset_label=label,
        applied_force=False,teleport_during_run=False,
        qualification='Only predeclared complete initial states and free-probe velocities; robot unactuated and remote')
    ET.indent(root)
    ET.ElementTree(root).write(target/'scene.xml',encoding='unicode')
    write_json(target/'scene.task.json',profile)
    files={str(p.relative_to(target)):{'sha256':sha(p),'size_bytes':p.stat().st_size}
        for p in sorted(target.rglob('*')) if p.is_file()}
    write_json(target/'resource-manifest.json',{'schema':'qlm-portable-mujoco-resource-v1',
        'entrypoint':'scene.xml','files':files})
    assert resource_closure(original,require_portable=True)['identity']==parent['identity']


def geom_points(model, data, gid):
    rotation = data.geom_xmat[gid].reshape(3,3)
    if model.geom_type[gid] == mujoco.mjtGeom.mjGEOM_MESH:
        mid = model.geom_dataid[gid]
        v = model.mesh_vert[model.mesh_vertadr[mid]:model.mesh_vertadr[mid]+model.mesh_vertnum[mid]]
        return v@rotation.T+data.geom_xpos[gid]
    s = model.geom_size[gid]
    if model.geom_type[gid] == mujoco.mjtGeom.mjGEOM_CAPSULE:
        half = np.abs(rotation[:,2])*s[1]+s[0]
        return data.geom_xpos[gid]+np.array([half*sign for sign in (-1,1)])
    return np.array([[a*s[0],b*s[1],c*s[2]] for a in (-1,1) for b in (-1,1) for c in (-1,1)])@rotation.T+data.geom_xpos[gid]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('original','candidate-root','fixtures','output'):
        p.add_argument('--'+name,required=True)
    p.add_argument('--prepare',action='store_true')
    p.add_argument('--backend',choices=('native','mjwarp'),default='native')
    args = p.parse_args()
    if args.prepare:
        for label in ('A','B','C'):
            prepare(args.original,args.candidate_root,Path(args.fixtures)/label,label)
    out = Path(args.output)
    out.mkdir(parents=True,exist_ok=False)
    write_json(out/'attempt.json',{'work_id':'QLM-SIM-017','backend':args.backend,
        'entry_sha256':sha(__file__),'formal_demonstration':False,'RAMBO_loaded':False,
        'kind':'actual_passive_asset_physics_qualification','args':vars(args)})
    reports = {}
    for label in ('A','B','C'):
        model = Path(args.fixtures)/label/'scene.xml'
        physics = MuJoCoPhysics(model,count=2,backend=args.backend,device='cpu' if args.backend=='native' else 'cuda:0')
        m = physics.model
        profile = json.loads(model.with_suffix('.task.json').read_text())
        primary = int(m.body('primary').id)
        oq = int(m.joint('object_free').qposadr[0])
        pq = int(m.joint('diagnostic_probe_free').qposadr[0])
        pv = int(m.joint('diagnostic_probe_free').dofadr[0])
        pg = int(m.geom('diagnostic_probe_geom').id)
        radius = float(m.geom_size[pg,0])
        initial = physics.snapshot(0)['qpos'].copy()
        gids = [g for g in range(m.ngeom) if m.geom_bodyid[g]==primary and m.geom_group[g]!=3]
        rows = []
        completed = {}
        def bounds(i=0):
            pts = np.concatenate([geom_points(m,physics.data[i],g) for g in gids])
            return pts.min(0),pts.max(0)
        def handle_bounds():
            d = physics.data[0]
            if label=='A':
                pts = np.asarray(profile['handle_vertices_local'])@d.xmat[primary].reshape(3,3).T+d.xpos[primary]
            else:
                pts = np.concatenate([geom_points(m,d,g) for g in gids
                    if (mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_GEOM,g) or '').startswith('handle_')])
            return pts.min(0),pts.max(0)
        def spec(q,v=None):
            # Independent passive scenarios restart the remote unactuated robot.
            # Its prior soft-limit resting values are not valid declared reset inputs.
            # The basket/probe state remains exactly the predeclared scenario state.
            q=q.copy()
            q[:7]=initial[:7]
            q[:3]=[-2,2,.4]
            q[physics.qadr]=initial[physics.qadr]
            return {'schema':'qlm-mujoco-initial-state-v1','model_identity':physics.model_identity,
                'qpos':q.tolist(),'qvel':(np.zeros(m.nv) if v is None else v).tolist()}
        def contacts():
            return [(int(c.geom[0]),int(c.geom[1])) for c in physics.data[0].contact[:physics.data[0].ncon]
                if pg in tuple(c.geom) and primary in tuple(m.geom_bodyid[int(g)] for g in c.geom)]
        try:
            assert m.neq==0 and abs(float(m.body_mass[primary])-.53)<1e-6
            assert np.all(m.body_inertia[primary]>0)
            q = initial.copy();q[:3]=[-2,2,.4];q[oq+2]+=.15
            states={0:spec(q),1:spec(q)}
            write_json(out/(label+'-drop-initial.json'),states)
            physics.reset(initial_states=states)
            z0 = bounds()[0][2]
            for step in range(500):
                physics.step(np.zeros((2,12),np.float32))
                if step%10==9:
                    lo,hi = bounds()
                    rows.append({'mode':'drop_settle','physics_step':step+1,'basket_min_world_z':float(lo[2])})
                assert np.all(physics.data[0].qfrc_applied==0) and np.all(physics.data[0].xfrc_applied==0)
            z1 = bounds()[0][2]
            assert abs(z1)<.005 and z0-z1>.10,'Free fall/rest contact incorrect'
            rest = physics.snapshot(0)
            rest_z = float(rest['qpos'][oq+2])
            completed['free_drop_rest']={'passed':True,'initial_bottom_z_m':float(z0),'final_bottom_z_m':float(z1)}
            # A real free sphere passes through the aperture before it falls onto the rim.
            hmin,hmax = handle_bounds();center=(hmin+hmax)/2
            q=rest['qpos'].copy();q[pq:pq+3]=[hmin[0]-radius-.005,center[1],.5*(hmin[2]+hmax[2])]
            v=np.zeros(m.nv);v[pv]=1.0
            states={0:spec(q,v),1:spec(rest['qpos'])}
            write_json(out/(label+'-aperture-initial.json'),states)
            physics.reset(initial_states=states)
            through_tick=None;hits=0
            for step in range(100):
                physics.step(np.zeros((2,12),np.float32));pairs=contacts()
                hits+=bool(pairs)
                rows.append({'mode':'open_aperture','physics_step':step+1,'probe_world':physics.data[0].xpos[int(m.geom_bodyid[pg])].tolist(),'contact_pairs':pairs})
                x=float(physics.data[0].qpos[pq])
                if x-radius>hmax[0]+.004:
                    through_tick=step+1;break
            assert through_tick is not None and hits==0,'Aperture blocked or probe hit basket before passing'
            completed['real_open_aperture']={'passed':True,'through_physics_tick':through_tick,'probe_object_contact_ticks':hits,'actual_FL_collision_radius_m':radius}
            # Upward momentum transfers by real underside contact, no force applied.
            q=rest['qpos'].copy();q[pq:pq+3]=[center[0],center[1],hmax[2]-2*radius-.04]
            v=np.zeros(m.nv);v[pv+2]=1.4
            states={0:spec(q,v),1:spec(rest['qpos'])}
            write_json(out/(label+'-contact-initial.json'),states)
            physics.reset(initial_states=states);hits=0;peak=rest_z
            for step in range(150):
                physics.step(np.zeros((2,12),np.float32));pairs=contacts();hits+=bool(pairs)
                peak=max(peak,float(physics.data[0].qpos[oq+2]))
                if step%10==9:
                    rows.append({'mode':'upward_real_contact','physics_step':step+1,'basket_root_z_m':float(physics.data[0].qpos[oq+2]),'probe_object_contact_pairs':pairs})
                assert np.all(physics.data[0].qfrc_applied==0) and np.all(physics.data[0].xfrc_applied==0)
            assert hits>0 and peak-rest_z>.0001,'No actual contact-driven basket response'
            completed['true_contact_response']={'passed':True,'probe_contact_ticks':hits,'peak_basket_root_delta_z_m':peak-rest_z,'not_task_success':True}
            other=physics.snapshot(0);physics.reset([1],initial_states={1:spec(rest['qpos'])});after=physics.snapshot(0)
            for key in ('qpos','qvel','physics_step','simulation_time_ns','time'):
                np.testing.assert_array_equal(other[key],after[key])
            snap=physics.snapshot(1);assert snap['physics_step']==0 and snap['simulation_time_ns']==0
            from qlm_bench.backends.mujoco.render import RenderMirror
            mirror=RenderMirror(model,world_id=1,rgb_profile='dual-rgb-360p-v1')
            try:
                frame=mirror.capture(snap)
                assert frame['mirror_physics_advanced'] is False
                np.testing.assert_array_equal(mirror.data.qpos,snap['qpos'])
                np.testing.assert_array_equal(mirror.data.qvel,snap['qvel'])
                assert mirror.data.time==snap['time']
                from PIL import Image
                Image.fromarray(frame['rgb']['d435i_rgb_task']).save(out/(label+'-reset-task.png'))
            finally:mirror.close()
            physics.assert_frozen_model(full=True)
            reports[label]={'passed':True,'gates':completed,'model_identity':physics.model_identity,
                'asset_id':profile['asset_id'],'backend_options':physics.backend_options,
                'full_state_mirror_no_physics_advance':True,'selected_lane_reset_zero_steps':True,
                'other_lane_unchanged':True,'no_applied_force_or_teleport_during_execution':True,
                'formal_task_or_RAMBO_qualification':'separate reference; passive tests do not prove controller performance'}
            write_json(out/(label+'-rows.json'),rows);write_json(out/(label+'-result.json'),reports[label])
            print(args.backend,label,json.dumps(reports[label]),flush=True)
        except BaseException as error:
            write_json(out/'failure.json',{'passed':False,'asset_label':label,'error':str(error),'completed_gates':completed,'previous_assets':reports})
            raise
        finally:physics.close()
    write_json(out/'result.json',{'passed':True,'work_id':'QLM-SIM-017','backend':args.backend,'assets':reports,
        'new_formal_demonstrations':0,'RAMBO_or_WAM_loaded':False})


if __name__=='__main__':
    main()
