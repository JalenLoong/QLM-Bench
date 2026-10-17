"""Offline Lift reference media and quality from immutable CUDA physical snapshots."""
import argparse
from collections import Counter
from pathlib import Path
import sys
import time

import mujoco
import numpy as np
from PIL import Image

from qlm_bench.backends.mujoco.render import RenderMirror
from qlm_bench.backends.mujoco.trace import SNAPSHOT_ARRAYS, sha, verify_trace, write_json
from qlm_bench.compatibility.dataset_v2.finalization import finalize_video
from qlm_bench.compatibility.dataset_v2.media import MediaTools
from qlm_bench.compatibility.dataset_v2.validation import PROFILE
from qlm_bench.compatibility.rgb_profiles import dataset_profile
from qlm_bench.data.video_writer import VideoSink


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('trace','model','output','ffmpeg','ffprobe'):
        p.add_argument('--'+name,required=True)
    p.add_argument('--frames-only',action='store_true',help='retarget endpoint/phase frames, no video workload')
    args=p.parse_args()
    manifest,arrays,telemetry,commands,terminal=verify_trace(args.trace)
    if not manifest['reference'] or manifest['profile']['task_id']!='lift_basket':
        raise ValueError('Only explicit Lift reference evidence')
    out=Path(args.output);out.mkdir(parents=True,exist_ok=False)
    mirror=RenderMirror(args.model,world_id=manifest['world_id'],rgb_profile='dual-rgb-360p-v1')
    if mirror.identity!=manifest['model_identity']:
        mirror.close();raise ValueError('Actual reference model identity mismatch')
    source_files={Path(args.trace)/name:sha(Path(args.trace)/name) for name in manifest['files']}
    phases=Counter(c['extensions']['expert']['phase'] for c in commands)
    selected={0,manifest['n_actions']}
    selected.update(next(i for i,c in enumerate(commands) if c['extensions']['expert']['phase']==phase) for phase in phases)
    primary=int(mirror.model.body('primary').id)
    fl=int(mirror.model.geom('FL').id)
    base=int(mirror.model.body('base').id)
    support=np.asarray(manifest['profile']['support_vertices_local'])
    # Geometry-only forensic data imports full snapshots. It never advances physics.
    review_data=mujoco.MjData(mirror.model)
    sinks={};rows=[];images={};timings=Counter();started=time.monotonic()
    counts=Counter()
    try:
        if not args.frames_only:
            for role,fps in [('ego',50),('task_centric',50),('observer',25)]:
                sinks[role]=VideoSink(out/'cameras'/(role+'.mp4'),args.ffmpeg,fps,
                    rgb_profile='dual-rgb-720p-v1' if role=='observer' else 'dual-rgb-360p-v1')
        for i,boundary in enumerate(telemetry['boundaries']):
            snapshot={k:arrays[k][i].copy() for k in SNAPSHOT_ARRAYS}
            snapshot.update(model_identity=manifest['model_identity'],model_parameters_identity=manifest['model_parameters_identity'],
                world_id=manifest['world_id'],reset_epoch=manifest['reset_epoch'],
                physics_step=int(arrays['physics_step'][i]),simulation_time_ns=int(arrays['simulation_time_ns'][i]),time=float(arrays['time'][i]))
            # Every snapshot is imported at its authoritative timestamp; no mj_step.
            for key in SNAPSHOT_ARRAYS:
                target=getattr(review_data,key);value=snapshot[key]
                assert target.shape==value.shape
                target[:]=value
            review_data.time=snapshot['time']
            mujoco.mj_forward(mirror.model,review_data)
            points=support@review_data.xmat[primary].reshape(3,3).T+review_data.xpos[primary]
            floor=float(manifest['profile']['floor_z_m'])
            bottom=float(points[:,2].min()-floor)
            recorded=float(boundary['state']['task.progress'][0])
            assert abs(bottom-recorded)<2e-6,'Rendered state disagrees with recorded whole-geometry clearance'
            pairs=[]
            for contact in review_data.contact[:review_data.ncon]:
                g1,g2=map(int,contact.geom)
                bodies=(int(mirror.model.geom_bodyid[g1]),int(mirror.model.geom_bodyid[g2]))
                if primary not in bodies:
                    continue
                names=[mujoco.mj_id2name(mirror.model,mujoco.mjtObj.mjOBJ_GEOM,g) or f'geom{g}' for g in (g1,g2)]
                body_names=[mujoco.mj_id2name(mirror.model,mujoco.mjtObj.mjOBJ_BODY,b) or f'body{b}' for b in bodies]
                fl_leg=any(name.startswith('FL_') for name in body_names)
                pairs.append({'geoms':names,'distance_m':float(contact.dist),'FL':fl in (g1,g2),
                    'bodies':body_names,'FL_leg':fl_leg,'base':base in bodies,'floor':0 in bodies,
                    'other_robot_part':all(b not in (primary,0,base) for b in bodies if b!=primary) and fl not in (g1,g2) and not fl_leg})
            counts['FL_basket_boundaries']+=any(x['FL'] for x in pairs)
            counts['FL_leg_basket_boundaries']+=any(x['FL_leg'] for x in pairs)
            counts['base_basket_boundaries']+=any(x['base'] for x in pairs)
            counts['other_robot_basket_boundaries']+=any(x['other_robot_part'] for x in pairs)
            counts['floor_basket_boundaries']+=any(x['floor'] for x in pairs)
            rows.append({'boundary':i,'simulation_time_ns':int(arrays['simulation_time_ns'][i]),
                'minimum_basket_floor_clearance_m':bottom,'snapshot_contact_geometry':pairs,
                'contact_scope':'Native collision reconstructed at actual CUDA state, not CUDA force telemetry',
                'physical_FL_world':review_data.geom_xpos[fl].tolist()})
            if not args.frames_only or i in selected:
                frame=mirror.capture(snapshot,terminal=i==manifest['n_actions'])
                assert not frame['mirror_physics_advanced']
                np.testing.assert_array_equal(mirror.data.qpos,snapshot['qpos'])
                np.testing.assert_array_equal(mirror.data.qvel,snapshot['qvel'])
                assert mirror.data.time==snapshot['time']
                timings.update(frame['timing_s'])
                rgb={'ego':frame['rgb']['go2_ego'],'task_centric':frame['rgb']['d435i_rgb_task']}
                if frame['observer_rgb'] is not None:rgb['observer']=frame['observer_rgb']
                for role,im in rgb.items():
                    if not args.frames_only and (role!='observer' or snapshot['physics_step']%20==0):
                        sinks[role].write(im)
                    if i in selected:
                        dest=out/'review_frames'/f'{i:06d}-{role}.png';dest.parent.mkdir(exist_ok=True)
                        Image.fromarray(im).save(dest)
                    if i==manifest['n_actions']:
                        dest=out/'terminal'/(role+'.png');dest.parent.mkdir(exist_ok=True)
                        Image.fromarray(im).save(dest);images[role]={'path':str(dest),'sha256':sha(dest)}
            if i%100==0:print(f'Lift reference rendering {i}/{manifest["n_actions"]}',flush=True)
        videos={role:sink.close() for role,sink in sinks.items()};sinks={}
        tools=MediaTools(args.ffmpeg,args.ffprobe);validation={}
        policy_profile=dataset_profile(PROFILE,'dual-rgb-360p-v1')['policy_video']
        for role,video in videos.items():
            validation[role]=finalize_video(video['partial'],video['final'],count=video['count'],
                fps=25 if role=='observer' else 50,tools=tools,profile=None if role=='observer' else policy_profile,receipt=video['receipt'])
            assert validation[role]['episode_status']=='video_validated'
        actual=np.array([r['physical_FL_world'] for r in rows])
        joints=np.rad2deg(np.array([b['state']['observation.state.joint_position'] for b in telemetry['boundaries']])[:,[0,4,8]])
        controls=telemetry['controller'];physical=telemetry['physics']
        # Scoped reference quality diagnostics use actual 100Hz points from the legacy stream.
        high=[r for r in physical if r['physics_step']%5==0]
        hi_joints=np.rad2deg(np.array([r['joint_position'] for r in high])[:,[0,4,8]])
        command_phase=np.array([c['extensions']['expert']['phase'] for c in commands])
        hphase=command_phase[np.minimum(np.array([r['physics_step']//10 for r in high]),len(commands)-1)]
        phase_metrics={}
        for phase in phases:
            idx=np.where(hphase==phase)[0];q=hi_joints[idx]
            diffs=np.abs(np.diff(q,axis=0));continuous=np.diff(np.array([high[i]['physics_step'] for i in idx]))==5
            phase_metrics[phase]={'actual_FL_joint_range_deg':np.ptp(q,axis=0).tolist(),
                'actual_max_10ms_joint_step_deg':diffs[continuous].max(axis=0).tolist() if np.any(continuous) else [0,0,0],
                'sample_count':len(idx),'joint_order':['hip','thigh','calf']}
        through=[i for i,c in enumerate(commands) if c['extensions']['expert']['completely_through']]
        lift=[i for i,c in enumerate(commands) if c['extensions']['expert']['phase']=='lift']
        quality={'quality_separate_from_task_success':True,'eligibility':'user_review_required','task_predicate_changed':False,
            'task_outcome':{'success':terminal['success'],'fallen':terminal['fallen'],'timed_out':terminal['timed_out']},
            'n_actions':manifest['n_actions'],'n_boundaries':len(rows),'phase_actions':dict(phases),
            'phase_100Hz_actual_joint_metrics':phase_metrics,'snapshot_contact_counts':dict(counts),
            'contact_provenance':'Native at-CUDA-state geometric pairs; CUDA force telemetry not independently measured',
            'unknown_contact_is_failure':False,'minimum_basket_terminal_floor_clearance_m':rows[-1]['minimum_basket_floor_clearance_m'],
            'actual_max_20ms_FL_world_step_m':float(np.linalg.norm(np.diff(actual,axis=0),axis=1).max()),
            'actual_FL_joint_total_range_deg':np.ptp(joints,axis=0).tolist(),
            'through_first_command':through[0] if through else None,'lift_first_command':lift[0] if lift else None,
            'full_foot_through_before_lift':bool(through and lift and through[0]<lift[0]),
            'force_zero':all(np.all(np.asarray(c['executed'])[6:]==0) for c in commands),
            'no_animation_smoothing':True,'phase_frames_only':args.frames_only}
        write_json(out/'quality.json',quality);write_json(out/'state-contact-review.json',rows)
        np.savez_compressed(out/'quality-curves.npz',time_s=arrays['simulation_time_ns']/1e9,
            FL_joint_deg=joints,FL_world=actual,basket_clearance=np.array([r['minimum_basket_floor_clearance_m'] for r in rows]),
            high_time_s=np.array([r['physics_step']*.002 for r in high]),high_FL_joint_deg=hi_joints)
        assert all(sha(path)==h for path,h in source_files.items())
        assert not any(s in sys.modules for s in ('qlm_bench.backends.mujoco.physics','qlm_bench.backends.mujoco.runtime'))
        assert not any(s.startswith(('qlm_bench.controllers','wam_policy')) for s in sys.modules)
        write_json(out/'result.json',{'passed':True,'reference_only':True,'formal_pilot':False,
            'recording_entry_sha256':sha(__file__),'trace_manifest_sha256':sha(Path(args.trace)/'manifest.json'),
            'source_trace_unchanged':True,'model_identity':mirror.identity,'snapshot_count':len(rows),
            'physics_reexecuted':False,'mirror_physics_advanced':False,'renderer_runtime_controller_WAM_loaded':False,
            'rgb_profile':'dual-rgb-360p-v1','videos':videos,'media_validation':validation,
            'terminal_images':images,'timings_s':dict(timings),'wall_s':time.monotonic()-started,'GL':mirror.gl_identity,
            'frames_only':args.frames_only})
    finally:
        for sink in sinks.values():sink.close()
        mirror.close()


if __name__=='__main__':
    main()
