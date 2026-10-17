"""Same-state visual fixtures for the two declared resources, not episode data."""
import argparse
import copy
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image

from qlm_bench.backends.mujoco.render import RenderMirror
from qlm_bench.backends.mujoco.trace import verify_trace,write_json,SNAPSHOT_ARRAYS,sha
from prepare_backgrounds import validate_nonvisual


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('trace','backgrounds','output'):p.add_argument('--'+k,required=True)
    a=p.parse_args();out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
    manifest,arrays,telemetry,commands,terminal=verify_trace(a.trace)
    variants=json.loads(Path(a.backgrounds).read_text())['profiles']
    original=Path(variants[0]['model'])
    if variants[0]['resource_identity']!=manifest['model_identity']:
        raise ValueError('Reference/ap00 resource identity mismatch')
    indices=[0,len(commands)//2,len(commands)];images={};records=[]
    for variant in variants:
        proof=validate_nonvisual(original,variant['model'])
        mirror=RenderMirror(variant['model'],world_id=manifest['world_id'],rgb_profile='dual-rgb-360p-v1')
        try:
            for i in indices:
                # This is a new, explicitly versioned render-fixture state for the
                # declared variant. Its physical source remains the original trace;
                # it cannot masquerade as a production episode from that variant.
                snapshot={k:arrays[k][i].copy() for k in SNAPSHOT_ARRAYS}
                snapshot.update(model_identity=mirror.identity,model_parameters_identity=mirror.model_parameters_identity,
                    world_id=manifest['world_id'],reset_epoch=manifest['reset_epoch'],
                    physics_step=int(arrays['physics_step'][i]),simulation_time_ns=int(arrays['simulation_time_ns'][i]),
                    time=float(arrays['time'][i]))
                capture=mirror.capture(snapshot,terminal=True)
                assert capture['mirror_physics_advanced'] is False
                for role,value in {**capture['rgb'],'observer':capture['observer_rgb']}.items():
                    if value is None:continue
                    file=out/f"{variant['preset']}-{i:04d}-{role}.png";Image.fromarray(value).save(file)
                    images[variant['preset'],i,role]=value
                    records.append({'preset':variant['preset'],'boundary':i,'role':role,'path':file.name,
                                    'sha256':sha(file),'shape':list(value.shape),'simulation_time_ns':snapshot['simulation_time_ns']})
        finally:mirror.close()
    diffs=[]
    for i in indices:
        for role in ('go2_ego','d435i_rgb_task','observer'):
            x=images['ap_00',i,role].astype(float);y=images['ap_01',i,role].astype(float)
            diffs.append({'boundary':i,'role':role,'mean_abs_pixel_difference':float(np.abs(x-y).mean()),
                          'fraction_pixels_different':float(np.any(x!=y,axis=-1).mean())})
    result={'passed':True,'kind':'same-state background review fixtures,not formal episode renditions',
        'physical_trace_manifest_sha256':sha(Path(a.trace)/'manifest.json'),'profiles':variants,'frames':records,
        'pixel_differences':diffs,'camera_and_physics_arrays_equal':True,'physics_steps':0,'controller_loaded':False,
        'relabelled_physical_trace':False,'new_demonstration_count':0,'production_rule':'Choose preset before physics;record actual full resource identity'}
    if any(name.startswith('qlm_bench.controllers') for name in sys.modules):raise RuntimeError('Unexpected controller import')
    write_json(out/'result.json',result);print('Two-background actual rendering fixtures passed')


if __name__=='__main__':main()
