"""Non-task Native/CUDA contact/rebound/reset checks for approved wall-mounted buttons."""
import argparse
import json
import os
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

import mujoco
import numpy as np

from qlm_bench.backends.mujoco.physics import MuJoCoPhysics
from qlm_bench.backends.mujoco.resources import resource_closure, file_hash
from qlm_bench.backends.mujoco.trace import write_json


def prepare(model, output):
    model = Path(model).resolve(); output = Path(output)
    parent = resource_closure(model, require_portable=True)
    shutil.copytree(model.parent, output, copy_function=os.link)
    tree = ET.parse(model); world = tree.getroot().find('worldbody')
    compiled = mujoco.MjModel.from_xml_path(str(model))
    radius = float(compiled.geom('FL').size[0])
    body = ET.SubElement(world, 'body', name='diagnostic_striker', pos='-2 3 .4')
    ET.SubElement(body, 'freejoint', name='diagnostic_striker_free')
    moment = 2 / 5 * .5 * radius**2
    ET.SubElement(body, 'inertial', pos='0 0 0', mass='.5', diaginertia=' '.join([str(moment)] * 3))
    ET.SubElement(body, 'geom', name='diagnostic_striker_geom', type='sphere', size=str(radius),
        rgba='.1 .7 .9 1', contype='1', conaffinity='6', friction='1 0 0', condim='3')
    profile = json.loads(model.with_suffix('.task.json').read_text())
    profile.update(kind='non_task_asset_qualification_not_demonstration', work_id='QLM-SIM-016',
        qualification_parent_identity=parent['identity'],
        qualification='Only predefined initial states and free-striker velocity; no applied force or object teleport during run')
    for name in ('scene.xml', 'scene.task.json', 'resource-manifest.json'):
        (output / name).unlink()
    ET.indent(tree); tree.write(output / 'scene.xml', encoding='unicode')
    write_json(output / 'scene.task.json', profile)
    files = {str(p.relative_to(output)): {'sha256': file_hash(p), 'size_bytes': p.stat().st_size}
             for p in sorted(output.rglob('*')) if p.is_file() and p.name != 'resource-manifest.json'}
    write_json(output / 'resource-manifest.json', {'schema': 'qlm-portable-mujoco-resource-v1',
        'entrypoint': 'scene.xml', 'files': files})
    if resource_closure(model, require_portable=True)['identity'] != parent['identity']:
        raise ValueError('Original asset profile changed')
    return output / 'scene.xml'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('model', 'fixture', 'output'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--backend', choices=('native', 'mjwarp'), default='native')
    args = parser.parse_args()
    if args.prepare:
        prepare(args.model, args.fixture)
    out = Path(args.output); out.mkdir(parents=True, exist_ok=False)
    profile = json.loads(Path(args.fixture).joinpath('scene.task.json').read_text())
    write_json(out / 'attempt.json', {'work_id': 'QLM-SIM-016', 'kind': 'actual_non_task_asset_physics_diagnostic',
        'backend': args.backend, 'model': args.model, 'fixture': args.fixture,
        'entry_sha256': file_hash(__file__), 'formal_demonstration': False,
        'applied_force': False, 'teleport_during_execution': False})
    physics = MuJoCoPhysics(Path(args.fixture) / 'scene.xml', count=2, backend=args.backend)
    m = physics.model; cap = int(m.joint('button_slide').qposadr[0])
    striker_q = int(m.joint('diagnostic_striker_free').qposadr[0])
    striker_v = int(m.joint('diagnostic_striker_free').dofadr[0])
    striker_geom = int(m.geom('diagnostic_striker_geom').id); wall_geom = int(m.geom('press_wall').id)
    cap_body = int(m.body('primary').id); rows = []; reports = {}
    initial_qpos = physics.snapshot(0)['qpos'].copy()

    def state(index, displacement=0., impact=None):
        snap = physics.snapshot(index)
        q = initial_qpos.copy(); v = np.zeros(m.nv); q[cap] = displacement
        q[:3] = [-2, 2, .4]
        if impact == 'cap':
            x, y, z = profile['button_rest_front_xyz']
            q[striker_q:striker_q+3] = [x - .07, y, z + .01]
            v[striker_v:striker_v+3] = [.6, 0., .3]
        elif impact in ('wall', 'wall_highspeed'):
            x = profile['environment_profile']['wall']['front_x_m']
            q[striker_q:striker_q+3] = [x - .07, 1., .31]
            # Normal collision test and separate high-speed source-compliance stress.
            v[striker_v:striker_v+3] = [.15, 0., 1.4] if impact == 'wall' else [.6, 0., .3]
        else:
            q[striker_q:striker_q+3] = [-2, 3, .4]
        return {'schema': 'qlm-mujoco-initial-state-v1', 'model_identity': physics.model_identity,
                'qpos': q.tolist(), 'qvel': v.tolist()}

    try:
        assert np.allclose(m.joint('button_slide').range, [0, .02])
        assert np.allclose(m.actuator('button_spring').gainprm, 0)
        assert np.allclose(m.actuator('button_spring').biasprm[:3], [0, -300, -8])
        assert m.neq == 0
        for mode in ('rest_rebound', 'cap_contact', 'wall_contact', 'wall_highspeed'):
            impact = 'cap' if mode == 'cap_contact' else 'wall' if mode == 'wall_contact' else 'wall_highspeed' if mode == 'wall_highspeed' else None
            states = {0: state(0, impact=impact),
                      1: state(1, displacement=.016)}
            write_json(out / (mode + '-initial-states.json'), states)
            physics.reset(initial_states=states)
            displacement = [[], []]; contacts = 0; max_striker_x = -float('inf')
            for step in range(300):
                physics.step(np.zeros((2, 12), np.float32))
                d = physics.data[0]
                for i in range(2):
                    displacement[i].append(float(physics.data[i].qpos[cap]))
                    assert np.all(physics.data[i].qfrc_applied == 0) and np.all(physics.data[i].xfrc_applied == 0)
                max_striker_x = max(max_striker_x, float(d.qpos[striker_q]))
                relevant = []
                for c in d.contact[:d.ncon]:
                    g1, g2 = map(int, c.geom)
                    hit = striker_geom in (g1, g2) and ((mode == 'cap_contact' and cap_body in (int(m.geom_bodyid[g1]), int(m.geom_bodyid[g2])))
                        or (mode in ('wall_contact', 'wall_highspeed') and wall_geom in (g1, g2)))
                    if hit:
                        relevant.append([g1, g2])
                contacts += bool(relevant)
                if step % 10 == 9:
                    rows.append({'mode': mode, 'physics_step': step+1,
                        'simulation_time_ns': int(physics.ticks[0])*2_000_000,
                        'cap_displacement_m': displacement[0][-1], 'rebound_displacement_m': displacement[1][-1],
                        'striker_x_m': float(d.qpos[striker_q]), 'contact_pairs': relevant})
            peak = max(displacement[0]); low = min(displacement[0])
            assert abs(displacement[1][-1]) < 1e-5, 'Passive spring did not rebound'
            assert -.001 <= low and peak <= .021, 'Mechanism exceeds declared stroke tolerance'
            if mode == 'rest_rebound':
                assert max(abs(x) for x in displacement[0]) < 1e-7, 'Unforced cap drift'
            elif mode == 'cap_contact':
                assert contacts > 0 and peak > .003, 'No true-contact button motion'
            else:
                assert contacts > 0, 'Wall is not a real collision surface'
                radius = float(m.geom('FL').size[0])
                bound = .003 if mode == 'wall_contact' else radius / 2
                # Half-radius penetration bound rejects tunnelling without treating
                # the retained 20ms compliant contact as an infinitely rigid surface.
                penetration = max(0., max_striker_x + radius - profile['environment_profile']['wall']['front_x_m'])
                assert penetration <= bound, 'Wall penetration exceeds the declared speed-specific bound'
            reports[mode] = {'passed': True, 'contact_physics_ticks': contacts, 'peak_displacement_m': peak,
                'minimum_displacement_m': low, 'rebound_final_m': displacement[1][-1],
                'cap_final_m': displacement[0][-1], 'max_striker_x_m': max_striker_x}
            if mode in ('wall_contact', 'wall_highspeed'):
                reports[mode].update(maximum_wall_penetration_m=penetration,
                    penetration_bound_m=bound, initial_x_velocity_m_s=.15 if mode == 'wall_contact' else .6,
                    contact_solref_s=float(m.geom_solref[wall_geom, 0]))
            print(args.backend, profile['asset_id'], mode, reports[mode], flush=True)
        # Reset selected lane at zero time, while preserving the other lane.
        other = physics.snapshot(0)
        requested = state(1, displacement=.016); requested['qpos'][:3] = [0, 0, .4]
        physics.reset([1], initial_states={1: requested})
        after = physics.snapshot(0)
        for key in ('qpos', 'qvel', 'physics_step', 'simulation_time_ns', 'time'):
            np.testing.assert_array_equal(other[key], after[key])
        snap = physics.snapshot(1)
        assert snap['physics_step'] == 0 and snap['simulation_time_ns'] == 0
        np.testing.assert_allclose(snap['qpos'], requested['qpos'], atol=1e-7, rtol=0)
        from qlm_bench.backends.mujoco.render import RenderMirror
        from PIL import Image
        mirror = RenderMirror(Path(args.fixture) / 'scene.xml', world_id=1, rgb_profile='dual-rgb-360p-v1')
        try:
            frame = mirror.capture(snap)
            assert frame['mirror_physics_advanced'] is False
            np.testing.assert_array_equal(mirror.data.qpos, snap['qpos'])
            np.testing.assert_allclose(mirror.data.qpos[cap], .016, atol=1e-7, rtol=0)
            Image.fromarray(frame['rgb']['d435i_rgb_task']).save(out / 'reset-articulation-task.png')
        finally:
            mirror.close()
        physics.assert_frozen_model(full=True)
        write_json(out / 'rows.json', rows)
        write_json(out / 'result.json', {'passed': True, 'work_id': 'QLM-SIM-016', 'backend': args.backend,
            'asset_id': profile['asset_id'], 'model_identity': physics.model_identity,
            'parent_resource_identity': profile['qualification_parent_identity'],
            'reports': reports, 'selected_lane_reset_at_zero_time': True, 'other_lane_unchanged': True,
            'mirror_complete_articulation': True, 'mirror_physics_advanced': False,
            'no_object_teleport_or_applied_force_during_execution': True,
            'task_or_demonstration_success_claim': False, 'RAMBO_execution': 'separate nominal task attempt',
            'backend_options': physics.backend_options})
    except BaseException as error:
        write_json(out / 'failure.json', {'passed': False, 'error': str(error), 'completed_gates': reports,
            'kind': 'failed_non_task_diagnostic_not_candidate_demonstration'})
        write_json(out / 'partial-rows.json', rows)
        raise
    finally:
        physics.close()


if __name__ == '__main__':
    main()
