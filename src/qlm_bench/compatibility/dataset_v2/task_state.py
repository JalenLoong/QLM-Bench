"""Task-specific state semantics over the unchanged dataset columns; CPU only."""
import numpy as np

PRESS_PROFILE = 'press-button-v2-1'

def push_progress(center_x, initial_center_x):
    """Frozen Push Box progress: forward displacement of the geometric center."""
    values=np.asarray([center_x,initial_center_x],dtype=float)
    if values.shape!=(2,) or not np.isfinite(values).all():
        raise ValueError('Finite current and reset box centers required')
    return float(values[0]-values[1])

def goal_position(profile):
    if "canonical_goal_position" in profile:
        goal=np.asarray(profile["canonical_goal_position"],dtype=float)
        if goal.shape!=(3,) or not np.isfinite(goal).all():
            raise ValueError("Finite canonical goal XYZ required")
        return goal.tolist()
    if profile.get('task_profile_version') == PRESS_PROFILE:
        return (np.asarray(profile['button_rest_front_xyz']) + np.asarray(profile['press_axis_world']) * profile['success_displacement_m']).tolist()
    if profile.get('task_profile_version','').startswith('lift-basket-'):
        return list(profile['lift_goal_position'])
    return [sum(profile['goal_x'])/2, sum(profile['goal_y'])/2, 0.]

def task_values(profile, center, initial_center_x):
    if profile.get('task_profile_version') == PRESS_PROFILE:
        progress=float(np.dot(np.asarray(center)-profile['button_rest_front_xyz'],profile['press_axis_world']))
    else:
        progress=push_progress(center[0],initial_center_x)
    return {'task.goal.position':goal_position(profile),'task.progress':[progress]}
