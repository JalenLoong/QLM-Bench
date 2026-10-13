"""Versioned conversion of the collaborator-identified procedural camera rig.

The package contains source identities, not the RAMBO file body. Recover its exact
Git blob, verify both package inventories, and consume the original box expressions.
Only camera-rig geoms and their explicit camera definition are replaced; historical
resource packs are never edited in place.
"""
import argparse
import ast
import copy
import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import tarfile
import xml.etree.ElementTree as ET

import mujoco
import numpy as np
from scipy.spatial.transform import Rotation

from qlm_bench.backends.mujoco.resources import resource_closure

SOURCE = 'source/rambo/rambo/tasks/common/lift_camera_rig.py'
INVENTORY = 'TRAIN009-portable-v8/workflow/runtime/selected/frozen/source-inventory.json'
OVERLAY = 'TRAIN009-portable-v8/source-overlay-manifest.json'
EXPECTED_SHA = '49f25a5319a8301d0f1d54144d99e969ac67ad385ae4fb2cb68db3d3e8473655'
TASKS = ('push_box', 'press_button', 'lift_basket')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')


def numbers(value):
    return ' '.join(format(float(x), '.17g') for x in np.asarray(value).reshape(-1))


def source_from_package(package, repo, output):
    with tarfile.open(package, 'r:gz') as archive:
        inventory_bytes = archive.extractfile(INVENTORY).read()
        overlay_bytes = archive.extractfile(OVERLAY).read()
    inventory = json.loads(inventory_bytes)
    overlay = json.loads(overlay_bytes)['repositories']['QLM-Bench']
    commit = overlay['git']['head']
    body = subprocess.check_output(['git', '-C', str(repo), 'show', commit+':'+SOURCE])
    digest = hashlib.sha256(body).hexdigest()
    if digest != EXPECTED_SHA or inventory['QLM-Bench'][SOURCE] != digest or overlay['files'][SOURCE]['sha256'] != digest:
        raise ValueError('Collaborator package and recovered source identity differ')
    output.mkdir(parents=True, exist_ok=False)
    source = output/'lift_camera_rig.py'
    source.write_bytes(body)
    (output/'package-source-inventory.json').write_bytes(inventory_bytes)
    (output/'package-source-overlay.json').write_bytes(overlay_bytes)
    identity = {'package_sha256':sha(package), 'source_path':SOURCE, 'source_commit':commit,
                'source_sha256':digest, 'package_inventory_member':INVENTORY,
                'package_overlay_member':OVERLAY, 'source_recovery':'byte-identical local Git blob',
                'standalone_CAD_or_mesh':'not supplied by this package'}
    write_json(output/'identity.json', identity)
    return source, identity


def programmatic_definition(source):
    if sha(source) != EXPECTED_SHA:
        raise ValueError('Only the collaborator-identified source revision is accepted')
    # The verified module imports only math/numpy; Isaac imports are inside functions.
    namespace = runpy.run_path(str(source))
    tree = ast.parse(Path(source).read_text())
    spawn = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'spawn')
    boxes = []
    def evaluate(node):
        return eval(compile(ast.Expression(node), str(source), 'eval'), {'__builtins__':{'tuple':tuple}}, namespace)
    for node in spawn.body:
        if isinstance(node, ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0], ast.Name) and node.targets[0].id in ('rotation','forward','center'):
            namespace[node.targets[0].id] = evaluate(node.value)
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id=='box':
            args = [evaluate(v) for v in node.value.args]
            name,position,size = args[:3]
            quat = args[3] if len(args)>3 else (0.,0.,0.,1.)
            color = args[4] if len(args)>4 else (.10,.12,.15)
            boxes.append({'name':name,'position_m':list(position),'full_size_m':list(size),
                          'quaternion_xyzw':list(quat),'color_rgb':list(color)})
    if [b['name'] for b in boxes] != ['mount_plate','support','boom','camera_housing','lens_face']:
        raise ValueError('Unexpected collaborator rig structure')
    mount = copy.deepcopy(namespace['CAMERAS']['task'])
    return {'schema':'qlm-collaborator-camera-rig-v1', 'geometries':boxes, 'task_camera':mount,
            'mass_modeled':False, 'collision':False, 'source_sha256':EXPECTED_SHA}


def replace_pack(before, after, source, identity, definition):
    closure = resource_closure(before/'scene.xml', require_portable=True)
    if after.exists():
        raise FileExistsError(after)
    # Reflink is an independent copy; mutable hardlinks to old resources are forbidden.
    subprocess.run(['cp','--reflink=auto','-a',str(before),str(after)],check=True)
    for name in ('attempt.json','result.json','resource-manifest.json'):
        (after/name).unlink(missing_ok=True)
    attempt = {'work_id':'QLM-SIM-006','parent_resource_identity':closure['identity'],
               'parent_path':str(before.resolve()),'builder_sha256':sha(__file__),
               'collaborator_source':identity,'kind':'camera-rig-only-derivative-not-demonstration'}
    write_json(after/'attempt.json', attempt)
    tree = ET.parse(after/'scene.xml')
    base = tree.getroot().find("worldbody/body[@name='base']")
    geoms = [g for g in base.findall('geom') if g.get('name','').startswith('original_camera_rig_')]
    if len(geoms)!=5:
        raise ValueError('Expected the current five-piece camera rig')
    for geom, box in zip(geoms,definition['geometries']):
        geom.set('pos',numbers(box['position_m']))
        geom.set('size',numbers(np.asarray(box['full_size_m'])/2))
        geom.set('quat',numbers(np.asarray(box['quaternion_xyzw'])[[3,0,1,2]]))
        geom.set('rgba',numbers([*box['color_rgb'],1.]))
        geom.set('contype','0');geom.set('conaffinity','0')
    profile = json.loads((after/'scene.task.json').read_text())
    mount = definition['task_camera']
    # Mount uses +X forward/+Y left/+Z up; MuJoCo camera uses -Z forward/+Y up.
    mount_from_optical = np.array([[0,0,1],[-1,0,0],[0,-1,0]])
    mount_rotation = Rotation.from_quat(mount['rotation_xyzw']).as_matrix()
    gl_rotation = Rotation.from_matrix(mount_rotation@mount_from_optical@np.diag([1.,-1.,-1.])).as_quat()
    camera = base.find("camera[@name='d435i_rgb_task']")
    camera.set('pos',numbers(mount['position']))
    camera.set('quat',numbers(gl_rotation[[3,0,1,2]]))
    vertical_fov = np.degrees(2*np.arctan(mount['vertical_aperture_mm']/(2*mount['focal_length_mm'])))
    camera.set('fovy',format(vertical_fov,'.17g'))
    ET.indent(tree);tree.write(after/'scene.xml',encoding='unicode')
    profile['asset_profile'] += '-ethan-rig-v1'
    profile['camera_rig'] = {'version':'ethan-programmatic-rig-v1','geometries':5,'source':identity,
                             'mass_modeled':False,'collision':False,'definition':'camera-rig-definition.json'}
    write_json(after/'scene.task.json',profile)
    write_json(after/'camera-rig-definition.json',definition)
    dest=after/'source/collaborator-camera-rig';dest.mkdir()
    for name in ('lift_camera_rig.py','identity.json','package-source-inventory.json','package-source-overlay.json'):
        (dest/name).write_bytes((source.parent/name).read_bytes())
    write_json(after/'camera-rig-derivation.json',attempt)
    files={str(p.relative_to(after)):{'sha256':sha(p),'size_bytes':p.stat().st_size}
           for p in sorted(after.rglob('*')) if p.is_file() and not (p.parent==after and p.name in ('attempt.json','result.json','resource-manifest.json'))}
    write_json(after/'resource-manifest.json',{'schema':'qlm-portable-mujoco-resource-v1','entrypoint':'scene.xml','files':files})
    new_closure=resource_closure(after/'scene.xml',require_portable=True)
    model=mujoco.MjModel.from_xml_path(str(after/'scene.xml'))
    result={'passed':True,'work_id':'QLM-SIM-006','compiled':True,'task':profile['task_id'],
            'new_resource_identity':new_closure['identity'],'parent_resource_identity':closure['identity'],
            'camera_rig_source_sha256':EXPECTED_SHA,'rig_mass_modeled':False,'rig_collision':False,
            'nq':model.nq,'nv':model.nv,'ngeoms':model.ngeom,'cameras':model.ncam}
    write_json(after/'result.json',result)
    return result


def main():
    p=argparse.ArgumentParser()
    for name in ('package','reference-repo','model-root','output'):
        p.add_argument('--'+name,required=True)
    args=p.parse_args();out=Path(args.output);out.mkdir(parents=True,exist_ok=False)
    source,identity=source_from_package(args.package,args.reference_repo,out/'collaborator-source')
    definition=programmatic_definition(source);write_json(out/'definition.json',definition)
    models={}
    for task in TASKS:
        before=Path(args.model_root)/('original-'+task+'-v1-a03')
        after=Path(args.model_root)/('original-'+task+'-v1-ethan-rig-a01')
        models[task]=replace_pack(before,after,source,identity,definition)
    write_json(out/'build-result.json',{'passed':True,'source':identity,'models':models})
    print(json.dumps({'passed':True,'source_sha256':EXPECTED_SHA,'tasks':list(models)}))


if __name__=='__main__':main()
