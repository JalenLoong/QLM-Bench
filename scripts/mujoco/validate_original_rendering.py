"""Same-state original-asset rendering gates; replay fixtures are not recordings."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time
import traceback

import mujoco
import numpy as np
from PIL import Image

from qlm_bench.backends.mujoco.physics import MuJoCoPhysics
from qlm_bench.backends.mujoco.render import RenderMirror


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,value):Path(path).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')


def prepare(model,captures,out):
    out.mkdir(parents=True,exist_ok=False)
    physics=MuJoCoPhysics(model)
    if physics.model.na or physics.model.nmocap or physics.model.neq:
        raise ValueError('Source capture only covers models without activation/mocap/equality state')
    rows=[json.loads(line) for line in Path(captures).read_text().splitlines()]
    selected=sorted(set([0,len(rows)//3,2*len(rows)//3,len(rows)-2,len(rows)-1]))
    records=[]
    for index in selected:
        source=rows[index];data=physics.data[0]
        data.qpos[:]=source['qpos'];data.qvel[:]=source['qvel'];data.time=source['simulation_time_ns']/1e9
        physics.ticks[0]=source['physics_step'];physics.epochs[0]=source['reset_epoch']
        mujoco.mj_forward(physics.model,data);snap=physics.snapshot()
        stem=f'{index:05d}';arrays={k:v for k,v in snap.items() if isinstance(v,np.ndarray)}
        np.savez_compressed(out/(stem+'.npz'),**arrays)
        meta={k:v for k,v in snap.items() if k not in arrays};write(out/(stem+'.json'),meta)
        records.append({'stem':stem,'physics_step':snap['physics_step'],'source_row':index})
    # Tolerances are fixed before either candidate renderer is evaluated.
    write(out/'manifest.json',{'kind':'fixed_actual_state_replay_fixture_not_recorded_RGB',
          'source_captures':str(Path(captures).resolve()),'source_sha256':sha(captures),
          'model':str(Path(model).resolve()),'resource_identity':physics.model_identity,'records':records,
          'tolerances':{'RGB_mae_255':2.,'RGB_p99_255':16.,'ROI_mae_255':2.,'ROI_p99_255':16.,
                        'mask_chebyshev_pixel_distance':1,'bbox_pixel_distance':1,'reset_max_abs_255':1},
          'physics_steps_executed':0,'camera_contract_changed':False})
    physics.close()


def load_snapshot(folder,stem):
    snap=json.loads((folder/(stem+'.json')).read_text())
    with np.load(folder/(stem+'.npz')) as a:snap.update({k:a[k].copy() for k in a.files})
    return snap


def masks(mirror):
    segmentations=mirror.geometry_masks();result={}
    model=mirror.model
    robot=set();objects=set()
    for gid in range(model.ngeom):
        name=model.geom(gid).name;body=model.body(int(model.geom_bodyid[gid])).name
        if body in ('primary','task_static') or name.startswith('original_Goal_'):objects.add(gid)
        elif body not in ('world','primary','task_static'):robot.add(gid)
    for camera,seg in segmentations.items():
        valid=seg[:,:,1]==int(mujoco.mjtObj.mjOBJ_GEOM)
        for label,ids in [('robot',robot),('object',objects)]:
            result[camera+'__'+label]=valid & np.isin(seg[:,:,0],list(ids))
    return result


def render(model,fixtures,out,iterations):
    out.mkdir(parents=True,exist_ok=False);manifest=json.loads((fixtures/'manifest.json').read_text())
    started=time.monotonic();mirror=RenderMirror(model);initialization=time.monotonic()-started
    frames=[]
    try:
        for record in manifest['records']:
            stem=record['stem'];snap=load_snapshot(fixtures,stem);capture=mirror.capture(snap,terminal=True)
            rgb={**capture['rgb'],'observer':capture['observer_rgb']}
            if any(v is None or v.shape!=(720,1280,3) or v.std()<1 for v in rgb.values()):
                raise ValueError('Missing/uniform source scene RGB')
            for name,im in rgb.items():Image.fromarray(im).save(out/(stem+'-'+name+'.png'))
            np.savez_compressed(out/(stem+'-masks.npz'),**masks(mirror))
            frames.append({'stem':stem,'physics_step':snap['physics_step'],'RGB_sha256':{k:hashlib.sha256(v.tobytes()).hexdigest() for k,v in rgb.items()}})
        # Every fixture must also produce the correct reset image without old buffers.
        first=load_snapshot(fixtures,manifest['records'][0]['stem']);first['reset_epoch']=mirror.last[0]+1
        reset=mirror.capture(first,terminal=True)
        reset_metrics={}
        for name,im in reset['rgb'].items():
            Image.fromarray(im).save(out/('reset-'+name+'.png'))
            before=np.asarray(Image.open(out/(manifest['records'][0]['stem']+'-'+name+'.png'))).astype(float)
            reset_metrics[name]={'max_abs':float(np.abs(im-before).max()),'mean_abs':float(np.abs(im-before).mean())}
        write(out/'reset-comparison.json',reset_metrics)
        # GL can vary by one8-bit rounding level even at identical geometry.
        # Preserve exact geometry/state checks; do not confuse bit determinism
        # with reset freshness. Previous exact-hash failures remain evidence.
        if any(v['max_abs']>manifest['tolerances']['reset_max_abs_255'] for v in reset_metrics.values()):
            raise ValueError('Reset RGB exceeds declared one-LSB allowance')
        first_masks=np.load(out/(manifest['records'][0]['stem']+'-masks.npz'));reset_masks=masks(mirror)
        if any(not np.array_equal(first_masks[name],mask) for name,mask in reset_masks.items()):
            raise ValueError('Reset geometry differs at identical state')
        if any(len({f['RGB_sha256'][name] for f in frames})<2 for name in ('go2_ego','d435i_rgb_task')):
            raise ValueError('Recorded motion did not change the rendered image')
        GL=mirror.gl_identity
    finally:mirror.close()
    performance={}
    for include_observer in (False,True):
        record=next(r for r in reversed(manifest['records']) if (r['physics_step']%20==0)==include_observer)
        snap=load_snapshot(fixtures,record['stem']);mirror=RenderMirror(model)
        try:
            for _ in range(3):mirror.capture(snap)
            timings=[]
            for _ in range(iterations):
                start=time.monotonic();capture=mirror.capture(snap)
                timings.append({'total':time.monotonic()-start,**capture['timing_s']})
            performance['pair_plus_observer' if include_observer else 'pair']={
                'samples':iterations,'median_s':float(np.median([x['total'] for x in timings])),
                'p95_s':float(np.percentile([x['total'] for x in timings],95)),'timings':timings}
        finally:mirror.close()
    import psutil,resource
    result={'status':'completed','kind':'renderer_only_actual_state_replay_not_rollout',
            'GL':GL,'MUJOCO_GL':os.environ['MUJOCO_GL'],'fixture_sha256':sha(fixtures/'manifest.json'),
            'initialization_s':initialization,'frames':frames,'reset_same_state_geometry_identical':True,
            'reset_RGB_within_one_LSB':True,'reset_comparison':reset_metrics,
            'performance':performance,'RSS_bytes':psutil.Process().memory_info().rss,
            'peak_RSS_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
            'physics_steps':0,'includes_physics_encoding_or_disk_pipeline':False}
    write(out/'result.json',result)


def compare(reference,candidate,fixtures,out):
    from scipy.ndimage import distance_transform_cdt
    out.mkdir(parents=True,exist_ok=False);manifest=json.loads((fixtures/'manifest.json').read_text());gates=manifest['tolerances']
    rows=[]
    for record in manifest['records']:
        stem=record['stem'];a=np.load(reference/(stem+'-masks.npz'));b=np.load(candidate/(stem+'-masks.npz'))
        for camera in ('go2_ego','d435i_rgb_task','observer'):
            x=np.asarray(Image.open(reference/(stem+'-'+camera+'.png'))).astype(float)
            y=np.asarray(Image.open(candidate/(stem+'-'+camera+'.png'))).astype(float);delta=np.abs(x-y)
            metrics={'stem':stem,'camera':camera,'RGB_mae_255':float(delta.mean()),'RGB_p99_255':float(np.percentile(delta,99))}
            ok=metrics['RGB_mae_255']<=gates['RGB_mae_255'] and metrics['RGB_p99_255']<=gates['RGB_p99_255']
            if camera!='observer':
                union=np.zeros(x.shape[:2],bool);geometry={}
                for label in ('robot','object'):
                    first=a[camera+'__'+label];second=b[camera+'__'+label];union|=first|second
                    if not first.any() and not second.any():geometry[label]={'both_occluded':True};continue
                    if first.any()!=second.any():geometry[label]={'missing_in_one_renderer':True};ok=False;continue
                    dist=max(int(distance_transform_cdt(~first,metric='chessboard')[second].max()),
                             int(distance_transform_cdt(~second,metric='chessboard')[first].max()))
                    bbox=lambda mask:np.r_[np.argwhere(mask).min(0),np.argwhere(mask).max(0)]
                    box_error=int(np.abs(bbox(first)-bbox(second)).max());geometry[label]={'mask_distance_px':dist,'bbox_delta_px':box_error}
                    ok=ok and dist<=gates['mask_chebyshev_pixel_distance'] and box_error<=gates['bbox_pixel_distance']
                metrics['geometry']=geometry
                if union.any():
                    roi=delta[union];metrics['ROI_mae_255']=float(roi.mean());metrics['ROI_p99_255']=float(np.percentile(roi,99))
                    ok=ok and metrics['ROI_mae_255']<=gates['ROI_mae_255'] and metrics['ROI_p99_255']<=gates['ROI_p99_255']
            metrics['passed']=bool(ok);rows.append(metrics)
    result={'passed':all(r['passed'] for r in rows),'reference':'OSMesa','rows':rows,'tolerances':gates,
            'fixture_sha256':sha(fixtures/'manifest.json'),'reference_result_sha256':sha(reference/'result.json'),
            'candidate_result_sha256':sha(candidate/'result.json'),'Isaac_pixel_equivalence_claimed':False}
    write(out/'result.json',result)
    if not result['passed']:raise ValueError('Renderer equivalence gate failed; retain differences and unchanged contract')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=('prepare','render','compare'))
    p.add_argument('--model');p.add_argument('--captures');p.add_argument('--fixtures',type=Path)
    p.add_argument('--reference',type=Path);p.add_argument('--candidate',type=Path);p.add_argument('--output',required=True,type=Path)
    p.add_argument('--iterations',type=int,default=20);a=p.parse_args()
    if not 5<=a.iterations<=100:raise ValueError('Bounded rendering benchmark')
    try:
        if a.mode=='prepare':prepare(a.model,a.captures,a.output)
        elif a.mode=='render':render(a.model,a.fixtures,a.output,a.iterations)
        else:compare(a.reference,a.candidate,a.fixtures,a.output)
    except BaseException as error:
        if a.output.is_dir():write(a.output/'failure.json',{'status':'failed','error':repr(error),'traceback':traceback.format_exc()})
        raise
