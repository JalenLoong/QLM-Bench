"""Approved bounded Push production: freeze candidates, actual physics, then rendition.

No online agent participates in per-candidate execution. Existing physical and
render-only queues own recovery. Task outcome and behavior review remain separate.
"""
import argparse
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import xml.etree.ElementTree as ET

import numpy as np
from qlm_bench.backends.mujoco.trace import sha, write_json, verify_trace
from qlm_bench.compatibility.dataset_v2.validation import digest

REPO = Path(__file__).resolve().parents[3]
WORKSPACE = REPO.parents[1]
LIMITS = np.array([.04, .035, .06, .03, .02])


def implementation():
    return {str(p.relative_to(REPO)): sha(p) for folder in ('src/qlm_bench', 'scripts/mujoco/synthesis')
            for p in sorted((REPO / folder).rglob('*')) if p.suffix in ('.py', '.json')}


def goal_variant(source, destination, dx, dy, *, work_id="QLM-DATA-015"):
    """Only translate contact-free visible goal and paired numerical goal."""
    import mujoco
    from qlm_bench.backends.mujoco.resources import resource_closure
    source, destination = Path(source), Path(destination)
    shutil.copytree(source.parent, destination, copy_function=os.link)
    for name in ('scene.xml', 'scene.task.json', 'resource-manifest.json'):
        (destination / name).unlink()
    tree = ET.parse(source); markers = []
    for geom in tree.getroot().iter('geom'):
        if geom.get('name', '').startswith('original_Goal_'):
            if int(geom.get('contype', '1')) or int(geom.get('conaffinity', '1')):
                raise ValueError('Goal marker has collision')
            pos = np.fromstring(geom.get('pos'), sep=' '); pos[:2] += [dx, dy]
            geom.set('pos', ' '.join(map(str, pos))); markers.append(geom.get('name'))
    if len(markers) != 4: raise ValueError('Expected four original goal markers')
    tree.write(destination / 'scene.xml', encoding='unicode')
    task = json.loads(source.with_suffix('.task.json').read_text())
    for target in (task, task['source_profile']):
        for key, shift in (('goal_x', dx), ('goal_y', dy)):
            if key in target: target[key] = [v + shift for v in target[key]]
        if 'canonical_goal_position' in target:
            target['canonical_goal_position'][:2] = [target['canonical_goal_position'][0] + dx, target['canonical_goal_position'][1] + dy]
    task['goal_variant'] = {'dx': dx, 'dy': dy, 'work_id': work_id}
    write_json(destination / 'scene.task.json', task)
    manifest = json.loads((source.parent / 'resource-manifest.json').read_text())
    for name in ('scene.xml', 'scene.task.json'):
        manifest['files'][name] = {'sha256': sha(destination / name), 'size_bytes': (destination / name).stat().st_size}
    write_json(destination / 'resource-manifest.json', manifest)
    a = mujoco.MjModel.from_xml_path(str(source)); b = mujoco.MjModel.from_xml_path(str(destination / 'scene.xml'))
    ids = [mujoco.mj_name2id(a, mujoco.mjtObj.mjOBJ_GEOM, n) for n in markers]
    expected = a.geom_pos.copy(); expected[ids, :2] += [dx, dy]
    np.testing.assert_allclose(b.geom_pos, expected, atol=1e-14, rtol=0)
    for name in dir(a):
        if name.startswith(('body_', 'jnt_', 'dof_', 'geom_', 'cam_', 'actuator_', 'eq_', 'mesh_')) and name != 'geom_pos':
            x, y = getattr(a, name), getattr(b, name)
            if isinstance(x, np.ndarray): np.testing.assert_array_equal(x, y, err_msg=name)
    return resource_closure(destination / 'scene.xml', require_portable=True)


def prepare(out):
    import mujoco
    from qlm_bench.backends.mujoco.resources import resource_closure
    approval = json.loads((out / 'approval.json').read_text())
    if not approval['reference_quality_approved'] or not approval['retarget_scope_approved']:
        raise ValueError('Reference and scope approval required')
    template_root = WORKSPACE / 'runs/audit/automated-push-synthesis-20261013-v1/template-development-v1'
    template = json.loads((template_root / 'template.json').read_text())
    # Stratified real configurations; failures retry inside the same small bin.
    centers = np.array([
        [.003, -.003, .005, .002, -.001], [-.003, .003, -.005, -.002, .001],
        [.04, .032, .055, 0, 0], [-.04, -.032, -.055, 0, 0],
        [.035, -.035, .06, 0, 0], [-.035, .035, -.06, 0, 0],
        [-.022, .023, .034, .03, -.02], [.023, -.022, -.034, -.03, .02],
        [.012, .026, -.045, .018, .014], [-.014, -.026, .045, -.018, -.014]])
    slots = []; rng = np.random.default_rng(2026101402)
    resources = out / 'resources'; resources.mkdir(exist_ok=False)
    for i, center in enumerate(centers):
        uid = f'push-approved-20261014-{i + 1:02d}'; preset = 'ap_00' if i < 2 or i % 2 == 0 else 'ap_01'
        source = WORKSPACE / f'assets/mujoco/push-two-backgrounds-20261014-v1/{preset}/scene.xml'
        closure = goal_variant(source, resources / uid, *center[3:])
        model = resources / uid / 'scene.xml'; task = json.loads(model.with_suffix('.task.json').read_text())
        compiled = mujoco.MjModel.from_xml_path(str(model))
        joint = mujoco.mj_name2id(compiled, mujoco.mjtObj.mjOBJ_JOINT, 'object_free')
        if joint < 0: raise ValueError('Original freejoint required')
        adr = int(compiled.jnt_qposadr[joint]); candidates = []
        for j in range(5):
            params = center.copy()
            if j: params[:3] += rng.uniform(-1, 1, 3) * ([.0005, .0005, .001] if i < 2 else [.002, .002, .003])
            params = np.clip(params, -LIMITS, LIMITS)
            scene = copy.deepcopy(template['source_scene']); initial = scene['initial_state']
            q = np.asarray(initial['qpos'], float); q[adr:adr + 2] += params[:2]
            dq = np.array([np.cos(params[2] / 2), 0, 0, np.sin(params[2] / 2)])
            rotated = np.empty(4); mujoco.mju_mulQuat(rotated, dq, q[adr + 3:adr + 7]); q[adr + 3:adr + 7] = rotated
            initial.update(qpos=q.tolist(), model_identity=closure['identity'])
            scene.update(candidate_id=f'{uid}-candidate-{j + 1:02d}', model=str(model), seed=140200 + i * 10 + j,
                         appearance_preset=preset, difficulty='clean' if i < 2 else 'randomized',
                         goal_x=task['goal_x'], goal_y=task['goal_y'], canonical_goal_position=task['canonical_goal_position'],
                         configuration_parameters=params.tolist(), configuration_sha256=digest(params.tolist()))
            candidates.append(scene)
        slots.append({'episode_uid': uid, 'task_id': 'push_box', 'difficulty': 'clean' if i < 2 else 'randomized',
                      'split': 'train', 'coverage_bin': i, 'candidates': candidates})
    configs = [c['configuration_sha256'] for s in slots for c in s['candidates']]
    if len(set(configs)) != len(configs): raise ValueError('Duplicate candidate configuration')
    source = {'work_id': 'QLM-DATA-015', 'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True).strip(),
              'implementation': implementation(), 'template_id': template['template_id'], 'template_sha256': sha(template_root / 'template.json'),
              'executor_variant': 'cross-track-smooth-v3', 'maximum_world_target_step_m': .008, 'approval_sha256': digest(approval)}
    profile = {'schema': 'qlm-approved-push-ten-pilot-v1', 'task_id': 'push_box', 'approval': approval,
               'source': source, 'template_root': str(template_root), 'template_sha256': source['template_sha256'],
               'slots': slots, 'scope_limits': LIMITS.tolist(), 'maximum_physics_attempts': 30, 'maximum_per_slot': 5,
               'maximum_consecutive_failures': 10, 'quality_policy': 'evidence-review-v1',
               'python': str(WORKSPACE / 'envs/qlm-mujoco-py312-v1/bin/python'),
               'ffmpeg': str(WORKSPACE / 'cache/tools/bin/ffmpeg'), 'ffprobe': str(WORKSPACE / 'cache/tools/bin/ffprobe'),
               'render_environment': {'LD_LIBRARY_PATH': str(WORKSPACE / 'assets/mujoco/p0-v1/osmesa/root/usr/lib/x86_64-linux-gnu'),
                                      'MESA_SHADER_CACHE_DIR': str(WORKSPACE / 'cache/mesa'), 'OMP_NUM_THREADS': '4', 'PYTHONPATH': str(REPO / 'src')}}
    profile['profile_sha256'] = digest(profile); write_json(out / 'physical-profile.json', profile)
    for name in source['implementation']:
        target = out / 'frozen-source' / name; target.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(REPO / name, target)
    print(json.dumps({'frozen_slots': 10, 'predeclared_candidates': 50, 'profile_sha256': profile['profile_sha256']}), flush=True)


def checked_profile(out):
    profile = json.loads((out / 'physical-profile.json').read_text())
    if digest({k: v for k, v in profile.items() if k != 'profile_sha256'}) != profile['profile_sha256']:
        raise ValueError('Physical profile changed')
    if implementation() != profile['source']['implementation']: raise ValueError('Frozen implementation changed')
    if sha(Path(profile['template_root']) / 'template.json') != profile['template_sha256']: raise ValueError('Template changed')
    return profile


def physics(out):
    import torch
    from qlm_bench.backends.mujoco.runtime import MuJoCoRuntime
    from qlm_bench.backends.mujoco.reference_retarget import ContactAwarePushExecutor
    from qlm_bench.backends.mujoco.synthesis_queue import PilotQueue
    from qlm_bench.backends.mujoco.trace import collect_trace
    from qlm_bench.backends.mujoco.quality import analyze_trace
    profile = checked_profile(out); torch.set_num_threads(1)
    executor = ContactAwarePushExecutor(profile['template_root'], working_y=.12, gain=1., maximum_world_step=.008)
    def run(scene, dest):
        checked_profile(out); start = time.monotonic()
        runtime = MuJoCoRuntime(scene['model'], str(WORKSPACE / 'checkpoints/rambo/go2/quadruped/model_2000.pt'), trace_only=True, seed=scene['seed'])
        try:
            if runtime.profile.get('appearance_preset', 'ap_00') != scene['appearance_preset']: raise ValueError('Background provenance mismatch')
            result = collect_trace(runtime, executor, scene, dest, batch_identity=profile['source'], quality_policy='evidence-review-v1')
            result['total_wall_s'] = time.monotonic() - start
            if result['passed']:
                quality, curves = analyze_trace(dest); write_json(out / 'quality' / (scene['candidate_id'] + '.json'), quality)
                print(json.dumps({'candidate': scene['candidate_id'], 'actions': result['n_actions'], 'quality': quality}), flush=True)
            else: print(json.dumps({'candidate': scene['candidate_id'], 'result': result}), flush=True)
            return result
        finally: runtime.close()
    with PilotQueue(out / 'physical', profile) as queue:
        queue.run(run, None, defer_render=True)
    print('Ten physical traces retained; no rendering or scale100 started', flush=True)


def freeze_rendition(out):
    from qlm_bench.backends.mujoco.rendition import audit_trace, validate_slot_inputs
    from qlm_bench.backends.mujoco.quality import analyze_trace
    from qlm_bench.compatibility.dataset_v2.pilot_rendition import load_profile
    old = checked_profile(out); queue = json.loads((out / 'physical/queue.json').read_text())
    profile = {k: copy.deepcopy(old[k]) for k in ('task_id', 'approval', 'quality_policy', 'template_root', 'template_sha256', 'python', 'ffmpeg', 'ffprobe', 'render_environment')}
    profile.update(schema='qlm-push-pilot-rendition-v1', profile_id='push-approved-ten-20261014-v2', work_id='QLM-DATA-015',
                   rgb_profile='dual-rgb-360p-v1', maximum_render_attempts=3, template_id=old['source']['template_id'],
                   recording_source={**old['source'], 'stage': 'offline-recording'}, render_script=str(REPO / 'scripts/mujoco/synthesis/render_trace.py'), slots=[])
    for declared in old['slots']:
        uid = declared['episode_uid']; row = queue['slots'][uid]
        if row['status'] != 'render_pending': raise ValueError('All ten physical slots required')
        trace = Path(row['trace']); audit = audit_trace(trace); m = verify_trace(trace)[0]; review, _ = analyze_trace(trace)
        # Conservative review holds, not task failure or universal learned-skill criteria.
        # Missing contact has no hard gate; measured body contact requests behavior inspection.
        flags = []
        if review['world_target_step_max_m'] is None or review['world_target_step_max_m'] > .00801: flags.append('world-target continuity')
        if review['push_body_midline_crossing_s'] > 0: flags.append('measured push midline crossing')
        if review['late_FL_hip_min_deg'] < -40: flags.append('posture outside reviewed reference neighborhood')
        if review['contact']['body_contact_boundaries'] > 0: flags.append('inspect actual body-contact behavior')
        if flags:
            write_json(out / (uid + '-behavior-review-hold.json'), {'task_success': True, 'flags': flags, 'evidence': review, 'automatic_SFT_rejection': False})
            raise ValueError('Actual behavior needs inspection before rendition admission: ' + uid)
        slot = {k: declared[k] for k in ('episode_uid', 'task_id', 'difficulty', 'split')}
        slot.update(trace=str(trace), model=m['scene']['model'], model_identity=m['model_identity'], physical_source_sha256=audit['source_identity_sha256'],
                    trace_manifest_sha256=audit['manifest_sha256'], physical_trajectory_sha256=audit['trajectory_sha256'], quality=audit['quality'],
                    quality_review_sha256=digest(review), review_status='eligible_for_ten_pilot_user_review', n_actions=m['n_actions'],
                    rendition_id=uid + '@dual-rgb-360p-v1', candidate_id=m['scene']['candidate_id'], asset_id=m['profile']['asset_id'],
                    appearance_preset=m['scene']['appearance_preset'], seed=m['scene']['seed'])
        profile['slots'].append(slot)
    profile['profile_sha256'] = digest(profile); path = out / 'recording-profile.json'
    if path.exists(): raise FileExistsError(path)
    write_json(path, profile); profile = load_profile(path)
    for s in profile['slots']: validate_slot_inputs(profile, s['episode_uid'])
    print(json.dumps({'passed': True, 'slots': 10, 'actions': sum(s['n_actions'] for s in profile['slots']), 'human_pilot_review': 'pending'}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('stage', choices=('prepare', 'physics', 'freeze-rendition')); parser.add_argument('--output', required=True)
    args = parser.parse_args(); {'prepare': prepare, 'physics': physics, 'freeze-rendition': freeze_rendition}[args.stage](Path(args.output).resolve())
