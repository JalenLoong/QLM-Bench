"""Predeclared passive momentum/contact diagnostics, never RAMBO demonstrations."""
import argparse,copy,json,os
from pathlib import Path
import xml.etree.ElementTree as ET
import mujoco
import numpy as np
from qlm_bench.backends.mujoco.physics import MuJoCoPhysics
from qlm_bench.backends.mujoco.trace import sha,write_json
from qlm_bench.backends.mujoco.kick_goal import GoalEntry


def fixture(source,target):
    source=Path(source);target=Path(target);target.mkdir(parents=True,exist_ok=False)
    for folder in ('meshes','textures','task_meshes'):
        for src in (source.parent/folder).rglob('*') if (source.parent/folder).exists() else []:
            if src.is_file():dst=target/src.relative_to(source.parent);dst.parent.mkdir(parents=True,exist_ok=True);os.link(src,dst)
    xml=ET.parse(source).getroot();r=float(mujoco.MjModel.from_xml_path(str(source)).geom('FL').size[0])
    b=ET.SubElement(xml.find('worldbody'),'body',name='diagnostic_probe',pos='-3 3 .2')
    ET.SubElement(b,'freejoint',name='diagnostic_probe_free');ET.SubElement(b,'inertial',pos='0 0 0',mass='.15',diaginertia=' '.join(map(str,[.4*.15*r*r]*3)))
    ET.SubElement(b,'geom',name='diagnostic_probe_geom',type='sphere',size=str(r),contype='1',conaffinity='7',rgba='.2 .7 .9 1')
    ET.indent(xml);ET.ElementTree(xml).write(target/'scene.xml',encoding='unicode')
    profile=json.loads(source.with_suffix('.task.json').read_text());profile['qualification_only']=True;write_json(target/'scene.task.json',profile)
    write_json(target/'resource-manifest.json',{'schema':'qlm-portable-mujoco-resource-v1','entrypoint':'scene.xml','files':{str(p.relative_to(target)):{'sha256':sha(p),'size_bytes':p.stat().st_size} for p in target.rglob('*') if p.is_file()}})


def main():
    p=argparse.ArgumentParser();p.add_argument('--packs',required=True);p.add_argument('--fixtures',required=True);p.add_argument('--output',required=True);p.add_argument('--backend',choices=('native','mjwarp'),required=True);p.add_argument('--prepare',action='store_true');a=p.parse_args()
    root=Path(a.output);root.mkdir(parents=True,exist_ok=False)
    write_json(root/'attempt.json',{'kind':'passive asset qualification, not task demonstration','backend':a.backend,'entry_sha256':sha(__file__),'work_id':'QLM-SIM-019','initial_momentum_only':True,'external_force_applied':False,'RAMBO_loaded':False})
    results={}
    for label in ('A','B','C'):
        path=Path(a.fixtures)/label/'scene.xml'
        if a.prepare:fixture(Path(a.packs)/label/'scene.xml',path.parent)
        physics=MuJoCoPhysics(path,count=2,backend=a.backend,device='cpu' if a.backend=='native' else 'cuda:0')
        m=physics.model;profile=json.loads(path.with_suffix('.task.json').read_text());oq=int(m.joint('object_free').qposadr[0]);ov=int(m.joint('object_free').dofadr[0]);pq=int(m.joint('diagnostic_probe_free').qposadr[0]);pv=int(m.joint('diagnostic_probe_free').dofadr[0]);radius=float(m.geom('FL').size[0]);initial=physics.snapshot()['qpos'].copy();start=np.array([.62,.18,.10]);goal=np.array([1.62,.18,0.]);records={}
        def state(pos,vel=(0.,0.,0.),spin=(0.,0.,0.),probe=None,probe_velocity=None):
            q=initial.copy();v=np.zeros(m.nv);q[:3]=[-2,2,.4];q[oq:oq+3]=pos;v[ov:ov+3]=vel;v[ov+3:ov+6]=spin
            if probe is not None:q[pq:pq+3]=probe;v[pv:pv+3]=probe_velocity
            return {'schema':'qlm-mujoco-initial-state-v1','model_identity':physics.model_identity,'qpos':q.tolist(),'qvel':v.tolist()}
        scenarios=[('drop',state(start+[0,0,.15]),400),('rolling_into_goal',state(start,(1.,0.,0.),(0.,10.,0.)),1000),('front_post',state(goal+[-.35,.42,.10],(2.,0.,0.)),200),('crossbar',state(goal+[-.35,0,.47],(2.,0.,.6)),200),('back_net',state(goal+[.15,0,.10],(2.,0.,0.)),200),('side_net',state(goal+[.20,.20,.10],(0.,2.,0.)),200),('FL_radius_contact',state(start,probe=start+[-.1-radius-.02,0,0],probe_velocity=(1.5,0,0)),200)]
        write_json(root/(label+'-predeclared-scenarios.json'),[{'name':name,'initial_state':s,'physics_steps':steps} for name,s,steps in scenarios])
        try:
            for name,s,steps in scenarios:
                physics.reset(initial_states={0:s,1:state(start)})
                entry=GoalEntry(profile['goal_geometry'],.1);entry.reset(start if name=='rolling_into_goal' else s['qpos'][oq:oq+3]);hold=peak=0;positions=[];hits={};max_x=-1e9;max_y=-1e9
                for step in range(steps):
                    physics.step(np.zeros((2,12),np.float32));d=physics.data[0];pos=d.qpos[oq:oq+3].copy();max_x=max(max_x,pos[0]);max_y=max(max_y,pos[1])
                    for contact in d.contact[:d.ncon]:
                        gs=[int(v) for v in contact.geom]
                        if int(m.geom('ball_collision').id) not in gs:continue
                        for gid in gs:
                            gname=mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_GEOM,gid)
                            if gname!='ball_collision':hits[gname]=hits.get(gname,0)+1
                    if (step+1)%10==0:
                        condition=entry.update(step+1,pos);hold=hold+1 if condition else 0;peak=max(peak,hold)
                        positions.append({'physics_step':step+1,'ball':pos.tolist(),'velocity':d.qvel[ov:ov+3].tolist()})
                    assert np.all(d.qfrc_applied==0) and np.all(d.xfrc_applied==0)
                if name=='drop':assert abs(pos[2]-.1)<.004,'Ball did not settle at its analytic radius'
                elif name=='rolling_into_goal':assert peak>=3 and any(k.startswith('back_net') for k in hits),'Ball did not roll through the open goal into the real back net'
                elif name=='front_post':assert any(k.startswith('front_post') for k in hits) and max_x<goal[0]+.02,'Post collision failed'
                elif name=='crossbar':assert 'front_crossbar' in hits,'Crossbar contact failed'
                elif name=='back_net':assert any(k.startswith('back_net') for k in hits) and max_x<goal[0]+.33,'Back net escaped'
                elif name=='side_net':assert any(k.startswith('side_net') for k in hits) and max_y<goal[1]+.35,'Side net escaped'
                else:assert 'diagnostic_probe_geom' in hits and max_x>start[0]+.04,'Actual FL-sized sphere did not transfer momentum'
                records[name]={'passed':True,'positions':positions,'contact_ticks_by_geom':hits,'maximum_ball_x':max_x,'maximum_ball_y':max_y,'goal_condition_peak_ticks':peak,'not_a_demonstration':True}
                print(label,a.backend,name,'passed',flush=True)
            other=physics.snapshot(1);selected=state(start);physics.reset([0],initial_states={0:selected});after=physics.snapshot(1)
            for key in ('qpos','qvel','act','eq_active','mocap_pos','mocap_quat'):np.testing.assert_array_equal(other[key],after[key])
            assert other['time']==after['time'] and other['physics_step']==after['physics_step'] and physics.ticks[0]==0
            from qlm_bench.backends.mujoco.render import RenderMirror
            mirror=RenderMirror(path,world_id=1,rgb_profile='dual-rgb-360p-v1');snapshot=physics.snapshot(1);capture=mirror.capture(snapshot,terminal=True)
            for key in ('qpos','qvel','mocap_pos','mocap_quat','act','eq_active'):np.testing.assert_array_equal(getattr(mirror.data,key),snapshot[key])
            assert not capture['mirror_physics_advanced'] and mirror.data.time==snapshot['time'];mirror.close()
            results[label]={'passed':True,'scenarios':records,'selected_lane_reset_and_other_lane_preserved':True,'same_timestamp_complete_native_render_mirror':True,'model_identity':physics.model_identity,'effective_backend_options':physics.backend_options}
            write_json(root/'partial-results.json',results)
        finally:physics.close()
    write_json(root/'result.json',{'passed':True,'backend':a.backend,'assets':results,'RAMBO_task_success':'not_run by passive diagnostics','physical_demonstrations':0,'source_entry_sha256':sha(__file__)})

if __name__=='__main__':main()
