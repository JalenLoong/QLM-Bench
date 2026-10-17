"""Prepare exactly two portable background variants; keep physics/cameras fixed."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

import mujoco
import numpy as np

from qlm_bench.backends.mujoco.resources import resource_closure
from qlm_bench.backends.mujoco.trace import write_json, sha


def validate_nonvisual(original, variant):
    a=mujoco.MjModel.from_xml_path(str(original));b=mujoco.MjModel.from_xml_path(str(variant))
    checked=[]
    prefixes=('body_','jnt_','dof_','geom_','cam_','actuator_','eq_','tendon_','pair_','exclude_','mesh_')
    for name in dir(a):
        if not name.startswith(prefixes) or name in ('geom_rgba','geom_matid'):continue
        x=getattr(a,name);y=getattr(b,name)
        if isinstance(x,np.ndarray):
            if not np.array_equal(x,y):raise ValueError('Nonvisual model changed: '+name)
            checked.append(name)
    for name in ('qpos0','qpos_spring'):
        if not np.array_equal(getattr(a,name),getattr(b,name)):raise ValueError('Reset state changed')
    for section in ('opt',):
        for name in dir(getattr(a,section)):
            if name.startswith('_'):continue
            x=getattr(getattr(a,section),name);y=getattr(getattr(b,section),name)
            if isinstance(x,np.ndarray):equal=np.array_equal(x,y)
            elif isinstance(x,(int,float,bool)) or isinstance(getattr(x,'value',None),int):equal=x==y
            else:continue
            if not equal:raise ValueError('Physics option changed: '+name)
    for section in ('global_','quality','headlight','map','scale','rgba'):
        x=getattr(a.vis,section);y=getattr(b.vis,section)
        for name in dir(x):
            if name.startswith('_'):continue
            v=getattr(x,name);z=getattr(y,name)
            if isinstance(v,np.ndarray):equal=np.array_equal(v,z)
            elif isinstance(v,(int,float,bool)):equal=v==z
            else:continue
            if not equal:raise ValueError('Rendering quality/calibration changed: '+section+'.'+name)
    return {'passed':True,'arrays_equal':checked,'physics_options_equal':True,
            'camera_arrays_equal':True,'render_quality_equal':True,'only_floor_visual_attributes_differ':True}


def prepare(source, destination, *, work_id='QLM-DATA-015'):
    source=Path(source).resolve();destination=Path(destination).resolve()
    original=resource_closure(source,require_portable=True)
    if destination.exists():raise FileExistsError(destination)
    destination.mkdir(parents=True)
    profiles=[]
    for preset in ('ap_00','ap_01'):
        root=destination/preset;shutil.copytree(source.parent,root,copy_function=os.link)
        if preset=='ap_01':
            for name in ('scene.xml','scene.task.json','resource-manifest.json'):(root/name).unlink()
            tree=ET.parse(source);xml=tree.getroot();asset=xml.find('asset')
            if asset is None:asset=ET.SubElement(xml,'asset')
            ET.SubElement(asset,'texture',name='qlm_ap01_floor_texture',type='2d',builtin='checker',
                          width='256',height='256',rgb1='.48 .42 .32',rgb2='.40 .34 .25')
            ET.SubElement(asset,'material',name='qlm_ap01_floor_material',texture='qlm_ap01_floor_texture',
                          texrepeat='2 2',texuniform='true',reflectance='0',specular='0',shininess='0')
            floor=xml.find("worldbody/geom[@name='floor']")
            if floor is None:raise ValueError('Explicit original floor geom required')
            floor.set('material','qlm_ap01_floor_material');floor.set('rgba','1 1 1 1')
            tree.write(root/'scene.xml',encoding='unicode')
            task=json.loads(source.with_suffix('.task.json').read_text())
            task.update(appearance_preset=preset,background_profile='two-background-review-v1',
                        source_resource_identity=original['identity'])
            write_json(root/'scene.task.json',task)
            manifest=json.loads((source.parent/'resource-manifest.json').read_text())
            for name in ('scene.xml','scene.task.json'):
                manifest['files'][name]={'sha256':sha(root/name),'size_bytes':(root/name).stat().st_size}
            write_json(root/'resource-manifest.json',manifest)
        validation=validate_nonvisual(source,root/'scene.xml')
        closure=resource_closure(root/'scene.xml',require_portable=True)
        profiles.append({'preset':preset,'model':str(root/'scene.xml'),'resource_identity':closure['identity'],
                         'validation':validation,'clutter':False,'phase':'background engineering,not formal pilot'})
    result={'schema':'qlm-two-background-review-v1','work_id':work_id,
            'source_resource_identity':original['identity'],'profiles':profiles,
            'physics_and_camera_changed':False,'default_selector_changed':False,
            'new_geometry_or_collision':False,'new_texture_source':'QLM-authored builtin checker; originalassets unchanged'}
    write_json(destination/'backgrounds.json',result);return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',required=True);p.add_argument('--output',required=True)
    p.add_argument('--work-id',default='QLM-DATA-015')
    a=p.parse_args();r=prepare(a.source,a.output,work_id=a.work_id);print('Verified two backgrounds:',[x['preset'] for x in r['profiles']])
