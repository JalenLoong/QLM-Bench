"""Build a portable Go2 candidate from an actual original Isaac reference export.

This is an explicit preparation tool, not a runtime USD dependency. Original
triangles, collision primitives and rigid-body parameters are retained. Solver
contact parameters are declared candidates and require independent behavior gates.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import traceback
import xml.etree.ElementTree as ET

import mujoco
import numpy as np
from scipy.spatial.transform import Rotation


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def numbers(v):
    return ' '.join(format(float(x), '.17g') for x in np.asarray(v).reshape(-1))


def quat(matrix):
    return numbers(Rotation.from_matrix(matrix).as_quat()[[3, 0, 1, 2]])


def attribute(record, name):
    return record['attributes'][name]['value']


def joint_frame(joint, side):
    m = np.eye(4)
    m[:3, :3] = Rotation.from_quat(attribute(joint, 'physics:localRot'+str(side))['quaternion_xyzw']).as_matrix()
    m[:3, 3] = attribute(joint, 'physics:localPos'+str(side))
    return m


def split_transform(row_matrix):
    m = np.asarray(row_matrix, dtype=float).T
    scale = np.linalg.norm(m[:3, :3], axis=0)
    rotation = m[:3, :3] / scale
    if not np.allclose(rotation.T @ rotation, np.eye(3), atol=1e-7) or np.linalg.det(rotation) < 0:
        raise ValueError('A primitive transform has shear/reflection; no implicit approximation')
    return m[:3, 3], rotation, scale


def primitive(g):
    pos, rotation, scale = split_transform(g['body_transform_row_major'])
    a = {k: v['value'] for k, v in g['geometry_attributes'].items()}
    if g['type'] == 'Cube':
        typ, size = 'box', scale * float(a['size']) / 2
    elif g['type'] == 'Sphere':
        if not np.allclose(scale, scale[0], atol=1e-7):
            raise ValueError('Nonuniform sphere would require an explicit ellipsoid mapping')
        typ, size = 'sphere', [float(a['radius']) * scale[0]]
    elif g['type'] == 'Cylinder':
        axis = {'X': 0, 'Y': 1, 'Z': 2}[a['axis']]
        radial = np.delete(scale, axis)
        if not np.allclose(radial, radial[0], atol=1e-7):
            raise ValueError('Elliptical cylinder is not silently approximated')
        axis_rotation = np.eye(3) if axis == 2 else Rotation.from_rotvec(
            np.array([0., np.pi / 2, 0.]) if axis == 0 else np.array([-np.pi / 2, 0., 0.])).as_matrix()
        rotation = rotation @ axis_rotation
        typ, size = 'cylinder', [float(a['radius']) * radial[0], float(a['height']) * scale[axis] / 2]
    else:
        raise ValueError('Unsupported original collision primitive: '+g['type'])
    return dict(type=typ, pos=numbers(pos), quat=quat(rotation), size=numbers(size))


def mesh_parts(g, arrays, folder, *, uv_name=None):
    """Retain every source triangle and face-varying normal/UV without decimation."""
    counts = arrays[g['face_counts']]
    if not np.all(counts == 3) or g['orientation'] != 'rightHanded':
        raise ValueError('Original robot exporter requires explicit right-handed triangles')
    faces = arrays[g['face_indices']].reshape(-1, 3)
    m = np.asarray(g['body_transform_row_major'], dtype=float).T
    points = arrays[g['points']] @ m[:3, :3].T + m[:3, 3]
    face_cross = np.cross(points[faces[:,1]]-points[faces[:,0]], points[faces[:,2]]-points[faces[:,0]])
    face_area2 = np.linalg.norm(face_cross, axis=1)
    # Authored source meshes contain repeated-vertex zero-area faces. They have
    # no surface and no rasterized area. Record their original indices instead
    # of passing invalid normals/faces to MuJoCo; never decimate valid geometry.
    nondegenerate = face_area2 > 0
    normals = arrays[g['normals']] @ np.linalg.inv(m[:3, :3]) if 'normals' in g else None
    if normals is not None:
        norms = np.linalg.norm(normals, axis=1, keepdims=True)
        normals = normals / np.where(norms == 0, 1., norms)
    # All validated robot shaders below are constant-color OmniPBR and do not
    # sample UVs. Several source UV sets are only defined on material subsets,
    # not the full mesh. Preserve them in source/geometry.npz, but do not invent
    # missing coordinates or attach an unused invalid UV stream to the OBJ.
    uv = g.get('primvars',{}).get(uv_name) if uv_name else None
    if uv_name and uv is None:
        raise ValueError('Required material UV set missing: '+uv_name)
    texcoords = arrays[uv['array']] if uv else None
    assigned = np.full(len(faces), -1, dtype=int)
    groups = []
    for subset in g['material_subsets']:
        indices = np.asarray(subset['indices'], dtype=int)
        if subset['element_type'] != 'face' or np.any(assigned[indices] != -1):
            raise ValueError('Overlapping or non-face material subsets')
        assigned[indices] = len(groups)
        groups.append((subset['material'], indices))
    if np.any(assigned == -1):
        groups.append((g['material'], np.flatnonzero(assigned == -1)))
    results = []
    for i, (material, selected) in enumerate(groups):
        degenerate = selected[~nondegenerate[selected]]
        selected = selected[nondegenerate[selected]]
        if not len(selected):
            raise ValueError('Entire material group has zero surface area')
        name = g['id']+'_'+str(i)
        path = folder / (name+'.obj')
        old_vertex, new_vertex = np.unique(faces[selected].reshape(-1), return_inverse=True)
        corners = (selected[:, None] * 3 + np.arange(3)).reshape(-1)
        def corner_indices(interpolation):
            if interpolation == 'faceVarying':
                return corners
            if interpolation in ('vertex', 'varying'):
                return faces[selected].reshape(-1)
            raise ValueError('Unsupported source interpolation: '+interpolation)
        n = None if normals is None else normals[corner_indices(g['normal_interpolation'])]
        t = None if texcoords is None else texcoords[corner_indices(uv['interpolation'])]
        repaired_normals = []
        if n is not None:
            missing = np.linalg.norm(n, axis=1) == 0
            n[missing] = np.repeat(face_cross[selected]/face_area2[selected,None],3,axis=0)[missing]
            repaired_normals = corners[missing].tolist()
        with path.open('x') as stream:
            stream.write('# Original USD triangles; source body-local coordinates; no simplification\n')
            np.savetxt(stream, points[old_vertex], fmt='v %.17g %.17g %.17g')
            if t is not None:
                np.savetxt(stream, t, fmt='vt %.17g %.17g')
            if n is not None:
                np.savetxt(stream, n, fmt='vn %.17g %.17g %.17g')
            for face_index, vertex in enumerate(new_vertex.reshape(-1, 3)):
                labels = []
                for corner, v in enumerate(vertex):
                    index = face_index*3 + corner + 1
                    labels.append(str(v+1) + (('/'+str(index)) if t is not None else '/') +
                                  (('/'+str(index)) if n is not None else ''))
                stream.write('f '+' '.join(labels)+'\n')
        results.append(dict(name=name, file='meshes/'+path.name, material=material,
                            source_faces=len(selected), vertices=len(old_vertex), sha256=sha(path),
                            zero_area_source_faces_removed=degenerate.tolist(), zero_normal_source_corners_repaired=repaired_normals))
    if sum(p['source_faces']+len(p['zero_area_source_faces_removed']) for p in results) != len(faces):
        raise ValueError('Not every visual face was exported exactly once')
    return results


def build(reference, output):
    ref, out = Path(reference), Path(output)
    out.mkdir(parents=True, exist_ok=False)
    result = {'work_id': 'QLM-SIM-005', 'status': 'started', 'source_reference': str(ref.resolve()), 'builder_sha256':sha(__file__)}
    (out/'attempt.json').write_text(json.dumps(result, indent=2)+'\n')
    try:
        identity = json.loads((ref/'result.json').read_text())
        usd = json.loads((ref/'robot_usd/reference.json').read_text())
        if identity['status'] != 'completed' or not identity['source_unchanged']:
            raise ValueError('Actual unchanged Isaac reference required')
        for path, expected in [('robot_physics.npz', identity['physics_arrays_sha256']),
                               ('robot_usd/reference.json', identity['usd_reference_sha256']),
                               ('robot_usd/geometry.npz', usd['geometry_arrays_sha256'])]:
            if sha(ref/path) != expected:
                raise ValueError('Reference checksum mismatch: '+path)
        data = np.load(ref/'robot_physics.npz', allow_pickle=False)
        arrays = np.load(ref/'robot_usd/geometry.npz', allow_pickle=False)
        if usd['meters_per_unit'] != 1 or usd['up_axis'] != 'Z':
            raise ValueError('Explicit source unit/axis conversion required')
        body_index = {name: i for i, name in enumerate(identity['body_names'])}
        joint_index = {name: i for i, name in enumerate(identity['joint_names'])}
        paths = {path: name for name, path in identity['body_paths'].items()}
        base_attributes = usd['bodies'][identity['body_paths']['base']]['attributes']
        if base_attributes['physxArticulation:enabledSelfCollisions']['value'] is not False:
            raise ValueError('This profile explicitly maps the original disabled self-collision setting')
        for field in ('joint_stiffness', 'joint_damping', 'joint_friction_coeff', 'joint_dynamic_friction_coeff', 'joint_viscous_friction_coeff'):
            if np.any(data[field] != 0):
                raise ValueError('Nonzero physical joint loss requires explicit mapping: '+field)
        root = ET.Element('mujoco', model='original-isaac-go2')
        ET.SubElement(root, 'compiler', angle='radian', autolimits='true', inertiafromgeom='false',
                      fusestatic='false', discardvisual='false', meshdir='.', texturedir='.')
        ET.SubElement(root, 'option', timestep='0.002', integrator='implicitfast', solver='Newton',
                      iterations='100', tolerance='1e-8', cone='pyramidal', gravity='0 0 -9.81')
        default = ET.SubElement(root, 'default')
        ET.SubElement(default, 'joint', damping='0', frictionloss='0', armature='0')
        ET.SubElement(default, 'geom', condim='3', friction='1 0 0', margin='0',
                      solref='.02 1', solimp='.9 .95 .001', priority='0')
        visual = ET.SubElement(root, 'visual')
        ET.SubElement(visual, 'global', offwidth='1280', offheight='720')
        ET.SubElement(visual, 'quality', offsamples='4')
        asset = ET.SubElement(root, 'asset')
        meshes = out/'meshes'; meshes.mkdir()
        material_names = {}
        for i, (path, mat) in enumerate(usd['materials'].items()):
            shader = [v for v in mat['nodes'].values() if v['type'] == 'Shader']
            if len(shader) != 1:
                raise ValueError('Robot material has unhandled shader graph: '+path)
            a = {k: v['value'] for k, v in shader[0]['attributes'].items() if k.startswith('inputs:')}
            if set(a) - {'inputs:diffuse_color_constant', 'inputs:emissive_color'}:
                raise ValueError('Unhandled original robot material inputs')
            color = a['inputs:diffuse_color_constant']
            if np.any(a.get('inputs:emissive_color', [0, 0, 0])):
                raise ValueError('Nonzero emissive material needs explicit mapping')
            name = 'original_material_'+str(i); material_names[path] = name
            ET.SubElement(asset, 'material', name=name, rgba=numbers([*color, 1]),
                          specular='.5', shininess='.5')
        world = ET.SubElement(root, 'worldbody')
        ET.SubElement(world, 'light', pos='1 -1 3', dir='-1 1 -2', diffuse='.8 .8 .8')
        ET.SubElement(world, 'geom', name='floor', type='plane', size='4 4 .1', rgba='.35 .4 .45 1', contype='2', conaffinity='1')
        bodies = {'base': ET.SubElement(world, 'body', name='base', pos='0 0 .4')}
        ET.SubElement(bodies['base'], 'freejoint', name='root')
        pending = list(usd['joints'])
        while pending:
            progress = False
            for j in pending[:]:
                parent = paths[j['relationships']['physics:body0'][0]]
                child = paths[j['relationships']['physics:body1'][0]]
                if parent not in bodies:
                    continue
                if child in bodies:
                    raise ValueError('Closed/duplicate joint graph is not supported by this robot exporter')
                m = joint_frame(j, 0) @ np.linalg.inv(joint_frame(j, 1))
                b = ET.SubElement(bodies[parent], 'body', name=child, pos=numbers(m[:3, 3]), quat=quat(m[:3, :3]))
                bodies[child] = b
                if j['type'] == 'PhysicsRevoluteJoint':
                    index = joint_index[j['name']]
                    axis = joint_frame(j, 1)[:3, :3] @ np.eye(3)[{'X': 0, 'Y': 1, 'Z': 2}[attribute(j, 'physics:axis')]]
                    ET.SubElement(b, 'joint', name=j['name'], type='hinge', axis=numbers(axis),
                                  pos=numbers(joint_frame(j, 1)[:3, 3]),
                                  range=numbers(data['joint_pos_limits'][0, index]),
                                  armature=numbers(data['joint_armature'][0, index]))
                elif j['type'] != 'PhysicsFixedJoint':
                    raise ValueError('Unexpected robot joint type')
                pending.remove(j); progress = True
            if not progress:
                raise ValueError('Disconnected original joint graph')
        if set(bodies) != set(identity['body_names']):
            raise ValueError('Incomplete robot body mapping')
        for name, body in bodies.items():
            index = body_index[name]
            inertia = data['body_inertia'][0, index].reshape(3, 3)
            # The exported runtime inertia is already expressed in the body
            # frame. body_com_pose_b's quaternion must NOT rotate it again.
            ET.SubElement(body, 'inertial', pos=numbers(data['body_com_pose_b'][0, index, :3]),
                          mass=numbers(data['body_mass'][0, index]),
                          fullinertia=numbers([inertia[0,0], inertia[1,1], inertia[2,2], inertia[0,1], inertia[0,2], inertia[1,2]]))
        geometry_map = []
        for g in usd['geometries']:
            body = bodies[paths[g['body']]]
            record = {'source_path': g['path'], 'source_type': g['type'], 'body': paths[g['body']]}
            if g['collision_enabled']:
                values = primitive(g)
                name = paths[g['body']][:2] if paths[g['body']].endswith('_foot') else g['id']+'_collision'
                ET.SubElement(body, 'geom', name=name, **values, group='3', rgba='.8 .2 .2 0', contype='1', conaffinity='2')
                record.update(role='collision', name=name, mapping=values)
            elif g['type'] == 'Mesh' and g['visibility'] != 'invisible' and g['purpose'] in ('default', 'render'):
                parts = mesh_parts(g, arrays, meshes)
                for part in parts:
                    ET.SubElement(asset, 'mesh', name=part['name'], file=part['file'], inertia='shell', maxhullvert='64')
                    ET.SubElement(body, 'geom', name=part['name'], type='mesh', mesh=part['name'],
                                  material=material_names[part['material']], contype='0', conaffinity='0', group='2')
                record.update(role='visual', parts=parts)
            else:
                raise ValueError('Unhandled source geometry: '+g['path'])
            geometry_map.append(record)
        actuator = ET.SubElement(root, 'actuator')
        for name in identity['joint_names']:
            ET.SubElement(actuator, 'motor', name=name+'_effort', joint=name, gear='1', ctrllimited='false', forcelimited='false')
        profile_path = Path(__file__).resolve().parents[2]/'src/qlm_bench/compatibility/dataset_v2/spec/profile.json'
        camera_profile = json.loads(profile_path.read_text())['policy_camera_geometry']
        for name, c in camera_profile.items():
            rotation = Rotation.from_quat(c['mount_quaternion_xyzw']).as_matrix() @ np.asarray(c['R_mount_from_optical']) @ np.diag([1., -1., -1.])
            ET.SubElement(bodies['base'], 'camera', name=name, pos=numbers(c['mount_position_m']),
                          quat=quat(rotation), fovy=str(np.degrees(2*np.arctan(c['height']/(2*c['intrinsics'][1][1])))))
        ET.indent(root); xml = out/'go2.xml'; ET.ElementTree(root).write(xml, encoding='unicode')
        model = mujoco.MjModel.from_xml_path(str(xml))
        # Native near/far are scaled by compiled model extent. Freeze absolute
        # policy clipping to the original .1..20m, not default extent multipliers.
        ET.SubElement(visual, 'map', znear=format(.1/model.stat.extent, '.17g'), zfar=format(20/model.stat.extent, '.17g'))
        ET.indent(root); ET.ElementTree(root).write(xml, encoding='unicode')
        verification = verify(xml, identity, data, geometry_map)
        source_dir = out/'source'; source_dir.mkdir()
        shutil.copyfile(ref/'result.json', source_dir/'isaac-identity.json')
        shutil.copyfile(ref/'robot_usd/reference.json', source_dir/'usd-reference.json')
        shutil.copyfile(ref/'robot_usd/geometry.npz', source_dir/'geometry.npz')
        shutil.copyfile(ref/'robot_physics.npz', source_dir/'robot_physics.npz')
        (out/'geometry-map.json').write_text(json.dumps(geometry_map, indent=2)+'\n')
        profile = {'schema': 'qlm-original-go2-candidate-v1', 'work_id': 'QLM-SIM-005',
                   'original_isaac_source_commit': identity['source_commit'], 'source_uri': identity['robot_source_uri'],
                   'acceptance': 'static_mapping_only_runtime_pending', 'license': 'original Isaac asset terms; local derivative; redistribution unverified',
                   'physics': {'contact_dimension': 3, 'sliding_friction': 1., 'torsional_rolling_friction': [0.,0.],
                               'contact_margin_m': 0., 'solver': 'Newton', 'solref': [.02,1.], 'solimp': [.9,.95,.001],
                               'self_collision': False, 'collision_bits': {'robot':[1,2], 'floor':[2,1]},
                               'mapping_note': 'Rigid PhysX contact offsets/compliance are preserved in source arrays. MuJoCo solver contact mapping is a candidate, not an equivalence claim.',
                               'motor': 'RAMBOCore owns all PD, delay and effort/speed saturation; gear-one effort actuators'},
                   'render': {'original_nondegenerate_triangles_preserved': True, 'material_groups_preserved': True,
                              'source_mesh_cleanup': 'Only exactly zero-area faces omitted; zero-length normals on remaining faces replaced by geometric face normal; all source indices recorded in geometry-map.json',
                              'uv': 'Original arrays retained; constant-color source shaders do not consume UVs; no replacement texture introduced',
                              'material_mapping': 'original diffuse color; Native renderer lighting differs from MDL/RTX',
                              'policy_camera_profile_sha256': sha(profile_path), 'clipping_m': [.1,20.],
                              'observer_and_rig_acceptance': 'pending'},
                   'verification': verification, 'builder_sha256': sha(__file__)}
        (out/'go2.profile.json').write_text(json.dumps(profile, indent=2)+'\n')
        files = {str(p.relative_to(out)): {'sha256': sha(p), 'size_bytes': p.stat().st_size}
                 for p in sorted(out.rglob('*')) if p.is_file() and p.name not in ('attempt.json','result.json')}
        (out/'resource-manifest.json').write_text(json.dumps({'schema':'qlm-portable-mujoco-resource-v1','entrypoint':'go2.xml','files':files},indent=2)+'\n')
        result.update(status='completed', static_mapping=verification, runtime_acceptance='not_run',
                      resource_manifest_sha256=sha(out/'resource-manifest.json'))
    except BaseException as e:
        result.update(status='failed', error=repr(e), traceback=traceback.format_exc())
        raise
    finally:
        (out/'result.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    return result


def verify(xml, identity, data, geometry_map):
    """Compare compiled model parameters/FK with actual original runtime arrays."""
    m = mujoco.MjModel.from_xml_path(str(xml)); d = mujoco.MjData(m)
    root_pose = data['body_link_pose_w'][0, identity['body_names'].index('base')]
    d.qpos[:3] = root_pose[:3]
    d.qpos[3:7] = Rotation.from_quat(root_pose[3:]).as_quat()[[3,0,1,2]]
    for i, name in enumerate(identity['joint_names']):
        j = m.joint(name); d.qpos[j.qposadr[0]] = data['joint_pos'][0,i]
        np.testing.assert_allclose(j.range, data['joint_pos_limits'][0,i], atol=1e-9, rtol=0)
        np.testing.assert_allclose(m.dof_armature[j.dofadr], data['joint_armature'][0,i], atol=1e-12, rtol=0)
    mujoco.mj_forward(m,d)
    rows = []
    for i,name in enumerate(identity['body_names']):
        b = m.body(name); original = data['body_link_pose_w'][0,i]
        rotation = Rotation.from_quat(b.iquat[[1,2,3,0]]).as_matrix()
        inertia = rotation @ np.diag(b.inertia) @ rotation.T
        np.testing.assert_allclose(b.mass, data['body_mass'][0,i], atol=1e-12, rtol=0)
        np.testing.assert_allclose(b.ipos, data['body_com_pose_b'][0,i,:3], atol=1e-10, rtol=0)
        np.testing.assert_allclose(inertia, data['body_inertia'][0,i].reshape(3,3), atol=5e-8, rtol=0)
        pos_error = float(np.max(np.abs(d.xpos[b.id]-original[:3])))
        rot_error = float(np.max(np.abs(d.xmat[b.id].reshape(3,3)-Rotation.from_quat(original[3:]).as_matrix())))
        if pos_error > 2e-6 or rot_error > 2e-6:
            raise ValueError(f'Original body FK mismatch {name}: position={pos_error}, rotation={rot_error}')
        rows.append({'body':name,'position_max_error_m':pos_error,'rotation_matrix_max_error':rot_error,
                     'inertia_max_error':float(np.max(np.abs(inertia-data['body_inertia'][0,i].reshape(3,3))))})
    visual_parts = [p for g in geometry_map if g['role']=='visual' for p in g['parts']]
    for p in visual_parts:
        if m.mesh(p['name']).facenum[0] != p['source_faces']:
            raise ValueError('Compiled mesh lost source faces: '+p['name'])
    if m.nu != 12 or m.nq != 19 or m.nv != 18 or m.nbody != 20:
        raise ValueError('Unexpected original Go2 compiled dimensions')
    return {'passed':True,'robot_bodies':m.nbody-1,'hinges':12,'colliders':sum(g['role']=='collision' for g in geometry_map),
            'total_mass_kg':float(m.body_mass.sum()),'original_visual_triangles':sum(p['source_faces'] for p in visual_parts),
            'compiled_visual_triangles':int(m.mesh_facenum.sum()),'bodies':rows,'physics_steps':0}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference', required=True); parser.add_argument('--output', required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.reference,args.output),indent=2))
