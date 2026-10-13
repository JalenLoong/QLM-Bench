"""Resource closure and explicitly frozen model parameters for MuJoCo profiles.

Data snapshots carry changing MjData, while MjModel parameters are frozen for an
episode. Change a model/profile through an explicit new runtime, not by mutating
camera/material/physics parameters behind the rendering mirror.
"""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np


def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def resource_closure(model_path, *, require_portable=False):
    """Identity includes all XML mesh/texture/hfield files and declared profile.

Legacy diagnostic XMLs can be identified but report portable=False for external
paths. New original-resource packs are verified against their complete manifest.
Includes must first be flattened by an explicit preparation step; unresolved or
unhashed resources fail before loading a simulator.
"""
    entry = Path(model_path).resolve(strict=True)
    root = entry.parent
    tree = ET.parse(entry).getroot()
    if tree.tag != 'mujoco' or tree.findall('.//include'):
        raise ValueError('Expected a flattened MJCF profile; unresolved includes are not accepted')
    compiler = tree.find('compiler')
    compiler = {} if compiler is None else compiler.attrib
    paths = {entry}
    portable = True
    for node in tree.iter():
        file = node.get('file')
        if file is None:
            continue
        folder = compiler.get('meshdir' if node.tag == 'mesh' else 'texturedir', '') if node.tag in ('mesh','texture') else ''
        target = (root / folder / file).resolve(strict=True)
        if Path(folder).is_absolute() or Path(file).is_absolute() or not target.is_relative_to(root):
            portable = False
        paths.add(target)
    manifest_path = root/'resource-manifest.json'
    manifest = None
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        if manifest.get('schema') != 'qlm-portable-mujoco-resource-v1' or manifest.get('entrypoint') != entry.name:
            raise ValueError('Resource manifest schema/entrypoint mismatch')
        declared = set()
        for name, expected in manifest['files'].items():
            relative = Path(name)
            if relative.is_absolute() or '..' in relative.parts:
                raise ValueError('Unsafe resource manifest path')
            target = (root/relative).resolve(strict=True)
            if not target.is_relative_to(root):
                raise ValueError('Resource symlink escapes portable pack')
            if target.stat().st_size != expected['size_bytes'] or file_hash(target) != expected['sha256']:
                raise ValueError('Resource checksum mismatch: '+name)
            declared.add(target)
        if not paths <= declared:
            raise ValueError('MJCF dependency missing from resource manifest')
        paths.update(declared)
        paths.add(manifest_path)
    else:
        for suffix in ('.profile.json','.task.json'):
            sidecar = entry.with_suffix(suffix)
            if sidecar.exists():
                paths.add(sidecar)
    if require_portable and not portable:
        raise ValueError('External/absolute resources are not a portable runtime profile')
    files = {(str(p.relative_to(root)) if p.is_relative_to(root) else str(p)):file_hash(p) for p in sorted(paths)}
    payload = json.dumps({'schema':'qlm-mujoco-closure-v1','entrypoint':entry.name,'files':files},sort_keys=True,separators=(',',':'))
    return {'identity':hashlib.sha256(payload.encode()).hexdigest(),'files':files,'portable':portable,
            'declared_manifest_verified':manifest is not None,'entrypoint':entry.name}


_SMALL_PARAMETER_PREFIXES = ('body_', 'jnt_', 'dof_', 'geom_', 'cam_', 'light_', 'mat_',
                             'actuator_', 'eq_', 'tendon_', 'pair_', 'exclude_')


def model_parameter_identity(model, *, full=False):
    """Fingerprint frozen physics/visual parameters, including mutable cameras.

Large mesh/texture data is checked on initialization and close (full=True).
Every capture checks all small model parameter arrays and option values, making
unsupported per-frame camera/light/material/geometry changes fail explicitly.
"""
    h = hashlib.sha256()
    for name in sorted(dir(model)):
        if name.startswith('_') or (not full and not name.startswith(_SMALL_PARAMETER_PREFIXES)):
            continue
        value = getattr(model,name)
        if not isinstance(value,np.ndarray):
            continue
        if value.dtype.hasobject:
            raise ValueError('Unexpected object model parameter: '+name)
        h.update(name.encode()); h.update(str((value.shape,value.dtype.str)).encode()); h.update(value.tobytes())
    sections=[('opt',model.opt),('stat',model.stat)]
    sections.extend(('vis.'+name,getattr(model.vis,name)) for name in ('global_','quality','headlight','map','scale','rgba'))
    for section,obj in sections:
        for name in sorted(dir(obj)):
            if name.startswith('_'):
                continue
            value = getattr(obj,name)
            if isinstance(value,np.ndarray):
                h.update((section+'.'+name).encode()); h.update(value.tobytes())
            elif isinstance(value,(int,float,bool)) or isinstance(getattr(value,'value',None),int):
                h.update((section+'.'+name+'='+repr(value)).encode())
    return h.hexdigest()
