"""Prepare approved three-asset Press wall profiles without advancing physics."""
import argparse
import copy
import json
import os
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

import mujoco
import numpy as np

from build_original_robot import mesh_parts, numbers
from build_original_task import MaterialExporter
from qlm_bench.backends.mujoco.press_wall import WALL, convex_mass_properties, wall_mount_translation
from qlm_bench.backends.mujoco.resources import resource_closure, file_hash


def detached_write(path, text):
    # Shared immutable payloads are hardlinked; changed metadata/XML must detach first.
    if path.exists():
        path.unlink()
    path.write_text(text)


def build(parent_model, review_root, label, output, *, y=.1, z=.3):
    output = Path(output)
    if output.exists():
        raise FileExistsError(output)
    parent_model = Path(parent_model).resolve()
    parent = resource_closure(parent_model, require_portable=True)
    review = Path(review_root) / label
    candidate = json.loads((review / 'candidate.json').read_text())
    source_root = Path(candidate['source_root'])
    source_manifest = json.loads(Path(candidate['source_manifest']).read_text())
    verified_sources = {}
    for name, record in source_manifest['files'].items():
        path = source_root / name
        if path.stat().st_size != record['size_bytes'] or file_hash(path) != record['sha256']:
            raise ValueError('Approved asset source changed: ' + name)
        verified_sources[str(path.resolve())] = record['sha256']
    if source_manifest['license']['redistribution_status'] != 'verified_source_declaration':
        raise ValueError('Approved license declaration required')
    shutil.copytree(parent_model.parent, output, copy_function=os.link)
    tree = ET.parse(parent_model); xml = tree.getroot(); world = xml.find('worldbody')
    primary = world.find("body[@name='primary']"); static = world.find("body[@name='task_static']")
    profile = json.loads(parent_model.with_suffix('.task.json').read_text())
    before_model = mujoco.MjModel.from_xml_path(str(parent_model))
    cameras_before = {k: getattr(before_model, k).copy() for k in ('cam_pos', 'cam_quat', 'cam_fovy')}
    # The new whole wall replaces the original small mounting plate.
    for geom in list(world.findall('geom')):
        if geom.get('name', '').startswith('original_ButtonMount'):
            world.remove(geom)
    wall = copy.deepcopy(WALL)
    ET.SubElement(world, 'geom', name='press_wall', type='box',
        pos=numbers([wall['front_x_m'] + wall['thickness_m']/2, wall['center_y_m'], wall['height_m']/2]),
        size=numbers([wall['thickness_m']/2, wall['width_m']/2, wall['height_m']/2]),
        rgba='.52 .54 .56 1', contype='4', conaffinity='3', group='0',
        friction='1 0 0', condim='3', priority='1')
    bounds = candidate['actual_visual_bounds_m']
    translation = wall_mount_translation(bounds, y, z, wall)
    source_front = float(bounds[0][0])
    actual_front = translation[0] + source_front
    inertia = None
    if label in ('A', 'B'):
        old_position = np.array(list(map(float, primary.get('pos').split())))
        old_front = np.asarray(profile['button_rest_front_xyz'])
        delta = np.array([actual_front, y, z]) - old_front
        primary.set('pos', numbers(old_position + delta))
        static.set('pos', numbers(delta))
        if label == 'B':
            from PIL import Image
            cap_source = source_root / 'textures/cap-color.png'
            if str(cap_source.resolve()) not in verified_sources:
                raise ValueError('Verified source cap texture required')
            filename = 'approved_blue_cap_' + file_hash(cap_source)[:16] + '.png'
            Image.open(cap_source).convert('RGB').save(output / 'textures' / filename)
            mat = xml.find("asset/material[@name='task_mat_3']")
            rgb_name = next(layer.get('texture') for layer in mat.findall('layer') if layer.get('role') == 'rgb')
            xml.find(f"asset/texture[@name='{rgb_name}']").set('file', 'textures/' + filename)
    else:
        # Source Cap Mesh and Stem remain separate convex colliders, as in the Isaac wrapper.
        for child in list(primary):
            primary.remove(child)
        for child in list(static):
            static.remove(child)
        primary.set('pos', numbers(translation)); primary.set('quat', '1 0 0 0')
        static.set('pos', numbers(translation))
        asset = xml.find('asset')
        for node in list(asset):
            if node.get('name', '').startswith(('task_', 'original_collision_')):
                asset.remove(node)
        source = json.loads((review / 'usd/reference.json').read_text())
        arrays = np.load(review / 'usd/geometry.npz')
        materials = MaterialExporter(asset, output, verified_sources)
        cap_parts = []
        for g in source['geometries']:
            if g['visibility'] == 'invisible' or g['purpose'] not in ('default', 'render'):
                continue
            if g['material_subsets']:
                raise ValueError('Explicit subset mapping required')
            mg = copy.deepcopy(g); mg['id'] = 'wallc_' + g['id']
            mg['body_transform_row_major'] = mg['root_transform_row_major']
            transform = np.array(mg['body_transform_row_major']).T
            points = arrays[mg['points']] @ transform[:3, :3].T + transform[:3, 3]
            moving = g['body'] == '/Button/Cap'
            owner = primary if moving else static
            if moving:
                cap_parts.append(points)
            mat = materials.export(g['material'], source['materials'][g['material']])
            for part in mesh_parts(mg, arrays, output / 'meshes', uv_name=mat['uv_name']):
                ET.SubElement(asset, 'mesh', name=part['name'], file=part['file'], inertia='shell')
                ET.SubElement(owner, 'geom', name=part['name'] + '_visual', type='mesh',
                    mesh=part['name'], material=mat['name'], contype='0', conaffinity='0', group='2')
                ET.SubElement(owner, 'geom', name=part['name'] + '_collision', type='mesh',
                    mesh=part['name'], contype='2' if moving else '4', conaffinity='1',
                    group='3', rgba='.7 .2 .2 0', friction='1 0 0', condim='3', priority='1')
        inertia = convex_mass_properties(cap_parts, profile['mass_kg'])
        i = np.array(inertia['inertia_kg_m2'])
        ET.SubElement(primary, 'inertial', pos=numbers(inertia['center_m']), mass=str(inertia['mass_kg']),
            fullinertia=numbers([i[0, 0], i[1, 1], i[2, 2], i[0, 1], i[0, 2], i[1, 2]]))
        ET.SubElement(primary, 'joint', name='button_slide', type='slide', axis='1 0 0',
            range='0 .02', stiffness='0', damping='0')
    position = np.array(list(map(float, primary.get('pos').split())))
    profile.update(work_id='QLM-SIM-016', asset_id=candidate['asset_id'],
        asset_profile='press-wall-' + label.lower() + '-v1', status='approved_asset_physics_qualification_pending',
        button_rest_front_xyz=[float(actual_front), y, z],
        canonical_goal_position=[float(actual_front + profile['threshold_m']), y, z],
        environment_profile={'id': 'press-full-wall-v1', 'wall': wall,
            'button_in_plane_yz_m': [y, z], 'back_face_flush': True,
            'position_randomization_axes': ['Y', 'Z'], 'installation_depth_randomized': False},
        source_asset=source_manifest,
        source_asset_preparation={'candidate_label': label, 'source_manifest_sha256': candidate['source_manifest_sha256'],
            'geometry_root_translation_m': translation.tolist(),
            'inertia': inertia, 'collision': 'retained original cooked hulls' if label != 'C' else 'one MuJoCo convex hull per source moving/static mesh; head/stem separate',
            'parent_resource_identity': parent['identity']})
    profile['source_profile'].update(asset_id=candidate['asset_id'],
        button_rest_front_xyz=profile['button_rest_front_xyz'], asset_origin_xyz=position.tolist(),
        canonical_goal_position=profile['canonical_goal_position'], wall=wall)
    ET.indent(tree)
    detached_write(output / 'scene.xml', ET.tostring(xml, encoding='unicode'))
    detached_write(output / 'scene.task.json', json.dumps(profile, indent=2) + '\n')
    model = mujoco.MjModel.from_xml_path(str(output / 'scene.xml'))
    for key, before in cameras_before.items():
        np.testing.assert_array_equal(getattr(model, key), before)
    np.testing.assert_array_equal(model.jnt_range, before_model.jnt_range)
    for name in ('button_slide',):
        np.testing.assert_array_equal(model.joint(name).range, before_model.joint(name).range)
    detached_write(output / 'asset-wall-provenance.json', json.dumps({
        'work_id': 'QLM-SIM-016', 'label': label, 'source_manifest': source_manifest,
        'source_manifest_sha256': candidate['source_manifest_sha256'], 'license': source_manifest['license'],
        'wall': wall, 'source_asset_modified': False, 'physics_executed': False,
        'controller_camera_action_contract_changed': False, 'cap_inertia': inertia,
        'parent_resource_identity': parent['identity']}, indent=2) + '\n')
    files = {str(p.relative_to(output)): {'sha256': file_hash(p), 'size_bytes': p.stat().st_size}
             for p in sorted(output.rglob('*')) if p.is_file() and p.name != 'resource-manifest.json'}
    detached_write(output / 'resource-manifest.json', json.dumps({
        'schema': 'qlm-portable-mujoco-resource-v1', 'entrypoint': 'scene.xml', 'files': files}, indent=2) + '\n')
    current = resource_closure(output / 'scene.xml', require_portable=True)
    if resource_closure(parent_model, require_portable=True)['identity'] != parent['identity']:
        raise RuntimeError('Original resource changed during derivation')
    return {'passed': True, 'label': label, 'model': str(output / 'scene.xml'),
            'resource_identity': current['identity'], 'parent_unchanged': True,
            'button_rest_front_xyz': profile['button_rest_front_xyz'], 'physics_qualification': 'pending'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('parent-model', 'asset-review', 'output'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--label', choices=('A', 'B', 'C'), required=True)
    parser.add_argument('--button-y', type=float, default=.1)
    parser.add_argument('--button-z', type=float, default=.3)
    args = parser.parse_args()
    print(json.dumps(build(args.parent_model, args.asset_review, args.label, args.output,
        y=args.button_y, z=args.button_z)), flush=True)


if __name__ == '__main__':
    main()
