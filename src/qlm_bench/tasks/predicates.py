"""Pure physical success predicates shared across simulator adapters."""
import numpy as np
from qlm_bench.compatibility.dataset_v2.task_state import push_progress


def push_goal_condition(points_xy,goal_x,goal_y):
    points=np.asarray(points_xy,dtype=float)
    if points.ndim!=2 or points.shape[1]!=2 or not np.isfinite(points).all():raise ValueError('Finite footprint points required')
    return bool(np.all((points[:,0]>=goal_x[0])&(points[:,0]<=goal_x[1])&
                       (points[:,1]>=goal_y[0])&(points[:,1]<=goal_y[1])))


def lift_clearance_condition(minimum_world_z,floor_z,minimum):
    if not np.isfinite([minimum_world_z,floor_z,minimum]).all():raise ValueError('Finite measured clearance required')
    return bool(minimum_world_z-floor_z>=minimum)


def physical_condition(task_id,profile,*,corners_world,displacement=0.,time_s=0.,
                       center_x=None,initial_center_x=None):
    corners=np.asarray(corners_world,dtype=float)
    if corners.ndim!=2 or corners.shape[1]!=3 or not np.isfinite(corners).all():
        raise ValueError('Measured finite object geometry required')
    if task_id=='push_box':
        x,y=profile['goal_x'],profile['goal_y']
        condition=push_goal_condition(corners[:,:2],x,y)
        # Goal membership and episode progress are different quantities. This
        # is the same progress function used by the original Isaac recorder.
        return condition,push_progress(center_x,initial_center_x)
    if task_id=='press_button':
        if not np.isfinite(displacement):raise ValueError('Actual slider displacement required')
        return bool(displacement>=profile['threshold_m']),float(displacement)
    if task_id=='lift_basket':
        clearance=float(corners[:,2].min()-profile['floor_z_m'])
        return bool(lift_clearance_condition(corners[:,2].min(),profile['floor_z_m'],profile['minimum_clearance_m']) and
                    time_s>=profile.get('success_enable_after_s',2.1)),clearance
    raise ValueError('No accepted physical predicate for this task')
