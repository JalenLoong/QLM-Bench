"""Kick behavior evidence from authoritative snapshots; never step or render physics."""
from collections import Counter
import mujoco
import numpy as np
from .trace import verify_trace, SNAPSHOT_ARRAYS
from .kick_goal import GoalEntry


def analyze_kick(trace):
    m,z,tel,commands,terminal=verify_trace(trace)
    if m['profile']['task_id']!='kick_ball_to_goal':raise ValueError('Kick trace required')
    model=mujoco.MjModel.from_xml_path(m['scene']['model']);data=mujoco.MjData(model)
    ball=model.body('primary').id;goal=model.body('goal').id
    robot={'base','Head_upper','Head_lower'}
    robot.update(n for i in range(model.nbody) if (n:=mujoco.mj_id2name(model,mujoco.mjtObj.mjOBJ_BODY,i) or '').startswith(('FL_','FR_','RL_','RR_')))
    phases=[c['extensions']['expert']['phase'] for c in commands]
    entry=GoalEntry(m['profile']['goal_geometry'],m['profile']['ball_radius_m'])
    entry.reset(tel['boundaries'][0]['state']['task.object.position'])
    counts=Counter();contacts=Counter();records=[];last=None
    for i,b in enumerate(tel['boundaries']):
        for k in SNAPSHOT_ARRAYS:getattr(data,k)[:]=z[k][i]
        data.time=float(z['time'][i]);mujoco.mj_forward(model,data)
        measured=data.xpos[ball].copy();np.testing.assert_allclose(measured,b['state']['task.object.position'],rtol=0,atol=1e-10)
        condition=False if i==0 else entry.update(int(z['physics_step'][i]),measured)
        kinds=set();pairs=[]
        for contact in data.contact[:data.ncon]:
            bodies=[int(model.geom_bodyid[int(g)]) for g in contact.geom]
            if ball not in bodies:continue
            names=[mujoco.mj_id2name(model,mujoco.mjtObj.mjOBJ_BODY,bid) or '' for bid in bodies]
            other=names[1] if bodies[0]==ball else names[0]
            kind='FL_leg' if other.startswith('FL_') else 'other_robot' if other in robot else 'goal' if goal in bodies else 'floor'
            kinds.add(kind);pairs.append({'bodies':names,'kind':kind,'distance_m':float(contact.dist)})
        # A boundary represents the command that just completed, not the next command.
        phase='initial' if i==0 else phases[i-1]
        for kind in kinds:counts[kind+'_contact_boundaries']+=1
        if 'FL_leg' in kinds:contacts[phase]+=1;last=i
        records.append({'boundary':i,'simulation_time_ns':int(z['simulation_time_ns'][i]),'completed_command_phase':phase,'ball_world':measured.tolist(),'whole_sphere_goal_condition':condition,'actual_snapshot_geometry_contacts':pairs})
    assert all(r['whole_sphere_goal_condition'] for r in records[-3:])
    high=[r for r in tel['physics'] if r['physics_step']%5==0]
    q=np.rad2deg(np.array([r['joint_position'] for r in high])[:,[0,4,8]])
    hp=np.array([phases[min(r['physics_step']//10,len(phases)-1)] for r in high]);metrics={}
    for phase in dict.fromkeys(phases):
        ix=np.where(hp==phase)[0];values=q[ix];contiguous=np.diff(ix)==1
        metrics[phase]={'joint_order':['FL_hip_roll','FL_thigh','FL_calf'],'range_deg':np.ptp(values,axis=0).tolist(),
            'maximum_10ms_step_deg':np.abs(np.diff(values,axis=0))[contiguous].max(axis=0).tolist() if np.any(contiguous) else [0,0,0]}
    strike=phases.index('strike');initial=np.array(records[0]['ball_world']);before=np.array([r['ball_world'] for r in records[:strike+1]])
    pre=float(np.linalg.norm(before[:,:2]-initial[:2],axis=1).max())
    # These evidence flags hold the successful trace for review; they never change task success.
    holds=[]
    if counts['other_robot_contact_boundaries']:holds.append('measured other-robot/ball contact requires behavior review')
    if pre>.001:holds.append('measured pre-strike ball motion exceeds1mm; review physical behavior')
    return {'task_success':terminal['success'],'fallen':terminal['fallen'],'n_actions':m['n_actions'],'simulation_s':m['n_actions']/50,
        'snapshot_contact_counts':dict(counts),'FL_contact_phase_boundaries':dict(contacts),'pre_strike_ball_displacement_m':pre,
        'last_FL_contact_s':None if last is None else last/50,'free_ball_motion_after_last_contact_s':None if last is None else (m['n_actions']-last)/50,
        'terminal_ball_world':records[-1]['ball_world'],'phase_actual_100Hz_joint_metrics':metrics,'behavior_review_holds':holds,
        'task_success_separate_from_quality':True,'unknown_or_zero_FL_contact_not_hard_failure':True,
        'contact_scope':'Native geometry at actual50Hz snapshots; no full-continuous-contact claim','physics_advanced':False},records
