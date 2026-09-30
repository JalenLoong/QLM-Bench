"""Task-specific state semantics over the unchanged dataset columns; CPU only."""
import numpy as np

PRESS_PROFILE = 'press-button-v2-1'

def goal_position(profile):
    if profile.get('task_profile_version') == PRESS_PROFILE:
        return (np.asarray(profile['button_rest_front_xyz']) + np.asarray(profile['press_axis_world']) * profile['success_displacement_m']).tolist()
    return [sum(profile['goal_x'])/2, sum(profile['goal_y'])/2, 0.]

def task_values(profile, center, initial_center_x):
    if profile.get('task_profile_version') == PRESS_PROFILE:
        progress=float(np.dot(np.asarray(center)-profile['button_rest_front_xyz'],profile['press_axis_world']))
    else:
        progress=float(center[0])-initial_center_x
    return {'task.goal.position':goal_position(profile),'task.progress':[progress]}
