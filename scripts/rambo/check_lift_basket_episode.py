"""Independent Lift mesh extrema, success and terminal evidence checks."""
import argparse,json,hashlib
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"source/rambo"))
import numpy as np
from scipy.spatial import ConvexHull
from pxr import Usd,UsdGeom,Gf
from rambo.tasks.common.push_box_geometry import rotation_xyzw

def main():
    p=argparse.ArgumentParser();p.add_argument('--raw',type=Path,required=True);p.add_argument('--workspace',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    cap=json.loads((a.raw/'capture.json').read_text());summary=json.loads((a.raw/'summary.json').read_text());profile=cap['profile'];source=a.workspace/profile['asset_path'];assert hashlib.sha256(source.read_bytes()).hexdigest()==profile['asset_sha256']
    s=Usd.Stage.Open(str(source));root=s.GetDefaultPrim();x=UsdGeom.XformCache();vertices=[]
    for prim in s.Traverse():
        if prim.IsA(UsdGeom.Mesh):
            m=x.ComputeRelativeTransform(prim,root)[0]
            vertices.extend(list(m.Transform(Gf.Vec3d(*v))) for v in UsdGeom.Mesh(prim).GetPointsAttr().Get())
    all_vertices=np.asarray(vertices)*np.asarray(root.GetAttribute('xformOp:scale').Get());vertices=all_vertices[ConvexHull(all_vertices).vertices]
    b=cap['boundaries'];cmd=cap['commands'];assert len(b)==len(cmd)+1;assert summary['terminal_before_reset'];assert not cap['terminal']['partial_interval'];assert summary['reset_events']==['reset_enter_after_terminal_copy','reset_exit'];assert cap['terminal']['simulation_time_ns']==b[-1]['simulation_time_ns']
    valid=[];clearance=[]
    for row in b:
        state=row['state'];R=rotation_xyzw(state['task.object.orientation']);pos=np.asarray(state['task.object.position']);z=float((vertices@R.T+pos)[:,2].min()-profile['floor_z_m']);clearance.append(z)
        assert abs(z-row['task_review']['clearance_m'])<1e-6
        assert abs(z-state['task.progress'][0])<1e-6
        upright=state['observation.state.base.position'][2]>=.1 and np.linalg.norm(np.asarray(state['observation.state.projected_gravity'])-[0,0,-1])<=.75
        valid.append(z>=profile['minimum_clearance_m'] and upright)
        assert row['contact']['status']=='unknown' and row['contact']['valid'] is False
    task_success=bool(summary['status']=='success');assert task_success==bool(all(valid[-3:]))
    assert all(np.all(np.asarray(c['executed'])[6:]==0) for c in cmd)
    assert all(np.all(np.asarray(p['external_force'])==0) and np.all(np.asarray(p['external_torque'])==0) for p in cap['physics'])
    assert all(y['simulation_time_ns']>x['simulation_time_ns'] for x,y in zip(b,b[1:]))
    lift_indices=[i for i,c in enumerate(cmd) if c['extensions']['expert']['phase']=='lift']
    first_lift=lift_indices[0] if lift_indices else None
    prior=cmd[first_lift-1]['extensions']['expert'] if first_lift is not None and first_lift>0 else {}
    threaded_then_lift=bool(first_lift is not None and prior.get('completely_through') and prior.get('through_count',0)>=3)
    assert np.allclose(b[0]['state']['observation.state.base.position'][:2],[0.,0.],atol=1e-6)
    assert np.allclose(b[0]['state']['task.object.position'][:2],profile['primary_position'][:2],atol=1e-6)
    result=dict(passed=True,task_success=task_success,threaded_then_lift=threaded_then_lift,lift_start_ns=None if first_lift is None else cmd[first_lift]['start_tick']*2_000_000,pre_lift_rear_clearance_m=prior.get('foot_rear_past_handle_far_side_m'),actions=len(cmd),boundaries=len(b),duration_s=b[-1]['simulation_time_ns']/1e9,terminal_before_reset=True,terminal_clearance_m=clearance[-1],maximum_clearance_m=max(clearance),geometry_method='independent source mesh vertices + authored root scale + convex-hull extrema + recorded pose',source_vertex_count=len(all_vertices),support_vertices=len(vertices),phases=sorted({x['extensions']['expert']['phase'] for x in cmd}),contact='unknown_diagnostic_only')
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':main()
