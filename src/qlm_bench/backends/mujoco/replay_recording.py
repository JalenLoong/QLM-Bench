"""Offline recorded-state RGB/Raw/Canonical production; no controller or stepping."""
import copy
import json
from pathlib import Path
import shutil
import sys
import time

import numpy as np

from .trace import verify_trace,sha,write_json,SNAPSHOT_ARRAYS
from qlm_bench.compatibility.dataset_v2.validation import digest


def record_trace(trace,model,output,*,episode_uid,ffmpeg,ffprobe,formal=False,metadata=None,batch_source=None,rgb_profile="dual-rgb-360p-v1",recording_profile_path=None):
    manifest,arrays,telemetry,commands,terminal=verify_trace(trace)
    recording_profile=None;slot=None;physical_audit=None
    if recording_profile_path is not None:
        from qlm_bench.compatibility.dataset_v2.pilot_rendition import load_profile,slot_for
        from .rendition import validate_slot_inputs,RecordingIntegrityError
        recording_profile=load_profile(recording_profile_path);slot=slot_for(recording_profile,episode_uid)
        physical_audit=validate_slot_inputs(recording_profile,episode_uid)
        if Path(trace).resolve()!=Path(slot['trace']).resolve() or Path(model).resolve()!=Path(slot['model']).resolve() or rgb_profile!=recording_profile['rgb_profile']:
            raise RecordingIntegrityError('Recorder input differs from frozen rendition slot')
        if not formal or not metadata or any(metadata.get(k)!=slot[k] for k in ('episode_uid','task_id','difficulty','split')):
            raise RecordingIntegrityError('Explicit admitted formal metadata required')
    model=Path(model);output=Path(output)
    if output.exists():raise FileExistsError(output)
    output.mkdir(parents=True);raw=output/'raw'/episode_uid;raw.mkdir(parents=True)
    if formal and (not metadata or metadata.get('split')!='train' or metadata.get('episode_uid')!=episode_uid):
        raise ValueError('Explicit formal pilot slot/all-train metadata required')
    from .render import RenderMirror
    from qlm_bench.data.video_writer import VideoSink
    from qlm_bench.compatibility.dataset_v2.conversion import convert
    mirror=RenderMirror(model,world_id=manifest['world_id'],rgb_profile=rgb_profile)
    if mirror.identity!=manifest['model_identity']:
        mirror.close();raise ValueError('Offline resource differs from successful trace')
    started=time.monotonic();sinks={};indices=[];captures=[];write_s=0.;mirror_s=0.;render_s=0.
    videos={};last=None;source_rgb_hashes=[];review_frames=[]
    contact_indices=[i for i,b in enumerate(telemetry['boundaries']) if b['contact'].get('fl_object')]
    phase_indices=[i for i,c in enumerate(commands) if c['extensions']['expert'].get('phase')=='straight_push']
    selected=sorted(set([0,manifest['n_actions']] +
        ([contact_indices[0],contact_indices[len(contact_indices)//2]] if contact_indices else []) +
        ([phase_indices[0]] if phase_indices else [])))
    try:
        for role,fps in [('ego',50),('task_centric',50),('observer',25)]:
            if role=='observer' and mirror.observer_clip is None:continue
            sinks[role]=VideoSink(raw/'cameras'/f'{role}.mp4',ffmpeg,fps,rgb_profile='dual-rgb-720p-v1' if role=='observer' else rgb_profile)
        for i,boundary in enumerate(telemetry['boundaries']):
            snapshot={k:arrays[k][i].copy() for k in SNAPSHOT_ARRAYS}
            snapshot.update(model_identity=manifest['model_identity'],model_parameters_identity=manifest['model_parameters_identity'],
                world_id=manifest['world_id'],reset_epoch=manifest['reset_epoch'],physics_step=int(arrays['physics_step'][i]),
                simulation_time_ns=int(arrays['simulation_time_ns'][i]),time=float(arrays['time'][i]))
            last=mirror.capture(snapshot,terminal=i==manifest['n_actions'])
            mirror_s+=last['timing_s']['mirror_refresh'];render_s+=last['timing_s']['render_readback']
            row=copy.deepcopy(boundary);row['rgb_hashes']={};row['sensor_frame_ids']={}
            import hashlib
            for role,key in [('ego','go2_ego'),('task_centric','d435i_rgb_task')]:
                rgb=last['rgb'][key];row['rgb_hashes'][role]=hashlib.sha256(rgb.tobytes()).hexdigest()
                row['sensor_frame_ids'][role]=i
                before=time.monotonic();sinks[role].write(rgb);write_s+=time.monotonic()-before
                indices.append(dict(camera_key='observation.images.'+role,frame_index=i,
                    simulation_time_ns=row['simulation_time_ns'],physics_step=row['physics_step'],valid=True))
            source_rgb_hashes.append(row['rgb_hashes']);captures.append(row)
            if i in selected:
                from PIL import Image
                for role,key in [('ego','go2_ego'),('task_centric','d435i_rgb_task')]:
                    dest=output/'review_frames'/f'{i:06d}-{role}.png';dest.parent.mkdir(parents=True,exist_ok=True)
                    Image.fromarray(last['rgb'][key]).save(dest)
                    review_frames.append({'boundary':i,'role':role,'path':str(dest.relative_to(output)),
                        'sha256':sha(dest),'simulation_time_ns':row['simulation_time_ns'],'actual_state':row['state']})
                if last['observer_rgb'] is not None:
                    dest=output/'review_frames'/f'{i:06d}-observer.png';Image.fromarray(last['observer_rgb']).save(dest)
                    review_frames.append({'boundary':i,'role':'observer','path':str(dest.relative_to(output)),
                        'sha256':sha(dest),'simulation_time_ns':row['simulation_time_ns'],'actual_state':row['state']})
            if last['observer_rgb'] is not None and row['physics_step']%20==0:
                before=time.monotonic();sinks['observer'].write(last['observer_rgb']);write_s+=time.monotonic()-before
                indices.append(dict(camera_key='monitor.images.observer',frame_index=sinks['observer'].count-1,
                    simulation_time_ns=row['simulation_time_ns'],physics_step=row['physics_step'],valid=True))
            if i%100==0:print(f'Render {episode_uid}: {i}/{manifest["n_actions"]}',flush=True)
        terminal=copy.deepcopy(terminal);terminal.pop('physical_snapshot',None)
        terminal['rgb_hashes']=captures[-1]['rgb_hashes'];terminal['sensor_frame_ids']=captures[-1]['sensor_frame_ids']
        terminal['actual_images']={}
        from PIL import Image
        images={'ego':last['rgb']['go2_ego'],'task_centric':last['rgb']['d435i_rgb_task']}
        if last['observer_rgb'] is not None:images['observer']=last['observer_rgb']
        for role,image in images.items():
            dest=raw/'terminal'/f'{role}.png';dest.parent.mkdir(parents=True,exist_ok=True);Image.fromarray(image).save(dest)
            terminal['actual_images'][role]={'path':str(dest.relative_to(raw)),'sha256':sha(dest)}
        for role,sink in sinks.items():videos[role]=sink.close()
        sinks={}
        profile=copy.deepcopy(manifest['profile'].get('source_profile',{}))
        profile.update(task_profile_version='mujoco-push_box-runtime-v1',goal_x=manifest['profile']['goal_x'],
            goal_y=manifest['profile']['goal_y'],canonical_goal_position=manifest['profile']['canonical_goal_position'],
            asset_id=manifest['profile']['asset_id'],asset_sha256=manifest['model_identity'])
        backend={**manifest['backend'],'render':'osmesa','GL':mirror.gl_identity,'recording_mode':'offline_state_replay'}
        # An old physical execution must never acquire the new recorder's source label.
        source=copy.deepcopy(manifest['batch_identity'])
        lineage=None
        if recording_profile is not None:
            lineage={'schema':'qlm-physical-recording-lineage-v1',
                'physical':{'manifest_sha256':physical_audit['manifest_sha256'],
                    'trajectory_sha256':physical_audit['trajectory_sha256'],
                    'source_identity_sha256':physical_audit['source_identity_sha256'],
                    'model_identity':manifest['model_identity'],'world_id':manifest['world_id'],
                    'reset_epoch':manifest['reset_epoch'],'quality':physical_audit['quality'],
                    'template_id':source['template_id'],'template_sha256':source['template_sha256']},
                'recording':{'profile_sha256':recording_profile['profile_sha256'],'profile_id':recording_profile['profile_id'],
                    'rendition_id':slot['rendition_id'],'rgb_profile':rgb_profile,
                    'source_identity':recording_profile['recording_source'],
                    'source_identity_sha256':digest(recording_profile['recording_source']),
                    'physics_reexecuted':False,'controller_executed':False,'renderer':'native-osmesa',
                    'physical_demo_count':1,'GL':mirror.gl_identity}}
        cap=dict(rgb_spatial_profile=rgb_profile,boundaries=captures,commands=commands,controller=telemetry['controller'],physics=telemetry['physics'],
            contact_sensor=telemetry['contact_sensor'],camera_index=indices,terminal=terminal,videos=videos,
            profile=profile,task_text=manifest['profile']['instruction'],
            checkpoint_sha256='1cc5f68fe15e37ccabae26060d79a26a8c078ed465a81f6f729c2009b67ca706',
            implementation=source.get('implementation',{}),source_commit=source.get('source_commit','unavailable'),
            source_identity=source,diagnostic_only=not formal,mode='formal_pilot_offline_state_replay' if formal else 'engineering_offline_state_replay',
            work_id=recording_profile['work_id'] if recording_profile is not None else 'QLM-DATA-011',reset_epoch=manifest['reset_epoch'],task_id='push_box',status='success',
            initial_geometry={'source':'actual_captured_state','state':captures[0]['state']},backend=backend,
            recording_mode='offline_state_replay',physical_trace={'manifest_sha256':sha(Path(trace)/'manifest.json'),
                'candidate_id':manifest['scene']['candidate_id']},formal_metadata=metadata)
        if lineage is not None:cap['recording_lineage']=lineage
        write_json(raw/'capture.json',cap)
        write_json(raw/'summary.json',{'passed':True,'terminal_before_reset':True,'partial_interval':False,
            'physical_success':True,'recording_mode':'offline_state_replay','formal_pilot':formal})
        packaging_start=time.monotonic();result=convert(raw,output/'canonical',ffmpeg=ffmpeg,ffprobe=ffprobe)
        packaging_s=time.monotonic()-packaging_start
        write_json(output/'source-rgb-hashes.json',source_rgb_hashes)
        write_json(output/'producer.json',{'schema':'qlm-formal-pilot-producer-v1','episode_uid':episode_uid,
            'metadata':metadata,'recording_mode':'offline_state_replay','physical_trace':cap['physical_trace'],
            'scene':manifest['scene'],'source':source,'recording_lineage':lineage,'formal':formal,'passed':True})
        import resource
        report={'passed':True,'raw':result['raw'],'canonical':result['canonical'],
            'physics_reexecuted':False,'physics_owner_loaded':any(x in sys.modules for x in ('qlm_bench.backends.mujoco.physics','qlm_bench.backends.mujoco.runtime')),'controller_loaded':any(x.startswith('qlm_bench.controllers') for x in sys.modules),
            'WAM_loaded':any(x.startswith('wam_policy') for x in sys.modules),
            'n_actions':manifest['n_actions'],'n_boundaries':manifest['n_boundaries'],
            'wall_s':time.monotonic()-started,'mirror_refresh_s':mirror_s,'render_readback_s':render_s,
            'encoder_pipe_write_s':write_s,'export_validate_s':packaging_s,
            'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
            'bytes':sum(p.stat().st_size for p in output.rglob('*') if p.is_file()),'GL':mirror.gl_identity}
        if report['controller_loaded'] or report['WAM_loaded'] or report['physics_owner_loaded']:raise RuntimeError('Replay worker loaded a controller/model')
        write_json(output/'review-frames.json',review_frames)
        report.update(recording_profile_sha256=recording_profile['profile_sha256'] if recording_profile else None,
            rendition_id=slot['rendition_id'] if slot else None,mirror_physics_advanced=last['mirror_physics_advanced'])
        write_json(output/'result.json',report);return report
    finally:
        for sink in sinks.values():
            try:sink.close()
            except Exception:pass
        mirror.close()
