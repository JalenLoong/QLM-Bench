"""Reference-only full-state offline media review; no physics or controller owner."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
import time

import mujoco
import numpy as np
from PIL import Image

from qlm_bench.backends.mujoco.render import RenderMirror
from qlm_bench.backends.mujoco.trace import SNAPSHOT_ARRAYS, sha, verify_trace, write_json
from qlm_bench.data.video_writer import VideoSink
from qlm_bench.compatibility.dataset_v2.finalization import finalize_video
from qlm_bench.compatibility.dataset_v2.media import MediaTools
from qlm_bench.compatibility.dataset_v2.validation import PROFILE
from qlm_bench.compatibility.rgb_profiles import dataset_profile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('trace', 'model', 'output', 'ffmpeg', 'ffprobe'):
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args()
    manifest, arrays, telemetry, commands, terminal = verify_trace(args.trace)
    if not manifest['reference'] or manifest['profile']['task_id'] != 'press_button':
        raise ValueError('Only explicit Press reference evidence is admitted')
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    mirror = RenderMirror(args.model, world_id=manifest['world_id'], rgb_profile='dual-rgb-360p-v1')
    if mirror.identity != manifest['model_identity']:
        mirror.close()
        raise ValueError('Reference resource identity differs')
    sinks = {}; rows = []; images = {}; timings = Counter(); started = time.monotonic()
    phases = Counter(c['extensions']['expert']['phase'] for c in commands)
    selected = {0, manifest['n_actions']}
    selected.update(next(i for i, c in enumerate(commands) if c['extensions']['expert']['phase'] == p)
                    for p in phases)
    joint = mirror.model.joint('button_slide')
    qadr = int(joint.qposadr[0])
    cap_body = int(mirror.model.body('primary').id)
    static_body = int(mirror.model.body('task_static').id)
    wall_geom = mujoco.mj_name2id(mirror.model, mujoco.mjtObj.mjOBJ_GEOM, 'press_wall')
    foot_geom = int(mirror.model.geom('FL').id)
    contact_counts = Counter()
    source_files = {Path(args.trace) / name: sha(Path(args.trace) / name) for name in manifest['files']}
    try:
        for role, fps in [('ego', 50), ('task_centric', 50), ('observer', 25)]:
            sinks[role] = VideoSink(output / 'cameras' / (role + '.mp4'), args.ffmpeg, fps,
                rgb_profile='dual-rgb-720p-v1' if role == 'observer' else 'dual-rgb-360p-v1')
        for i, boundary in enumerate(telemetry['boundaries']):
            snapshot = {k: arrays[k][i].copy() for k in SNAPSHOT_ARRAYS}
            snapshot.update(model_identity=manifest['model_identity'],
                model_parameters_identity=manifest['model_parameters_identity'],
                world_id=manifest['world_id'], reset_epoch=manifest['reset_epoch'],
                physics_step=int(arrays['physics_step'][i]), simulation_time_ns=int(arrays['simulation_time_ns'][i]),
                time=float(arrays['time'][i]))
            frame = mirror.capture(snapshot, terminal=i == manifest['n_actions'])
            assert not frame['mirror_physics_advanced']
            timings.update(frame['timing_s'])
            rgb = {'ego': frame['rgb']['go2_ego'], 'task_centric': frame['rgb']['d435i_rgb_task']}
            if frame['observer_rgb'] is not None:
                rgb['observer'] = frame['observer_rgb']
            for role, image in rgb.items():
                if role != 'observer' or snapshot['physics_step'] % 20 == 0:
                    sinks[role].write(image)
                if i in selected:
                    dest = output / 'review_frames' / f'{i:06d}-{role}.png'
                    dest.parent.mkdir(exist_ok=True)
                    Image.fromarray(image).save(dest)
                if i == manifest['n_actions']:
                    dest = output / 'terminal' / (role + '.png'); dest.parent.mkdir(exist_ok=True)
                    Image.fromarray(image).save(dest); images[role] = {'path': str(dest), 'sha256': sha(dest)}
            pairs = []; environment_pairs = []
            for contact in mirror.data.contact[:mirror.data.ncon]:
                g1, g2 = map(int, contact.geom)
                bodies = (int(mirror.model.geom_bodyid[g1]), int(mirror.model.geom_bodyid[g2]))
                if wall_geom in (g1, g2) or static_body in bodies:
                    environment_pairs.append({'geoms': [mujoco.mj_id2name(mirror.model, mujoco.mjtObj.mjOBJ_GEOM, g) or f'geom{g}' for g in (g1, g2)],
                        'distance_m': float(contact.dist), 'wall': wall_geom in (g1, g2)})
                if cap_body not in (int(mirror.model.geom_bodyid[g1]), int(mirror.model.geom_bodyid[g2])):
                    continue
                pair = [mujoco.mj_id2name(mirror.model, mujoco.mjtObj.mjOBJ_GEOM, g) or f'geom{g}' for g in (g1, g2)]
                pairs.append({'geoms': pair, 'distance_m': float(contact.dist), 'FL': foot_geom in (g1, g2)})
            contact_counts['FL_cap_boundaries'] += any(p['FL'] for p in pairs)
            contact_counts['other_geom_cap_boundaries'] += any(not p['FL'] for p in pairs)
            contact_counts['wall_contact_boundaries'] += any(p['wall'] for p in environment_pairs)
            contact_counts['housing_contact_boundaries'] += any(not p['wall'] for p in environment_pairs)
            rows.append({'boundary': i, 'simulation_time_ns': boundary['simulation_time_ns'],
                'button_displacement_m': float(arrays['qpos'][i, qadr]),
                'captured_runtime_contact': boundary['contact'],
                'contact_geometry_at_actual_snapshot': pairs,
                'environment_contact_geometry_at_actual_snapshot': environment_pairs,
                'contact_geometry_scope': 'Native collision at captured CUDA state, not CUDA force telemetry',
                'physical_FL_world': mirror.data.geom_xpos[foot_geom].tolist()})
            if i % 100 == 0:
                print(f'Reference rendering: {i}/{manifest["n_actions"]}', flush=True)
        videos = {role: sink.close() for role, sink in sinks.items()}; sinks = {}
        tools = MediaTools(args.ffmpeg, args.ffprobe)
        policy_profile = dataset_profile(PROFILE, 'dual-rgb-360p-v1')['policy_video']
        media_validation = {}
        for role, video in videos.items():
            media_validation[role] = finalize_video(video['partial'], video['final'],
                count=video['count'], fps=25 if role == 'observer' else 50, tools=tools,
                profile=None if role == 'observer' else policy_profile,
                receipt=video['receipt'])
            if media_validation[role]['episode_status'] != 'video_validated':
                raise ValueError('Full reference media validation failed: ' + role)
        write_json(output / 'state-contact-review.json', rows)
        commanded = np.array([c['filtered'] for c in commands])
        actual = np.array([r['physical_FL_world'] for r in rows])
        deltas = np.linalg.norm(np.diff(actual, axis=0), axis=1)
        quality = {'task_outcome': terminal['outcome'] if 'outcome' in terminal else terminal,
            'quality_separate_from_success': True, 'eligibility': 'user_review_required',
            'unknown_contact_is_failure': False, 'snapshot_contact_geometry_counts': dict(contact_counts),
            'snapshot_contact_geometry_scope': 'not independent actual CUDA contact-force measurement',
            'phase_actions': dict(phases), 'maximum_actual_FL_boundary_step_m': float(deltas.max()),
            'p95_actual_FL_boundary_step_m': float(np.percentile(deltas, 95)),
            'max_native9_component_steps': np.abs(np.diff(commanded, axis=0)).max(axis=0).tolist(),
            'force_zero': bool(np.all(commanded[:, 6:] == 0)),
            'button_displacement_final_m': rows[-1]['button_displacement_m']}
        write_json(output / 'quality.json', quality)
        assert all(sha(path) == expected for path, expected in source_files.items())
        forbidden = any(x in sys.modules for x in ('qlm_bench.backends.mujoco.physics', 'qlm_bench.backends.mujoco.runtime'))
        forbidden |= any(x.startswith(('qlm_bench.controllers', 'wam_policy')) for x in sys.modules)
        assert not forbidden
        write_json(output / 'result.json', {'passed': True, 'reference_only': True, 'formal_pilot': False,
            'recording_entry_sha256': sha(__file__),
            'source_trace_manifest_sha256': sha(Path(args.trace) / 'manifest.json'),
            'source_trace_unchanged': True, 'model_identity': mirror.identity,
            'snapshot_count': len(rows), 'physics_reexecuted': False, 'mirror_physics_advanced': False,
            'physics_owner_controller_WAM_loaded': False, 'rgb_profile': 'dual-rgb-360p-v1',
            'videos': videos, 'media_validation': media_validation,
            'terminal_images': images, 'timings_s': dict(timings),
            'wall_s': time.monotonic() - started, 'GL': mirror.gl_identity})
    finally:
        for sink in sinks.values():
            sink.close()
        mirror.close()


if __name__ == '__main__':
    main()
