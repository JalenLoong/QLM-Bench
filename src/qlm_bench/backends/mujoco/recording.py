"""Bounded engineering collection driver with durable, separate failure evidence.

The driver owns reset/step. Recorder callbacks only consume completed states.
Partial/error attempts remain auditable and never enter the frozen Canonical format.
"""
import copy
import hashlib
import json
import time
import shutil
import traceback
import math
import importlib.metadata
from pathlib import Path

import numpy as np

from qlm_bench.compatibility.contracts_v2.runtime import prepare_command
from qlm_bench.controllers.rambo.core import CHECKPOINT_SHA256
from .expert_adapter import ExpertAdapter
from .video import VideoSink
from .conversion import convert
from qlm_bench.collection.orchestrator import source_identity


def _write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_suffix(path.suffix+'.writing')
    temporary.write_text(json.dumps(_json_safe(value),indent=2,allow_nan=False)+'\n');temporary.replace(path)


def _json_safe(value):
    if isinstance(value,(float,np.floating)) and not math.isfinite(float(value)):
        return {'nonfinite_float':str(value)}
    if isinstance(value,np.ndarray):return _json_safe(value.tolist())
    if isinstance(value,np.generic):return value.item()
    if isinstance(value,dict):return {k:_json_safe(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [_json_safe(v) for v in value]
    return value


def _snapshot_record(snapshot):
    return {k:copy.deepcopy(v) for k,v in snapshot.items() if k not in ('rgb','observer_rgb')}


def record_engineering(runtime,output,*,ffmpeg,ffprobe,commands=101,source_commit,expert_profile=None,work_id='QLM-SIM-005'):
    out=Path(output);raw=out/'raw'/f"{runtime.task.task}__engineering_ep0001"
    raw.mkdir(parents=True,exist_ok=False)
    runtime.profile['horizon_s']=commands*.02
    runtime.task.profile['horizon_s']=commands*.02
    expert=ExpertAdapter(runtime.physics,runtime.core,runtime.task)
    if expert_profile is not None:expert.apply_profile_override(expert_profile)
    boundaries=[];controls=[];physical=[];contacts=[];indices=[];completed=[]
    started=time.monotonic()
    runtime_timing_start=dict(runtime.timing)
    timing={'runtime_and_overhead_s':0.,'capture_render_write_s':0.,'encoder_close_s':0.,'packaging_s':0.}
    source_root=Path(__file__).resolve().parents[4]
    source=source_identity(source_root)
    implementation={}
    for folder in ('src/qlm_bench','scripts/mujoco'):
        for path in sorted(p for p in (source_root/folder).rglob('*') if p.suffix in ('.py','.json')):
            name=str(path.relative_to(source_root));implementation[name]=hashlib.sha256(path.read_bytes()).hexdigest()
            target=out/'source_snapshot'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target)
    _write(out/'source_snapshot/identity.json',{'source':source,'files':implementation})
    sinks={};videos={};errors=[];attempts=[];terminal=None;epoch=None
    def event(kind,payload):
        with (raw/'events.jsonl').open('a') as stream:
            stream.write(json.dumps(_json_safe({'event':kind,**payload}),allow_nan=False)+'\n');stream.flush()
    def channels():return runtime.state_channels()
    def physics_row(rt,efforts):
        state=channels();tick=int(rt.physics.ticks[0]);ns=tick*2_000_000
        physical.append(dict(timestamp_ns=ns,physics_step=tick,
            base_pose=state['observation.state.base.position']+state['observation.state.base.orientation'],
            base_twist=state['observation.state.base.linear_velocity']+state['observation.state.base.angular_velocity'],
            joint_position=state['observation.state.joint_position'],joint_velocity=state['observation.state.joint_velocity'],
            joint_torque=np.asarray(efforts[0],np.float32).tolist(),
            object_pose=state['task.object.position']+state['task.object.orientation'],
            object_velocity=state['task.object.linear_velocity']+state['task.object.angular_velocity'],
            external_force=[0.,0.,0.],external_torque=[0.,0.,0.],external_wrench_frame='world'))
        contacts.append(dict(measurement_timestamp_ns=ns,sensor_sequence_index=len(contacts),
            force=state['observation.state.fl_contact_force'],torque=None,frame='world',force_kind='net_normal',valid=True))
    def control_row(rt,residual):
        tick=int(rt.physics.ticks[0])
        controls.append(dict(timestamp_ns=tick*2_000_000,controller_tick=tick//5,
            high_level_command=rt.current['filtered'],policy_residual=residual[0].cpu().tolist(),
            reference_state=rt.core._desired_joint_pos[0].cpu().tolist(),
            residual_observation_command_id=rt.controller_reference_command_id,
            fl_ik_command_id=rt.controller_reference_command_id,
            fl_ik_computed_tick=rt.controller_reference_tick,
            desired_joint_target=rt.core.desired_pos[0].cpu().tolist(),
            desired_joint_velocity=rt.core.desired_vel[0].cpu().tolist(),
            desired_joint_torque=rt.core.desired_tor[0].cpu().tolist(),
            controller_mode='retained_quadruped_rambo',safety_flags=0))
    def boundary():
        before=time.monotonic()
        snapshot=runtime.state();row={k:copy.deepcopy(snapshot[k]) for k in ('simulation_time_ns','physics_step','state','rgb_hashes','sensor_frame_ids')}
        row['contact']={'status':'measured','valid':True,'fl_object':bool(snapshot['state']['task.contact.fl_object'][0]),
                        'body_object':bool(snapshot['state']['task.contact.body_object'][0])}
        row['task_review']={'source':'actual_mujoco_state','backend_profile':runtime.profile['asset_profile']}
        boundaries.append(row)
        event('boundary',row)
        for role,rgb in snapshot['rgb'].items():
            sinks[role].write(rgb)
            indices.append(dict(camera_key='observation.images.'+role,frame_index=sinks[role].count-1,
                                simulation_time_ns=row['simulation_time_ns'],physics_step=row['physics_step'],valid=True))
        if snapshot.get('observer_rgb') is not None and row['physics_step']%20==0:
            sinks['observer'].write(snapshot['observer_rgb'])
            indices.append(dict(camera_key='monitor.images.observer',frame_index=sinks['observer'].count-1,
                                simulation_time_ns=row['simulation_time_ns'],physics_step=row['physics_step'],valid=True))
        timing['capture_render_write_s']+=time.monotonic()-before
    def save_terminal(snapshot):
        record=_snapshot_record(snapshot)
        from PIL import Image
        record['actual_images']={}
        images=dict(snapshot.get('rgb',{}))
        if snapshot.get('observer_rgb') is not None:images['observer']=snapshot['observer_rgb']
        for role,image in images.items():
            path=raw/'terminal'/f'{role}.png';path.parent.mkdir(parents=True,exist_ok=True);Image.fromarray(image).save(path)
            record['actual_images'][role]={'path':str(path.relative_to(raw)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
        event('terminal',record)
        return record
    try:
        roles=('ego','task_centric','observer') if runtime.renderer.observer_clip is not None else ('ego','task_centric')
        for role in roles:sinks[role]=VideoSink(raw/'cameras'/(role+'.mp4'),ffmpeg,25 if role=='observer' else 50,rgb_profile='dual-rgb-720p-v1' if role=='observer' else runtime.rgb_profile)
        runtime.reset();epoch=int(runtime.physics.epochs[0])
        runtime.on_physics=physics_row;runtime.on_control=control_row
        physics_row(runtime,np.zeros((1,12),dtype=np.float32));boundary()
        for i in range(commands):
            values,diagnostic=expert.command()
            prepared=prepare_command(values,f'p2:{i}',int(runtime.physics.ticks[0]))
            event('command_submitted',{'command':prepared,'expert':diagnostic})
            result=runtime.step(prepared)
            actual=copy.deepcopy(result['command']);actual['extensions']['expert']=diagnostic;attempts.append(actual)
            event('command_confirmation',{'command':actual})
            if result['completed_interval']:
                completed.append(actual);boundary()
            if result['terminal'] is not None:terminal=save_terminal(result['terminal'])
            if result['terminal'] is not None:break
        if runtime.terminal is None:
            raise ValueError('Engineering recording must have a physical terminal')
    except BaseException as error:
        errors.append({'stage':'capture','type':type(error).__name__,'message':str(error),'traceback':traceback.format_exc()})
        try:terminal=save_terminal(runtime.abort('recording_error'))
        except BaseException as terminal_error:
            errors.append({'stage':'terminal_capture','type':type(terminal_error).__name__,'message':str(terminal_error)})
            # Preserve factual physics state even when rendering cannot supply an
            # observation. No stale/grey/synthetic image substitutes are created.
            try:
                terminal={'simulation_time_ns':int(runtime.physics.ticks[0])*2_000_000,
                          'physics_step':int(runtime.physics.ticks[0]),'reset_epoch':int(runtime.physics.epochs[0]),
                          'state':runtime.state_channels(),'reason':'recording_error','rgb_unavailable':True,
                          'command_confirmation':copy.deepcopy(runtime.current),'unconfirmed_physics_prefix':True}
            except BaseException as state_error:
                terminal={'reason':'recording_error','state_unavailable':True,'error':str(state_error)}
    finally:
        runtime.on_physics=None;runtime.on_control=None
        before_close=time.monotonic()
        # Persist state before encoder close: an encoder failure must not discard
        # the actual terminal/confirmation history already observed.
        _write(raw/'capture-state.json',{'boundaries':boundaries,'completed_commands':completed,'command_attempts':attempts,
            'current_command':copy.deepcopy(runtime.current),'executed_history':copy.deepcopy(runtime.history),
            'terminal':terminal,'physics':physical,'controller':controls,'errors':errors})
        for role,sink in sinks.items():
            try:videos[role]=sink.close()
            except BaseException as error:
                errors.append({'stage':'encoder_close','role':role,'type':type(error).__name__,'message':str(error)})
        timing['encoder_close_s']=time.monotonic()-before_close
    if source_identity(source_root)['dirty_source_sha256']!=source['dirty_source_sha256']:
        errors.append({'stage':'source_identity','message':'Source changed during collection; attempt cannot enter Canonical'})
    try:
        from .resources import resource_closure,model_parameter_identity
        runtime.physics.assert_frozen_model(full=True)
        if model_parameter_identity(runtime.renderer.model,full=True)!=runtime.renderer.full_model_identity:
            raise ValueError('Rendering model/texture changed during collection')
        if resource_closure(runtime.physics.model_path)!=runtime.physics.resource_profile:
            raise ValueError('Resource pack changed during collection')
    except Exception as error:
        errors.append({'stage':'frozen_resources','type':type(error).__name__,'message':str(error)})
    profile=dict(expert.cfg.approved_profile)
    profile.update(task_profile_version='mujoco-'+runtime.task.task+'-runtime-v1',
                   canonical_goal_position=runtime.profile.get('canonical_goal_position',boundaries[0]['state']['task.goal.position'] if boundaries else None),
                   asset_id=runtime.profile['asset_id'],asset_sha256=runtime.physics.model_identity)
    cap=dict(rgb_spatial_profile=runtime.rgb_profile,boundaries=boundaries,commands=completed,controller=controls,physics=physical,contact_sensor=contacts,
        camera_index=indices,terminal=terminal,videos=videos,profile=profile,task_text=runtime.profile['instruction'],
        checkpoint_sha256=CHECKPOINT_SHA256,implementation=implementation,source_commit=source_commit,source_identity=source,
        diagnostic_only=True,mode='p2_engineering_not_demonstration',work_id=work_id,reset_epoch=epoch,task_id=runtime.task.task,
        status='success' if runtime.outcome['success'] else 'failure',
        initial_geometry={'source':'actual_initial_snapshot','state':boundaries[0]['state'] if boundaries else None},
        command_attempts=attempts,executed_history=copy.deepcopy(runtime.history),current_command=copy.deepcopy(runtime.current),errors=errors,
        backend=dict(physics=runtime.physics.backend,render=__import__('os').environ['MUJOCO_GL'],
                     controller='original model_2000',asset_profile=copy.deepcopy(runtime.profile),
                     resources=runtime.physics.resource_profile,GL=runtime.renderer.gl_identity,
                     effective_physics_options=runtime.physics.backend_options,
                     model_parameters_identity=runtime.physics.model_parameters_identity,
                     motor_lags_physics_ticks=runtime.core.motor.lags.cpu().tolist(),
                     case_seed=runtime.case_seed,random_streams=runtime.core.case_rng.identity(),
                     controller_configuration=vars(runtime.core.cfg),
                     normalizer_mean_sha256=hashlib.sha256(runtime.core.actor.mean.cpu().numpy().tobytes()).hexdigest(),
                     normalizer_std_sha256=hashlib.sha256(runtime.core.actor.std.cpu().numpy().tobytes()).hexdigest(),
                     environment={name:importlib.metadata.version(name) for name in ('mujoco','mujoco-warp','warp-lang','torch','qpth','numpy','av')},
                     controller_device=str(runtime.core.device),
                     expert_override=expert.override,
                     expert=expert.cfg.approved_profile['expert']))
    eligible=bool(not errors and terminal and not terminal.get('partial_interval',False) and completed and
                  len(boundaries)==len(completed)+1 and terminal['physics_step']==boundaries[-1]['physics_step'])
    summary={'passed':eligible,'terminal_before_reset':bool(terminal and epoch==int(runtime.physics.epochs[0])),
             'mode':cap['mode'],'canonical_eligible':eligible,'errors':errors,
             'partial_interval':bool(terminal and terminal.get('partial_interval')),
             'failure_artifacts_preserved':True,'completed_commands':len(completed)}
    _write(raw/'capture.json',cap);_write(raw/'summary.json',summary)
    before_packaging=time.monotonic()
    result={'passed':False,'canonical':None,'capture':str(raw),'reason':'incomplete/partial/error attempt retained; frozen Canonical not produced'}
    if eligible:
        try:result={'passed':True,**convert(raw,out/'canonical',ffmpeg=ffmpeg,ffprobe=ffprobe)}
        except BaseException as error:
            errors.append({'stage':'conversion','type':type(error).__name__,'message':str(error),'traceback':traceback.format_exc()})
            summary.update(passed=False,errors=errors);_write(raw/'summary.json',summary)
            result.update(reason='conversion failed; retained attempt is not usable Canonical',error=errors[-1])
    timing['packaging_s']=time.monotonic()-before_packaging
    timing['total_s']=time.monotonic()-started
    timing['runtime_and_overhead_s']=timing['total_s']-sum(timing[k] for k in ('capture_render_write_s','encoder_close_s','packaging_s'))
    import psutil
    performance={'timing_s':timing,'state_transfer':runtime.physics.transfer_metrics,
        'runtime_breakdown_s':{k:v-runtime_timing_start[k] for k,v in runtime.timing.items()},
        'timing_note':'observation_s includes mirror_refresh_s/render_readback_s; runtime_and_overhead_s includes runtime captures, not physics alone',
        'peak_rss_bytes':__import__('resource').getrusage(__import__('resource').RUSAGE_SELF).ru_maxrss*1024,
        'rss_bytes':psutil.Process().memory_info().rss,
        'simulation_s':len(completed)*.02,'commands':len(completed),
        'dataset_bytes':sum(p.stat().st_size for p in out.rglob('*') if p.is_file())}
    (out/'performance.json').write_text(json.dumps(performance,indent=2)+'\n')
    _write(out/'result.json',result)
    return result
