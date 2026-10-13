"""Versioned non-task fixture for passive hinge/contact and complete state reset gates."""
import argparse
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

from qlm_bench.backends.mujoco.defaults import resolve_model,validate_default_identity
from qlm_bench.backends.mujoco.resources import resource_closure,file_hash


def main():
    p=argparse.ArgumentParser();p.add_argument('--model-root',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();source=resolve_model(task_id='push_box',model_root=a.model_root)
    parent=resource_closure(source,require_portable=True);validate_default_identity(source,parent)
    out=Path(a.output)
    if out.exists():raise FileExistsError(out)
    shutil.copytree(source.parent,out)
    tree=ET.parse(out/'scene.xml');root=tree.getroot();world=root.find('worldbody')
    hinge=ET.SubElement(world,'body',name='diagnostic_hinge',pos='.9 -.25 .2')
    # The parent preserves explicit Isaac inertias (inertiafromgeom=false).
    # These analytical cuboid inertias belong only to the new diagnostic bodies.
    ET.SubElement(hinge,'inertial',pos='.12 0 0',mass='.3',diaginertia='.0006625 .00208 .0014625')
    ET.SubElement(hinge,'joint',name='diagnostic_hinge_joint',type='hinge',axis='0 0 1',
        limited='true',range='-.4 1.2',damping='.04',armature='0')
    ET.SubElement(hinge,'geom',name='diagnostic_panel',type='box',pos='.12 0 0',size='.12 .015 .08',
        mass='.3',friction='.5 .005 .0001',condim='3',rgba='.08 .6 .75 1',contype='1',conaffinity='1')
    striker=ET.SubElement(world,'body',name='diagnostic_striker',pos='1.05 -.335 .2')
    ET.SubElement(striker,'inertial',pos='0 0 0',mass='.15',diaginertia='.0000625 .0000625 .0000625')
    ET.SubElement(striker,'freejoint',name='diagnostic_striker_joint')
    ET.SubElement(striker,'geom',name='diagnostic_striker_geom',type='box',size='.025 .025 .025',
        mass='.15',friction='.5 .005 .0001',condim='3',rgba='.9 .55 .08 1',contype='1',conaffinity='1')
    ET.indent(tree);tree.write(out/'scene.xml',encoding='unicode')
    old=json.loads((out/'scene.task.json').read_text())
    profile={'schema':'qlm-mujoco-hinge-reset-fixture-v1','kind':'non_task_diagnostic_not_formal_demonstration',
        'work_id':'QLM-SIM-013','parent_resource_identity':parent['identity'],
        'observer':old['observer'],'mjwarp_capacity':old['mjwarp_capacity'],
        'runtime':'Same MuJoCoPhysics/RenderMirror;not registered as a benchmark task',
        'physics_interaction':'Passive panel driven only by contact from a free striker with declared initial velocity',
        'randomization':'Seeded initial qpos/qvel only;no model/camera/mass/friction mutation',
        'force_or_teleport_during_run':False}
    (out/'scene.task.json').write_text(json.dumps(profile,indent=2)+'\n')
    # The fixture changes XML/task profile only. Every inherited mesh,texture,
    # original STEP provenance and protected LOD file is copied without changes.
    files={str(f.relative_to(out)):{'sha256':file_hash(f),'size_bytes':f.stat().st_size}
           for f in sorted(out.rglob('*')) if f.is_file() and f.name!='resource-manifest.json'}
    (out/'resource-manifest.json').write_text(json.dumps({'schema':'qlm-portable-mujoco-resource-v1',
        'entrypoint':'scene.xml','files':files},indent=2)+'\n')
    current=resource_closure(out/'scene.xml',require_portable=True)
    print(json.dumps({'passed':True,'model':str(out/'scene.xml'),'resource_identity':current['identity'],
        'parent_resource_identity':parent['identity'],'registered_task':False}),flush=True)


if __name__=='__main__':main()
