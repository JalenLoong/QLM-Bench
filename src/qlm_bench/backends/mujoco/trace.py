"""Actual, non-rendering physical traces. This is not a simulator resume format."""
import copy
import gzip
import hashlib
import importlib.metadata
import json
from pathlib import Path
import os
import shutil
import time

import numpy as np

SNAPSHOT_ARRAYS=('qpos','qvel','act','mocap_pos','mocap_quat','eq_active')


class CandidateRejected(Exception):
    """Expected frozen-executor failure; not a simulator/system error."""


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()


def write_json(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    partial=path.with_name(path.name+'.writing')
    partial.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n');partial.replace(path)


def collect_trace(runtime,executor,scene,output,*,batch_identity,reference=False,
                  quality_policy='legacy-fl-contact-v1'):
    """Use existing execution and required legacy Raw-compatible streams.

    High-rate streams here serve the currently frozen Raw validator and scoped
    reference diagnostics, not an unconditional retention rule for future traces.
    New evidence-review traces separate physical success from human eligibility.
    """
    if quality_policy not in ('legacy-fl-contact-v1', 'evidence-review-v1'):
        raise ValueError('Unknown explicit demonstration quality policy')
    if not runtime.trace_only or runtime.renderer is not None:
        raise ValueError('PhysicalTrace requires runtime without a renderer')
    output=Path(output)
    if output.exists():raise FileExistsError(output)
    started=time.monotonic();boundaries=[];snapshots=[];physics=[];controls=[];contacts=[];commands=[]
    source_root=Path(__file__).resolve().parents[4]
    implementation={str(p.relative_to(source_root)):sha(p) for folder in ('src/qlm_bench','scripts/mujoco/synthesis')
        for p in sorted((source_root/folder).rglob('*')) if p.suffix in ('.py','.json')}
    batch_identity={**batch_identity,'implementation':implementation}
    peak_vram=0
    def boundary(packet):
        snap=copy.deepcopy(packet['physical_snapshot'])
        state=copy.deepcopy(packet['state'])
        fl=state.get('task.contact.fl_object',[None])[0]
        body=state.get('task.contact.body_object',[None])[0]
        known=isinstance(fl,(bool,np.bool_)) and isinstance(body,(bool,np.bool_))
        boundaries.append({'simulation_time_ns':packet['simulation_time_ns'],'physics_step':packet['physics_step'],
            'state':state,'contact':{'status':'measured' if known else 'unknown','valid':known,
                'fl_object':bool(fl) if known else None,'body_object':bool(body) if known else None},
            'task_review':{'source':'captured_physical_state','recording_mode':'offline_state_replay'}})
        snapshots.append(snap)
    def physics_row(rt,efforts):
        state=rt.state_channels();tick=int(rt.physics.ticks[0]);ns=tick*2_000_000
        physics.append(dict(timestamp_ns=ns,physics_step=tick,
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
            fl_ik_command_id=rt.controller_reference_command_id,fl_ik_computed_tick=rt.controller_reference_tick,
            desired_joint_target=rt.core.desired_pos[0].cpu().tolist(),
            desired_joint_velocity=rt.core.desired_vel[0].cpu().tolist(),desired_joint_torque=rt.core.desired_tor[0].cpu().tolist(),
            controller_mode='retained_quadruped_rambo',safety_flags=0))
    runtime.set_case_seed(scene['seed']);runtime.on_observation=boundary
    runtime.reset(initial_state=scene['initial_state'])
    executor.reset(runtime,scene)
    runtime.on_physics=physics_row;runtime.on_control=control_row
    physics_row(runtime,np.zeros((1,12),np.float32))
    from qlm_bench.compatibility.contracts_v2.runtime import prepare_command
    try:
        for index in range(int(runtime.profile['horizon_s']*50)):
            values,diagnostic=executor.command()
            prepared=prepare_command(values,f"{scene['candidate_id']}:{index}",int(runtime.physics.ticks[0]))
            result=runtime.step(prepared)
            if result['completed_interval']:
                command=copy.deepcopy(result['command']);command['extensions']['expert']=diagnostic;commands.append(command)
            if result['terminal'] is not None:break
        valid=bool(runtime.terminal and runtime.outcome['success'] and not runtime.outcome['fallen']
            and not runtime.terminal['partial_interval'] and len(boundaries)==len(commands)+1)
        quality={'fl_contact_boundaries':sum(bool(b['contact']['fl_object']) for b in boundaries),
            'body_contact_boundaries':sum(bool(b['contact']['body_object']) for b in boundaries)}
        physical_success=valid
        if quality_policy=='legacy-fl-contact-v1':
            valid=valid and quality['fl_contact_boundaries']>0 and quality['body_contact_boundaries']==0
        elapsed=time.monotonic()-started
        if not valid:
            return {'passed':False,'stage':'physics','outcome':copy.deepcopy(runtime.outcome),
                'reason':('task success or complete interval failed' if quality_policy=='evidence-review-v1'
                          else 'task/complete-interval/legacy FL-quality gate failed'),
                'physical_success':physical_success,'quality_policy':quality_policy,
                'quality':quality,'wall_s':elapsed}
        runtime.physics.assert_frozen_model(full=True)
        partial=output.with_name(output.name+'.writing')
        if partial.exists():shutil.rmtree(partial)
        partial.mkdir(parents=True)
        arrays={k:np.stack([s[k] for s in snapshots]) for k in SNAPSHOT_ARRAYS}
        arrays.update(time=np.asarray([s['time'] for s in snapshots]),
            physics_step=np.asarray([s['physics_step'] for s in snapshots],np.int64),
            simulation_time_ns=np.asarray([s['simulation_time_ns'] for s in snapshots],np.int64))
        np.savez_compressed(partial/'render_snapshots.npz',**arrays)
        with gzip.open(partial/'telemetry.json.gz','wt') as f:
            json.dump({'boundaries':boundaries,'controller':controls,'physics':physics,'contact_sensor':contacts},f,allow_nan=False)
        with (partial/'commands.jsonl').open('w') as f:
            for c in commands:f.write(json.dumps(c,allow_nan=False)+'\n')
        terminal={k:v for k,v in runtime.terminal.items() if k!='physical_snapshot'}
        write_json(partial/'terminal.json',terminal)
        import torch
        if torch.device(runtime.core.device).type=='cuda':peak_vram=torch.cuda.max_memory_allocated(runtime.core.device)
        import resource
        manifest={'schema':'qlm-physical-trace-v1','passed':True,'scene':scene,'batch_identity':batch_identity,
            'reference':reference,'profile':copy.deepcopy(runtime.profile),'n_actions':len(commands),
            'n_boundaries':len(boundaries),'model_identity':runtime.physics.model_identity,
            'model_parameters_identity':runtime.physics.model_parameters_identity,
            'world_id':snapshots[0]['world_id'],'reset_epoch':snapshots[0]['reset_epoch'],
                'quality':quality,'quality_policy':quality_policy,
                'demonstration_eligibility':'review_required' if quality_policy=='evidence-review-v1' else 'legacy_technical_gate',
                'physical_success':physical_success,
                'telemetry_purpose':'required_existing_Raw_streams_and_explicit_reference_diagnostics',
                'terminal_before_reset':True,'renderer_created':False,'renderer_calls':0,
            'backend':{'physics':runtime.physics.backend,'controller':'original model_2000','controller_device':str(runtime.core.device),
                'resources':runtime.physics.resource_profile,'asset_profile':copy.deepcopy(runtime.profile),
                'model_parameters_identity':runtime.physics.model_parameters_identity,
                'effective_physics_options':runtime.physics.backend_options,
                'case_seed':scene['seed'],'random_streams':runtime.core.case_rng.identity(),
                'motor_lags_physics_ticks':runtime.core.motor.lags.cpu().tolist(),
                'environment':{n:importlib.metadata.version(n) for n in ('mujoco','mujoco-warp','warp-lang','torch','qpth','numpy','av')}},
            'performance':{'physics_capture_wall_s':elapsed,'trace_write_s':time.monotonic()-started-elapsed,
                'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,'peak_torch_vram_bytes':peak_vram,
                'state_transfer':copy.deepcopy(runtime.physics.transfer_metrics),'runtime_breakdown_s':dict(runtime.timing)},
            'files':{p.name:sha(p) for p in partial.iterdir() if p.is_file()}}
        write_json(partial/'manifest.json',manifest);verify_trace(partial);partial.rename(output)
        return {'passed':True,'trace':str(output),'trace_sha256':sha(output/'manifest.json'),
            'n_actions':len(commands),'wall_s':time.monotonic()-started,'quality':quality}
    except CandidateRejected as error:
        terminal=runtime.abort('template_cannot_continue')
        return {'passed':False,'stage':'physics','reason':str(error),
            'outcome':copy.deepcopy(runtime.outcome),'termination':'template_cannot_continue',
            'completed_commands':len(commands),'wall_s':time.monotonic()-started}
    finally:
        runtime.on_physics=None;runtime.on_control=None;runtime.on_observation=None


def verify_trace(path):
    path=Path(path);m=json.loads((path/'manifest.json').read_text())
    if m.get('schema')!='qlm-physical-trace-v1' or m.get('passed') is not True:
        raise ValueError('Only actual successful physical traces admitted')
    backend=m.get('backend',{});kind=backend.get('physics')
    if kind=='native':
        options=backend.get('effective_physics_options',{})
        if m.get('batch_identity',{}).get('native_trace_profile')!='native-cpu-original-rambo-v1' or backend.get('controller_device')!='cpu' or options.get('device')!='cpu' or options.get('backend')!='native' or options.get('precision')!='float64':
            raise ValueError('Explicit qualified Native CPU/controller profile required')
    elif kind!='mjwarp':raise ValueError('Unknown physical backend')
    for name,expected in m['files'].items():
        if Path(name).name!=name or sha(path/name)!=expected:raise ValueError('Trace inventory mismatch')
    with np.load(path/'render_snapshots.npz',allow_pickle=False) as z:
        arrays={k:z[k].copy() for k in z.files}
    n=m['n_actions']
    if n<1 or m['n_boundaries']!=n+1 or not np.array_equal(arrays['physics_step'],np.arange(n+1)*10):
        raise ValueError('Trace action/boundary clock mismatch')
    if not np.array_equal(arrays['simulation_time_ns'],arrays['physics_step']*2_000_000):raise ValueError('Trace timestamp drift')
    if any(len(a)!=n+1 or not np.isfinite(a).all() for a in arrays.values()):raise ValueError('Incomplete/nonfinite trace arrays')
    commands=[json.loads(s) for s in (path/'commands.jsonl').read_text().splitlines()]
    with gzip.open(path/'telemetry.json.gz','rt') as f:telemetry=json.load(f)
    terminal=json.loads((path/'terminal.json').read_text())
    if len(commands)!=n or len(telemetry['boundaries'])!=n+1 or len(telemetry['physics'])!=n*10+1 or len(telemetry['controller'])!=n*2:
        raise ValueError('Missing full-rate trace telemetry')
    if not terminal['success'] or terminal['fallen'] or terminal['partial_interval'] or terminal['physics_step']!=n*10:
        raise ValueError('Trace has no valid task-success terminal')
    for i,c in enumerate(commands):
        if c['status']!='completed' or c['start_tick']!=i*10 or c['end_tick']!=(i+1)*10 or any(c['executed'][6:]):
            raise ValueError('Invalid trace executed commands')
    return m,arrays,telemetry,commands,terminal
