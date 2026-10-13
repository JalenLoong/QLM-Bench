"""Register the CAD Go2 trunk surface to the unchanged MuJoCo base visual mesh."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation


def obj_vertices(path):
    points=[]
    with Path(path).open() as f:
        for line in f:
            if line.startswith('v '):points.append([float(v) for v in line.split()[1:4]])
            elif line.startswith(('vn ','vt ','f ')) and points:break
    return np.asarray(points)


def main():
    p=argparse.ArgumentParser();p.add_argument('--cad-mesh',required=True);p.add_argument('--robot-pack',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
    with np.load(a.cad_mesh) as z:cad=z['vertices_mm'].astype(float)/1000;normals=z['normals'].astype(float)
    # CAD has flawed remote robot surfaces; only finite trunk-local points enter fit.
    keep=(cad[:,2]>1.29)&(cad[:,2]<1.50)&(np.abs(cad[:,0])<.13)&(np.abs(cad[:,1])<.38)
    cad=cad[keep];normals=normals[keep]
    geometry=json.loads((Path(a.robot_pack)/'geometry-map.json').read_text())
    body_files=[Path(a.robot_pack)/p['file'] for g in geometry if g['body']=='base' and g['role']=='visual' for p in g['parts']]
    target=np.concatenate([obj_vertices(p) for p in body_files])
    target=np.unique(target,axis=0)
    rng=np.random.default_rng(0);target=target[rng.choice(len(target),min(18000,len(target)),replace=False)]
    trials=[]
    for degrees in (90.,-90.):
        rotation=Rotation.from_euler('z',degrees,degrees=True).as_matrix()
        # Assembly Go2 local Z0 plus known component translation; CAD width center
        # is checked by the actual trunk registration rather than only assumed.
        center=np.array([-.004624983344704178,0.,1.397019122648223])
        translation=-rotation@center
        initial_rotation=rotation.copy();initial_translation=translation.copy()
        current=cad@rotation.T+translation
        tree=cKDTree(current)
        for iteration in range(45):
            distance,index=tree.query(target,workers=4)
            cutoff=min(.018,float(np.quantile(distance,.75)))
            good=distance<=cutoff
            source=current[index[good]];destination=target[good]
            # Point-to-plane: preserve correct dimensional scale and avoid the
            # vertex-density bias of differently triangulated matching surfaces.
            n=normals[index[good]]@rotation.T
            valid=np.linalg.norm(n,axis=1)>.5
            source=source[valid];destination=destination[valid];n=n[valid]
            lhs=np.column_stack((np.cross(source,n),n));rhs=np.sum((destination-source)*n,axis=1)
            change=np.linalg.lstsq(lhs,rhs,rcond=None)[0]
            if np.linalg.norm(change[:3])>.04 or np.linalg.norm(change[3:])>.025:break
            delta=Rotation.from_rotvec(change[:3]).as_matrix()
            rotation=delta@rotation;translation=delta@translation+change[3:]
            current=cad@rotation.T+translation;tree=cKDTree(current)
            if np.linalg.norm(change)<1e-9:break
        distances,indices=tree.query(target,workers=4)
        trial={'initial_yaw_deg':degrees,'rotation':rotation.tolist(),'translation_m':translation.tolist(),
               'target_to_CAD_distance_m':{'median':float(np.median(distances)),'p90':float(np.quantile(distances,.90)),
                                         'p95':float(np.quantile(distances,.95)),'max':float(distances.max()),
                                         'fraction_within_1mm':float(np.mean(distances<.001))},
               'rotation_correction_deg':float(np.degrees(Rotation.from_matrix(rotation@initial_rotation.T).magnitude())),
               'translation_correction_m':float(np.linalg.norm(translation-initial_translation)),
               'iterations':iteration+1}
        trials.append(trial);print(trial,flush=True)
    best=min(trials,key=lambda t:t['target_to_CAD_distance_m']['median'])
    t=np.eye(4);t[:3,:3]=best['rotation'];t[:3,3]=best['translation_m']
    report={'work_id':'QLM-SIM-007','method':'body-surface rigid registration; exact unit scale; competing front/back axis hypotheses',
            'cad_source_points':len(cad),'trunk_reference_points':len(target),'candidates':trials,'chosen':best,
            'T_base_from_CAD_world_m':t.tolist(),'no_scaling_or_shape_warp':True,
            'cad_mesh_sha256':hashlib.sha256(Path(a.cad_mesh).read_bytes()).hexdigest(),
            'acceptance':'pending numeric thresholds, head/front check and actual visual inspection'}
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    # Small diagnostic point-cloud for independent overlap inspection.
    np.savez_compressed(out/'points.npz',reference=target,cad_base=cad@t[:3,:3].T+t[:3,3])


if __name__=='__main__':main()
