"""Render/inspect the same successful Kick timestamp states, never advance physics."""
import argparse,json,time
from collections import Counter
from pathlib import Path
import mujoco
import numpy as np
from PIL import Image
from qlm_bench.backends.mujoco.render import RenderMirror
from qlm_bench.backends.mujoco.trace import verify_trace,SNAPSHOT_ARRAYS,sha,write_json
from qlm_bench.backends.mujoco.kick_goal import GoalEntry
from qlm_bench.compatibility.dataset_v2.finalization import finalize_video
from qlm_bench.compatibility.dataset_v2.media import MediaTools
from qlm_bench.compatibility.dataset_v2.validation import PROFILE
from qlm_bench.compatibility.rgb_profiles import dataset_profile
from qlm_bench.data.video_writer import VideoSink


def main():
    p=argparse.ArgumentParser();p.add_argument('--trace',required=True);p.add_argument('--output',required=True);p.add_argument('--ffmpeg',required=True);p.add_argument('--ffprobe',required=True);p.add_argument('--frames-only',action='store_true');a=p.parse_args()
    m,z,tel,commands,terminal=verify_trace(a.trace)
    assert m['reference'] and m['profile']['task_id']=='kick_ball_to_goal'
    out=Path(a.output);out.mkdir(parents=True,exist_ok=False);start=time.monotonic()
    mirror=RenderMirror(m['scene']['model'],rgb_profile='dual-rgb-360p-v1');assert mirror.identity==m['model_identity']
    entry=GoalEntry(m['profile']['goal_geometry'],m['profile']['ball_radius_m']);entry.reset(tel['boundaries'][0]['state']['task.object.position'])
    phases=[c['extensions']['expert']['phase'] for c in commands];selected={0,m['n_actions']};selected.update(i for i,x in enumerate(phases) if i==0 or x!=phases[i-1])
    selected.update(min(m['n_actions'],int((next((i for i,x in enumerate(phases) if x=='strike'),0)/50+dt)*50)) for dt in [0.,.2,.4,.8,1.6])
    records=[];counts=Counter();sinks={};validation={};rows=[];images={};contact_by_phase=Counter();first_contact=None;last_contact=None
    physics_data=mujoco.MjData(mirror.model);ball=mirror.model.body('primary').id;goal=mirror.model.body('goal').id
    robot_names=set(['base','Head_upper','Head_lower'])
    for bid in range(mirror.model.nbody):
        name=mujoco.mj_id2name(mirror.model,mujoco.mjtObj.mjOBJ_BODY,bid) or ''
        if name.startswith(('FL_','FR_','RL_','RR_')):robot_names.add(name)
    try:
        if not a.frames_only:
            for role,fps in [('ego',50),('task_centric',50),('observer',25)]:sinks[role]=VideoSink(out/'cameras'/(role+'.mp4'),a.ffmpeg,fps,rgb_profile='dual-rgb-720p-v1' if role=='observer' else 'dual-rgb-360p-v1')
        for i,b in enumerate(tel['boundaries']):
            snap={k:z[k][i].copy() for k in SNAPSHOT_ARRAYS};snap.update(model_identity=m['model_identity'],model_parameters_identity=m['model_parameters_identity'],world_id=m['world_id'],reset_epoch=m['reset_epoch'],physics_step=int(z['physics_step'][i]),simulation_time_ns=int(z['simulation_time_ns'][i]),time=float(z['time'][i]))
            for k in SNAPSHOT_ARRAYS:getattr(physics_data,k)[:]=snap[k]
            physics_data.time=snap['time'];mujoco.mj_forward(mirror.model,physics_data)
            measured=physics_data.xpos[ball].copy();np.testing.assert_allclose(measured,b['state']['task.object.position'],atol=1e-12)
            condition=False if i==0 else entry.update(int(z['physics_step'][i]),measured)
            pairs=[];phase=phases[min(i,len(phases)-1)]
            for c in physics_data.contact[:physics_data.ncon]:
                bodies=[int(mirror.model.geom_bodyid[int(g)]) for g in c.geom]
                if ball not in bodies:continue
                names=[mujoco.mj_id2name(mirror.model,mujoco.mjtObj.mjOBJ_BODY,bid) or '' for bid in bodies]
                other=names[1] if bodies[0]==ball else names[0]
                kind='FL_leg' if other.startswith('FL_') else 'other_robot' if other in robot_names else 'goal' if goal in bodies else 'floor'
                pairs.append({'bodies':names,'kind':kind,'distance_m':float(c.dist)})
            kinds={p['kind'] for p in pairs}
            for kind in kinds:counts[kind+'_contact_boundaries']+=1
            if 'FL_leg' in kinds:contact_by_phase[phase]+=1;first_contact=i if first_contact is None else first_contact;last_contact=i
            records.append({'boundary':i,'phase':phase,'ball_world':measured.tolist(),'whole_sphere_goal_condition':condition,'actual_snapshot_geometry_contacts':pairs})
            if not a.frames_only or i in selected:
                capture=mirror.capture(snap,terminal=i==m['n_actions']);assert not capture['mirror_physics_advanced']
                for k in SNAPSHOT_ARRAYS:np.testing.assert_array_equal(getattr(mirror.data,k),snap[k])
                frames={'ego':capture['rgb']['go2_ego'],'task_centric':capture['rgb']['d435i_rgb_task']}
                if capture['observer_rgb'] is not None:frames['observer']=capture['observer_rgb']
                for role,image in frames.items():
                    if not a.frames_only and (role!='observer' or snap['physics_step']%20==0):sinks[role].write(image)
                    if i in selected:
                        dest=out/'review_frames'/f'{i:06d}-{role}.jpg';dest.parent.mkdir(exist_ok=True);Image.fromarray(image).save(dest,quality=95);rows.append({'boundary':i,'phase':phase,'role':role,'path':str(dest),'simulation_time_ns':snap['simulation_time_ns']})
                    if i==m['n_actions']:
                        dest=out/'terminal'/(role+'.png');dest.parent.mkdir(exist_ok=True);Image.fromarray(image).save(dest);images[role]={'path':str(dest),'sha256':sha(dest)}
            if i%150==0:print('Kick same-state mirror',i,'/',m['n_actions'],flush=True)
        assert all(x['whole_sphere_goal_condition'] for x in records[-3:])
        videos={role:s.close() for role,s in sinks.items()};sinks={};tools=MediaTools(a.ffmpeg,a.ffprobe);policy=dataset_profile(PROFILE,'dual-rgb-360p-v1')['policy_video']
        for role,v in videos.items():validation[role]=finalize_video(v['partial'],v['final'],count=v['count'],fps=25 if role=='observer' else 50,tools=tools,profile=None if role=='observer' else policy,receipt=v['receipt'])
        high=tel['physics'];joints=np.rad2deg(np.asarray([r['joint_position'] for r in high if r['physics_step']%5==0])[:,[0,4,8]])
        hi_rows=[r for r in high if r['physics_step']%5==0];hphase=[phases[min(r['physics_step']//10,len(phases)-1)] for r in hi_rows];metrics={}
        for phase in dict.fromkeys(phases):
            ix=np.where(np.asarray(hphase)==phase)[0];q=joints[ix];continuous=np.diff(ix)==1;diff=np.abs(np.diff(q,axis=0))
            metrics[phase]={'joint_order':['FL_hip_roll','FL_thigh','FL_calf'],'range_deg':np.ptp(q,axis=0).tolist(),'maximum_10ms_step_deg':diff[continuous].max(axis=0).tolist() if np.any(continuous) else [0,0,0]}
        strike_i=next(i for i,p in enumerate(phases) if p=='strike');initial=np.asarray(records[0]['ball_world']);before=np.asarray([r['ball_world'] for r in records[:strike_i]])
        pre=float(np.linalg.norm(before[:,:2]-initial[:2],axis=1).max());free_duration=(m['n_actions']-last_contact)/50 if last_contact is not None else None
        quality={'reference_only':True,'user_quality_approval':'pending','task_outcome':{'success':terminal['success'],'fallen':terminal['fallen']},'n_actions':m['n_actions'],'n_boundaries':m['n_boundaries'],'simulation_s':m['n_actions']/50,'snapshot_contact_counts':dict(counts),'FL_contact_phase_boundaries':dict(contact_by_phase),'pre_strike_ball_displacement_m':pre,'last_FL_contact_s':None if last_contact is None else last_contact/50,'free_ball_motion_after_last_contact_s':free_duration,'terminal_ball_world':records[-1]['ball_world'],'last_three_whole_sphere_goal_conditions':True,'phase_actual_100Hz_joint_metrics':metrics,'task_success_separate_from_quality':True,'unknown_contact_not_hard_failure':True,'contact_scope':'Native geometry at authoritative50Hz states; high-rate pose/force source remains original recorded telemetry','no_video_or_action_smoothing':True}
        write_json(out/'quality.json',quality);write_json(out/'state-contact-review.json',records);write_json(out/'review-frames.json',rows)
        write_json(out/'result.json',{'passed':True,'reference_only':True,'formal_demonstrations':0,'trace_manifest_sha256':sha(Path(a.trace)/'manifest.json'),'entry_sha256':sha(__file__),'mirror_physics_advanced':False,'controller_loaded':False,'WAM_loaded':False,'frames_only':a.frames_only,'media_validation':validation,'terminal_images':images,'actual_GL':mirror.gl_identity,'wall_s':time.monotonic()-start})
    finally:
        for s in sinks.values():s.close()
        mirror.close()

if __name__=='__main__':main()
